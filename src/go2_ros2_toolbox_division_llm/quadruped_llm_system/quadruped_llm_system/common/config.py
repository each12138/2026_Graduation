from pathlib import Path
from typing import Any, Dict
import json

import yaml


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def config_dir() -> Path:
    return package_root() / "config"


def load_yaml(name: str) -> Dict[str, Any]:
    path = config_dir() / name
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_json(name: str) -> Dict[str, Any]:
    path = config_dir() / name
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}
