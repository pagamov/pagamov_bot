
import html
import traceback
from telegram import Update, ReplyKeyboardRemove
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler
from telegram.ext import filters, CallbackContext, ApplicationBuilder, CallbackQueryHandler, ChosenInlineResultHandler

import sqlite3
import re
import random
import logging
from typing import Final, Sequence
import os
from dotenv import load_dotenv
import time
import json

import functools
from typing import Callable

# TODO сделать изменение внутреннего аноним ника
# TODO после смены ника, нужно в базе поменять ВСЕ логи где он участвует на этот ник
# TODO удалять через админскую консоль пользователей
# TODO создавать через консоль юзеров
# TODO 
# TODO 
# TODO 
# TODO 
# TODO 
# TODO 
# TODO 

"""
Секция с константами
"""
load_dotenv() # Загрузка файла .env
TOKEN : Final = os.getenv("TOKEN") # Паша если сольешь токен опять - обещаю перестать писать ботов для ВКР
LOGGER_VERBOSE : Final = True # Означает, будет ли модуль Logger выводить данные не только в БД но еще и в консоль
TELEGRAM_MAX_MESSAGE_SIZE : Final = 4096 # Столько char может быть максимум в одном текстовом сообщении в телеграме

class Text:
    """
    Тут будут лежать все возможные текстовые константы
    """
    start_command_t0 = """chat_id ({}), tg_username ({}) in start_command {}: {}"""
    start_command_t1 = """Добро пожаловать, {}!"""
    start_command_t2 = """Добро пожаловать в мое приложение, {}!"""
    start_command_t2 += """\nВам доступны напоминания и трекер привычек."""
    start_command_t2 += """\nТакже вы можете воспользоваться готовыми программами приобретения привычек или отказа от плохих."""
    start_command_t2 += """\nЖелаю удачи!"""
    start_command_t3 = """Добро пожаловать, о великий равный небу {}. Ваши покои вас ждут."""
    
    FROM_IDLE_MENU_t0 = "Вернулись после падения сервера (не ваш косяк), о великий равный небу."
    FROM_IDLE_MENU_t1 = "Вернулись после падения сервера"
    
    cancel_command_t0 = "Работа бота завершена"
    
    MAIN_MENU_KEYBOARD : list[str] = ["Напоминания","_Дела","Привычки","Готовые программы","Обо мне"]
    
    MAIN_MENU_t0 = "Система напоминаний"
    MAIN_MENU_t1 = "Система твоих дел"
    MAIN_MENU_t2 = "Система привычек"
    MAIN_MENU_t3 = "Система готовых программ для тебя"
    MAIN_MENU_t4 = "Что то о тебе"
    

    MAIN_MENU_ADMIN_t0 = MAIN_MENU_t0
    MAIN_MENU_ADMIN_t1 = MAIN_MENU_t1
    MAIN_MENU_ADMIN_t2 = MAIN_MENU_t2
    MAIN_MENU_ADMIN_t3 = MAIN_MENU_t3
    MAIN_MENU_ADMIN_t4 = MAIN_MENU_t4
    MAIN_MENU_ADMIN_t5 = "Ну раз ты админ..."
    
    MAIN_MENU_ADMIN_KEYBOARD : list[str] = MAIN_MENU_KEYBOARD + ["Панель Админа"]
    
    NOTIFY_MENU_KEYBOARD : list[str] = ["Мои напоминания","Добавить","Удалить","Изменить","Настройки","Назад"]
    # JOB_MENU_KEYBOARD : list[str] = ["Мои дела","Добавить","Удалить","Изменить","Настройки","Назад"]
    HABBIT_MENU_KEYBOARD : list[str] = ["Мои привычки","Добавить","Удалить","Изменить","Настройки","Назад"]
    PROGRAMM_MENU_KEYBOARD : list[str] = ["Мои готовые программы","Добавить","Удалить","Изменить","Настройки","Назад"]
    ABOUT_ME_MENU_KEYBOARD : list[str] = ["Изменить мой ник", "Назад"]
    
    ADMIN_PANEL_1_KEYBOARD : list[str] = ["Получить логи бота", "Добавить напоминание через 1 минуту"] + ["Назад",">"]
    ADMIN_PANEL_2_KEYBOARD : list[str] = [] + ["<","Назад",">"]
    ADMIN_PANEL_3_KEYBOARD : list[str] = [] + ["<","Назад"]

    error_t0 : str = """Update:\n\n{}\n\nCaused error:\n\n{}"""


    createBot_username_t0 : list[str] = ["Удачливый","Смелый","Весёлый","Храбрый","Гениальный","Остроумный",
                                           "Талантливый","Умный","Забавный","Быстрый","Честный","Осторожный",
                                           "Решительный","Проницательный","Верный","Любимый","Дерзкий",
                                           "Очаровательный","Щедрый","Находчивый"]
    createBot_username_t1 : list[str] = ['слон','тигр','медведь','лев','крокодил','голубь','жираф',
                                           'верблюд','броненосец','кот']
    
    createBot_username_t2 : list[str] = ['0','1','2','3','4','5','6','7','8','9']

    createUser_t0 : str = """INSERT INTO user (tg_username, bot_username)
                                VALUES ("{}", "{}");"""
    

    createUser_t1 : str = """
                INSERT INTO user_role
                    (user, role)
                VALUES(
                    (SELECT user.id_user FROM user WHERE user.tg_username = '{}'), 
                    (SELECT role.id_role FROM role WHERE role.name_role = '{}'))"""
    
    createUser_t2 : str = """
                INSERT INTO user_role
                    (user, role)
                VALUES
                (
                    (SELECT user.id_user FROM user WHERE user.tg_username = '{}'), 
                    (SELECT role.id_role FROM role WHERE role.name_role = '{}'))"""

    get_id_user_t0 : str = '''SELECT id_user FROM user
            WHERE tg_username = "{}"'''
    

    is_admin_t0 : str = """
            SELECT 
                id_user_role 
            FROM
                user_role
            WHERE 
                user = (SELECT id_user FROM user WHERE tg_username = '{}') AND 
                role = (SELECT id_role FROM role WHERE name_role = '{}')"""
    
    get_bot_username_t0 : str = """
            SELECT bot_username FROM user
            WHERE tg_username = "{}"
        """
    get_bot_username_err : str = "tg_username is empty"

    tail_log_bot_t0 : str = """
        WITH tmp AS
            (SELECT * from bot_log
            ORDER BY bot_log_id DESC
            LIMIT {})
        SELECT 
            datetime, text 
        from tmp
        ORDER BY
            bot_log_id ASC
    """

class Keyboard:
    MAIN_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton(Text.MAIN_MENU_KEYBOARD[0]),KeyboardButton(Text.MAIN_MENU_KEYBOARD[1])],
                    [KeyboardButton(Text.MAIN_MENU_KEYBOARD[2]),KeyboardButton(Text.MAIN_MENU_KEYBOARD[3])],
                    [KeyboardButton(Text.MAIN_MENU_KEYBOARD[4])]
                ], resize_keyboard=True)
    
    MAIN_MENU_ADMIN = ReplyKeyboardMarkup([
                    [KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[0]),KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[1])],
                    [KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[2]),KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[3])],
                    [KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[4]),KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[5])]
                ], resize_keyboard=True)
    
    NOTIFY_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[0]),KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[1])],
                    [KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[2]),KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[3])],
                    [KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[4]),KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[5])]
                ], resize_keyboard=True)
    
    # JOB_MENU = ReplyKeyboardMarkup([
    #                 [KeyboardButton(Text.JOB_MENU_KEYBOARD[0]),KeyboardButton(Text.JOB_MENU_KEYBOARD[1])],
    #                 [KeyboardButton(Text.JOB_MENU_KEYBOARD[2]),KeyboardButton(Text.JOB_MENU_KEYBOARD[3])],
    #                 [KeyboardButton(Text.JOB_MENU_KEYBOARD[4]),KeyboardButton(Text.JOB_MENU_KEYBOARD[5])]
    #             ], resize_keyboard=True)
    
    HABBIT_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton(Text.HABBIT_MENU_KEYBOARD[0]),KeyboardButton(Text.HABBIT_MENU_KEYBOARD[1])],
                    [KeyboardButton(Text.HABBIT_MENU_KEYBOARD[2]),KeyboardButton(Text.HABBIT_MENU_KEYBOARD[3])],
                    [KeyboardButton(Text.HABBIT_MENU_KEYBOARD[4]),KeyboardButton(Text.HABBIT_MENU_KEYBOARD[5])]
                ], resize_keyboard=True)
    
    PROGRAMM_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[0]),KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[1])],
                    [KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[2]),KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[3])],
                    [KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[4]),KeyboardButton(Text.PROGRAMM_MENU_KEYBOARD[5])]
                ], resize_keyboard=True)
    
    ABOUT_ME_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton(Text.ABOUT_ME_MENU_KEYBOARD[0]),KeyboardButton(Text.ABOUT_ME_MENU_KEYBOARD[1])]
                ], resize_keyboard=True)
    
    ABOUT_ME_CHANGE_NICK = ReplyKeyboardMarkup([
                [KeyboardButton("Попробуем еще раз"), KeyboardButton("Мне нравится")],
                [KeyboardButton("Оставить все как было")]
            ], resize_keyboard=True)
    
    ADMIN_PANEL_1 = ReplyKeyboardMarkup([
                    [KeyboardButton(Text.ADMIN_PANEL_1_KEYBOARD[0]), KeyboardButton(Text.ADMIN_PANEL_1_KEYBOARD[1])],
                    
                    [KeyboardButton(Text.ADMIN_PANEL_1_KEYBOARD[-2]),  # Назад
                     KeyboardButton(Text.ADMIN_PANEL_1_KEYBOARD[-1])], # >
                ], resize_keyboard=True)
    
    ADMIN_PANEL_2 = ReplyKeyboardMarkup([
        
                    [KeyboardButton(Text.ADMIN_PANEL_2_KEYBOARD[-3]),   # <
                     KeyboardButton(Text.ADMIN_PANEL_2_KEYBOARD[-2]),   # Назад 
                     KeyboardButton(Text.ADMIN_PANEL_2_KEYBOARD[-1])],  # >
                ], resize_keyboard=True)
    
    ADMIN_PANEL_3 = ReplyKeyboardMarkup([
        
                    [KeyboardButton(Text.ADMIN_PANEL_3_KEYBOARD[-2]),  # <
                     KeyboardButton(Text.ADMIN_PANEL_3_KEYBOARD[-1])], # Назад
                ], resize_keyboard=True)
    
class State:
    MAIN_MENU = 1

    NOTIFY_MENU = 2
    NOTIFY_MENU_LIST,       NOTIFY_MENU_ADD         = 21, 22
    NOTIFY_MENU_DELETE,     NOTIFY_MENU_CHANGE      = 23, 24

    # JOB_MENU = 3
    # JOB_MENU_LIST,          JOB_MENU_ADD            = 31, 32
    # JOB_MENU_DELETE,        JOB_MENU_CHANGE         = 33, 34

    HABBIT_MENU = 4
    HABBIT_MENU_LIST,       HABBIT_MENU_ADD         = 41, 42
    HABBIT_MENU_DELETE,     HABBIT_MENU_CHANGE      = 43, 44

    
    PROGRAMM_MENU = 5
    PROGRAMM_MENU_LIST,     PROGRAMM_MENU_ADD       = 51, 52
    PROGRAMM_MENU_DELETE,   PROGRAMM_MENU_CHANGE    = 53, 54


    ABOUT_ME_MENU = 6
    ABOUT_ME_MENU_CHANGE_NICK = 61

    ADMIN_PANEL_1, ADMIN_PANEL_2, ADMIN_PANEL_3     = 7, 77, 777

    ADMIN_PANEL_TAIL_LOG_BOT = 700_001

    MAIN_MENU_ADMIN = 8


class Database: 
    """
    Родительский класс для работы с базой данных.  Мы не хотим переходить на postgresql!
    Мы фанаты sqlite3!
    """
    def __init__(self):
        # Мы ищем файл который исполняется
        # Далее отступаем назад и в папке db делаем файл main.db
        self.path = os.path.dirname(os.path.abspath(__file__)) + '/../db/main.db'

    def run_query(self, query : str) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(query)
        con.commit()
        cur.close()
        con.close()

    def run_many_query(self, query : str, arr : list[str]) -> None:
        for item in arr:
            self.run_query(query, item)

    def get_from_query(self, query : str) -> list[any]:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(query)
        res = cur.fetchall()
        cur.close()
        con.close()
        return res

    def firstInitDatabase(self):
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        
        # Хочется чтобы чат был чистый, тут пишутся сообщения на удаление
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS message_to_delete (
                message_to_delete_id    INTEGER UNIQUE,
                datetime_to_delete      TEXT NOT NULL,
                chat_id                 TEXT NOT NULL,
                message_id              TEXT NOT NULL,
                deleted                 INTEGER DEFAULT 0,
                PRIMARY KEY(message_to_delete_id)
            );
        """)
        
        # Нужна для работы class Logger(Database)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS bot_log (
                bot_log_id      INTEGER UNIQUE,
                datetime        TEXT NOT NULL,
                text            TEXT NOT NULL,
                PRIMARY KEY(bot_log_id)
            );
        """)
        # Нужна для работы class User(Database)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS user (
                id_user	        INTEGER UNIQUE,
                tg_username	    TEXT NOT NULL UNIQUE,
                bot_username	TEXT,
                user_is_valid   INTEGER DEFAULT 1 CHECK (user_is_valid in (0, 1)),
                PRIMARY KEY(id_user)
            );
        """)
        # Тут указываются роли пользователей, данные заполняются при init
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS role (
                id_role	            INTEGER,
                name_role	        TEXT NOT NULL UNIQUE,
                description_role	TEXT,
                PRIMARY KEY(id_role)
            );
        """)
        con.commit()

        # Таблица напоминаний
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS notify (
                id_notify               INTEGER,
                chat_id                 INTEGER NOT NULL,
                user_id                 INTEGER NOT NULL,
                description             TEXT NOT NULL,
                time_create             TEXT NOT NULL,
                time_notify             TEXT NOT NULL,
                sent                    INTEGER DEFAULT 0,
                done                    INTEGER DEFAULT 0,
                PRIMARY KEY(id_notify),
                FOREIGN KEY(user_id) REFERENCES user(id_user)
            );
        """)
        con.commit()

        # Более крутые таблицы

        # Тут указываются какие роли для каких пользователей заведены
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS user_role (
                id_user_role	INTEGER,
                user	INTEGER NOT NULL,
                role	INTEGER NOT NULL,
                PRIMARY KEY(id_user_role),
                FOREIGN KEY(role) REFERENCES role(id_role),
                FOREIGN KEY(user) REFERENCES user(id_user)
            );
        """)
        con.commit()

        try:
            # Заполняем начальные значения для ролей в свежей базе
            Database().run_many_query(f"""
                INSERT INTO role
                    (name_role, description_role)
                VALUES 
                    (?,?);
            """, [("admin", "Имеет доступ ко всему контенту"),
                     ("user", "Начальная роль всех пользователей")])
        except Exception as e:
            # Если видим ошибку, получается что такие значения есть.
            print(e)
        cur.close()
        con.close()

# Можно настроить минимальный уровень вывода в консоль или файл
# logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="w")
# logging.basicConfig(level=logging.INFO)

class Logger(Database):
    """
    Данный класс работает с таблицей bot_log
    Туда я хочу писать события и ошибки бота

    TODO sec_taken - хочу сюда писать кол-во времени которое заняла та или иная операция
    TODO хочется чтобы при краше, выдавался список ошибок которые были ранее, например 10 до. что привело к ошибке.
    """

    def __init__(self):
        super().__init__()
    
    def log(self, message : str, level : str = 'INFO', verbose : bool = LOGGER_VERBOSE) -> None:
        """
        level = INFO | ERROR | WARNING | CRITICAL
        """
        assert message != '', "message is empty"
        assert level in ['INFO', 'ERROR', 'WARNING', 'CRITICAL'], f"level cant be {level}"

        Database().run_query(f"""
            INSERT INTO bot_log 
            (datetime, text)
            VALUES
            (datetime(), "{message}")
        """)

        if verbose:
            match level:
                case "INFO":
                    logging.info(f"{message}")
                case "ERROR":
                    logging.error(f"{message}")
                case "WARNING":
                    logging.warning(f"{message}")
                case "CRITICAL":
                    logging.critical(f"{message}")
                    exit()
                    
    def tail_log_bot(self, n : int) -> list[str] | str:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(Text.tail_log_bot_t0.format(n))
        res = cur.fetchall()
        cur.close()
        con.close()

        if len(res) == 0:
            return "Данная таблица пустая"
        else:
            return ["{} : {}\n\n".format(row[0], row[1]) for row in res]

class User(Database):
    """
    def createUser(self, tg_username : str) -> None

    def get_id_user(self, tg_username : str) -> int
    def get_bot_username(self, tg_username : str) -> str
    """
    def __init__(self):
        super().__init__()
        self.default_user_role = 'user'
        self.admin_user_role = 'admin'
        self.admin_list = ['pagamov']

    def createBot_username(self) -> str:
        """
        Делаем случайное имя для анонимного чата
        """
        pril = Text.createBot_username_t0
        animals = Text.createBot_username_t1
        dig = Text.createBot_username_t2

        return f"{random.choice(pril)}_{random.choice(animals)}_{''.join([random.choice(dig) for i in range(5)])}"

    def createUser(self, tg_username : str) -> None:
        """
        1. Добавляет пользователя в базу
        
        2. Ставит ему базовые права пользователя (роль)
        
        3. Проверяет есть ли ник в списке админов. Если есть - добавляет ему админские права
        """
        assert tg_username != '', "tg_username is empty"
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        Logger().log(f"Создаем пользователя {tg_username}")
        cur.execute(Text.createUser_t0.format(tg_username, self.createBot_username()))
        con.commit()
        # Ставим пользователю доступ по умолчанию
        Logger().log(f"Создаем пользователя {tg_username} - права по умолчанию")
        cur.execute(Text.createUser_t1.format(tg_username, self.default_user_role))
        con.commit()

        # Админские штучки
        if tg_username in self.admin_list:
            Logger().log(f"Создаем пользователя {tg_username} - админские штучки")
            cur.execute(Text.createUser_t2.format(tg_username, self.admin_user_role))
            con.commit()

        cur.close()
        con.close()

    def get_id_user(self, tg_username : str) -> int:
        """
        Вернем id_user из таблицы user по нику из tg. 
        
        -1 если пользователя нет в базе.
        """
        assert tg_username != '', "tg_username is empty"

        con = sqlite3.connect(self.path)
        cur = con.cursor()
        Logger().log(f"Ищем пользователя с ником {tg_username}")
        cur.execute(Text.get_id_user_t0.format(tg_username))
        res = cur.fetchall()
        cur.close()
        con.close()
        return -1 if len(res) == 0 else res[0][0]

    def is_admin(self, tg_username : str) -> bool:
        """
        Проверяет, является ли человек админом в системе по нику в тг.
        """
        assert tg_username != '', "tg_username is empty"

        con = sqlite3.connect(self.path)
        cur = con.cursor()
        Logger().log(f"Проверяем пользователя с ником {tg_username} является ли он админом")
        cur.execute(Text.is_admin_t0.format(tg_username, self.admin_user_role))
        res = cur.fetchall()
        cur.close()
        con.close()
        return False if len(res) == 0 else True

    def get_bot_username(self, tg_username : str) -> str:
        assert tg_username != '', Text.get_bot_username_err

        con = sqlite3.connect(self.path)
        cur = con.cursor()
        Logger().log(f"Ищем внутренний никнейм у пользователя с ником {tg_username}")
        cur.execute(Text.get_bot_username_t0.format(tg_username))
        res = cur.fetchall()
        cur.close()
        con.close()
        bot_username : str = res[0][0]
        assert bot_username != '', Text.get_bot_username_err
        return bot_username

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





async def NOTIFY_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    
    if text == Text.NOTIFY_MENU_KEYBOARD[0]:
        await update.message.reply_text('_Твои напоминания', )
        return State.NOTIFY_MENU
    
    elif text == Text.NOTIFY_MENU_KEYBOARD[1]:
        await update.message.reply_text('_Давай добавим тебе напоминание', )
        return State.NOTIFY_MENU
    
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
    logger = Logger()
    
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

    # states = dict(map(lambda i, k : k.append(CallbackQueryHandler(notify_queue_handler)), states))
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