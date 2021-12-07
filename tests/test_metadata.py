"""Test metadata wrapper functions"""
import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from py._path.local import LocalPath

from databooks.common import write_notebook
from databooks.data_models.notebook import CellMetadata, JupyterNotebook
from databooks.metadata import clear
from tests.test_data_models.test_notebook import TestJupyterNotebook  # type: ignore


def test_metadata_clear(tmpdir) -> None:
    """Clear metadata from a notebook and write clean notebook"""
    read_path = tmpdir.mkdir("notebooks") / "test_nb.ipynb"
    write_notebook(nb=TestJupyterNotebook().jupyter_notebook, path=read_path)

    read_path = Path("notebooks/small.ipynb")
    write_path = read_path.parent / ("clean_" + read_path.name)

    clear(
        read_path=read_path,
        write_path=write_path,
        cell_outputs=True,
    )

    nb_read = JupyterNotebook.parse_file(path=read_path, content_type="json")
    nb_write = JupyterNotebook.parse_file(path=write_path, content_type="json")

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
