"""
device_utils.py: find removable disks and keep the user from recovering
files onto the very card they are recovering from.

Read-only queries only. Nothing here writes to, formats or mounts a device.
"""

from __future__ import annotations

import json
import os
import platform
import plistlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Device:
    path: str                    # what PhotoRec is given, e.g. /dev/disk4
    label: str                   # human-readable line for the dropdown
    size: str = ""
    mountpoints: List[str] = field(default_factory=list)


def _run(cmd: List[str], timeout: int = 15) -> Optional[str]:
    """Run a read-only system query. Never uses shell=True."""
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


# ---------------------------------------------------------------- macOS

def _mac_devices() -> List[Device]:
    raw = _run(["diskutil", "list", "-plist", "external", "physical"])
    if not raw:
        return []
    try:
        data = plistlib.loads(raw.encode())
    except Exception:
        return []

    devices: List[Device] = []
    for disk in data.get("AllDisksAndPartitions", []):
        ident = disk.get("DeviceIdentifier")
        if not ident:
            continue
        size_bytes = disk.get("Size", 0)
        mounts = [
            p["MountPoint"]
            for p in disk.get("Partitions", [])
            if p.get("MountPoint")
        ]
        if disk.get("MountPoint"):
            mounts.append(disk["MountPoint"])
        names = [
            p.get("VolumeName")
            for p in disk.get("Partitions", [])
            if p.get("VolumeName")
        ]
        size = human_size(size_bytes)
        name = ", ".join(names) or "unnamed"
        devices.append(
            Device(
                path=f"/dev/{ident}",
                label=f"/dev/{ident}  ·  {size}  ·  {name}",
                size=size,
                mountpoints=mounts,
            )
        )
    return devices


# ---------------------------------------------------------------- Linux

def _linux_devices() -> List[Device]:
    raw = _run(["lsblk", "-J", "-b", "-o", "NAME,SIZE,MODEL,RM,TYPE,MOUNTPOINT,TRAN"])
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    devices: List[Device] = []
    for dev in data.get("blockdevices", []):
        if dev.get("type") != "disk":
            continue
        removable = str(dev.get("rm")) in ("1", "True", "true")
        if not removable and dev.get("tran") != "usb":
            continue  # skip internal drives so nobody picks their OS disk
        mounts = []
        for child in dev.get("children", []) or []:
            if child.get("mountpoint"):
                mounts.append(child["mountpoint"])
        if dev.get("mountpoint"):
            mounts.append(dev["mountpoint"])
        size = human_size(int(dev.get("size") or 0))
        model = (dev.get("model") or "card reader").strip()
        devices.append(
            Device(
                path=f"/dev/{dev['name']}",
                label=f"/dev/{dev['name']}  ·  {size}  ·  {model}",
                size=size,
                mountpoints=mounts,
            )
        )
    return devices


def list_removable_devices() -> List[Device]:
    """Best-effort list of external/removable disks. Empty list on Windows,
    where the user types the drive (e.g. E:) or picks a disk image."""
    system = platform.system()
    if system == "Darwin":
        return _mac_devices()
    if system == "Linux":
        return _linux_devices()
    return []


def unmount_mac_disk(device_path: str) -> tuple[bool, str]:
    """macOS needs the card unmounted before PhotoRec can read it raw.
    Unmounting is safe and reversible: the card stays untouched."""
    out = subprocess.run(
        ["diskutil", "unmountDisk", device_path],
        capture_output=True, text=True, check=False,
    )
    ok = out.returncode == 0
    return ok, (out.stdout or out.stderr).strip()


# ---------------------------------------------------------------- safety

def destination_is_on_device(dest: Path, device: Optional[Device]) -> bool:
    """True if `dest` sits on one of the selected device's mounted volumes.
    Writing recovered files there could overwrite the data being recovered."""
    if device is None:
        return False
    try:
        dest_resolved = dest.resolve()
    except OSError:
        return False
    for mp in device.mountpoints:
        try:
            mp_resolved = Path(mp).resolve()
        except OSError:
            continue
        if dest_resolved == mp_resolved or mp_resolved in dest_resolved.parents:
            return True
    return False


def human_size(n: int) -> str:
    step = 1000.0  # disks are sold in decimal units; match what's on the label
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < step:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= step
    return f"{n:.1f} PB"


def free_space(path: Path) -> int:
    try:
        st = os.statvfs(path)
        return st.f_bavail * st.f_frsize
    except (AttributeError, OSError):
        import shutil
        try:
            return shutil.disk_usage(path).free
        except OSError:
            return 0


_DISK_RE = re.compile(r"^/dev/(r?disk\d+|sd[a-z]+|mmcblk\d+|nvme\d+n\d+)$")


def looks_like_device(path: str) -> bool:
    return bool(_DISK_RE.match(path)) or bool(re.match(r"^[A-Za-z]:$", path))
