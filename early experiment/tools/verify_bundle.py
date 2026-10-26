"""Verify archived research artifacts; optionally check the full historical snapshot."""
import argparse
from pathlib import Path
import hashlib
import json
import re
import zipfile

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / 'early experiment'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict-snapshot',action='store_true',
                        help='Also require documentation and helper files to match the original publication snapshot.')
    args=parser.parse_args()
    manifest = json.loads((BUNDLE/'provenance/public_manifest.json').read_text(encoding='utf-8'))
    errors=[]
    artifacts=[BUNDLE/name for name in ('experiments','presentation','diagrams')]
    checked=0
    for item in manifest['files']:
        path=REPO/item['path']
        if not args.strict_snapshot and not any(path.is_relative_to(folder) for folder in artifacts):
            continue
        checked+=1
        if not path.is_file():
            errors.append('Missing: '+item['path'])
        elif hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            errors.append('Hash mismatch: '+item['path'])
    code=[]
    for path in (BUNDLE/'experiments').rglob('*.py'):
        code.append(path)
        if re.search(r'[\u3400-\u9fff]',path.read_text(encoding='utf-8-sig')):
            errors.append('Non-English source text: '+str(path.relative_to(REPO)))
    with zipfile.ZipFile(BUNDLE/'presentation/NR_Progress_2026-10-22.pptx') as z:
        slide_count=sum(bool(re.fullmatch(r'ppt/slides/slide\d+\.xml',name)) for name in z.namelist())
        if slide_count!=12:
            errors.append(f'Expected 12 slides, found {slide_count}')
    for ext in ['png','svg','pdf']:
        if not (BUNDLE/f'diagrams/workflow/interaction_history_state_flow.{ext}').is_file():
            errors.append('Missing diagram: '+ext)
    if errors:
        raise SystemExit('\n'.join(errors))
    print(json.dumps({'status':'passed','hashed_files':checked,
                      'scope':'historical_snapshot' if args.strict_snapshot else 'research_artifacts',
                      'code_files_without_chinese':len(code),'slides':slide_count,
                      'diagram_formats':['png','svg','pdf']},indent=2))

if __name__ == '__main__':
    main()
