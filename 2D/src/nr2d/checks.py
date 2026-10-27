"""Numerical checks with explicit measured errors and pilot acceptance tolerances."""
from dataclasses import replace
import time
import numpy as np
from scipy.linalg import expm
from .physics import Config, SpatialModel
from .protocols import protocol


def run_checks(c=Config()):
    started=time.perf_counter(); rows=[]
    def add(name,value,tolerance,unit,meaning):
        rows.append(dict(check=name,error=float(value),tolerance=float(tolerance),unit=unit,
                         passed=bool(np.isfinite(value) and value<=tolerance),meaning=meaning))
    m=SpatialModel(c)
    affine=np.column_stack((.002*m.nodes[:,0]+.001*m.nodes[:,1],-.003*m.nodes[:,1])).ravel()
    add("Affine strain patch",np.max(np.abs(m.strain(affine)-[.002,-.003,.001])),1e-12,"strain",
        "Constant-strain element reproduces an affine displacement field")
    h=c.dt/4; times=np.arange(round(1.2/h)+1)*h
    z=np.zeros(2); eps=.001; numerical=[]
    for _ in times:
        numerical.append(c.E_inf*eps+np.dot(m.Ebranch,eps-z))
        a=m.tau/(m.tau+h); z=a*z+(1-a)*eps
    reference=eps*(c.E_inf+c.E_fast*np.exp(-times/c.tau_fast)+c.E_slow*np.exp(-times/c.tau_slow))
    add("Relaxation reference",np.max(np.abs(numerical-reference))/reference[0],.02,"relative",
        "Backward-Euler material-point response versus continuous Maxwell solution")
    A=(np.ones((2,1))*m.Ebranch/(c.E_inf+sum(m.Ebranch))-np.eye(2))/m.tau[:,None]
    z0=np.array([.0007,.0003]); z=z0.copy(); numerical=[]
    for t in times:
        numerical.append(np.linalg.norm(z-expm(A*t)@z0)/np.linalg.norm(z0))
        z=np.linalg.solve(np.eye(2)-h*A,z)
    add("Free recovery reference",max(numerical),.02,"relative",
        "Zero-stress two-mode recovery versus matrix-exponential solution")
    commands,phases,cut=protocol(c)
    base=m.simulate(commands,phases)
    add("Body force balance",base.diagnostics[:,0].max(),2e-7,"N","Bottom vertical reaction equals tool reaction")
    add("Tool dynamic balance",base.diagnostics[:,1].max(),2e-7,"N","Actuator - contact = mass * acceleration")
    wait=base.phase=="wait"
    add("Contact separation",base.force[wait].max(),1e-7,"N","No tensile contact; zero reaction while separated")
    add("Recontact detected",0 if base.force[base.phase=="recontact"].max()>.02 else 1,0,"flag",
        "Reaction returns after physical approach")
    add("Contact penetration",base.diagnostics[:,2].max()*1e6,5,"um","Penalty penetration, not exact complementarity")
    add("Small-strain range",base.diagnostics[:,3].max(),.06,"strain","Frobenius strain norm; synthetic small-strain scope")
    energy=base.diagnostics[wait,4]
    add("Unforced recovery energy",max(0,np.diff(energy).max()),1e-10,"J","Stored body energy cannot increase during detached wait")
    elastic=SpatialModel(replace(c,E_fast=0.,E_slow=0.))
    ec,ep,_=protocol(elastic.c)
    et=elastic.simulate(ec,ep)
    add("Elastic recovery control",np.max(np.abs(et.u[et.phase=="wait"])),1e-10,"m",
        "Zero-memory body returns to zero displacement on separation")
    last_hold=np.where(et.phase=="hold")[0][-max(2,round(.1/c.dt)):]
    add("Elastic hold drift",np.ptp(et.force[last_hold])/max(et.force.max(),1e-10),.001,"relative",
        "No constitutive relaxation for elastic material after actuator settling")
    def compare(trace,ref):
        aligned=np.interp(ref.time,trace.time,trace.force)
        return np.sqrt(np.mean((aligned-ref.force)**2))/max(np.sqrt(np.mean(ref.force**2)),1e-12)
    time_traces=[]
    for dt in (c.dt/2,c.dt/4):
        cc=replace(c,dt=dt); u,p,_=protocol(cc)
        time_traces.append(SpatialModel(cc).simulate(u,p))
    add("Time-step convergence",compare(base,time_traces[-1]),.05,"NRMSE", "Default dt versus dt/4 over the full episode")
    add("Time refinement trend",compare(time_traces[0],time_traces[-1]),.035,"NRMSE", "dt/2 versus dt/4")
    refined=[]
    for scale in (1.5,2):
        cc=replace(c,nx=int(c.nx*scale),ny=int(c.ny*scale)); u,p,_=protocol(cc)
        refined.append(SpatialModel(cc).simulate(u,p))
    add("Mesh convergence",compare(base,refined[-1]),.05,"NRMSE","Default mesh versus double resolution")
    add("Mesh refinement trend",compare(refined[0],refined[-1]),.035,"NRMSE","1.5x mesh versus 2x mesh")
    stiff=replace(c,penalty=2*c.penalty); u,p,_=protocol(stiff)
    stiff_trace=SpatialModel(stiff).simulate(u,p)
    add("Penalty sensitivity",compare(base,stiff_trace),.02,"NRMSE","Double contact penalty")
    return dict(rows=rows,passed=all(r["passed"] for r in rows),wall_seconds=time.perf_counter()-started,
                config=c.asdict(),scope="Synthetic quasistatic 2D body + dynamic tool; not real-material validation"),base
