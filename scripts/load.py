import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus


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

ENV_PATH = BASE_DIR / ".env"


# =====================================
# LOAD ENVIRONMENT VARIABLES
# =====================================

load_dotenv(dotenv_path=ENV_PATH)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# =====================================
# VALIDATE ENVIRONMENT VARIABLES
# =====================================

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
# DATABASE URL
# =====================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# =====================================
# FUNCTION: CONVERT TO SNAKE_CASE
# =====================================

def to_snake_case(column_name):
    column_name = str(column_name).strip().lower()

    # Ganti slash dan spasi menjadi underscore
    column_name = re.sub(r"[/\s]+", "_", column_name)

    # Hapus karakter selain huruf, angka, underscore
    column_name = re.sub(
        r"[^a-z0-9_]",
        "",
        column_name
    )

    # Hapus underscore berlebihan
    column_name = re.sub(
        r"_+",
        "_",
        column_name
    )

    return column_name.strip("_")


# =====================================
# MAIN PROCESS
# =====================================

def main():

    print("=" * 70)
    print("LOAD DATA TO SUPABASE POSTGRESQL")
    print("=" * 70)


    # =====================================
    # READ CSV
    # =====================================

    print("\nReading final_sales.csv...")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan:\n{INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    print(f"Total rows    : {len(df)}")
    print(f"Total columns : {len(df.columns)}")


    # =====================================
    # SHOW ORIGINAL COLUMNS
    # =====================================

    print("\nOriginal columns:")

    for column in df.columns:
        print(f" - {column}")


    # =====================================
    # CONVERT COLUMN NAMES
    # =====================================

    df.columns = [
        to_snake_case(column)
        for column in df.columns
    ]

    print("\nColumns after snake_case:")

    for column in df.columns:
        print(f" - {column}")


    # =====================================
    # CREATE DATABASE CONNECTION
    # =====================================

    print("\nConnecting to Supabase PostgreSQL...")

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

    try:
        with engine.connect() as connection:
            print("✓ Database connection successful")

    except Exception as e:
        print("\n✗ Database connection failed")
        raise e


    # =====================================
    # LOAD DATA TO POSTGRESQL
    # =====================================

    print("\nLoading data to table: public.sales...")

    df.to_sql(
        name="sales",
        con=engine,
        schema="public",
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi"
    )


    # =====================================
    # SUCCESS MESSAGE
    # =====================================

    print("\n" + "=" * 70)
    print("LOAD SUCCESSFUL")
    print("=" * 70)

    print(f"\nData loaded : {len(df):,} rows")
    print("Schema      : public")
    print("Table       : sales")

    print("\nDatabase columns:")

    for column in df.columns:
        print(f" - {column}")


# =====================================
# RUN SCRIPT
# =====================================

if __name__ == "__main__":
    main()