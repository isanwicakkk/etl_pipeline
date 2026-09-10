import sys
import joblib
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.sales_forecasting.predict import generate_forecast

MODEL_DIR = BASE_DIR / "ml" / "sales_forecasting" / "models"


@st.cache_data
def load_forecasting_data():
    daily_path = MODEL_DIR / "daily_revenue.csv"
    metrics_path = MODEL_DIR / "metrics.pkl"
    model_name_path = MODEL_DIR / "model_name.pkl"

    if not daily_path.exists():
        raise FileNotFoundError(
            "daily_revenue.csv belum ditemukan. Jalankan training terlebih dahulu."
        )

    daily_df = pd.read_csv(daily_path)
    daily_df["date"] = pd.to_datetime(daily_df["date"])

    metrics = joblib.load(metrics_path) if metrics_path.exists() else {}
    model_name = joblib.load(model_name_path) if model_name_path.exists() else "Unknown"

    return daily_df, metrics, model_name


def format_rupiah(value):
    return f"Rp {value:,.0f}"


def render_sales_forecasting():
    st.header("Sales Forecasting")
    st.caption(
        "Prediksi revenue penjualan berdasarkan data historis "
        "menggunakan Machine Learning Time Series Forecasting."
    )

    try:
        daily_df, metrics, model_name = load_forecasting_data()
    except Exception as e:
        st.error(f"Gagal memuat forecasting data: {e}")
        st.info("Jalankan training terlebih dahulu:\n\npython -m ml.sales_forecasting.train")
        return

    # Model information
    st.subheader("Model Performance")

    mae = metrics.get("mae", 0)
    rmse = metrics.get("rmse", 0)
    mape = metrics.get("mape", 0)
    wmape = metrics.get("wmape", 0)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Model", model_name)
    col2.metric("MAE", format_rupiah(mae))
    col3.metric("RMSE", format_rupiah(rmse))
    col4.metric("MAPE", f"{mape:.2f}%")
    col5.metric("WMAPE", f"{wmape:.2f}%")

    st.divider()

    # Forecast control
    st.subheader("Forecast Configuration")
    forecast_days = st.radio(
        "Pilih periode forecasting:",
        options=[7, 14, 30],
        horizontal=True,
        index=0
    )

    try:
        forecast_df = generate_forecast(days=forecast_days)
    except Exception as e:
        st.error(f"Gagal membuat forecast: {e}")
        return

    # Forecast KPI
    total_forecast = forecast_df["forecast_revenue"].sum()
    average_forecast = forecast_df["forecast_revenue"].mean()
    max_forecast_row = forecast_df.loc[forecast_df["forecast_revenue"].idxmax()]
    min_forecast_row = forecast_df.loc[forecast_df["forecast_revenue"].idxmin()]

    st.subheader(f"Forecast {forecast_days} Hari")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Forecast", format_rupiah(total_forecast))
    col2.metric("Average Daily", format_rupiah(average_forecast))
    col3.metric("Highest Forecast", format_rupiah(max_forecast_row["forecast_revenue"]))
    col4.metric("Lowest Forecast", format_rupiah(min_forecast_row["forecast_revenue"]))

    st.divider()

    # Historical vs forecast
    st.subheader("Historical Revenue vs Forecast")

    historical_days = st.slider(
        "Jumlah data historis yang ditampilkan:",
        min_value=30,
        max_value=min(365, len(daily_df)),
        value=min(90, len(daily_df))
    )

    historical_df = daily_df.tail(historical_days).copy()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=historical_df["date"],
        y=historical_df["revenue"],
        mode="lines",
        name="Historical Revenue"
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=forecast_df["forecast_revenue"],
        mode="lines+markers",
        name="Forecast Revenue"
    ))
    fig.update_layout(
        title="Historical Revenue vs Forecast",
        xaxis_title="Date",
        yaxis_title="Revenue (Rp)",
        hovermode="x unified",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Forecast daily chart
    col_chart, col_summary = st.columns([2, 1])

    with col_chart:
        st.subheader("Daily Forecast Revenue")

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=forecast_df["date"],
            y=forecast_df["forecast_revenue"],
            name="Forecast"
        ))
        fig_bar.update_layout(
            title=f"Forecast Revenue {forecast_days} Hari",
            xaxis_title="Date",
            yaxis_title="Forecast Revenue (Rp)",
            height=400
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    with col_summary:
        st.subheader("Forecast Summary")

        start_date = forecast_df["date"].min()
        end_date = forecast_df["date"].max()

        st.info(
            f"**Forecast Period**\n\n"
            f"Start:\n{start_date.strftime('%d %B %Y')}\n\n"
            f"End:\n{end_date.strftime('%d %B %Y')}\n\n"
            f"Duration:\n{forecast_days} Days"
        )

        st.success(f"**Expected Revenue**\n\n{format_rupiah(total_forecast)}")

    st.divider()

    # Forecast table
    st.subheader("Forecast Detail")

    display_df = forecast_df.copy()
    display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%d-%m-%Y")
    display_df["forecast_revenue"] = display_df["forecast_revenue"].round(0)
    display_df = display_df.rename(columns={
        "date": "Tanggal",
        "forecast_revenue": "Forecast Revenue"
    })

    st.dataframe(
        display_df,
        column_config={
            "Tanggal": st.column_config.TextColumn("Tanggal"),
            "Forecast Revenue": st.column_config.NumberColumn(
                "Forecast Revenue", format="Rp %d"
            )
        },
        hide_index=True,
        use_container_width=True
    )

    # Download
    csv_data = forecast_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Forecast CSV",
        data=csv_data,
        file_name=f"sales_forecast_{forecast_days}_days.csv",
        mime="text/csv"
    )