"""
Main FastAPI application entry point.
Configures CORS, registers lifespan context for model loading, and includes routes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.core.config import settings
from app.utils.logging_config import setup_logging
from app.services.inference import model_service
from app.api.routes.prediction import router as prediction_router

setup_logging()
logger = logging.getLogger("app.main")

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to load the ML model on startup and cleanup on shutdown."""
    logger.info("Initializing application and loading model artifact...")
    try:
        model_service.load_model(settings.MODEL_PATH)
    except Exception as exc:
        logger.error(f"Failed to load model from {settings.MODEL_PATH}: {exc}")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the web UI directly on GET /
@app.get("/", include_in_schema=False)
async def serve_index():
    if STATIC_INDEX.exists():
        return FileResponse(str(STATIC_INDEX), media_type="text/html")
    return {"message": "House Price Prediction API", "docs": "/docs"}

# Register prediction routes
app.include_router(prediction_router, prefix=settings.API_V1_STR)
