import pandas as pd


def load_geo_data(engine):
    """
    Mengambil data transaksi untuk Geo Segmentation.
    """

    query = """
        SELECT
            order_id,
            status_pesanan,
            jumlah,
            total_pembayaran,
            kota_kabupaten,
            provinsi
        FROM sales
        WHERE provinsi IS NOT NULL;
    """

    return pd.read_sql(query, engine)


def create_geo_features(df, level="provinsi"):
    """
    Membuat fitur geografis untuk clustering.

    level:
    - provinsi
    - kota_kabupaten
    """

    df = df.copy()

    required_columns = [
        "order_id",
        "status_pesanan",
        "jumlah",
        "total_pembayaran",
        level
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

    # Bersihkan data
    df[level] = df[level].fillna("Unknown")

    df["jumlah"] = pd.to_numeric(
        df["jumlah"],
        errors="coerce"
    ).fillna(0)

    df["total_pembayaran"] = pd.to_numeric(
        df["total_pembayaran"],
        errors="coerce"
    ).fillna(0)

    # =====================================
    # UNIQUE ORDER
    # =====================================

    # Menghindari double counting revenue/order
    df_orders = df.drop_duplicates(
        subset=["order_id"]
    ).copy()

    # =====================================
    # SUCCESSFUL ORDERS
    # =====================================

    df_success = df_orders[
        df_orders["status_pesanan"] == "Selesai"
    ].copy()

    # =====================================
    # GEO FEATURES
    # =====================================

    geo_features = df.groupby(level).agg(
        total_rows=("order_id", "count")
    ).reset_index()

    # Successful revenue
    success_geo = df_success.groupby(level).agg(
        total_revenue=("total_pembayaran", "sum"),
        total_orders=("order_id", "nunique"),
        total_quantity=("jumlah", "sum")
    ).reset_index()

    geo_features = geo_features.merge(
        success_geo,
        on=level,
        how="left"
    )

    # =====================================
    # CANCELLATION RATE
    # =====================================

    order_geo = df_orders.groupby(level).agg(
        total_orders_all=("order_id", "nunique"),
        cancelled_orders=(
            "status_pesanan",
            lambda x: (x == "Batal").sum()
        )
    ).reset_index()

    geo_features = geo_features.merge(
        order_geo,
        on=level,
        how="left"
    )

    geo_features["cancellation_rate"] = (
        geo_features["cancelled_orders"]
        / geo_features["total_orders_all"].replace(0, 1)
        * 100
    )

    # =====================================
    # AVERAGE ORDER VALUE
    # =====================================

    geo_features["average_order_value"] = (
        geo_features["total_revenue"]
        / geo_features["total_orders"].replace(0, 1)
    )

    # Bersihkan NaN
    numeric_columns = [
        "total_revenue",
        "total_orders",
        "total_quantity",
        "average_order_value",
        "total_orders_all",
        "cancelled_orders",
        "cancellation_rate"
    ]

    geo_features[numeric_columns] = (
        geo_features[numeric_columns]
        .fillna(0)
    )

    return geo_features


def get_geo_feature_columns():
    """
    Feature yang digunakan untuk K-Means.
    """

    return [
        "total_revenue",
        "total_orders",
        "total_quantity",
        "average_order_value",
        "cancellation_rate"
    ]