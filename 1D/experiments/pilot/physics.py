"""1D unilateral Maxwell pad + known, gravity-compensated impedance actuator.

SI units. x is positive downward from the undeformed pad surface. z_i are
dashpot extensions. A detached pad has NONZERO free-surface compression.
Backward Euler solves the material and actuator implicitly at each step.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class Material:
    k_inf: float
    k: np.ndarray
    tau: np.ndarray

    @classmethod
    def from_dict(cls, d):
        return cls(float(d['k_inf']), np.asarray(d['k'], dtype=float),
                   np.asarray(d['tau'], dtype=float))

    def as_dict(self):
        return dict(k_inf=float(self.k_inf), k=self.k.tolist(), tau=self.tau.tolist())


def material_step(x_next, z, mat, dt):
    a = mat.tau / (mat.tau + dt)
    b = 1 - a
    effective_k = mat.k_inf + np.sum(mat.k * a)
    residual = np.sum(mat.k * a * z, axis=-1)
    free_surface = residual / effective_k
    compression = np.maximum(x_next, free_surface)
    z_next = a * z + b * compression[..., None]
    force = np.maximum(effective_k * x_next - residual, 0.0)
    return z_next, force, compression


def step(x, v, z, command, mat, plant, dt, mode='carry'):
    m, K, D = plant['mass'], plant['stiffness'], plant['damping']
    a = mat.tau / (mat.tau + dt)
    b = 1 - a
    effective_k = mat.k_inf + np.sum(mat.k * a)
    residual = np.sum(mat.k * a * z, axis=-1)
    denominator = m + dt * D + dt * dt * K
    vf = (m * v + dt * K * (command - x)) / denominator
    xf = x + dt * vf
    free = xf <= residual / effective_k
    vc = (m * v + dt * K * (command - x) - dt * (effective_k*x-residual)) / (denominator+dt*dt*effective_k)
    xn = np.where(free, xf, x+dt*vc)
    vn = np.where(free, vf, vc)
    zn, fn, compression = material_step(xn, z, mat, dt)
    if mode == 'reset':
        zn = np.where(free[..., None], 0.0, zn)
    elif mode == 'freeze':
        zn = np.where(free[..., None], z, zn)
    elif mode != 'carry':
        raise ValueError(mode)
    return xn, vn, zn, fn, compression, ~free


def simulate(commands, mat, plant, dt, initial=None, mode='carry'):
    commands = np.asarray(commands)
    batch, length = commands.shape
    if initial is None:
        x, v, z = commands[:, 0].copy(), np.zeros(batch), np.zeros((batch, len(mat.k)))
    else:
        x, v, z = [np.array(a, copy=True) for a in initial]
    ys, zs, contacts, compressions = [], [], [], []
    for t in range(length):
        x, v, z, f, e, c = step(x, v, z, commands[:, t], mat, plant, dt, mode)
        ys.append(np.stack([x, v, f], axis=-1))
        zs.append(z.copy()); contacts.append(c); compressions.append(e)
    return (np.stack(ys, 1), np.stack(zs, 1), np.stack(contacts, 1),
            np.stack(compressions, 1))


def ground_history(history, mat, dt):
    """Ground z using ONLY observed past positions and the known relaxed start."""
    z = np.zeros((len(history), len(mat.k)))
    for t in range(1, history.shape[1]):
        z, _, _ = material_step(history[:, t, 0], z, mat, dt)
    return z


def observe_force_from_positions(xs, mat, dt):
    z = np.zeros((len(xs), len(mat.k)))
    forces = np.zeros_like(xs)
    for t in range(1, xs.shape[1]):
        z, forces[:, t], _ = material_step(xs[:, t], z, mat, dt)
    return forces
