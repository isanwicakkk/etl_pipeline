import streamlit as st
import plotly.express as px

from utils.helpers import (
    format_rupiah,
    get_unique_orders,
    get_success_orders,
    filter_by_date,
    calculate_kpi
)


def show_executive_dashboard(df):

    st.header("Executive KPI & Trends")

    if df.empty:
        st.warning("Data tidak tersedia.")
        return

    # ==========================================
    # FILTER TANGGAL
    # ==========================================

    min_date = df[
        "waktu_pesanan_dibuat"
    ].min().date()

    max_date = df[
        "waktu_pesanan_dibuat"
    ].max().date()

    date_range = st.sidebar.date_input(
        "Rentang Tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:

        start_date, end_date = date_range

        df = filter_by_date(
            df,
            start_date,
            end_date
        )

    # ==========================================
    # FILTER STATUS
    # ==========================================

    status_options = sorted(
        df["status_pesanan"]
        .dropna()
        .unique()
    )

    selected_status = st.sidebar.multiselect(
        "Status Pesanan",
        options=status_options,
        default=status_options
    )

    df = df[
        df["status_pesanan"].isin(
            selected_status
        )
    ]

    # ==========================================
    # FILTER PROVINSI
    # ==========================================

    province_options = sorted(
        df["provinsi"]
        .dropna()
        .unique()
    )

    selected_province = st.sidebar.multiselect(
        "Provinsi",
        options=province_options,
        default=province_options
    )

    df = df[
        df["provinsi"].isin(
            selected_province
        )
    ]

    # ==========================================
    # PREPARE DATA
    # ==========================================

    df_unique = get_unique_orders(df)

    df_success = get_success_orders(df_unique)

    # ==========================================
    # KPI
    # ==========================================

    kpi = calculate_kpi(df)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Revenue",
        format_rupiah(kpi["total_revenue"])
    )

    col2.metric(
        "Total Pesanan",
        f'{kpi["total_orders"]:,}'
    )

    col3.metric(
        "Average Order Value",
        format_rupiah(kpi["aov"])
    )

    col4.metric(
        "Cancellation Rate",
        f'{kpi["cancellation_rate"]:.2f}%'
    )

    # ==========================================
    # MONTHLY SALES
    # ==========================================

    st.subheader("Tren Pendapatan Bulanan")

    if not df_success.empty:

        df_success["bulan"] = (
            df_success[
                "waktu_pesanan_dibuat"
            ]
            .dt.to_period("M")
            .astype(str)
        )

        monthly_sales = (
            df_success
            .groupby("bulan")
            .agg(
                total_revenue=(
                    "total_pembayaran",
                    "sum"
                ),

                total_orders=(
                    "order_id",
                    "nunique"
                )
            )
            .reset_index()
        )

        fig = px.line(
            monthly_sales,
            x="Bulan",
            y="Total Revenue",
            markers=True,
            hover_data=["total_orders"]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ==========================================
    # PRODUCT ANALYSIS
    # ==========================================

    st.subheader("Analisis Produk")

    product_sales = (
        df_success
        .groupby("product_category")
        .agg(
            total_revenue=(
                "total_pembayaran",
                "sum"
            ),

            total_orders=(
                "order_id",
                "nunique"
            ),

            total_quantity=(
                "jumlah",
                "sum"
            )
        )
        .reset_index()
        .sort_values(
            "total_revenue",
            ascending=False
        )
    )

    fig = px.bar(
        product_sales,
        x="Kategori Produk",
        y="Total Revenue",
        title="Revenue Berdasarkan Produk"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ==========================================
    # PROVINCE ANALYSIS
    # ==========================================

    st.subheader("Top Provinsi")

    province_sales = (
        df_success
        .groupby("provinsi")
        .agg(
            total_revenue=(
                "total_pembayaran",
                "sum"
            ),

            total_orders=(
                "order_id",
                "nunique"
            )
        )
        .reset_index()
        .sort_values(
            "total_revenue",
            ascending=False
        )
        .head(10)
    )

    fig = px.bar(
        province_sales,
        x="Provinsi",
        y="Total Revenue",
        title="Top 10 Provinsi"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )