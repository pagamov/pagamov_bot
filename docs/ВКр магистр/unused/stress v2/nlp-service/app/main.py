from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import structlog

from app.config import get_settings
from app.schemas import (
    SentimentAnalysisRequest, SentimentAnalysisResponse,
    BatchSentimentRequest, BatchSentimentResponse,
    BurnoutAssessmentRequest, BurnoutAssessmentResponse,HealthResponse
)
from app.services.analyzer import SentimentAnalyzer, BurnoutClassifier

settings = get_settings()
logger = structlog.get_logger()

sentiment_analyzer: SentimentAnalyzer = None
burnout_classifier: BurnoutClassifier = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sentiment_analyzer, burnout_classifier
    
    logger.info("starting_nlp_service")
    
    sentiment_analyzer = SentimentAnalyzer(
        model_name=settings.model_name,
        device=settings.device,
        hf_token=settings.hf_token
    )
    burnout_classifier = BurnoutClassifier()
    
    await sentiment_analyzer.initialize()
    await burnout_classifier.initialize()
    
    logger.info("nlp_service_ready")
    
    yield
    
    logger.info("shutting_down_nlp_service")


app = FastAPI(
    title="Sofia NLP Service",
    description="NLP Service for Burnout Detection",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.post("/api/v1/analyze/sentiment", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(request: SentimentAnalysisRequest):
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        logger.info("analyzing_text", text=request.text[:500])
        result = await sentiment_analyzer.analyze(request.text)
        logger.info(
            "analysis_result",
            text=request.text[:500],
            result={
                "positivity": result.get("positivity_score", 0),
                "negativity": result.get("negativity_score", 0),
                "cynicism": result.get("cynicism_score", 0),
                "apathy": result.get("apathy_score", 0),
                "irritability": result.get("irritability_score", 0),
                "devaluation": result.get("devaluation_score", 0),
                "complaint": result.get("complaint_score", 0)
            }
        )
        return SentimentAnalysisResponse(**result)
    except Exception as e:
        logger.error("sentiment_analysis_failed", error=str(e), text=request.text[:200])
        raise HTTPException(status_code=500, detail="Analysis failed")


@app.post("/api/v1/analyze/sentiment/batch", response_model=BatchSentimentResponse)
async def batch_analyze_sentiment(request: BatchSentimentRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail="Texts cannot be empty")
    
    logger.info("batch_analysis_started", text_count=len(request.texts))
    
    results = []
    for i, text in enumerate(request.texts):
        if text and len(text.strip()) > 0:
            try:
                result = await sentiment_analyzer.analyze(text)
                logger.info("batch_item_analyzed", index=i, text=text[:100])
                results.append(SentimentAnalysisResponse(**result))
            except Exception as e:
                logger.warning("batch_item_failed", index=i, error=str(e))
                results.append(None)
        else:
            results.append(None)
    
    return BatchSentimentResponse(
        results=results,
        processed_count=len([r for r in results if r is not None])
    )


@app.post("/api/v1/assess/burnout", response_model=BurnoutAssessmentResponse)
async def assess_burnout(request: BurnoutAssessmentRequest):
    try:
        result = await burnout_classifier.assess(
            sentiment_data=request.sentiment,
            message_metrics=request.message_metrics
        )
        return BurnoutAssessmentResponse(**result)
    except Exception as e:
        logger.error("burnout_assessment_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Assessment failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.nlp_api_port,
        reload=False
    )
