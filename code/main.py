from telegram import Update, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from telegram.ext import CommandHandler, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler
from telegram.ext import filters, ApplicationBuilder
from telegram.ext import CallbackQueryHandler

import json

import functools
from typing import Callable

from habbit import *
from const import *
from database import *
from notify import *

# TODO сделать изменение внутреннего аноним ника
# TODO после смены ника, нужно в базе поменять ВСЕ логи где он участвует на него
# TODO удалять через админскую консоль пользователей
# TODO создавать через консоль юзеров


# Wrapper section

def log_chat_message(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(update: Update,
                      context: ContextTypes.DEFAULT_TYPE,
                      *args, **kwargs) -> int:

        chat_id = update.effective_chat.id if update.effective_chat else 'N/A'
        message_id = update.message.message_id if update.message else 'N/A'
        print(f"Chat ID: {chat_id}, Message ID: {message_id}")
        return await func(update, context, *args, **kwargs)
    return wrapper

# Handler section


async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """Тут мы начинаем работу в режиме диалога. Возвращаем меню.
    """

    text: str = update.message.text
    tg_username: str = update.effective_user.username
    user: User = User()
    bot_username: str = user.get_bot_username(tg_username)

    Logger().log(Text.start_command_t0.format(update.message.chat.id,
                                              tg_username,
                                              update.message.chat.type, text))

    if user.get_id_user(tg_username) > 0:
        if user.is_admin(tg_username):
            await update.message.reply_text(
                Text.start_command_t3.format(bot_username),
                reply_markup=Keyboard.MAIN_MENU_ADMIN)

            return State.MAIN_MENU_ADMIN
        else:
            await update.message.reply_text(
                Text.start_command_t1.format(bot_username),
                reply_markup=Keyboard.MAIN_MENU)

            return State.MAIN_MENU
    else:
        user.createUser(tg_username)

        if user.is_admin(tg_username):
            await update.message.reply_text(
                Text.start_command_t2.format(bot_username),
                reply_markup=Keyboard.MAIN_MENU_ADMIN)

            return State.MAIN_MENU_ADMIN
        else:
            await update.message.reply_text(
                Text.start_command_t2.format(bot_username),
                reply_markup=Keyboard.MAIN_MENU)

            return State.MAIN_MENU

async def FROM_IDLE_MENU(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """Когда бот не работает и потом запускается, 
    пользователь может быть на другой клавиатуре посреди другого этапа.
    Чтобы вернуться к основному меню нажатием на клавишу, 
    добавлен такой entry_points
    """

    tg_username: str = update.effective_user.username

    if User().is_admin(tg_username):
        await update.message.reply_text(
            text=Text.FROM_IDLE_MENU_t0,
            reply_markup=Keyboard.MAIN_MENU_ADMIN)

        return State.MAIN_MENU_ADMIN
    else:
        await update.message.reply_text(
            text=Text.FROM_IDLE_MENU_t1,
            reply_markup=Keyboard.MAIN_MENU)

        return State.MAIN_MENU


async def cancel_command(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=Text.cancel_command_t0)


async def MAIN_MENU(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    text: str = update.message.text
    tg_username: str = update.effective_user.username

    if text == Text.MAIN_MENU_KEYBOARD[0]:
        await update.message.reply_text(
            Text.MAIN_MENU_t0,
            reply_markup=Keyboard.NOTIFY_MENU)

        return State.NOTIFY_MENU

    elif text == Text.MAIN_MENU_KEYBOARD[2]:
        await update.message.reply_text(
            Text.MAIN_MENU_t2, reply_markup=Keyboard.HABBIT_MENU)

        return State.HABBIT_MENU

    elif text == Text.MAIN_MENU_KEYBOARD[3]:
        await update.message.reply_text(
            Text.MAIN_MENU_t3, reply_markup=Keyboard.PROGRAMM_MENU)

        return State.PROGRAMM_MENU

    elif text == Text.MAIN_MENU_KEYBOARD[4]:
        await update.message.reply_text(
            Text.MAIN_MENU_t4, reply_markup=Keyboard.ABOUT_ME_MENU)

        return State.ABOUT_ME_MENU

    else:
        if User().is_admin(tg_username):
            return State.MAIN_MENU_ADMIN

        return State.MAIN_MENU


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


async def PROGRAMM_MENU(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    text: str = update.message.text
    tg_username: str = update.effective_user.username
    match text:

        case "Назад":
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
            return State.PROGRAMM_MENU


async def ABOUT_ME_MENU(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:

    text: str = update.message.text
    tg_username: str = update.effective_user.username

    user = User()

    if text == Text.ABOUT_ME_MENU_KEYBOARD[0]:
        context.user_data["new_bot_username"] = user.createBot_username()
        cur_username: str = user.get_bot_username(tg_username)

        await update.message.reply_text(
            Text.ABOUT_ME_MENU_CHANGE_NICK_t0.format(
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

    if text == Text.ABOUT_ME_MENU_CHANGE_NICK_t2:
        context.user_data["new_bot_username"] = User().createBot_username()

        await update.message.reply_text(
            Text.ABOUT_ME_MENU_CHANGE_NICK_t1.format(
                context.user_data["new_bot_username"]),
            reply_markup=Keyboard.ABOUT_ME_CHANGE_NICK)

        return State.ABOUT_ME_MENU_CHANGE_NICK

    elif text == Text.ABOUT_ME_MENU_CHANGE_NICK_t4:
        # Применить текущий ник к пользователю
        Database().run_query(
            Text.ABOUT_ME_MENU_CHANGE_NICK_t6.format(
                context.user_data["new_bot_username"], tg_username))

        await update.message.reply_text(
            Text.ABOUT_ME_MENU_CHANGE_NICK_t5,
            reply_markup=Keyboard.ABOUT_ME_MENU)

        return State.ABOUT_ME_MENU

    elif text == Text.ABOUT_ME_MENU_CHANGE_NICK_t3:
        await update.message.reply_text(
            Text.RETURN_TO_MENU, reply_markup=Keyboard.ABOUT_ME_MENU)
        return State.ABOUT_ME_MENU

    return State.ABOUT_ME_MENU_CHANGE_NICK


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


async def handle_final(update: Update, _: ContextTypes.DEFAULT_TYPE):
    pass


async def check_notify_queue(context: ContextTypes.DEFAULT_TYPE):
    notify_to_send = Database().get_from_query(f"""
        SELECT id_notify, chat_id, description
            FROM notify
            WHERE sent = 0 and time_notify <= DATETIME('now', '+3 hours')
    """)

    if len(notify_to_send) != 0:
        for notify in notify_to_send:
            id = notify[0]
            chat_id = notify[1]
            text = notify[2]

            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Выполнил",
                                          callback_data=json.dumps(
                                              {"text": f"notify_set_done",
                                               "id": id})),
                     InlineKeyboardButton("Отложить",
                                          callback_data=json.dumps(
                                              {"text": f"notify_delay",
                                               "id": id}))
                     ]]))

            Database().run_query(f"""
                UPDATE notify
                SET sent=1
                WHERE id_notify = {id}
            """)


async def notify_queue_handler(update: Update, _):
    query = update.callback_query
    callback_data = json.loads(query.data)

    await query.answer()

    if callback_data['text'] == "notify_set_done":
        id = callback_data['id']
        Database().run_query(f"""
            UPDATE notify
            SET done = 1
            WHERE id_notify = {int(id)}
        """)
        await query.edit_message_text(text="Выполнение подтверждено")

    elif callback_data['text'] == "notify_delay":
        id = callback_data['id']
        # await query.edit_message_text(text="Отложим на")
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("1 min",
                                       callback_data=json.dumps(
                                           {"text": "notify_delay_1min",
                                            "id": id}))
                  ]]))

    elif callback_data['text'] == "notify_delay_1min":
        id = callback_data['id']
        Database().run_query(f"""
            UPDATE notify
            SET sent = 0, time_notify=DATETIME('now', '+3 hour','+1 minute')
            WHERE id_notify = {int(id)}
        """)
        await query.edit_message_text(text="Отложил на 1 мин.")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import html
    import traceback
    # print(Text.error_t0.format(update, context.error))
    # await context.bot.send_message(chat_id=321911494,
    #        text=f"Bot Error:\n<code>{html.escape(str(context.error))}</code>",
    #        parse_mode='HTML')

    # print("Exception while handling an update: ", exc_info=context.error)

    tb_list = traceback.format_exception(None, context.error,
                                         context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2,
                                                ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(
            str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(
            str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    await context.bot.send_message(
        chat_id=321911494, text=message, parse_mode=ParseMode.HTML
    )


def main():
    Database().firstInitDatabase()

    try:
        Logger().log("Starting bot...")
        app = (ApplicationBuilder()
               .token(TOKEN)
               .build())
    except Exception as e:
        Logger().log(e, level='CRITICAL')

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
    
    states[State.NOTIFY_MENU_DELETE] = \
        [MessageHandler(basic_filters, NOTIFY_DELETE)]

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

    try:
        Logger().log("Polling bot...")
        app.run_polling(poll_interval=0.8, allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        Logger().log(e, level='CRITICAL')


if __name__ == '__main__':
    main()
