"""Feasible command histories and future interventions; no hidden-state editing."""
import numpy as np
from .physics import Config


def protocol(config=Config(), amplitude=0.00045, hold=0.45, wait=0.3,
             loading=0.35, release=0.25, include_future=True, excitation="hold"):
    values=[]; phases=[]; current=-config.clearance
    def ramp(target,duration,name):
        nonlocal current
        n=max(1,round(duration/config.dt))
        values.extend(np.linspace(current,target,n+1)[1:])
        phases.extend([name]*n); current=target
    ramp(amplitude,loading,"load")
    if excitation == "pulse":
        ramp(amplitude*.65,hold/3,"hold")
        ramp(amplitude*1.1,hold/3,"hold")
        ramp(amplitude,hold/3,"hold")
    else:
        ramp(amplitude,hold,"hold")
    ramp(-config.clearance,release,"release")
    ramp(-config.clearance,wait,"wait")
    cut=len(values)
    if include_future:
        ramp(0.0004,.5,"recontact")
        ramp(0.0004,.6,"final hold")
        ramp(-config.clearance,.3,"withdraw")
    return np.array(values),np.array(phases),cut


def future_commands(state,config,action="Slow press",duration=1.0):
    n=round(duration/config.dt)
    t=np.arange(1,n+1)*config.dt
    if action == "Release":
        target=-config.clearance; ramp=.2
    elif action == "Hold":
        target=state.d; ramp=.1
    else:
        target=.0004; ramp=.2 if action == "Fast press" else .65
    command=state.d+(target-state.d)*np.minimum(t/ramp,1)
    return command,np.full(n,action)
