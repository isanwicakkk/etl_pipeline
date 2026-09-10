import streamlit as st
import plotly.express as px


def render_geo_segmentation(df):

    st.header("🗺️ Geo Segmentation")

    st.caption(
        "Analisis segmentasi wilayah berdasarkan performa penjualan, "
        "jumlah pesanan, kuantitas, AOV, dan cancellation rate."
    )

    # ==========================================
    # KPI
    # ==========================================

    total_regions = df["provinsi"].nunique()
    total_segments = df["segment"].nunique()

    top_region = (
        df.sort_values(
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
        total_segments
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

    # ==========================================
    # DISTRIBUTION
    # ==========================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Distribusi Segment")

        distribution = (
            df["segment"]
            .value_counts()
            .reset_index()
        )

        distribution.columns = [
            "segment",
            "total_provinces"
        ]

        fig = px.bar(
            distribution,
            x="segment",
            y="total_provinces",
            color="segment",
            text="total_provinces"
        )

        fig.update_layout(
            showlegend=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        st.subheader("Top Revenue Provinsi")

        top_revenue = (
            df.sort_values(
                "total_revenue",
                ascending=False
            )
            .head(10)
        )

        fig = px.bar(
            top_revenue,
            x="total_revenue",
            y="provinsi",
            color="segment",
            orientation="h"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # ==========================================
    # CLUSTER VISUALIZATION
    # ==========================================

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
        ]
    )

    st.plotly_chart(
        fig_cluster,
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

    st.dataframe(
        df[display_columns],
        use_container_width=True,
        hide_index=True
    )