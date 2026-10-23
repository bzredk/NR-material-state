"""Continuous compliant Maxwell contact, SI units, RK4 with fixed command knots.

The sensor/command clock is separate from the integration grid. Commands are
piecewise linear between 10 ms knots; force peaks include every internal step.
No impulses, penetration clipping, or reset of detached material memory.
"""
import numpy as np
from numba import njit

TRUTH=np.array([400.,900.,1300.,.15,1.4,.35])
FITTED=np.array([399.9729394562822,898.8798015826692,1299.3765224561262,
                 .15053599295540507,1.4006405501416743,.35])

@njit(cache=True,inline='always')
def force(s,p):
    return max((p[0]+p[1]+p[2])*s[0]-p[1]*s[2]-p[2]*s[3],0.)

@njit(cache=True,inline='always')
def rhs(s,u,K,D,p):
    k0,k1,k2,t1,t2,m=p
    q=(k1*s[2]+k2*s[3])/(k0+k1+k2);e=max(s[0],q)
    f=max((k0+k1+k2)*s[0]-k1*s[2]-k2*s[3],0.)
    return np.array([s[1],(K*(u-s[0])-D*s[1]-f)/m,(e-s[2])/t1,(e-s[3])/t2])

@njit(cache=True,inline='always')
def rhs_tuple(x,v,z1,z2,u,K,D,p):
    k0,k1,k2,t1,t2,m=p;kt=k0+k1+k2;q=(k1*z1+k2*z2)/kt;e=max(x,q)
    return v,(K*(u-x)-D*v-max(kt*x-k1*z1-k2*z2,0.))/m,(e-z1)/t1,(e-z2)/t2

@njit(cache=True,inline='always')
def rk4_tuple(x,v,z1,z2,u0,u1,K,D,p,h):
    a,b,c,d=rhs_tuple(x,v,z1,z2,u0,K,D,p)
    e,f,g,j=rhs_tuple(x+h*a/2,v+h*b/2,z1+h*c/2,z2+h*d/2,(u0+u1)/2,K,D,p)
    k,l,m,n=rhs_tuple(x+h*e/2,v+h*f/2,z1+h*g/2,z2+h*j/2,(u0+u1)/2,K,D,p)
    o,q,r,s=rhs_tuple(x+h*k,v+h*l,z1+h*m,z2+h*n,u1,K,D,p)
    return x+h/6*(a+2*e+2*k+o),v+h/6*(b+2*f+2*l+q),z1+h/6*(c+2*g+2*m+r),z2+h/6*(d+2*j+2*n+s)

@njit(cache=True,inline='always')
def rk4(s,u0,u1,K,D,p,h):
    return np.array(rk4_tuple(s[0],s[1],s[2],s[3],u0,u1,K,D,p,h))

@njit(cache=True)
def advance(s,u0,u1,K,D,p,dt,nsub):
    h=dt/nsub;peak=force(s,p);impulse=0.;x,v,z1,z2=s;kt=p[0]+p[1]+p[2]
    for j in range(nsub):
        x,v,z1,z2=rk4_tuple(x,v,z1,z2,u0+(u1-u0)*j/nsub,u0+(u1-u0)*(j+1)/nsub,K,D,p,h)
        f=max(kt*x-p[1]*z1-p[2]*z2,0.);peak=max(peak,f);impulse+=h*f
    return np.array([x,v,z1,z2]),peak,impulse

@njit(cache=True)
def rollout(s0,commands,controls,p,dt=.01,nsub=10):
    """Includes initial sample; arrays B,T and B,T-1,2; output states and peaks."""
    B,T=commands.shape;states=np.empty((B,T,4));peaks=np.empty((B,T-1))
    for n in range(B):
        s=s0[n].copy();states[n,0]=s
        for t in range(T-1):
            s,peak,_=advance(s,commands[n,t],commands[n,t+1],controls[n,t,0],controls[n,t,1],p,dt,nsub)
            states[n,t+1]=s;peaks[n,t]=peak
    return states,peaks

def observations(states,p=TRUTH):
    f=np.maximum((p[0]+p[1]+p[2])*states[...,0]-states[...,2]*p[1]-states[...,3]*p[2],0.)
    return np.stack([states[...,0],states[...,1],f],-1)

@njit(cache=True)
def material_observed(z,x0,x1,p,dt=.01,nsub=5):
    """Integrate only material state, using interpolated measured motion."""
    h=dt/nsub
    def dz(q,x):
        e=max(x,(p[1]*q[0]+p[2]*q[1])/(p[0]+p[1]+p[2]))
        return np.array([(e-q[0])/p[3],(e-q[1])/p[4]])
    for j in range(nsub):
        a=x0+(x1-x0)*j/nsub;b=x0+(x1-x0)*(j+1)/nsub
        k1=dz(z,a);k2=dz(z+h/2*k1,(a+b)/2);k3=dz(z+h/2*k2,(a+b)/2);k4=dz(z+h*k3,b)
        z=z+h/6*(k1+2*k2+2*k3+k4)
    return z

@njit(cache=True)
def classical_history(hist,p=FITTED,dt=.01):
    out=np.zeros((len(hist),2))
    for n in range(len(hist)):
        z=np.zeros(2)
        for t in range(1,hist.shape[1]):z=material_observed(z,hist[n,t-1,0],hist[n,t,0],p,dt)
        out[n]=z
    return out
