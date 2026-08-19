"""
Inference service to load model artifacts and execute predictions.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional
import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ModelService:
    def __init__(self):
        self.model: Optional[Any] = None
        self.model_path: Optional[str] = None

    def load_model(self, path: str | Path) -> None:
        """Load the pipeline from disk."""
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Model file not found at: {path}")

        logger.info(f"Loading ML model from {path_obj.resolve()} ...")
        self.model = joblib.load(path_obj)
        self.model_path = str(path_obj)
        logger.info("Model pipeline loaded successfully.")

    def is_loaded(self) -> bool:
        return self.model is not None

    def predict(self, df: pd.DataFrame) -> float:
        """Run inference on the provided DataFrame."""
        if not self.is_loaded():
            raise RuntimeError("Model is not loaded. Call load_model() first.")

        raw_pred = self.model.predict(df)
        pred_value = float(raw_pred[0])
        # Ensure non-negative price prediction
        return max(0.0, pred_value)


# Global singleton instance
model_service = ModelService()


def format_indian_price(price: float) -> str:
    """Format numeric price into Indian currency terms (Lakh / Crore)."""
    if price < 0:
        return f"-{format_indian_price(-price)}"

    if price >= 1e7:
        cr = price / 1e7
        return f"₹{cr:,.2f} Cr"
    elif price >= 1e5:
        lk = price / 1e5
        return f"₹{lk:,.2f} Lakh"
    else:
        return f"₹{price:,.0f}"
