/**
 * TypeScript interfaces mirroring the backend Prediction schemas.
 */

export interface PredictionRequest {
  location: string;
  locality?: string | null;
  location_raw?: string | null;
  transaction: string;
  furnishing?: string | null;
  facing?: string | null;
  overlooking?: string | null;
  ownership?: string | null;
  carpet_area?: number | null;
  super_area?: number | null;
  bathroom: number;
  balcony?: number | null;
  parking_count?: number | null;
  floor_number?: number | null;
  building_height?: number | null;
  floor_ratio?: number | null;
}

export interface PredictionResponse {
  predicted_price: number;
  formatted_price?: string;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
}
