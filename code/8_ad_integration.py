import os
from enum import Enum
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

load_dotenv()

TOKEN = os.getenv("TOKEN")


class Text:
    REMINDER = "🔔 Время для привычки!"
    DESCRIPTION = "Выпить спортивный напиток после тренировки"
    FREQUENCY = "Ежедневно"
    
    AD = """💪 Не забудьте восстановить силы!
    
Активируйте скидку 15% на спортивные напитки XPower по промокоду: HABIT15
🔗 xpower.ru"""
    
    DONE = "✅ Выполнено!"
    POSTPONED = "⏰ Отложено"
    
    MENU = "Меню:"
    MAIN_KEYBOARD = ["Мои привычки", "Назад"]


class Keyboard:
    @staticmethod
    def get_main_menu():
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        return ReplyKeyboardMarkup([
            [KeyboardButton(Text.MAIN_KEYBOARD[0])],
            [KeyboardButton(Text.MAIN_KEYBOARD[1])]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_ad_keyboard(habit_id):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{habit_id}"),
                InlineKeyboardButton("⏰ Отложить", callback_data=f"postpone_{habit_id}")
            ]
        ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        Text.MENU,
        reply_markup=Keyboard.get_main_menu()
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "/reminder":
        habit_id = 1
        await update.message.reply_text(
            f"{Text.REMINDER}\n\n{Text.DESCRIPTION}\n({Text.FREQUENCY})\n\n{Text.AD}",
            reply_markup=Keyboard.get_ad_keyboard(habit_id)
        )
    
    return True


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("done_"):
        await query.edit_message_text(
            text=f"{query.message.text}\n\n{Text.DONE}"
        )
    elif query.data.startswith("postpone_"):
        await query.edit_message_text(
            text=f"{query.message.text}\n\n{Text.POSTPONED}"
        )


def main():
    app = Application.builder().token(TOKEN).build()
    
    # app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text(f"{Text.REMINDER}\n\n{Text.DESCRIPTION}\n({Text.FREQUENCY})\n\n{Text.AD}", reply_markup=Keyboard.get_ad_keyboard(1))))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    app.run_polling()


if __name__ == "__main__":
    main()