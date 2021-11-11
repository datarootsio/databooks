"""Data models - Pydantic models for Jupyter Notebooks and components"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple, Union

from pydantic import BaseModel, Extra, create_model, root_validator, validator


class BaseModelWithExtras(BaseModel):
    """Base Pydantic class with extras on managing fields."""

    class Config:
        extra = Extra.allow

    def remove_fields(self, fields: Iterable[str], *, recursive:bool = False) -> None:
        """
        Remove selected fields
        :param fields: Fields to remove
        :param recursive: Whether or not to remove the fields recursively in case of
         nested models
        :return:
        """
        for field in fields:
            if recursive and isinstance(getattr(self, field),BaseModelWithExtras):
                getattr(self, field).remove_fields(fields)
            else:
                delattr(self, field)

    def resolve(
        self, *, keep_first: bool = True, ignore_none: bool = True
    ) -> BaseModelWithExtras:
        """
        Resolve differences for 'diff models' into one similar to the parent class
         ``databooks.data_models.Cell.BaseModelWithExtras`
        :param keep_first: Whether to keep the information from the prior in the
         'diff model' or the later
        :param ignore_none: Whether or not to ignore `None` values if encountered, and
         use the other field value
        :return: Model with selected fields from the differences
        """
        if not (hasattr(self, "is_diff") and self.is_diff):  # type: ignore
            raise TypeError("Can only resolve 'diff models' (when `is_diff=True`).")

        field_vals = {
            field: value[not keep_first]
            if value[not keep_first] is not None and ignore_none
            else value[keep_first]
            for field, value in self
            if field != "is_diff"
        }

        field_vals["is_diff"] = False

        return self.__class__.__bases__[0](**field_vals)

    def __str__(self) -> str:
        """Equivalent to __repr__"""
        return repr(self)

    def __sub__(self, other: BaseModelWithExtras) -> BaseModelWithExtras:
        """
        The difference basically return models that replace each fields by a tuple,
         where for each field we have `field = (self_value, other_value)`
        """
        if type(self) != type(other):
            # Ensure we are comparing models of same type
            raise TypeError(
                f"Unsupported operand types for `-`: `{type(self).__name__}` and"
                f" `{type(other).__name__}`"
            )

        # Get field and values for each instance
        self_d = dict(self)
        other_d = dict(other)
        field_keys = set(list(self_d.keys()) + list(other_d.keys()))  # find common keys

        # Build dictionary for the field types and values
        field_pairs = [(self_d.get(field), other_d.get(field)) for field in field_keys]
        field_vals = (
            pairs[0] - pairs[-1]  # type: ignore
            if all(isinstance(el, BaseModelWithExtras) for el in pairs)
            else pairs
            for pairs in field_pairs
        )
        field_types = (
            (Tuple[type(self_val), type(other_val)], ...)
            for self_val, other_val in field_pairs
        )

        # Build Pydantic models dynamically
        DiffModel = create_model(
            "Diff" + self.__class__.__name__,
            __base__=self.__class__,
            is_diff=True,
            **dict(zip(field_keys, field_types)),  # type: ignore
        )
        return DiffModel(**dict(zip(field_keys, field_vals)))


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
    source: Union[List[str], str]
    cell_type: str

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
                self.outputs: List[Dict[str, Any]] = []
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
    def must_not_be_list_for_code_cells(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Check that code cells have list-type outputs"""
        if values["cell_type"] == "code" and not isinstance(values["outputs"], list):
            raise ValueError(
                "All code cells must have a list output property, got"
                f" {type(values.get('outputs'))}"
            )
        return values

    @root_validator
    def only_code_cells_have_outputs_and_execution_count(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
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
    metadata: NotebookMetadata
    nbformat: int
    nbformat_minor: int
    cells: List[Cell]

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
            _nb_cells = []
            for cell in self.cells:
                cell.clear_metadata(**cell_kwargs)
                _nb_cells.append(cell)
            self.cells = _nb_cells
