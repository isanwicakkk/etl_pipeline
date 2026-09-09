import sys
from pathlib import Path
import joblib
import pandas as pd

# Menentukan BASE_DIR yang konsisten (3 tingkat ke atas dari predict.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "ml" / "geo_segmentation" / "models"

def load_geo_models():
    # Cek keberadaan file sebelum di-load
    model_path = MODEL_DIR / "kmeans_model.pkl"
    csv_path = MODEL_DIR / "geo_segments.csv"
    
    if not model_path.exists() or not csv_path.exists():
        raise FileNotFoundError(
            "File Geo Segmentation belum ditemukan.\n"
            "Jalankan training terlebih dahulu:\n"
            "python -m ml.geo_segmentation.train"
        )
        
    kmeans = joblib.load(model_path)
    scaler = joblib.load(MODEL_DIR / "scaler.pkl")
    feature_columns = joblib.load(MODEL_DIR / "feature_columns.pkl")
    cluster_mapping = joblib.load(MODEL_DIR / "cluster_mapping.pkl")
    df_geo_segments = pd.read_csv(csv_path)
    
    return kmeans, scaler, feature_columns, cluster_mapping, df_geo_segments