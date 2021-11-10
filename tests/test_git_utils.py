from pathlib import Path

from git import Repo

from databooks.git_utils import get_repo


def test_get_repo() -> None:
    """Find git repository"""
    repo = get_repo(__file__)
    assert repo.working_dir is not None
    assert isinstance(repo, Repo)
    assert Path(repo.working_dir).stem == "databooks"
