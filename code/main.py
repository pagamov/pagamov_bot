from telegram import Update, ReplyKeyboardRemove
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler
from telegram.ext import filters, CallbackContext, ApplicationBuilder, CallbackQueryHandler, ChosenInlineResultHandler

import json

import functools
from typing import Callable

from const import *
from database import *
from notify import *

# TODO сделать изменение внутреннего аноним ника
# TODO после смены ника, нужно в базе поменять ВСЕ логи где он участвует на этот ник
# TODO удалять через админскую консоль пользователей
# TODO создавать через консоль юзеров




# Wrapper section

def log_chat_message(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> int:
        chat_id = update.effective_chat.id if update.effective_chat else 'N/A'
        message_id = update.message.message_id if update.message else 'N/A'
        print(f"Chat ID: {chat_id}, Message ID: {message_id}")
        return await func(update, context, *args, **kwargs)
    return wrapper

# Handler section

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Тут мы начинаем работу в режиме диалога.
    Возвращаем меню
    """

    text : str = update.message.text
    tg_username : str = update.effective_user.username

    Logger().log(Text.start_command_t0.format(update.message.chat.id, tg_username, update.message.chat.type, text))
    if User().get_id_user(tg_username) > 0:
        if User().is_admin(tg_username):
            await update.message.reply_text(Text.start_command_t3.format(User().get_bot_username(tg_username)), reply_markup=Keyboard.MAIN_MENU_ADMIN)
            return State.MAIN_MENU_ADMIN
        else:
            await update.message.reply_text(Text.start_command_t1.format(User().get_bot_username(tg_username)), reply_markup=Keyboard.MAIN_MENU)
            return State.MAIN_MENU
    else:
        User().createUser(tg_username)

        if User().is_admin(tg_username):
            await update.message.reply_text(Text.start_command_t2.format(User().get_bot_username(tg_username)), reply_markup=Keyboard.MAIN_MENU_ADMIN)
            return State.MAIN_MENU_ADMIN
        else:
            await update.message.reply_text(Text.start_command_t2.format(User().get_bot_username(tg_username)), reply_markup=Keyboard.MAIN_MENU)
            return State.MAIN_MENU

async def FROM_IDLE_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Когда бот не работает и потом запускается, 
    пользователь может быть на другой клавиатуре посреди другого этапа.
    Чтобы вернуться к основному меню нажатием на клавишу, добавлен такой entry_points
    """
    tg_username : str = update.effective_user.username
    
    if User().is_admin(tg_username):
        await update.message.reply_text(Text.FROM_IDLE_MENU_t0, reply_markup=Keyboard.MAIN_MENU_ADMIN)
        return State.MAIN_MENU_ADMIN
    else:
        await update.message.reply_text(Text.FROM_IDLE_MENU_t1, reply_markup=Keyboard.MAIN_MENU)
        return State.MAIN_MENU

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=Text.cancel_command_t0)
    
async def MAIN_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username

    if text == Text.MAIN_MENU_KEYBOARD[0]:
        await update.message.reply_text(Text.MAIN_MENU_t0, reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU

    # elif text == Text.MAIN_MENU_KEYBOARD[1]:
    #     await update.message.reply_text(Text.MAIN_MENU_t1, reply_markup=Keyboard.JOB_MENU)
    #     return State.JOB_MENU
    
    elif text == Text.MAIN_MENU_KEYBOARD[2]:
        await update.message.reply_text(Text.MAIN_MENU_t2, reply_markup=Keyboard.HABBIT_MENU)
        return State.HABBIT_MENU
    
    elif text == Text.MAIN_MENU_KEYBOARD[3]:
        await update.message.reply_text(Text.MAIN_MENU_t3, reply_markup=Keyboard.PROGRAMM_MENU)
        return State.PROGRAMM_MENU
    
    elif text == Text.MAIN_MENU_KEYBOARD[4]:
        await update.message.reply_text(Text.MAIN_MENU_t4, reply_markup=Keyboard.ABOUT_ME_MENU)
        return State.ABOUT_ME_MENU
    
    else:
        return State.MAIN_MENU_ADMIN if User().is_admin(tg_username) else State.MAIN_MENU
    
async def MAIN_MENU_ADMIN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username

    if text == Text.MAIN_MENU_ADMIN_KEYBOARD[0]:
        await update.message.reply_text(Text.MAIN_MENU_ADMIN_t0, reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU
    # elif text == Text.MAIN_MENU_ADMIN_KEYBOARD[1]:
    #     await update.message.reply_text(Text.MAIN_MENU_ADMIN_t1, reply_markup=Keyboard.JOB_MENU)
    #     return State.JOB_MENU
    elif text ==  Text.MAIN_MENU_ADMIN_KEYBOARD[2]:
        await update.message.reply_text(Text.MAIN_MENU_ADMIN_t2, reply_markup=Keyboard.HABBIT_MENU)
        return State.HABBIT_MENU
    elif text ==  Text.MAIN_MENU_ADMIN_KEYBOARD[3]:
        await update.message.reply_text(Text.MAIN_MENU_ADMIN_t3, reply_markup=Keyboard.PROGRAMM_MENU)
        return State.PROGRAMM_MENU
    elif text ==  Text.MAIN_MENU_ADMIN_KEYBOARD[4]:
        await update.message.reply_text(Text.MAIN_MENU_ADMIN_t4, reply_markup=Keyboard.ABOUT_ME_MENU)
        return State.ABOUT_ME_MENU
    elif text ==  Text.MAIN_MENU_ADMIN_KEYBOARD[5]:
        await update.message.reply_text(Text.MAIN_MENU_ADMIN_t5, reply_markup=Keyboard.ADMIN_PANEL_1)
        return State.ADMIN_PANEL_1

    else:
        return State.MAIN_MENU_ADMIN if User().is_admin(tg_username) else State.MAIN_MENU







# async def JOB_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     text : str = update.message.text
#     tg_username : str = update.effective_user.username
    
#     if text == Text.JOB_MENU_KEYBOARD[0]:
#         await update.message.reply_text('_Твои дела', )
#         return State.JOB_MENU
    
#     elif text == Text.JOB_MENU_KEYBOARD[1]:
#         await update.message.reply_text('_Давай добавим тебе дело', )
#         return State.JOB_MENU
    
#     elif text == Text.JOB_MENU_KEYBOARD[2]:
#         await update.message.reply_text('_Сейчас удалим дела', )
#         return State.JOB_MENU
    
#     elif text == Text.JOB_MENU_KEYBOARD[3]:
#         await update.message.reply_text('_Давай изменим дела', )
#         return State.JOB_MENU
    
#     elif text == Text.JOB_MENU_KEYBOARD[4]:
#         await update.message.reply_text('_Что там по настройкам?', )
#         return State.JOB_MENU
    
#     elif text == Text.JOB_MENU_KEYBOARD[5]:
#         match User().is_admin(tg_username):
#             case True:
#                 await update.message.reply_text('Давай в основное меню, великий господин равный небу', reply_markup=Keyboard.MAIN_MENU_ADMIN)
#                 return State.MAIN_MENU_ADMIN
#             case _:
#                 await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
#                 return State.MAIN_MENU
    
#     else:
#         return State.JOB_MENU

async def HABBIT_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    match text:
        # case "Мои дела":
        #     await update.message.reply_text('_Твои привычки', )
        #     return State.HABBIT_MENU
        # case "Добавить":
        #     await update.message.reply_text('_Давай добавим тебе привычки', )
        #     return State.HABBIT_MENU
        # case "Удалить":
        #     await update.message.reply_text('_Сейчас удалим привычки', )
        #     return State.HABBIT_MENU
        # case "Изменить":
        #     await update.message.reply_text('_Давай изменим привычки', )
        #     return State.HABBIT_MENU
        # case "Настройки":
        #     await update.message.reply_text('_Что там по настройкам?', )
        #     return State.HABBIT_MENU
        
        case "Назад":
            match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text('Давай в основное меню, великий господин равный небу', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _:
            return State.HABBIT_MENU

async def PROGRAMM_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    match text:
        # case "Мои дела":
        #     await update.message.reply_text('_Твои программы', )
        #     return State.PROGRAMM_MENU
        # case "Добавить":
        #     await update.message.reply_text('_Давай добавим тебе программы', )
        #     return State.PROGRAMM_MENU
        # case "Удалить":
        #     await update.message.reply_text('_Сейчас удалим программы', )
        #     return State.PROGRAMM_MENU
        # case "Изменить":
        #     await update.message.reply_text('_Давай изменим программы', )
        #     return State.PROGRAMM_MENU
        # case "Настройки":
        #     await update.message.reply_text('_Что там по программам?', )
        #     return State.PROGRAMM_MENU
        
        case "Назад":
            match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text('Давай в основное меню, великий господин равный небу', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _:
            return State.PROGRAMM_MENU


async def ABOUT_ME_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username

    user = User()

    if text == Text.ABOUT_ME_MENU_KEYBOARD[0]:
        context.user_data['new_bot_username'] = user.createBot_username()
        cur_username : str = user.get_bot_username(tg_username)
        await update.message.reply_text(f'А что вам не нравится в {cur_username}?\nСгенерируем вам новый ник...\nКак вам {context.user_data["new_bot_username"]}?', reply_markup=Keyboard.ABOUT_ME_CHANGE_NICK)
        return State.ABOUT_ME_MENU_CHANGE_NICK

    elif text == Text.ABOUT_ME_MENU_KEYBOARD[-1]:
        match User().is_admin(tg_username):
            case True:
                await update.message.reply_text('Давай в основное меню, великий господин равный небу', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                return State.MAIN_MENU_ADMIN
            case _:
                await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                return State.MAIN_MENU
    else:
        return State.ABOUT_ME_MENU

async def ABOUT_ME_MENU_CHANGE_NICK(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    user = User()
    db = Database()

    if text == "Попробуем еще раз":
        context.user_data['new_bot_username'] = user.createBot_username()
        await update.message.reply_text(f'А как вам {context.user_data["new_bot_username"]}?', reply_markup=Keyboard.ABOUT_ME_CHANGE_NICK)
        return State.ABOUT_ME_MENU_CHANGE_NICK
    
    elif text == "Мне нравится":
        # Применить текущий ник к пользователю
        db.run_query('''
            update user
            set bot_username="{}"
            where tg_username="{}";
            '''.format(context.user_data['new_bot_username'], tg_username))

        await update.message.reply_text('Изменения сохранены', reply_markup=Keyboard.ABOUT_ME_MENU)
        return State.ABOUT_ME_MENU
    
    elif text == "Оставить все как было":
        await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.ABOUT_ME_MENU)
        return State.ABOUT_ME_MENU
    
    return State.ABOUT_ME_MENU_CHANGE_NICK


async def ADMIN_PANEL_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    
    if text == Text.ADMIN_PANEL_1_KEYBOARD[0]:
        await update.message.reply_text('Сколько последних записей выдать?', reply_markup=ReplyKeyboardRemove())
        return State.ADMIN_PANEL_TAIL_LOG_BOT
    
    elif text == Text.ADMIN_PANEL_1_KEYBOARD[1]:
        Database().run_query(f"""
            INSERT INTO notify
                (chat_id, user_id, description, time_create, time_notify)
            VALUES   
                ({context._chat_id},
                (SELECT id_user FROM user WHERE tg_username = "{tg_username}" limit 1),
			    "Test notify 1 min for {tg_username}", DATETIME('NOW'), DATETIME('now', '+1 minute'))""")
        
        await update.message.reply_text('Напоминание через 1 мин. добавлено', reply_markup=Keyboard.ADMIN_PANEL_1)

    elif text == Text.ADMIN_PANEL_1_KEYBOARD[-2]: # Назад
        match User().is_admin(tg_username):
            case True:
                await update.message.reply_text('Давай в основное меню, великий господин равный небу', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                return State.MAIN_MENU_ADMIN
            case _:
                await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                return State.MAIN_MENU

    elif text == Text.ADMIN_PANEL_1_KEYBOARD[-1]: # >
        await update.message.reply_text('Админка 2', reply_markup=Keyboard.ADMIN_PANEL_2)
        return State.ADMIN_PANEL_2

    else:
        return State.ADMIN_PANEL_1

async def ADMIN_PANEL_TAIL_LOG_BOT(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    """
    Получить последние строчки таблицы log_bot
    """
    
    logger = Logger()
    text : str = update.message.text

    try:
        int(text)
    except ValueError:
        await update.message.reply_text("Не похоже на число... Давай еще раз...")
        return State.ADMIN_PANEL_TAIL_LOG_BOT
 
    if int(text) <= 0:
        await update.message.reply_text("Мне бы число больше нуля...")
        return State.ADMIN_PANEL_TAIL_LOG_BOT
    else:
        res : list[str] | str = logger.tail_log_bot(int(text))

        if type(res) == str:
            await update.message.reply_text(res, reply_markup=Keyboard.ADMIN_PANEL_1)
            
        else:
            # Нам тут важно чтобы отчет не вылез за пределы размера сообщения.
            # Если оно больше TELEGRAM_MAX_MESSAGE_SIZE то начинаем заполнять следующую ячейку.
            # Потом пачкой все отправляем.

            message_storage : list[str] = []
            storage : str = ''
            for row in res:
                if len(storage) + len(row) > TELEGRAM_MAX_MESSAGE_SIZE:
                    message_storage.append(storage)
                    storage = ''
                else:
                    storage += row

            message_storage.append(storage)

            for message in message_storage:
                await update.message.reply_text(message, reply_markup=Keyboard.ADMIN_PANEL_1)

        return State.ADMIN_PANEL_1

async def ADMIN_PANEL_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    match text:
        case '<':
            await update.message.reply_text('Панелька страничка 1', reply_markup=Keyboard.ADMIN_PANEL_1)
            return State.ADMIN_PANEL_1
        case '>':
            await update.message.reply_text('Панелька страничка 3', reply_markup=Keyboard.ADMIN_PANEL_3)
            return State.ADMIN_PANEL_3
        case 'Назад':
            match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text('Давай в основное меню, великий господин равный небу', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _:
            return State.ADMIN_PANEL_2

async def ADMIN_PANEL_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    match text:
        case '<':
             await update.message.reply_text('Панелька страничка 2', reply_markup=Keyboard.ADMIN_PANEL_2)
             return State.ADMIN_PANEL_2
        case 'Назад':
            match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text('Давай в основное меню, великий господин равный небу', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _:
            return State.ADMIN_PANEL_3

async def handle_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def check_notify_queue(context: ContextTypes.DEFAULT_TYPE):
    db = Database()

    notify_to_send = db.get_from_query(f"""
        SELECT id_notify, chat_id, description
                                FROM notify
                                WHERE sent = 0 and DATETIME('now') >= time_notify
    """)

    if len(notify_to_send) != 0:
        for notify in notify_to_send:
            id = notify[0]
            chat_id = notify[1]
            text = notify[2]
            await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("Выполнил", callback_data=json.dumps({"text":f"notify_set_done", "id":id})), 
                                 InlineKeyboardButton("Отложить", callback_data=json.dumps({"text":f"notify_delay", "id":id}))]]))
            db.run_query(f"""
                UPDATE notify
                SET sent=1
                WHERE id_notify = {id}
            """)

async def notify_queue_handler(update : Update, _):
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
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("1 min", callback_data=json.dumps({"text":"notify_delay_1min", "id":id}))
        ]]))
    
    elif callback_data['text'] == "notify_delay_1min":
        id = callback_data['id']
        Database().run_query(f"""
            UPDATE notify
            SET sent = 0, time_notify=DATETIME('now', '+1 minute')
            WHERE id_notify = {int(id)}
        """)
        await query.edit_message_text(text="Отложил на 1 мин.")

# Main section


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import html
    import traceback
    # print(Text.error_t0.format(update, context.error))
    # await context.bot.send_message(chat_id=321911494,
    #                                text=f"Bot Error:\n<code>{html.escape(str(context.error))}</code>",
    #                                parse_mode='HTML')
    
    # print("Exception while handling an update: ", exc_info=context.error)

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=321911494, text=message, parse_mode=ParseMode.HTML
    )

def main():
    # print('os.path.abspath(__file__)', os.path.abspath(__file__))
    # print('os.path.dirname(os.path.abspath(__file__))', os.path.dirname(os.path.abspath(__file__)))
    
    db = Database()
    db.firstInitDatabase()
 
    try:
        Logger().log("Starting bot...")
        app = (ApplicationBuilder()
               .token(TOKEN)
               .build())
    except Exception as e:
        Logger().log(e, level='CRITICAL') 
        
    entry_points : list = [ CommandHandler('start', start_command), 
                            MessageHandler(filters.TEXT & (~filters.COMMAND), FROM_IDLE_MENU)]
    
    states = {}
    states[State.MAIN_MENU] = [MessageHandler(filters.TEXT & (~filters.COMMAND), MAIN_MENU)]
    
    states[State.MAIN_MENU_ADMIN] =             [MessageHandler(filters.TEXT & (~filters.COMMAND), MAIN_MENU_ADMIN)]
    
    states[State.NOTIFY_MENU] =                 [MessageHandler(filters.TEXT & (~filters.COMMAND), NOTIFY_MENU)]
    states[State.NOTIFY_MENU_ADD_DESCRIPTION] = [MessageHandler(filters.TEXT & (~filters.COMMAND), NOTIFY_MENU_ADD_DESCRIPTION)]
    states[State.NOTIFY_MENU_ADD_DATEPICK] =    [MessageHandler(filters.TEXT & (~filters.COMMAND), NOTIFY_MENU_ADD_DATEPICK)]
    states[State.NOTIFY_MENU_ADD_TIMEPICK] =    [MessageHandler(filters.TEXT & (~filters.COMMAND), NOTIFY_MENU_ADD_TIMEPICK)]

    # states[State.JOB_MENU] =                    [MessageHandler(filters.TEXT & (~filters.COMMAND), JOB_MENU)]
    states[State.HABBIT_MENU] =                 [MessageHandler(filters.TEXT & (~filters.COMMAND), HABBIT_MENU)]
    states[State.PROGRAMM_MENU] =               [MessageHandler(filters.TEXT & (~filters.COMMAND), PROGRAMM_MENU)]
    
    states[State.ABOUT_ME_MENU] =               [MessageHandler(filters.TEXT & (~filters.COMMAND), ABOUT_ME_MENU)]
    states[State.ABOUT_ME_MENU_CHANGE_NICK] =   [MessageHandler(filters.TEXT & (~filters.COMMAND), ABOUT_ME_MENU_CHANGE_NICK)]
    
    states[State.ADMIN_PANEL_1] =               [MessageHandler(filters.TEXT & (~filters.COMMAND), ADMIN_PANEL_1)]

    states[State.ADMIN_PANEL_TAIL_LOG_BOT] =    [MessageHandler(filters.TEXT & (~filters.COMMAND), ADMIN_PANEL_TAIL_LOG_BOT)]

    states[State.ADMIN_PANEL_2] =               [MessageHandler(filters.TEXT & (~filters.COMMAND), ADMIN_PANEL_2)]
    states[State.ADMIN_PANEL_3] =               [MessageHandler(filters.TEXT & (~filters.COMMAND), ADMIN_PANEL_3)]
    states[ConversationHandler.END] =           [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_final)]

    for key, _ in states.items():
        states[key].append(CallbackQueryHandler(notify_queue_handler))


    app.add_handler(ConversationHandler(
        entry_points=entry_points,
        states=states,
        fallbacks=[CommandHandler('cancel', cancel_command)]
    ))

    # Обработчик для callback_data
    app.add_handler(CallbackQueryHandler(notify_queue_handler))

    # Добавление ассинхронного job который будет отправлять напоминания и сообщения из очереди
    check_notify_queue_job = app.job_queue.run_repeating(check_notify_queue, interval=5, first=1)

    app.add_error_handler(error)
    try:
        Logger().log("Polling bot...")
        app.run_polling(poll_interval=0.8, allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        Logger().log(e, level='CRITICAL')

if __name__ == '__main__':
    main()