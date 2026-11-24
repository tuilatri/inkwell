#!/usr/bin/env python3
"""One-click launcher for Inkwell Novel Reader (backend + frontend).

Double-click this file on Windows, or run `python start.py` from anywhere.
Both servers start in their own console window; closing this launcher (or
pressing Ctrl+C here) stops both. Secrets stay in the untracked .env file.
"""
from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

if os.name == "nt":  # Windows: react to closing the launcher window
    import ctypes
    from ctypes import wintypes

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV_PY = BACKEND / ".venv" / "Scripts" / ("python.exe" if os.name == "nt" else "python")
FRONT_URL = "http://localhost:5173"
BACK_URL = "http://localhost:8000"
PORTS = ((8000, "backend"), (5173, "frontend"))


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


def spawn(cmd: list[str], cwd: Path) -> subprocess.Popen:
    kwargs = {"cwd": str(cwd), "env": os.environ.copy()}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(cmd, **kwargs)


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

    processes: list[subprocess.Popen] = []
    try:
        backend = spawn([str(VENV_PY), "-m", "uvicorn", "app.main:app", "--reload",
                         "--host", "127.0.0.1", "--port", "8000"], BACKEND)
        processes.append(backend)
        npm = "npm.cmd" if os.name == "nt" else "npm"
        frontend = spawn([shutil.which(npm) or npm, "run", "dev"], FRONTEND)
        processes.append(frontend)
        if os.name == "nt":
            @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
            def on_console_event(event: int) -> bool:
                # 0=Ctrl+C, 1=Ctrl+Break, 2=close window, 5=logoff/shutdown
                if event in (0, 1, 2, 5):
                    for proc in processes:
                        stop(proc)
                return False  # let Windows complete the close

            ctypes.windll.kernel32.SetConsoleCtrlHandler(on_console_event, True)

        print(f"Inkwell Novel Reader starting...\n  frontend: {FRONT_URL}\n  backend:  {BACK_URL}")
        print("Close this window (or press Ctrl+C) to stop both servers.")
        if not args.no_browser:
            time.sleep(1)
            webbrowser.open(FRONT_URL)

        # Stay alive until the user closes this window / presses Ctrl+C, or a
        # server actually dies. No time limit - this is a user-facing launcher,
        # not a smoke test.
        while all(proc.poll() is None for proc in processes):
            time.sleep(0.5)
        for proc, label in zip(processes, ("backend", "frontend")):
            if proc.poll() is not None:
                print(f"[ERROR] {label} exited early with code {proc.returncode} - check its console window.")
        hold_window()
        return 1
    except KeyboardInterrupt:
        print("\nStopping both servers...")
        return 0
    finally:
        for proc in processes:
            stop(proc)


if __name__ == "__main__":
    sys.exit(main())
