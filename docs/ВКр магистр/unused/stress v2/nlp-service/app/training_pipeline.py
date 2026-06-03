import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import (
    AutoTokenizer, AutoModel, AutoConfig,
    get_linear_schedule_with_warmup
)
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScalesConfig:
    mbi: int = 3
    smbm: int = 3
    olbi: int = 2
    total: int = 8

    @property
    def mbi_indices(self) -> range:
        return range(0, self.mbi)

    @property
    def smbm_indices(self) -> range:
        return range(self.mbi, self.mbi + self.smbm)

    @property
    def olbi_indices(self) -> range:
        return range(self.mbi + self.smbm, self.total)


@dataclass
class TrainingConfig:
    base_model: str = "ai_forever/ruBert-base"
    max_length: int = 256
    batch_size: int = 16
    learning_rate: float = 2e-5
    epochs: int = 10
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    dropout: float = 0.1
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    output_dir: str = "./models/burnout_multitask"
    seed: int = 42


class MultiTaskBurnoutDataset(Dataset):
    def __init__(
        self,
        texts: list[str],
        labels: Optional[np.ndarray] = None,
        tokenizer: Optional[AutoTokenizer] = None,
        max_length: int = 256
    ):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        text = str(self.texts[idx])

        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        item = {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten()
        }

        if self.labels is not None:
            item['labels'] = torch.tensor(self.labels[idx], dtype=torch.float)

        return item


class MultiTaskBurnoutModel(nn.Module):
    def __init__(
        self,
        model_name: str,
        scales_config: ScalesConfig,
        dropout: float = 0.1
    ):
        super().__init__()

        self.scales_config = scales_config
        self.config = AutoConfig.from_pretrained(model_name)
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.config.hidden_size

        self.shared_fc = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        self.head_mbi = nn.Linear(hidden_size // 2, scales_config.mbi)
        self.head_smbm = nn.Linear(hidden_size // 2, scales_config.smbm)
        self.head_olbi = nn.Linear(hidden_size // 2, scales_config.olbi)

    def forward(self, input_ids, attention_mask) -> torch.Tensor:
        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        pooled = outputs.last_hidden_state[:, 0, :]
        shared = self.shared_fc(pooled)

        out_mbi = self.head_mbi(shared)
        out_smbm = self.head_smbm(shared)
        out_olbi = self.head_olbi(shared)

        logits = torch.cat([out_mbi, out_smbm, out_olbi], dim=-1)

        return logits


class BurnoutMultiTaskTrainer:
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = torch.device(config.device)
        self.scales = ScalesConfig()
        self.tokenizer = AutoTokenizer.from_pretrained(config.base_model)

        self.model = MultiTaskBurnoutModel(
            model_name=config.base_model,
            scales_config=self.scales,
            dropout=config.dropout
        ).to(self.device)

        self.optimizer = AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )

        os.makedirs(config.output_dir, exist_ok=True)
        self._set_seed()

        logger.info(f"Model initialized. Total scales: {self.scales.total}")
        logger.info(f"  MBI: {self.scales.mbi} (indices {list(self.scales.mbi_indices)})")
        logger.info(f"  SMBM: {self.scales.smbm} (indices {list(self.scales.smbm_indices)})")
        logger.info(f"  OLBI: {self.scales.olbi} (indices {list(self.scales.olbi_indices)})")

    def _set_seed(self):
        torch.manual_seed(self.config.seed)
        np.random.seed(self.config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.config.seed)

    def prepare_data(
        self,
        texts: list[str],
        labels: np.ndarray
    ) -> tuple[DataLoader, DataLoader]:
        from sklearn.model_selection import train_test_split

        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels,
            test_size=0.15,
            random_state=self.config.seed
        )

        train_dataset = MultiTaskBurnoutDataset(
            train_texts, train_labels,
            self.tokenizer, self.config.max_length
        )
        val_dataset = MultiTaskBurnoutDataset(
            val_texts, val_labels,
            self.tokenizer, self.config.max_length
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=0
        )

        return train_loader, val_loader

    def train_epoch(self, dataloader: DataLoader, scheduler) -> float:
        self.model.train()
        total_loss = 0
        criterion = nn.MSELoss()

        for batch in tqdm(dataloader, desc="Training"):
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(input_ids, attention_mask)
            loss = criterion(outputs, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            scheduler.step()

            total_loss += loss.item()

        return total_loss / len(dataloader)

    def validate(self, dataloader: DataLoader) -> dict:
        self.model.eval()
        total_loss = 0
        all_preds = []
        all_labels = []

        criterion = nn.MSELoss()

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                outputs = self.model(input_ids, attention_mask)
                loss = criterion(outputs, labels)

                total_loss += loss.item()
                all_preds.extend(outputs.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        all_preds = np.clip(np.array(all_preds), 0, 100)
        all_labels = np.array(all_labels)

        mse_total = np.mean((all_preds - all_labels) ** 2)
        mae_total = np.mean(np.abs(all_preds - all_labels))

        metrics = {
            'val_loss': total_loss / len(dataloader),
            'mse_total': mse_total,
            'mae_total': mae_total,
        }

        return metrics

    def train(self, texts: list[str], labels: np.ndarray) -> dict:
        logger.info(f"Training with {len(texts)} samples | Device: {self.device}")

        train_loader, val_loader = self.prepare_data(texts, labels)

        total_steps = len(train_loader) * self.config.epochs
        warmup_steps = int(total_steps * self.config.warmup_ratio)

        scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )

        history = []

        for epoch in range(self.config.epochs):
            logger.info(f"\nEpoch {epoch + 1}/{self.config.epochs}")

            train_loss = self.train_epoch(train_loader, scheduler)
            metrics = self.validate(val_loader)

            history.append({'epoch': epoch + 1, 'train_loss': train_loss, **metrics})

            logger.info(
                f"Train Loss: {train_loss:.4f} | "
                f"Val Loss: {metrics['val_loss']:.4f} | "
                f"MAE: {metrics['mae_total']:.2f}"
            )

            self.save_model(epoch)

        self._save_history(history)
        return {'history': history}

    def predict(self, texts: list[str]) -> np.ndarray:
        self.model.eval()

        dataset = MultiTaskBurnoutDataset(
            texts, None,
            self.tokenizer, self.config.max_length
        )
        dataloader = DataLoader(dataset, batch_size=self.config.batch_size, shuffle=False)

        predictions = []

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                outputs = self.model(input_ids, attention_mask)
                predictions.extend(outputs.cpu().numpy())

        predictions = np.clip(np.array(predictions), 0, 100)
        return predictions

    def predict_single(self, text: str) -> dict:
        pred = self.predict([text])[0]

        result = {
            "text": text,
            "scales": {
                "MBI": {
                    "emotional_exhaustion": round(float(pred[0]), 1),
                    "depersonalization": round(float(pred[1]), 1),
                    "personal_achievement": round(float(pred[2]), 1),
                },
                "SMBM": {
                    "physical_fatigue": round(float(pred[3]), 1),
                    "cognitive_weariness": round(float(pred[4]), 1),
                    "emotional_exhaustion": round(float(pred[5]), 1),
                },
                "OLBI": {
                    "exhaustion": round(float(pred[6]), 1),
                    "disengagement": round(float(pred[7]), 1),
                }
            }
        }

        result["interpretation"] = self._interpret(result["scales"])
        return result

    def _interpret(self, scales: dict) -> dict:
        mbi_ee = scales["MBI"]["emotional_exhaustion"]
        mbi_dp = scales["MBI"]["depersonalization"]
        mbi_pa = scales["MBI"]["personal_achievement"]

        olbi_ex = scales["OLBI"]["exhaustion"]
        olbi_dg = scales["OLBI"]["disengagement"]

        mbi_level = self._mbi_level(mbi_ee, mbi_dp, mbi_pa)
        smbm_level = self._smbm_level(scales["SMBM"])
        olbi_level = self._olbi_level(olbi_ex, olbi_dg)

        overall = (mbi_level["score"] + smbm_level["score"] + olbi_level["score"]) / 3

        if overall >= 60:
            status = "Критический уровень выгорания"
            action = "Требуется немедленное вмешательство"
        elif overall >= 40:
            status = "Выраженное выгорание"
            action = "Консультация специалиста"
        elif overall >= 25:
            status = "Умеренное выгорание"
            action = "Профилактические меры"
        else:
            status = "Норма"
            action = "Мониторинг"

        return {
            "overall_score": round(overall, 1),
            "status": status,
            "recommended_action": action,
            "MBI": mbi_level,
            "SMBM": smbm_level,
            "OLBI": olbi_level,
        }

    def _mbi_level(self, ee: float, dp: float, pa: float) -> dict:
        score = (ee * 2 + dp * 1.5 + (100 - pa)) / 3

        if ee >= 30 or dp >= 20:
            level = "Высокое"
        elif ee >= 15 or dp >= 10:
            level = "Среднее"
        else:
            level = "Низкое"

        if pa <= 40:
            pa_level = "Редукция"
        elif pa <= 60:
            pa_level = "Средняя"
        else:
            pa_level = "Норма"

        return {"score": score, "level": level, "emotional_exhaustion_level": level, "depersonalization_level": level, "personal_achievement_level": pa_level}

    def _smbm_level(self, smbm: dict) -> dict:
        avg = np.mean(list(smbm.values()))
        score = avg

        if avg >= 50:
            level = "Высокое"
        elif avg >= 30:
            level = "Среднее"
        else:
            level = "Низкое"

        return {"score": score, "level": level}

    def _olbi_level(self, ex: float, dg: float) -> dict:
        avg = (ex + dg) / 2
        score = avg

        if avg >= 50:
            level = "Высокое"
        elif avg >= 30:
            level = "Среднее"
        else:
            level = "Низкое"

        return {"score": score, "level": level}

    def save_model(self, epoch: int = -1):
        path = os.path.join(self.config.output_dir, "model.pt")
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': self.config,
            'scales_config': self.scales,
            'epoch': epoch
        }, path)
        self.tokenizer.save_pretrained(self.config.output_dir)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str = None):
        if path is None:
            path = os.path.join(self.config.output_dir, "model.pt")
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        logger.info(f"Model loaded from {path}")

    def _save_history(self, history: list):
        path = os.path.join(self.config.output_dir, "history.json")
        with open(path, 'w') as f:
            json.dump(history, f, indent=2)


def generate_synthetic_data(n_samples: int = 1000, seed: int = 42) -> tuple[list[str], np.ndarray]:
    np.random.seed(seed)

    patterns = {
        'critical': [
            "Не могу больше, уволиться хочу",
            "Всё бесит, ничего не хочу делать",
            "Ненавижу эту работу, каждый день мучение",
        ],
        'high': [
            "Так устал, нет сил",
            "Мне всё равно на результат",
            "Коллеги раздражают, смысла нет",
        ],
        'moderate': [
            "Бывают сложные дни",
            "Не всегда всё получается",
            "Иногда сомневаюсь в себе",
        ],
        'low': [
            "Нормальный день, всё ок",
            "Доволен работой",
            "Продуктивный день",
        ],
    }

    texts = []
    labels = []

    for _ in range(n_samples):
        p = np.random.random()

        if p < 0.2:
            cat = 'critical'
            ee_mbi, dp_mbi, pa_mbi = np.random.uniform(60, 100), np.random.uniform(50, 100), np.random.uniform(20, 50)
            pf, cw, ee_smbm = np.random.uniform(60, 100), np.random.uniform(50, 100), np.random.uniform(60, 100)
            ex_olbi, dg_olbi = np.random.uniform(60, 100), np.random.uniform(50, 100)
        elif p < 0.4:
            cat = 'high'
            ee_mbi, dp_mbi, pa_mbi = np.random.uniform(30, 60), np.random.uniform(30, 60), np.random.uniform(30, 70)
            pf, cw, ee_smbm = np.random.uniform(40, 70), np.random.uniform(30, 60), np.random.uniform(40, 70)
            ex_olbi, dg_olbi = np.random.uniform(40, 70), np.random.uniform(30, 60)
        elif p < 0.6:
            cat = 'moderate'
            ee_mbi, dp_mbi, pa_mbi = np.random.uniform(15, 35), np.random.uniform(10, 30), np.random.uniform(40, 70)
            pf, cw, ee_smbm = np.random.uniform(20, 50), np.random.uniform(15, 40), np.random.uniform(20, 50)
            ex_olbi, dg_olbi = np.random.uniform(25, 50), np.random.uniform(20, 40)
        else:
            cat = 'low'
            ee_mbi, dp_mbi, pa_mbi = np.random.uniform(5, 20), np.random.uniform(5, 15), np.random.uniform(60, 95)
            pf, cw, ee_smbm = np.random.uniform(10, 30), np.random.uniform(10, 25), np.random.uniform(10, 30)
            ex_olbi, dg_olbi = np.random.uniform(10, 30), np.random.uniform(10, 25)

        text = np.random.choice(patterns[cat])
        texts.append(text)
        labels.append([ee_mbi, dp_mbi, pa_mbi, pf, cw, ee_smbm, ex_olbi, dg_olbi])

    return texts, np.array(labels)


if __name__ == "__main__":
    config = TrainingConfig(
        base_model="ai_forever/ruBert-base",
        batch_size=8,
        epochs=3,
        output_dir="./models/burnout_multitask"
    )

    texts, labels = generate_synthetic_data(n_samples=500, seed=42)
    logger.info(f"Generated {len(texts)} samples | Labels shape: {labels.shape}")

    trainer = BurnoutMultiTaskTrainer(config)
    trainer.train(texts, labels)

    test_texts = [
        "Не могу больше, всё достало",
        "Нормальный рабочий день",
        "Бывают хорошие и плохие дни"
    ]

    for text in test_texts:
        result = trainer.predict_single(text)
        print(f"\n{'='*50}")
        print(f"Текст: {text}")
        print(f"Общий балл выгорания: {result['interpretation']['overall_score']}")
        print(f"Статус: {result['interpretation']['status']}")
        print(f"Рекомендация: {result['interpretation']['recommended_action']}")
        print(f"\nШкалы:")
        print(f"  MBI:   EE={result['scales']['MBI']['emotional_exhaustion']}, "
              f"DP={result['scales']['MBI']['depersonalization']}, "
              f"PA={result['scales']['MBI']['personal_achievement']}")
        print(f"  SMBM:  PF={result['scales']['SMBM']['physical_fatigue']}, "
              f"CW={result['scales']['SMBM']['cognitive_weariness']}, "
              f"EE={result['scales']['SMBM']['emotional_exhaustion']}")
        print(f"  OLBI:  EX={result['scales']['OLBI']['exhaustion']}, "
              f"DG={result['scales']['OLBI']['disengagement']}")
