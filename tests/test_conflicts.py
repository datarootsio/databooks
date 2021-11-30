from pathlib import Path, PosixPath

from pytest_git import GitRepo

from databooks.conflicts import DiffFile, path2diff
from databooks.data_models.notebook import Cell, CellMetadata, NotebookMetadata
from tests.test_data_models.test_notebook import TestJupyterNotebook
from tests.test_git_utils import init_repo_conflicts


def test_path2diff(git_repo: GitRepo) -> None:
    """Return a DiffFile based on a path and git conflicts"""
    notebook_main = TestJupyterNotebook().jupyter_notebook
    notebook_other = TestJupyterNotebook().jupyter_notebook

    notebook_main.metadata = NotebookMetadata(
        kernelspec=dict(
            display_name="different_kernel_display_name", name="kernel_name"
        ),
        field_to_remove=["Field to remove"],
        another_field_to_remove="another field",
    )
    extra_cell = Cell(
        cell_type="raw",
        metadata=CellMetadata(random_meta=["meta"]),
        source="extra",
    )
    notebook_other.cells = notebook_other.cells + [extra_cell]

    nb_filepath = Path("test_notebook.ipynb")

    git_repo = init_repo_conflicts(
        git_repo=git_repo,
        filename=nb_filepath,
        contents_main=notebook_main.json(),
        contents_other=notebook_other.json(),
        commit_message_main="Commit message from main",
        commit_message_other="Commit message from other",
    )

    diff_files = list(path2diff(nb_path=nb_filepath, repo=git_repo.api))

    assert len(diff_files) == 1

    diff_file = diff_files[0]
    assert isinstance(diff_file, DiffFile)
    assert diff_file.filename == PosixPath(nb_filepath)
    assert diff_file.diff_notebook == notebook_main - notebook_other

    # We use git logs for ids, which start with a hash that won't match
    assert diff_file.first_id.endswith("Commit message from main")
    assert diff_file.last_id.endswith("Commit message from other")
