"""House Price Prediction - Part 2: Outlier handling, preprocessing, modeling, saving.

Run the notebook 01_eda_cleaning_split.ipynb first; it writes train_test_split.joblib.
"""

import sys
from pathlib import Path
import matplotlib
if 'IPython' not in sys.modules:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# pyrefly: ignore [missing-import]
import joblib
import numpy as np
import pandas as pd

# Load the split produced by the notebook
split_path = Path("train_test_split.joblib")
if not split_path.exists():
    split_path = Path(__file__).resolve().parent / "train_test_split.joblib"
X_train, X_test, y_train, y_test = joblib.load(split_path)



# ======================================================================
# ## 7. Target Variable (`y_train`) Outlier Handling
#
# Real-estate prices have extreme upper outliers. We analyze the `y_train`
# distribution, compute IQR capping bounds **strictly on `y_train`**, and
# clip both `y_train` and `y_test` using those same bounds.
# ======================================================================


from scipy.stats import skew

# 1. Inspect y_train before outlier capping
print(f"y_train Skewness (Before): {skew(y_train):.3f}")
print("y_train Summary Statistics (Before):")
print(y_train.describe())

fig, axes = plt.subplots(1, 2, figsize=(13, 3.8))
sns.histplot(y_train, kde=True, ax=axes[0], color='crimson')
axes[0].set_title('y_train Distribution (Before Outlier Capping)')
sns.boxplot(x=y_train, ax=axes[1], color='crimson')
axes[1].set_title('y_train Boxplot (Before Outlier Capping)')
plt.tight_layout()
plt.show()


# 2. Compute IQR capping bounds STRICTLY from y_train
y_q1 = y_train.quantile(0.25)
y_q3 = y_train.quantile(0.75)
y_iqr = y_q3 - y_q1
y_lower = y_q1 - 1.5 * y_iqr
y_upper = y_q3 + 1.5 * y_iqr

print(f"y_train Q1: {y_q1:.2f}, Q3: {y_q3:.2f}, IQR: {y_iqr:.2f}")
print(f"y Capping Bounds: [{y_lower:.2f}, {y_upper:.2f}]")

# Count how many values fall outside the bounds
outliers_train = ((y_train < y_lower) | (y_train > y_upper)).sum()
outliers_test = ((y_test < y_lower) | (y_test > y_upper)).sum()
print(f"y_train outliers: {outliers_train} ({outliers_train / len(y_train) * 100:.2f}%)")
print(f"y_test  outliers: {outliers_test} ({outliers_test / len(y_test) * 100:.2f}%)")

# 3. Apply capping using y_train-derived bounds to BOTH sets
y_train = y_train.clip(lower=y_lower, upper=y_upper)
y_test = y_test.clip(lower=y_lower, upper=y_upper)


# ======================================================================
# ## 8. Feature (`X_train`) Outlier Handling
#
# - **IQR-based capping**: compute Q1, Q3, IQR bounds **strictly on
#   `X_train`** for continuous numerical features, then apply the same
#   bounds to `X_test`.
# - **Threshold capping**: cap discrete counts (`bathroom` <= 5,
#   `balcony` <= 5, `parking_count` <= 3).
# ======================================================================


# 1. IQR capping for continuous features
iqr_cols = ['carpet_area', 'super_area', 'amount_in_rupees', 'floor_number', 'building_height', 'floor_ratio']

for col in iqr_cols:
    if col in X_train.columns:
        q1 = X_train[col].quantile(0.25)
        q3 = X_train[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        # Clip both X_train and X_test using X_train-derived bounds
        X_train[col] = X_train[col].clip(lower=lower, upper=upper)
        X_test[col] = X_test[col].clip(lower=lower, upper=upper)
        print(f"{col:20s}: Bound [{lower:.2f}, {upper:.2f}] learned from X_train")

# 2. Discrete threshold capping
X_train['bathroom'] = X_train['bathroom'].clip(upper=5)
X_test['bathroom'] = X_test['bathroom'].clip(upper=5)

X_train['balcony'] = X_train['balcony'].clip(upper=5)
X_test['balcony'] = X_test['balcony'].clip(upper=5)

X_train['parking_count'] = X_train['parking_count'].clip(upper=3)
X_test['parking_count'] = X_test['parking_count'].clip(upper=3)

print("\nFeature outlier handling complete!")


# ======================================================================
# ## 9. Re-Visualization (After Outlier Handling)
# ======================================================================


# Visualize capped continuous features in X_train
viz_numeric = [c for c in iqr_cols + ['bathroom', 'balcony', 'parking_count'] if c in X_train.columns]

for col in viz_numeric:
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.2))
    sns.histplot(X_train[col].dropna(), kde=True, ax=axes[0])
    axes[0].set_title(f'Train Distribution: {col} (Capped)')
    sns.boxplot(x=X_train[col].dropna(), ax=axes[1])
    axes[1].set_title(f'Train Boxplot: {col} (Capped)')
    plt.tight_layout()
    plt.show()


# Correlation heatmap of features in X_train, post-capping
plt.figure(figsize=(10, 8))
corr = X_train[viz_numeric].corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0)
plt.title('Correlation Heatmap (X_train Features Post-Capping)')
plt.tight_layout()
plt.show()


# ======================================================================
# ## 10. Preprocessing Pipeline (`ColumnTransformer`)
#
# Modular sub-pipelines handle each feature type cleanly, with all
# imputation/scaling/encoding fit only on `X_train` (via `Pipeline.fit`)
# to avoid leakage:
#
# - **Numeric features**: `SimpleImputer(strategy='median')` + `StandardScaler()`
# - **Ordinal features**: `SimpleImputer(strategy='most_frequent')` + `OrdinalEncoder()`
#   (`furnishing`, `bathroom`, `balcony`)
# - **Low-cardinality categorical**: `SimpleImputer(strategy='constant', fill_value='Missing')`
#   + `OneHotEncoder()` (`transaction`, `facing`, `ownership`)
# - **High-cardinality categorical**: `SimpleImputer(strategy='constant', fill_value='Missing')`
#   + `OrdinalEncoder()` (`location`, `locality`, `overlooking`, `society`, `location_raw`)
# ======================================================================


from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder

# 1. Feature groupings
num_cols = [c for c in ['carpet_area', 'super_area', 'amount_in_rupees', 'floor_number',
                         'building_height', 'floor_ratio', 'parking_count'] if c in X_train.columns]
ord_cols = [c for c in ['furnishing', 'bathroom', 'balcony'] if c in X_train.columns]
ohe_cols = [c for c in ['transaction', 'facing', 'ownership'] if c in X_train.columns]
high_cat_cols = [c for c in ['location', 'locality', 'overlooking', 'society', 'location_raw'] if c in X_train.columns]

print(f"Numeric features       ({len(num_cols)}): {num_cols}")
print(f"Ordinal features       ({len(ord_cols)}): {ord_cols}")
print(f"OneHot features        ({len(ohe_cols)}): {ohe_cols}")
print(f"High-cardinality       ({len(high_cat_cols)}): {high_cat_cols}")

# 2. Sub-pipelines
num_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

ord_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))
])

ohe_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
    ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
])

high_cat_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
    ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))
])

# 3. Assemble into a single ColumnTransformer
preprocessor = ColumnTransformer(
    transformers=[
        ('num', num_pipe, num_cols),
        ('ord', ord_pipe, ord_cols),
        ('ohe', ohe_pipe, ohe_cols),
        ('high_cat', high_cat_pipe, high_cat_cols)
    ],
    remainder='drop'
)

preprocessor


# ======================================================================
# ## 11. Model Training & Evaluation
#
# We evaluate four regression algorithms, each wrapped together with the
# `preprocessor` inside a single `Pipeline` so that preprocessing is fit
# only on training data for every model:
#
# 1. **Linear Regression** (parametric baseline)
# 2. **Ridge Regression** (L2-regularized linear model)
# 3. **Random Forest Regressor** (bagged decision trees)
# 4. **XGBoost Regressor** (gradient-boosted decision trees)
# ======================================================================


import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Define the candidate models
models = {
    'Linear Regression': LinearRegression(),
    'Ridge': Ridge(alpha=10.0),
    'Random Forest': RandomForestRegressor(
        n_estimators=150,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    ),
    'XGBoost': XGBRegressor(
        n_estimators=150,
        learning_rate=0.08,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
}

results = []
trained_pipelines = {}  # keep every fitted pipeline so we can save the best one later

for name, model in models.items():
    print(f"Training {name}...")
    full_pipe = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', model)
    ])

    # Fit strictly on train
    full_pipe.fit(X_train, y_train)
    trained_pipelines[name] = full_pipe

    # Predict on both sets
    y_pred_train = full_pipe.predict(X_train)
    y_pred_test = full_pipe.predict(X_test)

    # Metrics
    tr_r2 = r2_score(y_train, y_pred_train)
    te_r2 = r2_score(y_test, y_pred_test)
    tr_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    te_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    tr_mae = mean_absolute_error(y_train, y_pred_train)
    te_mae = mean_absolute_error(y_test, y_pred_test)

    results.append({
        'Model': name,
        'Train R2': round(tr_r2, 4),
        'Test R2': round(te_r2, 4),
        'Train RMSE': round(tr_rmse, 2),
        'Test RMSE': round(te_rmse, 2),
        'Train MAE': round(tr_mae, 2),
        'Test MAE': round(te_mae, 2)
    })

# Summary comparison table
comparison_df = pd.DataFrame(results)
print("\n" + "=" * 50)
print("            MODEL EVALUATION COMPARISON")
print("=" * 50)
print(comparison_df.to_string(index=False))



# ======================================================================
# ## 12. Save the Best Model
#
# We pick the model with the highest **Test R2** from `comparison_df`
# (guarding against overfitting rather than just picking the highest
# train score), then persist the *entire* fitted pipeline — preprocessing
# included — with `joblib`. Saving the whole pipeline means new raw data
# can be fed straight into `.predict()` later without repeating any of the
# cleaning/encoding steps by hand.
# ======================================================================


import joblib

# 1. Pick the best model by Test R2
best_row = comparison_df.loc[comparison_df['Test R2'].idxmax()]
best_model_name = best_row['Model']
best_pipeline = trained_pipelines[best_model_name]

print(f"Best model: {best_model_name}")
print(f"Test R2: {best_row['Test R2']}  |  Test RMSE: {best_row['Test RMSE']}  |  Test MAE: {best_row['Test MAE']}")

# 2. Save the full pipeline (preprocessing + model) to disk
model_path = f"best_model_{best_model_name.lower().replace(' ', '_')}.joblib"
joblib.dump(best_pipeline, model_path)
print(f"Saved pipeline to: {model_path}")

# Also ensure saved pipeline copy is in both model folder and root workspace
for target_dir in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent]:
    target_file = target_dir / model_path
    if target_file.resolve() != Path(model_path).resolve():
        joblib.dump(best_pipeline, target_file)
        print(f"Also saved pipeline copy to: {target_file}")



# 3. Sanity check: reload the saved pipeline and confirm predictions match
reloaded_pipeline = joblib.load(model_path)

original_preds = best_pipeline.predict(X_test)
reloaded_preds = reloaded_pipeline.predict(X_test)

assert np.allclose(original_preds, reloaded_preds), "Reloaded model predictions differ!"
print("Reloaded model predictions match the original — save verified.")


# ======================================================================
# ## 13. Summary & Key Takeaways
#
# 1. **Target & Feature Outlier Handling:**
#    - `y_train` price outliers were capped using IQR bounds computed
#      strictly on `y_train`.
#    - All feature outlier bounds were fitted strictly on `X_train` and
#      applied to `X_test`, with zero leakage.
# 2. **Modular `ColumnTransformer` Pipeline:**
#    - Numerical features median-imputed and scaled.
#    - Ordinal and categorical features encoded appropriately for their
#      cardinality.
# 3. **Model Performance Summary:**
#    - See `comparison_df` above for the full train/test R2, RMSE, and MAE
#      comparison across Linear Regression, Ridge, Random Forest, and
#      XGBoost.
#    - The best-performing model (by Test R2) was saved as a complete,
#      ready-to-use pipeline in step 12.
# ======================================================================
