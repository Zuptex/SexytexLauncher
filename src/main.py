"""
SexytexBDO Launcher - GUI
A profile switcher and launcher for Black Desert Online with NVIDIA Profile Inspector.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
import subprocess
import threading
import webbrowser
import shutil
import time
from pathlib import Path
from updater import check_for_updates, APP_VERSION
from config import Config
import ctypes
from ctypes import wintypes

# ─── Paths ────────────────────────────────────────────────────────────────────
# sys.executable = the .exe itself (onedir mode), so .parent = the folder it lives in.
# In dev (not frozen), go up from src/ to the project root.
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

NPI_PATH     = BASE_DIR / "nvidiaProfileInspector" / "nvidiaProfileInspector.exe"
PROFILES_DIR = BASE_DIR / "profiles"
LAST_MODE    = BASE_DIR / "last_mode.txt"
CONFIG_FILE  = BASE_DIR / "config.json"

STEAM_PATH   = Path("C:/Program Files (x86)/Steam/steamapps/common/Black Desert Online/BlackDesertLauncher.exe")
PEARL_PATH   = Path("C:/Program Files (x86)/Black Desert Online/BlackDesertLauncher.exe")

COLORS = {
    "bg":        "#0d0d0f",
    "panel":     "#111116",
    "border":    "#1e1e28",
    "accent":    "#7c5cfc",
    "accent2":   "#c084fc",
    "green":     "#22c55e",
    "yellow":    "#f59e0b",
    "red":       "#ef4444",
    "text":      "#e2e8f0",
    "muted":     "#64748b",
    "input_bg":  "#16161f",
    "hover":     "#1a1a26",
}

FONT_TITLE  = ("Consolas", 22, "bold")
FONT_HEADER = ("Consolas", 11, "bold")
FONT_BODY   = ("Consolas", 10)
FONT_SMALL  = ("Consolas", 9)
FONT_MONO   = ("Courier New", 9)

ASCII_LOGO = """\
  ███████╗███████╗██╗  ██╗██╗   ██╗████████╗███████╗██╗  ██╗
  ██╔════╝██╔════╝╚██╗██╔╝╚██╗ ██╔╝╚══██╔══╝██╔════╝╚██╗██╔╝
  ███████╗█████╗   ╚███╔╝  ╚████╔╝    ██║   █████╗   ╚███╔╝ 
  ╚════██║██╔══╝   ██╔██╗   ╚██╔╝     ██║   ██╔══╝   ██╔██╗ 
  ███████║███████╗██╔╝ ██╗   ██║      ██║   ███████╗██╔╝ ██╗
  ╚══════╝╚══════╝╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝"""


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


class StyledButton(tk.Canvas):
    """Custom gradient-style button."""

    def __init__(self, parent, text, command=None, color=None, width=180, height=38, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=COLORS["panel"], highlightthickness=0, **kwargs)
        self.text    = text
        self.command = command
        self.color   = color or COLORS["accent"]
        self.w       = width
        self.h       = height
        self._draw()
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, bright=False):
        self.delete("all")
        c = self.color
        r, g, b = hex_to_rgb(c)
        glow_alpha = 180 if bright else 120
        # border glow
        self.create_rectangle(0, 0, self.w, self.h,
                              fill="", outline=c, width=1)
        # fill
        fill = f"#{min(r+20,255):02x}{min(g+20,255):02x}{min(b+20,255):02x}" if bright else c
        self.create_rectangle(1, 1, self.w-1, self.h-1,
                              fill=fill, outline="")
        # text
        self.create_text(self.w//2, self.h//2, text=self.text,
                         fill="white", font=FONT_HEADER)

    def _on_enter(self, _): self._draw(bright=True); self.config(cursor="hand2")
    def _on_leave(self, _): self._draw(bright=False); self.config(cursor="")
    def _on_click(self, _):
        if self.command:
            self.command()


class ProfileRow(tk.Frame):
    """Single row in the profile list."""

    def __init__(
        self,
        parent,
        name,
        path,
        on_apply,
        on_delete,
        on_select=None,
        is_active=False,
        is_selected=False,
        **kwargs
    ):
        bg = COLORS["hover"] if is_selected else COLORS["panel"]
        super().__init__(parent, bg=bg, **kwargs)
        self.name      = name
        self.path      = path
        self.on_apply  = on_apply
        self.on_delete = on_delete
        self.on_select = on_select
        self._base_bg = COLORS["panel"]
        self._sel_bg = COLORS["hover"]
        self._is_selected = bool(is_selected)
        self._is_hover = False

        dot_color = COLORS["green"] if is_active else COLORS["muted"]
        self.dot = tk.Label(self, text="●", fg=dot_color, bg=bg, font=FONT_SMALL)
        self.dot.pack(side="left", padx=(8, 4))

        self.name_lbl = tk.Label(self, text=name, fg=COLORS["text"], bg=bg,
                                 font=FONT_BODY, anchor="w", width=22)
        self.name_lbl.pack(side="left", padx=4)

        short = Path(path).name if path else "—"
        self.path_lbl = tk.Label(self, text=short, fg=COLORS["muted"], bg=bg,
                                 font=FONT_SMALL, anchor="w", width=30)
        self.path_lbl.pack(side="left", padx=4)

        def _apply():
            if self.on_select:
                self.on_select(name)
            self.on_apply(name)

        tk.Button(self, text="APPLY", command=_apply,
                  bg=COLORS["accent"], fg="white", font=FONT_SMALL,
                  relief="flat", padx=8, cursor="hand2").pack(side="right", padx=4, pady=4)

        tk.Button(self, text="✕", command=lambda: on_delete(name),
                  bg=COLORS["red"], fg="white", font=FONT_SMALL,
                  relief="flat", padx=6, cursor="hand2").pack(side="right", padx=2, pady=4)

        self.pack(fill="x", pady=1)
        self._bind_select()
        self._bind_hover()

    def _set_bg(self, bg: str):
        self.config(bg=bg)
        for w in (self.dot, self.name_lbl, self.path_lbl):
            w.config(bg=bg)

    def _bind_select(self):
        if not self.on_select:
            return

        def _select(_evt=None):
            self.on_select(self.name)

        for w in (self, self.dot, self.name_lbl, self.path_lbl):
            w.bind("<Button-1>", _select)
            w.config(cursor="hand2")

    def _bind_hover(self):
        def _enter(_):
            self._is_hover = True
            if not self._is_selected:
                self._set_bg(self._sel_bg)

        def _leave(_):
            self._is_hover = False
            if not self._is_selected:
                self._set_bg(self._base_bg)

        for w in (self, self.dot, self.name_lbl, self.path_lbl):
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("SexytexBDO Launcher")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.geometry("820x700")

        self.cfg          = Config(CONFIG_FILE)
        self.active_mode  = self._read_last_mode()
        self.log_lines    = []

        self._build_ui()
        self._scan_profiles_dir()
        self._refresh_profiles()
        self._log(f"SexytexBDO Launcher v{APP_VERSION} ready.", "ok")
        self._check_updates_bg()

    # ── WINDOWS HELPERS ───────────────────────────────────────────────────────

    @staticmethod
    def _parse_affinity_hex(s: str) -> int | None:
        """
        Convert a user-provided hex string into an affinity bitmask integer.
        Returns None if affinity is disabled (empty/"0"), otherwise an int.
        Raises ValueError for invalid non-empty values.
        """
        s = (s or "").strip()
        if not s or s == "0":
            return None
        # allow optional 0x prefix
        if s.lower().startswith("0x"):
            s = s[2:]
        if not all(ch in "0123456789abcdefABCDEF" for ch in s):
            raise ValueError("Affinity must be hex (e.g. 5550, FFFF, 0).")
        mask = int(s, 16)
        if mask <= 0:
            raise ValueError("Affinity mask must be > 0 (or use 0 to disable).")
        return mask

    @staticmethod
    def _set_process_affinity(pid: int, mask: int) -> None:
        """
        Set CPU affinity for a process id using Win32 API.
        Raises OSError on failure.
        """
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        OpenProcess = kernel32.OpenProcess
        OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        OpenProcess.restype = wintypes.HANDLE

        SetProcessAffinityMask = kernel32.SetProcessAffinityMask
        SetProcessAffinityMask.argtypes = [wintypes.HANDLE, wintypes.WPARAM]
        SetProcessAffinityMask.restype = wintypes.BOOL

        CloseHandle = kernel32.CloseHandle
        CloseHandle.argtypes = [wintypes.HANDLE]
        CloseHandle.restype = wintypes.BOOL

        PROCESS_SET_INFORMATION = 0x0200
        PROCESS_QUERY_INFORMATION = 0x0400
        handle = OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_INFORMATION, False, pid)
        if not handle:
            raise OSError(ctypes.get_last_error(), "OpenProcess failed")
        try:
            ok = SetProcessAffinityMask(handle, mask)
            if not ok:
                raise OSError(ctypes.get_last_error(), "SetProcessAffinityMask failed")
        finally:
            CloseHandle(handle)

    # ── UI BUILD ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=COLORS["bg"])
        hdr.pack(fill="x", padx=0, pady=0)

        logo_frame = tk.Frame(hdr, bg="#0a0a10")
        logo_frame.pack(fill="x")
        tk.Label(logo_frame, text=ASCII_LOGO, fg=COLORS["accent"],
                 bg="#0a0a10", font=("Courier New", 8, "bold"),
                 justify="left").pack(padx=16, pady=(10, 4), anchor="w")

        sub = tk.Frame(logo_frame, bg="#0a0a10")
        sub.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(sub, text="A Custom BDO Launcher for auto applying profiles and setting CPU affinity",
                 fg=COLORS["muted"], bg="#0a0a10",
                 font=FONT_SMALL).pack(side="left")
        self.version_label = tk.Label(sub, text=f"v{APP_VERSION}",
                                       fg=COLORS["accent2"], bg="#0a0a10",
                                       font=FONT_SMALL, cursor="hand2")
        self.version_label.pack(side="right")
        self.version_label.bind("<Button-1>", lambda _: self._check_updates_manual())

        # separator
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        # ── Main columns ──
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=10)

        left = tk.Frame(body, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side="right", fill="y", padx=(6, 0))

        # ── PROFILES panel ──
        self._section(left, "PROFILES")
        self.profile_frame = tk.Frame(left, bg=COLORS["panel"],
                                       relief="flat", bd=0)
        self.profile_frame.pack(fill="x", pady=(0, 8))

        add_row = tk.Frame(left, bg=COLORS["bg"])
        add_row.pack(fill="x", pady=(0, 12))
        StyledButton(add_row, "+ ADD PROFILE", self._add_profile,
                     color=COLORS["accent"], width=160, height=32).pack(side="left")

        # ── SETTINGS panel ──
        self._section(left, "SETTINGS")
        settings = tk.Frame(left, bg=COLORS["panel"])
        settings.pack(fill="x", pady=(0, 8))

        # Launch mode
        row = tk.Frame(settings, bg=COLORS["panel"])
        row.pack(fill="x", padx=10, pady=6)
        tk.Label(row, text="Launch Mode", fg=COLORS["muted"],
                 bg=COLORS["panel"], font=FONT_SMALL, width=18, anchor="w").pack(side="left")
        self.launch_mode = tk.StringVar(value=self.cfg.get("launch_mode", "steam"))
        for val, lbl in [("steam", "Steam"), ("pearl", "Pearl Abyss")]:
            tk.Radiobutton(row, text=lbl, variable=self.launch_mode, value=val,
                           bg=COLORS["panel"], fg=COLORS["text"],
                           selectcolor=COLORS["input_bg"], activebackground=COLORS["panel"],
                           font=FONT_SMALL, command=self._save_settings).pack(side="left", padx=8)

        # Custom exe
        crow = tk.Frame(settings, bg=COLORS["panel"])
        crow.pack(fill="x", padx=10, pady=4)
        tk.Label(crow, text="Custom Exe Path", fg=COLORS["muted"],
                 bg=COLORS["panel"], font=FONT_SMALL, width=18, anchor="w").pack(side="left")
        self.custom_exe = tk.StringVar(value=self.cfg.get("custom_exe", ""))
        ent = tk.Entry(crow, textvariable=self.custom_exe, bg=COLORS["input_bg"],
                       fg=COLORS["text"], insertbackground=COLORS["text"],
                       font=FONT_SMALL, relief="flat", width=32)
        ent.pack(side="left", padx=(0, 4))
        tk.Button(crow, text="Browse", command=self._browse_exe,
                  bg=COLORS["border"], fg=COLORS["text"], font=FONT_SMALL,
                  relief="flat", cursor="hand2").pack(side="left")

        # CPU Affinity
        arow = tk.Frame(settings, bg=COLORS["panel"])
        arow.pack(fill="x", padx=10, pady=4)
        tk.Label(arow, text="CPU Affinity (hex)", fg=COLORS["muted"],
                 bg=COLORS["panel"], font=FONT_SMALL, width=18, anchor="w").pack(side="left")
        self.affinity_var = tk.StringVar(value=self.cfg.get("affinity", "5550"))
        aff_entry = tk.Entry(arow, textvariable=self.affinity_var, bg=COLORS["input_bg"],
                             fg=COLORS["accent2"], insertbackground=COLORS["text"],
                             font=FONT_MONO, relief="flat", width=12)
        aff_entry.pack(side="left", padx=(0, 8))
        tk.Label(arow, text="(0=disable affinity)", fg=COLORS["muted"],
                 bg=COLORS["panel"], font=FONT_SMALL).pack(side="left")

        # Auto-update toggle
        urow = tk.Frame(settings, bg=COLORS["panel"])
        urow.pack(fill="x", padx=10, pady=(4, 8))
        tk.Label(urow, text="Auto-check updates", fg=COLORS["muted"],
                 bg=COLORS["panel"], font=FONT_SMALL, width=18, anchor="w").pack(side="left")
        self.auto_update = tk.BooleanVar(value=self.cfg.get("auto_update", True))
        tk.Checkbutton(urow, variable=self.auto_update, command=self._save_settings,
                       bg=COLORS["panel"], activebackground=COLORS["panel"],
                       selectcolor=COLORS["input_bg"], fg=COLORS["text"]).pack(side="left")
        tk.Label(urow, text="(checks GitHub on launch)",
                 fg=COLORS["muted"], bg=COLORS["panel"], font=FONT_SMALL).pack(side="left")

        # ── LOG ──
        self._section(left, "LOG")
        log_frame = tk.Frame(left, bg=COLORS["panel"])
        log_frame.pack(fill="both", expand=True)
        self.log_box = tk.Text(log_frame, bg=COLORS["panel"], fg=COLORS["muted"],
                                font=FONT_MONO, relief="flat", height=7,
                                state="disabled", wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=4, pady=4)
        self.log_box.tag_config("ok",   foreground=COLORS["green"])
        self.log_box.tag_config("warn", foreground=COLORS["yellow"])
        self.log_box.tag_config("err",  foreground=COLORS["red"])
        self.log_box.tag_config("info", foreground=COLORS["accent2"])

        # ── RIGHT: LAUNCH ──
        self._section(right, "LAUNCH")
        launch_panel = tk.Frame(right, bg=COLORS["panel"], width=200)
        launch_panel.pack(fill="x", pady=(0, 8))
        launch_panel.pack_propagate(False)
        launch_panel.configure(height=220)

        tk.Label(launch_panel, text="ACTIVE PROFILE",
                 fg=COLORS["muted"], bg=COLORS["panel"],
                 font=FONT_SMALL).pack(pady=(14, 2))
        self.active_label = tk.Label(launch_panel, text=self.active_mode or "—",
                                      fg=COLORS["accent"], bg=COLORS["panel"],
                                      font=FONT_HEADER)
        self.active_label.pack()

        tk.Frame(launch_panel, bg=COLORS["border"], height=1).pack(fill="x", padx=12, pady=10)

        self.launch_btn = StyledButton(launch_panel, "▶  LAUNCH BDO",
                                       self._launch, color=COLORS["green"],
                                       width=176, height=44)
        self.launch_btn.pack(pady=4)

        tk.Frame(launch_panel, bg=COLORS["border"], height=1).pack(fill="x", padx=12, pady=8)

        # selected profile indicator
        tk.Label(launch_panel, text="SELECTED",
                 fg=COLORS["muted"], bg=COLORS["panel"],
                 font=FONT_SMALL).pack()
        self.selected_label = tk.Label(launch_panel, text="—",
                                        fg=COLORS["text"], bg=COLORS["panel"],
                                        font=FONT_SMALL)
        self.selected_label.pack(pady=(2, 12))

        self.selected_profile = tk.StringVar()

        # ── GitHub link ──
        gh = tk.Label(right, text="★ GitHub", fg=COLORS["muted"],
                      bg=COLORS["bg"], font=FONT_SMALL, cursor="hand2")
        gh.pack(pady=4)
        gh.bind("<Button-1>", lambda _: webbrowser.open(
            "https://github.com/Zuptex/SexytexLauncher"))

    def _section(self, parent, title):
        row = tk.Frame(parent, bg=COLORS["bg"])
        row.pack(fill="x", pady=(6, 2))
        tk.Label(row, text=title, fg=COLORS["accent"],
                 bg=COLORS["bg"], font=FONT_HEADER).pack(side="left")
        tk.Frame(row, bg=COLORS["border"], height=1).pack(
            side="left", fill="x", expand=True, padx=8, pady=6)

    # ── PROFILES ─────────────────────────────────────────────────────────────

    def _scan_profiles_dir(self):
        """Auto-register any .nip files in the profiles/ folder not already in config."""
        if not PROFILES_DIR.exists():
            return
        profiles = self.cfg.get("profiles", {})
        known_paths = {Path(p).resolve() for p in profiles.values()}
        added = []
        for nip in sorted(PROFILES_DIR.glob("*.nip")):
            if nip.resolve() not in known_paths:
                # Use filename without extension as the display name
                name = nip.stem
                # Avoid name collisions
                unique_name = name
                i = 2
                while unique_name in profiles:
                    unique_name = f"{name} ({i})"
                    i += 1
                profiles[unique_name] = str(nip)
                added.append(unique_name)
        if added:
            self.cfg.set("profiles", profiles)
            self.cfg.save()

    def _refresh_profiles(self):
        for w in self.profile_frame.winfo_children():
            w.destroy()

        profiles = self.cfg.get("profiles", {})
        if not profiles:
            tk.Label(self.profile_frame, text="No profiles found. Add one above.",
                     fg=COLORS["muted"], bg=COLORS["panel"],
                     font=FONT_SMALL).pack(pady=8)
        else:
            # restore last selection if possible
            saved = (self.cfg.get("selected_profile", "") or "").strip()
            if saved and saved in profiles:
                self.selected_profile.set(saved)
                self.selected_label.config(text=saved)
            for name, path in profiles.items():
                is_active = (name.upper() == (self.active_mode or "").upper())
                is_selected = (name == self.selected_profile.get())
                ProfileRow(self.profile_frame, name, path,
                           on_apply=self._apply_profile,
                           on_delete=self._delete_profile,
                           on_select=self._select_profile,
                           is_active=is_active,
                           is_selected=is_selected)

        # auto-select first if nothing selected
        if not self.selected_profile.get() and profiles:
            first = next(iter(profiles))
            self._select_profile(first, refresh=False)

    def _select_profile(self, name: str, refresh: bool = True):
        """Set the currently selected profile (used for Launch / Apply)."""
        name = (name or "").strip()
        if not name:
            return
        self.selected_profile.set(name)
        self.selected_label.config(text=name)
        self.cfg.set("selected_profile", name)
        self.cfg.save()
        if refresh:
            self._refresh_profiles()

    def _add_profile(self):
        win = tk.Toplevel(self)
        win.title("Add Profile")
        win.configure(bg=COLORS["bg"])
        win.geometry("460x180")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Profile Name", fg=COLORS["text"],
                 bg=COLORS["bg"], font=FONT_BODY).grid(row=0, column=0, padx=12, pady=12, sticky="w")
        name_var = tk.StringVar()
        tk.Entry(win, textvariable=name_var, bg=COLORS["input_bg"],
                 fg=COLORS["text"], insertbackground=COLORS["text"],
                 font=FONT_BODY, relief="flat", width=30).grid(row=0, column=1, padx=8)

        tk.Label(win, text=".nip File", fg=COLORS["text"],
                 bg=COLORS["bg"], font=FONT_BODY).grid(row=1, column=0, padx=12, pady=4, sticky="w")
        path_var = tk.StringVar()
        path_entry = tk.Entry(win, textvariable=path_var, bg=COLORS["input_bg"],
                               fg=COLORS["text"], insertbackground=COLORS["text"],
                               font=FONT_SMALL, relief="flat", width=30)
        path_entry.grid(row=1, column=1, padx=8)

        def browse():
            f = filedialog.askopenfilename(
                title="Select .nip profile",
                filetypes=[("NIP Profile", "*.nip"), ("All Files", "*.*")]
            )
            if f:
                path_var.set(f)

        tk.Button(win, text="Browse", command=browse,
                  bg=COLORS["border"], fg=COLORS["text"],
                  font=FONT_SMALL, relief="flat", cursor="hand2").grid(row=1, column=2, padx=4)

        def save():
            n = name_var.get().strip()
            p = path_var.get().strip()
            if not n or not p:
                messagebox.showerror("Error", "Name and path required.", parent=win)
                return
            if not Path(p).exists():
                messagebox.showerror("Error", "Profile file not found.", parent=win)
                return

            # Copy into profiles dir
            dest = PROFILES_DIR / Path(p).name
            PROFILES_DIR.mkdir(exist_ok=True)
            shutil.copy2(p, dest)

            profiles = self.cfg.get("profiles", {})
            profiles[n] = str(dest)
            self.cfg.set("profiles", profiles)
            self.cfg.save()
            self._refresh_profiles()
            self._log(f"Profile '{n}' added.", "ok")
            win.destroy()

        StyledButton(win, "SAVE", save, color=COLORS["green"],
                     width=120, height=32).grid(row=2, column=1, pady=14, sticky="e")

    def _delete_profile(self, name):
        if not messagebox.askyesno("Delete Profile", f"Remove profile '{name}'?"):
            return
        profiles = self.cfg.get("profiles", {})
        profiles.pop(name, None)
        self.cfg.set("profiles", profiles)
        self.cfg.save()
        if self.selected_profile.get() == name:
            self.selected_profile.set("")
            self.selected_label.config(text="—")
        self._refresh_profiles()
        self._log(f"Profile '{name}' removed.", "warn")

    def _apply_profile(self, name):
        """Apply a named profile via NPI (no launch)."""
        # Keep "selected" in sync with what the user applies.
        self._select_profile(name)
        profiles = self.cfg.get("profiles", {})
        path = profiles.get(name)
        if not path or not Path(path).exists():
            self._log(f"Profile file missing for '{name}'.", "err")
            return
        self._run_npi(name, path)

    def _apply_selected(self):
        name = self.selected_profile.get()
        if not name:
            self._log("No profile selected.", "warn")
            return
        self._apply_profile(name)

    def _run_npi(self, name, path, on_done=None):
        """Apply an NPI profile in a background thread. Calls on_done() when finished."""
        if not NPI_PATH.exists():
            self._log("nvidiaProfileInspector.exe not found!", "err")
            if on_done:
                on_done(success=False)
            return

        last = self._read_last_mode()
        if last and last.upper() == name.upper():
            self._log(f"{name} already active — skipping import.", "info")
            if on_done:
                on_done(success=True)
            return

        def _worker():
            self._log(f"Applying profile: {name}…", "info")
            try:
                result = subprocess.run(
                    [str(NPI_PATH), "-importProfile", str(path)],
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    self._write_last_mode(name)
                    self.active_mode = name
                    self.after(0, lambda: self.active_label.config(
                        text=name, fg=COLORS["accent"]))
                    self.after(0, self._refresh_profiles)
                    self._log(f"Profile '{name}' applied.", "ok")
                    if on_done:
                        on_done(success=True)
                else:
                    self._log(f"NPI exited with code {result.returncode}.", "err")
                    if on_done:
                        on_done(success=False)
            except subprocess.TimeoutExpired:
                self._log("NPI timed out after 30s — profile may not have applied.", "warn")
                if on_done:
                    on_done(success=True)   # proceed anyway
            except Exception as e:
                self._log(f"NPI error: {e}", "err")
                if on_done:
                    on_done(success=False)

        threading.Thread(target=_worker, daemon=True).start()

    # ── LAUNCH ───────────────────────────────────────────────────────────────

    def _launch(self):
        # Resolve exe path first so we can bail early before touching NPI
        mode = self.launch_mode.get()
        custom = self.custom_exe.get().strip()
        if custom and Path(custom).exists():
            exe = Path(custom)
        elif mode == "steam":
            exe = STEAM_PATH
        else:
            exe = PEARL_PATH

        if not exe.exists():
            self._log(f"Game exe not found: {exe}", "err")
            messagebox.showerror("Not Found",
                                  f"Game launcher not found at:\n{exe}\n\n"
                                  "Set a custom path in Settings.")
            return

        self._save_settings()
        affinity = self.affinity_var.get().strip()

        def do_launch(success=True):
            try:
                affinity_mask = self._parse_affinity_hex(affinity)
            except ValueError as ve:
                self._log(f"Invalid affinity: {ve}", "err")
                messagebox.showerror("Invalid CPU Affinity", str(ve))
                return

            affinity_display = affinity if affinity_mask is not None else "none"
            self._log(f"Launching BDO (affinity={affinity_display})…", "info")
            try:
                work_dir = str(exe.parent)
                args = [str(exe)]
                if mode == "steam":
                    args.append("-steam")

                proc = subprocess.Popen(args, cwd=work_dir)
                if affinity_mask is not None:
                    # Best-effort: process may exit quickly if it fails to start.
                    try:
                        self._set_process_affinity(proc.pid, affinity_mask)
                        self._log(f"Applied CPU affinity mask 0x{affinity_mask:X}.", "ok")
                    except Exception as e:
                        self._log(f"Could not set affinity: {e}", "warn")
                self._log("BDO launched!", "ok")
                # Exit the launcher after a successful spawn.
                self.after(600, self.destroy)
            except Exception as e:
                self._log(f"Launch error: {e}", "err")
                messagebox.showerror("Launch Failed", f"Could not launch:\n{exe}\n\nError:\n{e}")

        # Apply profile in background, then launch when done
        name = self.selected_profile.get()
        if name:
            profiles = self.cfg.get("profiles", {})
            path = profiles.get(name, "")
            if Path(path).exists():
                last = self._read_last_mode()
                if last and last.upper() == name.upper():
                    # Profile already active, launch immediately
                    threading.Thread(target=do_launch, daemon=True).start()
                else:
                    # Apply profile first, then launch in the on_done callback
                    self._run_npi(name, path, on_done=lambda success: 
                                  threading.Thread(target=do_launch, daemon=True).start())
            else:
                self._log(f"Profile file missing for '{name}', launching anyway.", "warn")
                threading.Thread(target=do_launch, daemon=True).start()
        else:
            threading.Thread(target=do_launch, daemon=True).start()

    # ── SETTINGS ─────────────────────────────────────────────────────────────

    def _save_settings(self):
        self.cfg.set("launch_mode", self.launch_mode.get())
        self.cfg.set("affinity",    self.affinity_var.get().strip())
        self.cfg.set("auto_update", self.auto_update.get())
        self.cfg.set("custom_exe",  self.custom_exe.get().strip())
        self.cfg.save()

    def _browse_exe(self):
        f = filedialog.askopenfilename(
            title="Select BDO Launcher exe",
            filetypes=[("Executable", "*.exe"), ("All Files", "*.*")]
        )
        if f:
            self.custom_exe.set(f)
            self._save_settings()

    # ── UPDATES ──────────────────────────────────────────────────────────────

    def _check_updates_bg(self):
        if not self.cfg.get("auto_update", True):
            return
        def _check():
            result = check_for_updates()
            if result:
                self.after(0, lambda: self._prompt_update(result))
        threading.Thread(target=_check, daemon=True).start()

    def _check_updates_manual(self):
        self._log("Checking for updates…", "info")
        def _check():
            result = check_for_updates()
            if result:
                self.after(0, lambda: self._prompt_update(result))
            else:
                self.after(0, lambda: self._log("You are on the latest version.", "ok"))
        threading.Thread(target=_check, daemon=True).start()

    def _prompt_update(self, info):
        answer = messagebox.askyesno(
            "Update Available",
            f"Version {info['version']} is available!\n\n"
            f"Changes:\n{info['notes']}\n\n"
            "Open the releases page to download?"
        )
        if answer:
            webbrowser.open(info["url"])

    # ── HELPERS ──────────────────────────────────────────────────────────────

    def _read_last_mode(self):
        if LAST_MODE.exists():
            return LAST_MODE.read_text().strip()
        return None

    def _write_last_mode(self, name):
        LAST_MODE.write_text(name)

    def _log(self, msg, tag="info"):
        self.log_box.config(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_box.see("end")
        self.log_box.config(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
