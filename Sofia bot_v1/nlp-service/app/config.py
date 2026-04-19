from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    nlp_api_port: int = 8000
    
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "sofia_burnout")
    postgres_user: str = os.getenv("POSTGRES_USER", "sofia_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "sofia_password")
    
    database_url: str = ""
    
    model_name: str = "cointegrated/rubert-tiny2"
    hf_token: str = os.getenv("HF_TOKEN", "")
    device: str = "cpu"
    
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
