# utils.py
from telegram import Update
from telegram.ext import ContextTypes
from database import User
from const import Text, Keyboard, State

def get_user_info(update: Update) -> tuple[str, int]:
    """Получение информации о пользователе"""
    text = update.message.text
    tg_username = update.effective_user.username
    return text, tg_username


async def return_to_main_menu(update: Update, tg_username: str) -> int:
    """Универсальная функция возврата в главное меню"""
    if User().is_admin(tg_username):
        await update.message.reply_text(
            Text.RETURN_TO_MENU_ADMIN,
            reply_markup=Keyboard.MAIN_MENU_ADMIN)
        return State.MAIN_MENU_ADMIN
    else:
        await update.message.reply_text(
            Text.RETURN_TO_MENU,
            reply_markup=Keyboard.MAIN_MENU)
        return State.MAIN_MENU