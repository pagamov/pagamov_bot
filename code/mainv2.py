from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from telegram.ext import CommandHandler, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler
from telegram.ext import filters, ApplicationBuilder
from telegram.ext import CallbackQueryHandler

from enum import Enum
import json

import functools
from typing import Callable, Final
from dotenv import load_dotenv
import os


Users = []


# class User:
#     def __init__(self, tg_username):
#         self.id_user


class State(Enum):
    MAIN_MENU = 1


class Keyboard:
    MAIN_MENU = \
        ReplyKeyboardMarkup([
            [KeyboardButton()],
            #
            [KeyboardButton(),
             KeyboardButton()],
            #
            [KeyboardButton()]
        ], resize_keyboard=True)

async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    text: str = update.message.text
    tg_username: str = update.effective_user.username

    await update.message.reply_text(
            text="Добро пожаловать!",
            reply_markup=Keyboard.MAIN_MENU)

    return State.MAIN_MENU


async def FROM_IDLE_MENU(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    tg_username: str = update.effective_user.username

    await update.message.reply_text(
            text="Добро пожаловать назад",
            reply_markup=Keyboard.MAIN_MENU)

    return State.MAIN_MENU


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("""Update:\n\n{}\n\nCaused error:\n\n{}""".format(update, context.error))

def main():

    load_dotenv()
    TOKEN: Final = os.getenv("TOKEN")
    app = (ApplicationBuilder().token(TOKEN).build())


    basic_filters: filters = filters.TEXT & (~filters.COMMAND)

    entry_points: list = [CommandHandler('start', start_command),
                          MessageHandler(basic_filters, FROM_IDLE_MENU)]

    states = {}

    states[State.MAIN_MENU] = \
        [MessageHandler(basic_filters, MAIN_MENU)]

    states[State.MAIN_MENU_ADMIN] = \
        [MessageHandler(basic_filters, MAIN_MENU_ADMIN)]

    states[State.NOTIFY_MENU] = \
        [MessageHandler(basic_filters, NOTIFY_MENU)]

    states[State.NOTIFY_MENU_ADD_DESCRIPTION] = \
        [MessageHandler(basic_filters, NOTIFY_MENU_ADD_DESCRIPTION)]

    states[State.NOTIFY_MENU_ADD_DATEPICK] = \
        [MessageHandler(basic_filters, NOTIFY_MENU_ADD_DATEPICK)]

    states[State.NOTIFY_MENU_ADD_TIMEPICK] = \
        [MessageHandler(basic_filters, NOTIFY_MENU_ADD_TIMEPICK)]

    states[State.HABBIT_MENU] = \
        [MessageHandler(basic_filters, HABBIT_MENU)]

    states[State.PROGRAMM_MENU] = \
        [MessageHandler(basic_filters, PROGRAMM_MENU)]

    states[State.ABOUT_ME_MENU] = \
        [MessageHandler(basic_filters, ABOUT_ME_MENU)]

    states[State.ABOUT_ME_MENU_CHANGE_NICK] = \
        [MessageHandler(basic_filters, ABOUT_ME_MENU_CHANGE_NICK)]

    states[State.ADMIN_PANEL_1] = \
        [MessageHandler(basic_filters, ADMIN_PANEL_1)]

    states[State.ADMIN_PANEL_TAIL_LOG_BOT] = \
        [MessageHandler(basic_filters, ADMIN_PANEL_TAIL_LOG_BOT)]

    states[State.ADMIN_PANEL_2] = \
        [MessageHandler(basic_filters, ADMIN_PANEL_2)]

    states[State.ADMIN_PANEL_3] = \
        [MessageHandler(basic_filters, ADMIN_PANEL_3)]

    states[ConversationHandler.END] = \
        [MessageHandler(basic_filters, handle_final)]

    for key, _ in states.items():
        states[key].append(CallbackQueryHandler(notify_queue_handler))

    app.add_handler(ConversationHandler(
        entry_points=entry_points,
        states=states,
        fallbacks=[CommandHandler('cancel', cancel_command)]
    ))

    # Обработчик для callback_data
    app.add_handler(CallbackQueryHandler(notify_queue_handler))

    # Добавление ассинхронного job который будет
    # отправлять напоминания и сообщения из очереди
    check_notify_queue_job = app.job_queue.run_repeating(check_notify_queue,
                                                         interval=5, first=1)

    app.add_error_handler(error)

    app.run_polling(poll_interval=0.8, allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()