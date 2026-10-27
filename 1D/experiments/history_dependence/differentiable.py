"""Exact branchwise derivatives for FIXED physics; no observed future/contact used.
Small mechanics loops run in NumPy; encoder/decoder GRUs train on the GPU.
"""
import numpy as np
import torch


class MaxwellRollout(torch.autograd.Function):
    @staticmethod
    def forward(ctx,z0,initial,commands,constants):
        c=constants.detach().cpu().double().numpy()
        k0,k1,k2,t1,t2,m,K,D,dt=c;k=np.array([k1,k2]);tau=np.array([t1,t2])
        a=tau/(tau+dt);b=1-a;ka=k*a;ke=k0+ka.sum();den=m+dt*D+dt*dt*K
        z=z0.detach().cpu().double().numpy().copy()
        init=initial.detach().cpu().double().numpy();x=init[:,0].copy();v=init[:,1].copy()
        u=commands.detach().cpu().double().numpy();B,T=u.shape
        dx=np.zeros((B,2));dv=np.zeros((B,2));dz=np.broadcast_to(np.eye(2),(B,2,2)).copy()
        y=np.empty((B,T,3));J=np.empty((B,T,3,2))
        for t in range(T):
            r=(ka*z).sum(-1);dr=(ka[None,:,None]*dz).sum(1)
            vf=(m*v+dt*K*(u[:,t]-x))/den;xf=x+dt*vf
            free=xf<=r/ke
            vc=(m*v+dt*K*(u[:,t]-x)-dt*(ke*x-r))/(den+dt*dt*ke)
            vn=np.where(free,vf,vc);xn=x+dt*vn
            dvf=(m*dv-dt*K*dx)/den
            dvc=(m*dv-dt*(K+ke)*dx+dt*dr)/(den+dt*dt*ke)
            dvn=np.where(free[:,None],dvf,dvc);dxn=dx+dt*dvn
            e=np.maximum(xn,r/ke);de=np.where(free[:,None],dr/ke,dxn)
            zn=a*z+b*e[:,None];dzn=a[None,:,None]*dz+b[None,:,None]*de[:,None,:]
            f=np.maximum(ke*xn-r,0.);df=np.where(free[:,None],0.,ke*dxn-dr)
            y[:,t]=np.stack([xn,vn,f],-1);J[:,t]=np.stack([dxn,dvn,df],1)
            x,v,z,dx,dv,dz=xn,vn,zn,dxn,dvn,dzn
        ctx.save_for_backward(torch.as_tensor(J,device=z0.device,dtype=z0.dtype))
        return torch.as_tensor(y,device=z0.device,dtype=z0.dtype)

    @staticmethod
    def backward(ctx,grad):
        (J,)=ctx.saved_tensors
        return (grad[...,None]*J).sum((1,2)),None,None,None


class ClosureRollout(torch.autograd.Function):
    @staticmethod
    def forward(ctx,closure,initial,commands,constants,contact):
        c=constants.detach().cpu().double().numpy()
        k0,k1,k2,t1,t2,m,K,D,dt=c;ke=k0+k1*t1/(t1+dt)+k2*t2/(t2+dt)
        den=m+dt*D+dt*dt*K
        q=closure.detach().cpu().double().numpy();u=commands.detach().cpu().double().numpy()
        init=initial.detach().cpu().double().numpy();x=init[:,0].copy();v=init[:,1].copy()
        B,T=q.shape;y=np.empty((B,T,3));contact_flags=np.zeros((B,T),bool)
        for t in range(T):
            if contact:
                vf=(m*v+dt*K*(u[:,t]-x))/den;xf=x+dt*vf
                cc=xf>q[:,t];contact_flags[:,t]=cc
                vc=(m*v+dt*K*(u[:,t]-x)-dt*ke*(x-q[:,t]))/(den+dt*dt*ke)
                vn=np.where(cc,vc,vf);xn=x+dt*vn;f=np.maximum(ke*(xn-q[:,t]),0.)
            else:
                f=q[:,t];vn=(m*v+dt*K*(u[:,t]-x)-dt*f)/den;xn=x+dt*vn
            y[:,t]=np.stack([xn,vn,f],-1);x,v=xn,vn
        ctx.constants=(ke,m,K,D,dt,den);ctx.contact=contact;ctx.flags=contact_flags
        ctx.device=closure.device;ctx.dtype=closure.dtype
        return torch.as_tensor(y,device=closure.device,dtype=closure.dtype)

    @staticmethod
    def backward(ctx,grad):
        g=grad.detach().cpu().double().numpy();B,T,_=g.shape
        ke,m,K,D,dt,den=ctx.constants
        lx=np.zeros(B);lv=np.zeros(B);dq=np.zeros((B,T))
        for t in range(T-1,-1,-1):
            if ctx.contact:
                cc=ctx.flags[:,t];denom=den+cc*dt*dt*ke
                av=m/denom;ax=-dt*(K+cc*ke)/denom;aq=cc*dt*ke/denom
                gx=g[:,t,0]+lx+g[:,t,2]*ke*cc
                gv=g[:,t,1]+lv+dt*gx
                dq[:,t]=-g[:,t,2]*ke*cc+gv*aq
            else:
                av=m/den;ax=-dt*K/den
                gx=g[:,t,0]+lx;gv=g[:,t,1]+lv+dt*gx
                dq[:,t]=g[:,t,2]-gv*dt/den
            lx=gx+gv*ax;lv=gv*av
        return torch.as_tensor(dq,device=ctx.device,dtype=ctx.dtype),None,None,None,None
