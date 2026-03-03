
from telegram import Update
from telegram.ext import ContextTypes
import re
from datetime import datetime, time, timedelta

from database import Database, User
from const import *

async def HABBIT_MENU(update: Update, 
                      _: ContextTypes.DEFAULT_TYPE) -> int:

    text: str = update.message.text
    tg_username: str = update.effective_user.username

    # HABBIT_MENU_KEYBOARD: list[str] = \
    #     ["Мои привычки", "Добавить", "Удалить",
    #      "Изменить", "Настройки", "Назад"]

    if text == Text.HABBIT_MENU_KEYBOARD[0]:
        # TODO закончить путь
        await update.message.reply_text(
            text="Модуль пока не работает",
            reply_markup=Keyboard.HABBIT_MENU
        )
        return State.HABBIT_MENU

    elif text == Text.HABBIT_MENU_KEYBOARD[1]:
        # TODO закончить путь
        await update.message.reply_text(
            text="Модуль пока не работает",
            reply_markup=Keyboard.HABBIT_MENU
        )
        return State.HABBIT_MENU

    elif text == Text.HABBIT_MENU_KEYBOARD[2]:
        # TODO закончить путь
        await update.message.reply_text(
            text="Модуль пока не работает",
            reply_markup=Keyboard.HABBIT_MENU
        )
        return State.HABBIT_MENU

    elif text == Text.HABBIT_MENU_KEYBOARD[3]:
        # TODO закончить путь
        await update.message.reply_text(
            text="Модуль пока не работает",
            reply_markup=Keyboard.HABBIT_MENU
        )
        return State.HABBIT_MENU

    elif text == Text.HABBIT_MENU_KEYBOARD[4]:
        # TODO закончить путь
        await update.message.reply_text(
            text="Модуль пока не работает",
            reply_markup=Keyboard.HABBIT_MENU
        )
        return State.HABBIT_MENU

    elif text == Text.HABBIT_MENU_KEYBOARD[-1]:
        match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text(
                        Text.RETURN_TO_MENU_ADMIN,
                        reply_markup=Keyboard.MAIN_MENU_ADMIN)

                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text(
                        Text.RETURN_TO_MENU,
                        reply_markup=Keyboard.MAIN_MENU)

                    return State.MAIN_MENU

    return State.HABBIT_MENU
            