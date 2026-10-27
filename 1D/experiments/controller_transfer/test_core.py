import json
from pathlib import Path
import numpy as np
import torch
from dynamics import constants,state_rollout,closure_forward,closure_backward,simulate
from physics_base import Material,simulate as base_simulate
from dataset import histories,command
from models import make_model

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'config.json').read_text())


def fixture():
    d=histories(dict(CFG,train_pairs=1),'train');initial=d['initial'].reshape(-1,2);z=d['z'].reshape(-1,2)
    u=np.stack([command(CFG,.006,.2,.3,.0075)]*2);ctrl=np.array([[1200.,25.],[3600.,80.]])
    return d,initial,z,u,ctrl


def test_batched_control_matches_original():
    _,initial,z,u,ctrl=fixture();y=simulate(z,initial,u,ctrl,CFG['truth'],CFG)
    for n in range(2):
        p=dict(mass=.35,stiffness=ctrl[n,0],damping=ctrl[n,1])
        ref=base_simulate(u[n:n+1],Material.from_dict(CFG['truth']),p,CFG['dt'],
                         (initial[n:n+1,0],initial[n:n+1,1],z[n:n+1]))[0]
        np.testing.assert_allclose(y[n:n+1],ref,rtol=1e-10,atol=1e-11)


def test_state_derivative_multiple_controls():
    _,initial,z,u,ctrl=fixture();c=constants(CFG['truth'],CFG);y,J=state_rollout(z,initial,u,ctrl,c,True)
    eps=1e-8
    for j in range(2):
        zp=z.copy();zm=z.copy();zp[:,j]+=eps;zm[:,j]-=eps
        diff=(state_rollout(zp,initial,u,ctrl,c)[0]-state_rollout(zm,initial,u,ctrl,c)[0])/(2*eps)
        np.testing.assert_allclose(J[...,j],diff,rtol=1e-5,atol=1e-5)


def test_closure_adjoint():
    _,initial,z,u,ctrl=fixture();u=u[:,:70];c=constants(CFG['truth'],CFG)
    q=np.full(u.shape,.002);y,flags=closure_forward(q,initial,u,ctrl,c)
    rng=np.random.default_rng(9);g=rng.normal(size=y.shape);direction=rng.normal(size=q.shape)
    adj=(closure_backward(g,flags,ctrl,c)*direction).sum();eps=1e-8
    num=((closure_forward(q+eps*direction,initial,u,ctrl,c)[0]-closure_forward(q-eps*direction,initial,u,ctrl,c)[0])*g).sum()/(2*eps)
    np.testing.assert_allclose(adj,num,rtol=1e-5)


def test_state_encoder_has_no_future_controller_input():
    d,*_=fixture();h=torch.tensor(d['history'].reshape(2,-1,5));m=make_model('history_state',CFG,CFG['truth'])
    np.testing.assert_array_equal(d['history'][0,0,-1],d['history'][0,1,-1])
    assert m.state(h).shape==(2,2)
    assert 'controls' not in __import__('inspect').signature(m.state).parameters


def test_selector_rejection_and_failures_are_not_fast_success():
    from actions import select,outcomes
    time=np.array([[1.,2.,3.],[1.,2.,3.]])
    peak=np.array([[5.,3.,2.],[5.,4.,3.]])
    choice=select(time,peak,2.5,.03);np.testing.assert_array_equal(choice,[2,-1])
    result=outcomes(choice,time,peak,2.5,5.)
    np.testing.assert_array_equal(result['success'],[True,False])
    np.testing.assert_array_equal(result['cost'],[3.,6.])


def test_completion_requires_contiguous_post_approach_hold():
    from actions import response_metrics
    y=np.zeros((2,60,3));y[:,:,2]=1.;y[:,:10,0]=.006
    y[0,20:39,0]=.006;y[0,40:60,0]=.006;y[1,20:39,0]=.006
    time,peak=response_metrics(y,np.array([.2,.2]),.01,.004,.2)
    assert time[0]==.60 and np.isinf(time[1])


def test_peak_includes_force_after_goal_completion():
    from actions import response_metrics
    y=np.zeros((1,100,3));y[:,:,0]=.006;y[:,:,2]=1.;y[:,90,2]=8.
    time,peak=response_metrics(y,np.array([.2]),.01,.004,.2)
    assert time[0]<.5 and peak[0]==8.
