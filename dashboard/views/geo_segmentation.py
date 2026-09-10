import streamlit as st
import plotly.express as px


def format_rupiah(value):
    return f"Rp {value:,.0f}".replace(",", ".")


def render_geo_segmentation(df):
    st.header("Geo Segmentation")
    st.caption(
        "Segmentasi wilayah berdasarkan revenue, jumlah pesanan, kuantitas, "
        "Average Order Value (AOV), dan tingkat pembatalan."
    )

    # ==========================================
    # VALIDASI DATA
    # ==========================================

    if df is None or df.empty:
        st.warning("Data Geo Segmentation belum tersedia.")
        return

    required_columns = [
        "provinsi",
        "segment",
        "total_revenue",
        "total_orders",
        "total_quantity",
        "average_order_value",
        "cancellation_rate"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        st.error(
            f"Kolom berikut tidak ditemukan: {', '.join(missing_columns)}"
        )
        return

    # ==========================================
    # FILTER
    # ==========================================

    st.subheader("Filter Analisis")

    available_segments = sorted(df["segment"].dropna().unique())

    selected_segments = st.multiselect(
        "Pilih Segment",
        options=available_segments,
        default=available_segments
    )

    if not selected_segments:
        st.warning("Pilih minimal satu segment.")
        return

    filtered_df = df[
        df["segment"].isin(selected_segments)
    ].copy()

    # ==========================================
    # KPI
    # ==========================================

    total_regions = filtered_df["provinsi"].nunique()
    total_segments = filtered_df["segment"].nunique()

    total_revenue = filtered_df["total_revenue"].sum()

    avg_cancellation = (
        filtered_df["cancellation_rate"].mean()
    )

    top_region = (
        filtered_df
        .sort_values("total_revenue", ascending=False)
        .iloc[0]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Provinsi",
        f"{total_regions:,}"
    )

    col2.metric(
        "Total Revenue",
        format_rupiah(total_revenue)
    )

    col3.metric(
        "Top Province",
        top_region["provinsi"]
    )

    col4.metric(
        "Avg Cancellation",
        f"{avg_cancellation:.2f}%"
    )

    st.divider()

    # ==========================================
    # BUSINESS INSIGHT
    # ==========================================

    st.subheader("Geo Performance Insight")

    top_revenue_region = (
        filtered_df
        .sort_values("total_revenue", ascending=False)
        .iloc[0]
    )

    highest_cancel_region = (
        filtered_df
        .sort_values("cancellation_rate", ascending=False)
        .iloc[0]
    )

    best_aov_region = (
        filtered_df
        .sort_values("average_order_value", ascending=False)
        .iloc[0]
    )

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    insight_col1.info(
        f"**Market Terbesar**\n\n"
        f"{top_revenue_region['provinsi']}\n\n"
        f"Revenue: {format_rupiah(top_revenue_region['total_revenue'])}"
    )

    insight_col2.success(
        f"**AOV Tertinggi**\n\n"
        f"{best_aov_region['provinsi']}\n\n"
        f"AOV: {format_rupiah(best_aov_region['average_order_value'])}"
    )

    insight_col3.warning(
        f"**Cancellation Tertinggi**\n\n"
        f"{highest_cancel_region['provinsi']}\n\n"
        f"Rate: {highest_cancel_region['cancellation_rate']:.2f}%"
    )

    st.divider()

    # ==========================================
    # DISTRIBUSI SEGMENT
    # ==========================================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribusi Segment Wilayah")

        segment_distribution = (
            filtered_df["segment"]
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
            color="segment",
            text="total_provinces",
            title="Jumlah Provinsi per Segment",
            labels={
                "segment": "Segment",
                "total_provinces": "Jumlah Provinsi"
            }
        )

        fig_segment.update_traces(
            textposition="outside"
        )

        fig_segment.update_layout(
            showlegend=False,
            margin=dict(t=50, l=20, r=20, b=20)
        )

        st.plotly_chart(
            fig_segment,
            use_container_width=True
        )

    with col2:
        st.subheader("Top Revenue per Provinsi")

        top_revenue = (
            filtered_df
            .sort_values("total_revenue", ascending=False)
            .head(10)
            .sort_values("total_revenue")
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
            showlegend=False,
            margin=dict(t=50, l=20, r=20, b=20)
        )

        st.plotly_chart(
            fig_revenue,
            use_container_width=True
        )

    st.divider()

    # ==========================================
    # CLUSTER VISUALIZATION
    # ==========================================

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("Visualisasi Cluster Wilayah")

        fig_cluster = px.scatter(
            filtered_df,
            x="total_orders",
            y="total_revenue",
            size="total_quantity",
            color="segment",
            hover_name="provinsi",
            hover_data={
                "average_order_value": ":,.0f",
                "cancellation_rate": ":.2f",
                "total_orders": True,
                "total_quantity": True
            },
            title="Geo Market Clustering",
            labels={
                "total_orders": "Total Orders",
                "total_revenue": "Total Revenue (Rp)",
                "total_quantity": "Total Quantity"
            }
        )

        fig_cluster.update_layout(
            margin=dict(t=50, l=20, r=20, b=20)
        )

        st.plotly_chart(
            fig_cluster,
            use_container_width=True
        )

    with col2:
        st.subheader("Rangkuman Performa Segment")

        segment_summary = (
            filtered_df
            .groupby("segment")
            .agg(
                total_provinsi=("provinsi", "nunique"),
                total_revenue=("total_revenue", "sum"),
                avg_aov=("average_order_value", "mean"),
                avg_cancellation=("cancellation_rate", "mean")
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
                    "Total Revenue",
                    format="Rp %d"
                ),

                "avg_aov": st.column_config.NumberColumn(
                    "Avg AOV",
                    format="Rp %d"
                ),

                "avg_cancellation": st.column_config.NumberColumn(
                    "Avg Cancel (%)",
                    format="%.2f%%"
                )
            },
            hide_index=True,
            use_container_width=True
        )

    st.divider()

    # ==========================================
    # PERFORMANCE ANALYSIS
    # ==========================================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("AOV vs Cancellation Rate")

        fig_performance = px.scatter(
            filtered_df,
            x="average_order_value",
            y="cancellation_rate",
            color="segment",
            size="total_revenue",
            hover_name="provinsi",
            hover_data={
                "total_revenue": ":,.0f",
                "total_orders": True
            },
            title="Korelasi AOV dan Cancellation Rate",
            labels={
                "average_order_value": "Average Order Value (Rp)",
                "cancellation_rate": "Cancellation Rate (%)"
            }
        )

        fig_performance.update_layout(
            margin=dict(t=50, l=20, r=20, b=20)
        )

        st.plotly_chart(
            fig_performance,
            use_container_width=True
        )

    with col2:
        st.subheader("Top Cancellation Rate")

        top_cancel = (
            filtered_df
            .sort_values("cancellation_rate", ascending=False)
            .head(10)
            .sort_values("cancellation_rate")
        )

        fig_cancel = px.bar(
            top_cancel,
            x="cancellation_rate",
            y="provinsi",
            orientation="h",
            color="segment",
            text="cancellation_rate",
            title="Top 10 Provinsi dengan Cancellation Rate Tertinggi",
            labels={
                "cancellation_rate": "Cancellation Rate (%)",
                "provinsi": "Provinsi"
            }
        )

        fig_cancel.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig_cancel.update_layout(
            showlegend=False,
            margin=dict(t=50, l=20, r=20, b=20)
        )

        st.plotly_chart(
            fig_cancel,
            use_container_width=True
        )

    st.divider()

    # ==========================================
    # DETAIL TABLE
    # ==========================================

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
        filtered_df[display_columns]
        .sort_values("total_revenue", ascending=False)
        .copy()
    )

    st.dataframe(
        df_display,
        column_config={
            "provinsi": "Provinsi",
            "segment": "Segment",

            "total_revenue": st.column_config.NumberColumn(
                "Total Revenue",
                format="Rp %d"
            ),

            "total_orders": st.column_config.NumberColumn(
                "Total Orders"
            ),

            "total_quantity": st.column_config.NumberColumn(
                "Total Quantity"
            ),

            "average_order_value": st.column_config.NumberColumn(
                "AOV",
                format="Rp %d"
            ),

            "cancellation_rate": st.column_config.NumberColumn(
                "Cancellation Rate",
                format="%.2f%%"
            )
        },
        hide_index=True,
        use_container_width=True
    )