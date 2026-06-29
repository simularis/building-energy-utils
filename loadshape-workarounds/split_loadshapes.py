import pandas as pd
import zipfile
import os
import glob

# ── CONFIG ──────────────────────────────────────────────────────────
INPUT_DIR    = "csvs"                    # folder containing all CSVs
OUTPUT_DIR   = "cedars_zips"             # output folder for zip files
PROJECT      = "SWHC024-com"             # used in output file names
TARGET_MB    = 45                        # max zip size in MB
# ────────────────────────────────────────────────────────────────────

def process_csv(csv_path, output_dir, project):
    basename  = os.path.basename(csv_path)
    bldg_type = basename.replace("CEDARS_LoadShape_Com_", "").replace(".csv", "")
    base      = f"loadshapes-{project}-{bldg_type}"
    zip_path  = os.path.join(output_dir, f"{base}.zip")

    print(f"\nProcessing: {basename}  ({os.path.getsize(csv_path)/1e6:.1f} MB)")

    # Read and write entire CSV into one zip
    df = pd.read_csv(csv_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{base}.csv", df.to_csv(index=False))

    size_mb = os.path.getsize(zip_path) / 1e6
    flag    = "⚠️  OVER 45MB — needs splitting" if size_mb > TARGET_MB else "✅"
    print(f"  → {base}.zip  {size_mb:.2f} MB  {flag}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv_files = sorted(glob.glob(os.path.join(INPUT_DIR, "CEDARS_LoadShape_Com_*.csv")))

    if not csv_files:
        print("No CSV files found. Check INPUT_DIR.")
        return

    print(f"Found {len(csv_files)} CSV files.")
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}\n")

    for csv_path in csv_files:
        process_csv(csv_path, OUTPUT_DIR, PROJECT)

    zips = glob.glob(os.path.join(OUTPUT_DIR, "*.zip"))
    print(f"\n✅ Done. {len(zips)} zip files written to: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    main()
