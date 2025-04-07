from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters, ConversationHandler
from queue import Queue
import httpx
import asyncio

import os
from dotenv import load_dotenv

async def test_connection():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'https://api.telegram.org/bot{os.getenv("TOKEN")}/getMe')
            print(response.json())
    except httpx.ConnectError as e:
        print(f"Connection error: {e}")


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello! I am your bot.')

async def echo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(update.message.text)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update: {update} caused error {context.error}')

async def main() -> None:
    load_dotenv()
    await test_connection()
    app = Application.builder().token(os.getenv("TOKEN")).build()

    app.add_handler(CommandHandler("start", start))

    app.add_error_handler(error)

    app.run_polling(poll_interval=0.8)

if __name__ == '__main__':
    asyncio.run(main())