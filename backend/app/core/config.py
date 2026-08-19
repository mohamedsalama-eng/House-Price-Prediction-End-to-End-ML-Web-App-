"""
Application configuration using pydantic-settings.
Reads settings from environment variables or .env file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Root directory of backend (where .env and models/ are located)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "House Price Prediction API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""
    
    # Path to the trained pipeline (.pkl / .joblib)
    MODEL_PATH: str = str(BACKEND_DIR / "models" / "house_price.pkl")
    
    # CORS Origins
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://localhost:80"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return [v]

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
