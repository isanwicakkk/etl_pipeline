import plotly.express as px
import streamlit as st

from utils.helpers import (
    calculate_kpi,
    filter_by_date,
    format_rupiah,
    get_success_orders,
    get_unique_orders,
)


def show_executive_dashboard(df):
    st.header("Executive KPI & Trends")

    if df.empty:
        st.warning("Data tidak tersedia.")
        return

    # ==========================================
    # FILTER TANGGAL
    # ==========================================
    min_date = df["waktu_pesanan_dibuat"].min().date()
    max_date = df["waktu_pesanan_dibuat"].max().date()

    date_range = st.sidebar.date_input(
        "Rentang Tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
        df = filter_by_date(df, start_date, end_date)

    # ==========================================
    # FILTER STATUS
    # ==========================================
    status_options = sorted(df["status_pesanan"].dropna().unique())
    selected_status = st.sidebar.multiselect(
        "Status Pesanan", options=status_options, default=status_options
    )
    df = df[df["status_pesanan"].isin(selected_status)]

    # ==========================================
    # FILTER PROVINSI
    # ==========================================
    province_options = sorted(df["provinsi"].dropna().unique())
    selected_province = st.sidebar.multiselect(
        "Provinsi", options=province_options, default=province_options
    )
    df = df[df["provinsi"].isin(selected_province)]

    # ==========================================
    # PREPARE DATA
    # ==========================================
    df_unique = get_unique_orders(df)
    df_success = get_success_orders(df_unique)

    # ==========================================
    # KPI METRICS
    # ==========================================
    kpi = calculate_kpi(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", format_rupiah(kpi["total_revenue"]))
    col2.metric("Total Pesanan", f'{kpi["total_orders"]:,}')
    col3.metric("Average Order Value", format_rupiah(kpi["aov"]))
    col4.metric("Cancellation Rate", f'{kpi["cancellation_rate"]:.2f}%')

    # ==========================================
    # MONTHLY SALES TREND
    # ==========================================
    st.subheader("Tren Pendapatan Bulanan")

    if not df_success.empty:
        df_success["bulan"] = (
            df_success["waktu_pesanan_dibuat"].dt.to_period("M").astype(str)
        )

        monthly_sales = (
            df_success.groupby("bulan")
            .agg(
                total_revenue=("total_pembayaran", "sum"),
                total_orders=("order_id", "nunique"),
            )
            .reset_index()
        )

        # Cek jika data bulanan ada isi barisnya
        if not monthly_sales.empty:
            fig_line = px.line(
                monthly_sales,
                x="bulan",
                y="total_revenue",
                markers=True,
                hover_data=["total_orders"],
                labels={
                    "bulan": "Bulan",
                    "total_revenue": "Total Revenue (Rp)",
                    "total_orders": "Total Pesanan",
                },
                title="Tren Pendapatan Bulanan",
            )
            fig_line.update_traces(
                line_color="#1f77b4", line_width=3, marker_size=8
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Tidak ada data transaksi sukses pada periode ini.")

    # ==========================================
    # PRODUCT ANALYSIS
    # ==========================================
    st.subheader("Analisis Produk")

    if not df_success.empty:
        product_sales = (
            df_success.groupby("product_category")
            .agg(
                total_revenue=("total_pembayaran", "sum"),
                total_orders=("order_id", "nunique"),
                total_quantity=("jumlah", "sum"),
            )
            .reset_index()
            .sort_values("total_revenue", ascending=False)
        )

        if not product_sales.empty:
            fig_prod = px.bar(
                product_sales,
                x="product_category",
                y="total_revenue",
                text="total_revenue",  # Menampilkan angka nilai revenue
                title="Revenue Berdasarkan Produk",
                labels={
                    "product_category": "Kategori Produk",
                    "total_revenue": "Total Revenue (Rp)",
                },
            )
            # Format tampilan angka di dalam/atas bar chart
            fig_prod.update_traces(
                texttemplate="Rp %{text:,.0f}",
                textposition="outside",
            )
            fig_prod.update_layout(yaxis=dict(title="Revenue (Rp)"))
            st.plotly_chart(fig_prod, use_container_width=True)

    # ==========================================
    # PROVINCE ANALYSIS
    # ==========================================
    st.subheader("Top 10 Provinsi")

    if not df_success.empty:
        province_sales = (
            df_success.groupby("provinsi")
            .agg(
                total_revenue=("total_pembayaran", "sum"),
                total_orders=("order_id", "nunique"),
            )
            .reset_index()
            .sort_values("total_revenue", ascending=False)
            .head(10)
        )

        if not province_sales.empty:
            fig_prov = px.bar(
                province_sales,
                x="provinsi",
                y="total_revenue",
                text="total_revenue",  # Menampilkan angka nilai revenue
                title="Top 10 Provinsi Berdasarkan Revenue",
                labels={
                    "provinsi": "Provinsi",
                    "total_revenue": "Total Revenue (Rp)",
                },
            )
            # Format tampilan angka di dalam/atas bar chart
            fig_prov.update_traces(
                texttemplate="Rp %{text:,.0f}",
                textposition="outside",
            )
            fig_prov.update_layout(yaxis=dict(title="Revenue (Rp)"))
            st.plotly_chart(fig_prov, use_container_width=True)