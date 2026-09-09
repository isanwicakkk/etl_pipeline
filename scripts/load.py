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
# HELPER FUNCTION: CLEAN SNAKE CASE
# ==========================================


def to_snake_case(name: str) -> str:
    """Ubah nama kolom menjadi snake_case (huruf kecil, dipisah underscore)."""
    name = str(name).strip()

    # Pisahkan camelCase / PascalCase -> camel_Case
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)

    # Ganti spasi, tanda baca, dan karakter selain huruf/angka menjadi underscore
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)

    # Hilangkan underscore ganda dan di awal/akhir
    name = re.sub(r"_+", "_", name).strip("_")

    return name.lower()


# ==========================================
# LOAD DATA
# ==========================================

print("=" * 70)
print("LOAD DATA TO POSTGRESQL")
print("=" * 70)

print("\nReading final_sales.csv...")

df = pd.read_csv(INPUT_PATH)

# Bersihkan nama kolom DataFrame
df.columns = [to_snake_case(col) for col in df.columns]

print("✓ Nama kolom sudah dibersihkan menjadi snake_case")
print(f"  Contoh kolom: {list(df.columns)[:5]}")


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