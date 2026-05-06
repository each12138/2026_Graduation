import math
import re
from typing import Any, Dict, List, Optional


class DestinationRegistry:
    def __init__(self, rows: List[Dict[str, Any]], frame_id: str = "map") -> None:
        self.frame_id = str(frame_id).strip() or "map"
        self.destinations = {}  # type: Dict[str, Dict[str, Any]]
        self.alias_to_id = {}  # type: Dict[str, str]
        self._load(rows)

    @classmethod
    def from_yaml_data(cls, yaml_data: Dict[str, Any]) -> "DestinationRegistry":
        frame_id = str(yaml_data.get("frame_id", "map")).strip() or "map"
        rows = yaml_data.get("destinations", [])
        if not isinstance(rows, list):
            raise RuntimeError("destinations.yaml missing destinations list")
        return cls(rows, frame_id=frame_id)

    @staticmethod
    def _norm(text: str) -> str:
        text = text.strip().lower()
        text = re.sub(r"\s+", " ", text)
        return text

    def _load(self, rows: List[Dict[str, Any]]) -> None:
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

            all_aliases = [dest_id, name] + list(aliases)
            normalized = []
            for alias in all_aliases:
                key = self._norm(str(alias))
                if not key:
                    continue
                owner = self.alias_to_id.get(key)
                if owner and owner != dest_id:
                    raise RuntimeError(
                        "alias {0} already assigned to destination {1}".format(key, owner)
                    )
                self.alias_to_id[key] = dest_id
                if key not in normalized:
                    normalized.append(key)

            item["aliases"] = normalized
            self.destinations[dest_id] = item

    def get(self, dest_id: str) -> Optional[Dict[str, Any]]:
        return self.destinations.get(dest_id)

    def all(self) -> List[Dict[str, Any]]:
        return list(self.destinations.values())

    def resolve_direct(self, text: str) -> Optional[str]:
        return self.alias_to_id.get(self._norm(text))

    def rank_candidates(self, text: str, limit: int = 3) -> List[str]:
        needle = self._norm(text)
        if not needle:
            return []

        scored = []
        needle_tokens = set(needle.split())

        for dest_id, item in self.destinations.items():
            best = 0.0
            for alias in item["aliases"]:
                alias_tokens = set(alias.split())
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

    def as_catalog(self) -> List[Dict[str, Any]]:
        return [
            {
                "destination_id": d["id"],
                "destination_name": d["name"],
                "aliases": d["aliases"],
            }
            for d in self.destinations.values()
        ]

    def pose_stamped_dict(self, dest_id: str) -> Dict[str, Any]:
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
