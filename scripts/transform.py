import pandas as pd
from pathlib import Path


# ==================================
# PATH CONFIGURATION
# ==================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = BASE_DIR / "data" / "raw"

PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed"


# ==================================
# STANDARD SCHEMA
# ==================================

STANDARD_COLUMNS = [
    "order_id",
    "product_category",
    "Status Pesanan",
    "Alasan Pembatalan",
    "Opsi Pengiriman",
    "Waktu Pesanan Dibuat",
    "Metode Pembayaran",
    "Jumlah",
    "Returned quantity",
    "Total Diskon",
    "Total Berat",
    "Ongkos Kirim Dibayar oleh Pembeli",
    "Estimasi Potongan Biaya Pengiriman",
    "Total Pembayaran",
    "Perkiraan Ongkos Kirim",
    "Kota/Kabupaten",
    "Provinsi"
]


def transform_data():

    # Cari semua file Excel
    files = sorted(RAW_DATA_PATH.glob("*.xlsx"))

    print("=" * 70)
    print("DATA TRANSFORMATION")
    print("=" * 70)

    print(f"\nJumlah file ditemukan: {len(files)}")

    all_dataframes = []

    for file in files:

        print(f"\nMemproses: {file.name}")

        df = pd.read_excel(file)

        # ==================================
        # STANDARDISASI NAMA KOLOM
        # ==================================

        # Beberapa file menggunakan
        # Waktu Pengiriman Diatur
        if (
            "Waktu Pengiriman Diatur" in df.columns
            and "Waktu Pesanan Dibuat" not in df.columns
        ):

            df = df.rename(
                columns={
                    "Waktu Pengiriman Diatur":
                    "Waktu Pesanan Dibuat"
                }
            )

            print("✓ Kolom waktu distandarisasi")

        # ==================================
        # AMBIL KOLOM YANG DIPERLUKAN
        # ==================================

        missing_columns = [
            column
            for column in STANDARD_COLUMNS
            if column not in df.columns
        ]

        if missing_columns:

            print("⚠️ Kolom tidak ditemukan:")
            print(missing_columns)

        # Ambil hanya kolom yang tersedia
        available_columns = [
            column
            for column in STANDARD_COLUMNS
            if column in df.columns
        ]

        df = df[available_columns]

        # ==================================
        # TAMBAHKAN KOLOM YANG HILANG
        # ==================================

        for column in STANDARD_COLUMNS:

            if column not in df.columns:

                df[column] = pd.NA

        # Pastikan urutan kolom sama
        df = df[STANDARD_COLUMNS]

        # ==================================
        # TAMBAHKAN SOURCE FILE
        # ==================================

        df["source_file"] = file.name

        all_dataframes.append(df)

        print(f"✓ Berhasil: {df.shape}")

    # ==================================
    # GABUNGKAN SEMUA FILE
    # ==================================

    combined_df = pd.concat(
        all_dataframes,
        ignore_index=True
    )

    print("\n" + "=" * 70)
    print("SEMUA DATA BERHASIL DIGABUNGKAN")
    print("=" * 70)

    print(f"Total baris: {combined_df.shape[0]}")
    print(f"Total kolom: {combined_df.shape[1]}")

    # ==================================
    # SIMPAN HASIL
    # ==================================

    PROCESSED_DATA_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        PROCESSED_DATA_PATH /
        "combined_sales.csv"
    )

    combined_df.to_csv(
        output_file,
        index=False
    )

    print(f"\n✓ File berhasil disimpan:")
    print(output_file)

    return combined_df


if __name__ == "__main__":

    df = transform_data()

    print("\nPREVIEW DATA:")

    print(df.head())