import json
from pathlib import Path
import numpy as np
from physics import Material, step, simulate
from data import make_split

CFG = json.loads((Path(__file__).parent/'config.json').read_text())
MAT = Material.from_dict(CFG['truth'])


def test_free_surface_recovers_without_reset():
    z = np.array([[.003, .001]])
    x, v, zn, force, e, contact = step(np.array([-.004]), np.array([0.]), z,
                                      np.array([-.004]), MAT, CFG['plant'], .02)
    assert force[0] == 0 and not contact[0]
    assert e[0] > 0 and np.linalg.norm(zn) > 0
    assert not np.allclose(zn, z)
    assert np.allclose(MAT.k_inf*e+(MAT.k*(e[:,None]-zn)).sum(-1), 0, atol=1e-12)


def test_complementarity_and_actuator_balance():
    r = np.random.default_rng(9)
    x = r.uniform(-.004,.006,100); v = r.uniform(-.01,.01,100)
    z = r.uniform(0,.004,(100,2)); u = r.uniform(-.005,.008,100)
    xn,vn,zn,f,e,c = step(x,v,z,u,MAT,CFG['plant'],.02)
    gap = e-xn
    assert np.min(gap) >= -1e-12 and np.min(f) >= 0
    assert np.max(np.abs(f*gap)) < 1e-12
    p=CFG['plant']
    assert np.allclose(p['mass']*(vn-v)/.02, p['stiffness']*(u-xn)-p['damping']*vn-f)


def test_fixed_boundary_energy_decreases():
    z = np.array([[.004,.0005]])
    def energy(z):
        e=(MAT.k*z).sum(-1)/(MAT.k_inf+MAT.k.sum())
        return .5*MAT.k_inf*e**2+.5*(MAT.k*(e[:,None]-z)**2).sum(-1)
    energies=[]
    for _ in range(300):
        energies.append(energy(z)[0])
        _,_,z,_,_,_=step(np.array([-.004]),np.array([0.]),z,np.array([-.004]),MAT,CFG['plant'],.02)
    assert np.max(np.diff(energies)) < 1e-12
    assert energies[-1] < energies[0]*.05


def test_wait_pair_has_identical_past_and_distinct_future():
    a=make_split(CFG,[44],[.3]); b=make_split(CFG,[44],[1.])
    assert np.array_equal(a['history'],b['history'])
    assert not np.array_equal(a['commands'],b['commands'])
    assert np.array_equal(a['oracle_z'],b['oracle_z'])


def test_torch_physics_matches_numpy_and_has_no_future_label_argument():
    import torch
    from models import MaterialState, GRUForce
    ds=make_split(CFG,[11,12],[.3,1.])
    model=MaterialState(CFG).double()
    hist=torch.tensor(ds['history'],dtype=torch.float64)
    commands=torch.tensor(ds['commands'],dtype=torch.float64)
    model.eval()
    with torch.no_grad():
        pred,z=model(hist,commands,return_state=True)
    k0,k,tau=model.parameters_physical()
    mat=Material(float(k0.detach()),k.detach().numpy(),tau.detach().numpy())
    actual=simulate(ds['commands'],mat,CFG['plant'],CFG['dt'],
                    (ds['history'][:,-1,0].astype(float),ds['history'][:,-1,1].astype(float),z.numpy()))[0]
    np.testing.assert_allclose(pred.numpy(),actual,atol=1e-9)
    import inspect
    assert set(inspect.signature(GRUForce.forward).parameters)=={'self','history','commands'}
