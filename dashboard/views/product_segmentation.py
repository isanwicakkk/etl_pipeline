import streamlit as st
import plotly.express as px


def render_product_segmentation(product_df):
    """
    Menampilkan dashboard Product Segmentation
    menggunakan hasil K-Means.
    """

    st.header("Product Segmentation")

    st.markdown(
        "Analisis performa kategori produk menggunakan "
        "Machine Learning K-Means Clustering."
    )

    if product_df.empty:
        st.warning("Data product segmentation tidak tersedia.")
        return

    # =====================================
    # KPI
    # =====================================

    total_products = product_df["product_category"].nunique()

    total_segments = product_df["segment"].nunique()

    best_seller_count = (
        product_df["segment"]
        .astype(str)
        .str.contains(
            "Best",
            case=False,
            na=False
        )
        .sum()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Product Categories",
        f"{total_products:,}"
    )

    col2.metric(
        "Total Segments",
        f"{total_segments:,}"
    )

    col3.metric(
        "Best Seller Products",
        f"{best_seller_count:,}"
    )


    # =====================================
    # FILTER
    # =====================================

    st.subheader("Filter Segment")

    segments = sorted(
        product_df["segment"]
        .dropna()
        .unique()
    )

    selected_segments = st.multiselect(
        "Pilih Product Segment",
        options=segments,
        default=segments
    )

    filtered_df = product_df[
        product_df["segment"].isin(selected_segments)
    ].copy()

    if filtered_df.empty:
        st.warning("Tidak ada data untuk segment yang dipilih.")
        return

    # =====================================
# =====================================
    # REVENUE BY SEGMENT & CLUSTER VISUALIZATION (SIDE BY SIDE)
    # =====================================

    col_seg1, col_seg2 = st.columns(2)

    with col_seg1:
        st.subheader("Revenue by Segment")

        revenue_segment = (
            filtered_df
            .groupby("segment", as_index=False)["total_revenue"]
            .sum()
            .sort_values("total_revenue", ascending=False)
        )

        fig_revenue = px.bar(
            revenue_segment,
            x="segment",
            y="total_revenue",
            color="segment",
            text="total_revenue",
            title="Total Revenue per Segment",
            labels={
                "segment": "Product Segment",
                "total_revenue": "Total Revenue (Rp)"
            }
        )

        fig_revenue.update_traces(
            texttemplate="Rp %{text:,.0f}", 
            textposition="outside"
        )
        fig_revenue.update_layout(showlegend=False)

        st.plotly_chart(
            fig_revenue,
            use_container_width=True
        )

    with col_seg2:
        st.subheader("K-Means Product Cluster")

        fig_cluster = px.scatter(
            filtered_df,
            x="total_orders",
            y="total_revenue",
            color="segment",
            size="total_quantity",
            hover_name="product_category",
            hover_data=[
                "average_order_value",
                "return_rate",
                "cluster"
            ],
            title="Product Category Clustering"
        )

        st.plotly_chart(
            fig_cluster,
            use_container_width=True
        )

    # =====================================
   # =====================================
    # PRODUCT PERFORMANCE & RETURN RATE (SIDE BY SIDE)
    # =====================================

    col_prod1, col_prod2 = st.columns(2)

    with col_prod1:
        st.subheader("Top 5 Product Revenue")

        df_top_revenue = filtered_df.sort_values(
            "total_revenue", ascending=False
        ).head(5)

        fig_product = px.bar(
            df_top_revenue,
            x="product_category",
            y="total_revenue",
            color="segment",
            text="total_revenue",
            hover_data=[
                "total_orders",
                "total_quantity",
                "return_rate",
            ],
            title="Top 5 Revenue per Category",
            labels={
                "product_category": "Kategori Produk",
                "total_revenue": "Revenue (Rp)",
            },
        )

        fig_product.update_traces(
            texttemplate="Rp %{text:,.0f}", textposition="outside"
        )
        fig_product.update_layout(xaxis_tickangle=-45)

        st.plotly_chart(fig_product, use_container_width=True)

    with col_prod2:
        st.subheader("Top 5 Product Return Rate")

        df_top_return = filtered_df.sort_values(
            "return_rate", ascending=False
        ).head(5)

        fig_return = px.bar(
            df_top_return,
            x="product_category",
            y="return_rate",
            color="segment",
            text="return_rate",
            title="Top 5 Return Rate per Category",
            labels={
                "product_category": "Kategori Produk",
                "return_rate": "Return Rate (%)",
            },
        )

        fig_return.update_traces(
            texttemplate="%{text:.2f}%", textposition="outside"
        )
        fig_return.update_layout(xaxis_tickangle=-45)

        st.plotly_chart(fig_return, use_container_width=True)

    # =====================================
    # DATA TABLE
    # =====================================

    st.subheader("Product Segmentation Detail")

    display_columns = [
        "product_category",
        "segment",
        "cluster",
        "total_revenue",
        "total_orders",
        "total_quantity",
        "average_order_value",
        "return_rate"
    ]

    display_df = (
        filtered_df[display_columns]
        .sort_values(
            "total_revenue",
            ascending=False
        )
        .copy()
    )

    column_mapping = {
        "product_category": "Product Category",
        "segment": "Product Segment",
        "cluster": "Cluster",
        "total_revenue": "Total Revenue",
        "total_orders": "Total Orders",
        "total_quantity": "Total Quantity",
        "average_order_value": "Average Order Value",
        "return_rate": "Return Rate (%)"
    }

    display_df = display_df.rename(
        columns=column_mapping
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )