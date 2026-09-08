import pandas as pd
from pathlib import Path


# Lokasi folder tempat file extract.py berada
SCRIPT_DIR = Path(__file__).resolve().parent

# Naik satu level ke folder latihan_etl
BASE_DIR = SCRIPT_DIR.parent

# Path ke data/raw
RAW_DATA_PATH = BASE_DIR / "data" / "raw"


def extract_data():

    print("=" * 50)
    print("SCRIPT DIR:")
    print(SCRIPT_DIR)

    print("\nBASE DIR:")
    print(BASE_DIR)

    print("\nRAW DATA PATH:")
    print(RAW_DATA_PATH)

    print("\nFolder tersedia?")
    print(RAW_DATA_PATH.exists())

    print("=" * 50)

    # Cari semua file Excel
    files = sorted(RAW_DATA_PATH.glob("*.xlsx"))

    print(f"\nJumlah file ditemukan: {len(files)}\n")

    # Jika tidak ada file
    if not files:
        raise FileNotFoundError(
            f"Tidak ada file Excel ditemukan di: {RAW_DATA_PATH}"
        )

    dataframes = []

    # Membaca setiap file
    for file in files:

        print(f"Membaca: {file.name}")

        df = pd.read_excel(file)

        # Tambahkan nama file sumber
        df["source_file"] = file.name

        dataframes.append(df)

    # Gabungkan semua DataFrame
    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    print("\n" + "=" * 50)
    print("EXTRACT BERHASIL")
    print("=" * 50)

    print(f"Total baris: {combined_df.shape[0]}")
    print(f"Total kolom: {combined_df.shape[1]}")

    return combined_df


if __name__ == "__main__":

    df = extract_data()

    print("\nPreview Data:")
    print(df.head())