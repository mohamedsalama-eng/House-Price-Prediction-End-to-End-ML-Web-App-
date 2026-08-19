"""
Data Cleaning and Feature Engineering Script
Splits sections 1-5 of EDA_cleaned.ipynb into a standalone pipeline.

Usage:
    python clean_data.py [--input house_prices.csv] [--output cleaned_house_prices.csv]
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Helper Functions for Column Cleaning & Feature Engineering
# ---------------------------------------------------------------------------
def extract_location_raw(title: str | float) -> str | float:
    """Pull the free-text location out of the listing title,
    e.g. '... Flat for sale in Thane' -> 'Thane'."""
    if pd.isna(title):
        return np.nan
    match = re.search(r"Flat for sale (?:in )?(.+)", str(title))
    if match:
        return match.group(1).strip()
    return np.nan


def apply_unit(n: float | None, u: str | None) -> float | None:
    """Convert a (number, unit) pair into a plain rupee amount."""
    if pd.isna(n) or pd.isna(u):
        return None
    if u == "lac":
        return n * 1e5
    elif u == "cr":
        return n * 1e7
    return None


def sqft_convert(s: str | float) -> float | None:
    """Parse a '<number> <unit>' area string and convert to sqft."""
    if pd.isna(s):
        return None

    s = str(s).strip()
    parts = s.split()
    if len(parts) != 2:
        return None

    num, unit = parts
    try:
        num = float(num)
    except ValueError:
        return None

    if unit == "sqyrd":
        return num * 9
    elif unit == "sqft":
        return num
    return None


def map_floor(label: str | float) -> float | None:
    """Map a floor label to a numeric floor index.
    Ground -> 0, Upper Basement -> -1, Lower Basement -> -2,
    otherwise parse the number directly."""
    if pd.isna(label):
        return None
    label = str(label).strip().lower()
    if label == "ground":
        return 0.0
    elif label == "upper basement":
        return -1.0
    elif label == "lower basement":
        return -2.0
    try:
        return float(label)
    except ValueError:
        return None


def clean_overlooking(val: str | float) -> str | float:
    """Remove 'Not Available' entries and sort remaining values so
    combinations like 'A, B' and 'B, A' are treated as identical."""
    if pd.isna(val):
        return val
    parts = [p.strip() for p in str(val).split(",")]
    parts = [p for p in parts if p != "Not Available"]
    if not parts:
        return np.nan
    return ", ".join(sorted(parts))


def get_locality(row: pd.Series) -> str | float:
    """Derive the neighborhood/locality from the raw title location,
    removing the society name prefix if present."""
    raw = row["location_raw"]
    soc = row["society"]
    if pd.isna(raw):
        return np.nan
    raw_str = str(raw)
    if pd.notna(soc) and raw_str.lower().startswith(str(soc).lower()):
        return raw_str[len(str(soc)):].strip()
    return raw_str  # no society -> raw text IS the locality


def parse_area(val: str | float) -> float:
    """Parse a '<number> <unit>' super-area string and convert to sqft."""
    if pd.isna(val):
        return np.nan
    val_str = str(val).replace(",", "").strip()
    match = re.match(r"([\d.]+)\s*(sqft|sqyrd)", val_str)
    if match:
        num, unit = match.groups()
        num = float(num)
        return num * 9 if unit == "sqyrd" else num
    return np.nan


# ---------------------------------------------------------------------------
# Main Cleaning Pipeline
# ---------------------------------------------------------------------------
def clean_dataset(input_path: str | Path) -> pd.DataFrame:
    """Load raw dataset and apply all column-by-column cleaning and feature engineering."""
    print(f"Loading raw dataset from: {input_path}")
    df = pd.read_csv(input_path)
    print(f"Initial raw shape: {df.shape}")

    # 1. Drop useless columns & standardize column names
    print("Dropping useless columns (Index, Dimensions, Plot Area)...")
    df = df.drop(columns=["Index", "Dimensions", "Plot Area"], errors="ignore")
    df.columns = df.columns.str.replace(" ", "_").str.lower()

    # 2. 4.1 `title` -> extract `location_raw`
    print("Extracting location_raw from title...")
    df["location_raw"] = df["title"].apply(extract_location_raw)

    # 3. 4.2 `description` -> drop rows with missing description, then drop column
    print("Filtering missing description and dropping description column...")
    df = df.dropna(subset=["description"])
    df = df.drop(columns=["description"], errors="ignore")

    # 4. 4.3 `amount(in_rupees)` -> parse numeric amount and convert lac/cr
    print("Parsing amount(in_rupees)...")
    if "amount(in_rupees)" in df.columns:
        s = df["amount(in_rupees)"].astype(str).str.strip().str.lower()
        unit = s.str.extract(r"(lac|cr)", expand=False)
        number = s.str.extract(r"([\d.]+)", expand=False)
        number = pd.to_numeric(number, errors="coerce")
        df["amount_in_rupees"] = [apply_unit(n, u) for n, u in zip(number, unit)]
        df = df.drop(columns=["amount(in_rupees)"], errors="ignore")

    # 5. 4.4 `location`
    if "location" in df.columns:
        df["location"] = df["location"].astype(str).str.strip().str.lower()

    # 6. 4.5 `carpet_area` -> convert to sqft
    print("Standardizing carpet_area...")
    df["carpet_area"] = df["carpet_area"].apply(sqft_convert)

    # 7. 4.6 `status` -> drop rows with missing status, then drop column
    print("Filtering missing status and dropping status column...")
    df = df.dropna(subset=["status"])
    df = df.drop(columns=["status"], errors="ignore")

    # 8. 4.7 `floor` -> floor_number, building_height, floor_ratio
    print("Extracting floor_number, building_height, and floor_ratio...")
    if "floor" in df.columns:
        floor_label = df["floor"].astype(str).str.extract(r"^(.*?)(?:\s+out of\s+(\d+))?$")
        df["floor_number"] = floor_label[0].apply(map_floor)
        df["building_height"] = pd.to_numeric(floor_label[1], errors="coerce")
        df["floor_ratio"] = df["floor_number"] / df["building_height"]
        df = df.drop(columns=["floor"], errors="ignore")

    # 9. 4.8 `transaction` -> drop missing
    print("Filtering missing transaction...")
    df = df.dropna(subset=["transaction"])

    # 10. 4.11 `overlooking` -> clean and sort multi-values
    print("Cleaning overlooking values...")
    df["overlooking"] = df["overlooking"].apply(clean_overlooking)

    # 11. 4.12 `society` -> derive `locality`
    print("Deriving locality from society and location_raw...")
    df["locality"] = df.apply(get_locality, axis=1)

    # 12. 4.13 `bathroom` -> clean strings and convert to numeric
    print("Cleaning bathroom counts...")
    if "bathroom" in df.columns:
        df["bathroom"] = df["bathroom"].astype(str).str.replace("> ", "", regex=False)
        df["bathroom"] = pd.to_numeric(df["bathroom"], errors="coerce")
        df = df.dropna(subset=["bathroom"])

    # 13. 4.14 `balcony` -> clean strings and convert to numeric
    print("Cleaning balcony counts...")
    if "balcony" in df.columns:
        df["balcony"] = df["balcony"].astype(str).str.replace("> ", "", regex=False)
        df["balcony"] = pd.to_numeric(df["balcony"], errors="coerce")

    # 14. 4.15 `car_parking` -> parking_count & parking_type, cap > 10 to NaN
    print("Extracting parking_count and parking_type...")
    if "car_parking" in df.columns:
        extracted = (
            df["car_parking"]
            .astype(str)
            .str.strip(",")
            .str.extract(r"(\d+)\s*(Open|Covered)")
        )
        df["parking_count"] = pd.to_numeric(extracted[0], errors="coerce")
        df["parking_type"] = extracted[1]
        df.loc[df["parking_count"] > 10, "parking_count"] = np.nan

    # 15. 4.17 `super_area` -> parse to sqft
    print("Parsing super_area to sqft...")
    df["super_area"] = df["super_area"].apply(parse_area)

    print(f"Cleaning complete. Final cleaned shape: {df.shape}")
    return df


def main():
    parser = argparse.ArgumentParser(description="Clean raw house price dataset and engineer features.")
    parser.add_argument(
        "--input",
        type=str,
        default="house_prices.csv",
        help="Path to raw input CSV file (default: house_prices.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="cleaned_house_prices.csv",
        help="Path to output cleaned CSV file (default: cleaned_house_prices.csv)",
    )
    args = parser.parse_args()

    cleaned_df = clean_dataset(args.input)

    print(f"Saving cleaned dataset to: {args.output}")
    cleaned_df.to_csv(args.output, index=False)
    print("Done! Cleaned dataset successfully saved.")


if __name__ == "__main__":
    main()
