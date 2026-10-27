"""
gui.py: the Tkinter window. Simple on purpose: pick a card, pick a folder,
press Recover, watch the log.
"""

from __future__ import annotations

import platform
import queue
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import config
import device_utils as du
import photorec_wrapper as pr

C = config.COLOURS
IS_MAC = platform.system() == "Darwin"


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(config.APP_NAME)
        self.geometry("760x620")
        self.minsize(640, 520)

        self.photorec_path: Optional[str] = pr.find_photorec_binary()
        self.devices: list[du.Device] = []
        self.current_run: Optional[pr.RunHandle] = None
        self.msg_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self._permission_hint_shown = False

        self.source_mode = tk.StringVar(value="device")
        self.device_choice = tk.StringVar()
        self.image_path = tk.StringVar()
        self.dest_path = tk.StringVar(value=str(config.DEFAULT_DEST))
        self.unmount_first = tk.BooleanVar(value=IS_MAC)

        self._apply_style()
        self._build()
        self._refresh_binary_status()
        self._refresh_devices()
        self.after(100, self._poll_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------ style

    def _apply_style(self) -> None:
        """One clean ttk theme. 'clam' renders the same on Windows, Linux
        and the older Tk builds that ship with some macOS Pythons."""
        self.configure(bg=C["bg"])
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        base = ("Helvetica", 12)
        s.configure(".", background=C["bg"], foreground=C["ink"], font=base)
        s.configure("TFrame", background=C["bg"])
        s.configure("Card.TFrame", background=C["panel"], relief="flat")
        s.configure("Card.TLabel", background=C["panel"])
        s.configure("Card.TRadiobutton", background=C["panel"])
        s.configure("Card.TCheckbutton", background=C["panel"])
        s.configure("Title.TLabel", font=("Helvetica", 18, "bold"))
        s.configure("Sub.TLabel", foreground=C["muted"])
        s.configure("Section.TLabel", background=C["panel"], font=("Helvetica", 12, "bold"))
        s.configure("Hint.TLabel", background=C["panel"], foreground=C["muted"], font=("Helvetica", 11))
        s.configure("Accent.TButton", background=C["accent"], foreground="white",
                    font=("Helvetica", 12, "bold"), padding=(18, 8), borderwidth=0)
        s.map("Accent.TButton",
              background=[("active", C["accent_dark"]), ("disabled", "#9ca3af")])
        s.configure("TButton", padding=(10, 5))
        s.configure("Accent.Horizontal.TProgressbar", background=C["accent"])

    # ------------------------------------------------------------ layout

    def _build(self) -> None:
        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Recover deleted files", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Powered by PhotoRec. Read-only on your card; results go to a new folder every run.",
                  style="Sub.TLabel").pack(anchor="w", pady=(2, 10))

        self.status_lbl = ttk.Label(outer, text="")
        self.status_lbl.pack(anchor="w", pady=(0, 10))

        # --- source card
        src = ttk.Frame(outer, style="Card.TFrame", padding=14)
        src.pack(fill="x", pady=(0, 10))
        ttk.Label(src, text="1  ·  What to recover from", style="Section.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Radiobutton(src, text="SD card / USB drive", value="device",
                        variable=self.source_mode, style="Card.TRadiobutton",
                        command=self._sync_source_mode).grid(row=1, column=0, sticky="w")
        self.device_combo = ttk.Combobox(src, textvariable=self.device_choice, state="readonly", width=48)
        self.device_combo.grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(src, text="Refresh", command=self._refresh_devices).grid(row=1, column=2)

        ttk.Radiobutton(src, text="Disk image file", value="image",
                        variable=self.source_mode, style="Card.TRadiobutton",
                        command=self._sync_source_mode).grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.image_entry = ttk.Entry(src, textvariable=self.image_path)
        self.image_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=(8, 0))
        self.image_btn = ttk.Button(src, text="Choose…", command=self._choose_image)
        self.image_btn.grid(row=2, column=2, pady=(8, 0))

        if IS_MAC:
            ttk.Checkbutton(src, text="Unmount the card first (needed on macOS; doesn't change the card)",
                            variable=self.unmount_first, style="Card.TCheckbutton").grid(
                row=3, column=0, columnspan=3, sticky="w", pady=(10, 0))
        src.columnconfigure(1, weight=1)

        # --- destination card
        dst = ttk.Frame(outer, style="Card.TFrame", padding=14)
        dst.pack(fill="x", pady=(0, 10))
        ttk.Label(dst, text="2  ·  Where to save recovered files", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Entry(dst, textvariable=self.dest_path).grid(row=1, column=0, sticky="ew")
        ttk.Button(dst, text="Choose…", command=self._choose_dest).grid(row=1, column=1, padx=(8, 0))
        ttk.Label(dst, text="Never pick a folder on the card you're recovering from.",
                  style="Hint.TLabel").grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        dst.columnconfigure(0, weight=1)

        # --- actions
        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(4, 8))
        self.start_btn = ttk.Button(actions, text="Recover files", style="Accent.TButton", command=self._start)
        self.start_btn.pack(side="left")
        self.cancel_btn = ttk.Button(actions, text="Stop", command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=8)
        self.open_btn = ttk.Button(actions, text="Open results folder", command=self._open_results, state="disabled")
        self.open_btn.pack(side="right")

        self.progress = ttk.Progressbar(outer, mode="determinate", value=0, style="Accent.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(0, 8))

        # --- log
        log_frame = ttk.Frame(outer)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, height=10, bg=C["log_bg"], fg=C["log_fg"],
                           insertbackground=C["log_fg"], relief="flat", wrap="word",
                           font=("Menlo" if IS_MAC else "Courier", 11), padx=10, pady=8)
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set, state="disabled")
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self._sync_source_mode()

    # ------------------------------------------------------------ helpers

    def _write_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _refresh_binary_status(self) -> None:
        if self.photorec_path:
            self.status_lbl.configure(text=f"✓ PhotoRec found: {self.photorec_path}", foreground=C["ok"])
        else:
            self.status_lbl.configure(text=f"✗ PhotoRec not found. {pr.install_hint()}", foreground=C["error"])

    def _refresh_devices(self) -> None:
        self.devices = du.list_removable_devices()
        labels = [d.label for d in self.devices]
        self.device_combo["values"] = labels
        if labels:
            self.device_choice.set(labels[0])
        else:
            self.device_choice.set("")
            if platform.system() == "Windows":
                self.device_combo.configure(state="normal")  # type E: etc.
                self.device_choice.set("E:")
        self._write_log(f"Found {len(labels)} removable disk(s)." if labels
                        else "No removable disks found. Insert the card and press Refresh.")

    def _sync_source_mode(self) -> None:
        image = self.source_mode.get() == "image"
        self.image_entry.configure(state="normal" if image else "disabled")
        self.image_btn.configure(state="normal" if image else "disabled")
        if platform.system() != "Windows" or self.devices:
            self.device_combo.configure(state="disabled" if image else "readonly")

    def _selected_device(self) -> Optional[du.Device]:
        for d in self.devices:
            if d.label == self.device_choice.get():
                return d
        return None

    def _choose_image(self) -> None:
        p = filedialog.askopenfilename(title="Choose a disk image",
                                       filetypes=[("Disk images", "*.img *.dd *.dmg *.iso *.raw *.bin"),
                                                  ("All files", "*")])
        if p:
            self.image_path.set(p)

    def _choose_dest(self) -> None:
        p = filedialog.askdirectory(title="Save recovered files to…", initialdir=self.dest_path.get())
        if p:
            self.dest_path.set(p)

    # ------------------------------------------------------------ run

    def _start(self) -> None:
        if not self.photorec_path:
            messagebox.showerror(config.APP_NAME, f"PhotoRec isn't installed.\n\n{pr.install_hint()}")
            return

        dest = Path(self.dest_path.get()).expanduser()
        if not dest.is_dir():
            messagebox.showerror(config.APP_NAME, "That save folder doesn't exist.")
            return

        device = None
        if self.source_mode.get() == "image":
            source = self.image_path.get().strip()
            if not source or not Path(source).is_file():
                messagebox.showerror(config.APP_NAME, "Choose a disk image file first.")
                return
        else:
            device = self._selected_device()
            source = device.path if device else self.device_choice.get().strip()
            if not source or not du.looks_like_device(source):
                messagebox.showerror(config.APP_NAME, "Choose the card to recover from.")
                return

        if du.destination_is_on_device(dest, device):
            messagebox.showerror(config.APP_NAME,
                                 "The save folder is on the card you're recovering from.\n\n"
                                 "That could overwrite the very files you want back. Pick a folder on your computer.")
            return

        if du.free_space(dest) < 1_000_000_000:
            if not messagebox.askyesno(config.APP_NAME,
                                       "Less than 1 GB free in the save folder. Recovered files can be large.\n\nContinue anyway?"):
                return

        if not messagebox.askyesno(config.APP_NAME,
                                   f"Recover from:\n{source}\n\nSave to a new folder inside:\n{dest}\n\n"
                                   "PhotoRec only reads the card. Start?"):
            return

        if IS_MAC and device and self.unmount_first.get():
            ok, msg = du.unmount_mac_disk(device.path)
            self._write_log(msg or ("Unmounted." if ok else "Unmount failed."))
            if not ok:
                messagebox.showwarning(config.APP_NAME, "Couldn't unmount the card. Close anything using it and try again.")
                return

        self._permission_hint_shown = False
        try:
            self.current_run = pr.start_run(
                self.photorec_path, source, dest,
                on_line=lambda line: self.msg_queue.put(("line", line)),
                on_done=lambda h, code: self.msg_queue.put(("done", (h, code))),
            )
        except OSError as e:
            messagebox.showerror(config.APP_NAME, f"Couldn't start PhotoRec:\n{e}")
            return

        self._write_log(f"Saving to {self.current_run.run_dir}")
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.open_btn.configure(state="normal")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)

    def _cancel(self) -> None:
        if self.current_run:
            self.current_run.cancel()
            self._write_log("Stopping… files already recovered are kept.")

    def _finish(self, handle: pr.RunHandle, code: Optional[int]) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        n = pr.count_recovered(handle.run_dir)
        if handle.cancelled:
            self._write_log(f"Stopped. {n} file(s) recovered so far.")
        elif code == 0:
            self._write_log(f"Done. {n} file(s) recovered to {handle.run_dir}")
            messagebox.showinfo(config.APP_NAME, f"Finished.\n\n{n} file(s) recovered.")
        else:
            self._write_log(f"PhotoRec exited with code {code}. {n} file(s) recovered.")
            if not self._permission_hint_shown:
                self._show_permission_help()

    def _show_permission_help(self) -> None:
        self._permission_hint_shown = True
        if IS_MAC:
            text = ("macOS blocked PhotoRec from reading the card.\n\n"
                    "Fix (Catalina and later):\n"
                    "System Preferences → Security & Privacy → Privacy → Full Disk Access,\n"
                    "add Terminal (or whatever you launched this from), then quit and reopen it.\n\n"
                    "You may also need to launch with:  sudo python3 src/main.py")
        elif platform.system() == "Linux":
            text = "Reading a raw disk needs root. Launch with:\n\nsudo python3 src/main.py"
        else:
            text = "Reading a raw disk needs admin rights. Right-click your terminal → Run as administrator."
        messagebox.showwarning(config.APP_NAME, text)

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "line":
                    line = str(payload)
                    self._write_log(line)
                    if pr.looks_like_permission_problem(line) and not self._permission_hint_shown:
                        self._show_permission_help()
                elif kind == "done":
                    handle, code = payload  # type: ignore[misc]
                    self._finish(handle, code)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _open_results(self) -> None:
        target = self.current_run.run_dir if self.current_run else Path(self.dest_path.get())
        opener = {"Darwin": ["open"], "Windows": ["explorer"]}.get(platform.system(), ["xdg-open"])
        try:
            subprocess.Popen(opener + [str(target)])
        except OSError:
            messagebox.showinfo(config.APP_NAME, str(target))

    def _on_close(self) -> None:
        if self.current_run and self.current_run.process.poll() is None:
            if not messagebox.askyesno(config.APP_NAME, "Recovery is still running. Stop it and quit?"):
                return
            self.current_run.cancel()
        self.destroy()
