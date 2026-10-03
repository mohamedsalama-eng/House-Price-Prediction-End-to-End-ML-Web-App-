"""
House Price Prediction API
Serves a trained scikit-learn Pipeline (RandomForest) via FastAPI.
"""

from __future__ import annotations

import os
import math
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Pydantic request / response schemas
# ---------------------------------------------------------------------------
class PredictionRequest(BaseModel):
    """Raw feature values – mirrors the columns the pipeline was trained on."""

    location: str = Field(..., description="City slug, e.g. 'mumbai', 'pune'")
    locality: Optional[str] = Field(None, description="Locality / neighbourhood")
    location_raw: Optional[str] = Field(None, description="Full raw location string")
    transaction: str = Field(..., description="'Resale', 'New Property', or 'Other'")
    furnishing: Optional[str] = Field(None, description="'Furnished', 'Semi-Furnished', 'Unfurnished'")
    facing: Optional[str] = Field(None, description="'East', 'West', 'North', 'South', etc.")
    overlooking: Optional[str] = Field(None, description="'Garden/Park', 'Main Road', 'Pool', etc.")
    ownership: Optional[str] = Field(None, description="'Freehold', 'Co-operative Society', etc.")
    carpet_area: Optional[float] = Field(None, ge=0, description="Carpet area in sqft")
    super_area: Optional[float] = Field(None, ge=0, description="Super / built-up area in sqft")
    bathroom: float = Field(..., ge=0, description="Number of bathrooms")
    balcony: Optional[float] = Field(None, ge=0, description="Number of balconies")
    parking_count: Optional[float] = Field(None, ge=0, description="Number of parking spots")
    floor_number: Optional[float] = Field(None, ge=0, description="Floor number of the unit")
    building_height: Optional[float] = Field(None, ge=0, description="Total floors in the building")
    floor_ratio: Optional[float] = Field(None, description="floor_number / building_height")

    @model_validator(mode="after")
    def compute_floor_ratio(self) -> "PredictionRequest":
        """Auto-compute floor_ratio when both floor_number and building_height are present."""
        if (
            self.floor_ratio is None
            and self.floor_number is not None
            and self.building_height is not None
            and self.building_height > 0
        ):
            self.floor_ratio = self.floor_number / self.building_height
        return self


class PredictionResponse(BaseModel):
    predicted_price: float
    formatted_price: str


# ---------------------------------------------------------------------------
# Column order expected by the trained pipeline
# ---------------------------------------------------------------------------
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

# Known categories extracted from the trained encoders — served to the frontend
KNOWN_LOCATIONS = [
    "agra", "ahmadnagar", "ahmedabad", "allahabad", "aurangabad", "badlapur",
    "bangalore", "belgaum", "bhiwadi", "bhiwandi", "bhopal", "bhubaneswar",
    "chandigarh", "chennai", "coimbatore", "dehradun", "durgapur", "ernakulam",
    "faridabad", "ghaziabad", "goa", "greater-noida", "guntur", "gurgaon",
    "guwahati", "gwalior", "haridwar", "hyderabad", "indore", "jabalpur",
    "jaipur", "jamshedpur", "jodhpur", "kalyan", "kanpur", "kochi", "kolkata",
    "kozhikode", "lucknow", "ludhiana", "madurai", "mangalore", "mohali",
    "mumbai", "mysore", "nagpur", "nashik", "navi-mumbai", "navsari", "nellore",
    "new-delhi", "noida", "palakkad", "palghar", "panchkula", "patna",
    "pondicherry", "pune", "raipur", "rajahmundry", "ranchi", "satara", "shimla",
    "siliguri", "solapur", "sonipat", "surat", "thane", "thrissur", "tirupati",
    "trichy", "trivandrum", "udaipur", "udupi", "vadodara", "vapi", "varanasi",
    "vijayawada", "visakhapatnam", "vrindavan", "zirakpur",
]

KNOWN_CATEGORIES = {
    "transaction": ["Resale", "New Property", "Other"],
    "furnishing": ["Furnished", "Semi-Furnished", "Unfurnished"],
    "facing": [
        "East", "West", "North", "South",
        "North - East", "North - West", "South - East", "South -West",
    ],
    "overlooking": [
        "Garden/Park", "Main Road", "Pool",
        "Garden/Park, Main Road", "Garden/Park, Pool",
        "Garden/Park, Main Road, Pool", "Main Road, Pool",
    ],
    "ownership": [
        "Freehold", "Co-operative Society", "Leasehold", "Power Of Attorney",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def format_indian_price(price: float) -> str:
    """Format a number in the Indian numbering system (lakhs / crores)."""
    if price < 0:
        return f"-{format_indian_price(-price)}"

    abs_price = abs(price)
    if abs_price >= 1e7:
        cr = abs_price / 1e7
        return f"₹{cr:,.2f} Cr"
    elif abs_price >= 1e5:
        lk = abs_price / 1e5
        return f"₹{lk:,.2f} Lakh"
    else:
        return f"₹{abs_price:,.0f}"


def build_dataframe(req: PredictionRequest) -> pd.DataFrame:
    """Convert a PredictionRequest into a single-row DataFrame with the correct column order."""
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
        "location": req.location,
        "locality": req.locality,
        "overlooking": req.overlooking,
        "location_raw": req.location_raw,
    }

    # Replace Python None with np.nan so sklearn imputers handle them
    row = {k: (v if v is not None else np.nan) for k, v in row.items()}

    df = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    return df


# ---------------------------------------------------------------------------
# Application lifespan – load model once
# ---------------------------------------------------------------------------
MODEL = None

def _resolve_model_path() -> str:
    env_path = os.environ.get("MODEL_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    root_dir = Path(__file__).resolve().parent.parent
    for candidate in [
        root_dir / "best_model_random_forest.joblib",
        root_dir / "model" / "best_model_random_forest.joblib",
    ]:
        if candidate.exists():
            return str(candidate)
    return str(root_dir / "best_model_random_forest.joblib")

MODEL_PATH = _resolve_model_path()



@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL
    print(f"Loading model from {MODEL_PATH} ...")
    MODEL = joblib.load(MODEL_PATH)
    print("Model loaded successfully!")
    yield
    MODEL = None
    print("Model unloaded.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="House Price Predictor",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend
FRONTEND_PATH = Path(__file__).resolve().parent.parent / "frontend" / "index.html"


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse(str(FRONTEND_PATH), media_type="text/html")


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": MODEL is not None}


@app.get("/categories")
async def categories():
    """Return known category options so the frontend can populate dropdowns."""
    return {
        "locations": KNOWN_LOCATIONS,
        **KNOWN_CATEGORIES,
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(req: PredictionRequest):
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    try:
        df = build_dataframe(req)
        prediction = MODEL.predict(df)[0]

        # Clamp negative predictions to 0
        prediction = max(0.0, float(prediction))

        return PredictionResponse(
            predicted_price=round(prediction, 2),
            formatted_price=format_indian_price(prediction),
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Prediction failed: {exc}")
