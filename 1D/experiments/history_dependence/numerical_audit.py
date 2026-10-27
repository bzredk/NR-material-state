"""Small TRAIN-only integration audit; never used for model selection."""
from pathlib import Path
import argparse,json
import numpy as np
from data import history_pair,future_commands
from physics import Material,simulate


def main():
    root=Path(__file__).resolve().parent
    p=argparse.ArgumentParser();p.add_argument('--output',default=str(root/'runs/round2_v1'))
    out=Path(p.parse_args().output).resolve()
    if not out.is_relative_to(root):raise ValueError('Project-local outputs required')
    cfg=json.loads((out/'config.json').read_text());rows=[];mat=Material.from_dict(cfg['truth'])
    for seed in range(cfg['data_seed'],cfg['data_seed']+8):
        hu,hy,hz,_,_,_=history_pair(cfg,seed)
        fu,mask,onset=future_commands(cfg,seed,1.,hu[0,-1]);B=np.repeat(fu[None],2,0)
        base=simulate(B,mat,cfg['plant'],cfg['dt'],(hy[:,-1,0],hy[:,-1,1],hz[:,-1]))[0]
        base_delta=base[1,:,2]-base[0,:,2]
        for factor in [2,4]:
            c=dict(cfg,dt=cfg['dt']/factor)
            ht=np.arange(hu.shape[1])*cfg['dt'];ft=np.arange(1,len(fu)+1)*cfg['dt']
            fine_ht=np.arange((len(ht)-1)*factor+1)*c['dt'];fine_ft=np.arange(1,len(fu)*factor+1)*c['dt']
            fine_hu=np.stack([np.interp(fine_ht,ht,uu) for uu in hu])
            y,z,_,_=simulate(fine_hu,mat,cfg['plant'],c['dt'])
            fine_fu=np.interp(fine_ft,np.r_[0.,ft],np.r_[hu[0,-1],fu])
            # Same physical forecast initial state, finer future integration.
            fine_y=simulate(np.repeat(fine_fu[None],2,0),mat,cfg['plant'],c['dt'],
                            (hy[:,-1,0],hy[:,-1,1],hz[:,-1]))[0][:,factor-1::factor]
            delta=fine_y[1,:,2]-fine_y[0,:,2]
            # Independently reconstruct a matched history pair at the finer grid.
            rhu,rhy,rhz,_,_,_=history_pair(c,seed)
            rfu,rmask,_=future_commands(c,seed,1.,rhu[0,-1])
            ry=simulate(np.repeat(rfu[None],2,0),mat,c['plant'],c['dt'],(rhy[:,-1,0],rhy[:,-1,1],rhz[:,-1]))[0]
            rows.append(dict(seed=seed,dt=c['dt'],
                fixed_initial_effect_RMS_N=float(np.sqrt(np.mean(delta[mask]**2))),
                coarse_effect_RMS_N=float(np.sqrt(np.mean(base_delta[mask]**2))),
                fixed_initial_effect_discrepancy_N=float(np.sqrt(np.mean((delta[mask]-base_delta[mask])**2))),
                same_past_command_endpoint_force_mismatch_N=float(abs(y[1,-1,2]-y[0,-1,2])),
                reconstructed_endpoint_force_mismatch_N=float(abs(rhy[1,-1,2]-rhy[0,-1,2])),
                reconstructed_effect_RMS_N=float(np.sqrt(np.mean((ry[1,rmask,2]-ry[0,rmask,2])**2)))))
    report=dict(scope='8 training seeds, wait 1s, not a model-performance test',rows=rows,
       interpretation='Endpoint matching is exact at the construction timestep. Same-input finer integration may change endpoint matching; separately reconstructed finer-grid pairs test whether the alias mechanism persists.')
    (out/'numerical_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    for dt in [.005,.0025]:
        rr=[r for r in rows if r['dt']==dt]
        print(dt,{k:float(np.mean([r[k] for r in rr])) for k in rr[0] if k not in ['seed','dt']})


if __name__=='__main__':main()
