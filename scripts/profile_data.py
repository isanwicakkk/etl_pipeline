import pandas as pd
from pathlib import Path


# =====================================
# PATH CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "combined_sales.csv"
)


# =====================================
# LOAD DATA
# =====================================

df = pd.read_csv(DATA_PATH)


print("=" * 70)
print("DATA PROFILING REPORT")
print("=" * 70)


# =====================================
# 1. BASIC INFORMATION
# =====================================

print("\n1. BASIC INFORMATION")
print("-" * 70)

print(f"Total Rows    : {df.shape[0]}")
print(f"Total Columns : {df.shape[1]}")


# =====================================
# 2. DATA TYPES
# =====================================

print("\n2. DATA TYPES")
print("-" * 70)

print(df.dtypes)


# =====================================
# 3. MISSING VALUES
# =====================================

print("\n3. MISSING VALUES")
print("-" * 70)

missing = df.isnull().sum()

missing_percent = (
    df.isnull().sum()
    / len(df)
    * 100
)

missing_report = pd.DataFrame({
    "missing_values": missing,
    "percentage": missing_percent.round(2)
})

print(
    missing_report[
        missing_report["missing_values"] > 0
    ]
)


# =====================================
# 4. DUPLICATE ROWS
# =====================================

print("\n4. DUPLICATE ROWS")
print("-" * 70)

duplicate_rows = df.duplicated().sum()

print(f"Jumlah duplicate rows: {duplicate_rows}")


# =====================================
# 5. DUPLICATE ORDER ID
# =====================================

print("\n5. ORDER ID ANALYSIS")
print("-" * 70)

print(f"Total Order ID       : {df['order_id'].count()}")
print(f"Unique Order ID      : {df['order_id'].nunique()}")

duplicate_order = df.duplicated(
    subset=["order_id"]
).sum()

print(f"Duplicate Order ID   : {duplicate_order}")


# =====================================
# 6. ORDER STATUS
# =====================================

print("\n6. STATUS PESANAN")
print("-" * 70)

print(
    df["Status Pesanan"]
    .value_counts(dropna=False)
)


# =====================================
# 7. PAYMENT METHOD
# =====================================

print("\n7. METODE PEMBAYARAN")
print("-" * 70)

print(
    df["Metode Pembayaran"]
    .value_counts(dropna=False)
)


# =====================================
# 8. DATE CHECK
# =====================================

print("\n8. DATE ANALYSIS")
print("-" * 70)

print(
    df["Waktu Pesanan Dibuat"]
    .head(10)
)


# =====================================
# 9. SAMPLE DATA
# =====================================

print("\n9. SAMPLE DATA")
print("-" * 70)

print(df.head())


print("\n" + "=" * 70)
print("DATA PROFILING SELESAI")
print("=" * 70)