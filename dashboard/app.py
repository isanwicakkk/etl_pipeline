import sys
from pathlib import Path

# ==========================================
# SETUP PATH
# ==========================================

root_path = Path(__file__).resolve().parent.parent

if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

# ==========================================
# MODULE IMPORTS
# ==========================================

import streamlit as st

from utils.database import load_sales_data
from views.executive_dashboard import show_executive_dashboard
from ml.product_segmentation.predict import predict_product_segments
from ml.geo_segmentation.predict import predict_geo_segments
from views.product_segmentation import render_product_segmentation
from views.geo_segmentation import render_geo_segmentation

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("E-Commerce Dashboard")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# LOAD DATA
# ==========================================

try:
    df = load_sales_data()

except Exception as e:
    st.error(f"Gagal terhubung ke database: {e}")
    st.stop()

# PRODUCT AND GEO FUNCTION

try:
    product_segments = predict_product_segments(df)

except Exception as e:
    st.error(f"Gagal menjalankan Product Segmentation: {e}")
    st.stop()

try:
    geo_segments = predict_geo_segments(df)

except Exception as e:
    st.error(f"Gagal menjalankan Product Segmentation: {e}")
    st.stop()

# ==========================================
# HEADER
# ==========================================

st.title("📊 Data Analytical E-Commerce Sales Dashboard")

st.caption(
    "Monitoring Penjualan, Market Segmentation, Customer Analytics, dan Forecasting"
)

# ==========================================
# NAVIGATION
# ==========================================

tab1, tab2, tab3 = st.tabs([
    "📈 Executive Dashboard",
    "🎯 Market Segmentation",
    "🔮 Sales Forecasting"
])

# ==========================================
# TAB 1 - EXECUTIVE DASHBOARD
# ==========================================

with tab1:
    show_executive_dashboard(df)

# ==========================================
# TAB 2 - MARKET SEGMENTATION
# ==========================================

with tab2:
    subtab1, subtab2 = st.tabs([
        "📦 Product Segmentation",
        "🗺️ Geo Segmentation"
    ])

    with subtab1:
        render_product_segmentation(product_segments)

    with subtab2:
        render_geo_segmentation(geo_segments)

# ==========================================
# TAB 3 - SALES FORECASTING
# ==========================================

with tab3:
    st.header("🔮 Sales Forecasting")

    st.info(
        "Modul Forecasting akan diimplementasikan "
        "menggunakan Time Series Analysis."
    )