"""
Centralized application configuration.
Reads from environment variables / .env file using pydantic-settings.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "GuardianOps AI"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- MongoDB ---
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "guardianops_ai"

    # --- Mock / Simulation ---
    USE_MOCK_DATA: bool = True
    MOCK_SERVICE_COUNT: int = 14
    SIMULATION_TICK_SECONDS: int = 5

    # --- LLM (optional) ---
    USE_LLM: bool = False
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # --- Auth ---
    JWT_SECRET: str = "change-this-secret-in-production-guardianops-ai"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALLOW_REGISTRATION: bool = True  # auto-flips off after the first (only) user registers

    # --- Real / Live Monitoring ---
    LIVE_MONITORING: bool = True  # collect real psutil metrics + watch real app logs
    LOGS_DIR: str = "./sample_apps/logs"
    SCHEDULER_INTERVAL_SECONDS: int = 30

    # --- Guardian Agent telemetry ingestion ---
    # Standalone Guardian Agents (see /guardian-agent) authenticate with this
    # shared secret via the X-Agent-Api-Key header — distinct from user JWTs
    # since an agent is a process, not a logged-in operator. Leave blank to
    # disable telemetry ingestion entirely.
    AGENT_API_KEY: str = ""
    AGENT_OFFLINE_AFTER_SECONDS: int = 90  # agent considered offline if no telemetry in this window

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
