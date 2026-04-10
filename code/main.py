import sqlite3
import os
import random
import re
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")
db_path = os.path.join(os.path.dirname(__file__), 'db', 'main.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)


class State(Enum):
    MAIN_MENU = 1
    HABBIT_MENU = 2
    ADD_HABIT_DESCRIPTION = 3
    ADD_HABIT_FREQUENCY = 4
    ADD_HABIT_TIME = 5
    DELETE_HABIT = 6
    NOTIFY_MENU = 7


class Text:
    MAIN_MENU_KEYBOARD = ["Напоминания", "Мои привычки", "Готовые программы", "Обо мне"]
    
    HABBIT_MENU_KEYBOARD = ["Мои привычки", "Добавить", "Удалить", "Назад"]
    
    RETURN_TO_MENU = "Возвращаемся в главное меню"
    NO_HABITS = "У вас пока нет привычек."
    ENTER_DESCRIPTION = "Введите описание привычки:"
    ENTER_FREQUENCY = "Введите частоту (ежедневно/еженедельно):"
    ENTER_TIME = "Введите время (ЧЧ:ММ):"
    INVALID_FREQUENCY = "Пожалуйста, введите 'ежедневно' или 'еженедельно'"
    INVALID_TIME = "Пожалуйста, введите время в формате ЧЧ:ММ"
    HABIT_ADDED = "Привычка успешно добавлена!"
    HABIT_DELETED = "Привычка удалена!"
    NO_HABITS_TO_DELETE = "У вас нет привычек для удаления."
    SELECT_DELETE = "Выберите привычку для удаления:\n\n"
    ENTER_NUMBER = "\nВведите номер привычки:"
    INVALID_NUMBER = "Неверный номер привычки."
    ENTER_NUMBER_VALID = "Пожалуйста, введите номер привычки."
    USER_NOT_FOUND = "Ошибка: пользователь не найден."
    YOUR_HABITS = "Ваши привычки:\n\n"
    HABIT_ITEM = "{}. {}\n"
    COMING_SOON = "Этот раздел скоро будет доступен!"


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
                frequency_value TEXT,
                time_of_day TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS habit_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(habit_id) REFERENCES habits(id)
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
                     "Находчивый"]
        animals = ['слон', 'тигр', 'медведь', 'лев', 'крокодил',
                  'голубь', 'жираф', 'верблюд', 'броненосец', 'кот']
        digits = ''.join([str(random.randint(0, 9)) for _ in range(5)])
        return f"{random.choice(adjectives)}_{random.choice(animals)}_{digits}"
    
    def get_user_by_tg_username(self, tg_username):
        query = "SELECT * FROM users WHERE tg_username = ?"
        return self.db.fetch_one(query, (tg_username,))


class HabitService:
    def __init__(self, database):
        self.db = database
    
    def create_habit(self, user_id, description, frequency_type, time_of_day, start_date):
        query = """
        INSERT INTO habits 
        (user_id, description, frequency_type, time_of_day, start_date)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor = self.db.execute_query(query, (user_id, description, frequency_type, time_of_day, start_date))
        return cursor.lastrowid
    
    def get_user_habits(self, user_id):
        query = """
        SELECT id, description, frequency_type, time_of_day, start_date
        FROM habits 
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC
        """
        return self.db.fetch_all(query, (user_id,))
    
    def delete_habit(self, habit_id):
        query = "UPDATE habits SET is_active = 0 WHERE id = ?"
        self.db.execute_query(query, (habit_id,))


db = Database()
db.initialize_database()
user_service = UserService(db)
habit_service = HabitService(db)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_username = update.effective_user.username
    user_service.create_user(tg_username)
    
    await update.message.reply_text(
        "Добро пожаловать в бот для отслеживания привычек!",
        reply_markup=Keyboard.get_main_menu()
    )
    return State.MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Мои привычки":
        return await habit_menu(update, context)
    elif text == "Напоминания" or text == "Готовые программы" or text == "Обо мне":
        await update.message.reply_text(Text.COMING_SOON, reply_markup=Keyboard.get_main_menu())
        return State.MAIN_MENU
    
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
            habits = habit_service.get_user_habits(user[0])
            if habits:
                message = Text.YOUR_HABITS
                for i, habit in enumerate(habits, 1):
                    message += Text.HABIT_ITEM.format(i, habit[1])
            else:
                message = Text.NO_HABITS
        else:
            message = Text.USER_NOT_FOUND
        
        await update.message.reply_text(message, reply_markup=Keyboard.get_habbit_menu())
        return State.HABBIT_MENU
    
    elif text == "Добавить":
        await update.message.reply_text(Text.ENTER_DESCRIPTION)
        return State.ADD_HABIT_DESCRIPTION
    
    elif text == "Удалить":
        tg_username = update.effective_user.username
        user = user_service.get_user_by_tg_username(tg_username)
        
        if user:
            habits = habit_service.get_user_habits(user[0])
            if habits:
                message = Text.SELECT_DELETE
                for i, habit in enumerate(habits, 1):
                    message += Text.HABIT_ITEM.format(i, habit[1])
                message += Text.ENTER_NUMBER
                await update.message.reply_text(message)
                context.user_data['habits_for_deletion'] = habits
                return State.DELETE_HABIT
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
    await update.message.reply_text(Text.ENTER_FREQUENCY)
    return State.ADD_HABIT_FREQUENCY


async def add_habit_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frequency = update.message.text.lower()
    if frequency in ["ежедневно", "еженедельно"]:
        context.user_data['habit_frequency'] = frequency
        await update.message.reply_text(Text.ENTER_TIME)
        return State.ADD_HABIT_TIME
    else:
        await update.message.reply_text(Text.INVALID_FREQUENCY)
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
    try:
        habit_number = int(update.message.text) - 1
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


def main():
    app = Application.builder().token(TOKEN).build()
    
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
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
