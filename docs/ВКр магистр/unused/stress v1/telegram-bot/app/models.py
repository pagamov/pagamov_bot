from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey, Date, Time, Numeric, JSON
from sqlalchemy.sql import func
from app.database import Base


class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    chat_type = Column(String(50), nullable=False)
    title = Column(String(255))
    is_monitored = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class MessageMetrics(Base):
    __tablename__ = "message_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    recorded_at = Column(DateTime, server_default=func.now())
    message_count = Column(Integer, default=0)
    avg_message_length = Column(Numeric(10, 2), default=0)
    response_time_avg = Column(Numeric(10, 2))
    group_participation_rate = Column(Numeric(5, 4))
    active_hours_start = Column(Time)
    active_hours_end = Column(Time)
    period_date = Column(Date, index=True)
    period_type = Column(String(20), default="daily")


class SentimentMetrics(Base):
    __tablename__ = "sentiment_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    recorded_at = Column(DateTime, server_default=func.now())
    positivity_score = Column(Numeric(5, 4))
    negativity_score = Column(Numeric(5, 4))
    neutrality_score = Column(Numeric(5, 4))
    cynicism_score = Column(Numeric(5, 4))
    apathy_score = Column(Numeric(5, 4))
    irritability_score = Column(Numeric(5, 4))
    devaluation_score = Column(Numeric(5, 4))
    complaint_score = Column(Numeric(5, 4))
    period_date = Column(Date, index=True)
    period_type = Column(String(20), default="daily")


class BurnoutAssessment(Base):
    __tablename__ = "burnout_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    recorded_at = Column(DateTime, server_default=func.now())
    emotional_exhaustion = Column(Numeric(5, 2))
    depersonalization = Column(Numeric(5, 2))
    personal_achievement = Column(Numeric(5, 2))
    burnout_level = Column(String(20))
    burnout_score = Column(Numeric(5, 2))
    period_date = Column(Date, index=True)
    period_type = Column(String(20), default="daily")


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(String(50), nullable=False)
    recipient_type = Column(String(50), nullable=False)
    recipient_id = Column(Integer)
    department = Column(String(255))
    severity = Column(String(20))
    employee_count_affected = Column(Integer)
    department_avg_score = Column(Numeric(5, 2))
    trend = Column(String(20))
    message = Column(Text)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer)
    user_external_id = Column(String(255))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), index=True)
