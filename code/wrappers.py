from telegram import Update
from telegram.ext import ContextTypes

import functools
from typing import Callable

def log_chat_message(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(update: Update,
                      context: ContextTypes.DEFAULT_TYPE,
                      *args, **kwargs) -> int:

        chat_id = update.effective_chat.id if update.effective_chat else 'N/A'
        message_id = update.message.message_id if update.message else 'N/A'
        print(f"Chat ID: {chat_id}, Message ID: {message_id}")
        return await func(update, context, *args, **kwargs)
    return wrapper
