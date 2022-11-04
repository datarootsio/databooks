import logging
from copy import deepcopy
from importlib import resources
from pathlib import Path
from textwrap import dedent

from _pytest.logging import LogCaptureFixture
from typer import Context
from typer.core import TyperCommand
from typer.testing import CliRunner

from databooks.cli import _config_callback, app
from databooks.data_models.cell import BaseCell, CellMetadata, CellOutputs
from databooks.data_models.notebook import JupyterNotebook, NotebookMetadata
from databooks.git_utils import get_conflict_blobs
from databooks.version import __version__
from tests.test_data_models.test_notebook import TestJupyterNotebook
from tests.test_git_utils import init_repo_conflicts

runner = CliRunner()


def test_version_callback() -> None:
    """Print version and help."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"databooks version: {__version__}\n" == result.stdout


def test_config_callback() -> None:
    """Overwrite default parameters from `typer.Context`."""
    ctx: Context = Context(TyperCommand(name="test-config"))
    with resources.path("tests.files", "pyproject.toml") as conf:
        assert ctx.default_map is None
        parsed_config = _config_callback(ctx=ctx, config_path=conf)
        assert ctx.default_map == dict(config_default="config-value")
        assert parsed_config == conf


def test_meta(tmp_path: Path) -> None:
    """Remove notebook metadata."""
    read_path = tmp_path / "test_meta_nb.ipynb"  # type: ignore
    TestJupyterNotebook().jupyter_notebook.write(read_path)

    nb_read = JupyterNotebook.parse_file(path=read_path)
    result = runner.invoke(app, ["meta", str(read_path), "--yes"])
    nb_write = JupyterNotebook.parse_file(path=read_path)

    assert result.exit_code == 0
    assert len(nb_write.cells) == len(nb_read.cells)
    assert all(cell.metadata == CellMetadata() for cell in nb_write.cells)
    assert all(
        cell.execution_count is None
        for cell in nb_write.cells
        if cell.cell_type == "code"
    )
    assert all(
        not hasattr(cell, "outputs")
        for cell in nb_write.cells
        if cell.cell_type != "code"
    )
    assert all(
        not hasattr(cell, "execution_count")
        for cell in nb_write.cells
        if cell.cell_type != "code"
    )


def test_meta__check(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    """Report on existing notebook metadata (both when it is and isn't present)."""
    caplog.set_level(logging.INFO)

    read_path = tmp_path / "test_meta_nb.ipynb"  # type: ignore
    TestJupyterNotebook().jupyter_notebook.write(read_path)

    nb_read = JupyterNotebook.parse_file(path=read_path)
    result = runner.invoke(app, ["meta", str(read_path), "--check"])
    nb_write = JupyterNotebook.parse_file(path=read_path)

    logs = list(caplog.records)
    assert result.exit_code == 1
    assert len(logs) == 1
    assert nb_read == nb_write
    assert logs[0].message == "Found unwanted metadata in 1 out of 1 files."

    # Clean notebook and check again
    runner.invoke(app, ["meta", str(read_path), "--yes"])
    result = runner.invoke(app, ["meta", str(read_path), "--check"])

    logs = list(caplog.records)
    assert result.exit_code == 0
    assert len(logs) == 4
    assert logs[-1].message == "No unwanted metadata!"


def test_meta__config(tmp_path: Path) -> None:
    """Check notebook metadata with configuration overriding defaults."""
    read_path = tmp_path / "test_meta_nb.ipynb"  # type: ignore
    TestJupyterNotebook().jupyter_notebook.write(read_path)

    nb_read = JupyterNotebook.parse_file(path=read_path)
    with resources.path("tests.files", "pyproject.toml") as config_path:
        # Take arguments from config file
        result = runner.invoke(
            app, ["meta", str(read_path), "--config", str(config_path)]
        )
    nb_write = JupyterNotebook.parse_file(path=read_path)

    assert result.exit_code == 0
    assert nb_read != nb_write, "Notebook was not overwritten"
    assert all(
        c.outputs
        == CellOutputs(
            __root__=[
                {"name": "stdout", "output_type": "stream", "text": ["test text\n"]}
            ]
        )
        for c in nb_write.cells
    )
    assert all(c.execution_count is not None for c in nb_write.cells)

    # Override config file arguments
    result = runner.invoke(
        app, ["meta", str(read_path), "--rm-exec", "--config", str(config_path)]
    )
    nb_write = JupyterNotebook.parse_file(path=read_path)

    assert result.exit_code == 0
    assert all(c.execution_count is None for c in nb_write.cells)


def test_meta__script(tmp_path: Path) -> None:
    """Raise `typer.BadParameter` when passing a script instead of a notebook."""
    py_path = tmp_path / "a_script.py"  # type: ignore
    py_path.write_text("# some python code", encoding="utf-8")

    result = runner.invoke(app, ["meta", str(py_path)])
    assert result.exit_code == 2
    assert (
        "Expected either notebook files, a directory or glob expression."
        in result.output
    )


def test_meta__no_confirm(tmp_path: Path) -> None:
    """Don't make any changes without confirmation to overwrite files (prompt)."""
    nb_path = tmp_path / "test_meta_nb.ipynb"  # type: ignore
    TestJupyterNotebook().jupyter_notebook.write(nb_path)

    result = runner.invoke(app, ["meta", str(nb_path)])

    assert result.exit_code == 1
    assert JupyterNotebook.parse_file(nb_path) == TestJupyterNotebook().jupyter_notebook
    assert result.output == (
        "1 files will be overwritten (no prefix nor suffix was passed)."
        " Continue? [y/n]: \nAborted!\n"
    )


def test_meta__confirm(tmp_path: Path) -> None:
    """Make changes when confirming overwrite via the prompt."""
    nb_path = tmp_path / "test_meta_nb.ipynb"  # type: ignore
    TestJupyterNotebook().jupyter_notebook.write(nb_path)

    result = runner.invoke(app, ["meta", str(nb_path)], input="y")

    assert result.exit_code == 0
    assert JupyterNotebook.parse_file(nb_path) != TestJupyterNotebook().jupyter_notebook
    assert result.output == (
        "1 files will be overwritten (no prefix nor suffix was passed)."
        " Continue? [y/n]:"
        "   Removing metadata ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00\n"
    )


def test_meta__no_notebooks_found(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    """Log that no notebook was found in the paths passed."""
    caplog.set_level(logging.INFO)
    nb_path = tmp_path / "inexistent_nb.ipynb"  # type: ignore

    result = runner.invoke(app, ["meta", str(nb_path), "--check"])
    logs = list(caplog.records)
    assert result.exit_code == 0
    assert len(logs) == 1
    assert logs[0].message == f"No notebooks found in {[Path(nb_path)]}. Nothing to do."


def test_assert(caplog: LogCaptureFixture) -> None:
    """Assert that notebook has sequential and increasing cell execution."""
    caplog.set_level(logging.INFO)

    exprs = (
        "[c.execution_count for c in exec_cells] == list(range(1, len(exec_cells) + 1))"
    )
    recipe = "seq-increase"
    with resources.path("tests.files", "demo.ipynb") as nb_path:
        result = runner.invoke(
            app, ["assert", str(nb_path), "--expr", exprs, "--recipe", recipe]
        )

    logs = list(caplog.records)
    assert result.exit_code == 0
    assert len(logs) == 2
    assert [log.message for log in logs] == [
        f"{nb_path} failed 0 of 2 checks.",
        "All notebooks comply with the desired metadata!",
    ]


def test_assert__config(caplog: LogCaptureFixture) -> None:
    """Assert notebook based on statements from configuration file."""
    caplog.set_level(logging.INFO)

    with resources.path("tests.files", "pyproject.toml") as config:
        nb_dirpath = config.parent
        result = runner.invoke(
            app, ["assert", str(nb_dirpath), "--config", str(config)]
        )
    logs = list(caplog.records)
    assert result.exit_code == 1
    assert len(logs) == 5
    assert (
        logs[-1].message
        == "Found issues in notebook metadata for 2 out of 4 notebooks."
    )


def test_fix(tmp_path: Path) -> None:
    """Fix notebook conflicts."""
    # Setup
    nb_path = Path("test_conflicts_nb.ipynb")
    notebook_1 = TestJupyterNotebook().jupyter_notebook
    notebook_2 = TestJupyterNotebook().jupyter_notebook

    notebook_1.metadata = NotebookMetadata(
        kernelspec=dict(
            display_name="different_kernel_display_name", name="kernel_name"
        ),
        field_to_remove=["Field to remove"],
        another_field_to_remove="another field",
    )

    extra_cell = BaseCell(
        cell_type="raw",
        metadata=CellMetadata(random_meta=["meta"]),
        source="extra",
    )
    notebook_2.cells = notebook_2.cells + [extra_cell]
    notebook_2.nbformat += 1
    notebook_2.nbformat_minor += 1

    git_repo = init_repo_conflicts(
        tmp_path=tmp_path,
        filename=nb_path,
        contents_main=notebook_1.json(),
        contents_other=notebook_2.json(),
        commit_message_main="Notebook from main",
        commit_message_other="Notebook from other",
    )

    conflict_files = get_conflict_blobs(repo=git_repo)
    id_main = conflict_files[0].first_log
    id_other = conflict_files[0].last_log

    # Run CLI and check conflict resolution
    result = runner.invoke(app, ["fix", str(tmp_path)])
    fixed_notebook = JupyterNotebook.parse_file(path=tmp_path / nb_path)

    assert len(conflict_files) == 1
    assert result.exit_code == 0

    expected_metadata = deepcopy(notebook_2.metadata.dict())
    expected_metadata.update(notebook_1.metadata.dict())
    notebook_1.clear_metadata(
        notebook_metadata_remove=(),
        cell_metadata_remove=(),
        cell_remove_fields=["execution_count"],
    )
    assert fixed_notebook.metadata == NotebookMetadata(**expected_metadata)
    assert fixed_notebook.nbformat == notebook_1.nbformat
    assert fixed_notebook.nbformat_minor == notebook_1.nbformat_minor
    assert fixed_notebook.cells == notebook_1.cells + [
        BaseCell(
            metadata=CellMetadata(git_hash=id_main),
            source=[f"`<<<<<<< {id_main}`"],
            cell_type="markdown",
        ),
        BaseCell(
            source=["`=======`"],
            cell_type="markdown",
            metadata=CellMetadata(),
        ),
        extra_cell,
        BaseCell(
            metadata=CellMetadata(git_hash=id_other),
            source=[f"`>>>>>>> {id_other}`"],
            cell_type="markdown",
        ),
    ]


def test_fix__config(tmp_path: Path) -> None:
    """Fix notebook conflicts with configuration overriding defaults."""
    # Setup
    nb_path = Path("test_conflicts_nb.ipynb")
    notebook_1 = TestJupyterNotebook().jupyter_notebook
    notebook_2 = TestJupyterNotebook().jupyter_notebook

    notebook_1.metadata = NotebookMetadata(
        kernelspec=dict(
            display_name="different_kernel_display_name", name="kernel_name"
        ),
        field_to_remove=["Field to remove"],
        another_field_to_remove="another field",
    )

    extra_cell = BaseCell(
        cell_type="raw",
        metadata=CellMetadata(random_meta=["meta"]),
        source="extra",
    )
    notebook_2.cells = notebook_2.cells + [extra_cell]
    notebook_2.nbformat += 1
    notebook_2.nbformat_minor += 1

    git_repo = init_repo_conflicts(
        tmp_path=tmp_path,
        filename=nb_path,
        contents_main=notebook_1.json(),
        contents_other=notebook_2.json(),
        commit_message_main="Notebook from main",
        commit_message_other="Notebook from other",
    )

    conflict_files = get_conflict_blobs(repo=git_repo)
    id_main = conflict_files[0].first_log
    id_other = conflict_files[0].last_log

    with resources.path("tests.files", "pyproject.toml") as config_path:
        # Run CLI and check conflict resolution
        result = runner.invoke(
            app, ["fix", str(tmp_path), "--config", str(config_path)]
        )
    fixed_notebook = JupyterNotebook.parse_file(path=tmp_path / nb_path)

    assert len(conflict_files) == 1
    assert result.exit_code == 0

    expected_metadata = deepcopy(notebook_1.metadata.dict())
    expected_metadata.update(notebook_2.metadata.dict())
    notebook_1.clear_metadata(
        notebook_metadata_remove=(),
        cell_metadata_remove=(),
        cell_remove_fields=["execution_count"],
    )
    assert fixed_notebook.metadata == NotebookMetadata(**expected_metadata)
    assert fixed_notebook.nbformat == notebook_2.nbformat
    assert fixed_notebook.nbformat_minor == notebook_2.nbformat_minor
    assert fixed_notebook.cells == notebook_1.cells + [
        BaseCell(
            metadata=CellMetadata(git_hash=id_main),
            source=[f"`<<<<<<< {id_main}`"],
            cell_type="markdown",
        ),
        BaseCell(
            source=["`=======`"],
            cell_type="markdown",
            metadata=CellMetadata(),
        ),
        extra_cell,
        BaseCell(
            metadata=CellMetadata(git_hash=id_other),
            source=[f"`>>>>>>> {id_other}`"],
            cell_type="markdown",
        ),
    ]


def test_show() -> None:
    """Show notebook in terminal."""
    with resources.path("tests.files", "tui-demo.ipynb") as nb_path:
        result = runner.invoke(app, ["show", str(nb_path)])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
──────────────────────────────── tui-demo.ipynb ────────────────────────────────
                                                            Python 3 (ipykernel)
╭──────────────────────────────────────────────────────────────────────────────╮
│ ╔══════════════════════════════════════════════════════════════════════════╗ │
│ ║                             databooks demo!                              ║ │
│ ╚══════════════════════════════════════════════════════════════════════════╝ │
╰──────────────────────────────────────────────────────────────────────────────╯
In [1]:
╭──────────────────────────────────────────────────────────────────────────────╮
│ from random import random  # cell with tags                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
In [2]:
╭──────────────────────────────────────────────────────────────────────────────╮
│ random()                                                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
Out [2]:
0.570736084214906
In [3]:
╭──────────────────────────────────────────────────────────────────────────────╮
│ print("notebooks + git ❤️")                                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
notebooks + git ❤️

In [4]:
╭──────────────────────────────────────────────────────────────────────────────╮
│ throw error                                                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
  Cell In [4], line 1
    throw error
          ^
SyntaxError: invalid syntax
╭──────────────────────────────────────────────────────────────────────────────╮
│ This is a raw cell! 🚀                                                       │
╰──────────────────────────────────────────────────────────────────────────────╯
In [5]:
╭──────────────────────────────────────────────────────────────────────────────╮
│ import pandas as pd                                                          │
│ import numpy as np                                                           │
│                                                                              │
│ print("A dataframe! 🐼")                                                     │
│ pd.DataFrame(np.random.random((10,3)), columns=[f"col{i}" for i in range(3)] │
╰──────────────────────────────────────────────────────────────────────────────╯
A dataframe! 🐼

Out [5]:
<✨Rich✨ `text/html` not currently supported 😢>
       col0      col1      col2
0  0.849474  0.756456  0.268569
1  0.511937  0.357224  0.570879
2  0.836116  0.928280  0.946514
3  0.803129  0.540215  0.335783
4  0.074853  0.661168  0.344527
5  0.299696  0.782420  0.970147
6  0.159906  0.566822  0.243798
7  0.896461  0.174406  0.758376
8  0.708324  0.895195  0.769364
9  0.860726  0.381919  0.329727
In [ ]:
╭──────────────────────────────────────────────────────────────────────────────╮
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
"""
    )


def test_show_no_multiple() -> None:
    """Don't show multiple notebooks if not confirmed in prompt."""
    with resources.path("tests.files", "tui-demo.ipynb") as nb:
        dirpath = str(nb.parent)

    # Exit code is 0 if user responds to prompt with `n`
    result = runner.invoke(app, ["show", dirpath], input="n")
    assert result.exit_code == 0

    # Raise error (exit code 1) if no answer to prompt is given
    result = runner.invoke(app, ["show", dirpath])
    assert result.exit_code == 1
