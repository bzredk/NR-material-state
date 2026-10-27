"""Command-line entry points calling exactly the notebook's implementation."""
import argparse
from pathlib import Path

from .experiments import ROOT, RUNS, read_json, run_pilot, run_batch, sweep_for, write_json
from .physics import Config
from .estimators import ObserverConfig


def main():
    parser = argparse.ArgumentParser(description="Spatial 2D hidden-state experiments")
    parser.add_argument("command", choices=["demo", "batch", "export", "sweep", "checks"])
    parser.add_argument("--run", type=Path, help="Existing run; defaults to runs/2d_contact/latest.json")
    parser.add_argument("--config", type=Path, help="Physics JSON for demo/checks; default: configs/spatial_contact.json")
    parser.add_argument("--observer-config", type=Path, help="Observer JSON for demo/batch/sweep; writes separate comparisons")
    parser.add_argument("--recompute", action="store_true", help="Retain old results and compute a new version")
    parser.add_argument("--no-animation", action="store_true")
    parser.add_argument("--noise", type=float, default=0.)
    parser.add_argument("--excitation", choices=["hold", "pulse"], default="hold")
    parser.add_argument("--actions", nargs="+", default=["Slow press", "Fast press"])
    parser.add_argument("--noises", nargs="+", type=float, default=[0., 1.])
    args = parser.parse_args()
    if args.config and args.command not in ("demo", "checks"):
        parser.error("--config applies to demo/checks. Other commands use the selected run's recorded configuration.")
    if args.observer_config and args.command not in ("demo", "batch", "sweep"):
        parser.error("--observer-config applies to demo/batch/sweep.")
    observer_config = ObserverConfig(**read_json(args.observer_config)) if args.observer_config else None
    config = Config(**read_json(args.config or ROOT/"configs/spatial_contact.json")) if args.command in ("demo", "checks") else None
    if args.command == "demo":
        run, timing = run_pilot(config, force=args.recompute, observer_config=observer_config)
        print(run); print(timing)
        return
    if args.command == "checks":
        from .checks import run_checks
        result, _ = run_checks(config)
        write_json(RUNS/"standalone_checks.json", result)
        print(f"Passed {sum(r['passed'] for r in result['rows'])}/{len(result['rows'])} in {result['wall_seconds']:.2f} s")
        raise SystemExit(0 if result["passed"] else 1)
    run = args.run or ROOT/read_json(RUNS/"latest.json")["run"].replace("\\", "/")
    if args.command == "batch":
        result = run_batch(run, tuple(args.actions), tuple(args.noises), observer_config=observer_config)
        print(f"Batch: {result['independent_units']} independent parents; {result['wall_seconds']:.2f} s")
        print(result["path"])
    elif args.command == "sweep":
        _, mode = sweep_for(run, args.excitation, args.noise, args.recompute, print,
                            observer_config=observer_config)
        print(mode)
    elif args.command == "export":
        import matplotlib
        matplotlib.use("Agg")
        from .plotting import export_all
        print(export_all(run, not args.no_animation))


if __name__ == "__main__":
    main()
