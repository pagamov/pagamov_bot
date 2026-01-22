from typing import Final, Sequence
import os
from dotenv import load_dotenv

from telegram import KeyboardButton, ReplyKeyboardMarkup

# Загрузка файла .env
load_dotenv()

# Паша если сольешь токен опять - обещаю перестать писать ботов для ВКР
TOKEN : Final = os.getenv("TOKEN")

# Означает, будет ли модуль Logger выводить данные не только в БД но еще и в консоль
LOGGER_VERBOSE : Final = True

# Столько char может быть максимум в одном текстовом сообщении в телеграме
TELEGRAM_MAX_MESSAGE_SIZE : Final = 4096


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

    firstInitDatabase_message_to_delete : str = """
        CREATE TABLE IF NOT EXISTS message_to_delete (
            message_to_delete_id    INTEGER UNIQUE,
            datetime_to_delete      TEXT NOT NULL,
            chat_id                 TEXT NOT NULL,
            message_id              TEXT NOT NULL,
            deleted                 INTEGER DEFAULT 0,
            PRIMARY KEY(message_to_delete_id)
        );
    """

    firstInitDatabase_bot_log : str = """
        CREATE TABLE IF NOT EXISTS bot_log (
            bot_log_id      INTEGER UNIQUE,
            datetime        TEXT NOT NULL,
            text            TEXT NOT NULL,
            PRIMARY KEY(bot_log_id)
        );
    """

    firstInitDatabase_user : str = """
        CREATE TABLE IF NOT EXISTS user (
            id_user	        INTEGER UNIQUE,
            tg_username	    TEXT NOT NULL UNIQUE,
            bot_username	TEXT,
            user_is_valid   INTEGER DEFAULT 1 CHECK (user_is_valid in (0, 1)),
            PRIMARY KEY(id_user)
        );
    """
    
    firstInitDatabase_role : str = """
        CREATE TABLE IF NOT EXISTS role (
            id_role	            INTEGER,
            name_role	        TEXT NOT NULL UNIQUE,
            description_role	TEXT,
            PRIMARY KEY(id_role)
        );
    """
    
    firstInitDatabase_notify : str = """
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
    """
    
    firstInitDatabase_user_role : str = """
        CREATE TABLE IF NOT EXISTS user_role (
            id_user_role	INTEGER,
            user	INTEGER NOT NULL,
            role	INTEGER NOT NULL,
            PRIMARY KEY(id_user_role),
            FOREIGN KEY(role) REFERENCES role(id_role),
            FOREIGN KEY(user) REFERENCES user(id_user)
        );
    """

    firstInitDatabase_insert_role : str = """
        INSERT INTO role
            (name_role, description_role)
        VALUES 
            (?,?);
    """

    firstInitDatabase_insert_role_arr : list = [
                ("admin", "Имеет доступ ко всему контенту"),
                ("user", "Начальная роль всех пользователей")]



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

    NOTIFY_MENU_ADD_DESCRIPTION = 220
    NOTIFY_MENU_ADD_DATEPICK = 221
    NOTIFY_MENU_ADD_TIMEPICK = 222

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

