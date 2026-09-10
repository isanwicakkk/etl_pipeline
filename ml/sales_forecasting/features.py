import pandas as pd

from sqlalchemy import text


# ==========================================
# LOAD FORECASTING DATA
# ==========================================

def load_forecasting_data(engine):

    query = text("""
        SELECT
            order_id,
            status_pesanan,
            waktu_pesanan_dibuat,
            order_date,
            total_pembayaran
        FROM sales
        WHERE order_date IS NOT NULL
    """)

    df = pd.read_sql(
        query,
        engine
    )

    return df


# ==========================================
# CLEAN FORECASTING DATA
# ==========================================

def clean_forecasting_data(df):

    df = df.copy()

    required_columns = [
        "order_id",
        "status_pesanan",
        "order_date",
        "total_pembayaran"
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

    # ------------------------------------------
    # DATE CLEANING
    # ------------------------------------------

    df["order_date"] = pd.to_datetime(
        df["order_date"],
        errors="coerce"
    )

    # ------------------------------------------
    # REVENUE CLEANING
    # ------------------------------------------

    df["total_pembayaran"] = pd.to_numeric(
        df["total_pembayaran"],
        errors="coerce"
    )

    df["total_pembayaran"] = (
        df["total_pembayaran"]
        .fillna(0)
        .clip(lower=0)
    )

    # ------------------------------------------
    # STATUS CLEANING
    # ------------------------------------------

    df["status_clean"] = (
        df["status_pesanan"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # ------------------------------------------
    # REMOVE INVALID DATE
    # ------------------------------------------

    df = df.dropna(
        subset=["order_date"]
    )

    # ------------------------------------------
    # KEEP SUCCESSFUL ORDERS
    # ------------------------------------------

    successful_statuses = [
        "selesai",
        "completed",
        "success",
        "berhasil"
    ]

    df = df[
        df["status_clean"].isin(
            successful_statuses
        )
    ].copy()

    # ------------------------------------------
    # REMOVE DUPLICATE ORDERS
    # ------------------------------------------

    df = df.drop_duplicates(
        subset=["order_id"]
    )

    # ------------------------------------------
    # SORT
    # ------------------------------------------

    df = df.sort_values(
        "order_date"
    ).reset_index(drop=True)

    return df


# ==========================================
# CREATE DAILY REVENUE
# ==========================================

def create_daily_revenue(df):

    df = df.copy()

    daily_df = (
        df.groupby("order_date", as_index=False)
        .agg(
            revenue=(
                "total_pembayaran",
                "sum"
            ),
            total_orders=(
                "order_id",
                "nunique"
            )
        )
    )

    daily_df = daily_df.rename(
        columns={
            "order_date": "date"
        }
    )

    daily_df["date"] = pd.to_datetime(
        daily_df["date"]
    )

    daily_df = (
        daily_df
        .sort_values("date")
        .set_index("date")
    )

    # ------------------------------------------
    # FILL MISSING DAYS
    # ------------------------------------------

    daily_df = (
        daily_df
        .asfreq("D")
        .fillna(0)
    )

    daily_df = (
        daily_df
        .reset_index()
    )

    daily_df["revenue"] = (
        daily_df["revenue"]
        .astype(float)
    )

    daily_df["total_orders"] = (
        daily_df["total_orders"]
        .astype(float)
    )

    return daily_df


# ==========================================
# CREATE FORECASTING FEATURES
# ==========================================

def create_forecasting_features(daily_df):

    df = daily_df.copy()

    df["date"] = pd.to_datetime(
        df["date"]
    )

    df = df.sort_values(
        "date"
    ).reset_index(drop=True)

    # ==========================================
    # CALENDAR FEATURES
    # ==========================================

    df["year"] = df["date"].dt.year

    df["month"] = df["date"].dt.month

    df["quarter"] = df["date"].dt.quarter

    df["day"] = df["date"].dt.day

    df["day_of_week"] = df["date"].dt.dayofweek

    df["day_of_year"] = df["date"].dt.dayofyear

    df["week_of_year"] = (
        df["date"]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    df["is_weekend"] = (
        df["day_of_week"]
        .isin([5, 6])
        .astype(int)
    )

    df["is_month_start"] = (
        df["date"]
        .dt.is_month_start
        .astype(int)
    )

    df["is_month_end"] = (
        df["date"]
        .dt.is_month_end
        .astype(int)
    )

    # ==========================================
    # CYCLICAL FEATURES
    # ==========================================

    import numpy as np

    df["month_sin"] = np.sin(
        2 * np.pi * df["month"] / 12
    )

    df["month_cos"] = np.cos(
        2 * np.pi * df["month"] / 12
    )

    df["day_of_week_sin"] = np.sin(
        2 * np.pi * df["day_of_week"] / 7
    )

    df["day_of_week_cos"] = np.cos(
        2 * np.pi * df["day_of_week"] / 7
    )

    df["day_of_year_sin"] = np.sin(
        2 * np.pi * df["day_of_year"] / 365
    )

    df["day_of_year_cos"] = np.cos(
        2 * np.pi * df["day_of_year"] / 365
    )

    # ==========================================
    # LAG FEATURES
    # ==========================================

    lag_days = [
        1,
        2,
        3,
        7,
        14,
        21,
        28,
        30,
        60
    ]

    for lag in lag_days:

        df[f"lag_{lag}"] = (
            df["revenue"]
            .shift(lag)
        )

    # ==========================================
    # ORDER LAG FEATURES
    # ==========================================

    order_lags = [
        1,
        7,
        14,
        30
    ]

    for lag in order_lags:

        df[f"orders_lag_{lag}"] = (
            df["total_orders"]
            .shift(lag)
        )

    # ==========================================
    # ROLLING REVENUE FEATURES
    # ==========================================

    rolling_windows = [
        3,
        7,
        14,
        30,
        60
    ]

    for window in rolling_windows:

        df[f"rolling_mean_{window}"] = (
            df["revenue"]
            .shift(1)
            .rolling(window=window)
            .mean()
        )

        df[f"rolling_std_{window}"] = (
            df["revenue"]
            .shift(1)
            .rolling(window=window)
            .std()
        )

        df[f"rolling_min_{window}"] = (
            df["revenue"]
            .shift(1)
            .rolling(window=window)
            .min()
        )

        df[f"rolling_max_{window}"] = (
            df["revenue"]
            .shift(1)
            .rolling(window=window)
            .max()
        )

    # ==========================================
    # ORDER ROLLING FEATURES
    # ==========================================

    for window in [7, 14, 30]:

        df[f"orders_rolling_mean_{window}"] = (
            df["total_orders"]
            .shift(1)
            .rolling(window=window)
            .mean()
        )

    # ==========================================
    # TREND FEATURES
    # ==========================================

    df["trend"] = range(len(df))

    df["trend_squared"] = (
        df["trend"] ** 2
    )

    # ==========================================
    # GROWTH FEATURES
    # ==========================================

    df["growth_7"] = (
        (
            df["revenue"]
            - df["lag_7"]
        )
        / df["lag_7"].replace(0, np.nan)
    )

    df["growth_30"] = (
        (
            df["revenue"]
            - df["lag_30"]
        )
        / df["lag_30"].replace(0, np.nan)
    )

    # ==========================================
    # REVENUE VS ROLLING AVERAGE
    # ==========================================

    df["revenue_vs_avg_7"] = (
        df["lag_1"]
        / df["rolling_mean_7"].replace(
            0,
            np.nan
        )
    )

    df["revenue_vs_avg_30"] = (
        df["lag_1"]
        / df["rolling_mean_30"].replace(
            0,
            np.nan
        )
    )

    # ==========================================
    # CLEAN INFINITE VALUES
    # ==========================================

    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    return df


# ==========================================
# FEATURE COLUMNS
# ==========================================

def get_feature_columns():

    return [
        # Calendar
        "year",
        "month",
        "quarter",
        "day",
        "day_of_week",
        "day_of_year",
        "week_of_year",
        "is_weekend",
        "is_month_start",
        "is_month_end",

        # Cyclical
        "month_sin",
        "month_cos",
        "day_of_week_sin",
        "day_of_week_cos",
        "day_of_year_sin",
        "day_of_year_cos",

        # Revenue Lag
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_7",
        "lag_14",
        "lag_21",
        "lag_28",
        "lag_30",
        "lag_60",

        # Order Lag
        "orders_lag_1",
        "orders_lag_7",
        "orders_lag_14",
        "orders_lag_30",

        # Revenue Rolling Mean
        "rolling_mean_3",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "rolling_mean_60",

        # Revenue Rolling Std
        "rolling_std_3",
        "rolling_std_7",
        "rolling_std_14",
        "rolling_std_30",
        "rolling_std_60",

        # Revenue Rolling Min
        "rolling_min_3",
        "rolling_min_7",
        "rolling_min_14",
        "rolling_min_30",
        "rolling_min_60",

        # Revenue Rolling Max
        "rolling_max_3",
        "rolling_max_7",
        "rolling_max_14",
        "rolling_max_30",
        "rolling_max_60",

        # Orders Rolling
        "orders_rolling_mean_7",
        "orders_rolling_mean_14",
        "orders_rolling_mean_30",

        # Trend
        "trend",
        "trend_squared",

        # Growth
        "growth_7",
        "growth_30",

        # Revenue Ratio
        "revenue_vs_avg_7",
        "revenue_vs_avg_30"
    ]