"""Reuse round-2 CSV validation and require an explicit episode manifest."""
import csv,json
from pathlib import Path
import numpy as np
from real_data_intake import validate_rows

ROOT=Path(__file__).resolve().parents[1]

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write_json(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def write_csv(path,rows):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def local_output(path):
    p=Path(path).resolve()
    if not p.is_relative_to(ROOT):raise ValueError('Outputs must stay in this project')
    p.mkdir(parents=True,exist_ok=True)
    return p

def load_dataset(folder):
    folder=Path(folder);meta=read_json(folder/'metadata.json')
    with (folder/'raw.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    normalized,checks=validate_rows(rows,meta)
    if checks['status']!='passed':raise ValueError(checks['errors'])
    if any('large sampling gap' in w for w in checks['warnings']):
        raise ValueError('Large sampling gap requires explicit data review before fitting; raw intake tool can still inspect it')
    with (folder/'episodes.csv').open(encoding='utf-8-sig',newline='') as f:manifest=list(csv.DictReader(f))
    required={'session_id','episode_id','specimen_id','repeat','amplitude_m','wait_s','program','reset_verified','forecast_start_s'}
    if not manifest or not required.issubset(manifest[0]):raise ValueError('Incomplete episodes.csv')
    groups={}
    for row in normalized:groups.setdefault((row['session_id'],row['episode_id']),[]).append(row)
    seen=set();episodes=[]
    for entry in manifest:
        key=(entry['session_id'],entry['episode_id'])
        if key in seen:raise ValueError('Duplicate episode manifest key')
        seen.add(key)
        if key not in groups:raise ValueError('Manifest episode absent from CSV')
        if entry['reset_verified'].lower() not in ['true','1']:raise ValueError('Unverified relaxed start: retain continuous history or implement initial-state inference before fitting')
        rr=groups[key]
        if {r['specimen_id'] for r in rr}!={entry['specimen_id']}:raise ValueError('Specimen mismatch')
        t=np.array([r['timestamp_s'] for r in rr]);t-=t[0]
        if not 0<float(entry['forecast_start_s'])<t[-1]:raise ValueError('Forecast starts outside record or has no past history')
        phases=np.array([r['phase'] for r in rr])
        if not {'preload','hold','retract','wait','recontact','rehold'}.issubset(set(phases)):
            raise ValueError('Need preload/hold/retract/wait/recontact/rehold phase labels')
        if abs(rr[0]['normal_force_N'])>meta['analysis']['contact_threshold_N']:
            raise ValueError('First sample is loaded: relaxed initialization unsupported')
        episodes.append(dict(entry, key='/'.join(key), t=t,
          x=np.array([r['actual_position_m'] for r in rr]),
          u=np.array([r['command_position_m'] for r in rr]),
          f=np.array([r['normal_force_N'] for r in rr]),phase=phases,
          amplitude=float(entry['amplitude_m']),wait=float(entry['wait_s']),
          forecast=int(np.searchsorted(t,float(entry['forecast_start_s'])))))
    if set(groups)!=seen:raise ValueError('Unlisted CSV episodes; no silent exclusions')
    if len({e['specimen_id'] for e in episodes})!=1:
        raise ValueError('Fit one specimen at a time; do not silently pool specimen variation')
    for k in ['reference_compression_m','contact_threshold_N','contact_persistence_s']:
        if float(meta['analysis'][k])<=0:raise ValueError(f'Invalid analysis {k}')
    return episodes,meta,checks

def splits(episodes):
    amps=sorted({e['amplitude'] for e in episodes});waits=sorted({e['wait'] for e in episodes});programs=sorted({e['program'] for e in episodes})
    if len(amps)<2 or len(waits)<3 or len(programs)<2:raise ValueError('Require 2 amplitudes, 3 waits, 2 programs')
    criteria={'amplitude':lambda e:e['amplitude']==amps[-1],
              'wait':lambda e:e['wait']==waits[len(waits)//2],
              'program':lambda e:e['program']==('overshoot' if 'overshoot' in programs else programs[-1])}
    for axis,predicate in criteria.items():
        train=[e for e in episodes if not predicate(e)]
        test=[e for e in episodes if predicate(e)]
        assert not ({e['key'] for e in train}&{e['key'] for e in test})
        yield axis,train,test

def contact_position(t,x,f,phase,threshold,persistence):
    candidates=np.flatnonzero((phase=='recontact')|(phase=='rehold'))
    for i in candidates:
        end=np.searchsorted(t,t[i]+persistence)
        if end<len(t) and np.all(f[i:end+1]>threshold):
            return float(x[i])
    return None
