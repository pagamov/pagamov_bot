import sqlite3
import os
import random
import re
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


class Text:
    MAIN_MENU_KEYBOARD = ["Напоминания", "Мои привычки", "Готовые программы", "Обо мне"]
    HABBIT_MENU_KEYBOARD = ["Мои привычки", "Добавить", "Удалить", "Назад"]
    NOTIFY_MENU_KEYBOARD = ["Мои напоминания", "Добавить", "Удалить", "Назад"]
    
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
    def get_reminder_keyboard(notify_id):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Выполнено", callback_data=f"done_{notify_id}"),
                InlineKeyboardButton("Отложить на 1 час", callback_data=f"postpone_{notify_id}")
            ]
        ])


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
    
    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id = ?"
        return self.db.fetch_one(query, (user_id,))


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


db = Database()
db.initialize_database()
user_service = UserService(db)
habit_service = HabitService(db)
notify_service = NotifyService(db)

job_queue = None


async def check_notifications(context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pending = notify_service.get_pending_notifications(current_time)

    print("check_notifications, pending", len(pending))
    
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
    
    await update.message.reply_text(
        "Добро пожаловать в бот для отслеживания привычек!",
        reply_markup=Keyboard.get_main_menu()
    )
    return State.MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Мои привычки":
        return await habit_menu(update, context)
    elif text == "Напоминания":
        return await notify_menu(update, context)
    elif text == "Готовые программы" or text == "Обо мне":
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
                return State.DELETE_HABIT
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
    try:
        notify_number = int(update.message.text) - 1
        notifies = context.user_data.get('notifies_for_deletion', [])
        
        if 0 <= notify_number < len(notifies):
            notify_id = notifies[notify_number][0]
            notify_service.delete_notification(notify_id)
            await update.message.reply_text(Text.NOTIFY_DELETED, reply_markup=Keyboard.get_notify_menu())
        else:
            await update.message.reply_text(Text.INVALID_NUMBER)
            return State.DELETE_HABIT
    except ValueError:
        await update.message.reply_text(Text.ENTER_NUMBER_VALID)
        return State.DELETE_HABIT
    
    return State.NOTIFY_MENU


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("done_"):
        notify_id = int(data.split("_")[1])
        notify_service.mark_as_done(notify_id)
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ Отмечено как выполненное")
    
    elif data.startswith("postpone_"):
        notify_id = int(data.split("_")[1])
        new_time = datetime.now() + timedelta(hours=1)
        notify_service.postpone_notification(notify_id, new_time.strftime("%Y-%m-%d %H:%M:%S"))
        await query.edit_message_text(text=f"{query.message.text}\n\n⏰ Отложено на 1 час")


def main():
    global job_queue
    
    app = Application.builder().token(TOKEN).build()
    job_queue = app.job_queue
    
    job_queue.run_repeating(check_notifications, interval=60, first=1)
    
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
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()


if __name__ == "__main__":
    main()
