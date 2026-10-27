# PhotoRec Recovery GUI

A simple, friendly window for [PhotoRec](https://www.cgsecurity.org/wiki/PhotoRec), the free file-recovery tool by CGSecurity.

PhotoRec is brilliant at getting deleted photos, videos and documents back from SD cards and USB drives, even after a quick format. But it runs in a text-only terminal menu that's easy to get wrong. This app puts a clean point-and-click front end on it:

1. Pick the card
2. Pick where to save
3. Press **Recover files**

All the actual recovery is done by PhotoRec. This app just drives it safely.

## Why it's safe to use

- **Read-only on your card.** PhotoRec only reads the source. Nothing is written to it.
- **Refuses to save onto the card itself.** Saving recovered files to the card you're recovering from can overwrite the data you want back, so the app blocks it.
- **A new folder every run.** Each attempt goes into its own `run_YYYYMMDD_HHMMSS` folder, so a second run can never overwrite the first.
- **No network, no telemetry.** The app makes no internet connections. Its only file of its own is a local run history in `~/.photorec_gui/`.
- **No shell tricks.** PhotoRec is launched with a plain argument list (no `shell=True`), so an odd device name can't be run as a command.
- **No silent admin rights.** If reading the card needs admin/root, the app tells you how. It never escalates by itself.

## Requirements

- Python 3.8 or newer, with Tkinter (included in the python.org installers)
- PhotoRec, which comes in the TestDisk package:

| OS | Install |
|---|---|
| macOS | `brew install testdisk` |
| Ubuntu / Debian | `sudo apt install testdisk` |
| Fedora | `sudo dnf install testdisk` |
| Windows | Download from [cgsecurity.org](https://www.cgsecurity.org/wiki/TestDisk_Download) and add the folder to your PATH |

No third-party Python packages are needed.

## Run it

```bash
git clone https://github.com/lolo737/photorec-gui.git
cd photorec-gui
python3 src/main.py
```

Reading a raw card usually needs admin rights:

- **macOS / Linux:** `sudo python3 src/main.py`
- **Windows:** open your terminal with *Run as administrator*

## Using it

1. Insert the card and press **Refresh**. It appears in the dropdown with its size and name. Only external/removable drives are listed, so you can't accidentally pick your main disk.
2. Or choose **Disk image file** to recover from an `.img` / `.dd` backup of a card. (Imaging a failing card first, then recovering from the image, is the safest approach.)
3. The save folder defaults to your **Downloads**. Change it with **Choose…** if you like.
4. Press **Recover files** and watch the log. Press **Stop** at any time; anything already recovered is kept.
5. When it's done, **Open results folder** takes you straight there. Files sit in `recup_dir.1`, `recup_dir.2`… PhotoRec doesn't keep original file names, so expect names like `f0012345.jpg`.

## macOS notes (Catalina 10.15 and later)

**"PhotoRec doesn't work" / permission errors.** That's almost always macOS privacy protection, not PhotoRec:

1. **System Preferences → Security & Privacy → Privacy → Full Disk Access**
2. Unlock, then add **Terminal** (or iTerm, or your IDE if you launch from there)
3. Quit and reopen Terminal, then try again

The app spots permission errors in PhotoRec's output and shows these steps automatically.

**Unmount first.** macOS keeps cards mounted, which stops raw reads. The app's *Unmount the card first* option (on by default on Mac) does this for you. Unmounting doesn't change anything on the card.

**Window looks broken or blank.** Older macOS ships an old Tk (8.5) with rendering bugs. Install Python from [python.org](https://www.python.org/downloads/) (bundles Tk 8.6) or run `brew install python-tk`.

## Project layout

```
photorec-gui/
├── src/
│   ├── main.py              # entry point and Python/Tk checks
│   ├── gui.py               # the Tkinter window
│   ├── photorec_wrapper.py  # finds PhotoRec, builds the command, streams output
│   ├── device_utils.py      # lists removable disks, safety checks
│   └── config.py            # constants and colours
├── tests/
│   └── test_wrapper.py      # end-to-end test on a synthetic card image
├── requirements.txt
├── LICENSE
└── README.md
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The test builds a small fake card image with hidden JPEGs, runs real PhotoRec over it and checks they come back. It's skipped automatically if PhotoRec isn't installed.

## Credits

PhotoRec and TestDisk are by Christophe Grenier, [CGSecurity](https://www.cgsecurity.org), released under the GPL. This project is an independent front end and isn't affiliated with CGSecurity.

## Licence

MIT. See [LICENSE](LICENSE).
