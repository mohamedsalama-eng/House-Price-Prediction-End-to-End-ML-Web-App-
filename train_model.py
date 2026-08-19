"""
Model Training and Evaluation Pipeline Script
Loads the cleaned dataset, handles train/test splitting, outlier capping,
ColumnTransformer preprocessing, regression model training & evaluation,
and saves the best model pipeline with joblib.

Usage:
    python train_model.py [--input cleaned_house_prices.csv] [--output-model-prefix best_model]
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import skew
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from xgboost import XGBRegressor


# ---------------------------------------------------------------------------
# Pipeline Builder
# ---------------------------------------------------------------------------
def build_preprocessor(X_train: pd.DataFrame) -> tuple[ColumnTransformer, dict[str, list[str]]]:
    """Construct modular ColumnTransformer for numerical, ordinal, one-hot, and high-cardinality features."""
    num_cols = [
        c
        for c in [
            "carpet_area",
            "super_area",
            "amount_in_rupees",
            "floor_number",
            "building_height",
            "floor_ratio",
            "parking_count",
        ]
        if c in X_train.columns
    ]
    ord_cols = [c for c in ["furnishing", "bathroom", "balcony"] if c in X_train.columns]
    ohe_cols = [c for c in ["transaction", "facing", "ownership"] if c in X_train.columns]
    high_cat_cols = [
        c
        for c in ["location", "locality", "overlooking", "society", "location_raw"]
        if c in X_train.columns
    ]

    print("\nFeature groupings identified:")
    print(f"  Numeric features       ({len(num_cols)}): {num_cols}")
    print(f"  Ordinal features       ({len(ord_cols)}): {ord_cols}")
    print(f"  OneHot features        ({len(ohe_cols)}): {ohe_cols}")
    print(f"  High-cardinality       ({len(high_cat_cols)}): {high_cat_cols}")

    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    ord_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])

    ohe_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    high_cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
        ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipe, num_cols),
            ("ord", ord_pipe, ord_cols),
            ("ohe", ohe_pipe, ohe_cols),
            ("high_cat", high_cat_pipe, high_cat_cols),
        ],
        remainder="drop",
    )

    column_groups = {
        "num": num_cols,
        "ord": ord_cols,
        "ohe": ohe_cols,
        "high_cat": high_cat_cols,
    }

    return preprocessor, column_groups


# ---------------------------------------------------------------------------
# Outlier Handling Functions
# ---------------------------------------------------------------------------
def handle_target_outliers(
    y_train: pd.Series, y_test: pd.Series
) -> tuple[pd.Series, pd.Series, tuple[float, float]]:
    """Compute IQR bounds strictly from y_train and clip both train and test target variables."""
    print("\n--- Target Variable (y_train) Outlier Capping ---")
    print(f"y_train Skewness (Before): {skew(y_train):.3f}")

    y_q1 = y_train.quantile(0.25)
    y_q3 = y_train.quantile(0.75)
    y_iqr = y_q3 - y_q1
    y_lower = y_q1 - 1.5 * y_iqr
    y_upper = y_q3 + 1.5 * y_iqr

    print(f"y_train Q1: {y_q1:.2f}, Q3: {y_q3:.2f}, IQR: {y_iqr:.2f}")
    print(f"y Capping Bounds: [{y_lower:.2f}, {y_upper:.2f}]")

    outliers_train = ((y_train < y_lower) | (y_train > y_upper)).sum()
    outliers_test = ((y_test < y_lower) | (y_test > y_upper)).sum()
    print(f"y_train outliers: {outliers_train} ({outliers_train / len(y_train) * 100:.2f}%)")
    print(f"y_test  outliers: {outliers_test} ({outliers_test / len(y_test) * 100:.2f}%)")

    y_train_capped = y_train.clip(lower=y_lower, upper=y_upper)
    y_test_capped = y_test.clip(lower=y_lower, upper=y_upper)

    return y_train_capped, y_test_capped, (y_lower, y_upper)


def handle_feature_outliers(
    X_train: pd.DataFrame, X_test: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute IQR bounds strictly on X_train for continuous columns, and apply discrete caps."""
    print("\n--- Feature Outlier Capping ---")
    X_train = X_train.copy()
    X_test = X_test.copy()

    iqr_cols = [
        "carpet_area",
        "super_area",
        "amount_in_rupees",
        "floor_number",
        "building_height",
        "floor_ratio",
    ]

    for col in iqr_cols:
        if col in X_train.columns:
            q1 = X_train[col].quantile(0.25)
            q3 = X_train[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            X_train[col] = X_train[col].clip(lower=lower, upper=upper)
            X_test[col] = X_test[col].clip(lower=lower, upper=upper)
            print(f"  {col:20s}: Bound [{lower:.2f}, {upper:.2f}] learned from X_train")

    # Discrete threshold capping
    if "bathroom" in X_train.columns:
        X_train["bathroom"] = X_train["bathroom"].clip(upper=5)
        X_test["bathroom"] = X_test["bathroom"].clip(upper=5)

    if "balcony" in X_train.columns:
        X_train["balcony"] = X_train["balcony"].clip(upper=5)
        X_test["balcony"] = X_test["balcony"].clip(upper=5)

    if "parking_count" in X_train.columns:
        X_train["parking_count"] = X_train["parking_count"].clip(upper=3)
        X_test["parking_count"] = X_test["parking_count"].clip(upper=3)

    print("Feature outlier handling complete!")
    return X_train, X_test


# ---------------------------------------------------------------------------
# Training and Evaluation Pipeline
# ---------------------------------------------------------------------------
def run_training_pipeline(cleaned_data_path: str | Path, model_prefix: str = "best_model"):
    """Execute complete split, outlier capping, preprocessing, training, and model export."""
    print(f"Loading cleaned dataset from: {cleaned_data_path}")
    df = pd.read_csv(cleaned_data_path)
    print(f"Loaded dataset shape: {df.shape}")

    # 1. Drop rows missing the target variable
    target_col = "price_(in_rupees)"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset!")

    df_clean = df.dropna(subset=[target_col]).copy()

    # 2. Drop redundant/raw columns not used by the model
    drop_cols = ["car_parking", "parking_type", "title", "amount_in_rupees", "society"]
    df_clean = df_clean.drop(columns=drop_cols, errors="ignore")

    # 3. Separate features (X) and target (y)
    X = df_clean.drop(columns=[target_col])
    y = df_clean[target_col]

    # 4. Split 80% train / 20% test (fixed seed=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"\nDataset split complete:")
    print(f"  X_train: {X_train.shape}, X_test: {X_test.shape}")
    print(f"  y_train: {y_train.shape}, y_test: {y_test.shape}")

    # 5. Target outlier capping
    y_train, y_test, _ = handle_target_outliers(y_train, y_test)

    # 6. Feature outlier capping
    X_train, X_test = handle_feature_outliers(X_train, X_test)

    # 7. Build ColumnTransformer preprocessor
    preprocessor, _ = build_preprocessor(X_train)

    # 8. Define Candidate Models
    models = {
        "Linear Regression": LinearRegression(),
        "Ridge": Ridge(alpha=10.0),
        "Random Forest": RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
        "XGBoost": XGBRegressor(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
        ),
    }

    results = []
    trained_pipelines: dict[str, Pipeline] = {}

    print("\n" + "=" * 60)
    print("                 TRAINING & EVALUATION")
    print("=" * 60)

    for name, model in models.items():
        print(f"\nTraining [{name}]...")
        full_pipe = Pipeline([
            ("preprocessor", preprocessor),
            ("regressor", model),
        ])

        # Fit strictly on train
        full_pipe.fit(X_train, y_train)
        trained_pipelines[name] = full_pipe

        # Predictions
        y_pred_train = full_pipe.predict(X_train)
        y_pred_test = full_pipe.predict(X_test)

        # Metrics
        tr_r2 = r2_score(y_train, y_pred_train)
        te_r2 = r2_score(y_test, y_pred_test)
        tr_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        te_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        tr_mae = mean_absolute_error(y_train, y_pred_train)
        te_mae = mean_absolute_error(y_test, y_pred_test)

        print(f"  -> Train R2: {tr_r2:.4f} | Test R2: {te_r2:.4f}")
        print(f"  -> Test RMSE: {te_rmse:,.2f} | Test MAE: {te_mae:,.2f}")

        results.append({
            "Model": name,
            "Train R2": round(tr_r2, 4),
            "Test R2": round(te_r2, 4),
            "Train RMSE": round(tr_rmse, 2),
            "Test RMSE": round(te_rmse, 2),
            "Train MAE": round(tr_mae, 2),
            "Test MAE": round(te_mae, 2),
        })

    comparison_df = pd.DataFrame(results)
    print("\n" + "=" * 60)
    print("            MODEL EVALUATION COMPARISON TABLE")
    print("=" * 60)
    print(comparison_df.to_string(index=False))

    # 9. Select best model by Test R2
    best_row = comparison_df.loc[comparison_df["Test R2"].idxmax()]
    best_model_name = best_row["Model"]
    best_pipeline = trained_pipelines[best_model_name]

    print("\n" + "-" * 60)
    print(f"BEST MODEL SELECTED: {best_model_name}")
    print(f"  Test R2:   {best_row['Test R2']}")
    print(f"  Test RMSE: {best_row['Test RMSE']}")
    print(f"  Test MAE:  {best_row['Test MAE']}")
    print("-" * 60)

    # 10. Save the full pipeline (preprocessor + model) to disk
    slug = best_model_name.lower().replace(" ", "_")
    model_filename = f"{model_prefix}_{slug}.joblib"
    joblib.dump(best_pipeline, model_filename)
    print(f"Successfully saved fitted pipeline to: {model_filename}")

    # 11. Sanity check reload
    print("\nPerforming sanity check verification on saved pipeline...")
    reloaded_pipeline = joblib.load(model_filename)
    original_preds = best_pipeline.predict(X_test)
    reloaded_preds = reloaded_pipeline.predict(X_test)

    assert np.allclose(original_preds, reloaded_preds), "Reloaded model predictions differ!"
    print("Sanity check passed: Reloaded model predictions match exactly.")

    return comparison_df, model_filename


def main():
    parser = argparse.ArgumentParser(description="Train house price prediction models on cleaned data.")
    parser.add_argument(
        "--input",
        type=str,
        default="cleaned_house_prices.csv",
        help="Path to cleaned CSV file (default: cleaned_house_prices.csv)",
    )
    parser.add_argument(
        "--output-model-prefix",
        type=str,
        default="best_model",
        help="Prefix for saved joblib model file (default: best_model)",
    )
    args = parser.parse_args()

    run_training_pipeline(args.input, args.output_model_prefix)


if __name__ == "__main__":
    main()
