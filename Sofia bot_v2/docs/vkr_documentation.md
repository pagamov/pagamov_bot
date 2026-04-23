# Автоматизированный модуль для анализа степени выгорания сотрудников на предприятии

## Техническая документация

---

## Введение

Настоящая документация описывает программный комплекс «Sofia» — автоматизированный модуль для анализа степени эмоционального выгорания сотрудников на предприятии. Система представляет собой программное решение, реализующее функции мониторинга эмоционального состояния рабочих коллективов на основе анализа тональности сообщений в корпоративных чатах.

### Назначение системы

Разработанный программный комплекс предназначен для решения следующих задач:

1. **Мониторинг эмоционального состояния коллектива** — автоматический анализ тональности сообщений, передаваемых сотрудниками в рабочих чатах, с целью выявления признаков эмоционального неблагополучия.

2. **Оценка риска выгорания** — расчёт интегрального показателя уровня выгорания для каждого структурного подразделения на основе агрегированных данных о тональности коммуникаций.

3. **Визуализация трендов** — отображение динамики изменения уровня выгорания во времени для принятия управленческих решений службой персонала.

4. **Формирование уведомлений** — оповещение ответственных лиц о критических изменениях в эмоциональном состоянии коллективов.

### Архитектура системы

Система построена по принципу микросервисной архитектуры и включает следующие компоненты:

- **Telegram-бот** — клиентское приложение для взаимодействия с пользователями через мессенджер Telegram
- **NLP-сервис** — серверный компонент для обработки текста и анализа тональности
- **СУБД PostgreSQL** — система управления базами данных для хранения метрик и настроек

Взаимодействие между компонентами осуществляется по протоколу HTTP. Ниже представлена схема взаимодействия компонентов:

```
┌─────────────────┐     HTTP      ┌─────────────────┐
│  Telegram Bot   │─────────────>│   NLP Service   │
│   (Python)      │<─────────────│   (FastAPI)     │
└────────┬────────┘              └────────┬────────┘
         │                                │
         │ POST                           │
         │ /api/v1/analyze/sentiment       │
         │──────────���────────────────────>│
         │                               │
         │ POST                          │
         │ /api/v1/assess/burnout         │
         │───────────────────────────────>│
         │                               │
         v                               v
┌──────────────────────────────────────────────────┐
│              PostgreSQL Database                   │
│  ┌─────────┐ ┌──────────┐ ┌───────────────┐       │
│  │  Chats  │ │Sentiment │ │ BurnoutAssess │       │
│  │         │ │Metrics  │ │              │       │
│  └─────────┘ └──────────┘ └───────────────┘       │
└──────────────────────────────────────────────────┘
```

---

## Глава 1. Модуль Telegram-бота

### 1.1 Назначение и общая характеристика

Модуль Telegram-бота представляет собой клиентское приложение, реализующее интерфейс взаимодействия с системой через мессенджер Telegram. Бот обеспечивает получение согласия от пользователей на обработку их данных, приём команд управления, обработку и анализ сообщений из групповых чатов, а также отображение статистической информации о состоянии эмоционального благополучия в подразделениях.

Модуль разработан на языке Python с использованием библиотеки `python-telegram-bot версии 20.x` и обеспечивает асинхронную обработку входящих запросов. Выбор асинхронной архитектуры обусловлен необходимостью обработки большого количества одновременных запросов без блокировки очереди сообщений.

### 1.2 Архитектура модуля

В состав модуля входят следующие структурные компоненты:

| Файл | Назначение |
|------|------------|
| `bot.py` | Основной класс SofiaBot, обработчики команд и сообщений |
| `main.py` | Точка входа, инициализация приложения |
| `config.py` | Конфигурация приложения, загрузка переменных окружения |
| `database.py` | Настройка подключения к PostgreSQL |
| `models.py` | ORM-модели SQLAlchemy |
| `services/chat_service.py` | Сервисы для работы с данными |
| `services/nlp_client.py` | HTTP-клиент для NLP-сервиса |

#### 1.2.1 Основной класс SofiaBot

Основным компонентом модуля является класс `SofiaBot`, инкапсулирующий логику обработки команд и сообщений. Ниже представлен псевдокод класса с описанием ключевых методов:

```python
class SofiaBot:
    def __init__(self):
        self.application = None  # Telegram Application
        self.nlp_client = None    # NLPServiceClient
    
    async def start_command(self, update, context):
        # Отправ��а приветствия с запросом согласия
        # Создание inline-клавиатуры с кнопками "Да" и "Нет"
        pass
    
    async def help_command(self, update, context):
        # Отображение справки по доступным командам
        pass
    
    async def stats_command(self, update, context):
        # Получение статистики по всем чатам
        # Формирование сводного отчёта
        # Отправка пользователю
        pass
    
    async def handle_group_message(self, update, context):
        # Обработка входящего сообщения из группы
        # Анализ тональности через NLP-сервис
        # Сохранение метрик в БД
        pass
    
    def run(self):
        # Инициализация и запуск polling
        pass
```

Класс наследует шаблон проектирования «Command Handler» для декомпозиции функциональности по обработке различных типов команд. Каждый обработчик реализован как отдельный асинхронный метод класса.

### 1.3 Обработка согласия на обработку данных

Процесс получения согласия пользователей реализован через механизм inline-кнопок Telegram. При отправке команды `/start` пользователю направляется приветственное сообщение с объяснением целей системы и двумя кнопками:

```
┌─────────────────────────────────────────┐
│  Привет! Я — Sofia, бот для мониторинга  │
│  эмоционального благополучия.            │
│                                         │
│  📊 Я анализирую сообщения в рабочих    │
│  чатах и выявляю признаки выгорания.     │
│                                         │
│  🔒 Данные агрегируются по             │
│  подразделениям (чатам).               │
│  Ваши индивидуальные сообщения        │
│  не сохраняются.                     │
│                                         │
│  Вы даёте согласие на обработку     │
│  данных?                             │
│                                         │
│  [Да, я согласен]  [Нет, отказываюсь]  │
└─────────────────────────────────────────┘
```

При нажатии кнопки «Да, я согласен» бот сохраняет факт согласия в контексте пользователя и активирует режим мониторинга для чатов, в которых участвует данный пользователь. При нажатии «Нет, отказываюсь» бот деактивирует мониторинг для данного пользователя.

Ниже представлен код обработчика callback-запросов:

```python
async def consent_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    logger.info("consent_callback", user_id=user_id, data=query.data)
    
    if query.data == "consent_yes":
        await query.edit_message_text(
            "✅ Согласие получено!\n\n"
            "Теперь:\n"
            "• Добавив бота в группу, он начнёт анализировать сообщения\n"
            "• В личных сообщениях используйте /stats для просмотра статистики"
        )
    else:
        await query.edit_message_text("❌ Вы отказались от участия.")
```

### 1.4 Обработка команд управления

Система поддерживает следующие команды управления:

| Команда | Описание | Доступ |
|---------|----------|--------|
| `/start` | Начало работы, запрос согласия | PUBLIC |
| `/help` | Справка по использованию | PUBLIC |
| `/stats` | Просмотр статистики по подразделениям | PRIVATE |

#### 1.4.1 Команда /stats

Команда `/stats` предназначена для просмотра агрегированной статистики по подразделениям. Команда доступна только в личных сообщениях боту для защиты конфиденциальности данных. При попытке вызова команды в групповом чате пользователю направляется уведомление о необходимости перехода в личные сообщения.

Ниже представлен алгоритм обработки команды:

```
АЛГОРИТМ: Обработка команды /stats
─────────────────────────────────────
ВХОД: chat_id пользователя
ВЫХОД: форматированное сообщение со статистикой

1. Проверить тип чата
   ЕСЛИ тип чаты != PRIVATE THEN
       Отправить: "Команда /stats доступна только в личных сообщениях"
       ВЫХОД
   КОНЕЦ ЕСЛИ

2. Получить список всех мониторимых чатов из БД
   ВЫЗОВ: StatsService.get_all_chats_stats()

3. ДЛЯ каждого чата В списке:
   a. Получить текущую статистику
   b. Рассчитать тренд за последние 7 дней
   c. Определить уровень выгорания
   d. Сформировать строку отчёта

4. Отправить пользователю сводный отчёт
КОНЕЦ АЛГОРИТМА
```

Пример формируемого отчёта:

```
📊 *Статистика по подразделениям*

1. 🟡 *Отдел разработки*
   Сообщений сегодня: 47
   Выгорание: 32.5% (initial)

2. 🟢 *Отдел маркетинга*
   Сообщений сегодня: 23
   Выгорание: 18.2% (normal)

3. 🟠 *Бухгалтерия*
   Сообщений сегодня: 15
   Выгорание: 58.3% (moderate)
```

### 1.5 Обработка групповых сообщений

Обработка входящих сообщений из групповых чатов является основной функцией системы. При добавлении бота в групповой чат он начинает анализировать все текстовые сообщения участников.

#### 1.5.1 Процесс обработки сообщения

Ниже представлен алгоритм обработки входящего сообщения:

```
АЛГОРИТМ: Обработка входящего сообщения
─────────────────────────────────────────
ВХОД: текст сообщения, chat_id, chat_title
ВЫХОД: сохранённые метрики в БД

1. Проверить наличие текста
   ЕСЛИ текст пустой THEN
       ВЫХОД (игнорировать)
   КОНЕЦ ЕСЛИ

2. Вызвать NLP-сервис для анализа тональности
   ОТПРАВИТЬ: POST /api/v1/analyze/sentiment
   ПОЛУЧИТЬ: { positivity_score, negativity_score, ... }

3. ЕСЛИ анализ успешен THEN
   a. Получить или создать запись чата в БД
      ВЫЗОВ: ChatService.get_or_create_chat()
   
   b. Сохранить метрики тональности
      ВЫЗОВ: MetricsService.save_sentiment_metrics()
   
   c. Вызвать NLP-сервис для оценки выгорания
      ОТПРАВИТЬ: POST /api/v1/assess/burnout
   
   d. Сохранить оценку выгорания
      ВЫЗОВ: MetricsService.save_burnout_assessment()
   КОНЕЦ ЕСЛИ

4. Логировать результаты
КОНЕЦ АЛГОРИТМА
```

#### 1.5.2 Код обработчика сообщений

Ниже представлена реализация обработчика сообщений из групповых чатов:

```python
async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
    
    chat_id = update.message.chat_id
    chat_title = update.message.chat.title or f"Chat_{chat_id}"
    
    logger.info(
        "group_message_received",
        chat_id=chat_id,
        chat_title=chat_title,
        text=text[:50]
    )
    
    # Анализ тональности через NLP-сервис
    sentiment_result = nlp_client.analyze_sentiment_sync(text)
    
    if sentiment_result:
        async with AsyncSessionLocal() as db:
            chat_service = ChatService(db)
            metrics_service = MetricsService(db)
            
            # Получение или создание чата
            chat = await chat_service.get_or_create_chat(chat_id, "group", chat_title)
            
            # Сохранение метрик тональности
            await metrics_service.save_sentiment_metrics(chat_id, sentiment_result)
            
            # Оценка выгорания
            burnout_result = nlp_client.assess_burnout_sync(sentiment_result)
            if burnout_result:
                await metrics_service.save_burnout_assessment(chat_id, burnout_result)
            
            logger.info(
                "metrics_saved",
                chat_id=chat_id,
                sentiment=sentiment_result,
                burnout=burnout_result
            )
```

### 1.6 Взаимодействие с NLP-сервисом

Для взаимодействия с NLP-сервисом используется класс `NLPServiceClient`, реализующий синхронные HTTP-запросы. Клиент обеспечивает передачу текстовых данных на анализ и получение результатов оценки тональности и уровня выгорания.

```python
class NLPServiceClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def analyze_sentiment_sync(self, text: str) -> Optional[dict]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.post(
                    "/api/v1/analyze/sentiment",
                    json={"text": text}
                )
                response.raise_for_status()
                data = response.json()
                logger.info("sentiment_result", text=text[:50], data=data)
                return data
        except httpx.HTTPError as e:
            logger.error("nlp_sentiment_failed", error=str(e), text=text[:100])
            return None

    def assess_burnout_sync(self, sentiment_data: dict) -> Optional[dict]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.post(
                    "/api/v1/assess/burnout",
                    json={
                        "sentiment": sentiment_data,
                        "message_metrics": {}
                    }
                )
                response.raise_for_status()
                data = response.json()
                logger.info("burnout_assessment_result", data=data)
                return data
        except httpx.HTTPError as e:
            logger.error("nlp_burnout_failed", error=str(e))
            return None
```

### 1.7 Запуск и конфигурация

Запуск модуля осуществляется через точку входа `main.py`. При запуске выполняется инициализация logging-системы и создание экземпляра класса `SofiaBot`.

```python
def main():
    setup_logging()
    logger = structlog.get_logger()
    logger.info("starting_sofia_bot")
    
    bot = SofiaBot()
    bot.run()
```

Конфигурация модуля осуществляется через переменные окружения, загружаемые из файла `.env`:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота | `123456:ABC-DEF1234ghIkl-zyx57W2v1u22ew1` |
| `NLP_SERVICE_URL` | URL NLP-сервиса | `http://nlp_service:8000` |
| `POSTGRES_HOST` | Хост PostgreSQL | `postgres` |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` |
| `POSTGRES_DB` | Имя базы данных | `sofia_burnout` |
| `POSTGRES_USER` | Имя пользователя БД | `sofia_user` |
| `POSTGRES_PASSWORD` | Пароль пользователя БД | `sofia_password` |

---

## Глава 2. Модуль NLP-сервиса

### 2.1 Назначение и общая характеристика

Модуль NLP-сервиса представляет собой серверный компонент системы, обеспечивающий анализ текстовых сообщений и расчёт показателей эмоционального состояния сотрудников. Сервис реализован на основе фреймворка FastAPI и использует модели машинного обучения для обработки естественного языка.

Основные функции модуля:

1. **Анализ тональности** — определение эмоциональной окраски текстового сообщения
2. **Классификация признаков выгорания** — выявление в тексте маркеров эмоционального истощения
3. **Оценка уровня выгорания** — расчёт интегрального показателя burnout

### 2.2 Архитектура модуля

Сервис построен на базе FastAPI — современного веб-фреймворка для создания API на языке Python. Выбор FastAPI обусловлен следующими преимуществами:

- Встроенная поддержка асинхронного выполнения
- Автоматическая генерация докуме��тации Swagger
- Валидация данных через Pydantic
- Высокая производительность

В состав модуля входят следующие компоненты:

| Файл | Назначение |
|------|------------|
| `main.py` | FastAPI приложение, маршруты API |
| `config.py` | Конфигурация сервиса |
| `schemas.py` | Pydantic-схемы запросов и ответов |
| `services/analyzer.py` | Логика анализа текста |

### 2.3 API-энпоинты сервиса

Сервис предоставляет следующие REST-API-эндпоинты:

#### 2.3.1 Анализ тональности

```
POST /api/v1/analyze/sentiment
```

Входные данные:

```json
{
  "text": "Сегодня снова был сложный день, устал на работе"
}
```

Выходные данные:

```json
{
  "positivity_score": 0.15,
  "negativity_score": 0.65,
  "neutrality_score": 0.20,
  "cynicism_score": 0.0,
  "apathy_score": 0.25,
  "irritability_score": 0.0,
  "devaluation_score": 0.0,
  "complaint_score": 0.75
}
```

#### 2.3.2 Оценка выгорания

```
POST /api/v1/assess/burnout
```

Входные данные:

```json
{
  "sentiment": {
    "positivity_score": 0.15,
    "negativity_score": 0.65,
    "cynicism_score": 0.0,
    "apathy_score": 0.25
  },
  "message_metrics": {}
}
```

Выходные данные:

```json
{
  "emotional_exhaustion": 55.0,
  "depersonalization": 0.0,
  "personal_achievement": 56.0,
  "burnout_level": "initial",
  "burnout_score": 50.0
}
```

#### 2.3.3 Пакетный анализ

```
POST /api/v1/analyze/sentiment/batch
```

Входные данные:

```json
{
  "texts": [
    "Отличный день!",
    "Устал на работе",
    "Всё нормально"
  ]
}
```

#### 2.3.4 Проверка здоровья

```
GET /health
```

### 2.4 Компонент SentimentAnalyzer

Класс `SentimentAnalyzer` является основным компонентом сервиса, обеспечивающим анализ тональности текстовых сообщений. Комбинированный подход использует два механизма анализа:

1. **Key-word анализ** — поиск ключевых слов-маркеров различных эмоциональных состояний
2. **Transformer-модель** — нейросетевая модель для классификации тональности

#### 2.4.1 Архитектура анализатора

```
┌─────────────────────────────────────────────────────────────┐
│                   SentimentAnalyzer                        │
├─────────────────────────────────────────────────────────────┤
│  ВХОД: текст сообщения                                    │
│         │                                                  │
│         v                                                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  1. Keyword Scoring                                  │ │
│  │     - Поиск маркеров выгорания                       │ │
│  │     - Поиск позитивных/негативных слов             │ │
│  └─────────────────────────────────────────────────────┘ │
│         │                                                  │
│         v                                                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  2. Transformer Analysis (если модель доступна)  │ │
│  │     - rubert-tiny2 или аналог                       │ │
│  │     - Классификация тональности                    │ │
│  └─────────────────────────────────────────────────────┘ │
│         │                                                  │
│         v                                                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  3. Score Normalization                             │ │
│  │     - Приведение к диапазону [0, 1]               │ │
│  │     - Заполнение пропущенных значений              │ │
│  └─────────────────────────────────────────────────────┘ │
│         │                                                  │
│         v                                                  │
│  ВЫХОД: нормализованные оценки                          │
└─────────────────────────────────────────────────────────────┘
```

#### 2.4.2 Словари ключевых слов

Анализатор использует словари ключевых слов для каждой категории маркеров выгорания:

```python
_burnout_keywords = {
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
        "достало", "все бесит", "бесит!"
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

_positive_keywords = [
    "отлично", "прекрасно", "за��еч��тельно", "хорошо", "продуктивно",
    "доволен", "успех", "успешно", "классно", "супер", "круто",
    "нравится", "радует", "счастлив", "энергия", "мотивация"
]

_negative_keywords = [
    "плохо", "ужасно", "отвратительно", "грустно", "тоскливо",
    "депрессия", "несчастен", "разочарован", "огорчён"
]
```

#### 2.4.3 Расчёт ключевых оценок

Метод `_calculate_keyword_scores` выполняет подсчёт вхождений ключевых слов:

```python
def _calculate_keyword_scores(self, text: str) -> dict:
    scores = {f"{key}_score": 0.0 for key in self._burnout_keywords.keys()}
    
    for category, keywords in self._burnout_keywords.items():
        score_key = f"{category}_score"
        for keyword in keywords:
            if keyword in text:
                # Каждое вхождение добавляет 0.25 к оценке
                scores[score_key] = min(1.0, scores[score_key] + 0.25)
    
    return scores
```

При обнаружении ключевого слова категории «cynicism» (например, «скучно») оценка cynicism_score увеличивается на 0.25. При обнаружении нескольких ключевых слов одной категории оценка累计ируется с ограничением максимального значения 1.0.

#### 2.4.4 Анализ через Transformer-модель

При наличии доступа к предобученной модели transformers (`cointegrated/rubert-tiny2`) выполняется дополнительный анализ тональности:

```python
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
```

Модель `rubert-tiny2` — это компактная русскоязычная модель BERT, способная классифицировать текст на три категории: позитивная, негативная и нейтральная тональность.

#### 2.4.5 Нормализация оценок

После расчёта всех компонентов выполняется нормализация оценок:

```python
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
```

### 2.5 Компонент BurnoutClassifier

Класс `BurnoutClassifier` выполняет расчёт интегрального показателя уровня выгорания на основе оценок тональности.

#### 2.5.1 Модель выгорания

В основе классификатора лежит адаптированная модель выгорания Маслач (Maslach Burnout Inventory), включающая три измерения:

1. **Эмоциональное истощение (Emotional Exhaustion)** — чувство эмоциональной опустошённости
2. **Деперсонализация (Depersonalization)** — циничное отношение к работе и коллегам
3. **Снижение личных достижений (Reduced Personal Achievement)** — ощущение неэффективности

#### 2.5.2 Алгоритм расчёта burnout_score

```
АЛГОРИТМ: Расчёт уровня выгорания
─────────────────────────────────────
ВХОД: sentiment_data (оценки тональности)
ВЫХОД: burnout_score, burnout_level, компоненты

1. Извлечь компоненты из sentiment_data:
   - cynicism = sentiment_data["cynicism_score"]
   - apathy = sentiment_data["apathy_score"]
   - irritability = sentiment_data["irritability_score"]
   - devaluation = sentiment_data["devaluation_score"]
   - complaint = sentiment_data["complaint_score"]
   - negativity = sentiment_data["negativity_score"]
   - positivity = sentiment_data["positivity_score"]

2. Рассчитать burnout_score:
   score = cynicism * 20 +
           apathy * 20 +
           irritability * 15 +
           devaluation * 15 +
           complaint * 15 +
           negativity * 10 -
           positivity * 15

3. Ограничить диапазон [0, 100]:
   score = max(0, min(100, score))

4. Определить уровень:
   ЕСЛИ score < 25 THEN level = "normal"
   ИНАЧЕ ЕСЛИ score < 50 THEN level = "initial"
   ИНАЧЕ ЕСЛИ score < 75 THEN level = "moderate"
   ИНАЧЕ level = "high"

5. Рассчитать компоненты:
   emotional_exhaustion = score * 1.1
   depersonalization = cynicism * 25
   personal_achievement = 100 - score * 0.8

6. ВЕРНУТЬ результат
КОНЕЦ АЛГОРИТМА
```

Весовые коэффициенты распределены следующим образом:

| Компонент | Вес | Обоснование |
|-----------|-----|-------------|
| Cynicism | 20% | Циничное отношение — ключевой маркер выгорания |
| Apathy | 20% | Апатия свидетельствует о глубоком истощении |
| Irritability | 15% | Раздражительность — сопутствующий симптом |
| Devaluation | 15% | Обесценивание результатов — маркер деперсонализации |
| Complaint | 15% | Жалобы на условиях труда |
| Negativity | 10% | Общая негативная окраска |
| Positivity | -15% | Позитивные факторы снижают уровень выгорания |

#### 2.5.3 ��ро��ни выгорания

Система определяет четыре уровня выгорания:

| Уровень | Диапазон score | Описание | Рекомендации |
|---------|---------------|----------|--------------|
| Normal | 0-25% | Нормальное эмоциональное состояние | Мониторинг |
| Initial | 25-50% | Начальные признаки выгорания | Внимание HR |
| Moderate | 50-75% | Выраженное выгорание | Корректирующие меры |
| High | 75-100% | Критическое состояние | Немедленное вмешательство |

### 2.6 Инициализация сервиса

Сервис использует механизм lifespan для инициализации ресурсов при запуске:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global sentiment_analyzer, burnout_classifier
    
    logger.info("starting_nlp_service")
    
    # Инициализация анализатора тональности
    sentiment_analyzer = SentimentAnalyzer(
        model_name=settings.model_name,
        device=settings.device,
        hf_token=settings.hf_token
    )
    
    # Инициализация классификатора выгорания
    burnout_classifier = BurnoutClassifier()
    
    await sentiment_analyzer.initialize()
    await burnout_classifier.initialize()
    
    logger.info("nlp_service_ready")
    
    yield
    
    logger.info("shutting_down_nlp_service")
```

---

## Глава 3. Система управления базами данных и модели данных

### 3.1 Назначение и выбор СУБД

Система управления базами данных (СУБД) обеспечивает персистентное хранение информации о чатах, метриках тональности, оценках выгорания и служебных данных. В качестве СУБД используется PostgreSQL — реляционная система управления базами данных с расширенными возможностями.

Выбор PostgreSQL обусловлен след��ющими факторами:

1. **Надёжность** — ACID-совместимость и журналирование Write-Ahead Logging
2. **Производительность** — эффективная обработка сложных запросов с агрегацией
3. **Масштабируемость** — поддержка работы с большими объёмами данных
4. **Асинхронные драйверы** — поддержка asyncpg для асинхронного доступа

### 3.2 Архитектура доступа к данным

Доступ к данным реализован через ORM-слой SQLAlchemy с асинхронным движком:

```
┌─────────────────────────────────────────────────────┐
│              Telegram Bot (Application)            │
├─────────────────────────────────────────────────────┤
│         ┌─────────────────────────────────┐        │
│         │     SQLAlchemy AsyncEngine       │        │
│         │  create_async_engine(url)         │        │
│         └─────────────────────────────────┘        │
│                     │                               │
│                     │ asyncpg driver                │
│                     v                               │
│         ┌─────────────────────────────────┐        │
│         │     PostgreSQL Database           │        │
│         └─────────────────────────────────┘        │
└─────────────────────────────────────────────────────┘
```

Конфигурация движка базы данных:

```python
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)
```

Параметры пула соединений:

- `pool_size=10` — постоянные соединения в пуле
- `max_overflow=20` — дополнительные соединения при пиковой нагрузке
- `pool_pre_ping=True` — проверка соединений перед использованием

### 3.3 Модели данных

Система использует пять основных моделей данных:

#### 3.3.1 Модель Chat (Чат)

Модель `Chat` представляет рабочий чат, в котором ведётся мониторинг:

```python
class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    chat_type = Column(String(50), nullable=False)
    title = Column(String(255))
    is_monitored = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
```

Поля модели:

| Поле | Тип | Описание |
|------|-----|---------|
| id | Integer | Первичный ключ |
| chat_id | BigInteger | Идентификатор чата в Telegram |
| chat_type | String | Тип чата (group, supergroup, channel) |
| title | String | Название чата (название подразделения) |
| is_monitored | Boolean | Признак активного мониторинга |
| created_at | DateTime | Дата создания записи |

#### 3.3.2 Модель SentimentMetrics (Метрики тональности)

Модель `SentimentMetrics` хранит оценки тональности за период:

```python
class SentimentMetrics(Base):
    __tablename__ = "sentiment_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    recorded_at = Column(DateTime, server_default=func.now())
    positivity_score = Column(Numeric(5, 4))
    negativity_score = Column(Numeric(5, 4))
    neutrality_score = Column(Numeric(5, 4))
    cynicism_score = Column(Numeric(5, 4))
    apathy_score = Column(Numeric(5, 4))
    irritability_score = Column(Numeric(5, 4))
    devaluation_score = Column(Numeric(5, 4))
    complaint_score = Column(Numeric(5, 4))
    period_date = Column(Date, index=True)
    period_type = Column(String(20), default="daily")
```

Использование `Numeric(5, 4)` обеспечивает точность до 4 знаков после запятой (диапазон 0.0000-0.9999).

#### 3.3.3 Модель BurnoutAssessment (Оценка выгорания)

Модель `BurnoutAssessment` хранит оценки уровня выгорания:

```python
class BurnoutAssessment(Base):
    __tablename__ = "burnout_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    recorded_at = Column(DateTime, server_default=func.now())
    emotional_exhaustion = Column(Numeric(5, 2))
    depersonalization = Column(Numeric(5, 2))
    personal_achievement = Column(Numeric(5, 2))
    burnout_level = Column(String(20))
    burnout_score = Column(Numeric(5, 2))
    period_date = Column(Date, index=True)
    period_type = Column(String(20), default="daily")
```

#### 3.3.4 Модель Notification (Уведомление)

Модель `Notification` хранит информацию об отправленных уведомлениях:

```python
class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(String(50), nullable=False)
    recipient_type = Column(String(50), nullable=False)
    recipient_id = Column(Integer)
    department = Column(String(255))
    severity = Column(String(20))
    employee_count_affected = Column(Integer)
    department_avg_score = Column(Numeric(5, 2))
    trend = Column(String(20))
    message = Column(Text)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
```

#### 3.3.5 Модель AuditLog (Журнал аудита)

Модель `AuditLog` обеспечивает ведение журнала действий пользователей:

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer)
    user_external_id = Column(String(255))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), index=True)
```

### 3.4 ER-диаграмма базы данных

Ниже представлена схема связей между таблицами:

```
┌─────────────────┐         ┌───────────────────────┐
│      chats      │         │   sentiment_metrics   │
���─���───────────────┤         ├───────────────────────┤
│ id (PK)         │◄───────│ chat_id (FK)          │
│ chat_id         │    1:N │ id (PK)               │
│ chat_type      │         │ positivity_score      │
│ title          │         │ negativity_score      │
│ is_monitored   │         │ cynicism_score       │
│ created_at    │         │ apathy_score         │
└─────────────────┘         │ irritability_score │ 
                             │ devaluation_score   │
                             │ complaint_score     │
                             │ period_date       │
                             └───────────────────────┘
                                     │
                                     │
┌─────────────────┐                  │ N:1
│   notifications │                  │
├─────────────────┤                  │
│ id (PK)         │                  │
│ notification_type◄──────────────────┘
│ recipient_type │
│ department    │
│ severity     │         ┌───────────────────────┐
│ is_sent      │         │  burnout_assessments  │
│ created_at  │         ├───────────────────────┤
└─────────────────┘         │ id (PK)             │
                             │ chat_id (FK)        │
                             │ emotional_exhaustion │
                             │ depersonalization  │
                             │ personal_achievement│
                             │ burnout_level      │
                             │ burnout_score    │
                             │ period_date     │
                             └───────────────────────┘
                                     │
                                     │
                             ┌───────────────────────┐
                             │    audit_logs         │
                             ├───────────────────────┤
                             │ id (PK)              │
                             │ event_type            │
                             │ user_id              │
                             │ action               │
                             │ resource_type        │
                             │ details (JSON)       │
                             │ created_at           │
                             └───────────────────────┘
```

### 3.5 Сервисы доступа к данным

#### 3.5.1 ChatService

Сервис `ChatService` обеспечивает операции с чатами:

```python
class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_chat(self, chat_id: int, chat_type: str, title: str = None) -> Chat:
        # Поиск существующего чата
        result = await self.db.execute(
            select(Chat).where(Chat.chat_id == chat_id)
        )
        chat = result.scalar_one_or_none()
        
        # Создание нового чата при отсутствии
        if not chat:
            chat = Chat(
                chat_id=chat_id,
                chat_type=chat_type,
                title=title or f"Department_{chat_id}",
                is_monitored=True
            )
            self.db.add(chat)
            await self.db.commit()
            await self.db.refresh(chat)
            logger.info("chat_created", chat_id=chat_id, title=title)
        
        return chat
```

Принцип UPSERT: сначала выполняется поиск чата по `chat_id`, при отсутствии — создаётся новый с флагом `is_monitored=True`.

#### 3.5.2 MetricsService

Сервис `MetricsService` обеспечивает сохранение метрик:

```python
class MetricsService:
    async def save_sentiment_metrics(self, chat_id: int, sentiment_data: dict):
        # Получение или создание чата
        chat_result = await self.db.execute(
            select(Chat).where(Chat.chat_id == chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        
        if not chat:
            chat = await ChatService(self.db).get_or_create_chat(chat_id, "group")
        
        # Сохранение метрик тональности
        metrics = SentimentMetrics(
            chat_id=chat.id,
            positivity_score=sentiment_data.get("positivity_score", 0),
            negativity_score=sentiment_data.get("negativity_score", 0),
            neutrality_score=sentiment_data.get("neutrality_score", 0),
            cynicism_score=sentiment_data.get("cynicism_score", 0),
            apathy_score=sentiment_data.get("apathy_score", 0),
            irritability_score=sentiment_data.get("irritability_score", 0),
            devaluation_score=sentiment_data.get("devaluation_score", 0),
            complaint_score=sentiment_data.get("complaint_score", 0),
            period_date=date.today(),
            period_type="daily"
        )
        self.db.add(metrics)
        await self.db.commit()
```

#### 3.5.3 StatsService

Сервис `StatsService` обеспечивает получение статистики:

```python
class StatsService:
    async def get_chat_stats(self, chat_id: int) -> dict:
        # Запрос агрегированных данных тональности
        sentiment_result = await self.db.execute(
            select(
                func.avg(SentimentMetrics.positivity_score).label("avg_positivity"),
                func.avg(SentimentMetrics.negativity_score).label("avg_negativity"),
                func.avg(SentimentMetrics.cynicism_score).label("avg_cynicism"),
                func.avg(SentimentMetrics.apathy_score).label("avg_apathy"),
                func.avg(SentimentMetrics.complaint_score).label("avg_complaint"),
                func.count(SentimentMetrics.id).label("message_count")
            )
            .where(SentimentMetrics.chat_id == chat.id)
            .where(SentimentMetrics.period_date == date.today())
        )
        sentiment = sentiment_result.first()
        
        # Запрос агрегированных данных выгорания
        burnout_result = await self.db.execute(
            select(
                func.avg(BurnoutAssessment.burnout_score).label("avg_burnout"),
                func.max(BurnoutAssessment.burnout_level).label("max_level")
            )
            .where(BurnoutAssessment.chat_id == chat.id)
            .where(BurnoutAssessment.period_date == date.today())
        )
        burnout = burnout_result.first()
        
        return {
            "chat_id": chat_id,
            "title": chat.title,
            "message_count": sentiment.message_count if sentiment else 0,
            "burnout": {
                "avg_score": round(float(burnout.avg_burnout or 0), 1),
                "level": burnout.max_level or "normal"
            }
        }
```

Использование агрегатных ��ун��ций SQL (`func.avg`, `func.count`, `func.max`) обеспечивает эффективный расчёт статистики без загрузки отдельных записей.

---

## Глава 4. Развёртывание и конфигурация системы

### 4.1 Архитектура развёртывания

Система развёртывается в контейнеризованной среде Docker. Использование контейнеризации обеспечивает:

1. **Изоляция компонентов** — каждый сервис работает в отдельном контейнере
2. **Воспроизводимость** — идентичное окружение на всех этапах жизненного цикла
3. **Масштабируемость** — простое горизонтальное масштабирование
4. **Управление зависимостями** — автоматическое разрешение зависимостей

### 4.2 Состав контейнеров

Система использует следующие контейнеры:

| Контейнер | Образ | Назначение |
|-----------|------|------------|
| `telegram-bot` | python:3.11-slim | Приложение Telegram-бота |
| `nlp-service` | python:3.11-slim | NLP-сервис для анализа текста |
| `postgres` | postgres:15 | База данных PostgreSQL |

### 4.3 Compose-файл

Конфигурация развёртывания описывается в файле `compose.yaml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: sofia_burnout
      POSTGRES_USER: sofia_user
      POSTGRES_PASSWORD: sofia_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  nlp_service:
    build:
      context: ./nlp-service
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - NLP_API_PORT=8000
      - MODEL_NAME=cointegrated/rubert-tiny2
      - DEVICE=cpu
    depends_on:
      - postgres

  telegram_bot:
    build:
      context: ./telegram-bot
      dockerfile: Dockerfile
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - NLP_SERVICE_URL=http://nlp_service:8000
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=sofia_burnout
      - POSTGRES_USER=sofia_user
      - POSTGRES_PASSWORD=sofia_password
    depends_on:
      - postgres
      - nlp_service
    restart: unless-stopped

volumes:
  postgres_data:
```

### 4.4 Схема развёртывания

```
┌──────────────────────────────────────────────────────────────┐
│                      Host Machine                           │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Docker Network                    │    │
│  │                                                      │    │
│  │  ┌─────────────┐    ┌─────────────┐              │    │
│  │  │ telegram-  │    │  nlp-      │              │    │
│  │  │ bot        │◄───►│ service    │              │    │
│  │  │ (port 80)  │    │ (port 8000)│              │    │
│  │  └─────────────┘    └──────┬──────┘              │    │
│  │                           │                       │    │
│  │  ┌─────────────┐          │                       │    │
│  │  │ postgres    │◄────────┘                       │    │
│  │  │ (port 5432) │                                │    │
│  │  └─────────────┘                                 │    │
│  │                                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Telegram API ───────────────────────────────────────────►   │
│  (webhook или polling)                                          │
└──────────────────────────────────────────────────────────────┘
```

### 4.5 Конфигурация переменных окружения

#### 4.5.1 Обязательные переменные

| Переменная | Описание | Пример |
|-----------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота от @BotFather | `123456:ABC...` |

#### 4.5.2 Опциональные переменные NLP-сервиса

| Переменная | Описание | По умолчанию |
|-----------|----------|---------------|
| `NLP_API_PORT` | Порт API | `8000` |
| `MODEL_NAME` | Модель transformers | `cointegrated/rubert-tiny2` |
| `DEVICE` | Устройство для инференса | `cpu` |
| `HF_TOKEN` | Токен HuggingFace для закрытых моделей | — |

### 4.6 Запуск системы

#### 4.6.1 Предварительные требования

- Docker и Docker Compose установлены
- Токен Telegram-бота получен от @BotFather

#### 4.6.2 Процедура запуска

1. Создать `.env` файл в корне проекта:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```

2. Собрать и запустить контейнеры:
   ```bash
   docker-compose up -d --build
   ```

3. Проверить статус контейнеров:
   ```bash
   docker-compose ps
   ```

4. Проверить логи:
   ```bash
   docker-compose logs -f telegram_bot
   ```

#### 4.6.3 Проверка работоспособности

После запуска необходимо:

1. Открыть чат с ботом в Telegram
2. Отправить команду `/start`
3. Подтвердить согласие на обработку
4. Добавить бота в групповой чат
5. Отправить тестовое сообщение
6. Проверить сохранение метрик в БД

### 4.7 Схема сетевого взаимодействия

```
┌─────────────────┐      HTTP       ┌─────────────────┐
│                 │                 │                 │
│  Telegram Bot   │────────────────►│   NLP Service   │
│  Client         │◄────────────────│   (FastAPI)     │
│                 │    /api/v1/...  │                 │
└─────────────────┘                 └────────┬────────┘
                                           │
                                           │
                                  ┌────────▼────────┐
                                  │                │
                                  │  PostgreSQL    │
                                  │  (port 5432)  │
                                  │                │
                                  └────────────────┘
```

---

## Глава 5. Метрики и анализ результатов

### 5.1 Структура метрик

Система рассчитывает и хранит следующие категории метрик:

#### 5.1.1 Метрики тональности

| Метрика | Диапазон | Описание |
|---------|----------|----------|
| `positivity_score` | [0, 1] | Доля позитивной тональности |
| `negativity_score` | [0, 1] | Доля негативной тональности |
| `neutrality_score` | [0, 1] | Доля нейтральной тональности |
| `cynicism_score` | [0, 1] | Маркер циничного отношения |
| `apathy_score` | [0, 1] | Маркер апатии |
| `irritability_score` | [0, 1] | Маркер раздражительности |
| `devaluation_score` | [0, 1] | Маркер обесценивания |
| `complaint_score` | [0, 1] | Маркер жалоб |

#### 5.1.2 Метрики выгорания

| Метрика | Диапазон | Описание |
|---------|----------|----------|
| `burnout_score` | [0, 100] | Интегральный показатель |
| `emotional_exhaustion` | [0, 100] | Эмоциональное истощение |
| `depersonalization` | [0, 100] | Деперсонализация |
| `personal_achievement` | [0, 100] | Личные достижения |
| `burnout_level` | enum | Категория уровня |

### 5.2 Расчёт трендов

#### 5.2.1 Метод расчёта

Для анализа динамики изменения уровня выгорания используется сравнение средних значений за два периода:

```
АЛГОРИТМ: Расчёт тренда
─────────────────────────────────────
ВХОД: chat_id
ВЫХОД: { trend, change_percent, direction }

1. Определить периоды:
   - current_period: [сегодня - 7 дней, сегодня]
   - previous_period: [сегодня - 14 дней, сегодня - 7 дней]

2. Рассчитать среднее значение за текущий период:
   avg_current = AVG(burnout_score)
   WHERE chat_id = chat_id
   AND period_date >= current_period_start

3. Рассчитать среднее значение за предыдущий период:
   avg_previous = AVG(burnout_score)
   WHERE chat_id = chat_id
   AND period_date >= previous_period_start
   AND period_date < current_period_start

4. Рассчитать процент изменения:
   change_percent = ((avg_current - avg_previous) / avg_previous) * 100

5. Определить направление:
   ЕСЛИ change_percent > 10 THEN
       trend = "worsening"
       direction = "↗"
   ИНАЧЕ ЕСЛИ change_percent < -10 THEN
       trend = "improving"
       direction = "↘"
   ИНАЧЕ
       trend = "stable"
       direction = "➡"

6. ВЕРНУТЬ результат
КОНЕЦ АЛГОРИТМА
```

#### 5.2.2 Интерпретация трендов

| Тренд | Изменение | Определение |
|--------|------------|--------------|
| ↗ worsening | > +10% | Ухудшение состояния |
| ↘ improving | < -10% | Улучшение состояния |
| ➡ stable | ±10% | Стабильное состояние |

### 5.3 Визуализация истории

#### 5.3.1 Форматиро��ан��е столбчатой диаграммы

Для отображения истории используется ASCII-диаграмма:

```python
def _make_bar(value: float, max_value: float = 100, width: int = 10) -> str:
    filled = int((value / max_value) * width)
    filled = max(0, min(width, filled))
    return "▓" * filled + "░" * (width - filled)
```

#### 5.3.2 Пример визуализации

Пример отображения истории за 7 дней:

```
История:
Пн: ▓▓▓▓▓▓▓░░░ 45%
Вт: ▓▓▓▓▓▓░░░░ 40%
Ср: ▓▓▓▓▓░░░░░ 35%
Чт: ▓▓▓▓▓▓▓░░░ 45%
Пт: ▓▓▓▓▓▓▓▓░░ 50%
Сб: ░░░░░░░░░░ ▬▬%
Вс: ░░░░░░░░░░ ▬▬%
```

### 5.4 Агрегация по подразделениям

#### 5.4.1 Принцип агрегации

Каждый групповой чат в Telegram рассматривается как отдельное подразделение. Метрики агрегируются по `chat_id`, что позволяет:

1. Анализировать состояние каждого подразделения отдельно
2. Сравнивать подразделения между собой
3. Отслеживать динамику изменений

#### 5.4.2 Формирование отчёта

```
ОТЧЁТ: Статистика по подразделениям
─────────────────────────────────────────
Наименование    │ Сообщений │ Выгорание  │ Уровень    │ Тренд
─────────────────┼────────────┼────────────┼────────────┼────────
Отдел разработки │ 47         │ 32.5%      │ initial    │ ↗ +5%
Отдел маркетинга│ 23         │ 18.2%      │ normal     │ ➡ 0%
Бухгалтерия     │ 15         │ 58.3%      │ moderate   │ ↗ +12%
```

### 5.5 Интерпретация результатов

#### 5.5.1 Уровни выгорания и рекомендации

| Уровень | Интерпретация | Действия HR |
|---------|--------------|-------------|
| Normal | Эмоциональное состояние в норме | Регулярный мониторинг |
| Initial | Первые признаки стресса | Профилактические беседы, внимание к нагрузке |
| Moderate | Выраженное эмоциональное истощение | Индивидуальные консультации, пересмотр условий |
| High | Критическое состояние | Экстренное вмешательство, возможный отпуск |

#### 5.5.2 Граничные значения

Рекомендуемые пороговые значения для формирования уведомлений:

| Метрика | Внимание | Тревога |
|---------|----------|---------|
| burnout_score | > 30% | > 60% |
| change_percent (7 дней) | > +15% | > +25% |

---

## Глава 6. Выводы и рекомендации

### 6.1 Достигнутые результаты

В ходе разработки автоматизированного модуля для анализа степени выгорания сотрудников были достигнуты следующие результаты:

1. **Создание архитектуры системы** — разработана микросервисная архитектура с разделением на клиентскую (Telegram-бот) и ��ер��ерную (NLP-сервис) части.

2. **Реализация анализа тональности** — разработан модуль анализа текстовых сообщений с использованием комбинированного подхода (key-word + transformer).

3. **Оценка выгорания** — реализована модель расчёта интегрального показателя burnout на основе адаптированной модели Маслач.

4. **Персистентное хранение** — развёрнута система хранения метрик в PostgreSQL с использованием ORM SQLAlchemy.

5. **Визуализация результатов** — реализован вывод статистики с трендами и историей изменений в текстовом формате.

### 6.2 Ограничения системы

Разработанная система имеет ряд ограничений:

1. **Ограниченный анализ контекста** — key-word анализ не учитывает контекст употребления слов, что может приводить к ложным срабатываниям.

2. **Отсутствие механизма реального времени** — синхронные HTTP-запросы блокируют обработку; рекомендуется переход на async-клиент.

3. **Простая модель выгорания** — используется упрощённая весовая модель; для production-решений рекомендуется обучение классификатора на размеченных данных.

4. **Отсутствие механизма оповещений** — модуль уведомлений реализован только на уровне модели БД; требуется интеграция с каналами оповещений.

5. **Зависимость от Telegram** — система привязана к экосистеме Telegram; для кросс-платформенного решения требуется расширение каналов коммуникации.

### 6.3 Пути развития

#### 6.3.1 Краткосрочные улучшения

| Направление | Описание |
|------------|----------|
| Async-NLP клиент | Переход на httpx.AsyncClient для асинхронной обработки |
| Кэширование | Добавление Redis для кэширования результатов анализа |
| Rate limiting | Ограничение частоты запросов для предотвращения перегрузки |
| Логирование | Расширенное логирование для отладки |

#### 6.3.2 Среднесрочные улучшения

| Направление | Описание |
|------------|----------|
| Обученная модель | Обучение классификатора выгорания на корпоративных данных |
| Мониторинг активности | Анализ паттернов активности (время сообщений, частота) |
| Уведомления | Интеграция с email/Slack для отправки алертов |
| Dashboard | Веб-интерфейс для визуализации |

#### 6.3.3 Долгосрочные улучшения

| Направление | Описание |
|------------|----------|
| ML Pipeline | Автоматическое переобучение модели на новых данных |
| Интеграция с HRM | Экспорт данных в системы управления персоналом |
| Прогнозирование | Модель предсказания выгорания |
| Анонимизация | Полная анонимизация персональных данных |

### 6.4 Рекомендации для HR

При внедрении системы в корпоративную среду рекомендуется:

1. **Формализовать процесс** — разработать процедуры реагирования на алерты различных уровней.

2. **Обеспечить конфиденциальность** — чётко определить политику доступа к данным на уровне подразделений.

3. **Коммуницировать цели** — информировать сотрудников о целях мониторинга для повышения вовлечённости.

4. **Комбинировать с другими методами** — использовать систему совместно с регулярными опросами и анкетированием.

5. **Итеративно улучшать** — накапливать данные и корректировать пороговые значения.

---

## Заключение

Разработанный автоматизированный модуль представляет собой основу для системы мониторинга эмоционального благополучия сотрудников. Система требует дальнейшего развития и адаптации под конкретные потребности организации, однако базовая функциональность позволяет проводить анализ тональности корпоративных коммуникаций и оценивать риски эмоционального выгорания.

---

*Дата создания: 2026*
*Версия документа: 1.0*