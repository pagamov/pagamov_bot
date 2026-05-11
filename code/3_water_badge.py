import os
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")

PROGRAMS = [
    {"id": "water_twice", "description": "Пить воду дважды в день", "time": "09:00"},
    {"id": "morning_exercise", "description": "Зарядка по утрам", "time": "07:00"},
    {"id": "read_books", "description": "Читать книги 30 минут", "time": "21:00"},
    {"id": "meditation", "description": "Медитация перед сном", "time": "22:00"},
]


class Text:
    BADGE_EARNED = "🎖 Вам выдан новый бейдж!"
    BADGE_NAME = "💧 Гидра"
    BADGE_DESCRIPTION = "Вы выполнили привычку \"Пить воду\" 7 дней подряд"
    BADGE_ICON = "💧"
    MENU = "Меню:"
    MAIN_KEYBOARD = ["Мои бейджи", "Обо мне", "Назад"]
    
    YOUR_BADGES = "🎖 Ваши бейджи:"
    BADGE_LIST = "💧 Гидра — Вы выполнили привычку \"Пить воду\" 7 дней подряд"
    NO_BADGES = "У вас пока нет бейджей. Начните выполнять привычки!"


class Keyboard:
    @staticmethod
    def get_main_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MAIN_KEYBOARD[0])],
            [KeyboardButton(Text.MAIN_KEYBOARD[1]), KeyboardButton(Text.MAIN_KEYBOARD[2])]
        ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        Text.BADGE_EARNED + "\n\n" + Text.BADGE_ICON + " " + Text.BADGE_NAME + "\n" + Text.BADGE_DESCRIPTION + "\n\n🎉 Поздравляем!",
        reply_markup=Keyboard.get_main_menu()
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Мои бейджи":
        await update.message.reply_text(
            Text.YOUR_BADGES + "\n\n" + Text.BADGE_LIST,
            reply_markup=Keyboard.get_main_menu()
        )
    elif text == "Обо мне":
        await update.message.reply_text(
            "👤 Личный кабинет\n\nСтатистика:\n• Создано привычек: 3\n• Выполнено раз: 15\n• Текущая серия: 7 дней",
            reply_markup=Keyboard.get_main_menu()
        )
    elif text == "Назад":
        await update.message.reply_text(
            Text.MENU,
            reply_markup=Keyboard.get_main_menu()
        )
    
    return True


def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    
    app.run_polling()


if __name__ == "__main__":
    main()