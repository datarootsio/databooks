"""Git helper functions"""
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from git import Blob, Git, Repo  # type: ignore
from pydantic import FilePath

from databooks.common import get_logger

logger = get_logger(name=__file__)


@dataclass
class UnmergedBlob:
    filename: Path
    stage: dict[int, Blob]


@dataclass
class ConflictFile:
    filename: Path
    first_log: str
    last_log: str
    first_contents: str
    last_contents: str


def get_repo(path: FilePath = Path.cwd()) -> Repo:
    """Find git repo in current or parent directories"""
    repo = Repo(path=path, search_parent_directories=True)
    logger.info(f"Repo found at: {repo.working_dir}")
    return repo


def blob2commit(blob: Blob, repo: Repo = get_repo()) -> str:
    """Get the short commit message from blob hash"""
    _git = Git(working_dir=repo.working_dir)
    commit_id = _git.log(find_object=blob, max_count=1, all=True, oneline=True)
    return (
        commit_id
        if len(commit_id) > 0
        else _git.stash("list", "--oneline", "--max-count", "1", "--find-object", blob)
    )


def get_conflict_blobs(repo: Repo = get_repo()) -> Generator[ConflictFile, None, None]:
    """Get the source files for conflicts"""
    unmerged_blobs = repo.index.unmerged_blobs()
    blobs = (
        UnmergedBlob(filename=Path(k), stage=dict(v))
        for k, v in unmerged_blobs.items()
        if 0 not in dict(v).keys()  # only get blobs that could not be merged
    )
    return (
        ConflictFile(
            filename=blob.filename,
            first_log=blob2commit(blob=blob.stage[2], repo=repo),
            last_log=blob2commit(blob=blob.stage[3], repo=repo),
            first_contents=repo.git.show(blob.stage[2]),
            last_contents=repo.git.show(blob.stage[3]),
        )
        for blob in blobs
    )
