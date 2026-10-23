"""Implicit unilateral contact mechanics, with per-trajectory known impedance.

Only the initial material state (or the temporal closure) receives gradients.
No future measurement is an input. Numba evaluates exact piecewise derivatives;
GRU encoders/decoders and their optimization run on CUDA.
"""
import numpy as np
import torch
from numba import njit


@njit(cache=True)
def state_rollout(z0, initial, u, controls, c, jacobian=False):
    k0,k1,k2,t1,t2,m,dt,switch,oldK,oldD=c
    a=np.array([t1/(t1+dt),t2/(t2+dt)]);b=1-a;k=np.array([k1,k2]);ka=k*a;ke=k0+ka.sum()
    B,T=u.shape;y=np.empty((B,T,3));J=np.zeros((B,T if jacobian else 1,3,2))
    for n in range(B):
        x,v=initial[n];z=z0[n].copy();dx=np.zeros(2);dv=np.zeros(2);dz=np.eye(2)
        for t in range(T):
            K,D=(oldK,oldD) if (t+1)*dt<=switch+1e-12 else (controls[n,0],controls[n,1])
            den=m+dt*D+dt*dt*K
            r=ka@z;vf=(m*v+dt*K*(u[n,t]-x))/den;free=x+dt*vf<=r/ke
            vn=vf if free else (m*v+dt*K*(u[n,t]-x)-dt*(ke*x-r))/(den+dt*dt*ke)
            xn=x+dt*vn;e=max(xn,r/ke);f=max(ke*xn-r,0.)
            if jacobian:
                dr=ka@dz
                dvn=(m*dv-dt*K*dx)/den if free else (m*dv-dt*(K+ke)*dx+dt*dr)/(den+dt*dt*ke)
                dxn=dx+dt*dvn;de=dr/ke if free else dxn
                dzn=a.reshape(2,1)*dz+b.reshape(2,1)*de.reshape(1,2)
                J[n,t,0]=dxn;J[n,t,1]=dvn
                J[n,t,2]=np.zeros(2) if free else ke*dxn-dr
                dx,dv,dz=dxn,dvn,dzn
            z=a*z+b*e;x,v=xn,vn;y[n,t,0]=x;y[n,t,1]=v;y[n,t,2]=f
    return y,J


@njit(cache=True)
def closure_forward(q,initial,u,controls,c):
    k0,k1,k2,t1,t2,m,dt,switch,oldK,oldD=c;ke=k0+k1*t1/(t1+dt)+k2*t2/(t2+dt)
    B,T=u.shape;y=np.empty((B,T,3));flags=np.zeros((B,T),np.bool_)
    for n in range(B):
        x,v=initial[n]
        for t in range(T):
            K,D=(oldK,oldD) if (t+1)*dt<=switch+1e-12 else (controls[n,0],controls[n,1])
            den=m+dt*D+dt*dt*K
            vf=(m*v+dt*K*(u[n,t]-x))/den;cc=x+dt*vf>q[n,t];flags[n,t]=cc
            v=(m*v+dt*K*(u[n,t]-x)-dt*ke*(x-q[n,t]))/(den+dt*dt*ke) if cc else vf
            x=x+dt*v;y[n,t,0]=x;y[n,t,1]=v;y[n,t,2]=max(ke*(x-q[n,t]),0.)
    return y,flags


@njit(cache=True)
def closure_backward(g,flags,controls,c):
    k0,k1,k2,t1,t2,m,dt,switch,oldK,oldD=c;ke=k0+k1*t1/(t1+dt)+k2*t2/(t2+dt)
    B,T,_=g.shape;dq=np.empty((B,T))
    for n in range(B):
        lx=0.;lv=0.
        for t in range(T-1,-1,-1):
            K,D=(oldK,oldD) if (t+1)*dt<=switch+1e-12 else (controls[n,0],controls[n,1])
            den=m+dt*D+dt*dt*K
            cc=flags[n,t];denom=den+cc*dt*dt*ke
            av=m/denom;ax=-dt*(K+cc*ke)/denom;aq=cc*dt*ke/denom
            gx=g[n,t,0]+lx+g[n,t,2]*ke*cc;gv=g[n,t,1]+lv+dt*gx
            dq[n,t]=-g[n,t,2]*ke*cc+gv*aq;lx=gx+gv*ax;lv=gv*av
    return dq


def np64(t):return np.ascontiguousarray(t.detach().cpu().double().numpy())


class MaxwellRollout(torch.autograd.Function):
    @staticmethod
    def forward(ctx,z0,initial,u,controls,c):
        y,J=state_rollout(np64(z0),np64(initial),np64(u),np64(controls),np64(c),True)
        ctx.save_for_backward(torch.as_tensor(J,device=z0.device,dtype=z0.dtype))
        return torch.as_tensor(y,device=z0.device,dtype=z0.dtype)
    @staticmethod
    def backward(ctx,g):
        J,=ctx.saved_tensors
        return (g[...,None]*J).sum((1,2)),None,None,None,None


class ClosureRollout(torch.autograd.Function):
    @staticmethod
    def forward(ctx,q,initial,u,controls,c):
        ctrl=np64(controls);const=np64(c);y,flags=closure_forward(np64(q),np64(initial),np64(u),ctrl,const)
        ctx.args=(flags,ctrl,const);ctx.device=q.device;ctx.dtype=q.dtype
        return torch.as_tensor(y,device=q.device,dtype=q.dtype)
    @staticmethod
    def backward(ctx,g):
        dq=closure_backward(np64(g),*ctx.args)
        return torch.as_tensor(dq,device=ctx.device,dtype=ctx.dtype),None,None,None,None


def constants(material,cfg):
    return np.array([material['k_inf'],*material['k'],*material['tau'],cfg['plant']['mass'],cfg['dt'],
        cfg['controller_switch_time'],cfg['plant']['stiffness'],cfg['plant']['damping']],float)


def simulate(z0,initial,u,controls,material,cfg):
    return state_rollout(np.asarray(z0,float),np.asarray(initial,float),np.asarray(u,float),
                         np.asarray(controls,float),constants(material,cfg),False)[0]

