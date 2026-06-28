import json
import os
from pathlib import Path
from typing import Any, Dict

APP_NAME = "ControllerUtility"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "auto_start_mouse_mode": False,
    "mouse_overlay_enabled": False,
    "mouse_max_speed": 14,
    "mouse_deadzone": 0.15,
    "last_vibration_low": 0.5,
    "last_vibration_high": 0.5,
    "last_vibration_duration_ms": 1000,
}


def app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        path = Path(base) / APP_NAME
    else:
        path = Path.home() / f".{APP_NAME}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    return app_data_dir() / "settings.json"


def load_settings() -> Dict[str, Any]:
    path = settings_path()
    data = DEFAULT_SETTINGS.copy()
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
        except Exception:
            pass
    return data


def save_settings(data: Dict[str, Any]) -> None:
    merged = DEFAULT_SETTINGS.copy()
    merged.update(data)
    settings_path().write_text(json.dumps(merged, indent=2), encoding="utf-8")
