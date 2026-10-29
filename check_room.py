#!/usr/bin/env python3
"""
NASA Space Apps Cairo - Tech Ops | Room Inspector GUI
====================================================
Desktop GUI for Strike Team members to rapidly verify all 12 rooms.
Can be run directly via `python check_room.py` or compiled to `RoomChecker.exe`.

Features:
- Dark space NASA theme
- 12 Room Selector with live status from Firebase
- 1-Click Calibration Pattern (1080p RGB Bars, aspect ratio borders, focus grid)
- Background Cloudflare Speedtest + Ping to 8.8.8.8 + Wi-Fi Signal
- Automatic / Manual upload to Firebase Realtime Database
"""

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import requests
except ImportError:
    sys.exit("Missing requests library. Run: pip install requests")

# Resolve directory whether running as script or frozen .exe
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent

CONFIG_PATH = APP_DIR / "config.json"
ROOM_COUNT = 12
PING_HOST = "8.8.8.8"
SPEED_URL = "https://speed.cloudflare.com/__down?bytes=5000000"
IS_WINDOWS = sys.platform.startswith("win")

DEFAULTS = {
    "min_mbps": 5.0,
    "max_ping_ms": 150,
    "min_wifi_percent": 40,
    "projector_position": "",
    "firebase_url": "https://spaceapps-cairo-techops-default-rtdb.firebaseio.com",
    "checker_name": "Mohamed",
}

def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg

def save_config(cfg: dict):
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"Error saving config: {e}")

# --------------------------------------------------------------------------- Diagnostic tools
def _run(cmd, timeout):
    kwargs = {"capture_output": True, "timeout": timeout}
    if IS_WINDOWS:
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    return subprocess.run(cmd, **kwargs).stdout.decode("utf-8", errors="ignore")

def measure_ping(host: str = PING_HOST, count: int = 4):
    try:
        if IS_WINDOWS:
            out = _run(["ping", "-n", str(count), "-w", "2000", host], 20)
            for line in reversed(out.splitlines()):
                nums = re.findall(r"(\d+)\s*ms", line)
                if len(nums) == 3:
                    return float(nums[2])
            replies = [float(x) for x in re.findall(r"[=<](\d+)\s*ms", out)]
            if replies:
                return round(sum(replies) / len(replies), 1)
        else:
            out = _run(["ping", "-c", str(count), "-W", "2", host], 20)
            m = re.search(r"=\s*[\d.]+/([\d.]+)/", out)
            if m:
                return float(m.group(1))
    except Exception:
        pass

    # Fallback to TCP connect timing
    times = []
    for _ in range(count):
        try:
            t0 = time.perf_counter()
            with socket.create_connection((host, 53), timeout=2):
                times.append((time.perf_counter() - t0) * 1000)
        except OSError:
            pass
    return round(sum(times) / len(times), 1) if times else None

def measure_download(url: str = SPEED_URL, max_seconds: float = 30.0):
    try:
        total, t0 = 0, time.perf_counter()
        with requests.get(url, stream=True, timeout=(6, 15)) as r:
            r.raise_for_status()
            for chunk in r.iter_content(65536):
                total += len(chunk)
                if time.perf_counter() - t0 > max_seconds:
                    break
        dt = time.perf_counter() - t0
        return round(total * 8 / dt / 1e6, 2) if total and dt > 0 else None
    except Exception:
        return None

def measure_wifi():
    try:
        if IS_WINDOWS:
            out = _run(["netsh", "wlan", "show", "interfaces"], 8)
            m = re.search(r"^\s*\S[^:\n]*:\s*(\d{1,3})%\s*$", out, re.MULTILINE)
            return int(m.group(1)) if m else None
        if sys.platform.startswith("linux"):
            out = _run(["nmcli", "-t", "-f", "ACTIVE,SIGNAL", "dev", "wifi"], 8)
            m = re.search(r"^yes:(\d+)", out, re.MULTILINE)
            return int(m.group(1)) if m else None
    except Exception:
        pass
    return None

class Measurements:
    def __init__(self, callback=None):
        self.ping = None
        self.download = None
        self.wifi = None
        self.done = threading.Event()
        self.stage = "starting"
        self.callback = callback
        threading.Thread(target=self._run_all, daemon=True).start()

    def _run_all(self):
        try:
            self.stage = "ping"
            if self.callback: self.callback("Pinging 8.8.8.8...")
            self.wifi = measure_wifi()
            self.ping = measure_ping()
            self.stage = "download"
            if self.callback: self.callback(f"Measuring download speed (5MB payload)...")
            self.download = measure_download()
        finally:
            self.stage = "done"
            self.done.set()
            if self.callback: self.callback(self.summary())

    def summary(self) -> str:
        if not self.done.is_set():
            return f"Network test ({self.stage})..."
        p = f"{self.ping:g} ms" if self.ping is not None else "Fail"
        d = f"{self.download:g} Mbps" if self.download is not None else "Fail"
        w = f" | Wi-Fi {self.wifi}%" if self.wifi is not None else ""
        return f"Ping: {p}  |  Speed: {d}{w}"

# --------------------------------------------------------------------------- Fullscreen Calibration
def open_calibration_window(room: int, meas: Measurements, cfg: dict, on_complete=None):
    win = tk.Toplevel()
    win.title(f"Projector Calibration — Room {room:02d}")
    win.configure(bg="black")
    win.config(cursor="none")

    pos = str(cfg.get("projector_position", "")).strip()
    if re.fullmatch(r"-?\d+\s*,\s*-?\d+", pos):
        x, y = [int(v) for v in pos.split(",")]
        win.geometry(f"1280x720+{x}+{y}")
        win.update_idletasks()
    win.attributes("-fullscreen", True)
    win.attributes("-topmost", True)

    canvas = tk.Canvas(win, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    def finish(choice):
        win.destroy()
        if on_complete:
            on_complete(choice)

    def on_key(event):
        k = event.keysym.lower()
        if k == "g": finish("G")
        elif k == "b": finish("B")
        elif k == "escape": finish(None)

    win.bind("<Key>", on_key)

    def draw(_event=None):
        W, H = canvas.winfo_width(), canvas.winfo_height()
        if W < 10 or H < 10: return
        canvas.delete("all")
        s = min(W / 1920, H / 1080)

        # Focus grid
        step = max(20, int(60 * s))
        for i, gx in enumerate(range(0, W, step)):
            canvas.create_line(gx, 0, gx, H, fill="#6a6a6a" if i % 5 == 0 else "#222222")
        for i, gy in enumerate(range(0, H, step)):
            canvas.create_line(0, gy, W, gy, fill="#6a6a6a" if i % 5 == 0 else "#222222")

        # Diagonals & circle
        canvas.create_line(0, 0, W, H, fill="#666")
        canvas.create_line(0, H, W, 0, fill="#666")
        r = H * 0.30
        canvas.create_oval(W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r, outline="#ffffff", width=max(2, int(3 * s)))

        # RGB Bars
        bars = ["#ffffff", "#ffff00", "#00ffff", "#00ff00", "#ff00ff", "#ff0000", "#0000ff", "#000000"]
        x0, x1, y0, y1 = W * 0.08, W * 0.92, H * 0.09, H * 0.27
        bw = (x1 - x0) / len(bars)
        for i, c in enumerate(bars):
            canvas.create_rectangle(x0 + i * bw, y0, x0 + (i + 1) * bw, y1, fill=c, outline="#333")

        # Instructions
        px0, px1, py0, py1 = W * 0.16, W * 0.84, H * 0.36, H * 0.64
        canvas.create_rectangle(px0, py0, px1, py1, fill="#04060f", outline="#fc3d21", width=max(2, int(4 * s)))
        cx = W / 2
        canvas.create_text(cx, py0 + (py1 - py0) * 0.22, fill="#38bdf8",
                           font=("Segoe UI", max(12, int(34 * s)), "bold"),
                           text=f"ROOM {room:02d} — PROJECTOR CALIBRATION")
        canvas.create_text(cx, py0 + (py1 - py0) * 0.52, fill="white",
                           font=("Segoe UI", max(14, int(42 * s)), "bold"),
                           text="Press [G] if Data Show is GOOD  |  Press [B] if BAD")
        canvas.create_text(cx, py0 + (py1 - py0) * 0.80, fill="#facc15", tags="status",
                           font=("Segoe UI", max(10, int(24 * s))), text=meas.summary())

        # Outer border
        t = max(8, int(16 * s))
        canvas.create_rectangle(t / 2, t / 2, W - t / 2, H - t / 2, outline="white", width=t)

    canvas.bind("<Configure>", draw)

    def poll():
        if win.winfo_exists():
            canvas.itemconfig("status", text=meas.summary())
            win.after(300, poll)

    win.after(200, lambda: (win.focus_force(), canvas.focus_set()))
    win.after(300, poll)

# --------------------------------------------------------------------------- Firebase Upload
def upload_room_data(cfg, room: int, choice: str, ping: float, dl: float, wifi: int, note: str = ""):
    base = f"{cfg['firebase_url'].rstrip('/')}/rooms/room_{room}"
    problems = []
    if choice == "B" or choice == "Issue":
        problems.append("Data Show issue")
    if ping is None:
        problems.append("no internet (ping failed)")
    elif ping > cfg["max_ping_ms"]:
        problems.append(f"high ping {ping:g} ms")
    if dl is None:
        problems.append("speed test failed")
    elif dl < cfg["min_mbps"]:
        problems.append(f"slow download {dl:g} Mbps")
    if wifi is not None and wifi < cfg["min_wifi_percent"]:
        problems.append(f"weak Wi-Fi {wifi}%")
    if note.strip():
        problems.append(note.strip())

    payload = {
        "ping_ms": ping,
        "download_mbps": dl,
        "wifi_signal": wifi,
        "datashow": "OK" if (choice == "G" or choice == "OK") else "Issue",
        "checked_by": cfg.get("checker_name", "Tech Ops"),
        "updated_at": {".sv": "timestamp"},
        "source": "desktop-app",
        "note": "; ".join(problems) if problems else None,
    }

    try:
        sos = requests.get(f"{base}/sos.json", timeout=6).json()
    except Exception:
        sos = None
    if not sos:
        payload["status"] = "WARNING" if problems else "READY"

    for attempt in range(1, 4):
        try:
            r = requests.patch(f"{base}.json", json=payload, timeout=8)
            if r.ok:
                return True, payload.get("status", "READY"), problems
        except Exception:
            time.sleep(1)
    return False, "ERROR", ["Failed to connect to Firebase"]

# --------------------------------------------------------------------------- Main Desktop GUI
class TechOpsInspectorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NASA Space Apps Cairo — Room Inspector")
        self.geometry("900x680")
        self.minsize(800, 600)
        self.configure(bg="#04060f")

        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.cfg = load_config()
        self.selected_room = 1
        self.datashow_choice = "OK"
        self.current_ping = None
        self.current_dl = None
        self.current_wifi = None
        self.meas = None
        self.rooms_cache = {}

        self._init_styles()
        self._build_ui()
        self._start_firebase_sync()

    def _init_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(".", background="#04060f", foreground="#e2e8f0")

    def _build_ui(self):
        # Header Frame
        hdr = tk.Frame(self, bg="#0c1226", padx=16, pady=12, highlightthickness=1, highlightbackground="#1b2545")
        hdr.pack(fill="x", padx=14, pady=(12, 6))

        title_box = tk.Frame(hdr, bg="#0c1226")
        title_box.pack(side="left")
        tk.Label(title_box, text="🛰️ NASA SPACE APPS CAIRO", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0c1226").pack(anchor="w")
        tk.Label(title_box, text="Strike Team Room Inspector", font=("Segoe UI", 16, "bold"), fg="#ffffff", bg="#0c1226").pack(anchor="w")

        right_box = tk.Frame(hdr, bg="#0c1226")
        right_box.pack(side="right")
        self.lbl_cloud = tk.Label(right_box, text="● Cloud Sync Active", font=("Segoe UI", 9, "bold"), fg="#22c55e", bg="#0c1226")
        self.lbl_cloud.pack(anchor="e")

        # Config row
        cfg_bar = tk.Frame(self, bg="#080c1c", padx=14, pady=8)
        cfg_bar.pack(fill="x", padx=14, pady=4)
        tk.Label(cfg_bar, text="Inspector (Rooms Team):", font=("Segoe UI", 10), fg="#94a3b8", bg="#080c1c").pack(side="left")
        self.entry_name = ttk.Combobox(
            cfg_bar,
            values=["خيري · Khairy", "كريم · Karim", "تسبيح · Tasbeeh", "عمر · Omar", "لجين · Logain"],
            font=("Segoe UI", 10),
            width=20
        )
        self.entry_name.set(self.cfg.get("checker_name", "خيري · Khairy"))
        self.entry_name.pack(side="left", padx=(8, 20))
        self.entry_name.bind("<<ComboboxSelected>>", self._on_name_change)
        self.entry_name.bind("<KeyRelease>", self._on_name_change)

        tk.Label(cfg_bar, text="Display Output:", font=("Segoe UI", 10), fg="#94a3b8", bg="#080c1c").pack(side="left")
        self.disp_var = tk.StringVar(value="Primary Screen")
        disp_opts = ttk.Combobox(cfg_bar, textvariable=self.disp_var, values=["Primary Screen", "Secondary (1920,0)", "Secondary (2560,0)"], width=18, state="readonly")
        disp_opts.pack(side="left", padx=8)
        disp_opts.bind("<<ComboboxSelected>>", self._on_disp_change)

        # Main Split Content
        content = tk.Frame(self, bg="#04060f")
        content.pack(fill="both", expand=True, padx=14, pady=6)

        # Left Column: 12 Rooms Grid
        left_col = tk.Frame(content, bg="#0c1226", padx=12, pady=12, highlightthickness=1, highlightbackground="#1b2545")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(left_col, text="SELECT WORKSHOP ROOM", font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#0c1226").pack(anchor="w", pady=(0, 8))

        grid_frame = tk.Frame(left_col, bg="#0c1226")
        grid_frame.pack(fill="both", expand=True)

        self.room_buttons = {}
        for i in range(ROOM_COUNT):
            rn = i + 1
            btn = tk.Button(
                grid_frame, text=f"Room {rn:02d}\n⚪ UNCHECKED", font=("Segoe UI", 10, "bold"),
                bg="#121a36", fg="#ffffff", activebackground="#0b3d91", activeforeground="#ffffff",
                relief="flat", bd=0, padx=6, pady=8, cursor="hand2",
                command=lambda n=rn: self._select_room(n)
            )
            btn.grid(row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4)
            grid_frame.grid_columnconfigure(i % 3, weight=1)
            grid_frame.grid_rowconfigure(i // 3, weight=1)
            self.room_buttons[rn] = btn

        # Right Column: Room Action Panel
        right_col = tk.Frame(content, bg="#0c1226", padx=14, pady=12, highlightthickness=1, highlightbackground="#1b2545", width=380)
        right_col.pack(side="right", fill="both", expand=True, padx=(6, 0))
        right_col.pack_propagate(False)

        self.lbl_selected_room = tk.Label(right_col, text="ROOM 01 INSPECTION", font=("Segoe UI", 14, "bold"), fg="#38bdf8", bg="#0c1226")
        self.lbl_selected_room.pack(anchor="w", pady=(0, 10))

        # Big 1-Click Fast Check
        btn_fast = tk.Button(
            right_col, text="🚀 Rapid Check (Projector + Speed + Upload)", font=("Segoe UI", 11, "bold"),
            bg="#0b3d91", fg="#ffffff", activebackground="#1e40af", relief="flat", cursor="hand2", pady=8,
            command=self._start_rapid_check
        )
        btn_fast.pack(fill="x", pady=(0, 10))

        # Projector verification frame
        ds_frame = tk.LabelFrame(right_col, text=" 1. Projector / Data Show ", font=("Segoe UI", 9, "bold"), bg="#0c1226", fg="#94a3b8", padx=10, pady=8)
        ds_frame.pack(fill="x", pady=6)

        btn_row = tk.Frame(ds_frame, bg="#0c1226")
        btn_row.pack(fill="x")
        self.btn_ds_ok = tk.Button(btn_row, text="🟢 GOOD / OK", font=("Segoe UI", 9, "bold"), bg="#14532d", fg="#86efac", relief="flat", padx=10, pady=6, cursor="hand2", command=lambda: self._set_ds("OK"))
        self.btn_ds_ok.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.btn_ds_bad = tk.Button(btn_row, text="🔴 ISSUE / BROKEN", font=("Segoe UI", 9, "bold"), bg="#222", fg="#888", relief="flat", padx=10, pady=6, cursor="hand2", command=lambda: self._set_ds("Issue"))
        self.btn_ds_bad.pack(side="right", fill="x", expand=True, padx=(4, 0))

        btn_pattern = tk.Button(ds_frame, text="🖥️ Open Calibration Pattern on Projector", font=("Segoe UI", 9), bg="#1e293b", fg="#e2e8f0", relief="flat", pady=4, cursor="hand2", command=self._open_pattern_only)
        btn_pattern.pack(fill="x", pady=(6, 0))

        # Network frame
        net_frame = tk.LabelFrame(right_col, text=" 2. Wi-Fi & Speed Test ", font=("Segoe UI", 9, "bold"), bg="#0c1226", fg="#94a3b8", padx=10, pady=8)
        net_frame.pack(fill="x", pady=6)

        self.lbl_net_results = tk.Label(net_frame, text="Ping: —   |   Speed: —   |   Wi-Fi: —", font=("Segoe UI", 10, "bold"), fg="#38bdf8", bg="#0c1226")
        self.lbl_net_results.pack(pady=4)

        btn_net = tk.Button(net_frame, text="⚡ Run Speed Test Now", font=("Segoe UI", 9), bg="#1e293b", fg="#e2e8f0", relief="flat", pady=4, cursor="hand2", command=self._run_net_test_only)
        btn_net.pack(fill="x")

        # Notes & Save Frame
        notes_frame = tk.Frame(right_col, bg="#0c1226")
        notes_frame.pack(fill="x", pady=6)
        tk.Label(notes_frame, text="Notes (optional):", font=("Segoe UI", 9), fg="#94a3b8", bg="#0c1226").pack(anchor="w")
        self.entry_note = tk.Entry(notes_frame, font=("Segoe UI", 9), bg="#04060f", fg="#ffffff", insertbackground="white")
        self.entry_note.pack(fill="x", pady=(2, 6))

        self.btn_upload = tk.Button(
            right_col, text="💾 Save & Upload to Cloud", font=("Segoe UI", 11, "bold"),
            bg="#16a34a", fg="#ffffff", activebackground="#15803d", relief="flat", cursor="hand2", pady=8,
            command=self._upload_manual
        )
        self.btn_upload.pack(fill="x", pady=(4, 0))

        # Status log bar at bottom
        self.lbl_log = tk.Label(self, text="Ready. Select a room or tap 'Rapid Check'.", font=("Segoe UI", 9), fg="#94a3b8", bg="#04060f", anchor="w")
        self.lbl_log.pack(fill="x", padx=16, pady=6)

        self._select_room(1)

    def _set_ds(self, choice):
        self.datashow_choice = choice
        if choice == "OK":
            self.btn_ds_ok.configure(bg="#14532d", fg="#86efac")
            self.btn_ds_bad.configure(bg="#222", fg="#888")
        else:
            self.btn_ds_bad.configure(bg="#7f1d1d", fg="#fca5a5")
            self.btn_ds_ok.configure(bg="#222", fg="#888")

    def _select_room(self, n):
        self.selected_room = n
        self.lbl_selected_room.configure(text=f"ROOM {n:02d} INSPECTION")
        for rn, btn in self.room_buttons.items():
            if rn == n:
                btn.configure(relief="solid", bd=2)
            else:
                btn.configure(relief="flat", bd=0)
        self._update_room_details()

    def _update_room_details(self):
        r = self.rooms_cache.get(f"room_{self.selected_room}", {})
        p = f"{r.get('ping_ms')} ms" if r.get('ping_ms') is not None else "—"
        d = f"{r.get('download_mbps')} Mbps" if r.get('download_mbps') is not None else "—"
        w = f"{r.get('wifi_signal')}%" if r.get('wifi_signal') is not None else "—"
        self.lbl_net_results.configure(text=f"Ping: {p}  |  Speed: {d}  |  Wi-Fi: {w}")
        if r.get('datashow'):
            self._set_ds(r.get('datashow'))

    def _on_name_change(self, _event=None):
        name = self.entry_name.get().strip()
        if name:
            self.cfg["checker_name"] = name
            save_config(self.cfg)

    def _on_disp_change(self, _event=None):
        v = self.disp_var.get()
        if "1920" in v: self.cfg["projector_position"] = "1920,0"
        elif "2560" in v: self.cfg["projector_position"] = "2560,0"
        else: self.cfg["projector_position"] = ""
        save_config(self.cfg)

    def _start_rapid_check(self):
        room = self.selected_room
        self.lbl_log.configure(text=f"Room {room}: Testing Wi-Fi & opening Projector Calibration...")
        self.meas = Measurements(callback=lambda txt: self.lbl_log.configure(text=f"Room {room}: {txt}"))
        open_calibration_window(room, self.meas, self.cfg, on_complete=self._on_rapid_calibration_done)

    def _on_rapid_calibration_done(self, choice):
        if choice is None:
            self.lbl_log.configure(text="Calibration skipped.")
            return

        self._set_ds("OK" if choice == "G" else "Issue")
        self.lbl_log.configure(text="Finishing speed tests and uploading to cloud...")

        def wait_and_upload():
            self.meas.done.wait(timeout=30)
            self.current_ping = self.meas.ping
            self.current_dl = self.meas.download
            self.current_wifi = self.meas.wifi
            ok, st, errs = upload_room_data(self.cfg, self.selected_room, choice, self.current_ping, self.current_dl, self.current_wifi, self.entry_note.get())
            if ok:
                self.lbl_log.configure(text=f"✔ Room {self.selected_room:02d} uploaded -> {st}!")
                self._fetch_rooms()
            else:
                self.lbl_log.configure(text=f"✖ Upload failed: {errs}")

        threading.Thread(target=wait_and_upload, daemon=True).start()

    def _open_pattern_only(self):
        m = Measurements()
        open_calibration_window(self.selected_room, m, self.cfg, on_complete=lambda c: self._set_ds("OK" if c == "G" else "Issue") if c else None)

    def _run_net_test_only(self):
        self.lbl_log.configure(text="Running network diagnostic...")
        m = Measurements(callback=lambda txt: self.lbl_log.configure(text=txt))
        def wait_net():
            m.done.wait(timeout=30)
            self.current_ping = m.ping
            self.current_dl = m.download
            self.current_wifi = m.wifi
            p = f"{m.ping:g} ms" if m.ping is not None else "Fail"
            d = f"{m.download:g} Mbps" if m.download is not None else "Fail"
            w = f"{m.wifi}%" if m.wifi is not None else "—"
            self.lbl_net_results.configure(text=f"Ping: {p}  |  Speed: {d}  |  Wi-Fi: {w}")
            self.lbl_log.configure(text=f"Network test finished: {p}, {d}")
        threading.Thread(target=wait_net, daemon=True).start()

    def _upload_manual(self):
        room = self.selected_room
        choice = self.datashow_choice
        note = self.entry_note.get()
        self.lbl_log.configure(text=f"Uploading Room {room} to cloud...")
        def do_upload():
            ok, st, errs = upload_room_data(self.cfg, room, choice, self.current_ping, self.current_dl, self.current_wifi, note)
            if ok:
                self.lbl_log.configure(text=f"✔ Room {room:02d} marked {st} in Firebase!")
                self._fetch_rooms()
            else:
                self.lbl_log.configure(text=f"✖ Upload failed: {errs}")
        threading.Thread(target=do_upload, daemon=True).start()

    def _start_firebase_sync(self):
        def loop():
            while True:
                self._fetch_rooms()
                time.sleep(4)
        threading.Thread(target=loop, daemon=True).start()

    def _fetch_rooms(self):
        url = f"{self.cfg['firebase_url'].rstrip('/')}/rooms.json"
        try:
            r = requests.get(url, timeout=5)
            if r.ok:
                data = r.json() or {}
                self.rooms_cache = data
                self.after(0, self._render_room_statuses)
        except Exception:
            pass

    def _render_room_statuses(self):
        for i in range(ROOM_COUNT):
            rn = i + 1
            btn = self.room_buttons.get(rn)
            if not btn: continue
            data = self.rooms_cache.get(f"room_{rn}", {})
            st = "SOS" if data.get("sos") else data.get("status", "UNCHECKED")
            color_map = {
                "READY": ("#14532d", "#86efac", "🟢 READY"),
                "WARNING": ("#713f12", "#fde047", "🟡 WARNING"),
                "SOS": ("#7f1d1d", "#fca5a5", "🚨 SOS"),
                "UNCHECKED": ("#121a36", "#ffffff", "⚪ UNCHECKED")
            }
            bg, fg, label = color_map.get(st, ("#121a36", "#ffffff", st))
            btn.configure(text=f"Room {rn:02d}\n{label}", bg=bg, fg=fg)

def main():
    app = TechOpsInspectorApp()
    app.mainloop()

if __name__ == "__main__":
    main()
