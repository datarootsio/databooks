from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from git import Blob, Git, Repo  # type: ignore
from pydantic import FilePath

from databooks.common import get_logger

logger = get_logger(name=__file__)


@dataclass
class UnmergedBlob:
    filename: str
    stage: dict[int, Blob]  # see


@dataclass
class ConflictFile:
    filename: str
    hash_id: str
    contents: str


def get_repo(path: FilePath = Path.cwd()) -> Repo:
    """Find git repo in current or parent directories"""
    repo = Repo(path=path, search_parent_directories=True)
    logger.info(f"Repo found at: {repo.working_dir}")
    return repo


def blob2commit(blob: Blob, repo: Repo = get_repo()) -> str:
    """Get the short commit message from blob hash"""
    # TODO: change logic if conflict comes from stash?
    # https://stackoverflow.com/questions/64617225/git-get-hash-of-unmerged-files
    _git = Git(working_dir=repo.working_dir)
    return _git.log(find_object=blob, max_count=1, all=True, oneline=True)


def get_conflict_blobs(repo: Repo = get_repo()) -> Generator[ConflictFile, None, None]:
    unmerged_blobs = repo.index.unmerged_blobs()
    blobs = (
        UnmergedBlob(filename=str(k), stage=dict(v)) for k, v in unmerged_blobs.items()
    )
    return (
        ConflictFile(
            filename=blob.filename,
            hash_id=blob2commit(blob=blob.stage[i], repo=repo),
            contents=repo.git.show(blob.stage[i]),
        )
        for blob in blobs
        for i in (1, 2)
    )
