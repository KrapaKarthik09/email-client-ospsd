from setuptools import setup, find_packages

setup(
    name="my-inbox-impl",
    version="0.1.0",
    description="Implementation of the my-inbox-api interface",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "my-inbox-api",
    ],
    python_requires=">=3.12",
)
