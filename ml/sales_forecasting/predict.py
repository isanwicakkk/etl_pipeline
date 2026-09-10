import sys
import joblib
import pandas as pd

from pathlib import Path

# ==========================================
# PROJECT PATH
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.sales_forecasting.features import (
    create_forecasting_features
)

# ==========================================
# MODEL DIRECTORY
# ==========================================

MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "sales_forecasting"
    / "models"
)

# ==========================================
# FORECAST CONFIGURATION
# ==========================================

MAX_FORECAST_DAYS = 30


# ==========================================
# LOAD MODEL
# ==========================================

def load_forecasting_model():

    model_path = MODEL_DIR / "forecast_model.pkl"
    feature_path = MODEL_DIR / "feature_columns.pkl"

    missing_files = []

    if not model_path.exists():
        missing_files.append("forecast_model.pkl")

    if not feature_path.exists():
        missing_files.append("feature_columns.pkl")

    if missing_files:
        raise FileNotFoundError(
            "File model belum ditemukan: "
            f"{missing_files}. "
            "Jalankan training terlebih dahulu."
        )

    model = joblib.load(model_path)

    feature_columns = joblib.load(feature_path)

    return model, feature_columns


# ==========================================
# LOAD HISTORICAL DATA
# ==========================================

def load_daily_revenue():

    data_path = MODEL_DIR / "daily_revenue.csv"

    if not data_path.exists():

        raise FileNotFoundError(
            "daily_revenue.csv belum ditemukan. "
            "Jalankan training terlebih dahulu."
        )

    df = pd.read_csv(data_path)

    required_columns = [
        "date",
        "revenue"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Kolom tidak ditemukan: {missing_columns}"
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce"
    )

    df = (
        df
        .dropna(subset=["date", "revenue"])
        .sort_values("date")
        .drop_duplicates(subset=["date"])
        .reset_index(drop=True)
    )

    if df.empty:

        raise ValueError(
            "Historical revenue kosong."
        )

    return df


# ==========================================
# HISTORICAL STATISTICS
# ==========================================

def get_historical_statistics(df):

    revenue = df["revenue"].copy()

    recent_revenue = revenue.tail(30)

    stats = {
        "mean": revenue.mean(),
        "median": revenue.median(),
        "recent_mean": recent_revenue.mean(),
        "recent_median": recent_revenue.median(),
        "min_positive": revenue[
            revenue > 0
        ].min(),
        "max": revenue.max()
    }

    return stats


# ==========================================
# CREATE FUTURE FEATURE
# ==========================================

def create_future_feature_row(
    working_df,
    future_date
):

    future_row = pd.DataFrame({
        "date": [future_date],
        "revenue": [pd.NA]
    })

    temp_df = pd.concat(
        [working_df, future_row],
        ignore_index=True
    )

    feature_df = create_forecasting_features(
        temp_df
    )

    feature_row = (
        feature_df
        .tail(1)
        .copy()
    )

    return feature_row


# ==========================================
# STABILIZE PREDICTION
# ==========================================

def stabilize_prediction(
    prediction,
    historical_stats,
    recent_predictions
):
    """
    Menstabilkan hasil forecast agar:
    - tidak negatif
    - tidak collapse ke nol secara ekstrem
    - tidak menghasilkan outlier berlebihan
    """

    prediction = max(0, float(prediction))

    recent_mean = historical_stats["recent_mean"]
    recent_median = historical_stats["recent_median"]

    if pd.isna(recent_mean) or recent_mean <= 0:
        recent_mean = historical_stats["mean"]

    if pd.isna(recent_median) or recent_median <= 0:
        recent_median = historical_stats["median"]

    # ======================================
    # LOWER BOUND
    # ======================================

    lower_bound = max(
        0,
        recent_median * 0.05
    )

    # ======================================
    # UPPER BOUND
    # ======================================

    upper_bound = max(
        historical_stats["max"] * 1.5,
        recent_mean * 4
    )

    prediction = min(
        prediction,
        upper_bound
    )

    # ======================================
    # PREVENT FORECAST COLLAPSE
    # ======================================

    if prediction < lower_bound:

        prediction = (
            lower_bound
            + (
                recent_median * 0.10
            )
        )

    # ======================================
    # SMOOTH RECURSIVE PREDICTIONS
    # ======================================

    if len(recent_predictions) >= 3:

        prediction_history = (
            pd.Series(recent_predictions[-3:])
            .mean()
        )

        prediction = (
            prediction * 0.75
            + prediction_history * 0.25
        )

    return max(0, prediction)

def generate_forecast(days=7):
    valid_periods = [7, 14, 30]

    if days not in valid_periods:
        raise ValueError(
            "Forecast hanya tersedia untuk 7, 14, atau 30 hari."
        )

    return forecast_future(days)

# ==========================================
# FORECAST FUTURE
# ==========================================

def forecast_future(days=30):

    if days < 1:

        raise ValueError(
            "Jumlah hari forecast minimal 1."
        )

    model, feature_columns = (
        load_forecasting_model()
    )

    historical_df = load_daily_revenue()

    historical_stats = (
        get_historical_statistics(
            historical_df
        )
    )

    working_df = historical_df.copy()

    forecasts = []

    recent_predictions = []

    last_date = (
        working_df["date"].max()
    )

    for step in range(1, days + 1):

        future_date = (
            last_date
            + pd.Timedelta(days=step)
        )

        feature_row = (
            create_future_feature_row(
                working_df,
                future_date
            )
        )

        missing_features = [
            column
            for column in feature_columns
            if column not in feature_row.columns
        ]

        if missing_features:

            raise ValueError(
                "Feature untuk prediction tidak ditemukan: "
                f"{missing_features}"
            )

        X_future = (
            feature_row[feature_columns]
            .copy()
        )

        # Handle missing feature values

        X_future = X_future.fillna(0)

        # ==================================
        # MODEL PREDICTION
        # ==================================

        raw_prediction = model.predict(
            X_future
        )[0]

        # ==================================
        # STABILIZATION
        # ==================================

        prediction = (
            stabilize_prediction(
                prediction=raw_prediction,
                historical_stats=historical_stats,
                recent_predictions=recent_predictions
            )
        )

        # ==================================
        # SAVE FORECAST
        # ==================================

        forecasts.append({
            "date": future_date,
            "forecast_revenue": prediction
        })

        recent_predictions.append(
            prediction
        )

        # ==================================
        # ADD PREDICTION TO HISTORY
        # ==================================

        new_row = pd.DataFrame({
            "date": [future_date],
            "revenue": [prediction]
        })

        working_df = pd.concat(
            [working_df, new_row],
            ignore_index=True
        )

    forecast_df = pd.DataFrame(
        forecasts
    )

    return forecast_df


# ==========================================
# GET FORECAST
# ==========================================

def get_forecast(period=7):

    valid_periods = [
        7,
        14,
        30
    ]

    if period not in valid_periods:

        raise ValueError(
            f"Period harus salah satu dari: "
            f"{valid_periods}"
        )

    # Forecast hanya sekali sampai 30 hari

    forecast_30 = forecast_future(
        MAX_FORECAST_DAYS
    )

    return (
        forecast_30
        .head(period)
        .reset_index(drop=True)
    )


# ==========================================
# GET ALL FORECASTS
# ==========================================

def get_all_forecasts():

    forecast_30 = forecast_future(
        MAX_FORECAST_DAYS
    )

    forecast_7 = (
        forecast_30
        .head(7)
        .reset_index(drop=True)
    )

    forecast_14 = (
        forecast_30
        .head(14)
        .reset_index(drop=True)
    )

    forecast_30 = (
        forecast_30
        .reset_index(drop=True)
    )

    return {
        "7_days": forecast_7,
        "14_days": forecast_14,
        "30_days": forecast_30
    }


# ==========================================
# FORECAST SUMMARY
# ==========================================

def get_forecast_summary():

    forecasts = get_all_forecasts()

    summary = {}

    for period_name, forecast_df in forecasts.items():

        summary[period_name] = {
            "total_revenue": (
                forecast_df[
                    "forecast_revenue"
                ].sum()
            ),

            "average_daily_revenue": (
                forecast_df[
                    "forecast_revenue"
                ].mean()
            ),

            "max_daily_revenue": (
                forecast_df[
                    "forecast_revenue"
                ].max()
            ),

            "min_daily_revenue": (
                forecast_df[
                    "forecast_revenue"
                ].min()
            )
        }

    return summary


# ==========================================
# RUN PREDICTION
# ==========================================

if __name__ == "__main__":

    print("=" * 60)
    print("SALES FORECASTING PREDICTION")
    print("=" * 60)

    forecasts = get_all_forecasts()

    for period_name, forecast_df in forecasts.items():

        days = len(forecast_df)

        print("\n" + "-" * 60)

        print(
            f"FORECAST {days} DAYS"
        )

        print("-" * 60)

        print(
            forecast_df.to_string(
                index=False
            )
        )

        total = (
            forecast_df[
                "forecast_revenue"
            ].sum()
        )

        average = (
            forecast_df[
                "forecast_revenue"
            ].mean()
        )

        print(
            f"\nTotal Forecast: "
            f"Rp {total:,.0f}"
        )

        print(
            f"Average Daily Forecast: "
            f"Rp {average:,.0f}"
        )

    print("\n" + "=" * 60)
    print("PREDICTION COMPLETED")
    print("=" * 60)