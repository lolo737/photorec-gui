# 🕯️ PhotoRec Recovery GUI
### *A lantern for lost photographs, lovingly tuned for macOS Catalina*

> *Somewhere on that little SD card, beneath a freshly-formatted surface that swears blind it is empty, your photographs are still sleeping. They were never truly gone. The file table simply forgot their names.*
>
> *This app goes down into the dark and fetches them back.*

---

You pressed **Delete**. Or worse, you pressed **Format**, and a small cold wave rolled through your stomach. The wedding, the holiday, the half-finished animation tests, the one good photo of the dog: vanished, apparently.

Not quite. When a card is quick-formatted or a file is deleted, the data usually stays exactly where it was. Only the index pointing to it is wiped. **[PhotoRec](https://www.cgsecurity.org/wiki/PhotoRec)**, the magnificent free tool by Christophe Grenier at CGSecurity, ignores the index entirely and reads the raw card byte by byte, recognising photos, videos and documents by their very shape.

PhotoRec has one flaw: it greets you with a text-only terminal menu of arrow keys, partition tables and cryptic options, where one wrong choice can send recovered files straight back onto the card you're trying to save.

**This app is the friendly front door.** Pick the card. Pick a folder. Press one green button. Watch the files come home.

<p align="center"><b>Pick the card → Pick a folder → Recover files</b></p>

---

## 🍎 Built for Catalina. Truly.

Plenty of tools quietly assume you're on the latest macOS. This one was born on a **MacBook running macOS Catalina 10.15**, and it treats Catalina as a first-class citizen rather than an afterthought.

| Catalina quirk | What usually happens | What this app does |
|---|---|---|
| Privacy controls block raw disk reads | PhotoRec fails silently or with "no harddisk found" | Spots the error in PhotoRec's output and **pops up the exact fix** |
| Cards stay mounted by Finder | PhotoRec can't get exclusive access | **Unmount first** is ticked by default; one click, card untouched |
| The Python that ships with Catalina's tools uses an old, glitchy Tk 8.5 | Windows freeze, text vanishes | Uses the steady `clam` theme and tells you which Python to install |
| Newer apps demand newer Python | "Requires macOS 11 or later" | Needs only **Python 3.8+** and the standard library: nothing else to install |
| Homebrew no longer officially supports 10.15 | `brew install` grinds or fails | README gives you the **direct-download route** too (below) |

No Electron, no 300 MB runtime, no third-party Python packages. It runs on the Mac you already have.

---

## ✨ What it does

- **Lists only external drives** (SD cards, USB sticks), so your Mac's own disk never appears in the dropdown
- **Recovers from a disk image** too (`.img`, `.dd`, `.raw`), the safest route for a card that's starting to fail
- **Saves to your Downloads folder** by default; change it with one click
- **A fresh folder for every run** (`run_20261027_125422/`), so a second attempt can never overwrite the first
- **A live log** of exactly what PhotoRec is doing, cleaned of terminal gibberish
- **Stop at any time**: everything already recovered is kept
- **Open results folder** button, straight to your returned treasure

## 🛡️ Why it's safe

- **Read-only on your card.** PhotoRec only ever reads the source. Not one byte is written to it.
- **Refuses to save onto the card itself.** Writing recovered files back onto the card could overwrite the very data you're rescuing, so the app simply won't allow it.
- **Warns when space is short**, before you start rather than halfway through.
- **No network. No telemetry. No tracking.** The only file the app keeps is a small local run history in `~/.photorec_gui/`.
- **No shell tricks.** PhotoRec is launched with a plain argument list, never `shell=True`, so an odd device name can't be run as a command.
- **No sneaky admin rights.** If reading the card needs your password, the app tells you how, and never escalates on its own.

---

## 🚀 Setting it up on Catalina (10.15)

### 1. Get Python 3.8 or newer, with a modern Tk

Install Python from **[python.org/downloads/macos](https://www.python.org/downloads/macos/)**. Pick an installer marked as supporting macOS 10.13 or later. The python.org installers bundle **Tk 8.6**, which fixes Catalina's frozen-window and invisible-text bugs.

Check it worked:
```bash
python3 --version
python3 -c "import tkinter; print(tkinter.TkVersion)"   # should print 8.6
```

### 2. Get PhotoRec (two routes)

**Route A: Homebrew** (if you already have it working on Catalina)
```bash
brew install testdisk
```

**Route B: direct download** (the reliable route on 10.15)
1. Go to **[cgsecurity.org/wiki/TestDisk_Download](https://www.cgsecurity.org/wiki/TestDisk_Download)** and download the **macOS (Intel)** build.
2. Unpack it, then copy `photorec` somewhere the app will find it:
```bash
sudo mkdir -p /usr/local/bin
sudo cp ~/Downloads/testdisk-*/photorec /usr/local/bin/
sudo chmod +x /usr/local/bin/photorec
```
If macOS says the developer can't be verified, right-click `photorec` in Finder → **Open** once, or run `xattr -d com.apple.quarantine /usr/local/bin/photorec`.

### 3. Get the app
```bash
git clone https://github.com/lolo737/photorec-gui.git
cd photorec-gui
```

### 4. Give Terminal permission to read disks (the bit everyone misses)

Catalina guards raw disk access behind its privacy controls. Grant Terminal access **once**:

1. Open **System Preferences → Security & Privacy → Privacy**
2. Choose **Full Disk Access** in the left-hand list
3. Click the 🔒 padlock and enter your password
4. Click **+** and add **Terminal** (it lives in Applications → Utilities). Use iTerm or your editor instead if that's where you launch from.
5. **Quit Terminal completely** (⌘Q) and reopen it. The permission only takes effect in a fresh session.

If Catalina later asks whether Terminal may access files on a **removable volume**, click **OK**.

### 5. Launch
```bash
sudo python3 src/main.py
```
`sudo` is needed because macOS only lets administrators read a disk raw. The app itself never asks for or stores your password.

---

## 🎞️ Using it

1. **Insert the card**, then press **Refresh**. It appears with its size and name, e.g. `/dev/disk4 · 31.9 GB · NO NAME`.
2. Leave **Unmount the card first** ticked. Unmounting only tells Finder to let go; it doesn't change anything on the card.
3. Check the save folder (**Downloads** unless you change it).
4. Press **Recover files**, confirm, and watch the log.
5. When it finishes, press **Open results folder**. Your files are in `recup_dir.1`, `recup_dir.2` and so on.

> **A word on names:** PhotoRec rescues the *contents*, not the original filenames, so expect names like `f0012345.jpg`. Sort by type or date in Finder and they'll fall into place.

## 🩺 When things go wrong on Catalina

| Symptom | Likely cause | Fix |
|---|---|---|
| "Permission denied" / "No harddisk found" | Terminal lacks Full Disk Access, or not run with `sudo` | Step 4 above, then `sudo python3 src/main.py` |
| "Couldn't unmount the card" | Finder, Photos or Image Capture is using it | Quit those apps, or eject in Finder, then try again |
| Card doesn't appear in the list | Not detected yet, or it's an internal reader showing as internal | Reseat the card, press **Refresh**, or image the card and use **Disk image file** |
| Window is blank or text is invisible | Old Tk 8.5 | Install Python from python.org (step 1) |
| "PhotoRec not found" | Not installed, or not on PATH | Step 2, Route B |
| Recovered nothing | Card was overwritten, or fully (not quick) formatted | Sadly some data can't come back; stop using the card to protect what's left |

**Golden rule:** the moment you realise files are missing, **stop using the card**. Every new photo taken risks overwriting one you want back.

---

## 🧰 Also runs on Linux and Windows

- **Linux:** `sudo apt install testdisk python3-tk`, then `sudo python3 src/main.py`
- **Windows:** download TestDisk from cgsecurity.org, add its folder to PATH, then run `python src\main.py` from a terminal opened with *Run as administrator*. Type the drive letter (e.g. `E:`) in the source box.

## 🗂️ Project layout

```
photorec-gui/
├── src/
│   ├── main.py              # entry point: checks Python and Tk before opening
│   ├── gui.py               # the Tkinter window
│   ├── photorec_wrapper.py  # finds PhotoRec, builds the command, streams output
│   ├── device_utils.py      # lists external disks, unmounts, safety checks
│   └── config.py            # defaults and colours
├── tests/
│   └── test_wrapper.py      # end-to-end test on a synthetic card
├── requirements.txt         # (empty: standard library only)
├── LICENSE
└── README.md
```

## 🧪 Tests

```bash
python3 -m unittest discover -s tests -v
```

The test suite forges a small fake SD card with hidden JPEGs buried inside, sets real PhotoRec loose on it, and checks every one comes back. It also checks the safety rails: run folders never collide, saving onto the card is blocked, and device names are passed literally, never to a shell. The recovery test skips itself politely if PhotoRec isn't installed.

## 🙏 Credits

All the actual recovery magic belongs to **PhotoRec** and **TestDisk** by **Christophe Grenier, [CGSecurity](https://www.cgsecurity.org)**, released under the GPL. This project is an independent, affectionate front end and isn't affiliated with CGSecurity. If PhotoRec saves your memories, consider supporting the project via [cgsecurity.org](https://www.cgsecurity.org).

## 📜 Licence

MIT. See [LICENSE](LICENSE). Made in Skerries by Niall O'Hara, on a Catalina Mac that refused to be left behind.
