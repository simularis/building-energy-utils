#!/usr/bin/env python3
import csv
import io
import shutil
import tempfile
import zipfile
from pathlib import Path

MAX_MB = 50
ROWS_PER_CHUNK = 8760
SAFETY_FACTOR = 0.95  # leave room for ZIP overhead/estimation error


def zipped_size_of_file(csv_path):
    """Return compressed ZIP size in bytes for one CSV file."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(csv_path, arcname=csv_path.name)
    return len(buffer.getvalue())


def write_csv_from_chunks(csv_path, header, chunk_files):
    """Write one CSV using the original header plus selected chunk files."""
    with open(csv_path, "w", newline="", encoding="utf-8") as out:
        csv.writer(out).writerow(header)
        for chunk_file in chunk_files:
            with open(chunk_file, "r", encoding="utf-8", newline="") as cf:
                shutil.copyfileobj(cf, out)


def write_inner_zip_to_outer(zout, csv_path, zip_name):
    """Create one ZIP containing one CSV, then write that ZIP into the final output ZIP."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(csv_path, arcname=csv_path.name)

    # Store the inner zip without recompressing it.
    zout.writestr(zip_name, buffer.getvalue(), compress_type=zipfile.ZIP_STORED)
    return len(buffer.getvalue())


def split_csv_fast_estimate(zin, zout, zinfo, tmp_dir, max_bytes):
    csv_name = Path(zinfo.filename).stem

    work_dir = tmp_dir / csv_name
    groups_dir = work_dir / "groups"
    chunks_dir = work_dir / "chunks"
    parts_dir = work_dir / "parts"

    groups_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    parts_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # Step 1: Read CSV from the input ZIP and group rows by sort key.
    # ------------------------------------------------------------
    with zin.open(zinfo, "r") as raw:
        reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        header = next(reader)

        idx_type = header.index("BldgType")
        idx_vint = header.index("BldgVint")
        idx_hvac = header.index("BldgHVAC")
        idx_loc = header.index("BldgLoc")

        group_files = {}
        group_writers = {}
        group_handles = {}

        for row in reader:
            key = (
                row[idx_type],
                row[idx_vint],
                row[idx_hvac],
                row[idx_loc],
            )

            if key not in group_files:
                n = len(group_files)
                group_files[key] = groups_dir / f"group_{n:06d}.csv"
                h = open(group_files[key], "w", newline="", encoding="utf-8")
                group_handles[key] = h
                group_writers[key] = csv.writer(h)

            group_writers[key].writerow(row)

        for h in group_handles.values():
            h.close()

    # ------------------------------------------------------------
    # Step 2: Read sorted groups and create 8760-row chunk files.
    # Also estimate each chunk's compressed size once.
    # ------------------------------------------------------------
    chunk_info = []  # list of (chunk_path, estimated_zipped_size)
    rows = []
    chunk_num = 1

    header_only = parts_dir / "header_only.csv"
    with open(header_only, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(header)
    header_zip_size = zipped_size_of_file(header_only)

    for key in sorted(group_files.keys()):
        with open(group_files[key], "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)

            for row in reader:
                rows.append(row)

                if len(rows) == ROWS_PER_CHUNK:
                    chunk_path = chunks_dir / f"chunk_{chunk_num:06d}.csv"
                    with open(chunk_path, "w", newline="", encoding="utf-8") as cf:
                        csv.writer(cf).writerows(rows)

                    chunk_zip_size = zipped_size_of_file(chunk_path)
                    chunk_info.append((chunk_path, chunk_zip_size))

                    chunk_num += 1
                    rows = []

    if rows:
        chunk_path = chunks_dir / f"chunk_{chunk_num:06d}.csv"
        with open(chunk_path, "w", newline="", encoding="utf-8") as cf:
            csv.writer(cf).writerows(rows)

        chunk_zip_size = zipped_size_of_file(chunk_path)
        chunk_info.append((chunk_path, chunk_zip_size))

    # ------------------------------------------------------------
    # Step 3: Pack chunks into output parts using estimated compressed size.
    # ------------------------------------------------------------
    target_bytes = int(max_bytes * SAFETY_FACTOR)
    part_num = 1
    current_chunks = []
    current_estimated_size = header_zip_size

    def finalize_part(chunks_to_write, estimated_size):
        nonlocal part_num

        if not chunks_to_write:
            return

        csv_path = parts_dir / f"{csv_name}_part{part_num:04d}.csv"
        zip_name = f"{csv_name}_part{part_num:04d}.zip"

        write_csv_from_chunks(csv_path, header, chunks_to_write)
        actual_size = write_inner_zip_to_outer(zout, csv_path, zip_name)

        actual_mb = actual_size / 1024 / 1024
        estimated_mb = estimated_size / 1024 / 1024

        if actual_size > max_bytes:
            print(f"  WARNING: {zip_name} actual size is {actual_mb:.1f} MB; estimate was {estimated_mb:.1f} MB")
        else:
            print(f"  Created {zip_name} actual {actual_mb:.1f} MB; estimate {estimated_mb:.1f} MB")

        part_num += 1

    for chunk_path, chunk_est_size in chunk_info:
        candidate_estimated_size = current_estimated_size + chunk_est_size

        if candidate_estimated_size <= target_bytes:
            current_chunks.append(chunk_path)
            current_estimated_size = candidate_estimated_size
        else:
            if current_chunks:
                finalize_part(current_chunks, current_estimated_size)
                current_chunks = [chunk_path]
                current_estimated_size = header_zip_size + chunk_est_size
            else:
                # One chunk alone is estimated over the limit. Keep it whole anyway.
                finalize_part([chunk_path], header_zip_size + chunk_est_size)
                current_chunks = []
                current_estimated_size = header_zip_size

    finalize_part(current_chunks, current_estimated_size)


input_zip = Path(input("Input ZIP: ").strip())
output_zip = Path(input("Output ZIP: ").strip())
max_bytes = MAX_MB * 1024 * 1024

with tempfile.TemporaryDirectory() as td:
    tmp_dir = Path(td)

    with zipfile.ZipFile(input_zip, "r") as zin, \
         zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zout:

        for zinfo in zin.infolist():
            if zinfo.filename.lower().endswith(".csv"):
                print(f"Processing {zinfo.filename}")
                split_csv_fast_estimate(zin, zout, zinfo, tmp_dir, max_bytes)

print("Done")
