"""
Preprocessing service to convert PredictionRequest payloads into a single-row DataFrame.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from app.schemas.prediction import PredictionRequest


FEATURE_COLUMNS = [
    "carpet_area",
    "super_area",
    "floor_number",
    "building_height",
    "floor_ratio",
    "parking_count",
    "furnishing",
    "bathroom",
    "balcony",
    "transaction",
    "facing",
    "ownership",
    "location",
    "locality",
    "overlooking",
    "location_raw",
]


def request_to_dataframe(req: PredictionRequest) -> pd.DataFrame:
    """
    Transform a PredictionRequest into a single-row pandas DataFrame
    matching the exact column order and types expected by the trained pipeline.
    """
    row = {
        "carpet_area": req.carpet_area,
        "super_area": req.super_area,
        "floor_number": req.floor_number,
        "building_height": req.building_height,
        "floor_ratio": req.floor_ratio,
        "parking_count": req.parking_count,
        "furnishing": req.furnishing,
        "bathroom": req.bathroom,
        "balcony": req.balcony,
        "transaction": req.transaction,
        "facing": req.facing,
        "ownership": req.ownership,
        "location": req.location.strip().lower() if req.location else None,
        "locality": req.locality.strip() if req.locality else None,
        "overlooking": req.overlooking.strip() if req.overlooking else None,
        "location_raw": req.location_raw.strip() if req.location_raw else None,
    }

    # Convert None to np.nan for scikit-learn imputers
    row = {k: (v if v is not None else np.nan) for k, v in row.items()}

    df = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    return df
