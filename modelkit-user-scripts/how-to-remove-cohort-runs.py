from pathlib import Path
import shutil
p=Path()
folders=list(p.glob("*/runs/*/SFm&2*"))
for f in folders:
    print(f)
    shutil.rmtree(f)
