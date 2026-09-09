import os
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

from ml.product_segmentation.features import load_product_data
from ml.product_segmentation.predict import predict_product_segments


# =====================================
# PATH
# =====================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


# =====================================
# DATABASE
# =====================================

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


engine = create_engine(DATABASE_URL)


# =====================================
# LOAD DATA
# =====================================

print("Loading data...")

df = load_product_data(engine)

print(f"Total transaction: {len(df):,}")


# =====================================
# PREDICT
# =====================================

print("\nRunning product segmentation...")

result = predict_product_segments(df)


# =====================================
# RESULT
# =====================================

print("\nPRODUCT SEGMENTATION RESULT")

print(
    result[
        [
            "product_category",
            "total_revenue",
            "total_orders",
            "total_quantity",
            "return_rate",
            "cluster",
            "segment"
        ]
    ]
)


print("\nSEGMENT DISTRIBUTION")

print(
    result["segment"].value_counts()
)