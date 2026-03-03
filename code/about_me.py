
from telegram import Update
from telegram.ext import ContextTypes

from database import *

async def ABOUT_ME_MENU(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:

    text: str = update.message.text
    tg_username: str = update.effective_user.username

    user = User()

    if text == Text.ABOUT_ME_MENU_KEYBOARD[0]:
        context.user_data["new_bot_username"] = user.createBot_username()
        cur_username: str = user.get_bot_username(tg_username)

        responce = "А что вам не нравится в {}?\n"
        responce += "Сгенерируем вам новый ник...\nКак вам {}?"

        await update.message.reply_text(
            responce.format(
                cur_username, context.user_data["new_bot_username"]),
            reply_markup=Keyboard.ABOUT_ME_CHANGE_NICK)

        return State.ABOUT_ME_MENU_CHANGE_NICK

    elif text == Text.ABOUT_ME_MENU_KEYBOARD[-1]:
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
    else:
        return State.ABOUT_ME_MENU


async def ABOUT_ME_MENU_CHANGE_NICK(update: Update,
                                    context: ContextTypes.DEFAULT_TYPE) -> int:

    text: str = update.message.text
    tg_username: str = update.effective_user.username

    if text == "Попробуем еще раз":

        context.user_data["new_bot_username"] = User().createBot_username()

        await update.message.reply_text(
                "А как вам {}?".format(
                context.user_data["new_bot_username"]),
            reply_markup=Keyboard.ABOUT_ME_CHANGE_NICK)

        return State.ABOUT_ME_MENU_CHANGE_NICK

    elif text == "Мне нравится":
        # Применить текущий ник к пользователю

        query = '''
        update user
        set bot_username="{}"
        where tg_username="{}";'''
        
        Database().run_query(
            query.format(
                context.user_data["new_bot_username"], tg_username))

        await update.message.reply_text(
            "Изменения сохранены",
            reply_markup=Keyboard.ABOUT_ME_MENU)

        return State.ABOUT_ME_MENU

    elif text == "Оставить все как было":
        await update.message.reply_text(
            Text.RETURN_TO_MENU, reply_markup=Keyboard.ABOUT_ME_MENU)
        return State.ABOUT_ME_MENU

    return State.ABOUT_ME_MENU_CHANGE_NICK