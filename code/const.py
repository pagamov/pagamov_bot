from typing import Final
import os
from dotenv import load_dotenv
from enum import Enum
from datetime import datetime, timedelta
from telegram import KeyboardButton, ReplyKeyboardMarkup

load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
LOGGER_VERBOSE: Final = True
TELEGRAM_MAX_MESSAGE_SIZE: Final = 4096

class Text:
    start_command_t0 = "chat_id ({})\ntg_username ({}) in start_command {}: {}"
    start_command_t1 = "Добро пожаловать, {}!"
    start_command_t2 = "Добро пожаловать в мое приложение, {}!\nВам доступны напоминания и трекер привычек.\nТакже вы можете воспользоваться готовыми программами приобретения привычек или отказа от плохих.\nЖелаю удачи!"
    start_command_t3 = "Добро пожаловать, о великий равный небу {}.\nВаши покои вас ждут."
    
    MAIN_MENU_KEYBOARD = ["Напоминания", "Мои привычки", "Готовые программы", "Обо мне"]
    MAIN_MENU_ADMIN_KEYBOARD = MAIN_MENU_KEYBOARD + ["Панель Админа"]
    
    NOTIFY_MENU_KEYBOARD = ["Мои напоминания", "Добавить", "Удалить", "Изменить", "Настройки", "Назад"]
    HABBIT_MENU_KEYBOARD = ["Мои привычки", "Добавить", "Удалить", "Изменить", "Настройки", "Назад"]
    PROGRAMM_MENU_KEYBOARD = ["Мои готовые программы", "Добавить", "Удалить", "Изменить", "Настройки", "Назад"]
    ABOUT_ME_MENU_KEYBOARD = ["Изменить мой ник", "Назад"]
    
    ADMIN_PANEL_1_KEYBOARD = ["Получить логи бота", "Добавить напоминание через 1 минуту", "Назад", ">"]
    ADMIN_PANEL_2_KEYBOARD = ["<", "Назад", ">"]
    ADMIN_PANEL_3_KEYBOARD = ["<", "Назад"]
    ABOUT_ME_CHANGE_NICK_KEYBOARD = ["Попробуем еще раз", "Мне нравится", "Оставить все как было"]
    
    RETURN_TO_MENU_ADMIN = "Давай в основное меню, великий господин равный небу"
    RETURN_TO_MENU = "Давай в основное меню"

class Keyboard:
    @staticmethod
    def get_main_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MAIN_MENU_KEYBOARD[0])],
            [KeyboardButton(Text.MAIN_MENU_KEYBOARD[1]), KeyboardButton(Text.MAIN_MENU_KEYBOARD[2])],
            [KeyboardButton(Text.MAIN_MENU_KEYBOARD[3])]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_main_menu_admin():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[0])],
            [KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[1]), KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[2])],
            [KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[3]), KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[4])]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_notify_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[0]), KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[1])],
            [KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[2]), KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[3])],
            [KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[4]), KeyboardButton(Text.NOTIFY_MENU_KEYBOARD[5])]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_habbit_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.HABBIT_MENU_KEYBOARD[0]), KeyboardButton(Text.HABBIT_MENU_KEYBOARD[1])],
            [KeyboardButton(Text.HABBIT_MENU_KEYBOARD[2]), KeyboardButton(Text.HABBIT_MENU_KEYBOARD[3])],
            [KeyboardButton(Text.HABBIT_MENU_KEYBOARD[4]), KeyboardButton(Text.HABBIT_MENU_KEYBOARD[5])]
        ], resize_keyboard=True)

class State(Enum):
    MAIN_MENU = 1
    MAIN_MENU_ADMIN = 2
    NOTIFY_MENU = 3
    HABBIT_MENU = 4
    PROGRAMM_MENU = 5
    ABOUT_ME_MENU = 6
    ADMIN_PANEL_1 = 7
    ADMIN_PANEL_2 = 8
    ADMIN_PANEL_3 = 9
