import json
import os


def _default_map_path(filename):
    env_path = os.getenv("GO2_LLM_MAP_PATH")
    if env_path:
        return env_path

    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(script_dir, filename)
    if os.path.exists(source_path):
        return source_path

    workspace_path = os.path.join(os.getcwd(), filename)
    return workspace_path


class SemanticMap:
    def __init__(self, map_file="map.json"):
        self.map_path = _default_map_path(map_file)
        self.map = {}

        map_dir = os.path.dirname(self.map_path)
        if map_dir:
            os.makedirs(map_dir, exist_ok=True)

        if not os.path.exists(self.map_path):
            with open(self.map_path, "w", encoding="utf-8") as file_obj:
                json.dump({}, file_obj, ensure_ascii=False, indent=4)

        try:
            with open(self.map_path, "r", encoding="utf-8") as file_obj:
                self.map = json.load(file_obj)
            if not isinstance(self.map, dict):
                self.map = {}
        except (json.JSONDecodeError, OSError):
            self.map = {}
            with open(self.map_path, "w", encoding="utf-8") as file_obj:
                json.dump(self.map, file_obj, ensure_ascii=False, indent=4)

        print(f"Loaded semantic map with {len(self.map)} entries from {self.map_path}.")

    def memory(self, key, value):
        self.map[key] = value
        with open(self.map_path, "w", encoding="utf-8") as file_obj:
            json.dump(self.map, file_obj, ensure_ascii=False, indent=4)

    def get(self, key):
        return self.map.get(key, None)
