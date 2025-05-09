"""
General settings for the application.
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", "Bro")
    DESCRIPTION: str = os.getenv("DESCRIPTION", "Financial Assistant")

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "your_api_key_here")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"
