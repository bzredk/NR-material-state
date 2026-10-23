"""CSV validation and force-displacement diagnostics; does not control a robot."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import argparse,csv,json
import numpy as np

UNITS={'time':{'s':1.,'ms':1e-3,'us':1e-6},'position':{'m':1.,'mm':1e-3},'force':{'N':1.,'mN':1e-3,'kN':1e3}}
REQUIRED=['episode_id','specimen_id','session_id','timestamp','command_position','actual_position','normal_force']


def validate_rows(rows,meta):
    errors=[];warnings=[]
    if meta.get('data_type') not in ['real','synthetic_validation']:
        errors.append('Declare data_type as real or synthetic_validation.')
    factors={}
    for quantity,allowed in UNITS.items():
        unit=meta.get('units',{}).get(quantity)
        if unit not in allowed:errors.append(f'Unsupported/missing {quantity} unit: {unit}; allowed {list(allowed)}')
        else:factors[quantity]=allowed[unit]
    columns=meta.get('columns',{k:k for k in REQUIRED})
    if not rows:errors.append('CSV contains no data rows.')
    if rows:
        for k in REQUIRED:
            if columns.get(k,k) not in rows[0]:errors.append(f'Missing column for {k}')
    if errors:return [],{'status':'failed','errors':errors,'warnings':warnings}
    for flag in ['position_sign','force_sign']:
        if meta.get(flag,1) not in [-1,1]:errors.append(f'{flag} must be +1 or -1')
    for offset in ['surface_position_m','force_offset_N']:
        try:
            if not np.isfinite(float(meta.get(offset,0))):raise ValueError('nonfinite')
        except (TypeError,ValueError):errors.append(f'{offset} must be finite numeric SI value')
    if errors:return [],{'status':'failed','errors':errors,'warnings':warnings}
    normalized=[];groups={}
    for i,row in enumerate(rows,2):
        try:
            r={k:row[columns.get(k,k)].strip() for k in ['episode_id','specimen_id','session_id']}
            if not all(r.values()):raise ValueError('Empty episode/specimen/session ID')
            vals={k:float(row[columns.get(k,k)]) for k in ['timestamp','command_position','actual_position','normal_force']}
            if not all(np.isfinite(list(vals.values()))):raise ValueError('Nonfinite numeric value')
            r['timestamp_s']=vals['timestamp']*factors['time']
            for source,target in [('command_position','command_position_m'),('actual_position','actual_position_m')]:
                r[target]=(vals[source]*factors['position']-meta.get('surface_position_m',0))*meta.get('position_sign',1)
            r['normal_force_N']=(vals['normal_force']*factors['force']-meta.get('force_offset_N',0))*meta.get('force_sign',1)
            r['phase']=row.get(columns.get('phase','phase'),'unspecified')
            normalized.append(r);groups.setdefault((r['session_id'],r['episode_id']),[]).append(len(normalized)-1)
        except (ValueError,KeyError,TypeError) as exc:errors.append(f'Row {i}: {exc}')
    reports=[]
    for key,indices in groups.items():
        records=[normalized[i] for i in indices];t=np.array([r['timestamp_s'] for r in records]);dt=np.diff(t)
        if len(t)<3:errors.append(f'{key}: need at least 3 samples');continue
        if np.any(dt<=0):errors.append(f'{key}: timestamps must increase strictly; do not silently sort/drop duplicates');continue
        if len({r['specimen_id'] for r in records})>1:errors.append(f'{key}: specimen changes inside episode')
        x=np.array([r['actual_position_m'] for r in records]);f=np.array([r['normal_force_N'] for r in records]);v=np.gradient(x,t)
        for i,vel in zip(indices,v):normalized[i]['derived_velocity_m_s']=float(vel)
        md=float(np.median(dt));jitter=float(np.std(dt)/md)
        if dt.max()>5*md:warnings.append(f'{key}: large sampling gap {dt.max():.6g} s')
        if jitter>.1:warnings.append(f'{key}: irregular sampling; dt CV {jitter:.3f}; no automatic resampling applied')
        limits=meta.get('review_limits',{})
        for name,measured in [('max_abs_force_N',float(abs(f).max())),('max_abs_position_m',float(abs(x).max())),('max_abs_speed_m_s',float(abs(v).max()))]:
            if name in limits and measured>limits[name]:warnings.append(f'{key}: {name}={measured:.6g} exceeds declared review limit {limits[name]}')
        reports.append(dict(session_id=key[0],episode_id=key[1],samples=len(t),duration_s=float(t[-1]-t[0]),
          sampling_rate_Hz=1/md,max_gap_s=float(dt.max()),dt_cv=jitter,position_range_m=[float(x.min()),float(x.max())],
          force_range_N=[float(f.min()),float(f.max())],force_displacement_work_J=float(np.trapezoid(f,x))))
    warnings.append('CSV timestamps alone cannot establish force/position sensor synchronization; retain original clocks and calibration.')
    warnings.append('Velocity is an unfiltered numerical diagnostic; signed force-displacement work is not automatically dissipated energy.')
    return normalized,dict(status='failed' if errors else 'passed',data_type=meta.get('data_type'),errors=errors,warnings=warnings,episodes=reports,
       conventions='SI; positive position toward compression; positive compressive force',no_automatic_rows_removed=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('--metadata',required=True)
    p.add_argument('--output',default=str(ROOT/'runs'/'real_intake'))
    args=p.parse_args();out=Path(args.output).resolve()
    if not out.is_relative_to(ROOT):raise ValueError('Project-local outputs required')
    out.mkdir(parents=True,exist_ok=True)
    meta=json.loads(Path(args.metadata).read_text(encoding='utf-8-sig'))
    with Path(args.csv).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    normalized,report=validate_rows(rows,meta)
    report['source_csv']=str(Path(args.csv).resolve());report['source_metadata']=str(Path(args.metadata).resolve())
    (out/'data_checks.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'metadata.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    if report['status']=='failed':
        print(json.dumps(report,ensure_ascii=False));raise SystemExit(2)
    with (out/'normalized.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(normalized[0]));writer.writeheader();writer.writerows(normalized)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(2,2,figsize=(11,7));keys=list(dict.fromkeys((r['session_id'],r['episode_id']) for r in normalized))
    for key in keys[:12]:
        rr=[r for r in normalized if (r['session_id'],r['episode_id'])==key]
        t=np.array([r['timestamp_s'] for r in rr]);t-=t[0]
        x=np.array([r['actual_position_m'] for r in rr])*1000;u=np.array([r['command_position_m'] for r in rr])*1000
        force=np.array([r['normal_force_N'] for r in rr]);label='/'.join(key)
        line=axs[0,0].plot(t,x,label=label)[0]
        axs[0,0].plot(t,u,'--',alpha=.4,color=line.get_color())
        axs[0,1].plot(t,force,label=label);axs[1,0].plot(x,force,label=label)
        axs[1,1].plot(t[1:],np.diff(t)*1000,label=label)
    axs[0,0].set(xlabel='Time (s)',ylabel='Position (mm)',title='Actual; dashed = command')
    axs[0,1].set(xlabel='Time (s)',ylabel='Force (N)',title='Force history')
    axs[1,0].set(xlabel='Actual position (mm)',ylabel='Force (N)',title='Force-displacement path')
    axs[1,1].set(xlabel='Time (s)',ylabel='Sampling interval (ms)',title='Time-base diagnostic')
    max_interval=max(float(np.max(line.get_ydata())) for line in axs[1,1].lines)
    axs[1,1].set_ylim(0,max_interval*1.15)
    axs[1,1].ticklabel_format(axis='y',style='plain',useOffset=False)
    for ax in axs.ravel():ax.grid(alpha=.2)
    axs[0,1].legend(fontsize=7,frameon=False)
    fig.suptitle(f'{meta["data_type"]} | first {min(12,len(keys))} episodes shown; all checked')
    fig.tight_layout();fig.savefig(out/'force_displacement_diagnostics.png',dpi=160);plt.close(fig)
    print(json.dumps({'status':'passed','data_type':meta['data_type'],'episodes':len(keys),'output':str(out)},ensure_ascii=False))


if __name__=='__main__':main()
