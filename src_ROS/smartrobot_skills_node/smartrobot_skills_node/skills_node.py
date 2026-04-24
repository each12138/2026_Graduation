from .skill_executor import SkillExecutor


class SkillsNode:
    """Execution node boundary: action packet -> execution result."""

    def __init__(self, place_memory, state_reader):
        self.executor = SkillExecutor(
            place_memory=place_memory,
            state_reader=state_reader,
        )

    @property
    def skill_registry(self):
        return self.executor.skill_registry

    def run_action(self, action_packet):
        return self.executor.execute(action_packet)
