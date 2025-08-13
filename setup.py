from setuptools import setup, find_packages

setup(
    name="tfm",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    author="Germán Fros",
    description="Proyecto TFM",
    python_requires=">=3.8",
)