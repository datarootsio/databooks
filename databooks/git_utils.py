"""Git helper functions."""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union, cast, overload

from git import Git
from git.diff import DiffIndex
from git.objects.blob import Blob
from git.objects.commit import Commit
from git.objects.tree import Tree
from git.repo import Repo

from databooks.common import find_common_parent, find_obj
from databooks.logging import get_logger, set_verbose

logger = get_logger(name=__file__)

# https://github.com/python/mypy/issues/5317
ChangeType = Enum("ChangeType", [*DiffIndex.change_type, "U"])  # type: ignore[misc]


@dataclass
class UnmergedBlob:
    """Container for git unmerged blobs."""

    filename: Path
    stage: Dict[int, Blob]


@dataclass
class ConflictFile:
    """Container for path and different versions of conflicted notebooks."""

    filename: Path
    first_log: str
    last_log: str
    first_contents: str
    last_contents: str


@dataclass
class Contents:
    """Container for path of file versions."""

    path: Optional[Path]
    contents: Optional[str]


@dataclass
class DiffContents:
    """Container for path and different versions of conflicted notebooks."""

    a: Contents
    b: Contents
    change_type: ChangeType


@overload
def blob2str(blob: None) -> None:
    ...


@overload
def blob2str(blob: Blob) -> str:
    ...


def blob2str(blob: Optional[Blob]) -> Optional[str]:
    """Get the blob contents if they exist (otherwise return `None`)."""
    return blob.data_stream.read() if blob is not None else None


def blob2commit(blob: Blob, repo: Repo) -> str:
    """Get the short commit message from blob hash."""
    _git = Git(working_dir=repo.working_dir)
    commit_id = _git.log(find_object=blob, max_count=1, all=True, oneline=True)
    return (
        commit_id
        if len(commit_id) > 0
        else _git.stash("list", "--oneline", "--max-count", "1", "--find-object", blob)
    )


def diff2contents(
    blob: Blob,
    ref: Optional[Union[Tree, Commit, str]],
    path: Path,
    not_exists: bool = False,
) -> Optional[str]:
    """
    Get the blob contents from the diff.

    Depends on whether we are diffing against current working tree and if object exists
     at diff time (added or deleted objects only exist at one side). If comparing
     against working tree (`ref=None`) we return the current file contents.
    :param blob: git diff blob
    :param ref: git reference
    :param path: path to object
    :param not_exists: whether object exists at 'diff time' (added or removed objects
     do not exist)
    :return: blob contents as a string (if exists)
    """
    if not_exists:
        return None
    elif ref is None:
        return path.read_text()
    else:
        return blob2str(blob)


def get_repo(path: Path) -> Optional[Repo]:
    """Find git repo in current or parent directories."""
    repo_dir = find_obj(
        obj_name=".git", start=Path(path.anchor), finish=path, is_dir=True
    )
    if repo_dir is not None:
        repo = Repo(path=repo_dir)
        logger.debug(f"Repo found at: {repo.working_dir}.")
        return repo
    else:
        logger.debug(f"No repo found at {path}.")
        return None


def get_conflict_blobs(repo: Repo) -> List[ConflictFile]:
    """Get the source files for conflicts."""
    unmerged_blobs = repo.index.unmerged_blobs()
    blobs = (
        UnmergedBlob(filename=Path(k), stage=dict(v))
        for k, v in unmerged_blobs.items()
        if 0 not in dict(v).keys()  # only get blobs that could not be merged
    )

    if not isinstance(repo.working_dir, (Path, str)):
        raise RuntimeError(
            "Expected `repo` to be `pathlib.Path` or `str`, got"
            f" {type(repo.working_dir)}."
        )
    return [
        ConflictFile(
            filename=repo.working_dir / blob.filename,
            first_log=blob2commit(blob=blob.stage[2], repo=repo),
            last_log=blob2commit(blob=blob.stage[3], repo=repo),
            first_contents=blob2str(blob.stage[2]),
            last_contents=blob2str(blob.stage[3]),
        )
        for blob in blobs
    ]


def get_nb_diffs(
    ref_base: Optional[str] = None,
    ref_remote: Optional[str] = None,
    paths: Sequence[Path] = (),
    *,
    repo: Optional[Repo] = None,
    verbose: bool = False,
) -> List[DiffContents]:
    """
    Get the noteebook(s) git diff(s).

    By default, diffs are compared with the current working direcotory. That is, staged
     files will still show up in the diffs. Only return the diffs for notebook files.
    """
    if verbose:
        set_verbose(logger)

    common_path = find_common_parent(paths or [Path.cwd()])
    repo = get_repo(path=common_path) if repo is None else repo
    if repo is None or repo.working_dir is None:
        raise ValueError("No repo found - cannot compute diffs.")

    ref_base = repo.index if ref_base is None else repo.tree(ref_base)
    ref_remote = ref_remote if ref_remote is None else repo.tree(ref_remote)

    logger.debug(
        f"Looking for diffs on path(s) {[p.resolve() for p in paths]}.\n"
        f"Comparing `{ref_base}` and `{ref_remote}`."
    )
    repo_root_dir = Path(repo.working_dir)
    return [
        DiffContents(
            a=Contents(
                path=Path(d.a_path),
                contents=diff2contents(
                    blob=cast(Blob, d.a_blob),
                    ref=ref_base,
                    path=repo_root_dir / d.a_path,
                    not_exists=d.change_type is ChangeType.A,  # type: ignore
                ),
            ),
            b=Contents(
                path=Path(d.b_path),
                contents=diff2contents(
                    blob=cast(Blob, d.b_blob),
                    ref=ref_remote,
                    path=repo_root_dir / d.b_path,
                    not_exists=d.change_type is ChangeType.D,  # type: ignore
                ),
            ),
            change_type=ChangeType[d.change_type],
        )
        for d in ref_base.diff(
            other=ref_remote, paths=list(paths) or list(repo_root_dir.rglob("*.ipynb"))
        )
    ]
