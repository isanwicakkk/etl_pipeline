import pandas as pd
from pathlib import Path


# =========================
# PATH CONFIGURATION
# =========================

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw"


def validate_files():

    # Cari semua file Excel
    files = sorted(RAW_DATA_PATH.glob("*.xlsx"))

    print("=" * 70)
    print("DATA VALIDATION REPORT")
    print("=" * 70)

    print(f"\nJumlah file ditemukan: {len(files)}")

    if not files:
        raise FileNotFoundError(
            f"Tidak ada file Excel di: {RAW_DATA_PATH}"
        )

    # Kolom referensi dari file pertama
    reference_columns = None

    validation_results = []

    for file in files:

        print("\n" + "-" * 70)
        print(f"FILE: {file.name}")

        # Baca file
        df = pd.read_excel(file)

        # Informasi dasar
        rows, columns = df.shape

        print(f"Jumlah baris  : {rows}")
        print(f"Jumlah kolom  : {columns}")

        # Ambil kolom
        current_columns = list(df.columns)

        # File pertama menjadi referensi
        if reference_columns is None:

            reference_columns = current_columns

            column_status = "REFERENCE"

        else:

            # Bandingkan kolom
            if current_columns == reference_columns:

                column_status = "MATCH"

            else:

                column_status = "DIFFERENT"

                print("\n⚠️ STRUKTUR KOLOM BERBEDA!")

                missing_columns = set(reference_columns) - set(current_columns)
                extra_columns = set(current_columns) - set(reference_columns)

                if missing_columns:
                    print("Kolom hilang:")
                    print(missing_columns)

                if extra_columns:
                    print("Kolom tambahan:")
                    print(extra_columns)

        # Missing values
        total_missing = df.isnull().sum().sum()

        print(f"Total missing value: {total_missing}")
        print(f"Status kolom: {column_status}")

        # Simpan hasil
        validation_results.append({

            "file_name": file.name,
            "rows": rows,
            "columns": columns,
            "missing_values": total_missing,
            "column_status": column_status

        })

    # =========================
    # SUMMARY
    # =========================

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    result_df = pd.DataFrame(validation_results)

    print(result_df)

    # Simpan report
    output_path = BASE_DIR / "data" / "processed" / "validation_report.csv"

    result_df.to_csv(
        output_path,
        index=False
    )

    print(f"\nReport disimpan di:")
    print(output_path)

    # Cek apakah semua struktur sama
    different_files = result_df[
        result_df["column_status"] == "DIFFERENT"
    ]

    if different_files.empty:

        print("\n✅ SEMUA FILE MEMILIKI STRUKTUR KOLOM YANG SAMA")

    else:

        print("\n⚠️ ADA FILE DENGAN STRUKTUR BERBEDA")

        print(different_files[["file_name", "column_status"]])


if __name__ == "__main__":

    validate_files()