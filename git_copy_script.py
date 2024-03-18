"""git_copy_script.py: create a script to copy files while preserving git history.

For background and example for simpler cases, see
https://stackoverflow.com/questions/1043388/record-file-copy-operation-with-git/46484848

Example:
    Call the script via command line to output a script that copies a bunch of
    files while preserving their history in git. Then, invoke the script via bash.

        $ python git_copy_script.py FolderV1/ FolderV2/ > script.sh
        $ source script.sh

Copyright 2024, Nicholas Fette
Licensed under the Apache License, Version 2.0.
"""

from pathlib import Path
from argparse import ArgumentParser

def get_git_copy_files_script(files_from_to):
    tempbranchname = "temp-git-copy"
    git_script_loop0 = ""
    new_folders = set()
    git_script_loop1 = ""
    git_script_loop2 = ""

    for file_from, file_to in files_from_to:
        new_folders.add(file_to.parent)
        # Appends to script: move file from source to destination
        git_script_loop1 += f"""git mv '{file_from.as_posix()}' '{file_to.as_posix()}'\n"""
        # Appends to script: restore original file at source
        git_script_loop2 += f"""git checkout HEAD~ '{file_from.as_posix()}'\n"""

    for new_folder in new_folders:
        # Appends to script: make folders for destination files
        git_script_loop0 += f"""mkdir -p '{new_folder.as_posix()}'\n"""

    git_script = f"""{git_script_loop0}
git checkout -b {tempbranchname}
{git_script_loop1}
git commit -m 'Duplicate files (batch script)'
{git_script_loop2}
git commit -m 'Restore duplicated files (batch script)'
git checkout -
git merge --no-ff {tempbranchname} -m 'Merge duplicated files (batch script)'
git branch -D {tempbranchname}
"""
    return git_script

def git_copy_file(source : Path, dest : Path):
    git_script = get_git_copy_files_script((source, dest))
    return git_script

def git_copy_folder(source : Path, dest : Path):
    files_from = [f for f in source.glob("**/*") if f.is_file()]
    files_to = [dest.joinpath(f.relative_to(source)) for f in files_from]
    files_from_to = zip(files_from, files_to)
    git_script = get_git_copy_files_script(files_from_to)
    return git_script

def main():
    parser = ArgumentParser()
    parser.add_argument("source", help="The file or folder to copy.", type=Path)
    parser.add_argument("dest", help="The destination to copy.", type=Path)
    args = parser.parse_args()
    if args.source.is_file():
        git_script = git_copy_file(args.source, args.dest)
    else:
        git_script = git_copy_folder(args.source, args.dest)
    print(git_script)

if "__main__" == __name__:
    main()
