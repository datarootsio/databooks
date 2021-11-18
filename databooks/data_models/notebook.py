"""Data models - Jupyter Notebooks and components"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Union

from pydantic import BaseModel, Extra, root_validator, validator

from databooks.data_models.base import BaseModelWithExtras, DiffList


class NotebookMetadata(BaseModelWithExtras):
    ...


class CellMetadata(BaseModelWithExtras):
    ...


class Cell(BaseModel, extra=Extra.allow):
    """
    Jupyter notebook cells. `outputs` and `execution_count` not included since they
     should only be present in code cells - thus are treated as extra fields.
    """

    metadata: CellMetadata
    source: Union[list[str], str]
    cell_type: str

    def __hash__(self) -> int:
        """Cells must be hashable for `difflib.SequenceMatcher`"""
        return hash(
            (type(self),) + tuple(v) if isinstance(v, list) else v
            for v in self.__dict__.values()
        )

    def clear_metadata(
        self,
        *,
        cell_metadata_keep: Sequence[str] = None,
        cell_metadata_remove: Sequence[str] = None,
        cell_execution_count: bool = True,
        cell_outputs: bool = False,
    ) -> None:
        """
        Clear cell metadata, execution count and outputs
        :param cell_metadata_keep: Metadata values to keep - simply pass an empty
         sequence (i.e.: `()`) to remove all extra fields.
        :param cell_metadata_remove: Metadata values to remove
        :param cell_execution_count: Whether or not to keep the execution count
        :param cell_outputs: whether or not to keep the cell outputs
        :return:
        """
        nargs = sum((cell_metadata_keep is not None, cell_metadata_remove is not None))
        if nargs != 1:
            raise ValueError(
                "Exactly one of `cell_metadata_keep` or `cell_metadata_remove` must"
                f" be passed, got {nargs} arguments."
            )
        if cell_metadata_keep is not None:
            cell_metadata_remove = tuple(
                field for field, _ in self.metadata if field not in cell_metadata_keep
            )
        self.metadata.remove_fields(cell_metadata_remove)  # type: ignore

        if self.cell_type == "code":
            if cell_outputs:
                self.outputs: list[dict[str, Any]] = []
            if cell_execution_count:
                self.execution_count = None

    @validator("cell_type")
    def cell_has_valid_type(cls, v: str) -> str:
        """Check if cell has one of the three predefined types"""
        valid_cell_types = ("raw", "markdown", "code")
        if v not in valid_cell_types:
            raise ValueError(f"Invalid cell type. Must be one of {valid_cell_types}")
        return v

    @root_validator
    def must_not_be_list_for_code_cells(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Check that code cells have list-type outputs"""
        if values["cell_type"] == "code" and not isinstance(values["outputs"], list):
            raise ValueError(
                "All code cells must have a list output property, got"
                f" {type(values.get('outputs'))}"
            )
        return values

    @root_validator
    def only_code_cells_have_outputs_and_execution_count(
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        """Check that only code cells have outputs and execution count"""
        if values["cell_type"] != "code" and (
            ("outputs" in values) or ("execution_count" in values)
        ):
            raise ValueError(
                "Found `outputs` or `execution_count` for cell of type"
                f" `{values['cell_type']}`"
            )
        return values


class JupyterNotebook(BaseModelWithExtras, extra=Extra.forbid):
    nbformat: int
    nbformat_minor: int
    metadata: NotebookMetadata
    cells: DiffList[Cell]

    def clear_metadata(
        self,
        *,
        notebook_metadata_keep: Sequence[str] = None,
        notebook_metadata_remove: Sequence[str] = None,
        **cell_kwargs: Any,
    ) -> None:
        """
        Clear notebook and cell metadata
        :param notebook_metadata_keep: Metadata values to keep - simply pass an empty
         sequence (i.e.: `()`) to remove all extra fields.
        :param notebook_metadata_remove: Metadata values to remove
        :param cell_kwargs: keyword arguments to be passed to each cell's
         `databooks.data_models.Cell.clear_metadata`
        :return:
        """

        nargs = sum(
            (notebook_metadata_keep is not None, notebook_metadata_remove is not None)
        )
        if nargs != 1:
            raise ValueError(
                "Exactly one of `notebook_metadata_keep` or `notebook_metadata_remove`"
                f" must be passed, got {nargs} arguments."
            )
        if notebook_metadata_keep is not None:
            notebook_metadata_remove = tuple(
                field
                for field, _ in self.metadata
                if field not in notebook_metadata_keep
            )
        self.metadata.remove_fields(notebook_metadata_remove)  # type: ignore

        if len(cell_kwargs) > 0:
            _nb_cells: DiffList[Cell] = DiffList()
            for cell in self.cells:
                cell.clear_metadata(**cell_kwargs)
                _nb_cells.append(cell)
            self.cells = _nb_cells
