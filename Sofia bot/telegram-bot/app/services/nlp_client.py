import httpx
from typing import Optional
import structlog

logger = structlog.get_logger()


class NLPServiceClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def analyze_sentiment_sync(self, text: str) -> Optional[dict]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.post(
                    "/api/v1/analyze/sentiment",
                    json={"text": text}
                )
                response.raise_for_status()
                data = response.json()
                logger.info("sentiment_result", text=text[:50], data=data)
                return data
        except httpx.HTTPError as e:
            logger.error("nlp_sentiment_failed", error=str(e), text=text[:100])
            return None

    def assess_burnout_sync(self, sentiment_data: dict) -> Optional[dict]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.post(
                    "/api/v1/assess/burnout",
                    json={
                        "sentiment": sentiment_data,
                        "message_metrics": {}
                    }
                )
                response.raise_for_status()
                data = response.json()
                logger.info("burnout_assessment_result", data=data)
                return data
        except httpx.HTTPError as e:
            logger.error("nlp_burnout_failed", error=str(e))
            return None
