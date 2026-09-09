import os
import re
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# ==========================================
# PATH CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "data" / "processed" / "final_sales.csv"


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL belum ditemukan di file .env")


# ==========================================
# HELPER FUNCTION: SNAKE CASE CONVERTER
# ==========================================


def to_snake_case(text: str) -> str:
    """Mengubah string dari CamelCase, Title Case, Spasi, atau Simbol menjadi

    snake_case.
    """
    # Masukkan garis bawah sebelum huruf kapital (jika ada format CamelCase)
    text = re.sub(r"(?<!^)(?=[A-Z])", "_", text)
    # Ganti spasi, strip, atau karakter non-alphanumeric menjadi underscore
    text = re.sub(r"[\s\-\W]+", "_", text)
    # Hapus underscore di awal/akhir string dan ubah ke huruf kecil semua
    return text.strip("_").lower()


# ==========================================
# LOAD DATA
# ==========================================

print("=" * 70)
print("LOAD DATA TO POSTGRESQL")
print("=" * 70)

print("\nReading final_sales.csv...")

df = pd.read_csv(INPUT_PATH)

# Mengubah nama kolom menjadi snake_case
df.columns = [to_snake_case(col) for col in df.columns]

print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print(f"Columns (snake_case): {list(df.columns)}")


# ==========================================
# CREATE CONNECTION
# ==========================================

print("\nConnecting to PostgreSQL...")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("✓ Connection created")


# ==========================================
# LOAD DATA TO DATABASE
# ==========================================

print("\nLoading data...")

df.to_sql(
    name="sales", con=engine, if_exists="replace", index=False, chunksize=1000
)


print("\n" + "=" * 70)
print("LOAD SUCCESSFUL")
print("=" * 70)

print(f"\nData loaded: {len(df)} rows")
print("Table name: sales")