"""Copy one accepted experiment to a new workspace before reproducing it."""
import argparse
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
NAMES={'e1':'01_history',
       'e2':'02_transfer',
       'e3':'03_feedback',
       'p1':'lab',
       'pilot':'pilot'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment',choices=NAMES,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    source=ROOT/'experiments'/NAMES[args.experiment]
    target=args.destination.resolve()
    if target.exists():
        raise SystemExit('Destination exists. Choose a new work directory.')
    if source.resolve() in target.parents or target==source.resolve():
        raise SystemExit('The work copy must be outside the accepted source directory.')
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('.venv','__pycache__','.cache','.pytest_cache','*.nbc','*.nbi'))
    print(target)
    if args.experiment=='e2':
        print('Primary experiment:',target/'v2')

if __name__=='__main__':
    main()
