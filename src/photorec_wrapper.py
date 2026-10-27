"""
photorec_wrapper.py: find the PhotoRec binary, build a safe command line,
run it in the background and stream its output.

The recovery itself is done entirely by PhotoRec (CGSecurity, GPL).
This module never reimplements recovery and never writes to the source.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

import config


# ---------------------------------------------------------------- binary

def find_photorec_binary() -> Optional[str]:
    """Return the full path to PhotoRec, or None if it isn't installed."""
    names = config.PHOTOREC_BINARY_CANDIDATES.get(platform.system(), ["photorec"])
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    for folder in config.EXTRA_SEARCH_DIRS:
        for name in names:
            candidate = Path(folder) / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    return None


def install_hint() -> str:
    system = platform.system()
    if system == "Darwin":
        return "Install with Homebrew:  brew install testdisk"
    if system == "Linux":
        return "Install with your package manager, e.g.  sudo apt install testdisk"
    return "Download TestDisk & PhotoRec from https://www.cgsecurity.org and add it to PATH"


# ---------------------------------------------------------------- runs

def new_run_folder(dest_root: Path) -> Path:
    """Every run gets its own timestamped folder, so a second attempt can
    never overwrite files recovered by the first."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = dest_root / f"run_{stamp}"
    n = 1
    while run_dir.exists():  # two runs in the same second
        run_dir = dest_root / f"run_{stamp}_{n}"
        n += 1
    run_dir.mkdir(parents=True)
    return run_dir


def build_command(binary: str, source: str, run_dir: Path) -> List[str]:
    """PhotoRec non-interactive mode:
    whole disk (partition_none), every file type, then search.
    Output lands in run_dir/recup_dir.1, .2, ... (PhotoRec's own layout)."""
    return [
        binary,
        "/log",
        "/d", str(run_dir / "recup_dir"),
        "/cmd", source,
        "partition_none,fileopt,everything,enable,search",
    ]


def record_run(source: str, run_dir: Path, exit_code: Optional[int]) -> None:
    """Append to our local run history. Stored outside the destination so it
    is never mixed in with recovered files."""
    try:
        config.APP_HOME.mkdir(parents=True, exist_ok=True)
        history = []
        if config.RUN_HISTORY_FILE.exists():
            history = json.loads(config.RUN_HISTORY_FILE.read_text() or "[]")
        history.append(
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "source": source,
                "output": str(run_dir),
                "exit_code": exit_code,
            }
        )
        config.RUN_HISTORY_FILE.write_text(json.dumps(history[-200:], indent=2))
    except (OSError, ValueError):
        pass  # history is a nicety; never block a recovery over it


def count_recovered(run_dir: Path) -> int:
    total = 0
    for sub in run_dir.glob("recup_dir*"):
        if sub.is_dir():
            total += sum(1 for p in sub.iterdir() if p.is_file() and p.name != "report.xml")
    return total


# ANSI/curses escape sequences (cursor moves, colours) and leftover control chars.
_ESCAPES = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[()][0-9A-Za-z]|\x1b[=>]")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


PERMISSION_MARKERS = (
    "permission denied",
    "operation not permitted",
    "no harddisk found",
    "unable to open",
)


def looks_like_permission_problem(line: str) -> bool:
    low = line.lower()
    return any(m in low for m in PERMISSION_MARKERS)


@dataclass
class RunHandle:
    process: subprocess.Popen
    run_dir: Path
    source: str
    cancelled: bool = False

    def cancel(self) -> None:
        self.cancelled = True
        if self.process.poll() is None:
            self.process.terminate()


def start_run(
    binary: str,
    source: str,
    dest_root: Path,
    on_line: Callable[[str], None],
    on_done: Callable[[RunHandle, Optional[int]], None],
) -> RunHandle:
    """Launch PhotoRec in the background. No shell, arguments passed as a
    list, so a strange device name can't be interpreted as a command."""
    run_dir = new_run_folder(dest_root)
    cmd = build_command(binary, source, run_dir)
    on_line(f"$ {' '.join(cmd)}")

    proc = subprocess.Popen(
        cmd,
        cwd=run_dir,  # photorec.log lands with the results
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        errors="replace",
        bufsize=1,
    )
    handle = RunHandle(process=proc, run_dir=run_dir, source=source)

    last = [""]

    def pump() -> None:
        assert proc.stdout is not None
        for raw in proc.stdout:
            # PhotoRec draws a terminal UI; split its screen updates into
            # readable lines and drop the escape codes.
            for line in _ESCAPES.split(raw):
                line = _CONTROL.sub("", line).strip()
                if line and line != last[0]:
                    last[0] = line
                    on_line(line)
        proc.stdout.close()
        code = proc.wait()
        record_run(source, run_dir, code)
        on_done(handle, code)

    threading.Thread(target=pump, daemon=True).start()
    return handle
