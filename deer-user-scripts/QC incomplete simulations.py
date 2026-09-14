# Use this script to tabulate simulation status for models in this batch.

from pathlib import Path
from tqdm import tqdm
import pandas
import re
import sqlite3
from argparse import ArgumentParser

def gather_batch_stats(
        root='.',
        ENERGYPLUS_MODEL_FILEPATTERN = 'instance.idf',
        ENERGYPLUS_OUT_FILEPATTERN = 'instance-out.sql',
        ENERGYPLUS_ERR_FILEPATTERN = 'instance-out.err'
):
    root = Path(root)
    result = []
    # Loop over subfolders and create progress bars.
    for subroot in root.glob('*'):
        subroot_relpath = subroot.relative_to(root)
        # Count composed models.
        subroot_composed_models = list(subroot.glob('**/runs/**/'+ENERGYPLUS_MODEL_FILEPATTERN))
        n_models = len(subroot_composed_models)

        if n_models > 0:
            # Create the progress bar here.
            myiter = tqdm(subroot_composed_models, desc=subroot_relpath.parts[0])

            for i,f1 in enumerate(myiter):
                fileerr = f1.parent.joinpath(ENERGYPLUS_ERR_FILEPATTERN)
                fileout = f1.parent.joinpath(ENERGYPLUS_OUT_FILEPATTERN)

                # Parse the filename following DEER conventions
                # In 2023, residential models would be found like this:
                # relpath = "SFm_Furnace_1975\runs\CZ01\SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace\Msr-Res-GasFurnace-AFUE95-ECM\instance-out.sql
                # In 2024, commercial models would be found like this:
                # relpath = "SWXX000-00 Measure Name_1975\runs\CZ01\Asm\defaults\instance-out.sql"
                relpath = f1.relative_to(root)

                meas_group_vintage_combo, _, cz, cohort, techid, _ = relpath.parts
                cohort_clean = cohort.replace("&","=")
                meas_group, bldgvint = meas_group_vintage_combo.rsplit("_", 1)

                fileerr_exists = fileerr.exists()
                fileout_exists = fileout.exists()

                if not fileerr_exists:
                    success = False
                    timestamp = None
                    warnings = None
                    errors = None
                else:
                    # Match for a line at the beginning of the file like this:
                    # Program Version,EnergyPlus, Version 9.5.0-de239b2e5f, YMD=2025.07.29 19:21,
                    content = fileerr.read_text().splitlines()
                    firstline = content[0]
                    m = re.search(r'YMD=(?P<timestamp>[^,]*)',firstline)
                    if not m:
                        timestamp = None
                    else:
                        timestamp = m['timestamp']

                    # Match for a line at the end of the file like this:
                    # ************* EnergyPlus Completed Successfully-- 4 Warning; 0 Severe Errors; Elapsed Time=00hr 01min 53.20sec
                    lastline = content[-1]
                    success = (lastline.find(r'************* EnergyPlus Completed Successfully') > 0)
                    m = re.search(r'-- (?P<warnings>\d*) Warning; (?P<errors>\d*) Severe Errors; Elapsed Time', lastline)
                    if not m:
                        warnings = None
                        errors = None
                    else:
                        warnings = m['warnings']
                        errors = m['errors']

                if not fileout_exists:
                    fileout
                else:
                    pass

                hastempdir = False
                for f3 in f1.parent.glob("instance*"):
                    if f3.is_dir():
                        hastempdir = True

                result.append((relpath, meas_group_vintage_combo, cz, cohort, techid,
                            fileerr_exists, fileout_exists,
                            timestamp, success, warnings, errors, hastempdir))

            myiter.close()
        # end models
    # end subroot folder
    stats = pandas.DataFrame(result,
                            columns=['relpath', 'meas_group_vintage_combo', 'cz', 'cohort', 'techid',
                                    'fileerr_exists', 'fileout_exists',
                                    'timestamp', 'success', 'warnings', 'errors', 'hastempdir'])
    return stats

def main():
    parser = ArgumentParser()
    parser.add_argument('simfolder', type=Path, default='.', nargs='?')
    parser.add_argument('output_file', type=Path, default='simulation_stats.csv', nargs='?')

    args = parser.parse_args()
    
    stats1 = gather_batch_stats(
        root=args.simfolder,
        ENERGYPLUS_MODEL_FILEPATTERN = 'instance.idf',
        ENERGYPLUS_OUT_FILEPATTERN = 'instance-out.sql',
        ENERGYPLUS_ERR_FILEPATTERN = 'instance-out.err')
    stats2 = gather_batch_stats(
        root=args.simfolder,
        ENERGYPLUS_MODEL_FILEPATTERN = 'instance-hardsize.idf',
        ENERGYPLUS_OUT_FILEPATTERN = 'instance-hardsize-out.sql',
        ENERGYPLUS_ERR_FILEPATTERN = 'instance-hardsize-out.err')

    stats = pandas.concat([stats1, stats2])
    stats.to_csv(args.output_file, index=False)

    # Print a count of runs that failed
    print("Number of runs that failed:", len(stats[stats['success']==False]))
    # Note that files like 'instance.idf' in the measure case will not run through simulation. Ignore "failed" runs with that filename.
    # For measure case, files like 'instance-hardsize.idf' should be simulated without errors. (Confirm in simstats.csv.)

    # Print a count of runs that left behind a temporary directory (should have been deleted by modelkit)
    print("Number of runs that left behind a temporary directory:", len(stats[stats['hastempdir']==True]))
