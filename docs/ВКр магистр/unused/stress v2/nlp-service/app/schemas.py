from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SentimentAnalysisRequest(BaseModel):
    text: str


class BatchSentimentRequest(BaseModel):
    texts: list[str]


class SentimentAnalysisResponse(BaseModel):
    positivity_score: float = Field(ge=0, le=1, description="Score from 0 to 1")
    negativity_score: float = Field(ge=0, le=1)
    neutrality_score: float = Field(ge=0, le=1)
    cynicism_score: float = Field(ge=0, le=1)
    apathy_score: float = Field(ge=0, le=1)
    irritability_score: float = Field(ge=0, le=1)
    devaluation_score: float = Field(ge=0, le=1)
    complaint_score: float = Field(ge=0, le=1)


class BurnoutAssessmentRequest(BaseModel):
    sentiment: dict
    message_metrics: dict


class BurnoutAssessmentResponse(BaseModel):
    emotional_exhaustion: float = Field(ge=0, le=100)
    depersonalization: float = Field(ge=0, le=100)
    personal_achievement: float = Field(ge=0, le=100)
    burnout_level: str
    burnout_score: float = Field(ge=0, le=100)


class BatchSentimentResponse(BaseModel):
    results: list[Optional[SentimentAnalysisResponse]]
    processed_count: int


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
