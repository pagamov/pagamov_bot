import os
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")


USER_BADGES = [
    {"name": "💧 Гидра", "description": "Выполнили привычку 'Пить воду' 7 дней подряд"},
    {"name": "🏃 Марафонец", "description": "Выполнили привычку 30 дней подряд"},
    {"name": "📚 Библиофил", "description": "Создали 5 привычек"},
]


class Text:
    MENU = "🎖 Мои бейджи"
    MAIN_MENU = ["Личный кабинет", "Назад"]
    
    BADGES_HEADER = "🎖 Ваши бейджи:\n\n"
    
    BADGE_ITEM = "{} — {}\n"
    
    NO_BADGES = "У вас пока нет бейджей. Начните выполнять привычки!"
    
    STATS = "📊 Ваша статистика:\n\n• Создано привычек: 3\n• Выполнено раз: 47\n• Текущая серия: 12 дней"


class Keyboard:
    @staticmethod
    def get_main_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MAIN_MENU[0])],
            [KeyboardButton(Text.MAIN_MENU[1])]
        ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        Text.BADGES_HEADER + "".join(
            Text.BADGE_ITEM.format(b["name"], b["description"]) for b in USER_BADGES
        ),
        reply_markup=Keyboard.get_main_menu()
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Личный кабинет":
        await update.message.reply_text(
            Text.STATS + "\n\n" + Text.BADGES_HEADER + "".join(
                Text.BADGE_ITEM.format(b["name"], b["description"]) for b in USER_BADGES
            ),
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