from skills.skill_manager import SkillManager

from unitree_sdk2py.go2.sport.sport_client import SportClient

class SkillExecutor:
    def __init__(self, semantic_map=None, state_client=None):
        """
        初始化SportClient、状态获取和技能注册表。
        """
        self.sport_client = SportClient()
        self.sport_client.SetTimeout(10.0)
        self.sport_client.Init()

        self.skills_manager = SkillManager(
            self.sport_client,
            semantic_map=semantic_map,
            state_client=state_client,
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
            "go_to": self.skills_manager.go_to,
            "patrol": self.skills_manager.patrol
        }

    def execute(self, skill_name: str, params: dict = None):
        """
        执行指定的技能。

        :param skill_name: 要执行的技能名称。
        :param params: 技能需要的参数字典。
        """
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
        except TypeError as e:
            print(f"技能 '{skill_name}' 参数错误: {e}")
            return {"success": False, "error": "invalid_skill_args", "detail": str(e)}
        except Exception as e:
            print(f"执行技能 '{skill_name}' 时发生错误: {e}")
            return {"success": False, "error": str(e)}
