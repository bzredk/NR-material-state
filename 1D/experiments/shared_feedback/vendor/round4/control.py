"""Same 100 Hz observations, 50 Hz actions, command bounds and slew limit.

Predictive variants share one receding-horizon shooting controller and one
causal material observer. Only initialization (or the labelled oracle access)
changes. Reactive control has the same continuous command-rate action space.
"""
import numpy as np
from numba import njit
from physics import advance,force,material_observed,TRUTH,FITTED

GOAL=.004;TARGET=.0041;DT=.01;RMAX=.04;UMIN=-.004;UMAX=.0085

@njit(cache=True,inline='always')
def reactive_rate(x,v,F,cap,parameters):
    kp,kf,kd,buffer=parameters
    position_rate=kp*(TARGET-x)-kd*v
    force_rate=kf*(cap-buffer-max(F,0.))
    return min(RMAX,max(-RMAX,min(position_rate,force_rate)))

@njit(cache=True)
def observer(z,P,x0,x,F,p,contact_authorized=True):
    """Motion-driven prediction; scalar force update only in observed contact.

    Free force=0 is an inequality, not a fictitious equality measurement.
    All non-oracle predictive methods use identical covariance/noise settings.
    """
    kt=p[0]+p[1]+p[2];q=(p[1]*z[0]+p[2]*z[1])/kt
    z=material_observed(z,x0,x,p,DT,5)
    A=np.zeros((2,2));A[0,0]=-1/p[3];A[1,1]=-1/p[4]
    if .5*(x0+x)<q:
        A[0,0]+=p[1]/kt/p[3];A[0,1]=p[2]/kt/p[3]
        A[1,0]=p[1]/kt/p[4];A[1,1]+=p[2]/kt/p[4]
    M=np.eye(2)+DT*A+.5*DT*DT*(A@A)
    P=M@P@M.T+np.eye(2)*4e-12
    if F>.06 and x>0. and contact_authorized:
        H=np.array([-p[1],-p[2]]);R=.02**2+(kt*5e-6)**2
        PH=P@H;S=H@PH+R;gain=PH/S
        z=z+gain*(F-(kt*x-p[1]*z[0]-p[2]*z[1]))
        M=np.eye(2)-gain.reshape(2,1)*H.reshape(1,2)
        P=M@P@M.T+R*gain.reshape(2,1)*gain.reshape(1,2)
    return z,P

@njit(cache=True)
def predict_candidate(s,u,first_rate,K,D,p,cap,margin,reactive_parameters,horizon_steps,nsub,held=0):
    """First 20 ms action followed by the SAME reactive tail in every model.

    Tail observations are predicted from the candidate rollout, never read
    from future data. This makes the reactive action itself an explicit MPC
    candidate, and gives both controller families a strong goal-aware policy.
    """
    peak=force(s,p);shortfall=0.;rate=first_rate;finish=-1;count=held
    tail=reactive_parameters.copy();tail[3]=max(tail[3],margin)
    for j in range(horizon_steps):
        if finish>=0:rate=-RMAX
        elif j>=2 and j%2==0:rate=reactive_rate(s[0],s[1],force(s,p),cap,tail)
        un=min(UMAX,max(UMIN,u+DT*rate));s,pk,_=advance(s,u,un,K,D,p,DT,nsub);u=un
        peak=max(peak,pk)
        if finish<0:
            shortfall+=max(GOAL-s[0],0.)/GOAL
            count=count+1 if s[0]>=GOAL and force(s,p)>.02 else 0
            if count>=20:finish=j+1
    cost=(finish if finish>=0 else horizon_steps+20-count)*DT+.2*shortfall/horizon_steps
    if finish<0:cost+=.2*max(GOAL-s[0],0.)/GOAL
    return cost,peak

@njit(cache=True)
def mpc_rate(s,u,K,D,p,cap,margin,params,horizon_steps,nsub,held=0):
    r0=reactive_rate(s[0],s[1],force(s,p),cap,params)
    best=1e100;selected=r0;bestpeak=1e100;pred_peak=0.;any_safe=False
    # Continuous actuator freedom is common. MPC approximates its search with
    # a fixed grid plus the exact continuous reactive proposal.
    rates=np.array([r0,-0.04,-.03,-.02,-.01,0.,.01,.02,.03,.04])
    for r in rates:
        cost,peak=predict_candidate(s.copy(),u,r,K,D,p,cap,margin,params,horizon_steps,nsub,held)
        cost+=1e-5*abs(r-r0)/RMAX
        safe=peak<=cap-margin
        if safe:
            if not any_safe or cost<best:
                selected=r;best=cost;pred_peak=peak
            any_safe=True
        elif not any_safe and (peak<bestpeak-1e-10 or (abs(peak-bestpeak)<1e-10 and cost<best)):
            bestpeak=peak;selected=r;best=cost;pred_peak=peak
    return selected,pred_peak

@njit(cache=True)
def episode(s0,z0,K,D,wait,cap,noise,params,margin,horizon_steps,kind,
            update=True,truth_nsub=10,model_nsub=10,keep_trace=False):
    """kind 0 reactive, 1 predictive (fixed fitted physics), 2 full-state oracle.

    All run to the same goal hold (200 ms), then common rate-limited release
    (350 ms); force safety includes the complete release. Failure cost is 5 s.
    Unknown future real motion and force are never inputs to the planner.
    """
    s=s0.copy();z=z0.copy();P=np.eye(2)*.0015**2;u=UMIN;rate=0.;hold=0
    done=-1;release_left=-1;peak=0.;excess_integral=0.;first_contact=-1.;prediction=0.;observed_hold=0;positive_force_count=0
    trace=np.full((436 if keep_trace else 1,16),np.nan)
    prev_x=s[0]+noise[0,0];last_rmse=0.;errsum=0.;errcount=0;calls=0
    for t in range(435):
        if t>=400 and done<0:break
        x=s[0]+noise[t,0];v=s[1]+noise[t,1];F=force(s,TRUTH)+noise[t,2]
        observed_hold=observed_hold+1 if x>=GOAL and F>.02 and t*DT>=wait else 0
        positive_force_count=positive_force_count+1 if F>.06 and x>0. else 0
        if t:
            if update:z,P=observer(z,P,prev_x,x,F,FITTED,positive_force_count>=2)
            else:z=material_observed(z,prev_x,x,FITTED,DT,5)
        prev_x=x
        if kind==2:
            model_s=s.copy();p=TRUTH
        else:
            model_s=np.array([x,v,z[0],z[1]]);p=FITTED
        errsum+=np.sum(((s[2:] if kind==2 else z)-s[2:])**2);errcount+=1
        if keep_trace:
            trace[t]=np.array([t*DT,u,s[0],s[1],force(s,TRUTH),s[2],s[3],z[0],z[1],rate,prediction,F,x,v,float(hold),float(done)])
        if done>=0:
            rate=-RMAX
            if release_left<=0:break
            release_left-=1
        elif t*DT<wait-1e-10:rate=0.
        elif t%2==0:
            if kind==0:rate=reactive_rate(x,v,F,cap,params)
            else:
                rate,prediction=mpc_rate(model_s,u,K,D,p,cap,margin,params,horizon_steps,model_nsub,min(observed_hold,19));calls+=1
        un=min(UMAX,max(UMIN,u+DT*rate))
        sn,pk,imp=advance(s,u,un,K,D,TRUTH,DT,truth_nsub)
        # Integrate violation dose on the same fine execution grid (not tick peaks).
        if pk>cap:
            ss=s.copy();h=DT/truth_nsub
            for j in range(truth_nsub):
                a=u+(un-u)*j/truth_nsub;b=u+(un-u)*(j+1)/truth_nsub
                ss,_,_=advance(ss,a,b,K,D,TRUTH,h,1)
                excess_integral+=h*max(force(ss,TRUTH)-cap,0.)
        s=sn;u=un;peak=max(peak,pk)
        if first_contact<0 and pk>.02:first_contact=(t+1)*DT
        if done<0:
            hold=hold+1 if s[0]>=GOAL and force(s,TRUTH)>.02 and (t+1)*DT>=wait else 0
            if hold>=20:done=t+1;release_left=35
    complete=done>=0;time=done*DT if complete else 4.;unsafe=peak>cap
    cost=time if complete and not unsafe else 5.
    return np.array([time,peak,1. if complete else 0.,1. if unsafe else 0.,1. if complete and not unsafe else 0.,cost,
                     max(peak-cap,0.),excess_integral,first_contact,np.sqrt(errsum/max(errcount,1)/2),calls]),trace

@njit(cache=True)
def batch(s,z,controls,waits,caps,noise,params,margin,horizon_steps,kind,update=True,truth_nsub=10,model_nsub=10):
    out=np.empty((len(s),11))
    for n in range(len(s)):
        out[n]=episode(s[n],z[n],controls[n,0],controls[n,1],waits[n],caps[n],noise[n],params,margin,
                       horizon_steps,kind,update,truth_nsub,model_nsub,False)[0]
    return out
