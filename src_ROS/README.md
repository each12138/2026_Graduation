# src_ROS

Refactored ROS-style workspace for the runtime chain:

1. `smartrobot_voice_node`: user speech/text input boundary.
2. `smartrobot_agent_node`: LLM ReAct decision boundary.
3. `smartrobot_skills_node`: action execution boundary.
4. `smartrobot_state_client`: state reading library from `rt/sportmodestate`.
5. `smartrobot_place_memory`: persistent named place memory.
6. `smartrobot_bringup`: end-to-end pipeline wiring and launch.

Main flow: `voice -> agent -> skills`.
