"""Entire-episode splits; test ID/OOD share only their held-out pasts.
Simulator internal states are written as oracle_* and never used for training.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from physics import Material, simulate


def command_protocol(cfg, seed, wait):
    r = np.random.default_rng(seed)
    dt, H, T = cfg['dt'], cfg['history_steps'], cfg['future_steps']
    target = r.uniform(.003, .007)
    levels = r.uniform(.002, .009, size=4)
    times = np.array([0, .3, .7, 1.1, 1.5, 1.9, 2.5, 3.0])
    values = np.array([-.004, -.004, *levels, target, target])
    history = np.interp(np.arange(H+1)*dt, times, values)
    next_depth = r.uniform(.003, .008)
    retract = .3
    onset = retract + wait
    ramp = r.uniform(.25, .5)
    ft = np.arange(1, T+1)*dt
    future = np.interp(ft, [0, retract, onset, onset+ramp, T*dt],
                       [target, -.004, -.004, next_depth, next_depth])
    mask = (ft >= onset) & (ft <= onset+1.2)
    return np.concatenate([history, future]), mask, onset


def make_split(cfg, seeds, waits):
    protocols = [command_protocol(cfg, int(s), float(w)) for s, w in zip(seeds, waits)]
    commands = np.stack([p[0] for p in protocols])
    mat = Material.from_dict(cfg['truth'])
    clean, states, contact, compression = simulate(commands, mat, cfg['plant'], cfg['dt'])
    noisy = clean.copy()
    sig = np.array(list(cfg['sensor_std'][k] for k in ['position', 'velocity', 'force']))
    for i, seed in enumerate(seeds):
        noisy[i] += np.random.default_rng(int(seed)+700000).normal(size=noisy[i].shape)*sig
    H = cfg['history_steps']
    hist = np.concatenate([noisy[:, :H+1], commands[:, :H+1, None],
                           np.full((len(seeds), H+1, 1), cfg['dt'])], axis=-1)
    return dict(history=hist.astype('float32'), commands=commands[:, H+1:].astype('float32'),
                labels=noisy[:, H+1:].astype('float32'), truth=clean[:, H+1:],
                oracle_z=states[:, H], oracle_initial=clean[:, H, :2],
                truth_contact=contact[:, H+1:], truth_compression=compression[:, H+1:],
                metric_mask=np.stack([p[1] for p in protocols]),
                onset=np.array([p[2] for p in protocols]), waits=np.array(waits),
                episode_ids=np.asarray(seeds), full_commands=commands,
                full_observed=noisy)


def generate(cfg, directory):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    r = np.random.default_rng(cfg['data_seed'])
    groups = {}
    def id_waits(n):
        intervals = np.asarray(cfg['train_wait_ranges'])
        selected = intervals[r.integers(0, len(intervals), n)]
        return r.uniform(selected[:, 0], selected[:, 1])
    for name, n, offset in [('train', cfg['train_episodes'], 0),
                             ('val', cfg['val_episodes'], 10000),
                             ('test_id', cfg['test_pairs'], 20000)]:
        seeds = np.arange(n)+cfg['data_seed']+offset
        groups[name] = make_split(cfg, seeds, id_waits(n))
    groups['test_wait'] = make_split(cfg, groups['test_id']['episode_ids'],
                                    r.uniform(*cfg['test_wait_range'], cfg['test_pairs']))
    assert np.array_equal(groups['test_id']['history'], groups['test_wait']['history'])
    assert not set(groups['train']['episode_ids']) & set(groups['test_id']['episode_ids'])
    manifest = {'config': cfg, 'splits': {}, 'training_columns': ['x', 'v', 'F', 'u', 'dt'],
                'test_id_wait_pairing': 'same unseen history and continuation, only wait differs',
                'privileged_fields': ['truth', 'oracle_z', 'oracle_initial', 'truth_contact', 'truth_compression']}
    for name, ds in groups.items():
        path = directory / f'{name}.npz'
        np.savez_compressed(path, **ds)
        manifest['splits'][name] = {'episodes': len(ds['history']),
            'wait_min': float(ds['waits'].min()), 'wait_max': float(ds['waits'].max()),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    (directory/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return groups


def load(directory):
    return {name: dict(np.load(Path(directory)/f'{name}.npz'))
            for name in ['train', 'val', 'test_id', 'test_wait']}
