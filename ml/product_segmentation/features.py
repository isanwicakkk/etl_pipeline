import pandas as pd


def load_product_data(engine):
    """
    Mengambil data transaksi dari database.
    """

    query = """
        SELECT
            order_id,
            product_category,
            status_pesanan,
            jumlah,
            returned_quantity,
            total_pembayaran
        FROM sales
        WHERE product_category IS NOT NULL;
    """

    df = pd.read_sql(query, engine)

    return df


def create_product_features(df):
    """
    Membuat feature engineering untuk setiap kategori produk.

    Features:
    - total_revenue
    - total_orders
    - total_quantity
    - average_order_value
    - return_rate
    """

    df = df.copy()

    numeric_columns = [
        "jumlah",
        "returned_quantity",
        "total_pembayaran"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

    # Hanya transaksi selesai
    df_success = df[
        df["status_pesanan"] == "Selesai"
    ].copy()

    # Aggregate berdasarkan kategori produk
    product_features = df_success.groupby(
        "product_category"
    ).agg(
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
        ),
        returned_quantity=(
            "returned_quantity",
            "sum"
        )
    ).reset_index()

    # Average Order Value
    product_features["average_order_value"] = (
        product_features["total_revenue"]
        / product_features["total_orders"].replace(0, 1)
    )

    # Return Rate
    product_features["return_rate"] = (
        product_features["returned_quantity"]
        / product_features["total_quantity"].replace(0, 1)
    ) * 100

    # Bersihkan infinity
    product_features = product_features.replace(
        [float("inf"), float("-inf")],
        0
    )

    product_features = product_features.fillna(0)

    return product_features


def get_feature_columns():
    """
    Mengembalikan feature yang digunakan K-Means.
    """

    return [
        "total_revenue",
        "total_orders",
        "total_quantity",
        "average_order_value",
        "return_rate"
    ]