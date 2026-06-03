import os
import re
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")

class State(Enum):
    MAIN = 1
    ADD_NAME = 2
    ADD_FREQUENCY = 3
    ADD_TIME = 4

class Text:
    MAIN_MENU = ["Добавить", "Назад"]
    FREQUENCY_KEYBOARD = ["Ежедневно", "Еженедельно"]
    
    ENTER_NAME = "Введите описание привычки:"
    ENTER_FREQUENCY = "Выберите частоту:"
    ENTER_TIME = "Введите время (ЧЧ:ММ):"
    INVALID_TIME = "Пожалуйста, введите время в формате ЧЧ:ММ"
    HABIT_ADDED = "✅ Привычка \"{}\" успешно добавлена!\n     Частота: {}\n     Время: {}"
    MENU = "Меню привычек:"


class Keyboard:
    @staticmethod
    def get_main_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MAIN_MENU[0]), KeyboardButton(Text.MAIN_MENU[1])]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_frequency_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.FREQUENCY_KEYBOARD[0]), KeyboardButton(Text.FREQUENCY_KEYBOARD[1])]
        ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        Text.MENU,
        reply_markup=Keyboard.get_main_menu()
    )
    return State.MAIN


async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == Text.MAIN_MENU[0]:
        await update.message.reply_text(Text.ENTER_NAME)
        return State.ADD_NAME
    
    return State.MAIN


async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['habit_name'] = update.message.text
    await update.message.reply_text(Text.ENTER_FREQUENCY, reply_markup=Keyboard.get_frequency_menu())
    return State.ADD_FREQUENCY


async def add_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frequency = update.message.text.lower()
    if frequency in ["ежедневно", "еженедельно"]:
        context.user_data['frequency'] = frequency
        await update.message.reply_text(Text.ENTER_TIME)
        return State.ADD_TIME
    else:
        await update.message.reply_text(Text.ENTER_FREQUENCY, reply_markup=Keyboard.get_frequency_menu())
        return State.ADD_FREQUENCY


async def add_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    if re.match(time_pattern, update.message.text):
        await update.message.reply_text(
            Text.HABIT_ADDED.format(
                context.user_data['habit_name'],
                context.user_data['frequency'],
                update.message.text
            ),
            reply_markup=Keyboard.get_main_menu()
        )
    else:
        await update.message.reply_text(Text.INVALID_TIME)
        return State.ADD_TIME
    
    return State.MAIN


def main():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.MAIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_handler)
            ],
            State.ADD_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)
            ],
            State.ADD_FREQUENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_frequency)
            ],
            State.ADD_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_time)
            ],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()