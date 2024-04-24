"""git_mvdir_script.py: create a script to rename a directory.
Applies recursively to all files within the directory.
Useful as a workaround since `git mv` can move files and directories, but cannot simply rename a directory.

Example:
    Call the script via command line to output a script that copies a bunch of
    files while preserving their history in git. Then, invoke the script via bash.

        $ python git_mvdir_script.py FolderV1/ FolderV2/ > script.sh
        $ source script.sh

Copyright 2024, Nicholas Fette
Licensed under the Apache License, Version 2.0.
"""

from pathlib import Path
from argparse import ArgumentParser

def get_git_mvdir_files_script(files_from, dest: Path):
    git_script_loop0 = ""
    new_folders = set()
    git_script_loop1 = ""

    for file_from in files_from:
        new_folders.add(dest)
        # Appends to script: move file or folder from source to destination
        git_script_loop1 += f"""git mv '{file_from.as_posix()}' '{dest.as_posix()}'\n"""

    for new_folder in new_folders:
        # Appends to script: make folders for destination files
        git_script_loop0 += f"""mkdir -p '{new_folder.as_posix()}'\n"""

    git_script = f"""echo === Making folders ===
{git_script_loop0}
echo === Executing git mv statements ===
{git_script_loop1}
"""
    return git_script

def git_mvdir_folder(source : Path, dest : Path):
    # List of files and subfolders within the source directory.
    files_from = [f for f in source.glob("*")]
    git_script = get_git_mvdir_files_script(files_from, dest)
    return git_script

def main():
    parser = ArgumentParser()
    parser.add_argument("source", help="The file or folder to copy.", type=Path)
    parser.add_argument("dest", help="The destination to copy.", type=Path)
    args = parser.parse_args()
    git_script = git_mvdir_folder(args.source, args.dest)
    print(git_script)

if "__main__" == __name__:
    main()
