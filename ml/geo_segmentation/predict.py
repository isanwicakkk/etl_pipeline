import joblib
from pathlib import Path

from ml.geo_segmentation.features import (
    create_geo_features,
    get_geo_feature_columns
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "geo_segmentation"
    / "models"
)


def predict_geo_segments(df, level="provinsi"):

    # ==========================================
    # LOAD MODEL
    # ==========================================

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

    # ==========================================
    # CREATE GEO FEATURES
    # ==========================================

    geo_features = create_geo_features(
        df,
        level=level
    )

    # ==========================================
    # SELECT FEATURES
    # ==========================================

    X = geo_features[
        feature_columns
    ].copy()

    # ==========================================
    # SCALE DATA
    # ==========================================

    X_scaled = scaler.transform(X)

    # ==========================================
    # PREDICT CLUSTER
    # ==========================================

    geo_features["cluster"] = (
        kmeans.predict(X_scaled)
    )

    # ==========================================
    # MAP CLUSTER TO SEGMENT
    # ==========================================

    geo_features["segment"] = (
        geo_features["cluster"]
        .map(cluster_mapping)
    )

    return geo_features