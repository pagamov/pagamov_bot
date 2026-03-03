from telegram import Update, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from telegram.ext import CommandHandler, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler
from telegram.ext import filters, ApplicationBuilder
from telegram.ext import CallbackQueryHandler

from telegram import Update

from const import *
from database import *

async def MAIN_MENU_ADMIN(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    text: str = update.message.text
    tg_username: str = update.effective_user.username

    if text == Text.MAIN_MENU_ADMIN_KEYBOARD[0]:
        await update.message.reply_text(
            Text.MAIN_MENU_ADMIN_t0, reply_markup=Keyboard.NOTIFY_MENU)

        return State.NOTIFY_MENU

    elif text == Text.MAIN_MENU_ADMIN_KEYBOARD[2]:
        await update.message.reply_text(
            Text.MAIN_MENU_ADMIN_t2, reply_markup=Keyboard.HABBIT_MENU)

        return State.HABBIT_MENU

    elif text == Text.MAIN_MENU_ADMIN_KEYBOARD[3]:
        await update.message.reply_text(
            Text.MAIN_MENU_ADMIN_t3, reply_markup=Keyboard.PROGRAMM_MENU)

        return State.PROGRAMM_MENU

    elif text == Text.MAIN_MENU_ADMIN_KEYBOARD[4]:
        await update.message.reply_text(
            Text.MAIN_MENU_ADMIN_t4, reply_markup=Keyboard.ABOUT_ME_MENU)

        return State.ABOUT_ME_MENU

    elif text == Text.MAIN_MENU_ADMIN_KEYBOARD[5]:
        await update.message.reply_text(
            Text.MAIN_MENU_ADMIN_t5, reply_markup=Keyboard.ADMIN_PANEL_1)

        return State.ADMIN_PANEL_1

    else:
        if User().is_admin(tg_username):
            return State.MAIN_MENU_ADMIN

        else:
            State.MAIN_MENU

async def ADMIN_PANEL_1(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:

    text: str = update.message.text
    tg_username: str = update.effective_user.username

    if text == Text.ADMIN_PANEL_1_KEYBOARD[0]:
        await update.message.reply_text(
            Text.ADMIN_PANEL_1_t0,
            reply_markup=ReplyKeyboardRemove())

        return State.ADMIN_PANEL_TAIL_LOG_BOT

    elif text == Text.ADMIN_PANEL_1_KEYBOARD[1]:
        Database().run_query(
            Text.ADMIN_PANEL_1_t1.format(
                context._chat_id, tg_username, tg_username))

        await update.message.reply_text(
            Text.ADMIN_PANEL_1_t2, reply_markup=Keyboard.ADMIN_PANEL_1)

    elif text == Text.ADMIN_PANEL_1_KEYBOARD[-2]:  # Назад
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

    elif text == Text.ADMIN_PANEL_1_KEYBOARD[-1]:  # >
        await update.message.reply_text(
            'Админка 2', reply_markup=Keyboard.ADMIN_PANEL_2)
        return State.ADMIN_PANEL_2

    else:
        return State.ADMIN_PANEL_1



async def ADMIN_PANEL_TAIL_LOG_BOT(update: Update,
                                   _: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить последние строчки таблицы log_bot
    """

    logger = Logger()
    text: str = update.message.text

    try:
        int(text)
    except ValueError:
        await update.message.reply_text("Не похоже на число.. Давай еще раз...")
        return State.ADMIN_PANEL_TAIL_LOG_BOT

    if int(text) <= 0:
        await update.message.reply_text("Мне бы число больше нуля...")
        return State.ADMIN_PANEL_TAIL_LOG_BOT
    else:
        res: list[str] | str = logger.tail_log_bot(int(text))

        if type(res) == str:
            await update.message.reply_text(
                res, reply_markup=Keyboard.ADMIN_PANEL_1)

        else:
            # Нам тут важно чтобы отчет не вылез за пределы размера сообщения.
            # Если оно больше TELEGRAM_MAX_MESSAGE_SIZE
            # то начинаем заполнять следующую ячейку.
            # Потом пачкой все отправляем.

            message_storage: list[str] = []
            storage: str = ''
            for row in res:
                if len(storage) + len(row) > TELEGRAM_MAX_MESSAGE_SIZE:
                    message_storage.append(storage)
                    storage = ''

                storage += row

            message_storage.append(storage)

            for message in message_storage:
                await update.message.reply_text(
                    message, reply_markup=Keyboard.ADMIN_PANEL_1)

        return State.ADMIN_PANEL_1

async def ADMIN_PANEL_2(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    text: str = update.message.text
    tg_username: str = update.effective_user.username
    match text:
        case Text.ADMIN_PANEL_backward:
            await update.message.reply_text(
                Text.ADMIN_PANEL_2_t0, reply_markup=Keyboard.ADMIN_PANEL_1)

            return State.ADMIN_PANEL_1

        case Text.ADMIN_PANEL_forward:
            await update.message.reply_text(
                Text.ADMIN_PANEL_2_t1, reply_markup=Keyboard.ADMIN_PANEL_3)

            return State.ADMIN_PANEL_3

        case Text.ADMIN_PANEL_return:
            match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text(
                        Text.RETURN_TO_MENU_ADMIN,
                        reply_markup=Keyboard.MAIN_MENU_ADMIN)

                    return State.MAIN_MENU_ADMIN

                case _:
                    await update.message.reply_text(
                        Text.RETURN_TO_MENU, reply_markup=Keyboard.MAIN_MENU)

                    return State.MAIN_MENU

        case _:
            return State.ADMIN_PANEL_2

async def ADMIN_PANEL_3(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    text: str = update.message.text
    tg_username: str = update.effective_user.username
    match text:
        case Text.ADMIN_PANEL_backward:
            await update.message.reply_text(
                Text.ADMIN_PANEL_3_t0, reply_markup=Keyboard.ADMIN_PANEL_2)

            return State.ADMIN_PANEL_2

        case Text.ADMIN_PANEL_return:

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
        case _:
            return State.ADMIN_PANEL_3