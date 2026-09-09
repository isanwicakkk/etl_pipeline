import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

st.set_page_config(page_title="E-Commerce Sales Dashboard", layout="wide")

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# =====================================
# LOAD ENV
# =====================================

load_dotenv(ENV_PATH)

# =====================================
# DATABASE CONFIGURATION
# =====================================

def get_db_config():
    try:
        # Streamlit Cloud
        return {
            "DB_USER": st.secrets["DB_USER"],
            "DB_PASSWORD": st.secrets["DB_PASSWORD"],
            "DB_HOST": st.secrets["DB_HOST"],
            "DB_PORT": st.secrets["DB_PORT"],
            "DB_NAME": st.secrets["DB_NAME"]
        }

    except Exception:
        # Local development
        return {
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD"),
            "DB_HOST": os.getenv("DB_HOST"),
            "DB_PORT": os.getenv("DB_PORT"),
            "DB_NAME": os.getenv("DB_NAME")
        }


db_config = get_db_config()

missing_vars = [
    key
    for key, value in db_config.items()
    if not value
]

if missing_vars:
    st.error(
        f"Database configuration belum lengkap: {', '.join(missing_vars)}"
    )
    st.stop()

DB_USER = db_config["DB_USER"]
DB_PASSWORD = db_config["DB_PASSWORD"]
DB_HOST = db_config["DB_HOST"]
DB_PORT = db_config["DB_PORT"]
DB_NAME = db_config["DB_NAME"]

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# =====================================
# DATABASE CONNECTION
# =====================================

@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)

engine = get_engine()

@st.cache_data(ttl=600)
def load_data():
    query = """
    SELECT
        order_id,
        product_category,
        waktu_pesanan_dibuat,
        status_pesanan,
        jumlah,
        total_pembayaran,
        kota_kabupaten,
        provinsi
    FROM sales
    WHERE waktu_pesanan_dibuat IS NOT NULL;
    """

    df = pd.read_sql(query, engine)
    df["waktu_pesanan_dibuat"] = pd.to_datetime(df["waktu_pesanan_dibuat"])
    return df

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Gagal terhubung ke database PostgreSQL Docker: {e}")
    st.stop()

st.title("🛒 E-Commerce Executive Dashboard")
st.markdown("Monitoring Kinerja Penjualan dan Analisis Data E-Commerce")

# Sidebar filters
st.sidebar.header("🎛️ Filter Dashboard")

min_date = df_raw["waktu_pesanan_dibuat"].min().date()
max_date = df_raw["waktu_pesanan_dibuat"].max().date()

date_range = st.sidebar.date_input(
    "📅 Pilih Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)

    df_filtered = df_raw[
        (df_raw["waktu_pesanan_dibuat"] >= start_date) &
        (df_raw["waktu_pesanan_dibuat"] < end_date)
    ].copy()
else:
    df_filtered = df_raw.copy()

# Status filter
status_options = sorted(df_filtered["status_pesanan"].dropna().unique())

selected_status = st.sidebar.multiselect(
    "📦 Status Pesanan",
    options=status_options,
    default=status_options
)

df_filtered = df_filtered[
    df_filtered["status_pesanan"].isin(selected_status)
]

# Province filter
province_options = sorted(df_filtered["provinsi"].dropna().unique())

selected_province = st.sidebar.multiselect(
    "🗺️ Provinsi",
    options=province_options,
    default=province_options
)

df_filtered = df_filtered[
    df_filtered["provinsi"].isin(selected_province)
]

# Product category filter
category_options = sorted(df_filtered["product_category"].dropna().unique())

selected_category = st.sidebar.multiselect(
    "📦 Kategori Produk",
    options=category_options,
    default=category_options
)

df_filtered = df_filtered[
    df_filtered["product_category"].isin(selected_category)
]

tab1, tab2, tab3 = st.tabs([
    "📊 Executive KPI & Trends",
    "👥 Customer Segmentation",
    "🔮 Sales Forecasting"
])

with tab1:
    st.header("📊 Executive KPI & Sales Analysis")

    df_unique_orders = df_filtered.drop_duplicates(subset=["order_id"]).copy()

    df_success = df_filtered[
        df_filtered["status_pesanan"] == "Selesai"
    ].copy()

    df_success_unique = df_success.drop_duplicates(
        subset=["order_id"]
    ).copy()

    # KPI calculations
    total_revenue = df_success_unique["total_pembayaran"].sum()
    total_orders = df_success_unique["order_id"].nunique()
    total_quantity = df_success["jumlah"].sum()

    aov = total_revenue / total_orders if total_orders > 0 else 0

    all_orders = df_unique_orders["order_id"].nunique()

    cancelled_orders = df_unique_orders[
        df_unique_orders["status_pesanan"] == "Batal"
    ]["order_id"].nunique()

    cancel_rate = (
        cancelled_orders / all_orders * 100
        if all_orders > 0 else 0
    )

    # KPI cards
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("💰 Total Revenue", f"Rp {total_revenue:,.0f}")
    col2.metric("🛒 Total Orders", f"{total_orders:,}")
    col3.metric("📦 Total Quantity", f"{total_quantity:,.0f}")
    col4.metric("💳 Average Order Value", f"Rp {aov:,.0f}")
    col5.metric("❌ Cancellation Rate", f"{cancel_rate:.2f}%")

    # Monthly trend
    st.subheader("📈 Tren Pendapatan Bulanan")

    if not df_success_unique.empty:
        df_success_unique["bulan"] = (
            df_success_unique["waktu_pesanan_dibuat"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly_sales = (
            df_success_unique
            .groupby("bulan")
            .agg(
                total_revenue=("total_pembayaran", "sum"),
                total_orders=("order_id", "nunique")
            )
            .reset_index()
        )

        fig_monthly = px.line(
            monthly_sales,
            x="bulan",
            y="total_revenue",
            markers=True,
            title="Trend Revenue Bulanan",
            labels={
                "bulan": "Bulan",
                "total_revenue": "Total Revenue"
            },
            hover_data=["total_orders"]
        )

        st.plotly_chart(fig_monthly, use_container_width=True)
    else:
        st.warning("Tidak ada data pesanan selesai pada filter yang dipilih.")

    # Product analysis
    st.subheader("📦 Analisis Kategori Produk")

    if not df_success.empty:
        product_sales = (
            df_success
            .groupby("product_category")
            .agg(
                total_revenue=("total_pembayaran", "sum"),
                total_quantity=("jumlah", "sum"),
                total_orders=("order_id", "nunique")
            )
            .reset_index()
            .sort_values("total_revenue", ascending=False)
        )

        col_product1, col_product2 = st.columns(2)

        with col_product1:
            fig_product_revenue = px.bar(
                product_sales.head(10),
                x="product_category",
                y="total_revenue",
                title="Top 10 Kategori Berdasarkan Revenue",
                labels={
                    "product_category": "Kategori Produk",
                    "total_revenue": "Total Revenue"
                },
                hover_data=["total_quantity", "total_orders"]
            )

            st.plotly_chart(
                fig_product_revenue,
                use_container_width=True
            )

        with col_product2:
            fig_product_quantity = px.bar(
                product_sales.head(10),
                x="product_category",
                y="total_quantity",
                title="Top 10 Kategori Berdasarkan Quantity",
                labels={
                    "product_category": "Kategori Produk",
                    "total_quantity": "Total Quantity"
                },
                hover_data=["total_orders"]
            )

            st.plotly_chart(
                fig_product_quantity,
                use_container_width=True
            )

    # Province analysis
    st.subheader("🗺️ Analisis Berdasarkan Provinsi")

    if not df_success.empty:
        province_sales = (
            df_success
            .groupby("provinsi")
            .agg(
                total_revenue=("total_pembayaran", "sum"),
                total_orders=("order_id", "nunique"),
                total_quantity=("jumlah", "sum")
            )
            .reset_index()
            .sort_values("total_revenue", ascending=False)
        )

        fig_province = px.bar(
            province_sales.head(10),
            x="provinsi",
            y="total_revenue",
            title="Top 10 Provinsi Berdasarkan Revenue",
            labels={
                "provinsi": "Provinsi",
                "total_revenue": "Total Revenue"
            },
            hover_data=["total_orders", "total_quantity"]
        )

        st.plotly_chart(fig_province, use_container_width=True)

    # City analysis
    st.subheader("🏙️ Analisis Berdasarkan Kota / Kabupaten")

    if not df_success.empty:
        city_sales = (
            df_success
            .groupby("kota_kabupaten")
            .agg(
                total_revenue=("total_pembayaran", "sum"),
                total_orders=("order_id", "nunique"),
                total_quantity=("jumlah", "sum")
            )
            .reset_index()
            .sort_values("total_revenue", ascending=False)
        )

        fig_city = px.bar(
            city_sales.head(15),
            x="kota_kabupaten",
            y="total_revenue",
            title="Top 15 Kota / Kabupaten Berdasarkan Revenue",
            labels={
                "kota_kabupaten": "Kota / Kabupaten",
                "total_revenue": "Total Revenue"
            },
            hover_data=["total_orders", "total_quantity"]
        )

        st.plotly_chart(fig_city, use_container_width=True)

    # Transaction detail
    st.subheader("📋 Detail Transaksi")

    display_columns = [
        "order_id",
        "waktu_pesanan_dibuat",
        "product_category",
        "status_pesanan",
        "jumlah",
        "total_pembayaran",
        "kota_kabupaten",
        "provinsi"
    ]

    df_display = (
        df_filtered[display_columns]
        .sort_values("waktu_pesanan_dibuat", ascending=False)
        .head(500)
    )

    column_mapping = {
        "order_id": "Order ID",
        "waktu_pesanan_dibuat": "Tanggal Pesanan",
        "product_category": "Kategori Produk",
        "status_pesanan": "Status Pesanan",
        "jumlah": "Jumlah",
        "total_pembayaran": "Total Pembayaran",
        "kota_kabupaten": "Kota / Kabupaten",
        "provinsi": "Provinsi"
    }

    df_display = df_display.rename(columns=column_mapping)

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.header("👥 Customer Segmentation")
    st.info(
        "Modul Customer Segmentation menggunakan RFM dan K-Means "
        "akan dibuat pada tahap berikutnya."
    )

with tab3:
    st.header("🔮 Sales Demand Forecasting")
    st.info("Modul Sales Forecasting akan dibuat pada tahap berikutnya.")