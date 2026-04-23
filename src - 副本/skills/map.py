import json
import os


class SemanticMap:
    def __init__(self, map_file="map.json"):
        # 加载或创建语义地图文件
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.map_path = os.path.join(script_dir, map_file)
        self.map = {}

        # 如果文件不存在，创建一个空的JSON文件
        if not os.path.exists(self.map_path):
            with open(self.map_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)

        # 加载现有的地图数据
        try:
            with open(self.map_path, "r", encoding="utf-8") as f:
                self.map = json.load(f)
            if not isinstance(self.map, dict):
                self.map = {}
        except (json.JSONDecodeError, OSError):
            self.map = {}
            with open(self.map_path, "w", encoding="utf-8") as f:
                json.dump(self.map, f, ensure_ascii=False, indent=4)

        print(f"Loaded semantic map with {len(self.map)} entries.")

    def memory(self, key, value):
        self.map[key] = value
        with open(self.map_path, "w", encoding="utf-8") as f:
            json.dump(self.map, f, ensure_ascii=False, indent=4)

    def get(self, key):
        return self.map.get(key, None)
