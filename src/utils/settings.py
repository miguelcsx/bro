"""
General settings for the application.
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", "Bro")
    DESCRIPTION: str = os.getenv("DESCRIPTION", "Financial Assistant")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"
