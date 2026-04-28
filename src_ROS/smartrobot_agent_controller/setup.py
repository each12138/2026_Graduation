from setuptools import find_packages, setup

package_name = "smartrobot_agent_controller"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="dev",
    maintainer_email="dev@example.com",
    description="SmartRobot 的智能体和 LLM 决策包。",
    license="MIT",
    tests_require=["pytest"],
)
