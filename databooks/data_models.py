"""Data models - Pydantic models for Jupyter notebook components"""
from typing import List, Optional, Union

from pydantic import BaseModel, Extra, PositiveInt, validator


class BaseModelWithRemoveExtras(BaseModel):
    def remove_extra_fields(self):
        """Remove extra fields"""
        for field_name, field_value in self:
            if field_name not in self.__fields__:
                setattr(self, field_name, None)


class KernelSpec(BaseModel):
    display_name: str
    name: str


class NotebookMetadata(BaseModelWithRemoveExtras, extra=Extra.allow):
    kernelspec: Optional[KernelSpec]


class CellMetadata(BaseModelWithRemoveExtras, extra=Extra.allow):
    ...


class CellOutputs(BaseModelWithRemoveExtras, extra=Extra.allow):
    ...


class Cell(BaseModel):
    cell_type: str
    metadata: CellMetadata
    source: Union[List[str], str]
    outputs: Optional[List[CellOutputs]]
    execution_count: Optional[PositiveInt]

    def clear_metadata(
        self, metadata: bool = True, execution_count: bool = True, outputs: bool = False
    ):
        """Clear cell metadata, execution count and outputs"""
        if metadata:
            self.metadata = CellMetadata()
        if outputs and self.cell_type == "code":
            self.outputs = []
        if execution_count and self.cell_type == "code":
            self.execution_count = None

    @validator("cell_type")
    def cell_has_valid_type(cls, v):
        """Check if cell has one of the three predefined types"""
        valid_cell_types = ("raw", "markdown", "code")
        if v not in valid_cell_types:
            raise ValueError(f"Invalid cell type. Must be one of {valid_cell_types}")
        return v

    @validator("outputs")
    def must_not_be_list_for_code_cells(cls, v, values):
        """Check that code cells have list-type outputs"""
        if values["cell_type"] == "code" and not isinstance(v, list):
            raise ValueError(
                f"All code cells must have a list output property, got {type(v)}"
            )
        return v


class JupyterNotebook(BaseModel):
    metadata: NotebookMetadata
    nbformat: int
    nbformat_minor: int
    cells: List[Cell]

    def clear_metadata(self, notebook=True, cells=True, **kwargs):
        """Clear notebook and cell metadata"""
        if notebook:
            self.metadata.remove_extra_fields()
            self.metadata.kernelspec = None
        if cells:
            _nb_cells = []
            for cell in self.cells:
                cell.clear_metadata(**kwargs)
                _nb_cells.append(cell)
            self.cells = _nb_cells
