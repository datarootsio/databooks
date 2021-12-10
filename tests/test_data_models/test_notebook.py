"""Test data models for notebook components"""
from copy import deepcopy
from typing import List, Tuple, cast

from databooks.data_models.base import DiffModel
from databooks.data_models.notebook import (
    Cell,
    CellMetadata,
    Cells,
    JupyterNotebook,
    NotebookMetadata,
)


class TestNotebookMetadata:
    @property
    def notebook_metadata(self) -> NotebookMetadata:
        return NotebookMetadata(
            kernelspec=dict(display_name="kernel_display_name", name="kernel_name"),
            field_to_remove="Field to remove",
        )

    def test_remove_fields(self) -> None:
        """Remove fields specified from NotebookMetadata model"""
        metadata = self.notebook_metadata
        assert hasattr(metadata, "field_to_remove")
        extra_fields = [
            field for field, _ in metadata if field not in metadata.__fields__
        ]
        metadata.remove_fields(extra_fields)
        assert not hasattr(metadata, "field_to_remove")


class TestCell:
    @property
    def cell_metadata(self) -> CellMetadata:
        return CellMetadata(field_to_remove="Field to remove")

    @property
    def cell(self) -> Cell:
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
        """Remove fields specified from CellMetadata model"""
        metadata = self.cell_metadata
        extra_fields = [
            field for field, _ in metadata if field not in metadata.__fields__
        ]
        metadata.remove_fields(extra_fields)
        assert metadata.dict() == {}
        assert metadata == CellMetadata()

    def test_clear(self) -> None:
        """Remove metadata specified from notebook Cell"""
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

    def test_cells(self) -> None:
        """Test cell type"""
        dl1 = Cells[Cell]([self.cell])
        dl2 = Cells[Cell]([self.cell] * 2)

        diff = dl1 - dl2

        assert type(dl1) == type(dl2) == Cells[Cell]
        assert type(diff) == Cells[Tuple[List[Cell], List[Cell]]]
        assert diff == Cells(
            [([self.cell], [self.cell]), ([], [self.cell])]  # type: ignore
        )


class TestJupyterNotebook(TestNotebookMetadata, TestCell):
    @property
    def jupyter_notebook(self) -> JupyterNotebook:
        return JupyterNotebook(
            metadata=self.notebook_metadata,
            nbformat=4,
            nbformat_minor=4,
            cells=[self.cell] * 2,
        )

    def test_clear_metadata(self) -> None:
        """Remove metadata specified from JupyterNotebook - cells and notebook levels"""
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
