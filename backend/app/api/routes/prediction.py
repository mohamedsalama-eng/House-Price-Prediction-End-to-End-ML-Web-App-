"""
Prediction and health router endpoints.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.preprocessing import request_to_dataframe
from app.services.inference import model_service, format_indian_price

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prediction"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    """Health check endpoint confirming service status and model readiness."""
    return {
        "status": "ok",
        "model_loaded": model_service.is_loaded(),
    }


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict house price",
)
async def predict(req: PredictionRequest):
    """
    Accept property features, transform into DataFrame, and run pipeline inference.
    """
    if not model_service.is_loaded():
        logger.error("Predict called before model was loaded.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded or unavailable.",
        )

    try:
        df = request_to_dataframe(req)
        price = model_service.predict(df)
        formatted = format_indian_price(price)

        return PredictionResponse(
            predicted_price=round(price, 2),
            formatted_price=formatted,
        )
    except Exception as exc:
        logger.exception(f"Prediction error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Inference failed: {str(exc)}",
        )
