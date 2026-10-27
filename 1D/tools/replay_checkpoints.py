"""Load all primary checkpoints and replay bounded inputs without retraining."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

BUNDLE=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--part',type=lambda value: {'e1':'history-dependence','e2':'controller-transfer'}.get(value,value), choices=['history-dependence','controller-transfer'])
    parser.add_argument('--device',choices=['auto','cpu','cuda'],default='auto')
    parser.add_argument('--strict-archive',action='store_true',
                        help='Require the original history-dependence tolerance even on CPU.')
    args=parser.parse_args()
    if args.part is None:
        for name in ['history-dependence','controller-transfer']:
            command=[sys.executable,__file__,'--part',name,'--device',args.device]
            if args.strict_archive:
                command.append('--strict-archive')
            subprocess.run(command,check=True)
        return
    import numpy as np
    import torch
    torch.set_num_threads(1)
    device=('cuda' if torch.cuda.is_available() else 'cpu') if args.device=='auto' else args.device
    if device=='cuda' and not torch.cuda.is_available():
        parser.error('CUDA is unavailable. Use --device cpu for the installation check.')
    strict_archive=args.strict_archive or device=='cuda'
    if args.part=='history-dependence':
        root=BUNDLE/'experiments/history_dependence'
        out=root/'runs/round2_v1'
    else:
        root=BUNDLE/'experiments/controller_transfer/v2'
        out=root/'runs/transfer_v2'
    sys.path.insert(0,str(root))
    from models import make_model, MODEL_NAMES
    cfg=json.loads((out/'config.json').read_text())
    material_file=out/'fixed_material.json' if args.part=='history-dependence' else root/'fixed_material.json'
    material=json.loads(material_file.read_text())['parameters']
    records=[]
    if args.part=='history-dependence':
        with np.load(out/'data/test_wait.npz') as d:
            h=d['history'][:1].reshape(2,301,5)
            commands=d['commands'][:1].reshape(2,420)
        archived=np.load(out/'predictions.npz')
    else:
        with np.load(out/'data/val.npz') as d:
            h=d['history'][0]
            commands=d['commands'][0,0]
            controls=d['controls'][0,0]
    for name in MODEL_NAMES:
        for seed in cfg['seeds']:
            model=make_model(name,cfg,material).to(device)
            checkpoint=torch.load(out/f'checkpoints/{name}_{seed}_best.pt',map_location=device,weights_only=False)
            model.load_state_dict(checkpoint['model'],strict=True)
            model.eval()
            with torch.no_grad():
                inputs=[torch.as_tensor(h,device=device),torch.as_tensor(commands,device=device)]
                if args.part=='controller-transfer':
                    inputs.append(torch.as_tensor(controls,device=device))
                pred=model(*inputs).cpu().numpy()
            assert pred.shape==(2,420 if args.part=='history-dependence' else 500,3)
            assert np.isfinite(pred).all()
            row={'model':name,'seed':seed,'finite_prediction':True}
            if args.part=='history-dependence':
                expected=archived[f'{name}__{seed}__test_wait'][0]
                maximum=float(np.max(np.abs(pred-expected)))
                # CPU recurrent kernels can drift from the saved CUDA rollout.
                # Report that difference; do not redefine the archived tolerance.
                row['archived_tolerance_met']=bool(np.allclose(pred,expected,rtol=1e-4,atol=1e-5))
                row['maximum_difference_by_channel']=dict(zip(
                    ['position_m','velocity_m_s','force_N'],
                    np.max(np.abs(pred-expected),axis=(0,1)).astype(float).tolist()))
                if strict_archive:
                    np.testing.assert_allclose(pred,expected,rtol=1e-4,atol=1e-5)
                row['maximum_difference_from_archived_prediction']=maximum
            records.append(row)
    if args.part=='history-dependence':
        archived.close()
    comparison=('strict' if strict_archive else 'cpu_diagnostic_only') if args.part=='history-dependence' else 'finite_outputs_only'
    print(json.dumps({'experiment':args.part,'device':device,'checkpoints_replayed':len(records),
                      'archive_comparison':comparison,'results':records},indent=2))

if __name__=='__main__':
    main()
