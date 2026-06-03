import sqlite3
import os
import random
import re
import json
import base64
from datetime import datetime, timedelta
from enum import Enum
from dotenv import load_dotenv

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters, CallbackQueryHandler, JobQueue
)

load_dotenv()

TOKEN = os.getenv("TOKEN")
ENCRYPTION_PASSWORD = os.getenv("ENCRYPTION_PASSWORD", "default_change_me_32bytes!")
db_path = os.path.join(os.path.dirname(__file__), 'db', 'main.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

PROGRAMS_FILE = os.path.join(os.path.dirname(__file__), 'programs.json')
SALT = b'\x9b\x1c\xd5\xe7\xa3\xf4\x2b\x8c\x6d\x1e\xf0\xa1\xc3\x7d\x4e\x5f'


class CryptoService:
    def __init__(self, password):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SALT,
            iterations=100000,
            backend=default_backend()
        )
        self.key = kdf.derive(password.encode())

    def encrypt(self, plaintext):
        if not plaintext:
            return plaintext
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return base64.b64encode(iv + encryptor.tag + ciphertext).decode()

    def decrypt(self, ciphertext_b64):
        if not ciphertext_b64 or ciphertext_b64.startswith(('http', ' ', 'П', 'М', 'В', 'Д', 'До', 'Вы', 'На')):
            return ciphertext_b64
        try:
            raw = base64.b64decode(ciphertext_b64)
            iv, tag, ciphertext = raw[:12], raw[12:28], raw[28:]
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return (decryptor.update(ciphertext) + decryptor.finalize()).decode()
        except Exception:
            return ciphertext_b64


class State(Enum):
    MAIN_MENU = 1
    HABBIT_MENU = 2
    ADD_HABIT_DESCRIPTION = 3
    ADD_HABIT_FREQUENCY = 4
    ADD_HABIT_TIME = 5
    DELETE_HABIT = 6
    NOTIFY_MENU = 7
    ADD_NOTIFY_TEXT = 8
    ADD_NOTIFY_DATE = 9
    ADD_NOTIFY_TIME = 10
    DELETE_NOTIFY = 11
    UNSUBSCRIBE_HABIT = 12
    PROGRAMM_MENU = 13
    PROGRAMM_SELECT = 14
    PROGRAMM_UNSUB = 15
    ABOUT_ME_MENU = 16
    BADGES = 17
    MENTOR_MENU = 18
    MENTOR_CHAT = 19
    CHANGE_NICK = 20


class Text:
    MAIN_MENU_KEYBOARD = ["Напоминания", "Мои привычки", "Готовые программы", "Обо мне"]
    HABBIT_MENU_KEYBOARD = ["Мои привычки", "Добавить", "Отписаться", "Назад"]
    NOTE_MENU_KEYBOARD = ["Мои напоминания", "Добавить", "Удалить", "Назад"]
    PROGRAMM_MENU_KEYBOARD = ["Мои программы", "Подписаться", "Отписаться", "Назад"]
    FREQUENCY_KEYBOARD = ["Ежедневно", "Еженедельно"]
    ABOUT_ME_KEYBOARD = ["Мои достижения", "Анонимный наставник", "Сменить ник", "Назад"]
    MENTOR_MENU_KEYBOARD = ["Найти наставника", "Завершить", "Назад"]
    BADGES_KEYBOARD = ["Полученные", "Не полученные", "Назад"]

    RETURN_TO_MENU = "Возвращаемся в главное меню"
    NO_HABITS = "У вас пока нет привычек."
    ENTER_DESCRIPTION = "Введите описание привычки:"
    ENTER_FREQUENCY = "Выберите частоту:"
    ENTER_TIME = "Введите время (ЧЧ:ММ):"
    INVALID_FREQUENCY = "Пожалуйста, выберите из кнопок."
    INVALID_TIME = "Пожалуйста, введите время в формате ЧЧ:ММ"
    HABIT_ADDED = "Привычка успешно добавлена!"
    HABIT_DELETED = "Привычка удалена!"
    HABIT_UNSUBSCRIBED = "Вы отписались от привычки!"
    NO_HABITS_TO_DELETE = "У вас нет привычек."
    SELECT_DELETE = "Выберите привычку для удаления:\n\n"
    SELECT_UNSUBSCRIBE = "Выберите привычку для отписки:\n\n"
    ENTER_NUMBER = "\nВведите номер:"
    INVALID_NUMBER = "Неверный номер."
    ENTER_NUMBER_VALID = "Пожалуйста, введите номер."
    USER_NOT_FOUND = "Ошибка: пользователь не найден."
    YOUR_HABITS = "Ваши привычки:\n\n"
    HABIT_ITEM = "{}. {} ({})\n   Время: {}\n"
    COMING_SOON = "Этот раздел скоро будет доступен!"

    ENTER_NOTIFY_TEXT = "Введите текст напоминания:"
    ENTER_NOTIFY_DATE = "Введите дату (ДД.ММ.ГГГГ):"
    ENTER_NOTIFY_TIME = "Введите время (ЧЧ:ММ):"
    INVALID_DATE = "Пожалуйста, введите дату в формате ДД.ММ.ГГГГ"
    DATE_PASSED = "Дата уже прошла. Введите будущую дату."
    NOTIFY_ADDED = "Напоминание добавлено!"
    NO_NOTIFIES = "У вас пока нет напоминаний."
    YOUR_NOTIFIES = "Ваши напоминания:\n\n"
    SELECT_NOTIFY_DELETE = "Выберите напоминание для удаления:\n\n"
    NO_NOTIFIES_TO_DELETE = "У вас нет напоминаний для удаления."
    NOTIFY_DELETED = "Напоминание удалено!"
    REMINDER_TEXT = "Напоминание:"

    NO_PROGRAMS = "У вас пока нет активных программ."
    YOUR_PROGRAMS = "Ваши программы:\n\n"
    PROGRAM_ITEM = "{}. {} ({})\n   Время: {}\n"
    SELECT_PROGRAM = "Выберите программу для подписки:\n\n"
    PROGRAM_ADDED = "Вы подписались на программу!"
    NO_PROGRAMS_TO_UNSUB = "У вас нет активных программ."
    SELECT_PROGRAM_UNSUB = "Выберите программу для отписки:\n\n"
    PROGRAM_UNSUBSCRIBED = "Вы отписались от программы!"
    PROGRAM_FROM_FILE = " "

    NICK_CHANGED = "Ник успешно изменен!"
    ABOUT_ME_MENU = "Личный кабинет"
    BADGES_MENU = "Меню достижений"
    ACHIEVEMENTS_HEADER = "Ваши достижения:\n\n"

    MENTOR_QUEUE = "Вы встали в очередь поиска наставника..."
    MENTOR_FOUND = "Наставник найден!\n\nВы общаетесь с анонимным наставником. Все сообщения анонимны."
    MENTOR_ENDED = "Беседа завершена."
    MENTOR_REPORT_SENT = "Жалоба отправлена. Мы рассмотрим её."
    MENTOR_ALREADY = "Вы уже в беседе. Завершите её сначала."
    MENTOR_NOT_ACTIVE = "У вас нет активной беседы."
    MENTOR_SEARCH = "Поиск наставника..."
    MENTOR_PARTNER = "Ваш собеседник вышел из чата."
    MENTOR_INFO = "Вы общаетесь анонимно. Ваш ник: {}\nСобеседник: {}"

    HABIT_REMINDER_VARIANTS_MORNING = [
        "☀️ Доброе утро! Самое время начать день с полезной привычки!",
        "🌅 Утро начинается с заботы о себе!",
        "🌤 Просыпайтесь и сияйте! Не забудьте о привычке!",
    ]
    HABIT_REMINDER_VARIANTS_DAY = [
        "⏰ Время для привычки!",
        "📋 Не забывайте о своей цели!",
        "💪 Продолжайте в том же духе!",
    ]
    HABIT_REMINDER_VARIANTS_EVENING = [
        "🌆 Вечер — отличное время, чтобы завершить дела!",
        "🌇 День подходит к концу, но у вас есть время!",
        "🌟 Вечернее напоминание о важном!",
    ]
    HABIT_REMINDER_VARIANTS_NIGHT = [
        "🌙 Перед сном не забудьте о привычке!",
        "⭐ Даже поздним вечером стоит уделить время себе!",
        "🌜 Тихий вечер — время для полезных ритуалов!",
    ]

    BADGE_EARNED = "Поздравляем! Вы получили новое достижение!"
    BADGE_LINE = "{} — {}"


class Keyboard:
    @staticmethod
    def get_main_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MAIN_MENU_KEYBOARD[0])],
            [KeyboardButton(Text.MAIN_MENU_KEYBOARD[1]), KeyboardButton(Text.MAIN_MENU_KEYBOARD[2])],
            [KeyboardButton(Text.MAIN_MENU_KEYBOARD[3])]
        ], resize_keyboard=True)

    @staticmethod
    def get_habbit_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.HABBIT_MENU_KEYBOARD[0]), KeyboardButton(Text.HABBIT_MENU_KEYBOARD[1])],
            [KeyboardButton(Text.HABBIT_MENU_KEYBOARD[2]), KeyboardButton(Text.HABBIT_MENU_KEYBOARD[3])]
        ], resize_keyboard=True)

    @staticmethod
    def get_note_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.NOTE_MENU_KEYBOARD[0]), KeyboardButton(Text.NOTE_MENU_KEYBOARD[1])],
            [KeyboardButton(Text.NOTE_MENU_KEYBOARD[2]), KeyboardButton(Text.NOTE_MENU_KEYBOARD[3])]
        ], resize_keyboard=True)

    @staticmethod
    def get_frequency_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.FREQUENCY_KEYBOARD[0]), KeyboardButton(Text.FREQUENCY_KEYBOARD[1])]
        ], resize_keyboard=True)

    @staticmethod
    def get_programm_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[0]), KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[1])],
            [KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[2]), KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[3])]
        ], resize_keyboard=True)

    @staticmethod
    def get_about_me_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.ABOUT_ME_KEYBOARD[0])],
            [KeyboardButton(Text.ABOUT_ME_KEYBOARD[1]), KeyboardButton(Text.ABOUT_ME_KEYBOARD[2])],
            [KeyboardButton(Text.ABOUT_ME_KEYBOARD[3])]
        ], resize_keyboard=True)

    @staticmethod
    def get_mentor_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MENTOR_MENU_KEYBOARD[0])],
            [KeyboardButton(Text.MENTOR_MENU_KEYBOARD[1]), KeyboardButton(Text.MENTOR_MENU_KEYBOARD[2])]
        ], resize_keyboard=True)

    @staticmethod
    def get_reminder_keyboard(notify_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Выполнено", callback_data=f"done_notify_{notify_id}"),
             InlineKeyboardButton("+1 час", callback_data=f"postpone1h_notify_{notify_id}")]
        ])

    @staticmethod
    def get_habit_keyboard(habit_id, is_program=False):
        prefix = "prog" if is_program else "habit"
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Выполнено", callback_data=f"done_{prefix}_{habit_id}"),
             InlineKeyboardButton("+15 мин", callback_data=f"postpone15m_{prefix}_{habit_id}"),
             InlineKeyboardButton("+1 час", callback_data=f"postpone1h_{prefix}_{habit_id}")]
        ])

    @staticmethod
    def get_mentor_chat_keyboard():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Пожаловаться", callback_data="mentor_report"),
             InlineKeyboardButton("Завершить", callback_data="mentor_end")]
        ])

    @staticmethod
    def get_badges_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.BADGES_KEYBOARD[0])],
            [KeyboardButton(Text.BADGES_KEYBOARD[1]), KeyboardButton(Text.BADGES_KEYBOARD[2])]
        ], resize_keyboard=True)


def load_programs_from_json():
    if os.path.exists(PROGRAMS_FILE):
        with open(PROGRAMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


class Database:
    def __init__(self):
        self.path = db_path

    def get_connection(self):
        return sqlite3.connect(self.path)

    def execute_query(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor

    def fetch_all(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def fetch_one(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()

    def initialize_database(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_username TEXT UNIQUE NOT NULL,
                bot_username TEXT,
                chat_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                description TEXT NOT NULL,
                frequency_type TEXT NOT NULL,
                time_of_day TEXT NOT NULL,
                start_date TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_program INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS habit_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                user_id INTEGER,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(habit_id) REFERENCES habits(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER,
                description TEXT NOT NULL,
                time_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_notify TIMESTAMP NOT NULL,
                sent INTEGER DEFAULT 0,
                done INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS program_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                program_id TEXT NOT NULL,
                description TEXT NOT NULL,
                frequency_type TEXT NOT NULL,
                time_of_day TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS program_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id INTEGER,
                user_id INTEGER,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(subscription_id) REFERENCES program_subscriptions(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                icon TEXT NOT NULL,
                badge_type TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                condition_value INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                badge_id INTEGER NOT NULL,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(badge_id) REFERENCES badges(id),
                UNIQUE(user_id, badge_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                total_completions INTEGER DEFAULT 0,
                total_habits_created INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                last_completion_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS mentor_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY(user1_id) REFERENCES users(id),
                FOREIGN KEY(user2_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_user_id INTEGER NOT NULL,
                reported_user_id INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(reporter_user_id) REFERENCES users(id),
                FOREIGN KEY(reported_user_id) REFERENCES users(id)
            )
            """
        ]
        for query in queries:
            self.execute_query(query)


class UserService:
    def __init__(self, database):
        self.db = database

    def create_user(self, tg_username):
        bot_username = self.generate_bot_username()
        query = "INSERT OR IGNORE INTO users (tg_username, bot_username) VALUES (?, ?)"
        self.db.execute_query(query, (tg_username, bot_username))
        user = self.get_user_by_tg_username(tg_username)
        if user:
            self.db.execute_query(
                "INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)",
                (user[0],)
            )
        return bot_username

    def generate_bot_username(self):
        adjectives = ["Удачливый", "Смелый", "Весёлый", "Храбрый", "Гениальный",
                     "Остроумный", "Талантливый", "Умный", "Забавный", "Быстрый",
                     "Честный", "Осторожный", "Решительный", "Проницательный",
                     "Верный", "Любимый", "Дерзкий", "Очаровательный", "Щедрый",
                     "Находчивый", "Спокойный", "Энергичный", "Креативный", "Искренний"]
        animals = ['слон', 'тигр', 'медведь', 'лев', 'крокодил',
                  'голубь', 'жираф', 'верблюд', 'броненосец', 'кот',
                  'заяц', 'волк', 'лиса', 'сова', 'дельфин']
        digits = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        return f"{random.choice(adjectives)}_{random.choice(animals)}_{digits}"

    def regenerate_bot_username(self):
        return self.generate_bot_username()

    def get_user_by_tg_username(self, tg_username):
        query = "SELECT * FROM users WHERE tg_username = ?"
        return self.db.fetch_one(query, (tg_username,))

    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id = ?"
        return self.db.fetch_one(query, (user_id,))

    def update_bot_username(self, tg_username, new_username):
        query = "UPDATE users SET bot_username = ? WHERE tg_username = ?"
        self.db.execute_query(query, (new_username, tg_username))

    def get_bot_username(self, tg_username):
        user = self.get_user_by_tg_username(tg_username)
        return user[2] if user else None

    def update_chat_id(self, user_id, chat_id):
        query = "UPDATE users SET chat_id = ? WHERE id = ?"
        self.db.execute_query(query, (chat_id, user_id))

    def get_chat_id(self, user_id):
        query = "SELECT chat_id FROM users WHERE id = ?"
        result = self.db.fetch_one(query, (user_id,))
        return result[0] if result else None


class HabitService:
    def __init__(self, database, crypto):
        self.db = database
        self.crypto = crypto

    def create_habit(self, user_id, description, frequency_type, time_of_day, start_date, is_program=0):
        encrypted_desc = self.crypto.encrypt(description)
        query = """
        INSERT INTO habits (user_id, description, frequency_type, time_of_day, start_date, is_program)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = self.db.execute_query(query, (user_id, encrypted_desc, frequency_type, time_of_day, start_date, is_program))
        return cursor.lastrowid

    def get_user_habits(self, user_id, include_programs=False):
        if include_programs:
            query = """
            SELECT id, description, frequency_type, time_of_day, start_date, is_program
            FROM habits WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
            """
        else:
            query = """
            SELECT id, description, frequency_type, time_of_day, start_date, is_program
            FROM habits WHERE user_id = ? AND is_active = 1 AND is_program = 0
            ORDER BY created_at DESC
            """
        rows = self.db.fetch_all(query, (user_id,))
        result = []
        for row in rows:
            row = list(row)
            row[1] = self.crypto.decrypt(row[1])
            result.append(tuple(row))
        return result

    def delete_habit(self, habit_id):
        query = "UPDATE habits SET is_active = 0 WHERE id = ?"
        self.db.execute_query(query, (habit_id,))

    def get_active_habits_for_sending(self, user_id):
        return self.db.fetch_all(
            "SELECT id, description, frequency_type, time_of_day, user_id FROM habits WHERE user_id = ? AND is_active = 1 AND is_program = 0",
            (user_id,)
        )

    def get_habit_description(self, habit_id):
        row = self.db.fetch_one("SELECT description FROM habits WHERE id = ?", (habit_id,))
        return self.crypto.decrypt(row[0]) if row else ""


class HabitProgressService:
    def __init__(self, database):
        self.db = database

    def mark_progress(self, habit_id, user_id, date, status):
        existing = self.get_today_progress(habit_id, user_id, date)
        if existing:
            self.update_progress(existing[0], status)
            return existing[0]
        query = "INSERT INTO habit_progress (habit_id, user_id, date, status) VALUES (?, ?, ?, ?)"
        self.db.execute_query(query, (habit_id, user_id, date, status))
        return self.db.fetch_one("SELECT last_insert_rowid()")[0]

    def get_today_progress(self, habit_id, user_id, date):
        return self.db.fetch_one(
            "SELECT * FROM habit_progress WHERE habit_id = ? AND date = ?",
            (habit_id, date)
        )

    def update_progress(self, progress_id, status):
        self.db.execute_query("UPDATE habit_progress SET status = ? WHERE id = ?", (status, progress_id))

    def count_habit_completions(self, user_id, keyword=None):
        if keyword:
            return self.db.fetch_one(
                """SELECT COUNT(*) FROM habit_progress hp
                   JOIN habits h ON hp.habit_id = h.id
                   WHERE hp.user_id = ? AND hp.status = 'done'
                   AND h.is_active = 1 AND LOWER(h.description) LIKE ?""",
                (user_id, f"%{keyword}%")
            )[0]
        return self.db.fetch_one(
            "SELECT COUNT(*) FROM habit_progress WHERE user_id = ? AND status = 'done'",
            (user_id,)
        )[0]

    def count_program_completions(self, user_id):
        return self.db.fetch_one(
            "SELECT COUNT(*) FROM program_progress WHERE user_id = ? AND status = 'done'",
            (user_id,)
        )[0]


class NotifyService:
    def __init__(self, database):
        self.db = database

    def create_notify(self, chat_id, user_id, description, time_notify):
        cursor = self.db.execute_query(
            "INSERT INTO notifications (chat_id, user_id, description, time_notify) VALUES (?, ?, ?, ?)",
            (chat_id, user_id, description, time_notify)
        )
        return cursor.lastrowid

    def get_pending_notifications(self, current_time):
        return self.db.fetch_all(
            "SELECT id, chat_id, description, time_notify FROM notifications WHERE done = 0 AND sent = 0 AND time_notify <= ?",
            (current_time,)
        )

    def mark_as_sent(self, notify_id):
        self.db.execute_query("UPDATE notifications SET sent = 1 WHERE id = ?", (notify_id,))

    def postpone_notification(self, notify_id, new_time):
        self.db.execute_query("UPDATE notifications SET time_notify = ?, sent = 0 WHERE id = ?", (new_time, notify_id))

    def mark_as_done(self, notify_id):
        self.db.execute_query("UPDATE notifications SET done = 1, sent = 1 WHERE id = ?", (notify_id,))

    def get_user_notifications(self, user_id):
        return self.db.fetch_all(
            "SELECT id, description, time_notify, done, sent FROM notifications WHERE user_id = ? AND done = 0 ORDER BY time_notify ASC",
            (user_id,)
        )

    def delete_notification(self, notify_id):
        self.db.execute_query("DELETE FROM notifications WHERE id = ?", (notify_id,))


class ProgramService:
    def __init__(self, database):
        self.db = database
        self.programs = self.load_programs()

    def load_programs(self):
        programs = [
            {"id": "water_twice", "description": "Пить воду дважды в день", "frequency_type": "ежедневно", "time_of_day": "09:00", "is_file": False},
            {"id": "morning_exercise", "description": "Зарядка по утрам", "frequency_type": "ежедневно", "time_of_day": "07:00", "is_file": False},
            {"id": "water_flowers", "description": "Поливать цветы", "frequency_type": "еженедельно", "time_of_day": "19:00", "days": ["понедельник", "четверг"], "is_file": False}
        ]
        file_progs = load_programs_from_json()
        for p in file_progs:
            p["is_file"] = True
        programs.extend(file_progs)
        return programs

    def get_programs(self):
        return self.programs

    def subscribe(self, user_id, program_id):
        for p in self.programs:
            if p["id"] == program_id:
                self.db.execute_query(
                    "INSERT INTO program_subscriptions (user_id, program_id, description, frequency_type, time_of_day) VALUES (?, ?, ?, ?, ?)",
                    (user_id, program_id, p["description"], p["frequency_type"], p["time_of_day"])
                )
                return True
        return False

    def get_user_subscriptions(self, user_id):
        return self.db.fetch_all(
            "SELECT id, program_id, description, frequency_type, time_of_day FROM program_subscriptions WHERE user_id = ? AND is_active = 1",
            (user_id,)
        )

    def unsubscribe(self, subscription_id):
        self.db.execute_query("UPDATE program_subscriptions SET is_active = 0 WHERE id = ?", (subscription_id,))


class StatsService:
    def __init__(self, database):
        self.db = database

    def get_or_create(self, user_id):
        row = self.db.fetch_one("SELECT * FROM user_stats WHERE user_id = ?", (user_id,))
        if not row:
            self.db.execute_query("INSERT INTO user_stats (user_id) VALUES (?)", (user_id,))
            return {"total_completions": 0, "total_habits_created": 0, "current_streak": 0, "max_streak": 0, "last_completion_date": None}
        return {"total_completions": row[2], "total_habits_created": row[3], "current_streak": row[4], "max_streak": row[5], "last_completion_date": row[6]}

    def increment_completions(self, user_id):
        stats = self.get_or_create(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        streak = stats["current_streak"]
        if stats["last_completion_date"] == today:
            pass
        elif stats["last_completion_date"] == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
            streak += 1
        else:
            streak = 1
        max_streak = max(streak, stats["max_streak"])
        total = stats["total_completions"] + 1
        self.db.execute_query(
            "UPDATE user_stats SET total_completions = ?, current_streak = ?, max_streak = ?, last_completion_date = ? WHERE user_id = ?",
            (total, streak, max_streak, today, user_id)
        )
        return {"total_completions": total, "current_streak": streak, "max_streak": max_streak}

    def increment_habits_created(self, user_id):
        stats = self.get_or_create(user_id)
        total = stats["total_habits_created"] + 1
        self.db.execute_query("UPDATE user_stats SET total_habits_created = ? WHERE user_id = ?", (total, user_id))
        return total


class BadgeService:
    def __init__(self, database):
        self.db = database

    def seed_badges(self):
        badges = [
            ("Гидра", "Выполнить привычку 'Пить воду' 7 раз", "", "коллекционное", "habit_water", 7),
            ("Ранняя пташка", "Выполнить любую привычку до 7 утра", "", "коллекционное", "early_bird", 1),
            ("Книжный червь", "Создать привычку для чтения", "", "коллекционное", "habit_read", 1),
            ("Дзен", "Выполнить 'Медитация' 7 раз", "", "коллекционное", "habit_meditation", 7),
            ("Силач", "Выполнить 'Зарядка' 7 раз", "", "коллекционное", "habit_exercise", 7),
            ("Зелный росток", "Создать 3 привычки", "", "коллекционное", "habits_created", 3),
            ("Стрела", "Достичь серии 7 дней", "", "коллекционное", "max_streak", 7),
            ("Железо", "Достичь серии 21 день", "", "коллекционное", "max_streak", 21),
            ("Марафонец", "Выполнить 50 привычек", "", "коллекционное", "total_completions", 50),
            ("Легенда", "Выполнить 100 привычек", "", "коллекционное", "total_completions", 100),
            ("Первый шаг", "Первое выполнение привычки", "", "прогрессивное", "total_completions", 1),
            ("Новичок", "10 выполненных привычек", "", "прогрессивное", "total_completions", 10),
            ("Труженик", "25 выполненных привычек", "", "прогрессивное", "total_completions", 25),
            ("Энергичный", "50 выполненных привычек", "", "прогрессивное", "total_completions", 50),
            ("Выносливый", "75 выполненных привычек", "", "прогрессивное", "total_completions", 75),
            ("Сильный", "100 выполненных привычек", "", "прогрессивное", "total_completions", 100),
            ("Стратег", "150 выполненных привычек", "", "прогрессивное", "total_completions", 150),
            ("Непоколебимый", "200 выполненных привычек", "", "прогрессивное", "total_completions", 200),
            ("Мастер привычек", "350 выполненных привычек", "", "прогрессивное", "total_completions", 350),
            ("Бессмертный", "500 выполненных привычек", "", "прогрессивное", "total_completions", 500),
        ]
        for name, desc, icon, btype, ctype, cval in badges:
            self.db.execute_query(
                "INSERT OR IGNORE INTO badges (name, description, icon, badge_type, condition_type, condition_value) VALUES (?, ?, ?, ?, ?, ?)",
                (name, desc, icon, btype, ctype, cval)
            )

    def check_and_award(self, user_id, condition_type, condition_value):
        potential = self.db.fetch_all(
            """SELECT id, name, description FROM badges
               WHERE condition_type = ? AND condition_value <= ?
               AND id NOT IN (SELECT badge_id FROM user_badges WHERE user_id = ?)""",
            (condition_type, condition_value, user_id)
        )
        awarded = []
        for badge in potential:
            badge_id, name, desc = badge
            self.db.execute_query(
                "INSERT OR IGNORE INTO user_badges (user_id, badge_id) VALUES (?, ?)",
                (user_id, badge_id)
            )
            awarded.append((name, desc))
        return awarded

    def get_earned_badges(self, user_id):
        return self.db.fetch_all(
            """SELECT b.name, b.description, b.icon, b.badge_type, ub.earned_at
               FROM user_badges ub JOIN badges b ON ub.badge_id = b.id
               WHERE ub.user_id = ? ORDER BY ub.earned_at DESC""",
            (user_id,)
        )

    def get_not_earned_badges(self, user_id):
        return self.db.fetch_all(
            "SELECT name, description, icon, badge_type, condition_type, condition_value FROM badges WHERE id NOT IN (SELECT badge_id FROM user_badges WHERE user_id = ?)",
            (user_id,)
        )

    def get_stats_value(self, stats, condition_type, user_id):
        if condition_type == "total_completions":
            return stats["total_completions"]
        elif condition_type == "max_streak":
            return stats["max_streak"]
        elif condition_type == "habits_created":
            return stats["total_habits_created"]
        return 0


class MentorService:
    def __init__(self, database):
        self.db = database
        self.queue = []

    def find_partner(self, user_id):
        if user_id in self.queue:
            return None, None
        if self.queue:
            partner_id = self.queue.pop(0)
            if partner_id != user_id:
                session_id = self.create_session(user_id, partner_id)
                self.queue = [u for u in self.queue if u != user_id]
                return partner_id, session_id
            else:
                self.queue.append(user_id)
                return None, None
        self.queue.append(user_id)
        return None, None

    def get_active_session(self, user_id):
        return self.db.fetch_one(
            """SELECT id, user1_id, user2_id FROM mentor_sessions
               WHERE (user1_id = ? OR user2_id = ?) AND is_active = 1""",
            (user_id, user_id)
        )

    def create_session(self, user1_id, user2_id):
        self.db.execute_query(
            "INSERT INTO mentor_sessions (user1_id, user2_id) VALUES (?, ?)",
            (user1_id, user2_id)
        )
        return self.db.fetch_one("SELECT last_insert_rowid()")[0]

    def end_session(self, user_id):
        session = self.get_active_session(user_id)
        if session:
            self.db.execute_query("UPDATE mentor_sessions SET is_active = 0 WHERE id = ?", (session[0],))
            if user_id == session[1]:
                return session[2]
            else:
                return session[1]
        return None

    def report_user(self, reporter_id, reported_id):
        self.db.execute_query(
            "INSERT INTO complaints (reporter_user_id, reported_user_id) VALUES (?, ?)",
            (reporter_id, reported_id)
        )
        self.end_session(reporter_id)

    def cancel_queue(self, user_id):
        self.queue = [u for u in self.queue if u != user_id]


crypto = CryptoService(ENCRYPTION_PASSWORD)

db = Database()
db.initialize_database()

user_service = UserService(db)
habit_service = HabitService(db, crypto)
habit_progress_service = HabitProgressService(db)
notify_service = NotifyService(db)
program_service = ProgramService(db)
program_progress_service = HabitProgressService(db)
stats_service = StatsService(db)
badge_service = BadgeService(db)
mentor_service = MentorService(db)

badge_service.seed_badges()

chat_user_ids = {}


def get_habit_message(description, frequency_type):
    hour = datetime.now().hour
    if 5 <= hour < 11:
        prefix = random.choice(Text.HABIT_REMINDER_VARIANTS_MORNING)
    elif 11 <= hour < 17:
        prefix = random.choice(Text.HABIT_REMINDER_VARIANTS_DAY)
    elif 17 <= hour < 22:
        prefix = random.choice(Text.HABIT_REMINDER_VARIANTS_EVENING)
    else:
        prefix = random.choice(Text.HABIT_REMINDER_VARIANTS_NIGHT)
    return f"{prefix}\n\n{description}\n({frequency_type})"


def check_habits(context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now().strftime("%H:%M")
    current_date = datetime.now().strftime("%Y-%m-%d")

    for user_row in db.fetch_all("SELECT id FROM users"):
        user_id = user_row[0]
        habits = db.fetch_all(
            "SELECT id, description, frequency_type, time_of_day FROM habits WHERE user_id = ? AND is_active = 1 AND is_program = 0",
            (user_id,)
        )
        for habit in habits:
            habit_id, description, frequency_type, time_of_day = habit
            if time_of_day == current_time:
                existing = habit_progress_service.get_today_progress(habit_id, user_id, current_date)
                if not existing:
                    chat_id = user_service.get_chat_id(user_id)
                    if chat_id:
                        desc = crypto.decrypt(description)
                        msg = get_habit_message(desc, frequency_type)
                        habit_progress_service.mark_progress(habit_id, user_id, current_date, "pending")
                        try:
                            context.bot.send_message(
                                chat_id=chat_id,
                                text=msg,
                                reply_markup=Keyboard.get_habit_keyboard(habit_id)
                            )
                        except Exception as e:
                            print(f"Send habit {habit_id} err: {e}")


def check_programs(context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now().strftime("%H:%M")
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_weekday = datetime.now().strftime("%A").lower()
    weekday_map = {"monday": "понедельник", "tuesday": "вторник", "wednesday": "среда",
                   "thursday": "четверг", "friday": "пятница", "saturday": "суббота", "sunday": "воскресенье"}
    russian_weekday = weekday_map.get(current_weekday, "")

    for user_row in db.fetch_all("SELECT id FROM users"):
        user_id = user_row[0]
        subs = program_service.get_user_subscriptions(user_id)
        for sub in subs:
            sub_id, program_id, description, frequency_type, time_of_day = sub
            if time_of_day != current_time:
                continue
            if frequency_type == "ежедневно":
                ok = True
            elif "еженедельн" in frequency_type:
                p = next((x for x in program_service.programs if x["id"] == program_id), None)
                ok = p and "days" in p and russian_weekday in p["days"]
            else:
                ok = False
            if ok:
                existing = program_progress_service.get_today_progress(sub_id, user_id, current_date)
                if not existing:
                    chat_id = user_service.get_chat_id(user_id)
                    if chat_id:
                        msg = get_habit_message(description, frequency_type)
                        program_progress_service.mark_progress(sub_id, user_id, current_date, "pending")
                        try:
                            context.bot.send_message(
                                chat_id=chat_id,
                                text=msg,
                                reply_markup=Keyboard.get_habit_keyboard(sub_id, is_program=True)
                            )
                        except Exception as e:
                            print(f"Send program {sub_id} err: {e}")


async def check_notifications(context: ContextTypes.DEFAULT_TYPE):
    current = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for n in notify_service.get_pending_notifications(current):
        nid, chat_id, desc, dt = n
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{Text.REMINDER_TEXT}\n\n{desc}",
                reply_markup=Keyboard.get_reminder_keyboard(nid)
            )
            notify_service.mark_as_sent(nid)
        except Exception as e:
            print(f"Send notify {nid} err: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    bot_username = user_service.create_user(tg_username)
    user = user_service.get_user_by_tg_username(tg_username)
    if user:
        user_service.update_chat_id(user[0], update.message.chat_id)
    await update.message.reply_text(
        f"Добро пожаловать!\n\nВаш ник: {bot_username}",
        reply_markup=Keyboard.get_main_menu()
    )
    return State.MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    user = user_service.get_user_by_tg_username(tg_username)
    if user:
        user_service.update_chat_id(user[0], update.message.chat_id)
    if text == "Мои привычки":
        await update.message.reply_text("Меню привычек:", reply_markup=Keyboard.get_habbit_menu())
        return State.HABBIT_MENU
    if text == "Напоминания":
        await update.message.reply_text("Меню напоминаний:", reply_markup=Keyboard.get_note_menu())
        return State.NOTIFY_MENU
    if text == "Готовые программы":
        await update.message.reply_text("Меню готовых программ:", reply_markup=Keyboard.get_programm_menu())
        return State.PROGRAMM_MENU
    if text == "Обо мне":
        return await about_me_menu(update, context)
    return State.MAIN_MENU


async def about_me_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    bot_username = user_service.get_bot_username(tg_username)
    await update.message.reply_text(
        f"{Text.ABOUT_ME_MENU}\n\nВаш ник: {bot_username}",
        reply_markup=Keyboard.get_about_me_menu()
    )
    return State.ABOUT_ME_MENU


async def about_me_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"

    if text == "Мои достижения":
        return await badges_menu(update, context)
    if text == "Анонимный наставник":
        return await mentor_menu(update, context)
    if text == "Сменить ник":
        new_nick = user_service.regenerate_bot_username()
        user_service.update_bot_username(tg_username, new_nick)
        await update.message.reply_text(f"Ваш новый ник: {new_nick}", reply_markup=Keyboard.get_about_me_menu())
        return State.ABOUT_ME_MENU
    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_main_menu())
        return State.MAIN_MENU
    return State.ABOUT_ME_MENU


async def badges_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(Text.BADGES_MENU, reply_markup=Keyboard.get_badges_menu())
    return State.BADGES


async def badges_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    user = user_service.get_user_by_tg_username(tg_username)
    if not user:
        return State.MAIN_MENU
    user_id = user[0]

    if text == "Полученные":
        badges = badge_service.get_earned_badges(user_id)
        if not badges:
            msg = "У вас пока нет полученных достижений."
        else:
            msg = Text.BADGES_HEADER
            for b in badges:
                msg += f"\n{b[2]} {b[0]} — {b[1]}"
        await update.message.reply_text(msg, reply_markup=Keyboard.get_badges_menu())
        return State.BADGES

    if text == "Не полученные":
        stats = stats_service.get_or_create(user_id)
        badges = badge_service.get_not_earned_badges(user_id)
        if not badges:
            msg = "Вы получили все доступные достижения!"
        else:
            msg = "Достижения, которые ещё можно получить:\n\n"
            for b in badges:
                _, desc, icon, btype, ctype, cval = b
                current = badge_service.get_stats_value(stats, ctype, user_id)
                progress = min(current, cval)
                bar_len = 10
                filled = int(progress / cval * bar_len) if cval > 0 else 0
                bar = "" * filled + "" * (bar_len - filled)
                msg += f"\n{icon} {_} — {desc}\n   Прогресс: {bar} {progress}/{cval}\n"
        await update.message.reply_text(msg, reply_markup=Keyboard.get_badges_menu())
        return State.BADGES

    if text == "Назад":
        return await about_me_menu(update, context)

    return State.BADGES


async def mentor_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Меню анонимного наставника:\n\nНайдите случайного собеседника для поддержки.",
        reply_markup=Keyboard.get_mentor_menu()
    )
    return State.MENTOR_MENU


async def mentor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    user = user_service.get_user_by_tg_username(tg_username)
    if not user:
        return State.MAIN_MENU
    uid = user[0]

    if text == "Найти наставника":
        session = mentor_service.get_active_session(uid)
        if session:
            await update.message.reply_text(Text.MENTOR_ALREADY, reply_markup=Keyboard.get_mentor_menu())
            return State.MENTOR_MENU

        await update.message.reply_text(Text.MENTOR_SEARCH)
        partner_id, session_id = mentor_service.find_partner(uid)

        if partner_id:
            partner = user_service.get_user_by_id(partner_id)
            my_nick = user_service.get_bot_username(tg_username)
            partner_nick = user_service.get_bot_username(partner[1]) if partner else "Неизвестный"
            await update.message.reply_text(
                f"{Text.MENTOR_FOUND}\n\nВаш ник: {my_nick} | Собеседник: {partner_nick}\n\nПросто напишите сообщение, и оно будет переслано анонимно.",
                reply_markup=Keyboard.get_mentor_chat_keyboard()
            )
            context.user_data['mentor_session'] = session_id

            partner_chat_id = user_service.get_chat_id(partner_id)
            if partner_chat_id:
                await context.bot.send_message(
                    chat_id=partner_chat_id,
                    text=f"{Text.MENTOR_FOUND}\n\nВаш ник: {partner_nick} | Собеседник: {my_nick}\n\nПросто напишите сообщение, и оно будет переслано анонимно.",
                    reply_markup=Keyboard.get_mentor_chat_keyboard()
                )
                p_ctx_data = context.application.user_data.get(partner_chat_id, {})
                p_ctx_data['mentor_session'] = session_id
                context.application.user_data[partner_chat_id] = p_ctx_data
            return State.MENTOR_CHAT
        else:
            await update.message.reply_text(
                f"{Text.MENTOR_QUEUE} Как только появится наставник, я сообщу.",
                reply_markup=Keyboard.get_mentor_menu()
            )
            return State.MENTOR_MENU

    if text == "Завершить":
        partner_id = mentor_service.end_session(uid)
        await update.message.reply_text(Text.MENTOR_ENDED, reply_markup=Keyboard.get_mentor_menu())
        if partner_id:
            p_chat = user_service.get_chat_id(partner_id)
            if p_chat:
                await context.bot.send_message(
                    chat_id=p_chat,
                    text=Text.MENTOR_PARTNER,
                    reply_markup=Keyboard.get_mentor_menu()
                )
        mentor_service.cancel_queue(uid)
        return State.MENTOR_MENU

    if text == "Назад":
        return await about_me_menu(update, context)

    return State.MENTOR_MENU


async def mentor_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    user = user_service.get_user_by_tg_username(tg_username)
    if not user:
        return State.MAIN_MENU
    uid = user[0]

    session = mentor_service.get_active_session(uid)
    if not session:
        await update.message.reply_text(Text.MENTOR_NOT_ACTIVE, reply_markup=Keyboard.get_mentor_menu())
        return State.MENTOR_MENU

    user1_id, user2_id = session[1], session[2]
    partner_id = user2_id if uid == user1_id else user1_id
    p_chat = user_service.get_chat_id(partner_id)

    if p_chat:
        my_nick = user_service.get_bot_username(tg_username)
        await context.bot.send_message(
            chat_id=p_chat,
            text=f"[{my_nick}]: {update.message.text}"
        )
        await update.message.reply_text("", reply_markup=Keyboard.get_mentor_chat_keyboard())
    else:
        await update.message.reply_text("Собеседник недоступен.")

    return State.MENTOR_CHAT


async def habit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Меню привычек:", reply_markup=Keyboard.get_habbit_menu())
    return State.HABBIT_MENU


async def habit_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    user = user_service.get_user_by_tg_username(tg_username)

    if text == "Мои привычки":
        if user:
            habits = habit_service.get_user_habits(user[0])
            msg = Text.YOUR_HABITS + "".join(
                Text.HABIT_ITEM.format(i, h[1], h[2], h[3]) for i, h in enumerate(habits, 1)
            ) if habits else Text.NO_HABITS
        else:
            msg = Text.USER_NOT_FOUND
        await update.message.reply_text(msg, reply_markup=Keyboard.get_habbit_menu())
        return State.HABBIT_MENU

    if text == "Добавить":
        await update.message.reply_text(Text.ENTER_DESCRIPTION)
        return State.ADD_HABIT_DESCRIPTION

    if text == "Отписаться":
        if user:
            habits = habit_service.get_user_habits(user[0])
            if habits:
                msg = Text.SELECT_UNSUBSCRIBE + "".join(
                    Text.HABIT_ITEM.format(i, h[1], h[2], h[3]) for i, h in enumerate(habits, 1)
                ) + Text.ENTER_NUMBER
                await update.message.reply_text(msg)
                context.user_data['habits_for_unsubscribe'] = habits
                return State.UNSUBSCRIBE_HABIT
            else:
                await update.message.reply_text(Text.NO_HABITS_TO_DELETE, reply_markup=Keyboard.get_habbit_menu())
        else:
            await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_habbit_menu())
        return State.HABBIT_MENU

    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_main_menu())
        return State.MAIN_MENU

    return State.HABBIT_MENU


async def add_habit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['habit_description'] = update.message.text
    await update.message.reply_text(Text.ENTER_FREQUENCY, reply_markup=Keyboard.get_frequency_menu())
    return State.ADD_HABIT_FREQUENCY


async def add_habit_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    freq = update.message.text.lower()
    if freq in ["ежедневно", "еженедельно"]:
        context.user_data['habit_frequency'] = freq
        await update.message.reply_text(Text.ENTER_TIME)
        return State.ADD_HABIT_TIME
    await update.message.reply_text(Text.INVALID_FREQUENCY, reply_markup=Keyboard.get_frequency_menu())
    return State.ADD_HABIT_FREQUENCY


async def add_habit_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', update.message.text):
        await update.message.reply_text(Text.INVALID_TIME)
        return State.ADD_HABIT_TIME
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    user = user_service.get_user_by_tg_username(tg_username)
    if user:
        habit_service.create_habit(
            user[0], context.user_data['habit_description'],
            context.user_data['habit_frequency'], update.message.text,
            datetime.now().strftime("%Y-%m-%d")
        )
        total = stats_service.increment_habits_created(user[0])
        awarded = badge_service.check_and_award(user[0], "habits_created", total)
        msg = Text.HABIT_ADDED
        for name, desc in awarded:
            msg += f"\n\n{Text.BADGE_EARNED}\n{name} — {desc}"
        await update.message.reply_text(msg, reply_markup=Keyboard.get_habbit_menu())
    else:
        await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_habbit_menu())
    return State.HABBIT_MENU


async def unsubscribe_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_habbit_menu())
        return State.HABBIT_MENU
    try:
        num = int(text) - 1
        habits = context.user_data.get('habits_for_unsubscribe', [])
        if 0 <= num < len(habits):
            habit_service.delete_habit(habits[num][0])
            await update.message.reply_text(Text.HABIT_UNSUBSCRIBED, reply_markup=Keyboard.get_habbit_menu())
        else:
            await update.message.reply_text(Text.INVALID_NUMBER)
            return State.UNSUBSCRIBE_HABIT
    except ValueError:
        await update.message.reply_text(Text.ENTER_NUMBER_VALID)
        return State.UNSUBSCRIBE_HABIT
    return State.HABBIT_MENU


async def notify_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    user = user_service.get_user_by_tg_username(tg_username)

    if text == "Мои напоминания":
        if user:
            notifies = notify_service.get_user_notifications(user[0])
            msg = Text.YOUR_NOTIFIES + "".join(
                f"{i}. {n[1]}\n   Дата: {n[2]}\n" for i, n in enumerate(notifies, 1)
            ) if notifies else Text.NO_NOTIFIES
        else:
            msg = Text.USER_NOT_FOUND
        await update.message.reply_text(msg, reply_markup=Keyboard.get_note_menu())
        return State.NOTIFY_MENU

    if text == "Добавить":
        await update.message.reply_text(Text.ENTER_NOTIFY_TEXT)
        return State.ADD_NOTIFY_TEXT

    if text == "Удалить":
        if user:
            notifies = notify_service.get_user_notifications(user[0])
            if notifies:
                msg = Text.SELECT_NOTIFY_DELETE + "".join(
                    f"{i}. {n[1]} - {n[2]}\n" for i, n in enumerate(notifies, 1)
                ) + Text.ENTER_NUMBER
                await update.message.reply_text(msg)
                context.user_data['notifies_for_deletion'] = notifies
                return State.DELETE_NOTIFY
            else:
                await update.message.reply_text(Text.NO_NOTIFIES_TO_DELETE, reply_markup=Keyboard.get_note_menu())
        else:
            await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_note_menu())
        return State.NOTIFY_MENU

    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_main_menu())
        return State.MAIN_MENU
    return State.NOTIFY_MENU


async def add_notify_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['notify_text'] = update.message.text
    await update.message.reply_text(Text.ENTER_NOTIFY_DATE)
    return State.ADD_NOTIFY_DATE


async def add_notify_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', update.message.text):
        await update.message.reply_text(Text.INVALID_DATE)
        return State.ADD_NOTIFY_DATE
    try:
        d = datetime.strptime(update.message.text, "%d.%m.%Y")
        if d.date() < datetime.now().date():
            await update.message.reply_text(Text.DATE_PASSED)
            return State.ADD_NOTIFY_DATE
        context.user_data['notify_date'] = update.message.text
        await update.message.reply_text(Text.ENTER_NOTIFY_TIME)
        return State.ADD_NOTIFY_TIME
    except ValueError:
        await update.message.reply_text(Text.INVALID_DATE)
        return State.ADD_NOTIFY_DATE


async def add_notify_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', update.message.text):
        await update.message.reply_text(Text.INVALID_TIME)
        return State.ADD_NOTIFY_TIME
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    user = user_service.get_user_by_tg_username(tg_username)
    if user:
        date_obj = datetime.strptime(context.user_data['notify_date'], "%d.%m.%Y")
        full_dt = datetime.combine(date_obj.date(), datetime.strptime(update.message.text, "%H:%M").time())
        notify_service.create_notify(
            update.message.chat_id, user[0],
            context.user_data['notify_text'],
            full_dt.strftime("%Y-%m-%d %H:%M:%S")
        )
        await update.message.reply_text(Text.NOTIFY_ADDED, reply_markup=Keyboard.get_note_menu())
    else:
        await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_note_menu())
    return State.NOTIFY_MENU


async def delete_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_note_menu())
        return State.NOTIFY_MENU
    try:
        num = int(text) - 1
        notifies = context.user_data.get('notifies_for_deletion', [])
        if 0 <= num < len(notifies):
            notify_service.delete_notification(notifies[num][0])
            await update.message.reply_text(Text.NOTIFY_DELETED, reply_markup=Keyboard.get_note_menu())
        else:
            await update.message.reply_text(Text.INVALID_NUMBER)
            return State.DELETE_NOTIFY
    except ValueError:
        await update.message.reply_text(Text.ENTER_NUMBER_VALID)
        return State.DELETE_NOTIFY
    return State.NOTIFY_MENU


async def programm_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
    user = user_service.get_user_by_tg_username(tg_username)

    if text == "Мои программы":
        if user:
            subs = program_service.get_user_subscriptions(user[0])
            msg = Text.YOUR_PROGRAMS + "".join(
                Text.PROGRAM_ITEM.format(i, s[2], s[3], s[4]) for i, s in enumerate(subs, 1)
            ) if subs else Text.NO_PROGRAMS
        else:
            msg = Text.USER_NOT_FOUND
        await update.message.reply_text(msg, reply_markup=Keyboard.get_programm_menu())
        return State.PROGRAMM_MENU

    if text == "Подписаться":
        programs = program_service.get_programs()
        msg = Text.SELECT_PROGRAM + "".join(
            f"{i}. {Text.PROGRAM_FROM_FILE if p.get('is_file') else ''}{p['description']} ({p['frequency_type']})\n   Время: {p['time_of_day']}\n"
            for i, p in enumerate(programs, 1)
        ) + Text.ENTER_NUMBER
        await update.message.reply_text(msg)
        context.user_data['available_programs'] = programs
        return State.PROGRAMM_SELECT

    if text == "Отписаться":
        if user:
            subs = program_service.get_user_subscriptions(user[0])
            if subs:
                msg = Text.SELECT_PROGRAM_UNSUB + "".join(
                    f"{i}. {s[2]} ({s[3]})\n   Время: {s[4]}\n" for i, s in enumerate(subs, 1)
                ) + Text.ENTER_NUMBER
                await update.message.reply_text(msg)
                context.user_data['programs_for_unsubscribe'] = subs
                return State.PROGRAMM_UNSUB
            else:
                await update.message.reply_text(Text.NO_PROGRAMS_TO_UNSUB, reply_markup=Keyboard.get_programm_menu())
        else:
            await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_programm_menu())
        return State.PROGRAMM_MENU

    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_main_menu())
        return State.MAIN_MENU
    return State.PROGRAMM_MENU


async def programm_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_programm_menu())
        return State.PROGRAMM_MENU
    programs = context.user_data.get('available_programs', [])
    if not programs:
        return State.PROGRAMM_MENU
    try:
        num = int(text) - 1
        if 0 <= num < len(programs):
            tg_username = update.effective_user.username or f"user_{update.effective_user.id}"
            user = user_service.get_user_by_tg_username(tg_username)
            if user:
                program_service.subscribe(user[0], programs[num]["id"])
                await update.message.reply_text(Text.PROGRAM_ADDED, reply_markup=Keyboard.get_programm_menu())
            else:
                await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_programm_menu())
        else:
            await update.message.reply_text(Text.INVALID_NUMBER)
            return State.PROGRAMM_SELECT
    except ValueError:
        await update.message.reply_text(Text.ENTER_NUMBER_VALID)
        return State.PROGRAMM_SELECT
    context.user_data['available_programs'] = []
    return State.PROGRAMM_MENU


async def programm_unsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_programm_menu())
        return State.PROGRAMM_MENU
    try:
        num = int(text) - 1
        subs = context.user_data.get('programs_for_unsubscribe', [])
        if 0 <= num < len(subs):
            program_service.unsubscribe(subs[num][0])
            await update.message.reply_text(Text.PROGRAM_UNSUBSCRIBED, reply_markup=Keyboard.get_programm_menu())
        else:
            await update.message.reply_text(Text.INVALID_NUMBER)
            return State.PROGRAMM_UNSUB
    except ValueError:
        await update.message.reply_text(Text.ENTER_NUMBER_VALID)
        return State.PROGRAMM_UNSUB
    return State.PROGRAMM_MENU


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Notify done
    if data.startswith("done_notify_"):
        nid = int(data.split("_")[2])
        notify_service.mark_as_done(nid)
        await query.edit_message_text(text=f"{query.message.text}\n\nВыполнено!")
        return

    # Notify postpone
    if data.startswith("postpone1h_notify_"):
        nid = int(data.split("_")[2])
        new_time = datetime.now() + timedelta(hours=1)
        notify_service.postpone_notification(nid, new_time.strftime("%Y-%m-%d %H:%M:%S"))
        await query.edit_message_text(text=f"{query.message.text}\n\nОтложено на 1 час")
        return

    # Mentor
    if data == "mentor_report":
        tg_username = query.from_user.username or f"user_{query.from_user.id}"
        user = user_service.get_user_by_tg_username(tg_username)
        if user:
            session = mentor_service.get_active_session(user[0])
            if session:
                partner_id = session[2] if user[0] == session[1] else session[1]
                mentor_service.report_user(user[0], partner_id)
                await query.edit_message_text(text=f"{query.message.text}\n\n{Text.MENTOR_REPORT_SENT}")
            else:
                await query.edit_message_text(text=f"{query.message.text}\n\n{Text.MENTOR_NOT_ACTIVE}")
        return

    if data == "mentor_end":
        tg_username = query.from_user.username or f"user_{query.from_user.id}"
        user = user_service.get_user_by_tg_username(tg_username)
        if user:
            partner_id = mentor_service.end_session(user[0])
            await query.edit_message_text(text=f"{query.message.text}\n\n{Text.MENTOR_ENDED}")
            if partner_id:
                p_chat = user_service.get_chat_id(partner_id)
                if p_chat:
                    await context.bot.send_message(
                        chat_id=p_chat,
                        text=Text.MENTOR_PARTNER,
                        reply_markup=Keyboard.get_mentor_menu()
                    )
        return

    # Habit/Program progress
    parts = data.split("_")
    if len(parts) >= 3:
        action = parts[0]
        obj_type = parts[1]
        obj_id = int(parts[2])
        current_date = datetime.now().strftime("%Y-%m-%d")

        if action == "done":
            status = "done"
            reply = "Выполнено!"
        elif action == "postpone15m":
            status = "postponed_15m"
            reply = "Отложено на 15 минут"
        elif action == "postpone1h":
            status = "postponed_1h"
            reply = "Отложено на 1 час"
        else:
            return

        tg_username = query.from_user.username or f"user_{query.from_user.id}"
        user = user_service.get_user_by_tg_username(tg_username)
        if not user:
            return
        uid = user[0]

        if obj_type == "habit":
            hp = habit_progress_service.mark_progress(obj_id, uid, current_date, status)
            if status == "done":
                stats = stats_service.increment_completions(uid)
                total = stats["total_completions"]
                streak = stats["max_streak"]

                awarded = badge_service.check_and_award(uid, "total_completions", total)
                awarded += badge_service.check_and_award(uid, "max_streak", streak)

                for name, desc in awarded:
                    try:
                        await query.message.chat.send_message(
                            f"{Text.BADGE_EARNED}\n{name} — {desc}"
                        )
                    except Exception:
                        pass
            await query.edit_message_text(text=f"{query.message.text}\n\n{reply}")

        elif obj_type == "prog":
            program_progress_service.mark_progress(obj_id, uid, current_date, status)
            if status == "done":
                stats = stats_service.increment_completions(uid)
                total = stats["total_completions"]
                streak = stats["max_streak"]
                awarded = badge_service.check_and_award(uid, "total_completions", total)
                awarded += badge_service.check_and_award(uid, "max_streak", streak)
                for name, desc in awarded:
                    try:
                        await query.message.chat.send_message(
                            f"{Text.BADGE_EARNED}\n{name} — {desc}"
                        )
                    except Exception:
                        pass
            await query.edit_message_text(text=f"{query.message.text}\n\n{reply}")


def main():
    app = Application.builder().token(TOKEN).build()
    jq = app.job_queue

    jq.run_repeating(check_notifications, interval=60, first=10)
    jq.run_repeating(check_habits, interval=60, first=15)
    jq.run_repeating(check_programs, interval=60, first=20)

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            State.HABBIT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, habit_menu_handler)],
            State.ADD_HABIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_description)],
            State.ADD_HABIT_FREQUENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_frequency)],
            State.ADD_HABIT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_time)],
            State.UNSUBSCRIBE_HABIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, unsubscribe_habit)],
            State.NOTIFY_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, notify_menu_handler)],
            State.ADD_NOTIFY_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_notify_text)],
            State.ADD_NOTIFY_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_notify_date)],
            State.ADD_NOTIFY_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_notify_time)],
            State.DELETE_NOTIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_notify)],
            State.PROGRAMM_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, programm_menu_handler)],
            State.PROGRAMM_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, programm_select)],
            State.PROGRAMM_UNSUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, programm_unsub)],
            State.ABOUT_ME_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, about_me_handler)],
            State.BADGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, badges_handler)],
            State.MENTOR_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, mentor_handler)],
            State.MENTOR_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, mentor_chat_handler)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()


if __name__ == "__main__":
    main()
