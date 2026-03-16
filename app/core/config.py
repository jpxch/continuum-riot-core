from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    STATIC_ROOT: str = Field(
        default="/var/lib/continuum/ddragon",
        description="Root directory for DDragon static assets",
    )

    DEFAULT_LOCALE: str = Field(
        default="en_US",
        description="Primary locale for static ingestion",
    )

    # Service
    ENV: str = "dev"
    SERVICE_NAME: str = "continuum-riot-core"

    # API
    HOST: str = "192.168.0.74"
    PORT: int = 8000

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Riot + DDragon
    RIOT_API_KEY: str
    DDDRAGON_BASE_URL: str = "https://ddragon.leagueoflegends.com"
    DDDRAGON_DATA_DIR: str = "./data/ddragon"

    PATCH_POLL_INTERVAL_SECONDS: int = 3600

    ENABLE_PATCH_POLLER: bool = True

settings = Settings()