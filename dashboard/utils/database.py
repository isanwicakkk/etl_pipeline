import os

import pandas as pd
import streamlit as st

from dotenv import load_dotenv
from sqlalchemy import create_engine


# Load environment variables
load_dotenv()


@st.cache_resource
def get_engine():
    # Coba ambil dari Streamlit Secrets
    if "DATABASE_URL" in st.secrets:
        database_url = st.secrets["DATABASE_URL"]
    else:
        # Jika local, ambil dari .env
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL belum ditemukan. "
            "Periksa .env atau Streamlit Secrets."
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True
    )

    return engine


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
        df["waktu_pesanan_dibuat"],
        errors="coerce"
    )

    df["jumlah"] = pd.to_numeric(
        df["jumlah"],
        errors="coerce"
    ).fillna(0)

    df["total_pembayaran"] = pd.to_numeric(
        df["total_pembayaran"],
        errors="coerce"
    ).fillna(0)

    return df