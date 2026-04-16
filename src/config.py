"""
Config manager — persists settings to JSON.
"""
import json
from pathlib import Path


class Config:
    _defaults = {
        "launch_mode": "steam",
        "affinity":    "5550",
        "auto_update": True,
        "custom_exe":  "",
        "selected_profile": "",
        "profiles":    {},
        "hidden_profile_files": [],
    }

    def __init__(self, path):
        self._path = Path(path)
        self._data = dict(self._defaults)
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                loaded = json.loads(self._path.read_text(encoding="utf-8"))
                self._data.update(loaded)
            except Exception:
                pass

    def get(self, key, default=None):
        return self._data.get(key, default if default is not None else self._defaults.get(key))

    def set(self, key, value):
        self._data[key] = value

    def save(self):
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
