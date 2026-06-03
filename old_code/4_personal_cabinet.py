import os
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")


class Text:
    MENU = "👤 Личный кабинет"
    STATS = """📊 Ваша статистика:
    
• Создано привычек: 3
• Выполнено раз: 47
• Текущая серия: 12 дней
• Рекордная серия: 21 день"""

    BADGES = """🎖 Ваши бейджи:

💧 Гидра — Выполнили привычку "Пить воду" 7 дней подряд
🏃 Марафонец — Выполнили привычку 30 дней подряд
📚 Вовлеченный — Создали 5 привычек"""

    MENU_KEYBOARD = ["Мои бейджи", "Моя статистика", "Назад"]


class Keyboard:
    @staticmethod
    def get_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MENU_KEYBOARD[0])],
            [KeyboardButton(Text.MENU_KEYBOARD[1]), KeyboardButton(Text.MENU_KEYBOARD[2])]
        ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        Text.MENU,
        reply_markup=Keyboard.get_menu()
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Моя статистика":
        await update.message.reply_text(
            Text.STATS,
            reply_markup=Keyboard.get_menu()
        )
    elif text == "Мои бейджи":
        await update.message.reply_text(
            Text.BADGES,
            reply_markup=Keyboard.get_menu()
        )
    elif text == "Назад":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=Keyboard.get_menu()
        )
    
    return True


def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    
    app.run_polling()


if __name__ == "__main__":
    main()