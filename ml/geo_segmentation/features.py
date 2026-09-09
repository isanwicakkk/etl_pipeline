import pandas as pd


def load_geo_data(engine):
    """Mengambil data yang diperlukan untuk Geo Segmentation."""

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
    """Membuat fitur geografis untuk clustering."""

    df = df.copy()

    # Validasi kolom
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

    # Cleaning
    df[level] = df[level].fillna("Unknown")

    df["status_pesanan"] = (
        df["status_pesanan"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["jumlah"] = pd.to_numeric(
        df["jumlah"],
        errors="coerce"
    ).fillna(0)

    df["total_pembayaran"] = pd.to_numeric(
        df["total_pembayaran"],
        errors="coerce"
    ).fillna(0)

    # Ambil satu record per order
    df_orders = df.drop_duplicates(
        subset=["order_id"]
    ).copy()

    # Semua order per wilayah
    geo_all = (
        df_orders
        .groupby(level)
        .agg(
            total_orders_all=("order_id", "nunique"),
            cancelled_orders=(
                "status_pesanan",
                lambda x: (x == "batal").sum()
            )
        )
        .reset_index()
    )

    # Order selesai
    df_success = df_orders[
        df_orders["status_pesanan"] == "selesai"
    ].copy()

    # Metrics dari transaksi selesai
    geo_success = (
        df_success
        .groupby(level)
        .agg(
            total_revenue=(
                "total_pembayaran",
                "sum"
            ),
            total_orders=(
                "order_id",
                "nunique"
            ),
            total_quantity=(
                "jumlah",
                "sum"
            )
        )
        .reset_index()
    )

    # Gabungkan
    geo_features = geo_all.merge(
        geo_success,
        on=level,
        how="left"
    )

    # Isi missing value
    numeric_columns = [
        "total_orders_all",
        "cancelled_orders",
        "total_revenue",
        "total_orders",
        "total_quantity"
    ]

    geo_features[numeric_columns] = (
        geo_features[numeric_columns]
        .fillna(0)
    )

    # Cancellation rate
    geo_features["cancellation_rate"] = (
        geo_features["cancelled_orders"]
        / geo_features["total_orders_all"].replace(0, 1)
        * 100
    )

    # Average Order Value
    geo_features["average_order_value"] = (
        geo_features["total_revenue"]
        / geo_features["total_orders"].replace(0, 1)
    )

    geo_features["average_order_value"] = (
        geo_features["average_order_value"]
        .fillna(0)
    )

    # Sort
    geo_features = (
        geo_features
        .sort_values(
            by="total_revenue",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return geo_features


def get_geo_feature_columns():
    """Mengembalikan fitur yang digunakan K-Means."""

    return [
        "total_revenue",
        "total_orders",
        "total_quantity",
        "average_order_value",
        "cancellation_rate"
    ]