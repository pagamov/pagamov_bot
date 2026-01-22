
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes
import re
from datetime import datetime, date, time

from database import Database, User
from const import *





async def NOTIFY_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    
    if text == Text.NOTIFY_MENU_KEYBOARD[0]:
        res = Database().get_from_query(f"""
            SELECT
                id_notify, description, time_notify 
            FROM
                notify
            WHERE
                user_id = (SELECT id_user FROM user WHERE tg_username = "{tg_username}" limit 1)
                AND done = 0
        """)

        if len(res) == 0:
            await update.message.reply_text('Список твоих напоминаний пуст', reply_markup=Keyboard.NOTIFY_MENU)
        else:
            reply = ''
            for i, item in enumerate(res):
                reply += "№{}. id:{} - {} (уведомить в {})\n\n".format(i, item[0], item[1], item[2])
            await update.message.reply_text(reply, reply_markup=Keyboard.NOTIFY_MENU)
        
        return State.NOTIFY_MENU
    
    elif text == Text.NOTIFY_MENU_KEYBOARD[1]:
        await update.message.reply_text('О чем тебе нужно напомнить?', reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]]))
        return State.NOTIFY_MENU_ADD_DESCRIPTION
    
    elif text == Text.NOTIFY_MENU_KEYBOARD[2]:
        await update.message.reply_text('_Сейчас удалим напоминания', )
        return State.NOTIFY_MENU
    
    elif text == Text.NOTIFY_MENU_KEYBOARD[3]:
        await update.message.reply_text('_Давай изменим напоминание', )
        return State.NOTIFY_MENU_CHANGE
    
    elif text == Text.NOTIFY_MENU_KEYBOARD[4]:
        await update.message.reply_text('_Что там по настройкам?', )
        return State.NOTIFY_MENU
    
    elif text == Text.NOTIFY_MENU_KEYBOARD[5]:
        match User().is_admin(tg_username):
            case True:
                await update.message.reply_text('Давай в основное меню, великий господин равный небу', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                return State.MAIN_MENU_ADMIN
            case _:
                await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                return State.MAIN_MENU
            
    else:
        return State.NOTIFY_MENU


async def NOTIFY_MENU_ADD_DESCRIPTION(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text : str = update.message.text
    tg_username : str = update.effective_user.username

    if text == "Отменить":
        await update.message.reply_text("Возвращаемся в напоминаниям", reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU
    else:
        context.user_data['NOTIFY_MENU_ADD_DESCRIPTION'] = text
        await update.message.reply_text("Какого числа? (dd.mm.yy)", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]]))
        return State.NOTIFY_MENU_ADD_DATEPICK

async def NOTIFY_MENU_ADD_DATEPICK(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text : str = update.message.text
    tg_username : str = update.effective_user.username

    if text == "Отменить":
        await update.message.reply_text("Возвращаемся в напоминаниям", reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU

    if re.match(r'[0-9]{1,2}[.:, ][0-9]{1,2}[.:, ][0-9]{2}', text) == None:
        await update.message.reply_text("Что то не так с вашими данными, попробуйте ввести в виде dd.mm.yy", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]]))
        return State.NOTIFY_MENU_ADD_DATEPICK

    dig : list[int] = list(map(int, re.findall(r'\d', text)))
    try:
        date = datetime.datetime(year=2000 + dig[2], month=dig[1], day=dig[0])

        if date.date() < datetime.now().date():
            await update.message.reply_text("Что то не так с вашими данными, вы ввели дату раньше сегодня, еще раз", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]]))
            return State.NOTIFY_MENU_ADD_DATEPICK

    except ValueError:
        await update.message.reply_text("Что то не так с вашими данными, попробуйте ввести в виде dd.mm.yy", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]]))
        return State.NOTIFY_MENU_ADD_DATEPICK
    
    context.user_data['NOTIFY_MENU_ADD_DATEPICK'] = date

    await update.message.reply_text("Введите время (hh.mm)", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]]))
    return State.NOTIFY_MENU_ADD_TIMEPICK

async def NOTIFY_MENU_ADD_TIMEPICK(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    text : str = update.message.text
    tg_username : str = update.effective_user.username

    if text == "Отменить":
        await update.message.reply_text("Возвращаемся в напоминаниям", reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU

    if re.match(r'[0-9]{1,2}[.:, ][0-9]{1,2}', text) == None:
        await update.message.reply_text("Что то не так с вашими данными, попробуйте ввести в виде hh.mm", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]]))
        return State.NOTIFY_MENU_ADD_TIMEPICK
    
    dig : list[int] = list(map(int, re.findall(r'\d', text)))

    if 0 <= dig[0] < 24 and 0 <= dig[1] < 60:
        pass
    else:
        await update.message.reply_text("Что то не так с вашими данными, попробуйте ввести в виде hh.mm", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]]))
        return State.NOTIFY_MENU_ADD_TIMEPICK

    description = context.user_data['NOTIFY_MENU_ADD_DESCRIPTION']
    time = datetime.time(hour=dig[0], minute=dig[1])
    date = context.user_data['NOTIFY_MENU_ADD_DATEPICK']

    if date.date() == datetime.now().date():
        if time < datetime.now().time():
            await update.message.reply_text("Что то не так с вашими данными, вы ввели время раньше чем времени сейчас, еще раз", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]]))
            return State.NOTIFY_MENU_ADD_TIMEPICK
    
    Database().run_query(f"""
        INSERT INTO notify
            (chat_id, user_id, description, time_create, time_notify)
        VALUES   
            ({context._chat_id},
            (SELECT id_user FROM user WHERE tg_username = "{tg_username}" limit 1),
            "{description}", DATETIME('NOW'), DATETIME('{date.year}-{date.month}-{date.day} {time.hour}:{time.minutes}:00'))""")

    await update.message.reply_text("Напоминание добавлено", reply_markup=Keyboard.NOTIFY_MENU)
    return State.NOTIFY_MENU

async def NOTIFY_LIST():
    pass

async def NOTIFY_ADD():
    pass

async def NOTIFY_DELETE():
    pass

async def NOTIFY_CHANGE():
    pass

async def NOTIFY_SETTINGS():
    pass

