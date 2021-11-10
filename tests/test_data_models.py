"""Test data models and methods"""
from databooks.data_models import Cell, CellMetadata, JupyterNotebook, NotebookMetadata


class TestNotebookMetadata:
    @property
    def notebook_metadata(self):
        return NotebookMetadata(
            kernelspec=dict(display_name="kernel_display_name", name="kernel_name"),
            field_to_remove="Field to remove",
        )

    def test_remove_fields(self):
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
    def cell_metadata(self):
        return CellMetadata(field_to_remove="Field to remove")

    @property
    def cell(self):
        return Cell(
            cell_type="code",
            metadata=self.cell_metadata,
            source="test_source",
            execution_count=1,
            outputs=["example output\n"],
        )

    def test_cell_metadata(self):
        """Remove fields specified from CellMetadata model"""
        metadata = self.cell_metadata
        extra_fields = [
            field for field, _ in metadata if field not in metadata.__fields__
        ]
        metadata.remove_fields(extra_fields)
        assert metadata.dict() == {}
        assert metadata == CellMetadata()

    def test_clear(self):
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
