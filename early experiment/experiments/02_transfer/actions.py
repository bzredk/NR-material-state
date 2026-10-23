"""Identical finite-action selector for every predictive model.

Completion requires 0.2 s continuously at target after re-approach starts.
Peak force includes the ENTIRE five-second rollout, including initial release
and any overshoot after first reaching the goal. Rejection is a failure, not a
free success. Reactive control is reported separately: it observes feedback.
"""
import numpy as np
from numba import njit
from dynamics import constants


@njit(cache=True)
def response_metrics(y,onsets,dt,goal,hold):
    B,T,_=y.shape;time=np.full(B,np.inf);peak=np.empty(B)
    required=int(round(hold/dt))
    for n in range(B):
        count=0
        for t in range(T):
            if (t+1)*dt>=onsets[n] and y[n,t,0]>=goal and y[n,t,2]>.02:count+=1
            else:count=0
            if count>=required:
                time[n]=(t+1)*dt;break
        peak[n]=np.max(y[n,:,2])
    return time,peak


def select(pred_time,pred_peak,cap,margin):
    feasible=np.isfinite(pred_time)&(pred_peak<=cap-margin)
    costs=np.where(feasible,pred_time,np.inf)
    choice=np.argmin(costs,axis=-1)
    return np.where(np.any(feasible,axis=-1),choice,-1)


def outcomes(choice,true_time,true_peak,cap,horizon):
    idx=np.maximum(choice,0)[...,None]
    time=np.take_along_axis(true_time,idx,axis=-1)[...,0]
    peak=np.take_along_axis(true_peak,idx,axis=-1)[...,0]
    execute=choice>=0;unsafe=execute&(peak>cap)
    success=execute&~unsafe&np.isfinite(time)
    return dict(choice=choice,success=success,unsafe=unsafe,reject=~execute,
        cost=np.where(success,time,horizon+1),time=np.where(execute,time,np.nan),
        peak=np.where(execute,peak,np.nan))


@njit(cache=True)
def reactive_rollout(initial,z0,start_u,controls,waits,caps,c,dt,T,speed,buffer,gain,noise):
    k0,k1,k2,t1,t2,m,_=c;a=np.array([t1/(t1+dt),t2/(t2+dt)]);b=1-a;k=np.array([k1,k2]);ka=k*a;ke=k0+ka.sum()
    B=len(initial);y=np.empty((B,T,3));us=np.empty((B,T))
    for n in range(B):
        K,D=controls[n];den=m+dt*D+dt*dt*K;x,v=initial[n];z=z0[n].copy();u=start_u[n]
        f=max((k0+k1+k2)*x-k@z,0.)
        for t in range(T):
            time=(t+1)*dt
            if time<=.3:u=start_u[n]+(-.004-start_u[n])*time/.3
            elif time<=.3+waits[n]:u=-.004
            else:
                rate=min(speed,max(-speed,gain*(caps[n]-buffer-f-noise[n,t])))
                u=min(.0075,max(-.004,u+dt*rate))
            r=ka@z;vf=(m*v+dt*K*(u-x))/den
            v=vf if x+dt*vf<=r/ke else (m*v+dt*K*(u-x)-dt*(ke*x-r))/(den+dt*dt*ke)
            x+=dt*v;e=max(x,r/ke);f=max(ke*x-r,0.);z=a*z+b*e
            y[n,t,0]=x;y[n,t,1]=v;y[n,t,2]=f;us[n,t]=u
    return y,us


def run_reactive(cfg,d,controls,waits,caps,parameters,seed=9001):
    N=len(d['history']);C=len(controls);W=len(waits);L=len(caps);shape=(N,2,C,W,L)
    initial=np.broadcast_to(d['initial'][:,:,None,None,None],(*shape,2)).reshape(-1,2).copy()
    z=np.broadcast_to(d['z'][:,:,None,None,None],(*shape,2)).reshape(-1,2).copy()
    u0=np.broadcast_to(d['history'][:,:,-1,3,None,None,None],shape).reshape(-1).astype(float)
    ctrl=np.broadcast_to(np.array(controls)[None,None,:,None,None,:],(*shape,2)).reshape(-1,2).copy()
    wait=np.broadcast_to(np.array(waits)[None,None,None,:,None],shape).reshape(-1).copy()
    cap=np.broadcast_to(np.array(caps)[None,None,None,None,:],shape).reshape(-1).copy()
    T=round(cfg['future_seconds']/cfg['dt']);rng=np.random.default_rng(seed)
    # Same noise stream reused for every reactive tuning candidate.
    noise=rng.normal(0,cfg['sensor_std']['force'],(len(z),T))
    y,u=reactive_rollout(initial,z,u0,ctrl,wait,cap,constants(cfg['truth'],cfg),cfg['dt'],T,
                        parameters['speed'],parameters['buffer'],parameters['gain'],noise)
    time,peak=response_metrics(y,.3+wait,cfg['dt'],cfg['goal_position'],cfg['goal_hold_seconds'])
    success=np.isfinite(time)&(peak<=cap);unsafe=peak>cap
    return dict(time=time.reshape(shape),peak=peak.reshape(shape),success=success.reshape(shape),
                unsafe=unsafe.reshape(shape),cost=np.where(success,time,cfg['future_seconds']+1).reshape(shape))
