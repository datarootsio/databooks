import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from py._path.local import LocalPath

from databooks.data_models.notebook import CellMetadata, JupyterNotebook
from databooks.metadata import clear
from tests.test_data_models.test_notebook import TestJupyterNotebook


def test_metadata_clear__check_verbose(
    tmpdir: LocalPath, caplog: LogCaptureFixture
) -> None:
    """Clear metadata from a notebook and write clean notebook."""
    caplog.set_level(logging.DEBUG)
    read_path = Path(tmpdir.mkdir("notebooks") / "test_nb.ipynb")  # type: ignore
    TestJupyterNotebook().jupyter_notebook.write(read_path)
    write_path = read_path.parent / ("clean_" + read_path.name)

    clear(
        read_path=read_path,
        write_path=write_path,
        cell_fields_keep=["outputs"],
        check=True,
        verbose=True,
    )
    logs = list(caplog.records)

    assert (
        JupyterNotebook.parse_file(path=read_path)
        == TestJupyterNotebook().jupyter_notebook
    )

    assert not write_path.exists()
    assert len(logs) == 2
    assert logs[1].message == (
        f"No action taken for {read_path} - only check (unwanted metadata found)."
    )


def test_metadata_clear(tmpdir: LocalPath) -> None:
    """Clear metadata from a notebook and write clean notebook."""
    read_path = Path(tmpdir.mkdir("notebooks") / "test_nb.ipynb")  # type: ignore
    TestJupyterNotebook().jupyter_notebook.write(read_path)
    write_path = read_path.parent / ("clean_" + read_path.name)

    clear(
        read_path=read_path,
        write_path=write_path,
        cell_fields_keep=["cell_type", "source", "metadata"],
    )

    nb_read = JupyterNotebook.parse_file(path=read_path)
    nb_write = JupyterNotebook.parse_file(path=write_path)

    assert write_path.exists()
    assert len(nb_write.cells) == len(nb_read.cells)
    assert all(cell.metadata == CellMetadata() for cell in nb_write.cells)
    assert all(
        cell.outputs == [] for cell in nb_write.cells if cell.cell_type == "code"
    )
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
