from pathlib import Path

from git import Repo

from databooks.git_utils import get_repo


def test_get_repo():
    """Find git repository"""
    repo = get_repo(__file__)
    assert isinstance(repo, Repo)
    assert Path(repo.working_dir).stem == "databooks"
