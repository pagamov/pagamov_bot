from functools import lru_cache
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN")
    nlp_service_url: str = "http://nlp_service:8000"
    
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "sofia_burnout"
    postgres_user: str = "sofia_user"
    postgres_password: str = "sofia_password"
    
    database_url: str = ""
    
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.database_url:
            self.database_url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment or .env file")


@lru_cache
def get_settings() -> Settings:
    return Settings()
