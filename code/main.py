import sqlite3
import os
import random
import re
import json
from datetime import datetime, timedelta
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters, CallbackQueryHandler, JobQueue
)

load_dotenv()

TOKEN = os.getenv("TOKEN")
db_path = os.path.join(os.path.dirname(__file__), 'db', 'main.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

PROGRAMS_FILE = os.path.join(os.path.dirname(__file__), 'programs.json')


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


class Text:
    MAIN_MENU_KEYBOARD = ["Напоминания", "Мои привычки", "Готовые программы", "Обо мне"]
    HABBIT_MENU_KEYBOARD = ["Мои привычки", "Добавить", "Отписаться", "Назад"]
    NOTIFY_MENU_KEYBOARD = ["Мои напоминания", "Добавить", "Удалить", "Назад"]
    PROGRAMM_MENU_KEYBOARD = ["Мои программы", "Подписаться", "Отписаться", "Назад"]
    FREQUENCY_KEYBOARD = ["Ежедневно", "Еженедельно"]
    ABOUT_ME_KEYBOARD = ["Сменить ник", "Мои достижения", "Назад"]
    BADGES_KEYBOARD = ["Назад"]
    
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
    PROGRAM_FROM_FILE = "📁 "
    
    NICK_CHANGED = "Ник успешно изменен!"
    BADGES_COMING = "Раздел 'Мои достижения' пока недоступен!"
    BADGES_MENU = "Меню достижений:"
    
    ABOUT_ME_MENU = "Личный кабинет:"
    
    HABIT_REMINDER = "Время для привычки!"


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
    def get_notify_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[0]), KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[1])],
            [KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[2]), KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[3])]
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
            [KeyboardButton(Text.ABOUT_ME_KEYBOARD[1]), KeyboardButton(Text.ABOUT_ME_KEYBOARD[2])]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_reminder_keyboard(notify_id):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Выполнено", callback_data=f"done_notify_{notify_id}"),
                InlineKeyboardButton("+1 час", callback_data=f"postpone1h_notify_{notify_id}")
            ]
        ])
    
    @staticmethod
    def get_habit_keyboard(habit_id, is_program=False):
        prefix = "prog" if is_program else "habit"
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Выполнено", callback_data=f"done_{prefix}_{habit_id}"),
                InlineKeyboardButton("+15 мин", callback_data=f"postpone15m_{prefix}_{habit_id}"),
                InlineKeyboardButton("+1 час", callback_data=f"postpone1h_{prefix}_{habit_id}")
            ]
        ])
    
    @staticmethod
    def get_badges_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.BADGES_KEYBOARD[0])]
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


class HabitService:
    def __init__(self, database):
        self.db = database
    
    def create_habit(self, user_id, description, frequency_type, time_of_day, start_date, is_program=0):
        query = """
        INSERT INTO habits 
        (user_id, description, frequency_type, time_of_day, start_date, is_program)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = self.db.execute_query(query, (user_id, description, frequency_type, time_of_day, start_date, is_program))
        return cursor.lastrowid
    
    def get_user_habits(self, user_id, include_programs=False):
        if include_programs:
            query = """
            SELECT id, description, frequency_type, time_of_day, start_date, is_program
            FROM habits 
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
            """
        else:
            query = """
            SELECT id, description, frequency_type, time_of_day, start_date, is_program
            FROM habits 
            WHERE user_id = ? AND is_active = 1 AND is_program = 0
            ORDER BY created_at DESC
            """
        return self.db.fetch_all(query, (user_id,))
    
    def delete_habit(self, habit_id):
        query = "UPDATE habits SET is_active = 0 WHERE id = ?"
        self.db.execute_query(query, (habit_id,))
    
    def get_active_habits_for_sending(self, user_id):
        query = """
        SELECT id, description, frequency_type, time_of_day, user_id
        FROM habits 
        WHERE user_id = ? AND is_active = 1 AND is_program = 0
        """
        return self.db.fetch_all(query, (user_id,))


class HabitProgressService:
    def __init__(self, database):
        self.db = database
    
    def mark_progress(self, habit_id, user_id, date, status):
        query = """
        INSERT INTO habit_progress (habit_id, user_id, date, status)
        VALUES (?, ?, ?, ?)
        """
        self.db.execute_query(query, (habit_id, user_id, date, status))
    
    def get_today_progress(self, habit_id, user_id, date):
        query = """
        SELECT * FROM habit_progress 
        WHERE habit_id = ? AND date = ?
        """
        return self.db.fetch_one(query, (habit_id, date))
    
    def update_progress(self, progress_id, status):
        query = "UPDATE habit_progress SET status = ? WHERE id = ?"
        self.db.execute_query(query, (status, progress_id))


class NotifyService:
    def __init__(self, database):
        self.db = database
    
    def create_notify(self, chat_id, user_id, description, time_notify):
        query = """
        INSERT INTO notifications (chat_id, user_id, description, time_notify)
        VALUES (?, ?, ?, ?)
        """
        cursor = self.db.execute_query(query, (chat_id, user_id, description, time_notify))
        return cursor.lastrowid
    
    def get_pending_notifications(self, current_time):
        query = """
        SELECT id, chat_id, description, time_notify
        FROM notifications
        WHERE done = 0 AND sent = 0 AND time_notify <= ?
        """
        return self.db.fetch_all(query, (current_time,))
    
    def mark_as_sent(self, notify_id):
        query = "UPDATE notifications SET sent = 1 WHERE id = ?"
        self.db.execute_query(query, (notify_id,))
    
    def postpone_notification(self, notify_id, new_time):
        query = """
        UPDATE notifications 
        SET time_notify = ?, sent = 0
        WHERE id = ?
        """
        self.db.execute_query(query, (new_time, notify_id))
    
    def mark_as_done(self, notify_id):
        query = "UPDATE notifications SET done = 1, sent = 1 WHERE id = ?"
        self.db.execute_query(query, (notify_id,))
    
    def get_user_notifications(self, user_id):
        query = """
        SELECT id, description, time_notify, done, sent
        FROM notifications
        WHERE user_id = ? AND done = 0
        ORDER BY time_notify ASC
        """
        return self.db.fetch_all(query, (user_id,))
    
    def delete_notification(self, notify_id):
        query = "DELETE FROM notifications WHERE id = ?"
        self.db.execute_query(query, (notify_id,))


class ProgramService:
    def __init__(self, database):
        self.db = database
        self.programs = self.load_programs()
    
    def load_programs(self):
        programs = [
            {
                "id": "water_twice",
                "description": "Пить воду дважды в день",
                "frequency_type": "ежедневно",
                "time_of_day": "09:00",
                "is_file": False
            },
            {
                "id": "morning_exercise",
                "description": "Зарядка по утрам",
                "frequency_type": "ежедневно",
                "time_of_day": "07:00",
                "is_file": False
            },
            {
                "id": "water_flowers",
                "description": "Поливать цветы",
                "frequency_type": "еженедельно",
                "time_of_day": "19:00",
                "days": ["понедельник", "четверг"],
                "is_file": False
            }
        ]
        
        file_programs = load_programs_from_json()
        for p in file_programs:
            p["is_file"] = True
        programs.extend(file_programs)
        
        return programs
    
    def get_programs(self):
        return self.programs
    
    def subscribe(self, user_id, program_id):
        for p in self.programs:
            if p["id"] == program_id:
                query = """
                INSERT INTO program_subscriptions 
                (user_id, program_id, description, frequency_type, time_of_day)
                VALUES (?, ?, ?, ?, ?)
                """
                self.db.execute_query(query, (
                    user_id, program_id, p["description"], 
                    p["frequency_type"], p["time_of_day"]
                ))
                return True
        return False
    
    def get_user_subscriptions(self, user_id):
        query = """
        SELECT id, program_id, description, frequency_type, time_of_day
        FROM program_subscriptions
        WHERE user_id = ? AND is_active = 1
        """
        return self.db.fetch_all(query, (user_id,))
    
    def unsubscribe(self, subscription_id):
        query = "UPDATE program_subscriptions SET is_active = 0 WHERE id = ?"
        self.db.execute_query(query, (subscription_id,))
    
    def get_subscription_by_id(self, subscription_id):
        query = "SELECT * FROM program_subscriptions WHERE id = ? AND is_active = 1"
        return self.db.fetch_one(query, (subscription_id,))


class ProgramProgressService:
    def __init__(self, database):
        self.db = database
    
    def mark_progress(self, subscription_id, user_id, date, status):
        query = """
        INSERT INTO program_progress (subscription_id, user_id, date, status)
        VALUES (?, ?, ?, ?)
        """
        self.db.execute_query(query, (subscription_id, user_id, date, status))
    
    def get_today_progress(self, subscription_id, date):
        query = """
        SELECT * FROM program_progress 
        WHERE subscription_id = ? AND date = ?
        """
        return self.db.fetch_one(query, (subscription_id, date))
    
    def update_progress(self, progress_id, status):
        query = "UPDATE program_progress SET status = ? WHERE id = ?"
        self.db.execute_query(query, (status, progress_id))


db = Database()
db.initialize_database()
user_service = UserService(db)
habit_service = HabitService(db)
habit_progress_service = HabitProgressService(db)
notify_service = NotifyService(db)
program_service = ProgramService(db)
program_progress_service = ProgramProgressService(db)

chat_ids = {}


async def check_habits(context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now()
    current_time_str = current_time.strftime("%H:%M")
    current_date = current_time.strftime("%Y-%m-%d")
    
    for user in db.fetch_all("SELECT id, tg_username FROM users"):
        user_id, tg_username = user
        habits = habit_service.get_active_habits_for_sending(user_id)
        
        for habit in habits:
            habit_id, description, frequency_type, time_of_day, h_user_id = habit
            
            if time_of_day == current_time_str:
                existing = habit_progress_service.get_today_progress(habit_id, current_date)
                if not existing:
                    chat_id = chat_ids.get(user_id)
                    if chat_id:
                        habit_progress_service.mark_progress(habit_id, user_id, current_date, "pending")
                        try:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"{Text.HABIT_REMINDER}\n\n{description}\n({frequency_type})",
                                reply_markup=Keyboard.get_habit_keyboard(habit_id)
                            )
                        except Exception as e:
                            print(f"Failed to send habit {habit_id}: {e}")


async def check_programs(context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now()
    current_time_str = current_time.strftime("%H:%M")
    current_date = current_time.strftime("%Y-%m-%d")
    current_weekday = current_time.strftime("%A").lower()
    
    weekday_map = {
        "monday": "понедельник", "tuesday": "вторник", "wednesday": "среда",
        "thursday": "четверг", "friday": "пятница", "saturday": "суббота", "sunday": "воскресенье"
    }
    current_russian_weekday = weekday_map.get(current_weekday, "")
    
    for user in db.fetch_all("SELECT id, tg_username FROM users"):
        user_id, tg_username = user
        subscriptions = program_service.get_user_subscriptions(user_id)
        
        for sub in subscriptions:
            sub_id, program_id, description, frequency_type, time_of_day = sub
            
            if time_of_day != current_time_str:
                continue
            
            should_send = False
            if frequency_type == "ежедневно":
                should_send = True
            elif "еженедельно" in frequency_type:
                program = next((p for p in program_service.programs if p["id"] == program_id), None)
                if program and "days" in program:
                    if current_russian_weekday in program["days"]:
                        should_send = True
            
            if should_send:
                existing = program_progress_service.get_today_progress(sub_id, current_date)
                if not existing:
                    chat_id = chat_ids.get(user_id)
                    if chat_id:
                        program_progress_service.mark_progress(sub_id, user_id, current_date, "pending")
                        try:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"{Text.HABIT_REMINDER}\n\n{description}\n({frequency_type})",
                                reply_markup=Keyboard.get_habit_keyboard(sub_id, is_program=True)
                            )
                        except Exception as e:
                            print(f"Failed to send program {sub_id}: {e}")


async def check_notifications(context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pending = notify_service.get_pending_notifications(current_time)
    
    for notify in pending:
        notify_id, chat_id, description, time_notify = notify
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{Text.REMINDER_TEXT}\n\n{description}",
                reply_markup=Keyboard.get_reminder_keyboard(notify_id)
            )
            notify_service.mark_as_sent(notify_id)
        except Exception as e:
            print(f"Failed to send notification {notify_id}: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_username = update.effective_user.username
    user_service.create_user(tg_username)
    bot_username = user_service.get_bot_username(tg_username)
    
    chat_ids[db.fetch_one("SELECT id FROM users WHERE tg_username = ?", (tg_username,))[0]] = update.message.chat_id
    
    await update.message.reply_text(
        f"Добро пожаловать в бот для отслеживания привычек!\n\nВаш ник: {bot_username}",
        reply_markup=Keyboard.get_main_menu()
    )
    return State.MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    tg_username = update.effective_user.username
    user = user_service.get_user_by_tg_username(tg_username)
    if user:
        chat_ids[user[0]] = update.message.chat_id
    
    if text == "Мои привычки":
        return await habit_menu(update, context)
    elif text == "Напоминания":
        return await notify_menu(update, context)
    elif text == "Готовые программы":
        return await programm_menu(update, context)
    elif text == "Обо мне":
        return await about_me_menu(update, context)
    
    return State.MAIN_MENU


async def habit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Меню привычек:",
        reply_markup=Keyboard.get_habbit_menu()
    )
    return State.HABBIT_MENU


async def habit_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Мои привычки":
        tg_username = update.effective_user.username
        user = user_service.get_user_by_tg_username(tg_username)
        
        if user:
            habits = habit_service.get_user_habits(user[0], include_programs=False)
            if habits:
                message = Text.YOUR_HABITS
                for i, habit in enumerate(habits, 1):
                    message += Text.HABIT_ITEM.format(i, habit[1], habit[2], habit[3])
            else:
                message = Text.NO_HABITS
        else:
            message = Text.USER_NOT_FOUND
        
        await update.message.reply_text(message, reply_markup=Keyboard.get_habbit_menu())
        return State.HABBIT_MENU
    
    elif text == "Добавить":
        await update.message.reply_text(Text.ENTER_DESCRIPTION)
        return State.ADD_HABIT_DESCRIPTION
    
    elif text == "Отписаться":
        tg_username = update.effective_user.username
        user = user_service.get_user_by_tg_username(tg_username)
        
        if user:
            habits = habit_service.get_user_habits(user[0], include_programs=False)
            if habits:
                message = Text.SELECT_UNSUBSCRIBE
                for i, habit in enumerate(habits, 1):
                    message += Text.HABIT_ITEM.format(i, habit[1], habit[2], habit[3])
                message += Text.ENTER_NUMBER
                await update.message.reply_text(message)
                context.user_data['habits_for_unsubscribe'] = habits
                return State.UNSUBSCRIBE_HABIT
            else:
                await update.message.reply_text(Text.NO_HABITS_TO_DELETE, reply_markup=Keyboard.get_habbit_menu())
        else:
            await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_habbit_menu())
        
        return State.HABBIT_MENU
    
    elif text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_main_menu())
        return State.MAIN_MENU
    
    return State.HABBIT_MENU


async def add_habit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['habit_description'] = update.message.text
    await update.message.reply_text(Text.ENTER_FREQUENCY, reply_markup=Keyboard.get_frequency_menu())
    return State.ADD_HABIT_FREQUENCY


async def add_habit_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frequency = update.message.text.lower()
    if frequency in ["ежедневно", "еженедельно"]:
        context.user_data['habit_frequency'] = frequency
        await update.message.reply_text(Text.ENTER_TIME)
        return State.ADD_HABIT_TIME
    else:
        await update.message.reply_text(Text.INVALID_FREQUENCY, reply_markup=Keyboard.get_frequency_menu())
        return State.ADD_HABIT_FREQUENCY


async def add_habit_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    if re.match(time_pattern, update.message.text):
        tg_username = update.effective_user.username
        user = user_service.get_user_by_tg_username(tg_username)
        
        if user:
            habit_service.create_habit(
                user_id=user[0],
                description=context.user_data['habit_description'],
                frequency_type=context.user_data['habit_frequency'],
                time_of_day=update.message.text,
                start_date=datetime.now().strftime("%Y-%m-%d")
            )
            await update.message.reply_text(Text.HABIT_ADDED, reply_markup=Keyboard.get_habbit_menu())
        else:
            await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_habbit_menu())
    else:
        await update.message.reply_text(Text.INVALID_TIME)
        return State.ADD_HABIT_TIME
    
    return State.HABBIT_MENU


async def delete_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_habbit_menu())
        return State.HABBIT_MENU
    
    try:
        habit_number = int(text) - 1
        habits = context.user_data.get('habits_for_deletion', [])
        
        if 0 <= habit_number < len(habits):
            habit_id = habits[habit_number][0]
            habit_service.delete_habit(habit_id)
            await update.message.reply_text(Text.HABIT_DELETED, reply_markup=Keyboard.get_habbit_menu())
        else:
            await update.message.reply_text(Text.INVALID_NUMBER)
            return State.DELETE_HABIT
    except ValueError:
        await update.message.reply_text(Text.ENTER_NUMBER_VALID)
        return State.DELETE_HABIT
    
    return State.HABBIT_MENU


async def unsubscribe_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_habbit_menu())
        return State.HABBIT_MENU
    
    try:
        habit_number = int(text) - 1
        habits = context.user_data.get('habits_for_unsubscribe', [])
        
        if 0 <= habit_number < len(habits):
            habit_id = habits[habit_number][0]
            habit_service.delete_habit(habit_id)
            await update.message.reply_text(Text.HABIT_UNSUBSCRIBED, reply_markup=Keyboard.get_habbit_menu())
        else:
            await update.message.reply_text(Text.INVALID_NUMBER)
            return State.UNSUBSCRIBE_HABIT
    except ValueError:
        await update.message.reply_text(Text.ENTER_NUMBER_VALID)
        return State.UNSUBSCRIBE_HABIT
    
    return State.HABBIT_MENU


async def notify_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Меню напоминаний:",
        reply_markup=Keyboard.get_notify_menu()
    )
    return State.NOTIFY_MENU


async def notify_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Мои напоминания":
        tg_username = update.effective_user.username
        user = user_service.get_user_by_tg_username(tg_username)
        
        if user:
            notifies = notify_service.get_user_notifications(user[0])
            if notifies:
                message = Text.YOUR_NOTIFIES
                for i, notify in enumerate(notifies, 1):
                    message += f"{i}. {notify[1]}\n   Дата: {notify[2]}\n"
            else:
                message = Text.NO_NOTIFIES
        else:
            message = Text.USER_NOT_FOUND
        
        await update.message.reply_text(message, reply_markup=Keyboard.get_notify_menu())
        return State.NOTIFY_MENU
    
    elif text == "Добавить":
        await update.message.reply_text(Text.ENTER_NOTIFY_TEXT)
        return State.ADD_NOTIFY_TEXT
    
    elif text == "Удалить":
        tg_username = update.effective_user.username
        user = user_service.get_user_by_tg_username(tg_username)
        
        if user:
            notifies = notify_service.get_user_notifications(user[0])
            if notifies:
                message = Text.SELECT_NOTIFY_DELETE
                for i, notify in enumerate(notifies, 1):
                    message += f"{i}. {notify[1]} - {notify[2]}\n"
                message += Text.ENTER_NUMBER
                await update.message.reply_text(message)
                context.user_data['notifies_for_deletion'] = notifies
                return State.DELETE_NOTIFY
            else:
                await update.message.reply_text(Text.NO_NOTIFIES_TO_DELETE, reply_markup=Keyboard.get_notify_menu())
        else:
            await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_notify_menu())
        
        return State.NOTIFY_MENU
    
    elif text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_main_menu())
        return State.MAIN_MENU
    
    return State.NOTIFY_MENU


async def add_notify_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['notify_text'] = update.message.text
    await update.message.reply_text(Text.ENTER_NOTIFY_DATE)
    return State.ADD_NOTIFY_DATE


async def add_notify_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'
    if re.match(date_pattern, update.message.text):
        try:
            notify_date = datetime.strptime(update.message.text, "%d.%m.%Y")
            if notify_date.date() < datetime.now().date():
                await update.message.reply_text(Text.DATE_PASSED)
                return State.ADD_NOTIFY_DATE
            context.user_data['notify_date'] = update.message.text
            await update.message.reply_text(Text.ENTER_NOTIFY_TIME)
            return State.ADD_NOTIFY_TIME
        except ValueError:
            await update.message.reply_text(Text.INVALID_DATE)
            return State.ADD_NOTIFY_DATE
    else:
        await update.message.reply_text(Text.INVALID_DATE)
        return State.ADD_NOTIFY_DATE


async def add_notify_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    if re.match(time_pattern, update.message.text):
        tg_username = update.effective_user.username
        user = user_service.get_user_by_tg_username(tg_username)
        
        if user:
            date_str = context.user_data['notify_date']
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            time_str = update.message.text
            full_datetime = datetime.combine(date_obj.date(), datetime.strptime(time_str, "%H:%M").time())
            
            notify_service.create_notify(
                chat_id=update.message.chat_id,
                user_id=user[0],
                description=context.user_data['notify_text'],
                time_notify=full_datetime.strftime("%Y-%m-%d %H:%M:%S")
            )
            await update.message.reply_text(Text.NOTIFY_ADDED, reply_markup=Keyboard.get_notify_menu())
        else:
            await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_notify_menu())
    else:
        await update.message.reply_text(Text.INVALID_TIME)
        return State.ADD_NOTIFY_TIME
    
    return State.NOTIFY_MENU


async def delete_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_notify_menu())
        return State.NOTIFY_MENU
    
    try:
        notify_number = int(text) - 1
        notifies = context.user_data.get('notifies_for_deletion', [])
        
        if 0 <= notify_number < len(notifies):
            notify_id = notifies[notify_number][0]
            notify_service.delete_notification(notify_id)
            await update.message.reply_text(Text.NOTIFY_DELETED, reply_markup=Keyboard.get_notify_menu())
        else:
            await update.message.reply_text(Text.INVALID_NUMBER)
            return State.DELETE_NOTIFY
    except ValueError:
        await update.message.reply_text(Text.ENTER_NUMBER_VALID)
        return State.DELETE_NOTIFY
    
    return State.NOTIFY_MENU


async def programm_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Меню готовых программ:",
        reply_markup=Keyboard.get_programm_menu()
    )
    return State.PROGRAMM_MENU


async def programm_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Мои программы":
        tg_username = update.effective_user.username
        user = user_service.get_user_by_tg_username(tg_username)
        
        if user:
            subs = program_service.get_user_subscriptions(user[0])
            if subs:
                message = Text.YOUR_PROGRAMS
                for i, sub in enumerate(subs, 1):
                    message += Text.PROGRAM_ITEM.format(i, sub[2], sub[3], sub[4])
            else:
                message = Text.NO_PROGRAMS
        else:
            message = Text.USER_NOT_FOUND
        
        await update.message.reply_text(message, reply_markup=Keyboard.get_programm_menu())
        return State.PROGRAMM_MENU
    
    elif text == "Подписаться":
        programs = program_service.get_programs()
        message = Text.SELECT_PROGRAM
        for i, p in enumerate(programs, 1):
            prefix = Text.PROGRAM_FROM_FILE if p.get("is_file") else ""
            message += f"{i}. {prefix}{p['description']} ({p['frequency_type']})\n   Время: {p['time_of_day']}\n"
        message += Text.ENTER_NUMBER
        await update.message.reply_text(message)
        context.user_data['available_programs'] = programs
        return State.PROGRAMM_SELECT
    
    elif text == "Отписаться":
        tg_username = update.effective_user.username
        user = user_service.get_user_by_tg_username(tg_username)
        
        if user:
            subs = program_service.get_user_subscriptions(user[0])
            if subs:
                message = Text.SELECT_PROGRAM_UNSUB
                for i, sub in enumerate(subs, 1):
                    message += f"{i}. {sub[2]} ({sub[3]})\n   Время: {sub[4]}\n"
                message += Text.ENTER_NUMBER
                await update.message.reply_text(message)
                context.user_data['programs_for_unsubscribe'] = subs
                return State.PROGRAMM_UNSUB
            else:
                await update.message.reply_text(Text.NO_PROGRAMS_TO_UNSUB, reply_markup=Keyboard.get_programm_menu())
        else:
            await update.message.reply_text(Text.USER_NOT_FOUND, reply_markup=Keyboard.get_programm_menu())
        
        return State.PROGRAMM_MENU
    
    elif text == "Назад":
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
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_programm_menu())
        return State.PROGRAMM_MENU
    
    try:
        num = int(text) - 1
        if 0 <= num < len(programs):
            tg_username = update.effective_user.username
            user = user_service.get_user_by_tg_username(tg_username)
            
            if user:
                program_id = programs[num]["id"]
                program_service.subscribe(user[0], program_id)
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
            sub_id = subs[num][0]
            program_service.unsubscribe(sub_id)
            await update.message.reply_text(Text.PROGRAM_UNSUBSCRIBED, reply_markup=Keyboard.get_programm_menu())
        else:
            await update.message.reply_text(Text.INVALID_NUMBER)
            return State.PROGRAMM_UNSUB
    except ValueError:
        await update.message.reply_text(Text.ENTER_NUMBER_VALID)
        return State.PROGRAMM_UNSUB
    
    return State.PROGRAMM_MENU


async def about_me_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_username = update.effective_user.username
    bot_username = user_service.get_bot_username(tg_username)
    
    await update.message.reply_text(
        f"{Text.ABOUT_ME_MENU}\n\nВаш ник: {bot_username}",
        reply_markup=Keyboard.get_about_me_menu()
    )
    return State.ABOUT_ME_MENU


async def about_me_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Сменить ник":
        tg_username = update.effective_user.username
        new_nick = user_service.regenerate_bot_username()
        user_service.update_bot_username(tg_username, new_nick)
        await update.message.reply_text(
            f"Ваш новый ник: {new_nick}",
            reply_markup=Keyboard.get_about_me_menu()
        )
        return State.ABOUT_ME_MENU
    
    elif text == "Мои достижения":
        await update.message.reply_text(
            Text.BADGES_COMING,
            reply_markup=Keyboard.get_badges_menu()
        )
        return State.BADGES
    
    elif text == "Назад":
        await update.message.reply_text(Text.RETURN_TO_MENU, reply_markup=Keyboard.get_main_menu())
        return State.MAIN_MENU
    
    return State.ABOUT_ME_MENU


async def badges_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Назад":
        return await about_me_menu(update, context)
    
    return State.BADGES


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("done_notify_"):
        notify_id = int(data.split("_")[2])
        notify_service.mark_as_done(notify_id)
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ Отмечено как выполненное")
    
    elif data.startswith("postpone1h_notify_"):
        notify_id = int(data.split("_")[2])
        new_time = datetime.now() + timedelta(hours=1)
        notify_service.postpone_notification(notify_id, new_time.strftime("%Y-%m-%d %H:%M:%S"))
        await query.edit_message_text(text=f"{query.message.text}\n\n⏰ Отложено на 1 час")
    
    elif data.startswith("done_habit_"):
        habit_id = int(data.split("_")[2])
        current_date = datetime.now().strftime("%Y-%m-%d")
        progress = habit_progress_service.get_today_progress(habit_id, current_date)
        if progress:
            habit_progress_service.update_progress(progress[0], "done")
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ Выполнено!")
    
    elif data.startswith("postpone15m_habit_"):
        habit_id = int(data.split("_")[2])
        current_date = datetime.now().strftime("%Y-%m-%d")
        progress = habit_progress_service.get_today_progress(habit_id, current_date)
        if progress:
            habit_progress_service.update_progress(progress[0], "postponed_15m")
        await query.edit_message_text(text=f"{query.message.text}\n\n⏰ Отложено на 15 минут")
    
    elif data.startswith("postpone1h_habit_"):
        habit_id = int(data.split("_")[2])
        current_date = datetime.now().strftime("%Y-%m-%d")
        progress = habit_progress_service.get_today_progress(habit_id, current_date)
        if progress:
            habit_progress_service.update_progress(progress[0], "postponed_1h")
        await query.edit_message_text(text=f"{query.message.text}\n\n⏰ Отложено на 1 час")
    
    elif data.startswith("done_prog_"):
        sub_id = int(data.split("_")[2])
        current_date = datetime.now().strftime("%Y-%m-%d")
        progress = program_progress_service.get_today_progress(sub_id, current_date)
        if progress:
            program_progress_service.update_progress(progress[0], "done")
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ Выполнено!")
    
    elif data.startswith("postpone15m_prog_"):
        sub_id = int(data.split("_")[2])
        current_date = datetime.now().strftime("%Y-%m-%d")
        progress = program_progress_service.get_today_progress(sub_id, current_date)
        if progress:
            program_progress_service.update_progress(progress[0], "postponed_15m")
        await query.edit_message_text(text=f"{query.message.text}\n\n⏰ Отложено на 15 минут")
    
    elif data.startswith("postpone1h_prog_"):
        sub_id = int(data.split("_")[2])
        current_date = datetime.now().strftime("%Y-%m-%d")
        progress = program_progress_service.get_today_progress(sub_id, current_date)
        if progress:
            program_progress_service.update_progress(progress[0], "postponed_1h")
        await query.edit_message_text(text=f"{query.message.text}\n\n⏰ Отложено на 1 час")


def main():
    app = Application.builder().token(TOKEN).build()
    job_queue = app.job_queue
    
    job_queue.run_repeating(check_notifications, interval=60, first=10)
    job_queue.run_repeating(check_habits, interval=60, first=15)
    job_queue.run_repeating(check_programs, interval=60, first=20)
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)
            ],
            State.HABBIT_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, habit_menu_handler)
            ],
            State.ADD_HABIT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_description)
            ],
            State.ADD_HABIT_FREQUENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_frequency)
            ],
            State.ADD_HABIT_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_time)
            ],
            State.DELETE_HABIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_habit)
            ],
            State.UNSUBSCRIBE_HABIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, unsubscribe_habit)
            ],
            State.NOTIFY_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, notify_menu_handler)
            ],
            State.ADD_NOTIFY_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_notify_text)
            ],
            State.ADD_NOTIFY_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_notify_date)
            ],
            State.ADD_NOTIFY_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_notify_time)
            ],
            State.DELETE_NOTIFY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_notify)
            ],
            State.PROGRAMM_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, programm_menu_handler)
            ],
            State.PROGRAMM_SELECT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, programm_select)
            ],
            State.PROGRAMM_UNSUB: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, programm_unsub)
            ],
            State.ABOUT_ME_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, about_me_handler)
            ],
            State.BADGES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, badges_handler)
            ],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()


if __name__ == "__main__":
    main()
