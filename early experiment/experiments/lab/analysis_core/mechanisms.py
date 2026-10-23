"""Effective 1D material laws, SI units; no robot control.

Nonlinear equilibrium spring, positive Maxwell branches, unilateral contact.
Rates are frozen at the previous internal state in each implicit substep.
The numerical scheme is checked by step refinement, not assumed exact.
"""
import numpy as np
from numba import njit

MODELS = {'L2': (2, False, False), 'L4': (4, False, False),
          'S2': (2, True, False), 'R2': (2, False, True),
          'SR2': (2, True, True), 'S4': (4, True, False),
          'Q2': (2, True, False), 'Q4': (4, True, False),
          'L6': (6, False, False), 'S6': (6, True, False), 'Q6': (6, True, False)}

@njit(cache=True)
def spring(e, k0, alpha, ref):
    if abs(alpha) < 1e-6:
        a=alpha*e/ref
        return k0*e*(1+a/2+a*a/6), k0*(1+a+a*a/2)
    a = alpha*e/ref
    return k0*ref*np.expm1(a)/alpha, k0*np.exp(a)

@njit(cache=True)
def root_force(residual, ke, k0, alpha, ref):
    # Solve s(e) + ke*e = residual, with positive derivative.
    if residual <= 0:
        return 0.0
    if alpha == 0.:
        return residual/(k0+ke)
    lo = 0.0
    hi = max(residual/ke, ref*1e-10)
    e = min(residual/(k0+ke), hi)
    for _ in range(30):
        s, ds = spring(e, k0, alpha, ref)
        f = s + ke*e - residual
        if abs(f) < 1e-11:
            break
        if f > 0: hi = e
        else: lo = e
        candidate = e-f/(ds+ke)
        e = candidate if lo < candidate < hi else .5*(lo+hi)
    return e

@njit(cache=True)
def advance(x, v, z, value, dt, k0, k, tau, alpha, beta, ref, plant, command_mode, qlv=False):
    q = min(3., max(0., np.dot(k,z)/np.sum(k)/ref))
    effective_tau = tau*np.exp(beta*q)
    a = effective_tau/(effective_tau+dt)
    ke = np.sum(k*a)
    residual = np.dot(k*a,z)
    if qlv:
        target=residual/(k0+ke)
        free=target*(1-alpha*target/(2*ref)) if abs(alpha)<1e-8 else ref*np.log1p(alpha*target/ref)/alpha
    else:
        free = root_force(residual,ke,k0,alpha,ref)
    if command_mode:
        m, K, D = plant
        den = m + dt*D + dt*dt*K
        vf = (m*v+dt*K*(value-x))/den
        xf = x+dt*vf
        if xf <= free:
            xn = xf
        else:
            # Actuator equilibrium: F(xn) + den/dt^2*(xn-xf)=0.
            stiffness = den/(dt*dt)
            xn = root_force(residual+stiffness*xf, stiffness if qlv else ke+stiffness,
                            k0+ke if qlv else k0,alpha,ref)
        vn = (xn-x)/dt
    else:
        xn = value
        vn = (xn-x)/dt
    e = max(xn,free)
    drive=spring(e,1.,alpha,ref)[0] if qlv else e
    zn = a*z+(1-a)*drive
    force = max(0.,k0*drive+np.dot(k,drive-zn)) if qlv else max(0.,spring(e,k0,alpha,ref)[0]+np.dot(k,e-zn))
    return xn,vn,zn,force,e

@njit(cache=True)
def rollout(t, u, measured_x, k0,k,tau,alpha,beta,ref,plant,
            forecast_index=-1, max_step=.01, qlv=False):
    """Before forecast_index use measured x, afterward ONLY u.

    -1: constitutive diagnostic conditioned on measured motion throughout.
    Future measured_x is never read when forecast_index >= 0.
    Initial internal state is relaxed; this must be established experimentally.
    """
    n=len(t); z=np.zeros(len(k)); x=measured_x[0]; v=0.
    forces=np.zeros(n); xs=np.zeros(n); zs=np.zeros((n,len(k))); es=np.zeros(n)
    xs[0]=x
    for i in range(1,n):
        dt=t[i]-t[i-1]; steps=max(1,int(np.ceil(dt/max_step)))
        cmd=forecast_index >= 0 and i>=forecast_index
        previous=x
        for j in range(steps):
            fraction=(j+1)/steps
            value=u[i-1]+fraction*(u[i]-u[i-1]) if cmd else previous+fraction*(measured_x[i]-previous)
            x,v,z,f,e=advance(x,v,z,value,dt/steps,k0,k,tau,alpha,beta,ref,plant,cmd,qlv)
        xs[i]=x;forces[i]=f;zs[i]=z;es[i]=e
    return forces,xs,zs,es

def unpack(p, name):
    modes, static, rate=MODELS[name]
    k0=np.exp(p[0]); k=np.exp(p[1:1+modes]); tau=np.exp(p[1+modes:1+2*modes])
    alpha=float(p[1+2*modes]) if static else 0.
    beta=float(p[-1]) if rate else 0.
    return k0,k,tau,alpha,beta

def initial_parameters(name, ref, force_scale, duration):
    modes,static,rate=MODELS[name]
    total=max(10.,force_scale/ref)
    times=np.geomspace(.15,max(.5,min(12.,duration/4)),modes)
    p=np.r_[np.log(total*.3),np.full(modes,np.log(total*.7/modes)),np.log(times)]
    lower=np.r_[np.log(1.),np.full(modes,np.log(1.)),np.full(modes,np.log(.02))]
    upper=np.r_[np.log(1e6),np.full(modes,np.log(1e6)),np.full(modes,np.log(max(60.,duration*3)))]
    if static: p=np.r_[p,0.];lower=np.r_[lower,-2.];upper=np.r_[upper,2.]
    if rate: p=np.r_[p,0.];lower=np.r_[lower,-2.];upper=np.r_[upper,3.]
    return p,lower,upper

def parameters_json(p,name):
    k0,k,tau,alpha,beta=unpack(p,name)
    order=np.argsort(tau)
    return dict(k0_N_m=float(k0),k_N_m=k[order].tolist(),tau_s=tau[order].tolist(),
                static_alpha=alpha,rate_beta=beta)
