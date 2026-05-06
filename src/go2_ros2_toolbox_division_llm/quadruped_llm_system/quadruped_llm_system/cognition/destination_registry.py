import math
import re
from typing import Any


class DestinationRegistry:
    # 负责把一批地点数据组织成可检索的索引结构。
    def __init__(self, rows: list[dict[str, Any]], frame_id: str = "map") -> None:
        self.frame_id = str(frame_id).strip() or "map"
        self.destinations: dict[str, dict[str, Any]] = {}
        self.alias_to_id: dict[str, str] = {}
        self._load(rows)

    @classmethod
    # 从 YAML 数据构造实例
    def from_yaml_data(cls, yaml_data: dict[str, Any]) -> "DestinationRegistry":
        frame_id = str(yaml_data.get("frame_id", "map")).strip() or "map"
        rows = yaml_data.get("destinations", [])
        if not isinstance(rows, list):
            raise RuntimeError("destinations.yaml missing destinations list")
        return cls(rows, frame_id=frame_id)

    @staticmethod
    # 规范化文本：去除多余空白、统一大小写等，确保别名匹配时的一致性。
    def _norm(text: str) -> str:
        text = text.strip().lower()
        text = re.sub(r"\s+", " ", text)
        return text

    # 加载地点数据，构建 id、name 和别名的索引，同时检查重复和冲突。
    def _load(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            dest_id = str(row.get("id", "")).strip()
            name = str(row.get("name", "")).strip() or dest_id
            pose = row.get("pose", {})
            aliases = row.get("aliases", [])

            if not dest_id:
                raise RuntimeError("destination id required")

            x = float(pose["x"])
            y = float(pose["y"])
            yaw_deg = float(pose["yaw_deg"])

            item = {
                "id": dest_id,
                "name": name,
                "frame_id": self.frame_id,
                "pose": {
                    "x": x,
                    "y": y,
                    "yaw_deg": yaw_deg,
                },
                "aliases": [],
            }

            # id、name 和显式 aliases 都会被纳入同一套别名索引。
            all_aliases = [dest_id, name] + list(aliases)
            normalized = []
            for alias in all_aliases:
                key = self._norm(str(alias))
                if not key:
                    continue
                owner = self.alias_to_id.get(key)
                if owner and owner != dest_id:
                    raise RuntimeError(f"alias {key} already assigned to destination {owner}")
                self.alias_to_id[key] = dest_id
                if key not in normalized:
                    normalized.append(key)

            item["aliases"] = normalized
            self.destinations[dest_id] = item

    def get(self, dest_id: str) -> dict[str, Any] | None:
        return self.destinations.get(dest_id)

    def all(self) -> list[dict[str, Any]]:
        return list(self.destinations.values())


    # 精确匹配
    def resolve_direct(self, text: str) -> str | None:
        return self.alias_to_id.get(self._norm(text))


    # 对输入文本进行模糊匹配，返回最相关的几个地点 ID，供后续处理使用。
    def rank_candidates(self, text: str, limit: int = 3) -> list[str]:
        needle = self._norm(text)
        if not needle:
            return []

        scored = []
        needle_tokens = set(needle.split())

        for dest_id, item in self.destinations.items():
            best = 0.0
            for alias in item["aliases"]:
                alias_tokens = set(alias.split())
                # 用词重叠和简单序列相似度做一个轻量排序，优先找最像的地点。
                overlap = len(needle_tokens & alias_tokens) / max(1, len(alias_tokens))
                seq = self._sequence_score(needle, alias)
                score = 0.7 * seq + 0.3 * overlap
                best = max(best, score)
            scored.append((best, dest_id))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [dest_id for _, dest_id in scored[:limit]]

    @staticmethod
    def _sequence_score(a: str, b: str) -> float:
        if a == b:
            return 1.0
        a_set = set(a.split())
        b_set = set(b.split())
        return len(a_set & b_set) / max(1, len(a_set | b_set))

    def as_catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "destination_id": d["id"],
                "destination_name": d["name"],
                "aliases": d["aliases"],
            }
            for d in self.destinations.values()
        ]

    def pose_stamped_dict(self, dest_id: str) -> dict[str, Any]:
        # 导航控制层最终要的是姿态消息，这里统一把 yaw 角转换成四元数。
        dest = self.destinations[dest_id]
        yaw_rad = math.radians(float(dest["pose"]["yaw_deg"]))
        return {
            "header": {"frame_id": dest["frame_id"]},
            "pose": {
                "position": {
                    "x": float(dest["pose"]["x"]),
                    "y": float(dest["pose"]["y"]),
                    "z": 0.0,
                },
                "orientation": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": math.sin(yaw_rad / 2.0),
                    "w": math.cos(yaw_rad / 2.0),
                },
            },
        }
