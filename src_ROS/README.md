# src_ROS

Refactored ROS-style workspace for the runtime chain:

1. `smartrobot_voice_node`: user speech/text input boundary.
2. `smartrobot_agent_node`: LLM ReAct decision boundary.
3. `smartrobot_skills_node`: action execution boundary.
4. `smartrobot_state_client`: state reading library from global pose topic (default `/amcl_pose`).
5. `smartrobot_place_memory`: persistent named place memory.
6. `smartrobot_bringup`: end-to-end pipeline wiring and launch.

Main flow: `voice -> agent -> skills`.

## Global Place Memory (map frame)

To make saved places reusable over time ("go back to Location 1"), place memory should store poses in the global `map` frame.

`smartrobot_state_client` now reads pose only from ROS2 global pose topic (default: `/amcl_pose`).

Recommended environment variables:

```bash
export GO2_NAV_FRAME=map
export GO2_GLOBAL_POSE_ENABLE=1
export GO2_GLOBAL_POSE_TOPIC=/amcl_pose
export GO2_GLOBAL_POSE_TIMEOUT=2.0
```

If `/amcl_pose` is unavailable, `StateReader.get_state()` returns `None`, and `memory_position` will report `state_unavailable`.
