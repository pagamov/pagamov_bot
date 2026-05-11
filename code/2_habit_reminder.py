import os
import random
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")


class Text:
    REMINDER = "🔔 Время для привычки!"
    DESCRIPTION = "Пить воду каждый день"
    FREQUENCY = "Ежедневно"
    DONE = "✅ Выполнено!"
    POSTPONED = "⏰ Отложено на 1 час"
    MENU = "Меню привычек:"
    MAIN_KEYBOARD = ["Мои привычки", "Назад"]


class Keyboard:
    @staticmethod
    def get_main_menu():
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MAIN_KEYBOARD[0])],
            [KeyboardButton(Text.MAIN_KEYBOARD[1])]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_habit_keyboard(habit_id):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{habit_id}"),
                InlineKeyboardButton("⏰ Отложить", callback_data=f"postpone_{habit_id}")
            ]
        ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать!",
        reply_markup=Keyboard.get_main_menu()
    )


async def habits_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Мои привычки":
        await update.message.reply_text(
            "📋 Ваши привычки:\n\n1. Пить воду каждый день (Ежедневно)\n   Время: 09:00",
            reply_markup=Keyboard.get_main_menu()
        )
    
    return True


async def show_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    habit_id = 1
    await update.message.reply_text(
        f"{Text.REMINDER}\n\n{Text.DESCRIPTION}\n({Text.FREQUENCY})",
        reply_markup=Keyboard.get_habit_keyboard(habit_id)
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("done_"):
        await query.edit_message_text(
            text=f"{query.message.text}\n\n{Text.DONE}"
        )
    elif query.data.startswith("postpone_"):
        await query.edit_message_text(
            text=f"{query.message.text}\n\n{Text.POSTPONED}"
        )


def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", show_reminder))
    app.add_handler(CommandHandler("reminder", show_reminder))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, habits_menu))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    app.run_polling()


if __name__ == "__main__":
    main()