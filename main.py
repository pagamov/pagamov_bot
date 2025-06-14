import sqlite3
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters, ConversationHandler
from queue import Queue
import httpx
import asyncio

import os
from dotenv import load_dotenv

# 
# CONST SECTION
# 

class SQLITE:
    def __init__(self):
        self.location : str = './db.sqlite3'
        self.name : str = 'db'

        # list of tables in db
        self.tables : list[str] = ["USERS"]
        
        # const on init text to allocate tables
        self.onInit : dict[str,str] = {
            "USERS" : f"""
                        CREATE TABLE IF NOT EXISTS {self.tables[0]} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE
                        );"""
        }
    
    def init(self) -> None:
        """
        init db in self.location and init tables with self.onInit
        """
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
        self.allowed : list[str] = ["pagamov"]

class UserRoles:
    def __init__(self) -> None:
        self.ADMIN : str = "ADMIN"
        self.USER : str = "USER"

class UserPermission:
    def __init__(self) -> None:
        pass

# 
# CLASS SECTION
# 

class User:
    """

    """
    def __init__(self) -> None:
        pass

class Database:
    """
    
    """
    def __init__(self) -> None:
        pass




# async def test_connection():
#     try:
#         with httpx.AsyncClient() as client:
#             response = await client.get(f'https://api.telegram.org/bot{os.getenv("TOKEN")}/getMe')
#             print(response.json())
#     except httpx.ConnectError as e:
#         print(f"Connection error: {e}")


async def start(update: Update, context: CallbackContext) -> None:

    if update.effective_user.username == "shaurma_1696":
        await update.message.reply_text("Спасибо за визит, записал все ваши данные!")
    else:
        keyboard = ReplyKeyboardMarkup([[KeyboardButton("b1")],[KeyboardButton("b2")]], resize_keyboard=True)
        await update.message.reply_text('Hello! I am your bot.',  reply_markup=keyboard)
    

async def messageH(update: Update, context: CallbackContext) -> None:
    
    id = update.effective_chat.id
    name = update.effective_user.username

    if name == "shaurma_1696":
        await update.message.reply_text("Привет красотка! Я тебя люблю!")
    else:
        await update.message.reply_text(f"chat id : {id}, login : {name}")

async def echo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(update.message.text)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update: {update} caused error {context.error}')


# 
# MAIN SECTION
# 

def main() -> None:

    # ENV SECTION
    load_dotenv()

    # DB SECTION
    db : SQLITE = SQLITE()
    db.init()


    # await test_connection()

    # BOT SECTION
    app = Application.builder().token(os.getenv("TOKEN")).build()
    app.add_handler(CommandHandler("start", start))


    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), messageH))

    app.add_error_handler(error)
    app.run_polling(poll_interval=0.8)

# 
# ENTERY SECTION
# 

if __name__ == '__main__':
    main()