import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.helpers import (
    calculate_kpi,
    filter_by_date,
    format_rupiah,
    get_success_orders,
    get_unique_orders,
)


def show_executive_dashboard(df):
    st.header("Executive KPI & Deep-DIVE Insights")

    if df.empty:
        st.warning("Data tidak tersedia.")
        return

    # ==========================================
    # FILTER TANGGAL, STATUS, PROVINSI
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

    status_options = sorted(df["status_pesanan"].dropna().unique())
    selected_status = st.sidebar.multiselect(
        "Status Pesanan", options=status_options, default=status_options
    )
    df = df[df["status_pesanan"].isin(selected_status)]

    province_options = sorted(df["provinsi"].dropna().unique())
    selected_province = st.sidebar.multiselect(
        "Provinsi", options=province_options, default=province_options
    )
    df = df[df["provinsi"].isin(selected_province)]

    # PREPARE DATA
    df_unique = get_unique_orders(df)
    df_success = get_success_orders(df_unique)

    # ==========================================
    # 1. ENHANCED KPI METRICS (DENGAN LOST REVENUE)
    # ==========================================
    kpi = calculate_kpi(df)

    # Hitung Lost Revenue akibat pembatalan
    df_cancelled = df_unique[
        df_unique["status_pesanan"].astype(str).str.contains("Batal|Cancel", case=False, na=False)
    ]
    lost_revenue = df_cancelled["total_pembayaran"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Revenue", format_rupiah(kpi["total_revenue"]))
    col2.metric("Total Pesanan", f'{kpi["total_orders"]:,}')
    col3.metric("Average Order Value", format_rupiah(kpi["aov"]))
    col4.metric("Cancellation Rate", f'{kpi["cancellation_rate"]:.2f}%')
    col5.metric(
        "Lost Revenue (Batal)",
        format_rupiah(lost_revenue),
        delta=f"-{len(df_cancelled)} Pesanan",
        delta_color="inverse",
    )

    st.markdown("---")

    # ==========================================
    # 2. TREN REVENUE & MOM GROWTH
    # ==========================================
    st.subheader("1. Tren Pendapatan & Pertumbuhan Bulanan")

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

        if not monthly_sales.empty:
            # Hitung Growth MoM (%)
            monthly_sales["mom_growth"] = (
                monthly_sales["total_revenue"].pct_change() * 100
            )

            fig_line = px.line(
                monthly_sales,
                x="bulan",
                y="total_revenue",
                markers=True,
                hover_data=["total_orders", "mom_growth"],
                labels={
                    "bulan": "Bulan",
                    "total_revenue": "Revenue (Rp)",
                    "total_orders": "Total Pesanan",
                    "mom_growth": "Pertumbuhan MoM (%)",
                },
                title="Tren Revenue Bulanan",
            )
            fig_line.update_traces(line_color="#0068C9", line_width=3, marker_size=8)
            st.plotly_chart(fig_line, use_container_width=True)

    # ==========================================
    # 3. ANALISIS LOSS: ALASAN PEMBATALAN PESANAN
    # ==========================================
    st.subheader("2. Analisis Potensi Kerugian & Pembatalan")

    col_cancel1, col_cancel2 = st.columns(2)

    with col_cancel1:
        if not df_cancelled.empty and "alasan_pembatalan" in df_cancelled.columns:
            cancel_reasons = (
                df_cancelled.groupby("alasan_pembatalan")
                .agg(
                    total_lost=("total_pembayaran", "sum"),
                    total_cases=("order_id", "nunique"),
                )
                .reset_index()
                .sort_values("total_cases", ascending=False)
                .head(7)
            )

            fig_cancel = px.bar(
                cancel_reasons,
                y="alasan_pembatalan",
                x="total_cases",
                orientation="h",
                title="Top Alasan Pembatalan Pesanan",
                labels={
                    "alasan_pembatalan": "Alasan Batal",
                    "total_cases": "Jumlah Kasus",
                },
                color="total_cases",
                color_continuous_scale="Reds",
            )
            fig_cancel.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_cancel, use_container_width=True)

    with col_cancel2:
        # Return Rate per Kategori Produk
        if not df.empty and "returned_quantity" in df.columns:
            df_returns = (
                df.groupby("product_category")
                .agg(
                    total_sold=("jumlah", "sum"),
                    total_returned=("returned_quantity", "sum"),
                )
                .reset_index()
            )
            df_returns["return_rate"] = (
                df_returns["total_returned"] / df_returns["total_sold"]
            ) * 100
            df_returns = df_returns.sort_values(
                "return_rate", ascending=False
            ).head(7)

            fig_return = px.bar(
                df_returns,
                x="product_category",
                y="return_rate",
                title="Top Kategori dengan Return Rate Tergi ( % )",
                text="return_rate",
                labels={
                    "product_category": "Kategori",
                    "return_rate": "Return Rate (%)",
                },
                color="return_rate",
                color_continuous_scale="Oranges",
            )
            fig_return.update_traces(
                texttemplate="%{text:.2f}%", textposition="outside"
            )
            st.plotly_chart(fig_return, use_container_width=True)

    # ==========================================
    # 4. ANALISIS BEBAN LOGISTIK & SUBSIDI ONGKIR
    # ==========================================
    st.subheader("3. Analisis Beban Logistik & Subsidized Shipping")

    if not df_success.empty and "estimasi_potongan_biaya_pengiriman" in df_success.columns:
        shipping_summary = (
            df_success.groupby("opsi_pengiriman")
            .agg(
                ongkir_pembeli=("ongkos_kirim_dibayar_oleh_pembeli", "sum"),
                subsidi_ongkir=("estimasi_potongan_biaya_pengiriman", "sum"),
                total_orders=("order_id", "nunique"),
            )
            .reset_index()
            .sort_values("total_orders", ascending=False)
        )

        fig_ship = go.Figure(
            data=[
                go.Bar(
                    name="Ongkir Dibayar Pembeli",
                    x=shipping_summary["opsi_pengiriman"],
                    y=shipping_summary["ongkir_pembeli"],
                    marker_color="#2CA02C",
                ),
                go.Bar(
                    name="Subsidi/Potongan Ongkir",
                    x=shipping_summary["opsi_pengiriman"],
                    y=shipping_summary["subsidi_ongkir"],
                    marker_color="#D62728",
                ),
            ]
        )
        fig_ship.update_layout(
            barmode="group",
            title="Perbandingan Ongkir Pembeli vs Subsidi Toko per Kurir",
            xaxis_title="Opsi Pengiriman",
            yaxis_title="Total Nilai (Rp)",
        )
        st.plotly_chart(fig_ship, use_container_width=True)

    # ==========================================
    # 5. EXECUTIVE SUMMARY & STRATEGIC RECOMMENDATIONS
    # ==========================================
    st.subheader("4. Executive Summary & Action Plan")

    st.info(
        f"""
        **Insight Utama:**
        1. **Efisiensi Pendapatan:** Total potensi pendapatan yang hilang akibat pembatalan adalah **{format_rupiah(lost_revenue)}**.
        2. **Perilaku Pengiriman:** Evaluasi opsi pengiriman dengan beban subsidi tertinggi untuk memastikan margin produk tetap sehat.
        3. **Rekomendasi Tindakan:**
            * Optimalkan stok pada kategori dengan *Return Rate* tinggi untuk mengurangi komplain pelanggan.
            * Tinjau kembali syarat minimum transaksi untuk pemberian promo subsidi ongkir.
        """
    )