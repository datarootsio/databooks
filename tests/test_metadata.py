"""Test metadata wrapper functions"""
from pathlib import Path

from databooks.data_models.notebook import CellMetadata, JupyterNotebook
from databooks.metadata import clear


def test_metadata_clear() -> None:
    """Clear metadata from a notebook and write clean notebook"""
    read_path = Path("notebooks/small.ipynb")
    write_path = Path("notebooks/clean_small.ipynb")

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
