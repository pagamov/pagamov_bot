import sqlite3
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.ext import CallbackQueryHandler, ContextTypes, Application, CommandHandler, MessageHandler, filters, ConversationHandler
from queue import Queue
import httpx
import asyncio

import os
from dotenv import load_dotenv


# %% CONST SECTION
# 

class DEBUG:
    def __init__(self):
        self.debugMode = True

class KEYBOARDS:
    """
    Тут находятся все возможные ReplyKeyboardMarkup с InlineKeyboardButton и callback_data
    """
    def __init__(self):
        self.SAMPLE = ReplyKeyboardMarkup([
            [InlineKeyboardButton(text="", callback_data=""), InlineKeyboardButton(text="", callback_data="")],
            [InlineKeyboardButton(text="", callback_data=""), InlineKeyboardButton(text="", callback_data="")],
            [InlineKeyboardButton(text="", callback_data=""), InlineKeyboardButton(text="", callback_data="")],
            [InlineKeyboardButton(text="", callback_data="")]
        ])

        self.MAIN = ReplyKeyboardMarkup([
            [InlineKeyboardButton(text="Привычки", callback_data=""), InlineKeyboardButton(text="Напоминания", callback_data="")],
            [InlineKeyboardButton(text="Заметки", callback_data=""), InlineKeyboardButton(text="", callback_data="")],
            [InlineKeyboardButton(text="", callback_data=""), InlineKeyboardButton(text="", callback_data="")],
            [InlineKeyboardButton(text="", callback_data="")]
        ])

        self.HABIT = ReplyKeyboardMarkup([
            [InlineKeyboardButton(text="Создать", callback_data=""), InlineKeyboardButton(text="Показать все", callback_data="")],
            [InlineKeyboardButton(text="Статистика", callback_data=""), InlineKeyboardButton(text="", callback_data="")],
            [InlineKeyboardButton(text="", callback_data=""), InlineKeyboardButton(text="", callback_data="")],
            [InlineKeyboardButton(text="Назад", callback_data="")]
        ])

class SQLITE(DEBUG):
    """
    Класс базы данных. Начальная инициация базы данных. Заполнение структуры базы данных.
    """
    def __init__(self):
        """
        Создание пути и кода инициации таблиц
        """

        super().__init__()

        self.location : str = './db.sqlite3'
        self.name : str = 'db'

        # list of tables in db
        self.tables : list[str] = ["USER", "HABIT"]
        
        # const on init text to allocate tables
        self.onInit : dict[str,str] = {
            f"{self.tables[0]}" : f"""
                        CREATE TABLE IF NOT EXISTS {self.tables[0]} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE,
                            chat TEXT NOT NULL UNIQUE,
                            active INTEGER,
                            role TEXT NOT NULL
                        );
                        """,
            f"{self.tables[1]}" : f"""
                        CREATE TABLE IF NOT EXISTS {self.tables[1]} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            FOREIGN KEY user_id REFERENCES {self.tables[0]} (id),
                            active INTEGER,
                            time TEXT,
                            date TEXT
                        );
                        """,
        }

    def clearDatabase(self) -> None:
        """
        Удаление всех таблиц из базы данных
        """
        conn : sqlite3.Connection = sqlite3.connect(self.location)
        cur : sqlite3.Cursor = conn.cursor()

        for i, table in enumerate(self.tables):
            try:
                cur.execute(f"DROP TABLE {self.onInit[table]}")
            except:
                continue
        conn.commit()

        cur.close()
        conn.close()

    def createTables(self) -> None:
        """
        Инициация базы данных по пути self.location и создание таблиц используя код в self.onInit
        """
        if self.debugMode:
            self.clearDatabase()

        conn : sqlite3.Connection = sqlite3.connect(self.location)
        cur : sqlite3.Cursor = conn.cursor()

        for i, table in enumerate(self.tables):
            cur.execute(self.onInit[table])

        # TODO check if this work
        conn.commit()

        cur.close()
        conn.close()

class WhiteList:
    def __init__(self) -> None:
        """
        Если self.use равно True - данный механизм используется для работы приложения
        """
        self.use : bool = True
        self.allowed : list[str] = ["pagamov"]

class UserRoles:
    def __init__(self) -> None:
        self.ADMIN : str = "ADMIN"
        self.USER : str = "USER"

class UserPermission:
    def __init__(self) -> None:
        pass

# %% CLASS SECTION
# 

class User:
    """

    """
    def __init__(self) -> None:
        pass

class Database(SQLITE):
    """
    Основные функции для записи и получения данных из базы данных.
    """
    def __init__(self):
        super().__init__()

    def userInDatabase(self, username : str) -> bool:
        """
        check if user in database
        """
        con : sqlite3.Connection
        cur : sqlite3.Cursor
        with sqlite3.connect(self.location) as con:
            with con.cursor() as cur:
                cur.execute(f"SELECT * FROM {self.tables[0]} WHERE username = {username}")
                rows = cur.fetchall()
                return len(rows) > 0
        return False



# %% CommandHandler SECTION
# 

async def start(update: Update, context: CallbackContext) -> None:
    """
    Первичная настройка человека, если он есть в базе, то пишем привет. Если его нет просим данные.
    """
    # Проверка на белый список
    whiteList : WhiteList = WhiteList()
    if whiteList.use and update.effective_user.username not in whiteList.allowed:
        await update.message.reply_text("Вас нет в разрешенном списке. Обратитесь к администратору.")
    else:

        if update.effective_user.username == "shaurma_1696":
            await update.message.reply_text("Спасибо за визит, записал все ваши данные!")
        else:
            keyboard = ReplyKeyboardMarkup([[KeyboardButton("b1")],[KeyboardButton("b2")]], resize_keyboard=True)
            await update.message.reply_text('Hello! I am your bot.',  reply_markup=keyboard)
            update.message.re


# %% CallbackQueryHandler SECTION
# 

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()



    # Example: Respond based on callback data
    if query.data == "1":
        await query.message.reply_text("You clicked Button 1")
    elif query.data == "2":
        await query.message.reply_text("You clicked Button 2")
    else:
        await query.message.reply_text(f"Unknown callback data: {query.data}")


# %% MessageHandler SECTION
# 

async def messageH(update: Update, context: CallbackContext) -> None:
    
    id = update.effective_chat.id
    name = update.effective_user.username

    if name == "shaurma_1696":
        await update.message.reply_text("Привет красотка! Я тебя люблю!")
    else:
        await update.message.reply_text(f"chat id : {id}, login : {name}")

async def echo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(update.message.text)


# %% add_error_handler SECTION
# 

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update: {update} caused error {context.error}')


# %% MAIN SECTION
# 

def main() -> None:

    # ENV SECTION
    load_dotenv()

    # DB SECTION
    db : SQLITE = SQLITE()
    db.createTables()

    # BOT SECTION
    app = Application.builder().token(os.getenv("TOKEN")).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(handle_query))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), messageH))

    app.add_error_handler(error)
    app.run_polling(poll_interval=0.5)
    

# %% ENTERY SECTION
#

if __name__ == '__main__':
    main()