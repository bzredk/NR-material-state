"""Construct physically replayed histories with matched present observations.
This is a designed mechanism witness, NOT an additional training/test split.
"""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache'/'matplotlib'))
import argparse
import json
import numpy as np
from scipy.linalg import null_space
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from physics import Material, simulate


def witness(cfg):
    dt=cfg['dt']/4;t=np.arange(round(3./dt)+1)*dt
    base=np.interp(t,[0,.3,.8,3.],[-.004,-.004,.006,.006])
    mat=Material.from_dict(cfg['truth'])
    def end(u):
        y,z,_,_=simulate(u[None],mat,cfg['plant'],dt)
        return y[0,-1],z[0,-1]
    y0,z0=end(base)
    # Smooth input perturbations, zero at both start and forecast cut.
    bases=np.stack([np.exp(-((t-c)/w)**2)
                    for c,w in zip([1.4,2.6,2.96,2.98],[.5,.15,.01,.01])])
    bases[:,-1]=0
    step_size=.0001
    J=np.stack([(end(base+step_size*b)[0]-y0)/step_size for b in bases],1)
    # Whiten observable units for a well-conditioned null-space calculation.
    null=null_space(J/np.array([.006,.02,8.])[:,None])[:,0]
    perturb=null@bases
    perturb*=.002/np.max(np.abs(perturb))
    modified=base+perturb
    y1,z1=end(modified)
    assert np.max(np.abs(y1-y0))<1e-8, (y0,y1)
    assert np.linalg.norm(z1-z0)>1e-7
    ft=np.arange(1,round(4.2/dt)+1)*dt
    common=np.interp(ft,[0,.3,.6,1.6,2.,4.2],[.006,.006,-.004,-.004,.006,.006])
    yA,zA,_,_=simulate(common[None],mat,cfg['plant'],dt,(y0[:1],y0[1:2],z0[None]))
    yB,zB,_,_=simulate(common[None],mat,cfg['plant'],dt,(y1[:1],y1[1:2],z1[None]))
    return t,base,modified,y0,y1,z0,z1,ft,common,yA[0],yB[0]


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default=str(ROOT/'runs'/'pilot_v1'))
    out=Path(p.parse_args().output).resolve()
    if not out.is_relative_to(ROOT):raise ValueError('Project-local outputs only')
    cfg=json.loads((out/'config.json').read_text())
    t,a,b,y0,y1,z0,z1,ft,u,ya,yb=witness(cfg)
    report={'purpose':'Designed replayable history witness, separate from main benchmark.',
            'diagnostic_dt_s':cfg['dt']/4,
            'current_observables_A':y0.tolist(),'current_observables_B':y1.tolist(),
            'max_current_observable_abs_difference':float(np.max(np.abs(y1-y0))),
            'current_observable_abs_difference':dict(zip(['position_m','velocity_m_s','force_N'],np.abs(y1-y0).tolist())),
            'internal_z_A_m':z0.tolist(),'internal_z_B_m':z1.tolist(),
            'future_peak_force_difference_N':float(np.max(np.abs(ya[:,2]-yb[:,2]))),
            'recontact_peak_force_difference_N':float(np.max(np.abs(ya[ft>=1.6,2]-yb[ft>=1.6,2]))),
            'difference_definition':'Maximum absolute pointwise force difference, not difference between two curve maxima.',
            'method':'Null space of endpoint observable response to smooth past command perturbations; replayed through unilateral simulator.'}
    (out/'alias_witness.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    np.savez_compressed(out/'alias_witness.npz',history_time=t,history_a=a,history_b=b,
                        future_time=ft,commands=u,future_a=ya,future_b=yb)
    fig,axs=plt.subplots(3,1,figsize=(10,8))
    axs[0].plot(t,a*1000,label='History A');axs[0].plot(t,b*1000,label='History B')
    axs[0].set_ylabel('Past command (mm)');axs[0].set_xlabel('History time (s)');axs[0].legend(frameon=False)
    axs[0].set_title('Different replayed histories, same current position / velocity / force')
    axs[1].plot(ft,ya[:,2],label='Future A');axs[1].plot(ft,yb[:,2],label='Future B')
    axs[1].set_ylabel('Force (N)');axs[1].legend(frameon=False)
    axs[2].plot(ft,yb[:,2]-ya[:,2],color='#8a4a86');axs[2].axhline(0,color='k',lw=.5)
    axs[2].set_ylabel('Force B - A (N)');axs[2].set_xlabel('Time after common future starts (s)')
    for ax in axs[1:]:ax.axvspan(.6,1.6,color='#efe8dc',alpha=.6)
    for ax in axs:ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
    fig.tight_layout();(out/'figures').mkdir(exist_ok=True)
    fig.savefig(out/'figures'/'05_matched_present_different_future.png',dpi=180)
    plt.close(fig)
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
