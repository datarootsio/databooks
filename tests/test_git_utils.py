from pathlib import Path, PosixPath

from git import GitCommandError, Repo
from pytest import raises
from pytest_git import GitRepo

from databooks.git_utils import ConflictFile, get_conflict_blobs, get_repo


def init_repo_conflicts(
    git_repo: GitRepo,
    filename: Path,
    contents_main: str,
    contents_other: str,
    commit_message_main: str,
    commit_message_other: str,
) -> GitRepo:
    """Create git repo and create a conflict"""
    git_filepath = git_repo.workspace / filename

    git_repo.run("git checkout -b main")
    git_repo.run("git commit --allow-empty -m 'Initial commit'")

    git_repo.run("git checkout -b other")
    git_filepath.write_text(contents_other)
    git_repo.run(f"git add {filename}")
    git_repo.run(f"git commit -m '{commit_message_other}'")

    git_repo.run("git checkout main")
    git_filepath.write_text(contents_main)
    git_repo.run(f"git add {filename}")
    git_repo.run(f"git commit -m '{commit_message_main}'")

    with raises(GitCommandError):
        git_repo.api.git.merge("other")  # merge fails and raises error due to conflict

    return git_repo


def test_get_repo() -> None:
    """Find git repository"""
    filepath = Path(__file__)
    repo = get_repo(filepath)
    assert repo.working_dir is not None
    assert isinstance(repo, Repo)
    assert Path(repo.working_dir).stem == "databooks"


def test_get_conflict_blobs(git_repo: GitRepo) -> None:
    """Return `databooks.git_utils.ConflctFile` from git merge conflict"""
    filename = "hello.txt"
    git_repo = init_repo_conflicts(
        git_repo=git_repo,
        filename=filename,
        contents_main="HELLO EVERYONE!",
        contents_other="hello world",
        commit_message_main="Commit message from main",
        commit_message_other="Commit message from other",
    )
    conflicts = list(get_conflict_blobs(repo=git_repo.api))
    assert len(conflicts) == 1

    conflict = conflicts[0]
    assert isinstance(conflict, ConflictFile)
    assert conflict.filename == PosixPath(filename)

    # Git logs start with git has, which won't match
    assert conflict.first_log.endswith("Commit message from main")
    assert conflict.last_log.endswith("Commit message from other")

    assert conflict.first_contents == "HELLO EVERYONE!"
    assert conflict.last_contents == "hello world"
