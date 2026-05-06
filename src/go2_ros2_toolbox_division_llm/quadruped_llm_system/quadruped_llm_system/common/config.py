from pathlib import Path
from typing import Any, Dict
import json

from ament_index_python.packages import get_package_share_directory
import yaml


def config_dir() -> Path:
    return Path(get_package_share_directory("quadruped_llm_system")) / "config"


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
