"""Local Jupyter backend for VS Code when its native kernel transport crashes.

This launches no browser. Authentication is retained; only loopback is bound.
Runtime credentials and logs stay in the ignored project-local .runtime folder.
"""
from pathlib import Path
import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT/".runtime"
STATE = RUNTIME/"notebook_server.json"


def request(state, path="/api/status", method="GET"):
    req = Request(state["base_url"]+path, headers={"Authorization": "token "+state["token"]}, method=method)
    return urlopen(req, timeout=3)


def status():
    if not STATE.exists():
        return None
    state = json.loads(STATE.read_text())
    try:
        with request(state):
            return state
    except OSError:
        return None


def start():
    existing = status()
    if existing:
        print("Local notebook backend is already running at "+existing["base_url"])
        return
    RUNTIME.mkdir(exist_ok=True)
    # Keep the local connection stable across backend restarts. Credentials never
    # enter the notebook, workspace settings, run manifests, or source control.
    previous = json.loads(STATE.read_text()) if STATE.exists() else {}
    token = previous.get("token") if previous.get("root") == str(ROOT) else None
    token = token or secrets.token_hex(32)
    port = 8897
    env = os.environ.copy()
    env["JUPYTER_TOKEN"] = token
    env["JUPYTER_RUNTIME_DIR"] = str(RUNTIME/"jupyter")
    args = [sys.executable, "-m", "jupyter_server", "--no-browser", "--ServerApp.ip=127.0.0.1",
            f"--ServerApp.port={port}", "--ServerApp.port_retries=0", f"--ServerApp.root_dir={ROOT}",
            "--MappingKernelManager.default_kernel_name=nr-spatial-state", "--ServerApp.log_level=WARN"]
    with (RUNTIME/"notebook_server.log").open("a", encoding="utf-8") as log:
        process = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    state = {"pid": process.pid, "base_url": f"http://127.0.0.1:{port}", "token": token,
             "connection_url": f"http://127.0.0.1:{port}/?token={token}", "root": str(ROOT), "python": sys.executable}
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    for _ in range(30):
        if process.poll() is not None:
            raise RuntimeError("Local backend exited; inspect .runtime/notebook_server.log")
        if status():
            print("Local notebook backend ready at "+state["base_url"])
            print("Private connection URL is in .runtime/notebook_server.json (not committed).")
            return
        time.sleep(.3)
    raise RuntimeError("Local backend startup timed out; inspect .runtime/notebook_server.log")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["start", "status", "url", "stop"])
    args = parser.parse_args()
    if args.command == "start":
        start()
        return
    state = status()
    if not state:
        print("Local notebook backend is not running.")
        return
    if args.command == "stop":
        with request(state, "/api/shutdown", "POST"):
            pass
        for _ in range(30):
            if status() is None:
                print("Local notebook backend stopped.")
                return
            time.sleep(.2)
        raise RuntimeError("Local backend shutdown timed out; inspect its runtime log.")
    elif args.command == "url":
        print(state["connection_url"])
    else:
        print("Running at "+state["base_url"]+"; loopback only; token authentication enabled.")


if __name__ == "__main__":
    main()
