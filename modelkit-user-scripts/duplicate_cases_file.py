"""duplicate_cases_file.py: copy cases.csv to overwrite existing files in target folder.

Example:
    Call the script via command line, given the locations of source file and target folder.

        $ python duplicate_cases_file.py mycases.csv "commercial measures/SWHC004-07 Space Heating Boiler"

Copyright 2024, Nicholas Fette
Licensed under the Apache License, Version 2.0.
"""

from pathlib import Path
from argparse import ArgumentParser
import shutil

def duplicate_cases_file(file_source: Path, folder_target: Path, dry_run=True):

    # Find all the existing cases files.
    list_cases_csv = list(folder_target.glob("**/cases/*.csv"))
    
    for file_target in list_cases_csv:
        print(file_source,"->",file_target)
        if not dry_run:
            shutil.copy(file_source, file_target)

def main():
    parser = ArgumentParser()
    parser.add_argument("source", help="The file to copy.", type=Path)
    parser.add_argument("dest", help="The destination.", type=Path)
    parser.add_argument("--dry-run", help="Dry run (don't actually copy files)", action='store_true')
    args = parser.parse_args()
    duplicate_cases_file(args.source, args.dest, args.dry_run)

if "__main__" == __name__:
    main()
