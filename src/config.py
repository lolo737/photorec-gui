"""
config.py: shared constants for PhotoRec Recovery GUI.

No network hosts, telemetry endpoints or analytics keys live here,
or anywhere else in this project, by design.
"""

from pathlib import Path

APP_NAME = "PhotoRec Recovery GUI"
APP_VERSION = "1.0.0"

# Local-only folder for the app's own state. Never synced or uploaded.
APP_HOME = Path.home() / ".photorec_gui"

# Our own record of past runs (device, time, output folder). Local only.
RUN_HISTORY_FILE = APP_HOME / "run_history.json"

# Default place recovered files go. Users can change it in the GUI.
DEFAULT_DEST = Path.home() / "Downloads"
if not DEFAULT_DEST.is_dir():
    DEFAULT_DEST = Path.home()

# Binary names to look for on PATH, per platform.
PHOTOREC_BINARY_CANDIDATES = {
    "Windows": ["photorec_win.exe", "photorec.exe"],
    "Darwin": ["photorec"],
    "Linux": ["photorec"],
}

# Extra install locations to check besides PATH (Homebrew, MacPorts, distro).
EXTRA_SEARCH_DIRS = [
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/opt/local/bin",
    "/usr/sbin",
    "/usr/bin",
    "/sbin",
]

# Colours for the GUI. Kept small on purpose.
COLOURS = {
    "bg": "#f5f5f2",
    "panel": "#ffffff",
    "ink": "#1f2328",
    "muted": "#6b7280",
    "accent": "#1f6f5c",
    "accent_dark": "#17574a",
    "warn": "#b45309",
    "error": "#b91c1c",
    "ok": "#15803d",
    "log_bg": "#111827",
    "log_fg": "#e5e7eb",
}
