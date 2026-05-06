from setuptools import setup
from glob import glob
import os

package_name = "quadruped_llm_system"

setup(
    name=package_name,
    version="0.1.0",
    packages=[
        package_name,
        f"{package_name}.common",
        f"{package_name}.cognition",
        f"{package_name}.execution",
        f"{package_name}.interaction",
        f"{package_name}.robot_interface",
    ],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.py")),
        (f"share/{package_name}/config", glob("config/*")),
    ],
    install_requires=["setuptools", "pyyaml", "requests"],
    zip_safe=True,
    maintainer="you",
    maintainer_email="you@example.com",
    description="Embodied LLM system for quadruped robots.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "text_input_node = quadruped_llm_system.interaction.text_input_node:main",
            "response_generator_node = quadruped_llm_system.interaction.response_generator_node:main",
            "dialogue_router_node = quadruped_llm_system.cognition.dialogue_router_node:main",
            "nav_controller_node = quadruped_llm_system.execution.nav_controller_node:main",
            "speaker_bridge_node = quadruped_llm_system.robot_interface.speaker_bridge_node:main",
            "nav_goal_relay_node = quadruped_llm_system.robot_interface.nav_goal_relay_node:main",
        ],
    },
)
