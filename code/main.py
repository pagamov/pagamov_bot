
from telegram import Update, ReplyKeyboardRemove
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler
from telegram.ext import filters

from Const import TOKEN, TELEGRAM_MAX_MESSAGE_SIZE

# TODO сделать изменение внутреннего аноним ника

from Database.Database import Database

from Database.Logger.Logger import Logger
from Database.User.User import User

# Handler section

class Text():
    MAIN_MENU_KEYBOARD =       ["Напоминания",      "Дела",
                                "Привычки",         "Готовые программы",
                                "Обо мне"]
    
    MAIN_MENU_ADMIN_KEYBOARD = ["Напоминания",      "Дела",
                                "Привычки",         "Готовые программы",
                                "Обо мне",          "Панель Админа"]

class Keyboard():
    MAIN_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton(Text.MAIN_MENU_KEYBOARD[0]),        KeyboardButton(Text.MAIN_MENU_KEYBOARD[1])],
                    [KeyboardButton(Text.MAIN_MENU_KEYBOARD[2]),        KeyboardButton(Text.MAIN_MENU_KEYBOARD[3])],
                    [KeyboardButton(Text.MAIN_MENU_KEYBOARD[4])]
                ], resize_keyboard=True)
    
    MAIN_MENU_ADMIN = ReplyKeyboardMarkup([
                    [KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[0]),        KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[1])],
                    [KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[2]),        KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[3])],
                    [KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[4]),        KeyboardButton(Text.MAIN_MENU_ADMIN_KEYBOARD[5])]
                ], resize_keyboard=True)
    
    NOTIFY_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton("Мои напоминания"),     KeyboardButton("Добавить")],
                    [KeyboardButton("Удалить"),             KeyboardButton("Изменить")],
                    [KeyboardButton("Настройки"),           KeyboardButton("Назад")]
                ], resize_keyboard=True)
    
    JOB_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton("Мои дела"),            KeyboardButton("Добавить")],
                    [KeyboardButton("Удалить"),             KeyboardButton("Изменить")],
                    [KeyboardButton("Настройки"),           KeyboardButton("Назад")]
                ], resize_keyboard=True)
    
    HABBIT_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton("Мои привычки"),        KeyboardButton("Добавить")],
                    [KeyboardButton("Удалить"),             KeyboardButton("Изменить")],
                    [KeyboardButton("Настройки"),           KeyboardButton("Назад")]
                ], resize_keyboard=True)
    
    PROGRAMM_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton("Мои готовые программы"),   KeyboardButton("Добавить")],
                    [KeyboardButton("Удалить"),                 KeyboardButton("Изменить")],
                    [KeyboardButton("Настройки"),               KeyboardButton("Назад")]
                ], resize_keyboard=True)
    
    ABOUT_ME_MENU = ReplyKeyboardMarkup([
                    [KeyboardButton("Изменить мой ник"),        KeyboardButton("Назад")]
                ], resize_keyboard=True)
    
    ADMIN_PANEL_1 = ReplyKeyboardMarkup([
                    [KeyboardButton("tail bot_log"),    KeyboardButton("2")],
                    [KeyboardButton("3"),               KeyboardButton("4")],
                    [KeyboardButton("5"),               KeyboardButton("6")],
                    [KeyboardButton("Назад"),           KeyboardButton(">")],
                ], resize_keyboard=True)
    
    ADMIN_PANEL_2 = ReplyKeyboardMarkup([
                    [KeyboardButton("7"),   KeyboardButton("8")],
                    [KeyboardButton("9"),   KeyboardButton("10")],
                    [KeyboardButton("11"),  KeyboardButton("12")],
                    [KeyboardButton("<"),   KeyboardButton("Назад"),    KeyboardButton(">")],
                ], resize_keyboard=True)
    
    ADMIN_PANEL_3 = ReplyKeyboardMarkup([
                    [KeyboardButton("13"),      KeyboardButton("14")],
                    [KeyboardButton("15"),      KeyboardButton("16")],
                    [KeyboardButton("17"),      KeyboardButton("18")],
                    [KeyboardButton("<"),       KeyboardButton("Назад")],
                ], resize_keyboard=True)
    
class State():
    MAIN_MENU = 1

    NOTIFY_MENU = 2
    NOTIFY_MENU_LIST,       NOTIFY_MENU_ADD         = 21, 22
    NOTIFY_MENU_DELETE,     NOTIFY_MENU_CHANGE      = 23, 24

    JOB_MENU = 3
    JOB_MENU_LIST,          JOB_MENU_ADD            = 31, 32
    JOB_MENU_DELETE,        JOB_MENU_CHANGE         = 33, 34

    HABBIT_MENU = 4
    HABBIT_MENU_LIST,       HABBIT_MENU_ADD         = 41, 42
    HABBIT_MENU_DELETE,     HABBIT_MENU_CHANGE      = 43, 44

    
    PROGRAMM_MENU = 5
    PROGRAMM_MENU_LIST,     PROGRAMM_MENU_ADD       = 51, 52
    PROGRAMM_MENU_DELETE,   PROGRAMM_MENU_CHANGE    = 53, 54


    ABOUT_ME_MENU = 6

    ADMIN_PANEL_1, ADMIN_PANEL_2, ADMIN_PANEL_3     = 7, 77, 777

    ADMIN_PANEL_TAIL_LOG_BOT = 700001

    MAIN_MENU_ADMIN = 8

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Тут мы начинаем работу в режиме диалога.
    Возвращаем меню
    """
    logger = Logger()
    user = User()

    message_type : str = update.message.chat.type
    text : str = update.message.text
    tg_username : str = update.effective_user.username

    t0 = """chat_id ({}), tg_username ({}) in start_command {}: {}"""
    t1 = "Добро пожаловать, {}!"
    t2 = """Добро пожаловать в мое приложение, {}!
Вам доступны напоминания и трекер привычек.
Также вы можете воспользоваться готовыми программами приобретения привычек или отказа от плохих.\n
Желаю удачи!"""
    t3 = """Добро пожаловать, о великий равный небу {}. Ваши покои вас ждут."""

    logger.log(t0.format(update.message.chat.id, tg_username, message_type, text))
    if user.get_id_user(tg_username) > 0:
        if user.is_admin(tg_username):
            await update.message.reply_text(t3.format(user.get_bot_username(tg_username)), reply_markup=Keyboard.MAIN_MENU_ADMIN)
            return State.MAIN_MENU_ADMIN
        else:
            await update.message.reply_text(t1.format(user.get_bot_username(tg_username)), reply_markup=Keyboard.MAIN_MENU)
            return State.MAIN_MENU
    else:
        user.createUser(tg_username)
        await update.message.reply_text(t2.format(user.get_bot_username(tg_username)), reply_markup=Keyboard.MAIN_MENU)
    return State.MAIN_MENU

async def FROM_IDLE_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Когда бот не работает и потом запускается, 
    пользователь может быть на другой клавиатуре посреди другого этапа.
    Чтобы вернуться к основному меню нажатием на клавишу, добавлен такой entry_points
    """
    user = User()
    tg_username : str = update.effective_user.username
    if user.is_admin(tg_username):
        await update.message.reply_text('Вернулись после падения сервера (не ваш косяк), о великий равный небу.', reply_markup=Keyboard.MAIN_MENU_ADMIN)
        return State.MAIN_MENU_ADMIN
    else:
        await update.message.reply_text('Вернулись после падения сервера', reply_markup=Keyboard.MAIN_MENU)
        return State.MAIN_MENU

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Работа бота завершена')
    
async def MAIN_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username

    if text == Text.MAIN_MENU_KEYBOARD[0]:
        await update.message.reply_text('Система напоминаний', reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU

    elif text == Text.MAIN_MENU_KEYBOARD[1]:
        await update.message.reply_text('Система твоих дел', reply_markup=Keyboard.JOB_MENU)
        return State.JOB_MENU
    
    elif text == Text.MAIN_MENU_KEYBOARD[2]:
        await update.message.reply_text('Система привычек', reply_markup=Keyboard.HABBIT_MENU)
        return State.HABBIT_MENU
    
    elif text == Text.MAIN_MENU_KEYBOARD[3]:
        await update.message.reply_text('Система готовых программ для тебя', reply_markup=Keyboard.PROGRAMM_MENU)
        return State.PROGRAMM_MENU
    
    elif text == Text.MAIN_MENU_KEYBOARD[4]:
        await update.message.reply_text('Что то о тебе', reply_markup=Keyboard.ABOUT_ME_MENU)
        return State.ABOUT_ME_MENU
    
    else:
        return State.MAIN_MENU_ADMIN if User().is_admin(tg_username) else State.MAIN_MENU
    
async def MAIN_MENU_ADMIN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username

    if text == Text.MAIN_MENU_ADMIN_KEYBOARD[0]:
        await update.message.reply_text('Система напоминаний', reply_markup=Keyboard.NOTIFY_MENU)
        return State.NOTIFY_MENU
    
    elif text == Text.MAIN_MENU_ADMIN_KEYBOARD[1]:
        await update.message.reply_text('Система твоих дел', reply_markup=Keyboard.JOB_MENU)
        return State.JOB_MENU
    
    elif text ==  Text.MAIN_MENU_ADMIN_KEYBOARD[2]:
        await update.message.reply_text('Система привычек', reply_markup=Keyboard.HABBIT_MENU)
        return State.HABBIT_MENU
    
    elif text ==  Text.MAIN_MENU_ADMIN_KEYBOARD[3]:
        await update.message.reply_text('Система готовых программ для тебя', reply_markup=Keyboard.PROGRAMM_MENU)
        return State.PROGRAMM_MENU
    
    elif text ==  Text.MAIN_MENU_ADMIN_KEYBOARD[4]:
        await update.message.reply_text('Что то о тебе', reply_markup=Keyboard.ABOUT_ME_MENU)
        return State.ABOUT_ME_MENU
    
    elif text ==  Text.MAIN_MENU_ADMIN_KEYBOARD[5]:
        await update.message.reply_text('Ну раз ты админ...', reply_markup=Keyboard.ADMIN_PANEL_1)
        return State.ADMIN_PANEL_1
    
    else:
        return State.MAIN_MENU_ADMIN if User().is_admin(tg_username) else State.MAIN_MENU

async def NOTIFY_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    match text:
        case "Мои напоминания":
            await update.message.reply_text('_Твои напоминания', )
            return State.NOTIFY_MENU
        case "Добавить":
            await update.message.reply_text('_Давай добавим тебе напоминание', )
            return State.NOTIFY_MENU
        case "Удалить":
            await update.message.reply_text('_Сейчас удалим напоминания', )
            return State.NOTIFY_MENU
        case "Изменить":
            await update.message.reply_text('_Давай изменим напоминание', )
            return State.NOTIFY_MENU_CHANGE
        case "Настройки":
            await update.message.reply_text('_Что там по настройкам?', )
            return State.NOTIFY_MENU
        case "Назад":
            match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _:
            return State.NOTIFY_MENU

async def JOB_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    match text:
        case "Мои дела":
            await update.message.reply_text('_Твои дела', )
            return State.JOB_MENU
        case "Добавить":
            await update.message.reply_text('_Давай добавим тебе дело', )
            return State.JOB_MENU
        case "Удалить":
            await update.message.reply_text('_Сейчас удалим дела', )
            return State.JOB_MENU
        case "Изменить":
            await update.message.reply_text('_Давай изменим дела', )
            return State.JOB_MENU
        case "Настройки":
            await update.message.reply_text('_Что там по настройкам?', )
            return State.JOB_MENU
        case "Назад":
            match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _:
            return State.JOB_MENU
    
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
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU_ADMIN)
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
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _:
            return State.PROGRAMM_MENU
        
async def ABOUT_ME_MENU(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # TODO сделать функцию смены ника
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    match text:
        # case "Изменить мой ник":
        #     await update.message.reply_text('_Сейчас поменяем твой ник', )
        #     return State.ABOUT_ME_MENU
        case "Назад":
            match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _: 
            return State.ABOUT_ME_MENU

async def ADMIN_PANEL_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text : str = update.message.text
    tg_username : str = update.effective_user.username
    match text:
        case 'tail bot_log':
            await update.message.reply_text('Сколько последних записей выдать?', reply_markup=ReplyKeyboardRemove())
            return State.ADMIN_PANEL_TAIL_LOG_BOT
            
        case '>':
            await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.ADMIN_PANEL_2)
            return State.ADMIN_PANEL_2
        
        case 'Назад':
            match User().is_admin(tg_username):
                case True:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _:
            return State.ADMIN_PANEL_1

async def ADMIN_PANEL_TAIL_LOG_BOT(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU_ADMIN)
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
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU_ADMIN)
                    return State.MAIN_MENU_ADMIN
                case _:
                    await update.message.reply_text('Давай в основное меню', reply_markup=Keyboard.MAIN_MENU)
                    return State.MAIN_MENU
        case _:
            return State.ADMIN_PANEL_3
        

async def handle_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

# Main section

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update:\n\n{update}\n\nCaused error:\n\n{context.error}')

def main():
    db = Database()
    db.firstInitDatabase()
    logger = Logger()
    
    try:
        logger.log("Starting bot...")
        app = Application.builder().token(TOKEN).build()
    except Exception as e:
        logger.log(e, level='CRITICAL') 

    app.add_handler(ConversationHandler(
        entry_points=[
                                        CommandHandler('start', start_command), 
                                        MessageHandler(filters.TEXT & (~filters.COMMAND), FROM_IDLE_MENU)],
        states= {
            State.MAIN_MENU :           [MessageHandler(filters.TEXT & (~filters.COMMAND), MAIN_MENU)],
            State.MAIN_MENU_ADMIN :     [MessageHandler(filters.TEXT & (~filters.COMMAND), MAIN_MENU_ADMIN)],
            State.NOTIFY_MENU :         [MessageHandler(filters.TEXT & (~filters.COMMAND), NOTIFY_MENU)],
            State.JOB_MENU :            [MessageHandler(filters.TEXT & (~filters.COMMAND), JOB_MENU)],
            State.HABBIT_MENU :         [MessageHandler(filters.TEXT & (~filters.COMMAND), HABBIT_MENU)],
            State.PROGRAMM_MENU :       [MessageHandler(filters.TEXT & (~filters.COMMAND), PROGRAMM_MENU)],
            State.ABOUT_ME_MENU :       [MessageHandler(filters.TEXT & (~filters.COMMAND), ABOUT_ME_MENU)],
            State.ADMIN_PANEL_1 :       [MessageHandler(filters.TEXT & (~filters.COMMAND), ADMIN_PANEL_1)],

            State.ADMIN_PANEL_TAIL_LOG_BOT : [MessageHandler(filters.TEXT & (~filters.COMMAND), ADMIN_PANEL_TAIL_LOG_BOT)],

            State.ADMIN_PANEL_2 :       [MessageHandler(filters.TEXT & (~filters.COMMAND), ADMIN_PANEL_2)],
            State.ADMIN_PANEL_3 :       [MessageHandler(filters.TEXT & (~filters.COMMAND), ADMIN_PANEL_3)],
            ConversationHandler.END :   [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_final)]
        },
        fallbacks=[MessageHandler('cancel', cancel_command)]
    ))
    app.add_error_handler(error)

    try:
        logger.log("Polling bot...")
        app.run_polling(poll_interval=0.8, )
    except Exception as e:
        logger.log(e, level='CRITICAL')

if __name__ == '__main__':
    main()