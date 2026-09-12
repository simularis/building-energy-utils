import os

# Copy each runs folder into a new folder (Energy_Models_Outputs_XXXX-XX-XX)
# Rename to unique names (i.e. runs_MFm_Ex)

# Top-level folders (update these paths)
top_level_dirs = [
    r"C:\path\to\runs_DMo_Ex",
    r"C:\path\to\runs_MFm_Ex",
    r"C:\path\to\runs_SFm_1975",
    r"C:\path\to\runs_SFm_1985",
]

# Files to keep
keep_files = {
    "instance.idf",
    "instance-out.err",
    "instance-tbl.htm",
    "instance-out.sql",
}

def is_leaf_directory(path):
    """Return True if directory has no subdirectories."""
    return not any(
        os.path.isdir(os.path.join(path, item))
        for item in os.listdir(path)
    )

for top_dir in top_level_dirs:
    for root, dirs, files in os.walk(top_dir):
        # Process only leaf directories (no subfolders)
        if len(dirs) == 0:
            print(f"Processing leaf folder: {root}")

            for file in files:
                if file not in keep_files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
