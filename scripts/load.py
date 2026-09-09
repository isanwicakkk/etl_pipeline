import os

import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine


# ==========================================
# PATH CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_sales.csv"
)


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL belum ditemukan di file .env"
    )


# ==========================================
# LOAD DATA
# ==========================================

print("=" * 70)
print("LOAD DATA TO POSTGRESQL")
print("=" * 70)

print("\nReading final_sales.csv...")

df = pd.read_csv(INPUT_PATH)

print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")


# ==========================================
# CREATE CONNECTION
# ==========================================

print("\nConnecting to PostgreSQL...")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

print("✓ Connection created")


# ==========================================
# LOAD DATA TO DATABASE
# ==========================================

print("\nLoading data...")

df.to_sql(
    name="sales",
    con=engine,
    if_exists="replace",
    index=False,
    chunksize=1000
)


print("\n" + "=" * 70)
print("LOAD SUCCESSFUL")
print("=" * 70)

print(f"\nData loaded: {len(df)} rows")
print("Table name: sales")