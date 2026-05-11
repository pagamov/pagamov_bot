import os
from enum import Enum
from dotenv import load_dotenv
import time

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")


class Text:
    START = "🔗 Поиск наставника..."
    FOUND = "🔗 Наставник найден!\n\nПознакомьтесь с вашим наставником: Удачливая_Лиса_247\n\nНапишите ему сообщение, он поможет вам советом."
    INSTRUCTIONS = "Вы в чате с анонимным наставником. Напишите сообщение."
    ENDED = "❌ Беседа завершена."
    REPORT = "⚠️ Жалоба отправлена. Мы рассмотрим её."
    
    MAIN_MENU = "👤 Личный кабинет"
    FIND_BUTTON = "Найти наставника"
    MAIN_KEYBOARD = ["Назад"]


class Keyboard:
    @staticmethod
    def get_main_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.FIND_BUTTON)],
            [KeyboardButton("Назад")]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_chat_keyboard():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Пожаловаться", callback_data="report")],
            [InlineKeyboardButton("Завершить беседу", callback_data="end_chat")]
        ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        Text.MAIN_MENU,
        reply_markup=Keyboard.get_main_menu()
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == Text.FIND_BUTTON:
        await update.message.reply_text(
            Text.START,
            reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Прекратить поиск", callback_data="end_chat")]
        ])
        )
        # time.sleep(60)
        await update.message.reply_text(
            Text.FOUND + "\n\n" + Text.INSTRUCTIONS,
            # reply_markup=Keyboard.get_chat_keyboard()
        )
    elif text == "Пожаловаться":
        await update.message.reply_text(Text.REPORT + "\n\n" + Text.ENDED, reply_markup=ReplyKeyboardRemove())

    elif text == "Завершить беседу":
        await update.message.reply_text(Text.ENDED)

    else:
        await update.message.reply_text(
            text="Привет! Не хочу тебе помогать :("
            ,reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Завершить беседу"), KeyboardButton("Пожаловаться")]], resize_keyboard=True)
        )
    
    return True


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "end_chat":
        await query.edit_message_text(
            text=query.message.text + "\n\n" + Text.ENDED
        )
    elif query.data == "report":
        await query.edit_message_text(
            text=query.message.text + "\n\n" + Text.REPORT
        )


def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    app.run_polling()


if __name__ == "__main__":
    main()