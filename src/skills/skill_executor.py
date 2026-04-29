from skills.skill_manager import SkillManager


class SkillExecutor:
    def __init__(self, sport_client, semantic_map=None, state_reader=None):
        if sport_client is None:
            raise ValueError("sport_client is required")

        self.sport_client = sport_client
        self.skills_manager = SkillManager(
            sport_client=self.sport_client,
            semantic_map=semantic_map,
            state_reader=state_reader,
        )

        self.skill_registry = {
            "stand_up": self.skills_manager.stand_up,
            "stand_down": self.skills_manager.stand_down,
            "move_forward": self.skills_manager.move_forward,
            "move_lateral": self.skills_manager.move_lateral,
            "move_rotate": self.skills_manager.move_rotate,
            "sit_down": self.skills_manager.sit_down,
            "hello": self.skills_manager.hello,
            "stretch": self.skills_manager.stretch,
            "wallow": self.skills_manager.wallow,
            "scrape": self.skills_manager.scrape,
            "front_jump": self.skills_manager.front_jump,
            "hand_stand": self.skills_manager.hand_stand,
            "memory_position": self.skills_manager.memory_position,
            "navigate": self.skills_manager.navigate,
        }

    def execute(self, skill_name: str, params: dict = None):
        if not isinstance(skill_name, str) or not skill_name.strip():
            print("技能名为空或类型错误")
            return {"success": False, "error": "invalid_skill_name"}

        skill_name = skill_name.strip()
        if skill_name not in self.skill_registry:
            print(f"技能 '{skill_name}' 不存在")
            return {"success": False, "error": f"技能 '{skill_name}' 不存在"}

        skill_func = self.skill_registry[skill_name]
        try:
            if params is None:
                params = {}
            if not isinstance(params, dict):
                print(f"技能 '{skill_name}' 参数必须为字典")
                return {"success": False, "error": "invalid_params"}
            result = skill_func(**params)
            if isinstance(result, dict):
                return result
            return {"success": True, "data": result}
        except TypeError as exc:
            print(f"技能 '{skill_name}' 参数错误: {exc}")
            return {"success": False, "error": "invalid_skill_args", "detail": str(exc)}
        except Exception as exc:
            print(f"执行技能 '{skill_name}' 时发生错误: {exc}")
            return {"success": False, "error": str(exc)}
