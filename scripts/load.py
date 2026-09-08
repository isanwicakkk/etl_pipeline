import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine


# =====================================
# PATH CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_sales.csv"
)


# =====================================
# DATABASE CONFIGURATION
# =====================================

DB_USER = "myuser"
DB_PASSWORD = "password123"
DB_HOST = "127.0.0.1"
DB_PORT = "5433"
DB_NAME = "mydb"


# =====================================
# DATABASE CONNECTION
# =====================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# =====================================
# LOAD DATA
# =====================================

print("=" * 70)
print("LOAD DATA TO POSTGRESQL")
print("=" * 70)


# Read CSV
print("\nReading final_sales.csv...")

df = pd.read_csv(INPUT_PATH)

print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")


# Create connection
print("\nConnecting to PostgreSQL...")

engine = create_engine(DATABASE_URL)

print("✓ Connection created")


# Load data
print("\nLoading data...")

df.to_sql(
    name="sales",
    con=engine,
    if_exists="replace",
    index=False
)


print("\n" + "=" * 70)
print("LOAD SUCCESSFUL")
print("=" * 70)

print(f"\nData loaded: {len(df)} rows")
print("Table name: sales")