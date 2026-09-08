import pandas as pd
from pathlib import Path


# =====================================
# PATH CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "combined_sales.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "clean_sales.csv"
)


# =====================================
# LOAD DATA
# =====================================

print("=" * 70)
print("DATA CLEANING")
print("=" * 70)

df = pd.read_csv(INPUT_PATH)

print(f"\nData awal: {df.shape}")


# =====================================
# 1. REMOVE EXACT DUPLICATES
# =====================================

before_rows = len(df)

df = df.drop_duplicates()

after_rows = len(df)

print("\n1. EXACT DUPLICATE CHECK")
print(f"Rows sebelum cleaning : {before_rows}")
print(f"Rows sesudah cleaning : {after_rows}")
print(f"Rows dihapus          : {before_rows - after_rows}")


# =====================================
# 2. CLEAN CANCEL REASON
# =====================================

df["Alasan Pembatalan"] = (
    df["Alasan Pembatalan"]
    .fillna("Tidak Dibatalkan")
)

print("\n2. ALASAN PEMBATALAN")
print("Missing value telah distandarisasi")


# =====================================
# 3. CLEAN RETURNED QUANTITY
# =====================================

df["Returned quantity"] = (
    df["Returned quantity"]
    .fillna(0)
)

df["Returned quantity"] = pd.to_numeric(
    df["Returned quantity"],
    errors="coerce"
)

print("\n3. RETURNED QUANTITY")
print("Missing value diisi dengan 0")


# =====================================
# 4. CONVERT & CLEAN DATE
# =====================================

df["Waktu Pesanan Dibuat"] = pd.to_datetime(
    df["Waktu Pesanan Dibuat"],
    errors="coerce"
)

missing_date = df["Waktu Pesanan Dibuat"].isna().sum()

# Drop baris dengan tanggal missing/invalid
df = df.dropna(subset=["Waktu Pesanan Dibuat"])

print("\n4. DATE CONVERSION & CLEANING")
print(f"Invalid/missing date dihapus : {missing_date}")
print(f"Rows setelah drop date invalid: {len(df)}")


# =====================================
# 5. STANDARDIZE STATUS PESANAN
# =====================================

def categorize_status(status):
    if pd.isna(status):
        return "Lainnya"
    
    status_str = str(status).strip()
    
    if "Selesai" in status_str or "Pesanan diterima" in status_str:
        return "Selesai"
    elif "Batal" in status_str:
        return "Batal"
    elif "Dikirim" in status_str:
        return "Sedang Dikirim"
    else:
        return "Lainnya"

if "Status Pesanan" in df.columns:
    df["status_pesanan_clean"] = df["Status Pesanan"].apply(categorize_status)

print("\n5. STATUS PESANAN")
print("Status pesanan berhasil dikategorikan ke status_pesanan_clean")


# =====================================
# 6. ADD DATE FEATURES
# =====================================

df["order_year"] = (
    df["Waktu Pesanan Dibuat"].dt.year
)

df["order_month"] = (
    df["Waktu Pesanan Dibuat"].dt.month
)

df["order_date"] = (
    df["Waktu Pesanan Dibuat"].dt.date
)

print("\n6. DATE FEATURES")
print("order_year ditambahkan")
print("order_month ditambahkan")
print("order_date ditambahkan")


# =====================================
# 7. FINAL CHECK
# =====================================

print("\n" + "=" * 70)
print("FINAL DATA QUALITY CHECK")
print("=" * 70)

print(f"\nFinal rows    : {df.shape[0]}")
print(f"Final columns : {df.shape[1]}")

print("\nMissing Values:")

print(
    df.isnull()
    .sum()
    .sort_values(ascending=False)
)


# =====================================
# SAVE CLEAN DATA
# =====================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\n" + "=" * 70)
print("DATA CLEANING SELESAI")
print("=" * 70)

print(f"\nFile disimpan di:")
print(OUTPUT_PATH)