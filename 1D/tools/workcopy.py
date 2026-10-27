"""Copy one accepted experiment to a new workspace before reproducing it."""
import argparse
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
NAMES={'history-dependence':'history_dependence',
       'controller-transfer':'controller_transfer',
       'shared-feedback':'shared_feedback',
       'material-collection':'lab',
       'pilot':'pilot'}
ALIASES=dict(zip(('e1','e2','e3','p1'), NAMES))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment',type=lambda value: ALIASES.get(value,value),choices=NAMES,required=True)
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
    if args.experiment=='controller-transfer':
        print('Primary experiment:',target/'v2')

if __name__=='__main__':
    main()
