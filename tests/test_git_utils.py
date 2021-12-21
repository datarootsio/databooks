from pathlib import Path
from typing import cast

from git import GitCommandError, Repo
from py._path.local import LocalPath
from pytest import raises

from databooks.git_utils import ConflictFile, get_conflict_blobs, get_repo


def init_repo_conflicts(
    tmpdir: LocalPath,
    filename: Path,
    contents_main: str,
    contents_other: str,
    commit_message_main: str,
    commit_message_other: str,
) -> Repo:
    """Create git repo and create a conflict."""
    git_repo = Repo.init(path=tmpdir)
    git_repo.working_dir = cast(Path, git_repo.working_dir)
    git_filepath = git_repo.working_dir / filename

    git_repo.git.checkout("-b", "main")
    git_repo.git.commit("--allow-empty", "-m", "Initial commit")

    git_repo.git.checkout("-b", "other")
    git_filepath.parent.mkdir(parents=True, exist_ok=True)
    with git_filepath.open("w") as f:
        f.write(contents_other)
    git_repo.git.add(filename)
    git_repo.git.commit("-m", commit_message_other)

    git_repo.git.checkout("main")
    git_filepath.parent.mkdir(parents=True, exist_ok=True)
    with git_filepath.open("w") as f:
        f.write(contents_main)
    git_repo.git.add(filename)
    git_repo.git.commit("-m", commit_message_main)

    with raises(GitCommandError):
        git_repo.git.merge("other")  # merge fails and raises error due to conflict

    return git_repo


def test_get_repo() -> None:
    """Find git repository."""
    filepath = Path(__file__)
    repo = get_repo(filepath)
    assert repo.working_dir is not None
    assert isinstance(repo, Repo)
    assert Path(repo.working_dir).stem == "databooks"


def test_get_conflict_blobs(tmpdir: LocalPath) -> None:
    """Return `databooks.git_utils.ConflctFile` from git merge conflict."""
    filepath = Path("hello.txt")
    git_repo = init_repo_conflicts(
        tmpdir=tmpdir,
        filename=filepath,
        contents_main="HELLO EVERYONE!",
        contents_other="hello world",
        commit_message_main="Commit message from main",
        commit_message_other="Commit message from other",
    )
    git_repo.working_dir = cast(Path, git_repo.working_dir)
    conflicts = get_conflict_blobs(repo=git_repo)
    assert len(conflicts) == 1

    conflict = conflicts[0]
    assert isinstance(conflict, ConflictFile)
    assert conflict.filename == (git_repo.working_dir / filepath)

    # Git logs start with git has, which won't match
    assert conflict.first_log.endswith("Commit message from main")
    assert conflict.last_log.endswith("Commit message from other")

    assert conflict.first_contents == "HELLO EVERYONE!"
    assert conflict.last_contents == "hello world"
