import os
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables untuk lokal
load_dotenv()


def get_secret_or_env(key: str) -> str | None:
    """Membaca variabel dari Streamlit Secrets terlebih dahulu,

    jika tidak ada/lokal, baru membaca dari os.getenv / .env.
    """
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key)


def build_database_url() -> str:
    """Membentuk DATABASE_URL yang valid baik dari string utuh

    maupun dari komponen terpisah (DB_USER, DB_PASSWORD, dll).
    """
    # 1. Coba ambil DATABASE_URL langsung jika sudah ada
    db_url = get_secret_or_env("DATABASE_URL")
    if db_url:
        return db_url

    # 2. Jika tidak ada DATABASE_URL utuh, rakit dari komponen terpisah
    user = get_secret_or_env("DB_USER")
    password = get_secret_or_env("DB_PASSWORD")
    host = get_secret_or_env("DB_HOST")
    port = get_secret_or_env("DB_PORT")
    dbname = get_secret_or_env("DB_NAME") or "postgres"

    if user and password and host:
        # quote_plus amankan karakter khusus pada password seperti @, #, $, %
        safe_password = quote_plus(password)
        return f"postgresql+psycopg2://{user}:{safe_password}@{host}:{port}/{dbname}"

    raise ValueError(
        "Konfigurasi database tidak lengkap. "
        "Pastikan 'DATABASE_URL' atau ('DB_USER', 'DB_PASSWORD', 'DB_HOST') "
        "tersedia di Streamlit Secrets atau file .env."
    )


@st.cache_resource
def get_engine():
    database_url = build_database_url()
    return create_engine(database_url, pool_pre_ping=True)


@st.cache_data(ttl=600)
def load_sales_data():
    engine = get_engine()

    query = """
        SELECT 
            order_id,
            product_category,
            status_pesanan,
            waktu_pesanan_dibuat,
            jumlah,
            total_pembayaran,
            kota_kabupaten,
            provinsi
        FROM sales
        WHERE waktu_pesanan_dibuat IS NOT NULL
    """

    df = pd.read_sql(query, engine)

    df["waktu_pesanan_dibuat"] = pd.to_datetime(
        df["waktu_pesanan_dibuat"], errors="coerce"
    )

    df["jumlah"] = pd.to_numeric(df["jumlah"], errors="coerce").fillna(0)

    df["total_pembayaran"] = (
        pd.to_numeric(df["total_pembayaran"], errors="coerce").fillna(0)
    )

    return df