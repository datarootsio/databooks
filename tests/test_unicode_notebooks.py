"""Read and write UTF-8 notebooks independently of the system encoding."""
import json
from pathlib import Path

from databooks import JupyterNotebook
from databooks.git_utils import get_nb_diffs
from tests.test_git_utils import init_repo_diff


def notebook_json(source: str) -> str:
    """Return a small notebook with unescaped Unicode source."""
    return json.dumps(
        {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {},
            "cells": [{"cell_type": "markdown", "metadata": {}, "source": source}],
        },
        ensure_ascii=False,
    )


def test_parse_utf8_notebook(tmp_path: Path) -> None:
    """Read the Unicode text stored in a normal Jupyter notebook."""
    path = tmp_path / "unicode.ipynb"
    path.write_text(notebook_json("Hello 世界 🚀"), encoding="utf-8")

    notebook = JupyterNotebook.parse_file(path)

    assert notebook.cells[0].source == "Hello 世界 🚀"


def test_write_utf8_notebook(tmp_path: Path) -> None:
    """Write unescaped notebook text as UTF-8, not the locale encoding."""
    path = tmp_path / "unicode.ipynb"
    notebook = JupyterNotebook.model_validate_json(notebook_json("Hello 世界 🚀"))

    notebook.write(path, ensure_ascii=False)

    assert json.loads(path.read_text(encoding="utf-8"))["cells"][0]["source"] == (
        "Hello 世界 🚀"
    )


def test_diff_utf8_working_tree(tmp_path: Path) -> None:
    """Read Unicode notebook changes from the working tree."""
    filename = Path("unicode.ipynb")
    repo = init_repo_diff(
        tmp_path=tmp_path,
        filename=filename,
        contents_main=notebook_json("original"),
        contents_other=notebook_json("other"),
        commit_message_main="Original notebook",
        commit_message_other="Other notebook",
    )
    contents = notebook_json("Hello 世界 🚀")
    (tmp_path / filename).write_text(contents, encoding="utf-8")

    diffs = get_nb_diffs(repo=repo)

    assert len(diffs) == 1
    assert diffs[0].b.contents == contents
