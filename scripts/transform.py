import re
import pandas as pd
from pathlib import Path


# PATH CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed"


# HELPER: SNAKE_CASE CONVERTER

def clean_to_snake_case(text: str) -> str:
    """Mengubah string biasa/camelCase/Spasi menjadi snake_case."""
    text = str(text).strip()
    text = re.sub(r'[/\\-]', ' ', text)       # ganti / atau - dengan spasi
    text = re.sub(r'[^\w\s]', '', text)       # hapus simbol unik
    text = re.sub(r'\s+', '_', text)          # ganti spasi dengan _
    return text.lower()


# STANDARD SCHEMA (SNAKE_CASE)

STANDARD_COLUMNS_SNAKE = [
    "order_id",
    "product_category",
    "status_pesanan",
    "alasan_pembatalan",
    "opsi_pengiriman",
    "waktu_pesanan_dibuat",
    "metode_pembayaran",
    "jumlah",
    "returned_quantity",
    "total_diskon",
    "total_berat",
    "ongkos_kirim_dibayar_oleh_pembeli",
    "estimasi_potongan_biaya_pengiriman",
    "total_pembayaran",
    "perkiraan_ongkos_kirim",
    "kota_kabupaten",
    "provinsi"
]


def transform_data():

    files = sorted(RAW_DATA_PATH.glob("*.xlsx"))

    print("=" * 70)
    print("DATA TRANSFORMATION")
    print("=" * 70)

    print(f"\nJumlah file ditemukan: {len(files)}")

    all_dataframes = []

    for file in files:

        print(f"\nMemproses: {file.name}")

        df = pd.read_excel(file)


        # STANDARISASI KOLOM INPUT KE SNAKE_CASE

        # Ubah semua header kolom di file Excel asli ke snake_case dulu
        df.columns = [clean_to_snake_case(col) for col in df.columns]

        # Penanganan khusus jika nama kolom waktu di Excel berbeda
        if (
            "waktu_pengiriman_diatur" in df.columns
            and "waktu_pesanan_dibuat" not in df.columns
        ):
            df = df.rename(
                columns={
                    "waktu_pengiriman_diatur": "waktu_pesanan_dibuat"
                }
            )
            print("✓ Kolom waktu distandarisasi")

  
        # AMBIL & NORMALSASI KOLOM


        missing_columns = [
            column
            for column in STANDARD_COLUMNS_SNAKE
            if column not in df.columns
        ]

        if missing_columns:
            print("⚠️ Kolom tidak ditemukan di file ini:")
            print(missing_columns)

        available_columns = [
            column
            for column in STANDARD_COLUMNS_SNAKE
            if column in df.columns
        ]

        df = df[available_columns]

        # Tambahkan kolom yang tidak ada di file Excel dengan isi NA
        for column in STANDARD_COLUMNS_SNAKE:
            if column not in df.columns:
                df[column] = pd.NA

        # Urutkan sesuai standar skema
        df = df[STANDARD_COLUMNS_SNAKE]

        # Tambahkan kolom nama file sumber
        df["source_file"] = file.name

        all_dataframes.append(df)

        print(f"✓ Berhasil: {df.shape}")

    # GABUNGKAN SEMUA FILE

    combined_df = pd.concat(
        all_dataframes,
        ignore_index=True
    )

    print("\n" + "=" * 70)
    print("SEMUA DATA BERHASIL DIGABUNGKAN (SNAKE_CASE)")
    print("=" * 70)

    print(f"Total baris: {combined_df.shape[0]}")
    print(f"Total kolom: {combined_df.shape[1]}")

    # SIMPAN HASIL

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

    print("\nPREVIEW DATA (HEADER SNAKE_CASE):")
    print(df.head())