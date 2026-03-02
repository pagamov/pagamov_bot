
from telegram import Update
from telegram.ext import ContextTypes
import re
from datetime import datetime, time, timedelta

from database import Database, User
from const import *


async def NOTIFY_MENU(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> int:

    text: str = update.message.text
    tg_username: str = update.effective_user.username

    if text == Text.NOTIFY_MENU_KEYBOARD[0]:
        """Получаем список моих напоминаний
        Если он пустой, то пишем что пусто
        """
        notify_list = Database().get_from_query(
            Text.NOTIFY_MENU_get_notify.format(tg_username))

        if len(notify_list) == 0:
            await update.message.reply_text(
                Text.NOTIFY_MENU_empty_list,
                reply_markup=Keyboard.NOTIFY_MENU)
        else:
            reply: str = ''
            for i, item in enumerate(notify_list):
                reply += Text.NOTIFY_MENU_item_in_list.format(
                    i, item[0], item[1], item[2])
            await update.message.reply_text(
                text=reply,
                reply_markup=Keyboard.NOTIFY_MENU)

        return State.NOTIFY_MENU

    elif text == Text.NOTIFY_MENU_KEYBOARD[1]:
        """Начинаем процедуру добавления напоминания - описание
        потом дата потом время
        """
        await update.message.reply_text(
            Text.NOTIFY_MENU_about_question,
            reply_markup=Keyboard.NOTIFY_MENU_ADD_CANCEL_KEYBOARD)

        return State.NOTIFY_MENU_ADD_DESCRIPTION

    elif text == Text.NOTIFY_MENU_KEYBOARD[2]:
        """Удаляем напоминание
        """

        notify_list = Database().get_from_query(
            Text.NOTIFY_MENU_get_notify.format(tg_username))

        if len(notify_list) == 0:
            await update.message.reply_text(
                Text.NOTIFY_MENU_empty_list,
                reply_markup=Keyboard.NOTIFY_MENU)
        else:
            """TODO вывести список всех напоминаний и пользоватеть вводит номер напоминания в списке.
            мы удаяем его из базы"""

            reply: str = ''
            for i, item in enumerate(notify_list):
                reply += Text.NOTIFY_MENU_item_in_list.format(
                    i, item[0], item[1], item[2])
            await update.message.reply_text(
                text=reply,
                reply_markup=Keyboard.NOTIFY_MENU_ADD_CANCEL_KEYBOARD)

            await update.message.reply_text(
                text="Введите номер напоминания который надо удалить. Как только больше ничего удалять не нужно, нажмите кнопку отмены",
                reply_markup=Keyboard.NOTIFY_MENU_ADD_CANCEL_KEYBOARD)
            return STATE.NOTIFY_MENU_DELETE


        # await update.message.reply_text(
        #     '_Сейчас удалим напоминания', )
        # return State.NOTIFY_MENU

    elif text == Text.NOTIFY_MENU_KEYBOARD[3]:
        # TODO зачем изменять напоминанеи если можно удалить и сделать новое
        await update.message.reply_text(
                text="Модуль изменения напоминаний пока что не работает",
                reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU

    elif text == Text.NOTIFY_MENU_KEYBOARD[4]:
        # TODO рассмотреть какие настройки можно добавить в модуль
        await update.message.reply_text(
                text="Модуль настроек пока что не работает",
                reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU
    

    elif text == Text.NOTIFY_MENU_KEYBOARD[5]:
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
        return State.NOTIFY_MENU


async def NOTIFY_MENU_ADD_DESCRIPTION(update: Update,
                                      context: ContextTypes.DEFAULT_TYPE):

    text: str = update.message.text

    if text == "Отменить":
        await update.message.reply_text(
            "Возвращаемся в напоминаниям",
            reply_markup=Keyboard.NOTIFY_MENU)

        return State.NOTIFY_MENU

    else:
        context.user_data['NOTIFY_MENU_ADD_DESCRIPTION'] = text
        await update.message.reply_text(
            "Какого числа? (dd.mm.yy)",
            reply_markup=Keyboard.get_NOTIFY_MENU_ADD_Date_pick_keyboard())

        return State.NOTIFY_MENU_ADD_DATEPICK


async def NOTIFY_MENU_ADD_DATEPICK(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE) -> int:
    text: str = update.message.text

    if text == "Отменить":
        await update.message.reply_text(
            "Возвращаемся в напоминаниям",
            reply_markup=Keyboard.NOTIFY_MENU)

        return State.NOTIFY_MENU

    if len(re.findall(r'[0-9]{1,2}[.:, ][0-9]{1,2}[.:, ][0-9]{2}', text)) == 0:
        await update.message.reply_text(
            Text.NOTIFY_MENU_ADD_DATEPICK_t0,
            reply_markup=Keyboard.get_NOTIFY_MENU_ADD_Date_pick_keyboard())

        return State.NOTIFY_MENU_ADD_DATEPICK

    dig: list[int] = list(map(int, re.findall(r'\d+', text)))
    try:
        date = datetime(year=2000 + dig[2], month=dig[1], day=dig[0])

        if date.date() < datetime.now().date():
            await update.message.reply_text(
                "Что то не так с вашими данными, \
                    вы ввели дату раньше сегодня, еще раз",
                reply_markup=Keyboard.get_NOTIFY_MENU_ADD_Date_pick_keyboard())

            return State.NOTIFY_MENU_ADD_DATEPICK

    except ValueError:
        await update.message.reply_text(
            Text.NOTIFY_MENU_ADD_DATEPICK_t0,
            reply_markup=Keyboard.get_NOTIFY_MENU_ADD_Date_pick_keyboard())
        return State.NOTIFY_MENU_ADD_DATEPICK

    context.user_data['NOTIFY_MENU_ADD_DATEPICK'] = date

    await update.message.reply_text(
        "Введите время (hh.mm)",
        reply_markup=Keyboard.get_NOTIFY_MENU_ADD_Time_pick_keyboard())

    return State.NOTIFY_MENU_ADD_TIMEPICK


async def NOTIFY_MENU_ADD_TIMEPICK(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):

    text: str = update.message.text
    tg_username: str = update.effective_user.username

    if text == "Отменить":
        await update.message.reply_text(
            "Возвращаемся в напоминаниям", reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU

    if len(re.findall(r'[0-9]{1,2}[.:, ][0-9]{1,2}', text)) == 0:
        await update.message.reply_text(
            Text.NOTIFY_MENU_ADD_TIMEPICK_t0,
            reply_markup=Keyboard.get_NOTIFY_MENU_ADD_Time_pick_keyboard())

        return State.NOTIFY_MENU_ADD_TIMEPICK

    dig: list[int] = list(map(int, re.findall(r'\d+', text)))

    if not (0 <= dig[0] < 24 and 0 <= dig[1] < 60):
        await update.message.reply_text(
            Text.NOTIFY_MENU_ADD_TIMEPICK_t0,
            reply_markup=Keyboard.get_NOTIFY_MENU_ADD_Time_pick_keyboard())

        return State.NOTIFY_MENU_ADD_TIMEPICK

    description: str = context.user_data['NOTIFY_MENU_ADD_DESCRIPTION']
    d: datetime = context.user_data['NOTIFY_MENU_ADD_DATEPICK']
    t: time = time(hour=dig[0], minute=dig[1])

    # TODO пока что мы работаем только в UTC+3, как же это решить то...?
    if d.date() == datetime.now().date() \
            and t < (datetime.now() + timedelta(hours=3)).time():

        await update.message.reply_text(
            Text.NOTIFY_MENU_time_err,
            reply_markup=Keyboard.get_NOTIFY_MENU_ADD_Time_pick_keyboard())

        return State.NOTIFY_MENU_ADD_TIMEPICK

    date_str = f"{d.year}" + \
        f"-{d.month if len(str(d.month)) == 2 else '0' + str(d.month)}" +\
        f"-{d.day if len(str(d.day)) == 2 else '0' + str(d.day)}"

    time_str = f"{t.hour if len(str(t.hour)) == 2 else '0' + str(t.hour)}:" + \
        f"{t.minute if len(str(t.minute)) == 2 else '0' + str(t.minute)}"

    Database().run_query(
        Text.NOTIFY_MENU_insert_notify.format(
            context._chat_id, tg_username, description, date_str, time_str
        ))

    await update.message.reply_text(
        Text.NOTIFY_MENU_exit_add_succ,
        reply_markup=Keyboard.NOTIFY_MENU)

    return State.NOTIFY_MENU


# async def NOTIFY_LIST():
#     pass

# async def NOTIFY_ADD():
#     pass

async def NOTIFY_DELETE():
    pass


async def NOTIFY_CHANGE():
    pass


async def NOTIFY_SETTINGS():
    pass
