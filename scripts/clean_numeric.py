import pandas as pd
import re
from pathlib import Path


# =====================================
# PATH CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "clean_sales.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_sales.csv"
)


# =====================================
# FUNCTION: CLEAN CURRENCY
# =====================================

def clean_currency(value):

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    # Hapus Rp dan spasi
    value = value.replace("Rp", "")
    value = value.replace("rp", "")
    value = value.replace(" ", "")

    # Hapus titik dan koma
    value = value.replace(".", "")
    value = value.replace(",", "")

    # Sisakan angka dan minus
    value = re.sub(r"[^\d-]", "", value)

    if value == "":
        return pd.NA

    return pd.to_numeric(value, errors="coerce")


# =====================================
# FUNCTION: CLEAN WEIGHT
# =====================================

def clean_weight(value):

    if pd.isna(value):
        return pd.NA

    value = str(value).lower().strip()

    # Ambil angka
    number = re.findall(r"[\d.,]+", value)

    if not number:
        return pd.NA

    number = number[0]

    # Normalisasi format angka
    number = number.replace(",", ".")

    try:
        number = float(number)
    except ValueError:
        return pd.NA

    # Konversi kg ke gram
    if "kg" in value:
        return number * 1000

    # Default gram
    return number


# =====================================
# LOAD DATA
# =====================================

print("=" * 70)
print("NUMERIC DATA CLEANING")
print("=" * 70)

df = pd.read_csv(INPUT_PATH)

print(f"\nData awal: {df.shape}")


# =====================================
# 1. QUANTITY
# =====================================

df["Jumlah"] = pd.to_numeric(
    df["Jumlah"],
    errors="coerce"
)

df["Returned quantity"] = pd.to_numeric(
    df["Returned quantity"],
    errors="coerce"
)


# =====================================
# 2. CURRENCY COLUMNS
# =====================================

currency_columns = [

    "Total Diskon",

    "Ongkos Kirim Dibayar oleh Pembeli",

    "Estimasi Potongan Biaya Pengiriman",

    "Total Pembayaran",

    "Perkiraan Ongkos Kirim"
]


print("\nCLEANING CURRENCY COLUMNS")

for column in currency_columns:

    if column in df.columns:

        print(f"Cleaning: {column}")

        df[column] = df[column].apply(
            clean_currency
        )


# =====================================
# 3. WEIGHT
# =====================================

print("\nCLEANING WEIGHT")

df["Total Berat"] = df["Total Berat"].apply(
    clean_weight
)


# =====================================
# 4. DATA TYPE CONVERSION
# =====================================

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


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# =====================================
# 5. CHECK FAILED CONVERSION
# =====================================

print("\n" + "=" * 70)
print("NUMERIC VALIDATION")
print("=" * 70)

for column in numeric_columns:

    missing = df[column].isna().sum()

    print(f"{column}: {missing} missing")


# =====================================
# 6. ADD BUSINESS METRICS
# =====================================

print("\nADDING BUSINESS METRICS")

# Estimasi jumlah barang berhasil dijual
df["net_quantity"] = (
    df["Jumlah"]
    - df["Returned quantity"]
)


# =====================================
# FINAL INFORMATION
# =====================================

print("\n" + "=" * 70)
print("FINAL DATA TYPES")
print("=" * 70)

print(df.dtypes)


print("\n" + "=" * 70)
print("FINAL SHAPE")
print("=" * 70)

print(df.shape)


# =====================================
# SAVE
# =====================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)


print("\n" + "=" * 70)
print("NUMERIC CLEANING SELESAI")
print("=" * 70)

print(f"\nFile disimpan di:")
print(OUTPUT_PATH)