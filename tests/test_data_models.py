"""Test data models and methods"""
from databooks.data_models import (
    Cell,
    CellMetadata,
    JupyterNotebook,
    KernelSpec,
    NotebookMetadata,
)


class TestNotebookMetadata:
    @property
    def kernel_spec(self):
        return KernelSpec(display_name="kernel_display_name", name="kernel_name")

    @property
    def notebook_metadata(self):
        return NotebookMetadata(
            kernelspec=self.kernel_spec, field_to_remove="Field to remove"
        )

    def test_remove_extra_fields(self):
        metadata = self.notebook_metadata
        assert hasattr(metadata, "field_to_remove")
        metadata.remove_extra_fields()
        assert metadata == NotebookMetadata(
            kernelspec=self.kernel_spec, field_to_remove=None
        )


class TestCell:
    @property
    def cell_metadata(self):
        return CellMetadata(field_to_remove="Field to remove")

    @property
    def cell(self):
        # TODO: how does this not throw an error? code cells should have ooutputs no?
        return Cell(
            cell_type="code",
            metadata=self.cell_metadata,
            source="test_source",
            execution_count=1,
        )

    def test_cell_metadata(self):
        metadata = self.cell_metadata
        metadata.remove_extra_fields()
        assert metadata.dict(exclude_none=True) == {}
        assert metadata.dict(exclude_none=False) == {"field_to_remove": None}
        assert metadata == CellMetadata(field_to_remove=None)

    def test_clear(self):
        cell = self.cell
        assert cell.metadata is not None
        cell.clear_metadata(metadata=True, execution_count=True, outputs=True)
        assert cell == Cell(
            cell_type="code",
            metadata=CellMetadata(),
            outputs=[],
            source="test_source",
            execution_count=None,
        )


class TestJupyterNotebook(TestNotebookMetadata, TestCell):
    @property
    def jupyter_notebook(self):
        return JupyterNotebook(
            metadata=self.notebook_metadata,
            nbformat=4,
            nbformat_minor=4,
            cells=[self.cell] * 2,
        )

    def test_clear_metadata(self):
        notebook = self.jupyter_notebook
        notebook.clear_metadata(notebook=True, cells=True, outputs=True)

        assert notebook.metadata.kernelspec is None
        assert all(cell.metadata == CellMetadata() for cell in notebook.cells)
        assert all(
            cell.outputs == [] for cell in notebook.cells if cell.cell_type == "code"
        )
        assert all(
            cell.execution_count is None
            for cell in notebook.cells
            if cell.cell_type == "code"
        )
