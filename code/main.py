from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from database import Database
from handlers.habit_handler import HabitHandler
import os

# Инициализация базы данных
db = Database()
db.initialize_database()

# Инициализация обработчиков
habit_handler = HabitHandler()

async def start(update, context):
    await update.message.reply_text("Добро пожаловать в бот для отслеживания привычек!")

def main():
    # Создание приложения
    application = Application.builder().token(os.getenv("TOKEN")).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
