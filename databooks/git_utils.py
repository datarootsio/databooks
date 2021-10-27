from git import Repo, InvalidGitRepositoryError
from pathlib import Path
from .common import FilePath, get_logger

logger = get_logger(name=__file__)

def get_repo(path: FilePath = None):
    """Find git repo in current or parent directories"""
    if path is None:
        path = Path.cwd()
    logger.info(path)
    try:
        return Repo(path)
    except InvalidGitRepositoryError:
        return get_repo(path.parent)
