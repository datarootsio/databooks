from pathlib import Path

from git import Repo

from .common import FilePath, get_logger

logger = get_logger(name=__file__)


def get_repo(path: FilePath = None) -> Repo:
    """Find git repo in current or parent directories"""
    if path is None:
        path = Path.cwd()
    repo = Repo(path=path, search_parent_directories=True)
    logger.info(f"Repo found at: {repo.working_dir}")
    return repo
