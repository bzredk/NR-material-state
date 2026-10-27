"""Check installed packages and run a small CPU or CUDA calculation."""
import argparse
import importlib
import importlib.metadata
import json
from pathlib import Path
import platform
import struct
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-cuda", action="store_true",
                        help="Fail if CUDA is unavailable or a CUDA calculation fails.")
    args = parser.parse_args()
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    expected = dict(line.split("==") for line in requirements.read_text().splitlines()
                    if line.strip() and not line.startswith("#"))
    expected["torch"] = "2.9.1"
    imports = {"pillow": "PIL"}
    errors, warnings, installed = [], [], {}
    if sys.version_info[:2] != (3, 11):
        warnings.append("Use Python 3.11 to match the recorded environment.")
    if struct.calcsize("P") != 8:
        errors.append("A 64-bit Python interpreter is required.")
    for name, version in expected.items():
        try:
            actual = importlib.metadata.version(name)
            importlib.import_module(imports.get(name, name))
            installed[name] = actual
            if actual.split("+")[0] != version:
                warnings.append(f"{name}: expected {version}, found {actual}.")
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")

    cuda = {"available": False}
    if "torch" in installed and not any(e.startswith("torch:") for e in errors):
        try:
            import torch
            cuda = {"available": torch.cuda.is_available(), "build": torch.version.cuda}
            device = "cuda" if cuda["available"] else "cpu"
            x = torch.arange(4, dtype=torch.float32, device=device)
            if float((x * x).sum().item()) != 14.0:
                raise RuntimeError("Tensor calculation returned an unexpected result.")
            if cuda["available"]:
                cuda["device"] = torch.cuda.get_device_name(0)
                cuda["memory_GiB"] = round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2)
        except Exception as exc:
            errors.append(f"Tensor calculation: {type(exc).__name__}: {exc}")
    if args.require_cuda and not cuda["available"]:
        errors.append("CUDA is required for full history/transfer runs and shared-feedback preparation.")
    if "numba" in installed and "numpy" in installed and not errors:
        try:
            import numba
            import numpy as np
            total = numba.njit(lambda x: x.sum())(np.arange(4, dtype=np.float64))
            if total != 6.0:
                raise RuntimeError("Numba calculation returned an unexpected result.")
        except Exception as exc:
            errors.append(f"Numba calculation: {type(exc).__name__}: {exc}")
    print(json.dumps({"status": "failed" if errors else "passed",
                      "python": platform.python_version(), "executable": sys.executable,
                      "packages": installed, "cuda": cuda,
                      "warnings": warnings, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
