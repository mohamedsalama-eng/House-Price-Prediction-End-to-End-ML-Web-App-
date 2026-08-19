"""
Pydantic schemas for house price prediction request and response.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, model_validator


class PredictionRequest(BaseModel):
    """Input payload matching the model's expected features."""
    location: str = Field(..., description="City slug, e.g. 'mumbai', 'pune'")
    locality: Optional[str] = Field(None, description="Locality / neighborhood name")
    location_raw: Optional[str] = Field(None, description="Full raw location or society string")
    transaction: str = Field(..., description="Transaction type, e.g. 'Resale', 'New Property'")
    furnishing: Optional[str] = Field(None, description="Furnishing status, e.g. 'Furnished', 'Semi-Furnished', 'Unfurnished'")
    facing: Optional[str] = Field(None, description="Facing direction, e.g. 'East', 'North'")
    overlooking: Optional[str] = Field(None, description="Overlooking views, e.g. 'Garden/Park', 'Main Road'")
    ownership: Optional[str] = Field(None, description="Ownership type, e.g. 'Freehold', 'Co-operative Society'")
    carpet_area: Optional[float] = Field(None, ge=0, description="Carpet area in sqft")
    super_area: Optional[float] = Field(None, ge=0, description="Super / built-up area in sqft")
    bathroom: float = Field(..., ge=0, description="Number of bathrooms")
    balcony: Optional[float] = Field(None, ge=0, description="Number of balconies")
    parking_count: Optional[float] = Field(None, ge=0, description="Number of parking spaces")
    floor_number: Optional[float] = Field(None, description="Floor number of the unit")
    building_height: Optional[float] = Field(None, ge=0, description="Total building height in floors")
    floor_ratio: Optional[float] = Field(None, description="floor_number / building_height")

    @model_validator(mode="after")
    def compute_floor_ratio(self) -> "PredictionRequest":
        """Auto-compute floor_ratio if not explicitly provided and floor_number/building_height are given."""
        if (
            self.floor_ratio is None
            and self.floor_number is not None
            and self.building_height is not None
            and self.building_height > 0
        ):
            self.floor_ratio = self.floor_number / self.building_height
        return self


class PredictionResponse(BaseModel):
    """Output schema returned by the prediction endpoint."""
    predicted_price: float = Field(..., description="Predicted price in INR")
    formatted_price: Optional[str] = Field(None, description="Formatted price in Indian notation (Lakh/Cr)")
