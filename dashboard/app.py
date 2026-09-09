import streamlit as st

from utils.database import load_sales_data
from views.executive_dashboard import show_executive_dashboard


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
    st.error(
        f"Gagal terhubung ke database: {e}"
    )

    st.stop()


# ==========================================
# HEADER
# ==========================================

st.title("📊 E-Commerce Executive Dashboard")

st.caption(
    "Monitoring Penjualan, Customer Analytics, dan Forecasting"
)


# ==========================================
# NAVIGATION
# ==========================================

tab1, tab2, tab3 = st.tabs([
    "📈 Executive Dashboard",
    "👥 Customer Segmentation",
    "🔮 Sales Forecasting"
])


# ==========================================
# TAB 1
# ==========================================

with tab1:

    show_executive_dashboard(df)


# ==========================================
# TAB 2
# ==========================================

with tab2:

    st.header("Customer Segmentation")

    st.info(
        "Modul Customer Segmentation akan menggunakan "
        "RFM Analysis dan K-Means Clustering."
    )


# ==========================================
# TAB 3
# ==========================================

with tab3:

    st.header("Sales Forecasting")

    st.info(
        "Modul Forecasting akan diimplementasikan "
        "menggunakan Time Series Analysis."
    )