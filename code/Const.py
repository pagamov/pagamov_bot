from typing import Final
import os
from dotenv import load_dotenv

# Загрузка файла .env
load_dotenv()

# Паша если сольешь токен опять - обещаю перестать писать ботов для ВКР
TOKEN : Final = os.getenv("TOKEN")

# Означает, будет ли модуль Logger выводить данные не только в БД но еще и в консоль
LOGGER_VERBOSE : Final = True

# Столько char может быть максимум в одном текстовом сообщении в телеграме
TELEGRAM_MAX_MESSAGE_SIZE : Final = 4096