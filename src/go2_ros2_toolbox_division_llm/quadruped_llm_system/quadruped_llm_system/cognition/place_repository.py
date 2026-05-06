import re
from pathlib import Path
from typing import Any

from quadruped_llm_system.common.config import load_yaml
from quadruped_llm_system.cognition.destination_registry import DestinationRegistry
from quadruped_llm_system.cognition.memory_store import MemoryStore


class PlaceRepository:
    # 对上层屏蔽“静态点位 + 动态点位”的双数据源细节。
    def __init__(self, static_yaml_name: str, memory_path: Path) -> None:
        self.static_yaml_name = static_yaml_name
        self.memory_store = MemoryStore(memory_path)
        self.static_registry = DestinationRegistry.from_yaml_data(load_yaml(static_yaml_name))
        self.frame_id = self.static_registry.frame_id
        self.dynamic_registry = DestinationRegistry([], frame_id=self.frame_id)
        self.registry = self.static_registry
        self._reload_dynamic()

    @staticmethod
    def _slug(text: str) -> str:
        lowered = text.strip().lower()
        lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
        return lowered.strip("_") or "point"

    def _reload_dynamic(self) -> None:
        # 重新从 memory_points.json 构建动态点位，并和静态点位合并成统一索引。
        rows: list[dict[str, Any]] = []
        reserved_ids = set(self.static_registry.destinations.keys())
        reserved_aliases = set(self.static_registry.alias_to_id.keys())

        for raw in self.memory_store.all().values():
            if not isinstance(raw, dict):
                continue

            dest_id = str(raw.get("id", "")).strip()
            name = str(raw.get("name", "")).strip() or dest_id
            pose = raw.get("pose", {})
            aliases = raw.get("aliases", [])
            if not dest_id or dest_id in reserved_ids:
                continue

            normalized_aliases = []
            conflict = False
            for alias in [dest_id, name] + list(aliases):
                key = DestinationRegistry._norm(str(alias))
                if not key:
                    continue
                # 动态点默认不覆盖静态点别名，避免运行时记忆把基础点位“顶掉”。
                if key in reserved_aliases:
                    conflict = True
                    break
                if key not in normalized_aliases:
                    normalized_aliases.append(key)

            if conflict:
                continue

            try:
                row = {
                    "id": dest_id,
                    "name": name,
                    "aliases": normalized_aliases,
                    "pose": {
                        "x": float(pose["x"]),
                        "y": float(pose["y"]),
                        "yaw_deg": float(pose["yaw_deg"]),
                    },
                }
            except (KeyError, TypeError, ValueError):
                continue

            rows.append(row)
            reserved_ids.add(dest_id)
            reserved_aliases.update(normalized_aliases)

        self.dynamic_registry = DestinationRegistry(rows, frame_id=self.frame_id)
        merged_rows = []
        # 上层只关心“有哪些可用地点”，不关心来源，所以这里合成统一视图。
        for item in self.static_registry.all() + self.dynamic_registry.all():
            merged_rows.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "aliases": item["aliases"],
                    "pose": item["pose"],
                }
            )
        self.registry = DestinationRegistry(merged_rows, frame_id=self.frame_id)

    def get(self, dest_id: str) -> dict[str, Any] | None:
        return self.registry.get(dest_id)

    def resolve_direct(self, text: str) -> str | None:
        return self.registry.resolve_direct(text)

    def rank_candidates(self, text: str, limit: int = 3) -> list[str]:
        return self.registry.rank_candidates(text, limit=limit)

    def as_catalog(self) -> list[dict[str, Any]]:
        return self.registry.as_catalog()

    def pose_stamped_dict(self, dest_id: str) -> dict[str, Any]:
        return self.registry.pose_stamped_dict(dest_id)

    def add_memory_point(
        self,
        name: str,
        x: float,
        y: float,
        yaw_deg: float,
        aliases: list[str] | None = None,
    ) -> dict[str, Any]:
        # 运行时新增记忆点时生成 mem_* 风格 id，避免和静态点位混淆。
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("memory point name required")

        alias_list = list(aliases or [])
        candidate_id = f"mem_{self._slug(clean_name)}"
        suffix = 1
        while self.get(candidate_id):
            suffix += 1
            candidate_id = f"mem_{self._slug(clean_name)}_{suffix}"

        # 新点位写入前先做别名冲突检查，避免后续导航命中不确定目标。
        for alias in [candidate_id, clean_name] + alias_list:
            owner = self.resolve_direct(str(alias))
            if owner is not None:
                raise ValueError(f"alias already in use: {alias}")

        point = {
            "id": candidate_id,
            "name": clean_name,
            "aliases": alias_list,
            "pose": {
                "x": float(x),
                "y": float(y),
                "yaw_deg": float(yaw_deg),
            },
        }
        self.memory_store.set(candidate_id, point)
        self._reload_dynamic()
        return point
