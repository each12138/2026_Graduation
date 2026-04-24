import json
import os


class PlaceMemory:
    """Persistent named-place memory, not a geometric map."""

    def __init__(self, memory_file=None):
        if memory_file is None:
            pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            memory_file = os.path.join(pkg_root, "config", "place_memory.json")

        self.memory_path = memory_file
        self.memory = {}

        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
        if not os.path.exists(self.memory_path):
            with open(self.memory_path, "w", encoding="utf-8") as file_obj:
                json.dump({}, file_obj, ensure_ascii=False, indent=2)

        try:
            with open(self.memory_path, "r", encoding="utf-8") as file_obj:
                self.memory = json.load(file_obj)
            if not isinstance(self.memory, dict):
                self.memory = {}
        except (json.JSONDecodeError, OSError):
            self.memory = {}
            with open(self.memory_path, "w", encoding="utf-8") as file_obj:
                json.dump(self.memory, file_obj, ensure_ascii=False, indent=2)

    def save_place(self, name, pose):
        key = str(name).strip()
        if not key:
            raise ValueError("invalid_place_name")
        self.memory[key] = pose
        with open(self.memory_path, "w", encoding="utf-8") as file_obj:
            json.dump(self.memory, file_obj, ensure_ascii=False, indent=2)

    def get_place(self, name):
        return self.memory.get(str(name).strip())

    def all_places(self):
        return dict(self.memory)
