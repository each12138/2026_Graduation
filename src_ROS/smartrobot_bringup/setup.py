from glob import glob

from setuptools import find_packages, setup

package_name = "smartrobot_bringup"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="dev",
    maintainer_email="dev@example.com",
    description="SmartRobot 的流程编排启动包。",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "smartrobot_pipeline = smartrobot_bringup.pipeline:main",
        ],
    },
)
