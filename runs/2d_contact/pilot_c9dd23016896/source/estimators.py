"""Model-based finite-window inference with measured motion and sensor residuals.

Finite-window states use a six-coefficient, model-derived initial-strain basis.
Full-history replay uses the shared known relaxed start. No internal truth labels
are given to these estimators. All predictions use the same spatial solver.
"""
from dataclasses import dataclass
import time
import numpy as np
from scipy.optimize import least_squares
from .physics import State, SpatialModel, Trace
from .protocols import future_commands

METHODS=["Snapshot","Short classical","Full classical","True state"]
COLORS={"Snapshot":"#C04A32","Short classical":"#D69A20","Full classical":"#167A70","True state":"#253D65"}
# Synthetic deployment resolutions/noise, not measured real sensor specifications.
RESOLUTION=np.array([2e-6,5e-5,.006,5e-6,5e-6])
NOISE_STD=np.array([.5e-6,1e-5,.0015,1e-6,1e-6])


@dataclass
class Estimate:
    state: State
    seconds: float
    diagnostics: dict


class Observer:
    def __init__(self,model: SpatialModel):
        self.model=model
        zero=model.initial().z
        # Model-generated elastic load shapes, fixed before evaluation histories.
        self.basis=np.array([model.strain(model.equilibrate(zero,d)) for d in (.0001,.00028,.00045)])

    def observations(self,trace,noise=0.,seed=123):
        rng=np.random.default_rng(seed)
        obs=trace.observation.copy()
        obs += rng.normal(size=obs.shape)*NOISE_STD*noise
        return obs

    def infer(self,trace: Trace,window,obs=None):
        start=time.perf_counter(); m=self.model
        obs=trace.observation if obs is None else obs
        n=len(trace.time)-1
        if window == "full":
            replay=m.simulate(trace.command[1:],trace.phase[1:],state=m.initial(),
                              actual_positions=obs[1:,0])
            state=replay.checkpoint(); state.d=float(obs[-1,0]); state.v=float(obs[-1,1])
            return Estimate(state,time.perf_counter()-start,dict(window="full",known_relaxed_start=True,
                            internal_truth_used=False,solver_steps=n,observation_use="actual tool position drives material replay"))
        steps=min(n,max(0,round(float(window)/m.c.dt)))
        begin=n-steps
        scale=np.array([.004,3e-6,3e-6])
        calls=0
        def rollout(coeff):
            z=np.einsum("ij,jab->iab",coeff.reshape(2,3),self.basis)
            d=float(obs[begin,0])
            u=m.equilibrate(z,d)
            state=State(u,z,d,float(obs[begin,1]),float(trace.time[begin]))
            if steps:
                tr=m.simulate(trace.command[begin+1:],trace.phase[begin+1:],state=state,
                              actual_positions=obs[begin+1:,0])
                return tr.checkpoint(),tr.observation[:,2:]
            force=m.contact(u,d)[2]
            return state,np.r_[force,m.marker_values(u)][None,:]
        def residual(coeff):
            nonlocal calls
            calls+=1
            _,prediction=rollout(coeff)
            error=(prediction-obs[begin:,2:])/scale
            # Mild minimum-norm regularization resolves unobservable initial fields.
            return np.r_[error.ravel()/np.sqrt(len(error)),.015*coeff]
        result=least_squares(residual,np.full(6,.12),bounds=(0,2.5),max_nfev=7,
                             ftol=1e-5,xtol=1e-5,gtol=1e-5,diff_step=1e-3)
        state,prediction=rollout(result.x)
        state.d=float(obs[-1,0]); state.v=float(obs[-1,1])
        return Estimate(state,time.perf_counter()-start,dict(window_seconds=steps*m.c.dt,
                        basis_coefficients=result.x.tolist(),basis_size=6,known_relaxed_start=False,
                        internal_truth_used=False,solver_calls=calls,optimizer_status=int(result.status),
                        optimizer_success=bool(result.success),weighted_residual=float(np.linalg.norm(result.fun)),
                        approximation="Nonnegative initial-strain basis; complete spatial future model"))


def compare_predictions(model,trace,action="Slow press",noise=0.,observer=None,seed=123,progress=None):
    observer=Observer(model) if observer is None else observer
    obs=observer.observations(trace,noise,seed)
    estimates={}
    for label,window in zip(METHODS[:3],(0,.2,"full")):
        if progress: progress(label)
        estimates[label]=observer.infer(trace,window,obs)
    estimates["True state"]=Estimate(trace.checkpoint(),0.,dict(privileged=True,scope="same solver and future commands"))
    # Commands are fixed from the true physical checkpoint as the selected intervention;
    # no future achieved motion is supplied to any predictor.
    commands,phases=future_commands(trace.checkpoint(),model.c,action)
    forecasts={name:model.simulate(commands,phases,state=estimate.state,
                                  metadata={"method":name,"action":action}) for name,estimate in estimates.items()}
    truth=forecasts["True state"]
    metrics={name:dict(force_rmse_N=float(np.sqrt(np.mean((tr.force-truth.force)**2))),
                       marker_rmse_m=float(np.sqrt(np.mean((tr.markers-truth.markers)**2))),
                       inference_seconds=estimates[name].seconds,
                       inference=estimates[name].diagnostics) for name,tr in forecasts.items()}
    return forecasts,metrics


def history_sweep(model,trace,noise=0.,action="Slow press",observer=None,progress=None):
    observer=Observer(model) if observer is None else observer
    obs=observer.observations(trace,noise,123)
    commands,phases=future_commands(trace.checkpoint(),model.c,action)
    truth=model.simulate(commands,phases,state=trace.checkpoint())
    rows=[]
    windows=[0,.04,.1,.2,.4,.8]
    windows=[w for w in windows if w<trace.time[-1]-trace.time[0]]+["full"]
    for window in windows:
        if progress: progress(str(window))
        estimate=observer.infer(trace,window,obs)
        prediction=model.simulate(commands,phases,state=estimate.state)
        rows.append(dict(window=window,window_seconds=float(trace.time[-1]-trace.time[0]) if window=="full" else float(window),
                         force_rmse_N=float(np.sqrt(np.mean((prediction.force-truth.force)**2))),
                         marker_rmse_m=float(np.sqrt(np.mean((prediction.markers-truth.markers)**2))),
                         inference_seconds=estimate.seconds,diagnostics=estimate.diagnostics))
    return rows
