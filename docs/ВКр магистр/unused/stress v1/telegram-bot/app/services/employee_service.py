from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models import (
    Employee, Consent, Chat, ChatMember, MessageMetrics,
    SentimentMetrics, BurnoutAssessment, Notification, AuditLog
)
from app.schemas import EmployeeCreate, NotificationCreate, DepartmentStats
import structlog

logger = structlog.get_logger()


class EmployeeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, external_id: str, chat_id: int, department: Optional[str] = None) -> Employee:
        result = await self.db.execute(
            select(Employee).where(Employee.external_id == external_id)
        )
        employee = result.scalar_one_or_none()
        
        if not employee:
            employee = Employee(
                external_id=external_id,
                chat_id=chat_id,
                department=department
            )
            self.db.add(employee)
            await self.db.commit()
            await self.db.refresh(employee)
            logger.info("employee_created", employee_id=employee.id, external_id=external_id)
        
        return employee

    async def update_last_activity(self, employee_id: int):
        await self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        result = await self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()
        if employee:
            employee.last_activity = datetime.utcnow()
            await self.db.commit()

    async def get_by_external_id(self, external_id: str) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(Employee.external_id == external_id)
        )
        return result.scalar_one_or_none()


class ConsentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def grant_consent(self, employee_id: int, consent_type: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Consent:
        result = await self.db.execute(
            select(Consent).where(
                and_(
                    Consent.employee_id == employee_id,
                    Consent.consent_type == consent_type
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.granted = True
            existing.granted_at = datetime.utcnow()
            existing.revoked_at = None
            consent = existing
        else:
            consent = Consent(
                employee_id=employee_id,
                consent_type=consent_type,
                granted=True,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(consent)
        
        employee_result = await self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = employee_result.scalar_one_or_none()
        if employee:
            employee.consent_given = True
            employee.consent_date = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(consent)
        return consent

    async def revoke_consent(self, employee_id: int, consent_type: str) -> Optional[Consent]:
        result = await self.db.execute(
            select(Consent).where(
                and_(
                    Consent.employee_id == employee_id,
                    Consent.consent_type == consent_type
                )
            )
        )
        consent = result.scalar_one_or_none()
        
        if consent:
            consent.granted = False
            consent.revoked_at = datetime.utcnow()
            await self.db.commit()
        
        return consent

    async def has_valid_consent(self, employee_id: int) -> bool:
        result = await self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()
        return employee.consent_given if employee else False


class MetricsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_sentiment_metrics(self, employee_id: int, sentiment_data: dict):
        from datetime import date
        metrics = SentimentMetrics(
            employee_id=employee_id,
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

    async def save_message_metrics(self, employee_id: int, chat_id: int, metrics_data: dict):
        from datetime import date
        metrics = MessageMetrics(
            employee_id=employee_id,
            chat_id=chat_id,
            message_count=metrics_data.get("message_count", 0),
            avg_message_length=metrics_data.get("avg_message_length", 0),
            response_time_avg=metrics_data.get("response_time_avg"),
            group_participation_rate=metrics_data.get("group_participation_rate"),
            active_hours_start=metrics_data.get("active_hours_start"),
            active_hours_end=metrics_data.get("active_hours_end"),
            period_date=date.today(),
            period_type="daily"
        )
        self.db.add(metrics)
        await self.db.commit()

    async def save_burnout_assessment(self, employee_id: int, assessment_data: dict):
        from datetime import date
        assessment = BurnoutAssessment(
            employee_id=employee_id,
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


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(self, notification_data: NotificationCreate) -> Notification:
        notification = Notification(
            notification_type=notification_data.notification_type,
            recipient_type=notification_data.recipient_type,
            recipient_id=notification_data.recipient_id,
            department=notification_data.department,
            severity=notification_data.severity,
            employee_count_affected=notification_data.employee_count_affected,
            department_avg_score=notification_data.department_avg_score,
            trend=notification_data.trend,
            message=notification_data.message
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def get_department_stats(self, department: str) -> Optional[DepartmentStats]:
        result = await self.db.execute(
            select(
                Employee.department,
                func.count(Employee.id).label("employee_count"),
                func.avg(BurnoutAssessment.burnout_score).label("avg_burnout_score"),
                func.max(BurnoutAssessment.burnout_level).label("max_level")
            )
            .join(BurnoutAssessment, Employee.id == BurnoutAssessment.employee_id)
            .where(Employee.department == department)
            .group_by(Employee.department)
        )
        row = result.first()
        
        if not row:
            return None
        
        at_risk_result = await self.db.execute(
            select(func.count(Employee.id))
            .join(BurnoutAssessment, Employee.id == BurnoutAssessment.employee_id)
            .where(
                and_(
                    Employee.department == department,
                    BurnoutAssessment.burnout_level.in_(["moderate", "high"])
                )
            )
        )
        at_risk_count = at_risk_result.scalar() or 0
        
        return DepartmentStats(
            department=row.department,
            employee_count=row.employee_count,
            avg_burnout_score=float(row.avg_burnout_score) if row.avg_burnout_score else 0,
            trend="stable",
            employees_at_risk=at_risk_count
        )


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
