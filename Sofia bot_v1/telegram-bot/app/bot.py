import asyncio
import structlog
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.constants import ChatType

from app.database import AsyncSessionLocal
from app.services.chat_service import ChatService, MetricsService, StatsService
from app.services.nlp_client import NLPServiceClient
from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()

nlp_client = NLPServiceClient(settings.nlp_service_url)


class SofiaBot:
    def __init__(self):
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("Да, я согласен", callback_data="consent_yes")],
            [InlineKeyboardButton("Нет, отказываюсь", callback_data="consent_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        consent_text = (
            "Привет! Я — Sofia, бот для мониторинга эмоционального благополучия.\n\n"
            "📊 Я анализирую сообщения в рабочих чатах и выявляю признаки выгорания.\n\n"
            "🔒 Данные агрегируются по подразделениям (чатам).\n"
            "Ваши индивидуальные сообщения не сохраняются.\n\n"
            "Вы даёте согласие на обработку данных?"
        )
        
        await update.message.reply_text(consent_text, reply_markup=reply_markup)

    async def consent_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        logger.info("consent_callback", user_id=user_id, data=query.data)
        
        if query.data == "consent_yes":
            await query.edit_message_text(
                "✅ Согласие получено!\n\n"
                "Теперь:\n"
                "• Добавив бота в группу, он начнёт анализировать сообщения\n"
                "• В личных сообщениях используйте /stats для просмотра статистики"
            )
        else:
            await query.edit_message_text("❌ Вы отказались от участия.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "📊 *Sofia — Мониторинг выгорания*\n\n"
            "📌 *Команды:*\n"
            "/start — Начать работу\n"
            "/help — Эта справка\n"
            "/stats — Статистика по чатам\n"
            "/stats [id чата] — Статистика конкретного чата\n\n"
            "📖 *Как работает:*\n"
            "• Бот анализирует сообщения в группах\n"
            "• Данные агрегируются по подразделениям\n"
            "• Личные сообщения не сохраняются"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        
        if update.message.chat.type not in [ChatType.PRIVATE]:
            await update.message.reply_text(
                "📊 Команда /stats доступна только в личных сообщениях боту."
            )
            return
        
        async with AsyncSessionLocal() as db:
            stats_service = StatsService(db)
            
            all_stats = await stats_service.get_all_chats_stats()
            
            if not all_stats:
                await update.message.reply_text(
                    "📊 Нет данных для отображения.\n\n"
                    "Добавьте бота в групповые чаты - он начнёт собирать статистику."
                )
                return
            
            message_lines = ["📊 *Статистика по подразделениям*\n"]
            
            for i, stats in enumerate(all_stats[:10], 1):
                level_emoji = {
                    "normal": "🟢",
                    "initial": "🟡",
                    "moderate": "🟠",
                    "high": "🔴"
                }.get(stats["burnout"]["level"], "⚪")
                
                message_lines.append(
                    f"{i}. {level_emoji} *{stats['title']}*\n"
                    f"   Сообщений сегодня: {stats['message_count']}\n"
                    f"   Выгорание: {stats['burnout']['avg_score']:.1f}% "
                    f"({stats['burnout']['level']})\n"
                    f"   EE: {stats['burnout']['emotional_exhaustion']:.1f} | "
                    f"DP: {stats['burnout']['depersonalization']:.1f}\n"
                )
            
            message_lines.append("\n_ID чата можно использовать с командой /stats [id]_")
            
            await update.message.reply_text(
                "\n".join(message_lines),
                parse_mode="Markdown"
            )

    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if not text:
            return
        
        chat_id = update.message.chat_id
        chat_title = update.message.chat.title or f"Chat_{chat_id}"
        
        logger.info(
            "group_message_received",
            chat_id=chat_id,
            chat_title=chat_title,
            text=text[:50]
        )
        
        sentiment_result = nlp_client.analyze_sentiment_sync(text)
        
        if sentiment_result:
            async with AsyncSessionLocal() as db:
                chat_service = ChatService(db)
                metrics_service = MetricsService(db)
                
                chat = await chat_service.get_or_create_chat(chat_id, "group", chat_title)
                
                await metrics_service.save_sentiment_metrics(chat_id, sentiment_result)
                
                burnout_result = nlp_client.assess_burnout_sync(sentiment_result)
                if burnout_result:
                    await metrics_service.save_burnout_assessment(chat_id, burnout_result)
                
                logger.info(
                    "metrics_saved",
                    chat_id=chat_id,
                    sentiment=sentiment_result,
                    burnout=burnout_result
                )

    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 Напишите /help для списка команд или /stats для просмотра статистики."
        )

    async def error_handler(self, update, context):
        logger.error(
            "telegram_error",
            error=str(context.error),
            update_id=update.update_id if update else None
        )

    def run(self):
        logger.info("initializing_telegram_bot")
        
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        
        self.application.add_handler(CallbackQueryHandler(self.consent_callback, pattern="consent_"))
        
        self.application.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
            self.handle_group_message
        ))
        
        self.application.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
            self.handle_private_message
        ))
        
        self.application.add_error_handler(self.error_handler)
        
        logger.info("telegram_bot_ready_starting_polling")
        self.application.run_polling(drop_pending_updates=True)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    logger.info("sofia_bot_starting")
    
    bot = SofiaBot()
    bot.run()


if __name__ == "__main__":
    main()
