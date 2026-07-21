"""Configuration settings for Cinematic-G backend."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    omdb_api_key: str
    secret_key: str = "your-secret-key-change-in-production"

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "movies"

    # API Settings
    api_timeout: int = 30
    max_movies_fetch: int = 500  # Limit for ETL pipeline

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
