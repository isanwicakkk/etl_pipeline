import joblib
from pathlib import Path

from ml.product_segmentation.features import (
    create_product_features,
    get_feature_columns
)


# =====================================
# PROJECT PATH
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "product_segmentation"
    / "models"
)


# =====================================
# LOAD MODEL
# =====================================

def load_models():
    """
    Load K-Means model, scaler,
    dan cluster mapping.
    """

    kmeans = joblib.load(
        MODEL_DIR / "kmeans_model.pkl"
    )

    scaler = joblib.load(
        MODEL_DIR / "scaler.pkl"
    )

    feature_columns = joblib.load(
        MODEL_DIR / "feature_columns.pkl"
    )

    cluster_mapping = joblib.load(
        MODEL_DIR / "cluster_mapping.pkl"
    )

    return (
        kmeans,
        scaler,
        feature_columns,
        cluster_mapping
    )


# =====================================
# PREDICT PRODUCT SEGMENTS
# =====================================

def predict_product_segments(df):
    """
    Membuat segmentasi produk menggunakan
    model K-Means yang sudah ditraining.
    """

    # Load model
    (
        kmeans,
        scaler,
        feature_columns,
        cluster_mapping
    ) = load_models()

    # Create product features
    product_features = create_product_features(df)

    # Ambil feature
    X = product_features[
        feature_columns
    ].copy()

    # Scaling
    X_scaled = scaler.transform(X)

    # Predict cluster
    product_features["cluster"] = (
        kmeans.predict(X_scaled)
    )

    # Mapping cluster ke nama bisnis
    product_features["segment"] = (
        product_features["cluster"]
        .map(cluster_mapping)
    )

    return product_features


# =====================================
# GET FEATURE COLUMNS
# =====================================

def get_segmentation_features():
    """
    Mengembalikan feature yang digunakan
    untuk segmentasi.
    """

    return get_feature_columns()