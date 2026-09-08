import pandas as pd
from pathlib import Path


# =====================================
# PATH
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "clean_sales.csv"
)


# =====================================
# LOAD DATA
# =====================================

df = pd.read_csv(INPUT_PATH)


numeric_columns = [
    "Jumlah",
    "Returned quantity",
    "Total Diskon",
    "Total Berat",
    "Ongkos Kirim Dibayar oleh Pembeli",
    "Estimasi Potongan Biaya Pengiriman",
    "Total Pembayaran",
    "Perkiraan Ongkos Kirim"
]


print("=" * 70)
print("NUMERIC DATA INVESTIGATION")
print("=" * 70)


for column in numeric_columns:

    print("\n" + "-" * 70)
    print(f"KOLOM: {column}")

    print("\nData Type:")
    print(df[column].dtype)

    print("\nSample Unique Values:")

    values = df[column].dropna().astype(str).unique()[:10]

    for value in values:
        print(value)


print("\n" + "=" * 70)