import os
from pathlib import Path
import yaml

CONFIG_DIR = Path.home() / ".config" / "flac-sync"
CONFIG_PATH = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "music_folder": "",
    "spotify": {
        "client_id": "",
        "client_secret": "",
    },
    "deezer": {
        "arl": "",
    },
    "matching": {
        "threshold": 85,
    },
    "download": {
        "temp_dir": str(Path.home() / ".cache" / "flac-sync" / "downloads"),
    },
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)


def is_configured(cfg: dict) -> bool:
    return bool(
        cfg.get("music_folder")
        and cfg.get("spotify", {}).get("client_id")
        and cfg.get("spotify", {}).get("client_secret")
        and cfg.get("deezer", {}).get("arl")
    )
