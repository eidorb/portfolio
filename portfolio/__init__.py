__version__ = "0.1.0"


import subprocess
from re import sub


def create_mamba_environment() -> subprocess.CompletedProcess:
    """Creates Mamba environment from environment file."""
    return subprocess.run("micromamba create --file environment.yml --yes".split())


def install_dependencies() -> subprocess.CompletedProcess:
    """Installs Python dependencies."""
    return subprocess.run("micromamba run --name portfolio poetry install".split())
