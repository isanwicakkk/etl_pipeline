import os
import sys
import joblib
import pandas as pd

from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# =====================================
# PROJECT PATH
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Tambahkan root project ke Python path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# =====================================
# IMPORT FEATURES
# =====================================

from ml.product_segmentation.features import (
    load_product_data,
    create_product_features,
    get_feature_columns
)


# =====================================
# ENVIRONMENT CONFIGURATION
# =====================================

ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


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


# =====================================
# DATABASE CONNECTION
# =====================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


engine = create_engine(DATABASE_URL)


# =====================================
# MODEL PATH
# =====================================

MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "product_segmentation"
    / "models"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =====================================
# LOAD DATA
# =====================================

print("=" * 70)
print("PRODUCT SEGMENTATION TRAINING")
print("=" * 70)

print("\nLoading data from database...")

df = load_product_data(engine)

print(f"Total transaction rows: {len(df):,}")


# =====================================
# CREATE PRODUCT FEATURES
# =====================================

print("\nCreating product features...")

product_features = create_product_features(df)

print(
    f"Total product categories: "
    f"{len(product_features):,}"
)

print("\nProduct Features:")

print(
    product_features.head()
)


# =====================================
# SELECT FEATURES
# =====================================

feature_columns = get_feature_columns()

X = product_features[
    feature_columns
].copy()


# =====================================
# SCALE FEATURES
# =====================================

print("\nScaling features...")

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# =====================================
# FIND BEST K
# =====================================

print("\nEvaluating K-Means clusters...")

results = []

max_k = min(
    6,
    len(product_features) - 1
)


for k in range(2, max_k + 1):

    kmeans = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = kmeans.fit_predict(
        X_scaled
    )

    score = silhouette_score(
        X_scaled,
        labels
    )

    inertia = kmeans.inertia_

    results.append({
        "k": k,
        "silhouette_score": score,
        "inertia": inertia
    })

    print(
        f"K={k} | "
        f"Silhouette Score={score:.4f} | "
        f"Inertia={inertia:.2f}"
    )


# =====================================
# SELECT BEST MODEL
# =====================================

results_df = pd.DataFrame(results)

best_k = results_df.loc[
    results_df["silhouette_score"].idxmax(),
    "k"
]

best_k = int(best_k)

print("\n" + "=" * 70)
print(f"BEST NUMBER OF CLUSTERS: {best_k}")
print("=" * 70)


# =====================================
# TRAIN FINAL MODEL
# =====================================

print("\nTraining final K-Means model...")

kmeans = KMeans(
    n_clusters=best_k,
    random_state=42,
    n_init=10
)

product_features["cluster"] = (
    kmeans.fit_predict(X_scaled)
)


# =====================================
# CLUSTER SUMMARY
# =====================================

cluster_summary = product_features.groupby(
    "cluster"
)[feature_columns].mean()

print("\nCluster Summary:")

print(cluster_summary)


# =====================================
# BUSINESS CLUSTER LABELING
# =====================================

cluster_revenue = product_features.groupby(
    "cluster"
)["total_revenue"].mean().sort_values()


cluster_mapping = {}

cluster_ids = cluster_revenue.index.tolist()


if len(cluster_ids) == 2:

    cluster_mapping = {
        cluster_ids[0]: "Low Performance",
        cluster_ids[1]: "High Performance"
    }

elif len(cluster_ids) == 3:

    cluster_mapping = {
        cluster_ids[0]: "Low Performance",
        cluster_ids[1]: "Medium Performance",
        cluster_ids[2]: "Best Seller"
    }

else:

    labels = [
        "Low Performance",
        "Below Average",
        "Medium Performance",
        "High Performance",
        "Best Seller"
    ]

    for index, cluster_id in enumerate(cluster_ids):

        if index < len(labels):
            cluster_mapping[cluster_id] = labels[index]

        else:
            cluster_mapping[cluster_id] = (
                f"Cluster {cluster_id}"
            )


product_features["segment"] = (
    product_features["cluster"]
    .map(cluster_mapping)
)


# =====================================
# SAVE MODELS
# =====================================

print("\nSaving models...")

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


# =====================================
# SAVE RESULTS
# =====================================

product_features.to_csv(
    MODEL_DIR / "product_segments.csv",
    index=False
)

results_df.to_csv(
    MODEL_DIR / "cluster_evaluation.csv",
    index=False
)


# =====================================
# FINAL OUTPUT
# =====================================

print("\n" + "=" * 70)
print("TRAINING SUCCESSFUL")
print("=" * 70)

print(f"\nBest K: {best_k}")

print("\nModel files:")

print(
    MODEL_DIR / "kmeans_model.pkl"
)

print(
    MODEL_DIR / "scaler.pkl"
)

print(
    MODEL_DIR / "product_segments.csv"
)


print("\nPRODUCT SEGMENTS")

print(
    product_features[
        [
            "product_category",
            "total_revenue",
            "total_orders",
            "total_quantity",
            "return_rate",
            "cluster",
            "segment"
        ]
    ].sort_values(
        "total_revenue",
        ascending=False
    )
)