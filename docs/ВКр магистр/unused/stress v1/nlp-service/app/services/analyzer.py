import torch
import numpy as np
from typing import Optional
import structlog
import traceback
import os

logger = structlog.get_logger()


def get_hf_token() -> Optional[str]:
    return os.getenv("HF_TOKEN", "")


class SentimentAnalyzer:
    def __init__(
        self,
        model_name: str = "cointegrated/rubert-tiny2",
        device: str = "cpu",
        hf_token: Optional[str] = None
    ):
        self.device = torch.device(device)
        self.model_name = model_name
        self.hf_token = hf_token or get_hf_token()
        self.model = None
        self.tokenizer = None
        self._initialized = False
        self._init_error: Optional[str] = None
        
        self._burnout_keywords = {
            "cynicism": [
                "скучно", "надоело", "безразлично", "всё равно", "фиолетово",
                "пофиг", "плевать", "наплевать", "без разницы",
                "мне все равно", "мне пофиг", "мне плевать"
            ],
            "apathy": [
                "апатия", "лениво", "не хочу", "не буду", "мне всё равно",
                "по барабану", "нет сил", "нет желания", "лень", "апатичен"
            ],
            "irritability": [
                "бесит", "раздражает", "злит", "ненавижу", "надоело",
                " достало", "все бесит", "бесит!", " бесит", "пипец"
            ],
            "devaluation": [
                "зря", "бесполезно", "смысла нет", "никому не нужно",
                "никто не оценит", "впустую", "без толку", "никчему"
            ],
            "complaint": [
                "жаловаться", "проблема", "трудно", "тяжело", "устал",
                "замучился", "измотан", "вымотан", "опустошён", "истощён"
            ]
        }
        
        self._positive_keywords = [
            "отлично", "прекрасно", "замечательно", "хорошо", "продуктивно",
            "доволен", "успех", "успешно", "классно", "супер", "круто",
            "нравится", "радует", "счастлив", "энергия", "мотивация"
        ]
        
        self._negative_keywords = [
            "плохо", "ужасно", "отвратительно", "грустно", "тоскливо",
            "депрессия", "несчастен", "разочарован", "огорчён"
        ]
    
    async def initialize(self):
        if self._initialized:
            return
        
        logger.info("initializing_sentiment_analyzer", model=self.model_name)

        logger.info("getting HF TOKEN = ", token=self.hf_token)
        
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            
            logger.info("attempting_to_load_transformer_model", model=self.model_name)
            
            token_kwargs = {}
            if self.hf_token:
                token_kwargs["use_auth_token"] = self.hf_token
                logger.info("using_hf_token_for_auth")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, **token_kwargs)
            logger.info("tokenizer_loaded", model=self.model_name)
            
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=3,
                **token_kwargs
            )
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("transformer_model_loaded_successfully", model=self.model_name)
            self._initialized = True
            self._init_error = None
            
        except Exception as e:
            error_msg = f"Failed to load transformer model '{self.model_name}': {str(e)}"
            logger.warning(error_msg)
            logger.debug("traceback", traceback=traceback.format_exc())
            
            self._init_error = str(e)
            self.model = None
            self.tokenizer = None
            
            logger.info("using_keyword_based_fallback_analyzer")
            self._initialized = True
    
    async def analyze(self, text: str) -> dict:
        if not self._initialized:
            try:
                await self.initialize()
            except Exception as e:
                logger.error("failed_to_initialize_analyzer", error=str(e))
                self._initialized = True
        
        text_lower = text.lower()
        
        scores = self._calculate_keyword_scores(text_lower)
        
        if self.model is not None and self.tokenizer is not None:
            try:
                sentiment_scores = self._get_transformer_sentiment(text)
                scores.update(sentiment_scores)
            except Exception as e:
                logger.warning("transformer_analysis_failed_using_keywords", error=str(e))
                self._apply_keyword_sentiment(text_lower, scores)
        else:
            self._apply_keyword_sentiment(text_lower, scores)
        
        normalized_scores = self._normalize_scores(scores)
        
        logger.debug("sentiment_analysis_complete",
                    cynicism=normalized_scores.get("cynicism_score", 0),
                    apathy=normalized_scores.get("apathy_score", 0),
                    positivity=normalized_scores.get("positivity_score", 0))
        
        return normalized_scores
    
    def _calculate_keyword_scores(self, text: str) -> dict:
        scores = {f"{key}_score": 0.0 for key in self._burnout_keywords.keys()}
        
        for category, keywords in self._burnout_keywords.items():
            score_key = f"{category}_score"
            for keyword in keywords:
                if keyword in text:
                    scores[score_key] = min(1.0, scores[score_key] + 0.25)
        
        return scores
    
    def _apply_keyword_sentiment(self, text: str, scores: dict):
        pos_count = sum(1 for kw in self._positive_keywords if kw in text)
        neg_count = sum(1 for kw in self._negative_keywords if kw in text)
        
        total = pos_count + neg_count
        if total > 0:
            positivity = pos_count / total
            negativity = neg_count / total
        else:
            positivity = 0.4
            negativity = 0.2
        
        neutrality = 1.0 - positivity - negativity
        if neutrality < 0:
            neutrality = 0.2
            total_adj = positivity + negativity
            if total_adj > 0:
                positivity = positivity / total_adj * 0.8
                negativity = negativity / total_adj * 0.8
        
        scores["positivity_score"] = positivity
        scores["negativity_score"] = negativity
        scores["neutrality_score"] = max(0.1, neutrality)
    
    def _get_transformer_sentiment(self, text: str) -> dict:
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            
            if logits.shape[-1] >= 3:
                probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
                positivity = float(probs[0])
                neutrality = float(probs[1]) if len(probs) > 1 else 0.3
                negativity = float(probs[2]) if len(probs) > 2 else 0.2
            else:
                positivity = 0.4
                negativity = 0.2
                neutrality = 0.4
        
        return {
            "positivity_score": positivity,
            "negativity_score": negativity,
            "neutrality_score": neutrality
        }
    
    def _normalize_scores(self, scores: dict) -> dict:
        burnout_categories = ["cynicism_score", "apathy_score", "irritability_score",
                              "devaluation_score", "complaint_score"]
        
        for key in burnout_categories:
            if key not in scores:
                scores[key] = 0.0
            scores[key] = min(1.0, max(0.0, scores[key]))
        
        if "positivity_score" not in scores:
            scores["positivity_score"] = 0.4
        if "negativity_score" not in scores:
            scores["negativity_score"] = 0.2
        if "neutrality_score" not in scores:
            scores["neutrality_score"] = 0.4
        
        scores["positivity_score"] = min(1.0, max(0.0, scores["positivity_score"]))
        scores["negativity_score"] = min(1.0, max(0.0, scores["negativity_score"]))
        scores["neutrality_score"] = min(1.0, max(0.0, scores["neutrality_score"]))
        
        return scores


class BurnoutClassifier:
    def __init__(self):
        self.model = None
        self._thresholds = {
            "normal": 25,
            "initial": 50,
            "moderate": 75,
            "high": 100
        }
    
    async def initialize(self):
        logger.info("initializing_burnout_classifier")
        try:
            self.model = None
            logger.info("using_fallback_burnout_calculation")
        except Exception as e:
            logger.warning("failed_to_load_burnout_model", error=str(e))
            self.model = None
    
    async def assess(self, sentiment_data: dict, message_metrics: dict) -> dict:
        return self._calculate_fallback_assessment(sentiment_data, message_metrics)
    
    def _calculate_fallback_assessment(self, sentiment_data: dict, message_metrics: dict) -> dict:
        cynicism = sentiment_data.get("cynicism_score", 0)
        apathy = sentiment_data.get("apathy_score", 0)
        irritability = sentiment_data.get("irritability_score", 0)
        devaluation = sentiment_data.get("devaluation_score", 0)
        complaint = sentiment_data.get("complaint_score", 0)
        negativity = sentiment_data.get("negativity_score", 0)
        positivity = sentiment_data.get("positivity_score", 0.4)
        
        burnout_score = (
            cynicism * 20 +
            apathy * 20 +
            irritability * 15 +
            devaluation * 15 +
            complaint * 15 +
            negativity * 10 -
            positivity * 15
        )
        
        burnout_score = max(0, min(100, burnout_score))
        level = self._get_level(burnout_score)
        
        logger.debug("burnout_assessed",
                    score=burnout_score,
                    level=level,
                    cynicism=cynicism,
                    apathy=apathy)
        
        return {
            "emotional_exhaustion": burnout_score * 1.1,
            "depersonalization": cynicism * 25,
            "personal_achievement": 100 - burnout_score * 0.8,
            "burnout_level": level,
            "burnout_score": burnout_score
        }
    
    def _prepare_features(self, sentiment_data: dict, message_metrics: dict) -> list:
        return [
            sentiment_data.get("positivity_score", 0),
            sentiment_data.get("negativity_score", 0),
            sentiment_data.get("cynicism_score", 0),
            sentiment_data.get("apathy_score", 0),
            sentiment_data.get("irritability_score", 0),
            sentiment_data.get("devaluation_score", 0),
            sentiment_data.get("complaint_score", 0),
            message_metrics.get("message_count", 0),
            message_metrics.get("avg_message_length", 0),
            message_metrics.get("response_time_avg", 0),
            message_metrics.get("group_participation_rate", 1)
        ]
    
    def _get_level(self, score: float) -> str:
        if score < self._thresholds["initial"]:
            return "normal"
        elif score < self._thresholds["moderate"]:
            return "initial"
        elif score < self._thresholds["high"]:
            return "moderate"
        else:
            return "high"
