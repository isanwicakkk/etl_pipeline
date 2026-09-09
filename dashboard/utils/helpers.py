import pandas as pd


# ==========================================
# FORMAT RUPIAH
# ==========================================

def format_rupiah(value):

    if pd.isna(value):
        return "Rp 0"

    return f"Rp {value:,.0f}"


# ==========================================
# GET UNIQUE ORDERS
# ==========================================
def get_unique_orders(df):

    return df.drop_duplicates(
        subset=["order_id"]
    ).copy()


# ==========================================
# FILTER DATE RANGE
# ==========================================

def filter_by_date(df, start_date, end_date):

    mask = (
        df["waktu_pesanan_dibuat"].dt.date >= start_date
    ) & (
        df["waktu_pesanan_dibuat"].dt.date <= end_date
    )

    return df[mask].copy()


# ==========================================
# GET SUCCESSFUL ORDERS
# ==========================================

def get_success_orders(df):

    return df[
        df["status_pesanan"] == "Selesai"
    ].copy()


# ==========================================
# CALCULATE KPI
# ==========================================

def calculate_kpi(df):

    df_unique = get_unique_orders(df)

    df_success = get_success_orders(df_unique)

    total_revenue = df_success[
        "total_pembayaran"
    ].sum()

    total_orders = df_success[
        "order_id"
    ].nunique()

    aov = (
        total_revenue / total_orders
        if total_orders > 0
        else 0
    )

    all_orders = df_unique[
        "order_id"
    ].nunique()

    cancelled_orders = df_unique[
        df_unique["status_pesanan"] == "Batal"
    ]["order_id"].nunique()

    cancellation_rate = (
        cancelled_orders / all_orders * 100
        if all_orders > 0
        else 0
    )

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "aov": aov,
        "all_orders": all_orders,
        "cancelled_orders": cancelled_orders,
        "cancellation_rate": cancellation_rate
    }