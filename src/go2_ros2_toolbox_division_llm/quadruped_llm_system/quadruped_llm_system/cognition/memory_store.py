import json
from pathlib import Path
from typing import Any


class MemoryStore:
    # 只负责 JSON 持久化，不承担地点解析等业务逻辑。
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str) -> Any:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._save()

    def all(self) -> dict[str, Any]:
        return dict(self._data)
