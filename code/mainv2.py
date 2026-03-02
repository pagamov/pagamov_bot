from telegram import Update, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from telegram.ext import CommandHandler, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler
from telegram.ext import filters, ApplicationBuilder
from telegram.ext import CallbackQueryHandler

import json

import functools
from typing import Callable


