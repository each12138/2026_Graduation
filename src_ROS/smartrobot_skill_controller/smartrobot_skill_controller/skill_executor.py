from unitree_sdk2py.go2.sport.sport_client import SportClient

from .skill_manager import SkillManager


class SkillExecutor:
    def __init__(self, place_memory, state_reader):
        self.sport_client = SportClient()
        self.sport_client.SetTimeout(10.0)
        self.sport_client.Init()

        self.manager = SkillManager(
            sport_client=self.sport_client,
            place_memory=place_memory,
            state_reader=state_reader,
        )

        self.skill_registry = {
            "stand_up": self.manager.stand_up,
            "stand_down": self.manager.stand_down,
            "move_forward": self.manager.move_forward,
            "move_lateral": self.manager.move_lateral,
            "move_rotate": self.manager.move_rotate,
            "sit_down": self.manager.sit_down,
            "hello": self.manager.hello,
            "stretch": self.manager.stretch,
            "wallow": self.manager.wallow,
            "scrape": self.manager.scrape,
            "front_jump": self.manager.front_jump,
            "hand_stand": self.manager.hand_stand,
            "memory_position": self.manager.memory_position,
            "go_to": self.manager.go_to,
            # "patrol": self.manager.patrol,
        }

    def execute(self, action_packet):
        action = action_packet.get("action")
        params = action_packet.get("params", {})

        if not isinstance(action, str) or not action.strip():
            return {"success": False, "error": "invalid_action_name"}
        action = action.strip()
        if action not in self.skill_registry:
            return {"success": False, "error": f"skill_not_found:{action}"}
        if not isinstance(params, dict):
            return {"success": False, "error": "invalid_params"}

        try:
            result = self.skill_registry[action](**params)
            if isinstance(result, dict):
                return result
            return {"success": True, "data": result}
        except TypeError as err:
            return {"success": False, "error": "invalid_skill_args", "detail": str(err)}
        except Exception as err:
            return {"success": False, "error": str(err)}
