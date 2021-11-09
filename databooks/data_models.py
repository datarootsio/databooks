"""Data models - Pydantic models for Jupyter notebook components"""
from collections import abc
from typing import Iterable, List, Sequence, Union

from pydantic import BaseModel, Extra, validator


class BaseModelWithExtras(BaseModel):
    """Base Pydantic class with extras on managing fields."""

    def remove_fields(self, fields: Iterable[str]):
        """Remove selected fields."""
        for field in fields:
            delattr(self, field)

    def remove_extra_fields(self) -> None:
        """Remove extra fields"""
        fields_to_remove = tuple(
            field for field, _ in self if field not in self.__fields__
        )
        self.remove_fields(fields_to_remove)

    class Config:
        extra = Extra.allow


class NotebookMetadata(BaseModelWithExtras):
    ...


class CellMetadata(BaseModelWithExtras):
    ...


class CellOutputs(BaseModel):
    name: str
    output_type: str


class Cell(BaseModelWithExtras):
    """
    Jupyter notebook cells. `outputs` and `execution_count` not included since
    they should only be present in code cells - thus they are treated as extra
    fields.
    """

    metadata: CellMetadata
    source: Union[List[str], str]
    cell_type: str
    # outputs: Optional[List[CellOutputs]]
    # execution_count: Optional[PositiveInt]

    def clear_metadata(
        self,
        cell_metadata: Union[Sequence[str], bool] = True,
        cell_execution_count: bool = True,
        cell_outputs: bool = False,
    ):
        """
        Clear cell metadata, execution count and outputs
        :param cell_metadata: Either a sequence of metadata fields to remove or `True`
         to remove all fields
        :param cell_execution_count: Whether or not to keep the execution count
        :param cell_outputs: whether or not to keep the cell outputs
        :return:
        """
        if isinstance(cell_metadata, abc.Sequence):
            self.metadata.remove_fields(cell_metadata)
        elif cell_metadata:
            self.metadata.remove_extra_fields()

        if self.cell_type == "code":
            if cell_outputs:
                self.outputs: List[CellOutputs] = []
            if cell_execution_count:
                self.execution_count = None

    @validator("cell_type")
    def cell_has_valid_type(cls, v):
        """Check if cell has one of the three predefined types"""
        valid_cell_types = ("raw", "markdown", "code")
        if v not in valid_cell_types:
            raise ValueError(f"Invalid cell type. Must be one of {valid_cell_types}")
        return v

    # TODO: Pydantic does not allow validation of extra fields (yet) - this could be
    #  done in `attrs`. Check https://github.com/samuelcolvin/pydantic/issues/515
    # @validator("cell_type")
    # def must_not_be_list_for_code_cells(cls, v, values):
    #     """Check that code cells have list-type outputs"""
    #     if v == "code" and not isinstance(values["outputs"], list):
    #         raise ValueError(
    #             f"All code cells must have a list output property, got {type(v)}"
    #         )
    #     return v

    @validator("cell_type")
    def only_code_cells_have_outputs_and_execution_count(cls, v, values):
        """Check that only code cells have outputs and execution count"""
        if v != "code" and (("outputs" in values) or ("execution_count" in values)):
            raise ValueError(
                f"Found `outputs` or `execution_count` for cell of type `{v}`"
            )
        return v


class JupyterNotebook(BaseModel):
    metadata: NotebookMetadata
    nbformat: int
    nbformat_minor: int
    cells: List[Cell]

    def clear_metadata(
        self, notebook_metadata: Union[Sequence[str], bool] = True, **cell_kwargs
    ):
        """
        Clear notebook and cell metadata
        :param notebook_metadata: Either a sequence of metadata fields to remove or
         `True` to remove all fields
        :param cell_kwargs: keyword arguments to be passed to each cell's
         `clear_metadata`
        :return:
        """
        if isinstance(notebook_metadata, abc.Sequence):
            self.metadata.remove_fields(notebook_metadata)
        elif notebook_metadata:
            self.metadata.remove_extra_fields()

        if len(cell_kwargs) > 0:
            _nb_cells = []
            for cell in self.cells:
                cell.clear_metadata(**cell_kwargs)
                _nb_cells.append(cell)
            self.cells = _nb_cells
