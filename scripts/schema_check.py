import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw"


files_to_check = [
    "AprilSales2024_public.xlsx",       # Reference
    "DecemberSales2024_public.xlsx",
    "JulySales2025_public.xlsx",
    "SeptemberSales2024_public.xlsx"
]


for file_name in files_to_check:

    file_path = RAW_DATA_PATH / file_name

    print("\n" + "=" * 80)
    print(f"FILE: {file_name}")
    print("=" * 80)

    df = pd.read_excel(file_path)

    print(f"\nSHAPE: {df.shape}")

    print("\nKOLOM:")

    for i, column in enumerate(df.columns, start=1):
        print(f"{i}. {column}")

    print("\nPREVIEW:")

    print(df.head(3).to_string())