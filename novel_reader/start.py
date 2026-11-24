#!/usr/bin/env python3
"""One-click launcher for Inkwell Novel Reader (backend + frontend).

Double-click start.bat on Windows, or run `python start.py` from anywhere.
Both servers start in their own console; closing this launcher (or pressing
Ctrl+C here) stops both. Child output is also mirrored to logs/*.log.
Secrets stay in the untracked .env file.
"""
from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

if os.name == "nt":  # Windows: react to closing the launcher window
    import ctypes
    from ctypes import wintypes

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
LOGS = ROOT / "logs"
VENV_PY = BACKEND / ".venv" / "Scripts" / ("python.exe" if os.name == "nt" else "python")
FRONT_URL = "http://localhost:5173"
BACK_URL = "http://localhost:8000"
PORTS = ((8000, "backend"), (5173, "frontend"))
MAX_RESTARTS = 5

CLOSE_EVENT = threading.Event()
_CONSOLE_HANDLER = None  # keep the ctypes callback alive for the process lifetime


def port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def hold_window() -> None:
    """Keep the double-clicked window open long enough to read an error."""
    if os.name == "nt" and sys.stdin is not None and sys.stdin.isatty():
        try:
            input("Press Enter to close...")
        except EOFError:
            pass


def stop(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), 15)
        except (ProcessLookupError, PermissionError):
            proc.terminate()


def spawn(cmd: list[str], cwd: Path, log: Path) -> subprocess.Popen:
    """Start one child in its own console with output mirrored to a log file."""
    LOGS.mkdir(exist_ok=True)
    handle = log.open("a", encoding="utf-8", buffering=1)
    kwargs = {"cwd": str(cwd), "env": os.environ.copy(),
              "stdout": handle, "stderr": subprocess.STDOUT}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    try:
        return subprocess.Popen(cmd, **kwargs)
    finally:
        handle.close()  # the child owns a duplicated handle


def make_worker(label: str, cmd: list[str], cwd: Path) -> dict:
    log = LOGS / f"{label}.log"
    return {"label": label, "cmd": cmd, "cwd": cwd, "log": log,
            "proc": spawn(cmd, cwd, log), "restarts": 0}


def install_close_handler() -> None:
    """Flag window close / logoff only — never call subprocess from this thread."""
    global _CONSOLE_HANDLER
    if os.name != "nt":
        return

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
    def on_console_event(event: int) -> bool:
        # 0=Ctrl+C, 1=Ctrl+Break, 2=window close, 5=logoff/shutdown.
        # Windows' default handler terminates the process immediately on these
        # (0xC000013A) and skips `finally`, orphaning the children. Swallow them
        # here and let the main loop exit cleanly with cleanup.
        if event in (0, 1, 2, 5):
            CLOSE_EVENT.set()
            return True
        return False

    _CONSOLE_HANDLER = on_console_event
    ctypes.windll.kernel32.SetConsoleCtrlHandler(_CONSOLE_HANDLER, True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser")
    args = parser.parse_args()

    problems: list[str] = []
    if not VENV_PY.is_file():
        problems.append(f"Missing backend venv: {VENV_PY}")
    if not (FRONTEND / "node_modules").is_dir():
        problems.append(f"Frontend deps missing - run: npm ci  (in {FRONTEND})")
    for port, label in PORTS:
        if port_busy(port):
            problems.append(f"Port {port} already in use ({label}). Close the existing server first.")
    if problems:
        print("Cannot start Inkwell Novel Reader:\n  - " + "\n  - ".join(problems))
        hold_window()
        return 1

    workers: list[dict] = []
    try:
        # No --reload: on Windows uvicorn's reloader sends CTRL_C_EVENT to the
        # whole console and restarts the app, which can close the child's tab.
        workers.append(make_worker(
            "backend",
            [str(VENV_PY), "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", "8000"],
            BACKEND,
        ))
        npm = "npm.cmd" if os.name == "nt" else "npm"
        workers.append(make_worker(
            "frontend", [shutil.which(npm) or npm, "run", "dev"], FRONTEND
        ))
        install_close_handler()

        print(f"Inkwell Novel Reader starting...\n  frontend: {FRONT_URL}\n  backend:  {BACK_URL}")
        print(f"Logs: {LOGS / 'backend.log'} , {LOGS / 'frontend.log'}")
        print("Close this window (or press Ctrl+C) to stop both servers.")
        if not args.no_browser:
            time.sleep(1)
            webbrowser.open(FRONT_URL)

        # Supervise: a crashed child is restarted; only a real close request or
        # exhausting the restart budget ends the launcher. No silent timeouts.
        while not CLOSE_EVENT.is_set():
            for worker in workers:
                proc = worker["proc"]
                if proc.poll() is None or CLOSE_EVENT.is_set():
                    continue
                label, log = worker["label"], worker["log"]
                if worker["restarts"] >= MAX_RESTARTS:
                    print(f"[ERROR] {label} keeps exiting (code {proc.returncode}) after "
                          f"{MAX_RESTARTS} restarts - see {log}")
                    return 1
                worker["restarts"] += 1
                print(f"[WARN] {label} exited with code {proc.returncode} - "
                      f"restarting ({worker['restarts']}/{MAX_RESTARTS}), log: {log}")
                CLOSE_EVENT.wait(2)
                if CLOSE_EVENT.is_set():
                    break
                worker["proc"] = spawn(worker["cmd"], worker["cwd"], log)
            CLOSE_EVENT.wait(0.5)
        return 0
    except KeyboardInterrupt:
        print("\nStopping both servers...")
        return 0
    finally:
        for worker in workers:
            stop(worker["proc"])


if __name__ == "__main__":
    sys.exit(main())
