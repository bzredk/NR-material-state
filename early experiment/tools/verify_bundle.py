"""Verify public artifact hashes, source language and the presentation scope."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / 'early experiment'

def main():
    manifest = json.loads((BUNDLE/'provenance/public_manifest.json').read_text(encoding='utf-8'))
    errors=[]
    for item in manifest['files']:
        path=REPO/item['path']
        if not path.is_file():
            errors.append('Missing: '+item['path'])
        elif hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            errors.append('Hash mismatch: '+item['path'])
    code=[]
    for path in REPO.rglob('*'):
        if not path.is_file() or {'.git','.venv','reproductions','verification-local','__pycache__'}.intersection(path.relative_to(REPO).parts):
            continue
        if path.suffix in {'.py','.ps1','.sh','.js','.ts','.yml','.yaml'}:
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
    print(json.dumps({'status':'passed','hashed_files':len(manifest['files']),
                      'code_files_without_chinese':len(code),'slides':slide_count,
                      'diagram_formats':['png','svg','pdf']},indent=2))

if __name__ == '__main__':
    main()
