import os
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")


class Text:
    MENU = "👑 Премиум меню"
    PREMIUM_KEYBOARD = ["📊 Подробная статистика", "💬 Чат с разработчиком", "Назад"]
    
    STATS = """📊 Подробная статистика (Премиум)

Период: За последние 30 дней

Привычки:
• Пить воду — 28/30 дней (93%)
• Зарядка — 21/30 дней (70%)
• Медитация — 15/30 дней (50%)

Серия: 12 дней
Лучшая серия: 21 день
Общее выполнение: 47 раз

График прогресса:
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 78%"""
    
    CHAT = "💬 Чат с разработчиком\n\nНапишите ваш вопрос, и мы ответим в течение 24 часов.\n\n📧 pag_habbit@mail.ru"
    
    PREMIUM_ONLY = "👑 Этот раздел доступен по подписке Премиум\n\nСтоимость: 199₽/месяц\n\n• Подробная статистика\n• Чат с разработчиком\n• Экспорт данных\n• Без рекламы\n\nДля активации нажмите /premium"
    
    BACK = "Назад"


class Keyboard:
    @staticmethod
    def get_premium_menu():
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.PREMIUM_KEYBOARD[0])],
            [KeyboardButton(Text.PREMIUM_KEYBOARD[1]), KeyboardButton(Text.PREMIUM_KEYBOARD[2])]
        ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        Text.MENU,
        reply_markup=Keyboard.get_premium_menu()
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == Text.PREMIUM_KEYBOARD[0]:
        await update.message.reply_text(
            Text.STATS,
            reply_markup=Keyboard.get_premium_menu()
        )
    elif text == Text.PREMIUM_KEYBOARD[1]:
        await update.message.reply_text(
            Text.CHAT,
            reply_markup=Keyboard.get_premium_menu()
        )
    elif text == Text.BACK:
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=Keyboard.get_premium_menu()
        )
    
    return True


def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    
    app.run_polling()


if __name__ == "__main__":
    main()