from copy import deepcopy
from typing import List, Tuple, cast

import pytest

from databooks.data_models.base import DiffModel
from databooks.data_models.notebook import (
    Cell,
    CellMetadata,
    Cells,
    JupyterNotebook,
    NotebookMetadata,
)


class TestNotebookMetadata:
    """Tests related to notebook metadata fields."""

    @property
    def notebook_metadata(self) -> NotebookMetadata:
        """`NotebookMetadata` property to test on."""
        return NotebookMetadata(
            kernelspec=dict(display_name="kernel_display_name", name="kernel_name"),
            field_to_remove="Field to remove",
            tags=[],
        )

    def test_remove_fields__missing_ok(self) -> None:
        """Remove fields specified from NotebookMetadata model (ignore if missing)."""
        metadata = deepcopy(self.notebook_metadata)
        assert hasattr(metadata, "field_to_remove")
        extra_fields = [
            field for field, _ in metadata if field not in metadata.__fields__
        ]

        with pytest.raises(KeyError):
            metadata.remove_fields(["missing_field"], missing_ok=False)

        metadata.remove_fields(["missing_field"], missing_ok=True)
        metadata.remove_fields(extra_fields, missing_ok=True)

        assert not hasattr(metadata, "field_to_remove")

    def test_remove_fields(self) -> None:
        """Remove fields specified from NotebookMetadata model."""
        metadata = deepcopy(self.notebook_metadata)
        assert hasattr(metadata, "field_to_remove")
        assert hasattr(metadata, "tags")
        extra_fields = [
            field for field, _ in metadata if field not in metadata.__fields__
        ]
        metadata.remove_fields(extra_fields)
        assert not hasattr(metadata, "field_to_remove")
        assert not hasattr(metadata, "tags")


class TestCell:
    """Tests related to notebook cell fields."""

    @property
    def cell_metadata(self) -> CellMetadata:
        """`CellMetadata` property to test on."""
        return CellMetadata(field_to_remove="Field to remove")

    @property
    def cell(self) -> Cell:
        """`Cell` property to test on."""
        return Cell(
            cell_type="code",
            metadata=self.cell_metadata,
            source=["test_source"],
            execution_count=1,
            outputs=[
                {"name": "stdout", "output_type": "stream", "text": ["test text\n"]}
            ],
        )

    def test_cell_metadata(self) -> None:
        """Remove fields specified from `CellMetadata` model."""
        metadata = self.cell_metadata
        extra_fields = [
            field for field, _ in metadata if field not in metadata.__fields__
        ]
        metadata.remove_fields(extra_fields)
        assert metadata.dict() == {}
        assert metadata == CellMetadata()

    def test_clear(self) -> None:
        """Remove metadata specified from notebook `Cell`."""
        cell = self.cell
        assert cell.metadata is not None
        cell.clear_metadata(
            cell_metadata_keep=[], cell_execution_count=True, cell_outputs=True
        )
        assert cell == Cell(
            cell_type="code",
            metadata=CellMetadata(),
            outputs=[],
            source=["test_source"],
            execution_count=None,
        )

    def test_sub_cells(self) -> None:
        """Get the diff from different `Cells`."""
        dl1 = Cells[Cell]([self.cell])
        dl2 = Cells[Cell]([self.cell] * 2)

        diff = dl1 - dl2

        assert type(dl1) == type(dl2) == Cells[Cell]
        assert type(diff) == Cells[Tuple[List[Cell], List[Cell]]]
        assert diff == Cells(
            [([self.cell], [self.cell]), ([], [self.cell])]  # type: ignore
        )


class TestJupyterNotebook(TestNotebookMetadata, TestCell):
    """Tests related to notebooks."""

    @property
    def jupyter_notebook(self) -> JupyterNotebook:
        """`JupyterNotebook` property to test on."""
        return JupyterNotebook(
            metadata=self.notebook_metadata,
            nbformat=4,
            nbformat_minor=4,
            cells=[self.cell] * 2,
        )

    def test_clear_metadata(self) -> None:
        """Remove metadata specified in JupyterNotebook - cells and notebook levels."""
        notebook = self.jupyter_notebook
        notebook.clear_metadata(
            notebook_metadata_keep=[], cell_metadata_keep=[], cell_outputs=True
        )

        assert all(cell.metadata == CellMetadata() for cell in notebook.cells)
        assert all(
            cell.outputs == [] for cell in notebook.cells if cell.cell_type == "code"
        )
        assert all(
            cell.execution_count is None
            for cell in notebook.cells
            if cell.cell_type == "code"
        )

    def test_notebook_sub(self) -> None:
        """
        Compute and resolve diffs of notebooks.

        Use the `-` operator and resolve the diffs from the child classes with nested
         models
        """
        notebook_1 = deepcopy(self.jupyter_notebook)
        notebook_2 = deepcopy(self.jupyter_notebook)
        notebook_1.metadata = NotebookMetadata(
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
        notebook_2.cells = notebook_2.cells + [extra_cell]

        diff = cast(DiffModel, notebook_1 - notebook_2)
        notebook = deepcopy(notebook_1)

        # add `tags` since we resolve with default `ignore_none = True`
        notebook.metadata = NotebookMetadata(
            **notebook_1.metadata.dict(), **{"tags": []}
        )

        assert diff.resolve(keep_first_cells=True) == notebook

        notebook.cells = notebook_2.cells
        assert diff.resolve(keep_first_cells=False) == notebook

        notebook.cells = notebook_1.cells + [
            Cell(
                metadata=CellMetadata(git_hash=None),
                source=["`<<<<<<< None`"],
                cell_type="markdown",
            ),
            Cell(
                source=["`=======`"],
                cell_type="markdown",
                metadata=CellMetadata(),
            ),
            extra_cell,
            Cell(
                metadata=CellMetadata(git_hash=None),
                source=["`>>>>>>> None`"],
                cell_type="markdown",
            ),
        ]
        assert diff.resolve(keep_first_cells=None) == notebook
