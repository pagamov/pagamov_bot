import os
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")

ALL_BADGES = [
    {"name": "💧 Гидра", "earned": True, "progress": 7, "target": 7, "desc": "Выполнить привычку 'Пить воду' 7 дней"},
    {"name": "🏃 Марафонец", "earned": False, "progress": 12, "target": 30, "desc": "Выполнить привычку 30 дней"},
    {"name": "📚 Вовлеченный", "earned": True, "progress": 5, "target": 5, "desc": "Создать 5 привычек"},
    {"name": "🌟 Перфекционист", "earned": False, "progress": 3, "target": 7, "desc": "Не пропускать 7 дней"},
    {"name": "🔥 Энерджайзер", "earned": False, "progress": 0, "target": 100, "desc": "Выполнить 100 привычек"},
]


class Text:
    MENU = "🏆 Прогресс к бейджам"
    MAIN_MENU = ["Личный кабинет", "Назад"]
    
    EARNED = "{} ✅ — {}"
    LOCKED = "{} ⬜ — {} (прогресс: {}/{})"
    LOCKED_NO_PROGRESS = "🔒 {} — {} (прогресс: 0/{})"
    
    HEADER = "🏆 Прогресс к бейджам:\n\n"


class Keyboard:
    @staticmethod
    def get_main_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MAIN_MENU[0])],
            [KeyboardButton(Text.MAIN_MENU[1])]
        ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = Text.HEADER
    
    for badge in ALL_BADGES:
        if badge["earned"]:
            message += Text.EARNED.format(badge["name"], badge["desc"]) + "\n"
        elif badge["progress"] > 0:
            message += Text.LOCKED.format(badge["name"], badge["desc"], badge["progress"], badge["target"]) + "\n"
        else:
            message += Text.LOCKED_NO_PROGRESS.format(badge["name"], badge["desc"], badge["target"]) + "\n"
    
    await update.message.reply_text(
        message,
        reply_markup=Keyboard.get_main_menu()
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Личный кабинет":
        return await start(update, context)
    
    return True


def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    
    app.run_polling()


if __name__ == "__main__":
    main()