from re import sub
import subprocess


def create_mamba_environment() -> subprocess.CompletedProcess:
    """Creates Mamba environment from environment file."""
    return subprocess.run("micromamba create --file environment.yml --yes".split())


def install_dependencies() -> subprocess.CompletedProcess:
    """Installs Python dependencies."""
    return subprocess.run("micromamba run --name portfolio poetry install".split())
