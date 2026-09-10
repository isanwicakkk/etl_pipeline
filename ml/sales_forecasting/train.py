import os
import sys
import joblib
import numpy as np
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    HistGradientBoostingRegressor
)

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error
)


# ==========================================
# PROJECT PATH
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from ml.sales_forecasting.features import (
    load_forecasting_data,
    clean_forecasting_data,
    create_daily_revenue,
    create_forecasting_features,
    get_feature_columns
)


# ==========================================
# PROJECT CONFIG
# ==========================================

MODEL_DIR = BASE_DIR / "ml" / "sales_forecasting" / "models"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# START TRAINING
# ==========================================

print("=" * 60)
print("SALES FORECASTING TRAINING")
print("=" * 60)


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

print("\nLoading environment...")

load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

required_vars = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME
}

missing_vars = [
    key
    for key, value in required_vars.items()
    if not value
]

if missing_vars:
    raise ValueError(
        f"Environment variable belum ditemukan: {missing_vars}"
    )

print("Environment loaded successfully")


# ==========================================
# DATABASE CONNECTION
# ==========================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("\nConnecting to database...")

engine = create_engine(DATABASE_URL)

print("Database connection created")


# ==========================================
# LOAD DATA
# ==========================================

print("\nLoading sales data...")

df = load_forecasting_data(engine)

print(f"Total transaction rows: {len(df):,}")

if df.empty:
    raise ValueError("Data dari database kosong.")


# ==========================================
# CLEAN DATA
# ==========================================

print("\nCleaning data...")

df = clean_forecasting_data(df)

print(f"Rows after cleaning: {len(df):,}")

if df.empty:
    raise ValueError("Data kosong setelah cleaning.")


# ==========================================
# CREATE DAILY REVENUE
# ==========================================

print("\nCreating daily revenue...")

daily_df = create_daily_revenue(df)

if len(daily_df) < 100:
    raise ValueError(
        "Data historis terlalu sedikit untuk forecasting."
    )

print(f"Total days: {len(daily_df):,}")

print(
    f"Date range: "
    f"{daily_df['date'].min().date()} "
    f"until "
    f"{daily_df['date'].max().date()}"
)

zero_days = (
    daily_df["revenue"] <= 0
).sum()

print(f"Days with zero revenue: {zero_days:,}")


# ==========================================
# FEATURE ENGINEERING
# ==========================================

print("\nCreating forecasting features...")

forecast_df = create_forecasting_features(
    daily_df
)

forecast_df = (
    forecast_df
    .replace([np.inf, -np.inf], np.nan)
    .dropna()
    .reset_index(drop=True)
)

print(
    f"Rows after feature engineering: "
    f"{len(forecast_df):,}"
)


# ==========================================
# FEATURE VALIDATION
# ==========================================

feature_columns = get_feature_columns()

missing_features = [
    column
    for column in feature_columns
    if column not in forecast_df.columns
]

if missing_features:
    raise ValueError(
        f"Feature tidak ditemukan: {missing_features}"
    )

X = forecast_df[
    feature_columns
].copy()

y = forecast_df[
    "revenue"
].copy()

print(f"Total features: {len(feature_columns)}")


# ==========================================
# TIME SERIES SPLIT
# ==========================================

split_index = int(
    len(forecast_df) * 0.8
)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

print("\nTrain/Test Split")

print(f"Training samples: {len(X_train):,}")
print(f"Testing samples: {len(X_test):,}")


# ==========================================
# MODEL CONFIGURATION
# ==========================================

models = {

    "Random Forest": RandomForestRegressor(
        n_estimators=600,
        max_depth=12,
        min_samples_split=3,
        min_samples_leaf=2,
        max_features=0.8,
        random_state=42,
        n_jobs=-1
    ),

    "Extra Trees": ExtraTreesRegressor(
        n_estimators=600,
        max_depth=16,
        min_samples_split=3,
        min_samples_leaf=2,
        max_features=0.9,
        random_state=42,
        n_jobs=-1
    ),

    "Hist Gradient Boosting": HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_iter=300,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        random_state=42
    )
}


# ==========================================
# MODEL COMPARISON
# ==========================================

print("\n" + "=" * 60)
print("MODEL COMPARISON")
print("=" * 60)

results = []

best_model = None
best_model_name = None
best_predictions = None
best_mae = float("inf")


for model_name, model in models.items():

    print(f"\nTraining {model_name}...")

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    predictions = np.maximum(
        predictions,
        0
    )

    # --------------------------------------
    # MAE
    # --------------------------------------

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    # --------------------------------------
    # RMSE
    # --------------------------------------

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    # --------------------------------------
    # MAPE
    # --------------------------------------

    valid_mask = y_test > 10000

    if valid_mask.sum() > 0:

        actual_valid = (
            y_test[valid_mask]
        )

        prediction_valid = (
            predictions[valid_mask]
        )

        mape = (
            np.mean(
                np.abs(
                    (
                        actual_valid
                        - prediction_valid
                    )
                    / actual_valid
                )
            )
            * 100
        )

    else:

        mape = 0

    # --------------------------------------
    # WMAPE
    # --------------------------------------

    total_actual = (
        y_test.abs().sum()
    )

    if total_actual > 0:

        wmape = (
            np.abs(
                y_test.values
                - predictions
            ).sum()
            / total_actual
            * 100
        )

    else:

        wmape = 0

    print(f"MAE   : Rp {mae:,.0f}")
    print(f"RMSE  : Rp {rmse:,.0f}")
    print(f"MAPE  : {mape:.2f}%")
    print(f"WMAPE : {wmape:.2f}%")

    results.append({
        "model": model_name,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "wmape": wmape
    })

    if mae < best_mae:

        best_mae = mae
        best_model = model
        best_model_name = model_name
        best_predictions = predictions


# ==========================================
# MODEL RANKING
# ==========================================

results_df = (
    pd.DataFrame(results)
    .sort_values("mae")
    .reset_index(drop=True)
)

print("\n" + "=" * 60)
print("MODEL RANKING")
print("=" * 60)

print(
    results_df.to_string(
        index=False
    )
)


# ==========================================
# BEST MODEL
# ==========================================

best_metrics = (
    results_df
    .iloc[0]
    .to_dict()
)

print("\n" + "=" * 60)
print("BEST MODEL")
print("=" * 60)

print(f"Model : {best_model_name}")
print(f"MAE   : Rp {best_metrics['mae']:,.0f}")
print(f"RMSE  : Rp {best_metrics['rmse']:,.0f}")
print(f"MAPE  : {best_metrics['mape']:.2f}%")
print(f"WMAPE : {best_metrics['wmape']:.2f}%")


# ==========================================
# FEATURE IMPORTANCE
# ==========================================

if hasattr(
    best_model,
    "feature_importances_"
):

    feature_importance = pd.DataFrame({
        "feature": feature_columns,
        "importance": best_model.feature_importances_
    })

    feature_importance = (
        feature_importance
        .sort_values(
            "importance",
            ascending=False
        )
        .reset_index(drop=True)
    )

    feature_importance.to_csv(
        MODEL_DIR / "feature_importance.csv",
        index=False
    )

    print("\nTOP 10 FEATURE IMPORTANCE")

    print(
        feature_importance
        .head(10)
        .to_string(index=False)
    )


# ==========================================
# SAVE MODEL
# ==========================================

print("\nSaving model...")

joblib.dump(
    best_model,
    MODEL_DIR / "forecast_model.pkl"
)

joblib.dump(
    feature_columns,
    MODEL_DIR / "feature_columns.pkl"
)

joblib.dump(
    best_model_name,
    MODEL_DIR / "model_name.pkl"
)

joblib.dump(
    best_metrics,
    MODEL_DIR / "metrics.pkl"
)

results_df.to_csv(
    MODEL_DIR / "model_comparison.csv",
    index=False
)


# ==========================================
# SAVE DATA
# ==========================================

daily_df.to_csv(
    MODEL_DIR / "daily_revenue.csv",
    index=False
)

forecast_df.to_csv(
    MODEL_DIR / "forecast_features.csv",
    index=False
)


# ==========================================
# SAVE TEST PREDICTIONS
# ==========================================

test_result = (
    forecast_df
    .iloc[split_index:]
    .copy()
)

test_result["actual_revenue"] = (
    y_test.values
)

test_result["predicted_revenue"] = (
    best_predictions
)

test_result.to_csv(
    MODEL_DIR / "test_predictions.csv",
    index=False
)


# ==========================================
# TRAINING COMPLETED
# ==========================================

print("\n" + "=" * 60)
print("TRAINING COMPLETED")
print("=" * 60)

print(f"\nBest model: {best_model_name}")

print(
    f"\nModel saved to:\n{MODEL_DIR}"
)