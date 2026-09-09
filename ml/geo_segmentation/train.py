import os
import sys
from pathlib import Path

import joblib
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# IMPORT FEATURES
# ============================================================

from ml.geo_segmentation.features import (
    load_geo_data,
    create_geo_features,
    get_geo_feature_columns
)


# ============================================================
# MODEL DIRECTORY
# ============================================================

MODEL_DIR = BASE_DIR / "ml" / "geo_segmentation" / "models"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# ============================================================
# VALIDATE ENVIRONMENT
# ============================================================

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


# ============================================================
# DATABASE CONNECTION
# ============================================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("GEO SEGMENTATION TRAINING")
print("=" * 60)

print("\nLoading data...")

df = load_geo_data(engine)

print(f"Total rows: {len(df):,}")


# ============================================================
# CREATE FEATURES
# ============================================================

print("\nCreating province features...")

geo_features = create_geo_features(
    df,
    level="provinsi"
)

print(f"Total provinces: {len(geo_features):,}")


# ============================================================
# FEATURE SELECTION
# ============================================================

feature_columns = get_geo_feature_columns()

X = geo_features[feature_columns].copy()


# ============================================================
# CHECK DATA
# ============================================================

if len(geo_features) < 3:
    raise ValueError(
        "Data wilayah terlalu sedikit untuk melakukan clustering."
    )

if X.isnull().any().any():
    raise ValueError(
        "Masih terdapat missing value pada fitur clustering."
    )


# ============================================================
# SCALING
# ============================================================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# ============================================================
# FIND BEST K
# ============================================================

print("\nEvaluating number of clusters...")

max_k = min(6, len(geo_features) - 1)

best_k = 2
best_score = -1

for k in range(2, max_k + 1):

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = model.fit_predict(X_scaled)

    score = silhouette_score(
        X_scaled,
        labels
    )

    print(
        f"K={k} | Silhouette Score={score:.4f}"
    )

    if score > best_score:
        best_score = score
        best_k = k


print(f"\nBest K: {best_k}")
print(f"Best Silhouette Score: {best_score:.4f}")


# ============================================================
# TRAIN FINAL MODEL
# ============================================================

print("\nTraining final model...")

kmeans = KMeans(
    n_clusters=best_k,
    random_state=42,
    n_init=10
)

geo_features["cluster"] = (
    kmeans.fit_predict(X_scaled)
)


# ============================================================
# CLUSTER MAPPING
# ============================================================

cluster_summary = (
    geo_features
    .groupby("cluster")["total_revenue"]
    .mean()
    .sort_values()
)

segment_names = [
    "Low Potential",
    "Medium Potential",
    "High Potential",
    "Top Market",
    "Strategic Market"
]

cluster_mapping = {}

for i, cluster_id in enumerate(cluster_summary.index):

    cluster_mapping[cluster_id] = (
        segment_names[
            min(i, len(segment_names) - 1)
        ]
    )


geo_features["segment"] = (
    geo_features["cluster"]
    .map(cluster_mapping)
)


# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    kmeans,
    MODEL_DIR / "kmeans_model.pkl"
)

joblib.dump(
    scaler,
    MODEL_DIR / "scaler.pkl"
)

joblib.dump(
    feature_columns,
    MODEL_DIR / "feature_columns.pkl"
)

joblib.dump(
    cluster_mapping,
    MODEL_DIR / "cluster_mapping.pkl"
)


# ============================================================
# SAVE RESULT
# ============================================================

geo_features.to_csv(
    MODEL_DIR / "geo_segments.csv",
    index=False
)


# ============================================================
# RESULT
# ============================================================

print("\n" + "=" * 60)
print("TRAINING COMPLETED")
print("=" * 60)

print("\nSegment Distribution:")

print(
    geo_features["segment"]
    .value_counts()
)

print("\nSaved files:")

print(f"- {MODEL_DIR / 'kmeans_model.pkl'}")
print(f"- {MODEL_DIR / 'scaler.pkl'}")
print(f"- {MODEL_DIR / 'feature_columns.pkl'}")
print(f"- {MODEL_DIR / 'cluster_mapping.pkl'}")
print(f"- {MODEL_DIR / 'geo_segments.csv'}")