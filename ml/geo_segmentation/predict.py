import joblib
from pathlib import Path

from ml.geo_segmentation.features import create_geo_features

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "geo_segmentation"
    / "models"
)


def predict_geo_segments(df, level="provinsi"):
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

    geo_features = create_geo_features(
        df,
        level=level
    )

    X = geo_features[feature_columns].copy()

    X_scaled = scaler.transform(X)

    geo_features["cluster"] = kmeans.predict(X_scaled)

    geo_features["segment"] = (
        geo_features["cluster"]
        .map(cluster_mapping)
    )

    return geo_features