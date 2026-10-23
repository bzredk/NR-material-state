import json
from pathlib import Path
import numpy as np
import torch
from physics import Material,simulate,ground_history
from data import split
from models import make_model
from differentiable import MaxwellRollout,ClosureRollout

CFG=json.loads((Path(__file__).parent/'config.json').read_text())
C=torch.tensor([400.,900.,1300.,.15,1.4,.35,2200.,45.,.01],dtype=torch.float64)


def test_maxwell_forward_and_exact_gradient():
    z=torch.tensor([[.002,.001]],dtype=torch.float64,requires_grad=True)
    init=torch.tensor([[.003,.001]],dtype=torch.float64)
    u=torch.linspace(.004,-.003,40,dtype=torch.float64)[None]
    y=MaxwellRollout.apply(z,init,u,C)
    ref=simulate(u.numpy(),Material.from_dict(CFG['truth']),CFG['plant'],.01,
                 (init[:,0].numpy(),init[:,1].numpy(),z.detach().numpy()))[0]
    np.testing.assert_allclose(y.detach().numpy(),ref,atol=1e-10)
    assert torch.autograd.gradcheck(lambda zz:MaxwellRollout.apply(zz,init,u,C),(z,),eps=1e-7,atol=1e-4)


def test_contact_closure_exact_gradient_and_unilateral_force():
    q=torch.full((1,20),.002,dtype=torch.float64,requires_grad=True)
    init=torch.tensor([[.003,0.]],dtype=torch.float64)
    u=torch.linspace(.004,-.004,20,dtype=torch.float64)[None]
    y=ClosureRollout.apply(q,init,u,C,True)
    assert y[...,2].min()>=0 and y[0,-1,2]==0
    assert torch.autograd.gradcheck(lambda qq:ClosureRollout.apply(qq,init,u,C,True),(q,),eps=1e-7,atol=1e-4)


def test_force_closure_exact_gradient():
    q=torch.full((1,15),2.,dtype=torch.float64,requires_grad=True)
    init=torch.tensor([[.003,0.]],dtype=torch.float64);u=torch.full((1,15),.004,dtype=torch.float64)
    assert torch.autograd.gradcheck(lambda qq:ClosureRollout.apply(qq,init,u,C,False),(q,),eps=1e-6,atol=1e-5)


def test_paired_data_has_identical_current_and_command_but_different_response():
    d=split(CFG,[15,16],[.9,1.1])
    assert np.array_equal(d['history'][:,0,-1],d['history'][:,1,-1])
    assert np.array_equal(d['commands'][:,0],d['commands'][:,1])
    assert np.max(np.abs(d['truth'][:,0,:,2]-d['truth'][:,1,:,2]))>.03
    h=torch.tensor(d['history'].reshape(-1,301,5));u=torch.tensor(d['commands'].reshape(-1,420))
    model=make_model('snapshot_state',CFG,CFG['truth'])
    with torch.no_grad():y=model(h,u).numpy().reshape(2,2,420,3)
    assert np.array_equal(y[:,0],y[:,1])


def test_history_integral_reconstructs_states_from_clean_replayed_motion():
    from data import history_pair
    u,y,z,_,_,_=history_pair(CFG,25)
    np.testing.assert_allclose(ground_history(y,Material.from_dict(CFG['truth']),.01),z[:,-1],atol=1e-12)


def test_recent_contact_observer_recovers_noise_free_state_without_relaxed_start():
    from data import history_pair
    from physics import local_contact_observer
    _,y,z,_,_,_=history_pair(CFG,41)
    np.testing.assert_allclose(local_contact_observer(y,Material.from_dict(CFG['truth']),.01),z[:,-1],atol=1e-12)
