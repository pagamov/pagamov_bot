from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from telegram.ext import CommandHandler, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler
from telegram.ext import filters, ApplicationBuilder
from telegram.ext import CallbackQueryHandler

import json
import html
import traceback

from habit_handler import HabitHandler
from utils import get_user_info
from habbit import *
from const import *
from database import *
from notify import *
from admin import *
from about_me import *

# TODO сделать изменение внутреннего аноним ника
# TODO после смены ника, нужно в базе поменять ВСЕ логи где он участвует на него
# TODO удалять через админскую консоль пользователей
# TODO создавать через консоль юзеров

async def check_habit_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Проверка и отправка уведомлений о привычках"""
    from database import HabitService
    from database import Database
    import json
    
    habit_service = HabitService()
    database = Database()
    
    # Получаем все активные привычки
    habits = database.get_from_query("""
        SELECT h.id_habit, h.description, h.time_of_day, h.user_id, u.tg_username
        FROM habit h
        JOIN user u ON h.user_id = u.id_user
        WHERE h.is_active = 1
    """)
    
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M')
    
    for habit in habits:
        habit_id, description, time_of_day, user_id, tg_username = habit
        
        # Проверяем, нужно ли отправлять уведомление сегодня
        schedule = habit_service.get_habit_schedule_for_period(
            habit_id, today, today
        )
        
        if schedule and time_of_day <= current_time:
            # Проверяем, не отправляли ли уже сегодня
            already_sent = database.get_from_query("""
                SELECT id_progress FROM habit_progress 
                WHERE habit_id = ? AND date = ? AND status = 'notified'
            """, (habit_id, today))
            
            if not already_sent:
                # Отправляем уведомление
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                chat_id = database.get_from_query(
                    "SELECT chat_id FROM notify WHERE user_id = ? LIMIT 1", 
                    (user_id,)
                )
                
                if chat_id:
                    chat_id = chat_id[0][0]
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🎯 Напоминание о привычке:\n{description}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Выполнено", 
                                callback_data=json.dumps({
                                    "type": "habit_completed", 
                                    "habit_id": habit_id
                                })),
                             InlineKeyboardButton("Пропустить", 
                                callback_data=json.dumps({
                                    "type": "habit_skipped", 
                                    "habit_id": habit_id
                                }))]
                        ])
                    )
                    
                    # Отмечаем, что уведомление отправлено
                    database.run_query_with_params("""
                        INSERT INTO habit_progress (habit_id, date, status)
                        VALUES (?, ?, 'notified')
                    """, (habit_id, today))

async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """Тут мы начинаем работу в режиме диалога. Возвращаем меню.
    """

    text, tg_username = get_user_info(update)

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

    _, tg_username = get_user_info(update)

    FROM_IDLE_MENU_t0 : str = \
        "Вернулись после падения сервера (не ваш косяк), о великий равный небу."

    if User().is_admin(tg_username):
        await update.message.reply_text(
            text=FROM_IDLE_MENU_t0,
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
        chat_id=update.effective_chat.id, text="Работа бота завершена")

async def MAIN_MENU(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    text, tg_username = get_user_info(update)

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

async def PROGRAMM_MENU(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    text, tg_username = get_user_info(update)

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

async def handle_final(update: Update, _: ContextTypes.DEFAULT_TYPE):
    pass

async def check_notify_queue(context: ContextTypes.DEFAULT_TYPE):
    notify_to_send = Database().get_from_query(f"""
        SELECT id_notify, chat_id, description
            FROM notify
            WHERE sent = 0 and time_notify <= DATETIME('now', '+3 hours')
    """)

    if len(notify_to_send) == 0:
        return

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
        [MessageHandler(basic_filters, 
                        lambda u, c: HabitHandler().menu(u, c))]

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
    
    states[State.HABBIT_MENU_ADD_DESCRIPTION] = \
        [MessageHandler(filters.TEXT & (~filters.COMMAND), 
                   lambda u, c: HabitHandler().add_description(u, c))]

    states[State.HABBIT_MENU_ADD_FREQUENCY] = \
        [MessageHandler(filters.TEXT & (~filters.COMMAND), 
                   lambda u, c: HabitHandler().add_frequency(u, c))]

    states[State.HABBIT_MENU_ADD_WEEKDAYS] = \
        [MessageHandler(filters.TEXT & (~filters.COMMAND), 
                   lambda u, c: HabitHandler().add_weekdays(u, c))]

    states[State.HABBIT_MENU_ADD_TIME] = \
        [MessageHandler(filters.TEXT & (~filters.COMMAND), 
                   lambda u, c: HabitHandler().add_time(u, c))]

    states[State.HABBIT_MENU_DELETE] = \
        [MessageHandler(filters.TEXT & (~filters.COMMAND), 
                   lambda u, c: HabitHandler().delete_habit(u, c))]

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
    check_notify_queue_job = app.job_queue.run_repeating(
        check_notify_queue,
        interval=30, 
        first=1)
    
    check_habit_job = app.job_queue.run_repeating(
        check_habit_notifications, 
        interval=60,  # Проверяем каждую минуту
        first=1
    )

    app.add_error_handler(error)

    try:
        Logger().log("Polling bot...")
        app.run_polling(poll_interval=0.8, allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        Logger().log(e, level='CRITICAL')

if __name__ == '__main__':
    main()
