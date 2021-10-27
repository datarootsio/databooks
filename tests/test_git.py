from databooks.git_utils import get_repo
from pathlib import Path
from git import Repo

def test_get_repo():
    path = Path(__file__)
    repo = get_repo(path)
    assert isinstance(repo, Repo)
    assert Path(repo.working_dir).stem == "databooks"