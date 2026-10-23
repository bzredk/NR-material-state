"""Two observation-grounded predictors, with the SAME known actuator.
No teacher forcing or access to future observations in either forward method.
"""
import torch
from torch import nn
import torch.nn.functional as F


class Base(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        h = cfg['hidden_size']
        self.encoder = nn.GRU(5, h, batch_first=True)
        self.register_buffer('scale', torch.tensor([.006, .02, 8., .006, cfg['dt']]))

    def encode(self, history):
        return self.encoder(history/self.scale)[1][-1]


class MaterialState(Base):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.state_head = nn.Linear(cfg['hidden_size'], 2)
        nn.init.constant_(self.state_head.bias, -1.)
        p = cfg['initial_guess']
        self.log_parameters = nn.Parameter(torch.tensor([p['k_inf'], *p['k'], *p['tau']]).log())

    def parameters_physical(self):
        p = self.log_parameters.exp()
        return p[0], p[1:3], p[3:5]

    def forward(self, history, commands, mode='carry', return_state=False):
        h = self.encode(history)
        z = torch.sigmoid(self.state_head(h))*.010
        initial_z = z
        x, v = history[:, -1, 0], history[:, -1, 1]
        dt = self.cfg['dt']; plant = self.cfg['plant']
        m, K, D = plant['mass'], plant['stiffness'], plant['damping']
        k0, k, tau = self.parameters_physical()
        a = tau/(tau+dt); b = 1-a
        ke = k0+(k*a).sum()
        den = m+dt*D+dt*dt*K
        outputs = []
        if mode == 'no_history':
            z = z*0
        for u in commands.unbind(1):
            r = (k*a*z).sum(-1)
            vf = (m*v+dt*K*(u-x))/den
            xf = x+dt*vf
            free = xf <= r/ke
            vc = (m*v+dt*K*(u-x)-dt*(ke*x-r))/(den+dt*dt*ke)
            xn = torch.where(free, xf, x+dt*vc)
            vn = torch.where(free, vf, vc)
            e = torch.maximum(xn, r/ke)
            zn = a*z+b*e[:, None]
            force = torch.relu(ke*xn-r)
            if mode == 'reset':
                zn = torch.where(free[:, None], zn*0, zn)
            elif mode == 'freeze':
                zn = torch.where(free[:, None], z, zn)
            x, v, z = xn, vn, zn
            outputs.append(torch.stack([x, v, force], -1))
        result = torch.stack(outputs, 1)
        return (result, initial_z) if return_state else result


class GRUForce(Base):
    """History GRU predicts a force closure; known actuator predicts motion.
    Stronger physics-matched comparator than a completely unstructured decoder.
    """
    def __init__(self, cfg):
        super().__init__(cfg)
        h = cfg['hidden_size']
        self.decoder = nn.GRUCell(5, h)
        self.force_head = nn.Sequential(nn.Linear(h, 24), nn.Tanh(), nn.Linear(24, 1))
        nn.init.constant_(self.force_head[-1].bias, -2.)

    def forward(self, history, commands):
        hidden = self.encode(history)
        x, v, force = history[:, -1, 0], history[:, -1, 1], history[:, -1, 2]
        dt = self.cfg['dt']; plant = self.cfg['plant']
        m, K, D = plant['mass'], plant['stiffness'], plant['damping']
        den = m+dt*D+dt*dt*K
        outputs = []
        for u in commands.unbind(1):
            features = torch.stack([x, v, force, u, torch.full_like(x, dt)], -1)/self.scale
            hidden = self.decoder(features, hidden)
            force = 8.*F.softplus(self.force_head(hidden).squeeze(-1))
            v = (m*v+dt*K*(u-x)-dt*force)/den
            x = x+dt*v
            outputs.append(torch.stack([x, v, force], -1))
        return torch.stack(outputs, 1)


def prediction_loss(prediction, labels):
    # Future labels are used ONLY here, never as rollout inputs.
    force = ((prediction[..., 2]-labels[..., 2])/8.).square().mean()
    position = ((prediction[..., 0]-labels[..., 0])/.006).square().mean()
    return force+position


class MaterialSnapshot(MaterialState):
    """Same parameter count and physical decoder, only the latest observation."""
    def encode(self, history):
        return self.encoder(history[:, -1:]/self.scale)[1][-1]


MODELS = {'material_state': MaterialState, 'gru_force': GRUForce,
          'material_snapshot': MaterialSnapshot}
