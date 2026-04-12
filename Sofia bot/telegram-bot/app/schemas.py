from pydantic import BaseModel, Field
from datetime import datetime, date, time
from typing import Optional
from decimal import Decimal


class ConsentRequest(BaseModel):
    consent_type: str
    granted: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ConsentResponse(BaseModel):
    id: int
    employee_id: int
    consent_type: str
    granted: bool
    granted_at: datetime
    revoked_at: Optional[datetime]

    class Config:
        from_attributes = True


class MessageAnalysisRequest(BaseModel):
    user_id: str
    chat_id: int
    text: str
    timestamp: datetime


class MessageMetricsInput(BaseModel):
    employee_id: int
    chat_id: int
    message_count: int
    avg_message_length: float
    response_time_avg: Optional[float] = None
    group_participation_rate: Optional[float] = None
    active_hours_start: Optional[time] = None
    active_hours_end: Optional[time] = None


class SentimentResult(BaseModel):
    positivity_score: float = Field(ge=0, le=1)
    negativity_score: float = Field(ge=0, le=1)
    neutrality_score: float = Field(ge=0, le=1)
    cynicism_score: float = Field(ge=0, le=1)
    apathy_score: float = Field(ge=0, le=1)
    irritability_score: float = Field(ge=0, le=1)
    devaluation_score: float = Field(ge=0, le=1)
    complaint_score: float = Field(ge=0, le=1)


class BurnoutAssessmentResult(BaseModel):
    emotional_exhaustion: float = Field(ge=0, le=100)
    depersonalization: float = Field(ge=0, le=100)
    personal_achievement: float = Field(ge=0, le=100)
    burnout_level: str
    burnout_score: float = Field(ge=0, le=100)


class EmployeeCreate(BaseModel):
    external_id: str
    chat_id: int
    department: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    external_id: str
    chat_id: int
    department: Optional[str]
    consent_given: bool
    last_activity: datetime

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    notification_type: str
    recipient_type: str
    recipient_id: Optional[int] = None
    department: Optional[str] = None
    severity: str
    employee_count_affected: Optional[int] = None
    department_avg_score: Optional[float] = None
    trend: Optional[str] = None
    message: Optional[str] = None


class DepartmentStats(BaseModel):
    department: str
    employee_count: int
    avg_burnout_score: float
    trend: str
    employees_at_risk: int


class HealthResponse(BaseModel):
    status: str
    database: bool
    nlp_service: bool
    timestamp: datetime
