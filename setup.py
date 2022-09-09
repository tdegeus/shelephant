from pathlib import Path

from setuptools import find_packages
from setuptools import setup

project_name = "shelephant"

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name=project_name,
    license="MIT",
    author="Tom de Geus",
    author_email="tom@geus.me",
    description="YAML based shell commands",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="YAML, Bash",
    url=f"https://github.com/tdegeus/{project_name:s}",
    packages=find_packages(),
    use_scm_version={"write_to": f"{project_name}/_version.py"},
    setup_requires=["setuptools_scm"],
    install_requires=["click", "pyyaml", "mergedeep", "numpy", "prettytable", "termcolor"],
    entry_points={
        "console_scripts": [
            f"shelephant_checksum = {project_name}.cli.shelephant_checksum:main",
            f"shelephant_cp = {project_name}.cli.shelephant_cp:main",
            f"shelephant_diff = {project_name}:_shelephant_diff_catch",
            f"shelephant_dump = {project_name}.cli.shelephant_dump:main",
            f"shelephant_extract = {project_name}.cli.shelephant_extract:main",
            f"shelephant_get = {project_name}.cli.shelephant_get:main",
            f"shelephant_hostinfo = {project_name}.cli.shelephant_hostinfo:main",
            f"shelephant_merge = {project_name}.cli.shelephant_merge:main",
            f"shelephant_mv = {project_name}.cli.shelephant_mv:main",
            f"shelephant_parse = {project_name}.cli.shelephant_parse:main",
            f"shelephant_rm = {project_name}.cli.shelephant_rm:main",
            f"shelephant_send = {project_name}.cli.shelephant_send:main",
        ]
    },
)
