import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path


def render_geo_segmentation():

    st.header("Geo Segmentation")

    st.caption(
        "Analisis segmentasi wilayah berdasarkan performa penjualan, "
        "jumlah pesanan, kuantitas, AOV, dan cancellation rate."
    )

    # ============================================================
    # PATH
    # ============================================================

    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    DATA_PATH = (
        BASE_DIR
        / "ml"
        / "geo_segmentation"
        / "models"
        / "geo_segments.csv"
    )

    # ============================================================
    # CHECK FILE
    # ============================================================

    if not DATA_PATH.exists():

        st.error(
            "File Geo Segmentation belum ditemukan."
        )

        st.info(
            "Jalankan training terlebih dahulu:\n\n"
            "python -m ml.geo_segmentation.train"
        )

        return

    # ============================================================
    # LOAD DATA
    # ============================================================

    df = pd.read_csv(DATA_PATH)

    # ============================================================
    # KPI
    # ============================================================

    total_regions = df["provinsi"].nunique()

    total_segments = df["segment"].nunique()

    top_region = (
        df
        .sort_values(
            "total_revenue",
            ascending=False
        )
        .iloc[0]
    )

    top_segment = (
        df["segment"]
        .value_counts()
        .index[0]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Provinsi",
        f"{total_regions:,}"
    )

    col2.metric(
        "Total Segment",
        f"{total_segments}"
    )

    col3.metric(
        "Top Province",
        top_region["provinsi"]
    )

    col4.metric(
        "Largest Segment",
        top_segment
    )

    st.divider()

    # ============================================================
    # SEGMENT DISTRIBUTION
    # ============================================================

    # ============================================================
    # DISTRIBUSI SEGMENT & REVENUE BERDASARKAN PROVINSI (SIDE BY SIDE)
    # ============================================================

    col_geo1, col_geo2 = st.columns(2)

    with col_geo1:
        st.subheader("Distribusi Segment Wilayah")

        segment_distribution = (
            df["segment"]
            .value_counts()
            .reset_index()
        )
        segment_distribution.columns = [
            "segment",
            "total_provinces"
        ]

        fig_segment = px.bar(
            segment_distribution,
            x="segment",
            y="total_provinces",
            text="total_provinces",
            color="segment",
            title="Jumlah Provinsi per Segment",
            labels={
                "segment": "Segment",
                "total_provinces": "Jumlah Provinsi"
            }
        )
        fig_segment.update_traces(textposition="outside")
        fig_segment.update_layout(showlegend=False)

        st.plotly_chart(
            fig_segment,
            use_container_width=True
        )

    with col_geo2:
        st.subheader("Top 10 Revenue per Provinsi")

        top_revenue = (
            df
            .sort_values(
                "total_revenue",
                ascending=False
            )
            .head(10)
        )

        fig_revenue = px.bar(
            top_revenue,
            x="total_revenue",
            y="provinsi",
            orientation="h",
            color="segment",
            title="Top 10 Provinsi Berdasarkan Revenue",
            labels={
                "total_revenue": "Total Revenue (Rp)",
                "provinsi": "Provinsi"
            }
        )
        fig_revenue.update_layout(
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(
            fig_revenue,
            use_container_width=True
        )

    st.divider()

    # ============================================================
    # CLUSTER VISUALIZATION & DETAIL SUMMARY (SIDE BY SIDE)
    # ============================================================

    col_geo3, col_geo4 = st.columns(2)

    with col_geo3:
        st.subheader("Visualisasi Cluster Wilayah")

        fig_cluster = px.scatter(
            df,
            x="total_orders",
            y="total_revenue",
            size="total_quantity",
            color="segment",
            hover_name="provinsi",
            hover_data=[
                "average_order_value",
                "cancellation_rate"
            ],
            title="Product & Geo Clustering Scatter",
            labels={
                "total_orders": "Total Orders",
                "total_revenue": "Total Revenue (Rp)",
                "total_quantity": "Total Quantity"
            }
        )

        st.plotly_chart(
            fig_cluster,
            use_container_width=True
        )

    with col_geo4:
        st.subheader("Rangkuman Performa Segment")

        # Tabel ringkasan performa per segmen wilayah
        segment_summary = (
            df.groupby("segment")
            .agg(
                total_provinsi=("provinsi", "nunique"),
                total_revenue=("total_revenue", "sum"),
                avg_aov=("average_order_value", "mean")
            )
            .reset_index()
            .sort_values("total_revenue", ascending=False)
        )

        st.dataframe(
            segment_summary,
            column_config={
                "segment": "Segment",
                "total_provinsi": "Jumlah Wilayah",
                "total_revenue": st.column_config.NumberColumn(
                    "Total Revenue", format="Rp %d"
                ),
                "avg_aov": st.column_config.NumberColumn(
                    "Avg AOV", format="Rp %d"
                ),
            },
            hide_index=True,
            use_container_width=True
        )

    st.divider()

    # ============================================================
    # AOV VS CANCELLATION RATE & TOP CANCELLATION (SIDE BY SIDE)
    # ============================================================

    col_perf1, col_perf2 = st.columns(2)

    with col_perf1:
        st.subheader("AOV vs Cancellation Rate")

        fig_performance = px.scatter(
            df,
            x="average_order_value",
            y="cancellation_rate",
            color="segment",
            size="total_revenue",
            hover_name="provinsi",
            title="Korelasi AOV & Pembatalan",
            labels={
                "average_order_value": "Average Order Value (Rp)",
                "cancellation_rate": "Cancellation Rate (%)",
            },
        )

        st.plotly_chart(fig_performance, use_container_width=True)

    with col_perf2:
        st.subheader("Top 10 Cancellation Rate Wilayah")

        top_cancel = df.sort_values(
            "cancellation_rate", ascending=False
        ).head(10)

        fig_cancel_prov = px.bar(
            top_cancel,
            x="cancellation_rate",
            y="provinsi",
            orientation="h",
            color="segment",
            text="cancellation_rate",
            title="Top 10 Provinsi Tingkat Pembatalan Tinggi",
            labels={
                "cancellation_rate": "Cancellation Rate (%)",
                "provinsi": "Provinsi",
            },
        )

        fig_cancel_prov.update_traces(
            texttemplate="%{text:.2f}%", textposition="outside"
        )
        fig_cancel_prov.update_layout(
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(fig_cancel_prov, use_container_width=True)

    st.divider()

    # ============================================================
    # DETAIL TABLE
    # ============================================================

    st.subheader("Detail Geo Segmentation")

    display_columns = [
        "provinsi",
        "segment",
        "total_revenue",
        "total_orders",
        "total_quantity",
        "average_order_value",
        "cancellation_rate"
    ]

    df_display = (
        df[display_columns]
        .sort_values(
            "total_revenue",
            ascending=False
        )
        .copy()
    )

    df_display = df_display.rename(
        columns={
            "provinsi": "Provinsi",
            "segment": "Segment",
            "total_revenue": "Total Revenue",
            "total_orders": "Total Orders",
            "total_quantity": "Total Quantity",
            "average_order_value": "AOV",
            "cancellation_rate": "Cancellation Rate (%)"
        }
    )

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )