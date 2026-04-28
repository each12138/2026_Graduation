from setuptools import find_packages, setup

package_name = "smartrobot_voice_input"

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
    description="SmartRobot 的语音和文本输入包。",
    license="MIT",
    tests_require=["pytest"],
)
