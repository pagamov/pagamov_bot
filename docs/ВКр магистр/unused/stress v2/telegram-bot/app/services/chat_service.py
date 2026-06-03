from datetime import datetime, date, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.models import (
    Chat, MessageMetrics,
    SentimentMetrics, BurnoutAssessment, Notification, AuditLog
)
import structlog

logger = structlog.get_logger()


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_chat(self, chat_id: int, chat_type: str, title: str = None) -> Chat:
        result = await self.db.execute(
            select(Chat).where(Chat.chat_id == chat_id)
        )
        chat = result.scalar_one_or_none()
        
        if not chat:
            chat = Chat(
                chat_id=chat_id,
                chat_type=chat_type,
                title=title or f"Department_{chat_id}",
                is_monitored=True
            )
            self.db.add(chat)
            await self.db.commit()
            await self.db.refresh(chat)
            logger.info("chat_created", chat_id=chat_id, title=title)
        
        return chat

    async def get_all_monitored_chats(self) -> List[Chat]:
        result = await self.db.execute(
            select(Chat).where(Chat.is_monitored == True)
        )
        return list(result.scalars().all())


class MetricsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_sentiment_metrics(self, chat_id: int, sentiment_data: dict):
        chat_result = await self.db.execute(
            select(Chat).where(Chat.chat_id == chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        
        if not chat:
            chat = await ChatService(self.db).get_or_create_chat(chat_id, "group")
        
        metrics = SentimentMetrics(
            chat_id=chat.id,
            positivity_score=sentiment_data.get("positivity_score", 0),
            negativity_score=sentiment_data.get("negativity_score", 0),
            neutrality_score=sentiment_data.get("neutrality_score", 0),
            cynicism_score=sentiment_data.get("cynicism_score", 0),
            apathy_score=sentiment_data.get("apathy_score", 0),
            irritability_score=sentiment_data.get("irritability_score", 0),
            devaluation_score=sentiment_data.get("devaluation_score", 0),
            complaint_score=sentiment_data.get("complaint_score", 0),
            period_date=date.today(),
            period_type="daily"
        )
        self.db.add(metrics)
        await self.db.commit()

    async def save_message_metrics(self, chat_id: int, metrics_data: dict):
        chat_result = await self.db.execute(
            select(Chat).where(Chat.chat_id == chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        
        if not chat:
            chat = await ChatService(self.db).get_or_create_chat(chat_id, "group")
        
        metrics = MessageMetrics(
            chat_id=chat.id,
            message_count=metrics_data.get("message_count", 0),
            avg_message_length=metrics_data.get("avg_message_length", 0),
            period_date=date.today(),
            period_type="daily"
        )
        self.db.add(metrics)
        await self.db.commit()

    async def save_burnout_assessment(self, chat_id: int, assessment_data: dict):
        chat_result = await self.db.execute(
            select(Chat).where(Chat.chat_id == chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        
        if not chat:
            chat = await ChatService(self.db).get_or_create_chat(chat_id, "group")
        
        assessment = BurnoutAssessment(
            chat_id=chat.id,
            emotional_exhaustion=assessment_data.get("emotional_exhaustion", 0),
            depersonalization=assessment_data.get("depersonalization", 0),
            personal_achievement=assessment_data.get("personal_achievement", 0),
            burnout_level=assessment_data.get("burnout_level", "normal"),
            burnout_score=assessment_data.get("burnout_score", 0),
            period_date=date.today(),
            period_type="daily"
        )
        self.db.add(assessment)
        await self.db.commit()


class StatsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._weekday_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    def _make_bar(self, value: float, max_value: float = 100, width: int = 10) -> str:
        filled = int((value / max_value) * width)
        filled = max(0, min(width, filled))
        return "▓" * filled + "░" * (width - filled)

    async def get_chat_history(self, chat_id: int, days: int = 7) -> List[dict]:
        chat_result = await self.db.execute(
            select(Chat).where(Chat.chat_id == chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        
        if not chat:
            return []
        
        start_date = date.today() - timedelta(days=days - 1)
        
        result = await self.db.execute(
            select(BurnoutAssessment)
            .where(BurnoutAssessment.chat_id == chat.id)
            .where(BurnoutAssessment.period_date >= start_date)
            .order_by(BurnoutAssessment.period_date)
        )
        assessments = list(result.scalars().all())
        
        history = []
        day_map = {}
        for a in assessments:
            day_map[a.period_date] = a
        
        for i in range(days):
            d = start_date + timedelta(days=i)
            weekday = self._weekday_ru[d.weekday()]
            
            if d in day_map:
                a = day_map[d]
                score = float(a.burnout_score or 0)
                history.append({
                    "date": d,
                    "weekday": weekday,
                    "score": score,
                    "level": a.burnout_level,
                    "bar": self._make_bar(score)
                })
            else:
                history.append({
                    "date": d,
                    "weekday": weekday,
                    "score": None,
                    "level": None,
                    "bar": "░" * 10
                })
        
        return history

    async def calculate_trend(self, chat_id: int) -> dict:
        chat_result = await self.db.execute(
            select(Chat).where(Chat.chat_id == chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        
        if not chat:
            return {"trend": "unknown", "change_percent": 0, "direction": "?"}
        
        today = date.today()
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)
        
        result_current = await self.db.execute(
            select(func.avg(BurnoutAssessment.burnout_score))
            .where(BurnoutAssessment.chat_id == chat.id)
            .where(BurnoutAssessment.period_date >= week_ago)
        )
        avg_current = result_current.scalar() or 0
        
        result_previous = await self.db.execute(
            select(func.avg(BurnoutAssessment.burnout_score))
            .where(BurnoutAssessment.chat_id == chat.id)
            .where(BurnoutAssessment.period_date >= two_weeks_ago)
            .where(BurnoutAssessment.period_date < week_ago)
        )
        avg_previous = result_previous.scalar() or 0
        
        if avg_previous == 0:
            return {"trend": "unknown", "change_percent": 0, "direction": "?", "avg_current": 0, "avg_previous": 0}
        
        change_percent = ((avg_current - avg_previous) / avg_previous) * 100
        
        if change_percent > 10:
            trend = "worsening"
            direction = "↗"
        elif change_percent < -10:
            trend = "improving"
            direction = "↘"
        else:
            trend = "stable"
            direction = "➡"
        
        return {
            "trend": trend,
            "change_percent": round(change_percent, 1),
            "direction": direction,
            "avg_current": round(avg_current, 1),
            "avg_previous": round(avg_previous, 1)
        }

    async def get_chat_stats(self, chat_id: int) -> dict:
        chat_result = await self.db.execute(
            select(Chat).where(Chat.chat_id == chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        
        if not chat:
            return None
        
        sentiment_result = await self.db.execute(
            select(
                func.avg(SentimentMetrics.positivity_score).label("avg_positivity"),
                func.avg(SentimentMetrics.negativity_score).label("avg_negativity"),
                func.avg(SentimentMetrics.cynicism_score).label("avg_cynicism"),
                func.avg(SentimentMetrics.apathy_score).label("avg_apathy"),
                func.avg(SentimentMetrics.complaint_score).label("avg_complaint"),
                func.count(SentimentMetrics.id).label("message_count")
            )
            .where(SentimentMetrics.chat_id == chat.id)
            .where(SentimentMetrics.period_date == date.today())
        )
        sentiment = sentiment_result.first()
        
        burnout_result = await self.db.execute(
            select(
                func.avg(BurnoutAssessment.burnout_score).label("avg_burnout"),
                func.avg(BurnoutAssessment.emotional_exhaustion).label("avg_ee"),
                func.avg(BurnoutAssessment.depersonalization).label("avg_dp"),
                func.avg(BurnoutAssessment.personal_achievement).label("avg_pa"),
                func.max(BurnoutAssessment.burnout_level).label("max_level")
            )
            .where(BurnoutAssessment.chat_id == chat.id)
            .where(BurnoutAssessment.period_date == date.today())
        )
        burnout = burnout_result.first()
        
        return {
            "chat_id": chat_id,
            "title": chat.title,
            "message_count": sentiment.message_count if sentiment else 0,
            "sentiment": {
                "positivity": round(float(sentiment.avg_positivity or 0), 3),
                "negativity": round(float(sentiment.avg_negativity or 0), 3),
                "cynicism": round(float(sentiment.avg_cynicism or 0), 3),
                "apathy": round(float(sentiment.avg_apathy or 0), 3),
                "complaint": round(float(sentiment.avg_complaint or 0), 3),
            },
            "burnout": {
                "avg_score": round(float(burnout.avg_burnout or 0), 1),
                "emotional_exhaustion": round(float(burnout.avg_ee or 0), 1),
                "depersonalization": round(float(burnout.avg_dp or 0), 1),
                "personal_achievement": round(float(burnout.avg_pa or 0), 1),
                "level": burnout.max_level or "normal"
            }
        }

    async def get_all_chats_stats(self) -> List[dict]:
        chats_result = await self.db.execute(
            select(Chat).where(Chat.is_monitored == True)
        )
        chats = list(chats_result.scalars().all())
        
        stats = []
        for chat in chats:
            chat_stats = await self.get_chat_stats(chat.chat_id)
            if chat_stats:
                stats.append(chat_stats)
        
        return stats


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(self, notification_data: dict) -> Notification:
        notification = Notification(
            notification_type=notification_data.get("notification_type", "burnout_alert"),
            recipient_type=notification_data.get("recipient_type", "manager"),
            department=notification_data.get("department"),
            severity=notification_data.get("severity", "info"),
            employee_count_affected=notification_data.get("employee_count_affected"),
            department_avg_score=notification_data.get("department_avg_score"),
            trend=notification_data.get("trend"),
            message=notification_data.get("message")
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        event_type: str,
        action: str,
        user_id: Optional[int] = None,
        user_external_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        log_entry = AuditLog(
            event_type=event_type,
            action=action,
            user_id=user_id,
            user_external_id=user_external_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log_entry)
        await self.db.commit()
