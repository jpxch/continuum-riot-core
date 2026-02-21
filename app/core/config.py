from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service
    ENV: str = "dev"
    SERVICE_NAME: str = "continuum-riot-core"

    # API
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Riot + DDragon
    RIOT_API_KEY: str
    DDDRAGON_BASE_URL: str = "https://ddragon.leagueoflegends.com"
    DDDRAGON_DATA_DIR: str = "./data/ddragon"

settings = Settings()