"""Data models - Cells and components."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from pydantic import PositiveInt, root_validator, validator
from rich.console import Console, ConsoleOptions, RenderResult
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from databooks.data_models.base import DatabooksBase
from databooks.logging import get_logger

logger = get_logger(__file__)


class CellMetadata(DatabooksBase):
    """Cell metadata. Empty by default but can accept extra fields."""


class Cell(DatabooksBase):
    """
    Jupyter notebook cells.

    Fields `outputs` and `execution_count` are not included since they should only be
     present in code cells - thus are treated as extra fields.
    """

    metadata: CellMetadata
    source: Union[List[str], str]
    cell_type: str

    def __hash__(self) -> int:
        """Cells must be hashable for `difflib.SequenceMatcher`."""
        return hash(
            (type(self),) + tuple(v) if isinstance(v, list) else v
            for v in self.__dict__.values()
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich display of cell."""
        if self.cell_type == "code":
            yield CodeCell(**self.dict())

    def remove_fields(
        self, fields: Iterable[str] = (), missing_ok: bool = True, **kwargs: Any
    ) -> None:
        """
        Remove Cell fields.

        Similar to `databooks.data_models.base.remove_fields`, but will ignore required
         fields for `databooks.data_models.notebook.Cell`.
        """
        # Ignore required `Cell` fields
        cell_fields = self.__fields__  # required fields especified in class definition
        if any(field in fields for field in cell_fields):
            logger.debug(
                "Ignoring removal of required fields "
                + str([f for f in fields if f in cell_fields])
                + f" in `{type(self).__name__}`."
            )
            fields = [f for f in fields if f not in cell_fields]

        super(Cell, self).remove_fields(fields, missing_ok=missing_ok)

        if self.cell_type == "code":
            self.outputs: CellOutputs = (
                CellOutputs(__root__=[])
                if "outputs" not in dict(self)
                else self.outputs
            )
            self.execution_count: Optional[PositiveInt] = (
                None if "execution_count" not in dict(self) else self.execution_count
            )

    def clear_fields(
        self,
        *,
        cell_metadata_keep: Sequence[str] = None,
        cell_metadata_remove: Sequence[str] = None,
        cell_remove_fields: Sequence[str] = (),
    ) -> None:
        """
        Clear cell metadata, execution count, outputs or other desired fields (id, ...).

        You can also specify metadata to keep or remove from the `metadata` property of
         `databooks.data_models.notebook.Cell`.
        :param cell_metadata_keep: Metadata values to keep - simply pass an empty
         sequence (i.e.: `()`) to remove all extra fields.
        :param cell_metadata_remove: Metadata values to remove
        :param cell_remove_fields: Fields to remove from cell
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

        self.remove_fields(fields=cell_remove_fields, missing_ok=True)

    @validator("cell_type")
    def cell_has_valid_type(cls, v: str) -> str:
        """Check if cell has one of the three predefined types."""
        valid_cell_types = ("raw", "markdown", "code")
        if v not in valid_cell_types:
            raise ValueError(f"Invalid cell type. Must be one of {valid_cell_types}")
        return v

    @root_validator
    def code_cell_has_outputs(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Check that code cells have outputs."""
        if values.get("cell_type") == "code" and "outputs" not in values:
            raise ValueError(
                f"All code cells must have an `outputs` property, got {values}"
            )
        return values

    @root_validator
    def outputs_are_valid(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Check and parse that cell outputs are valid."""
        outputs = values.get("outputs")
        if outputs is not None:
            values["outputs"] = CellOutputs(__root__=outputs)
        return values

    @root_validator
    def only_code_cells_have_outputs_and_execution_count(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check that only code cells have outputs and execution count."""
        if values.get("cell_type") != "code" and (
            ("outputs" in values) or ("execution_count" in values)
        ):
            raise ValueError(
                "Found `outputs` or `execution_count` for cell of type"
                f" `{values['cell_type']}`"
            )
        return values


class CellStreamOutput(DatabooksBase):
    """Cell output of type `stream`."""

    output_type: str
    name: str
    text: List[str]

    @validator("output_type")
    def output_type_must_be_stream(cls, v: str) -> str:
        """Check if stream has `stream` type."""
        if v != "stream":
            raise ValueError(f"Invalid output type. Expected `stream`, got {v}.")
        return v

    @validator("name")
    def stream_name_must_match(cls, v: str) -> str:
        """Check if stream name is either `stdout` or `stderr`."""
        valid_names = ("stdout", "stderr")
        if v not in valid_names:
            raise ValueError(
                f"Invalid stream name. Expected one of {valid_names}, got {v}."
            )
        return v


class CellDisplayDataOutput(DatabooksBase):
    """Cell output of type `display_data`."""

    output_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]

    @validator("output_type")
    def output_type_must_match(cls, v: str) -> str:
        """Check if stream has `display_data` type."""
        if v != "display_data":
            raise ValueError(f"Invalid output type. Expected `display_data`, got {v}.")
        return v


class CellExecuteResultOutput(CellDisplayDataOutput):
    """Cell output of type `execute_result`."""

    execution_count: PositiveInt

    @validator("output_type")
    def output_type_must_match(cls, v: str) -> str:
        """Check if stream has `execute_result` type."""
        if v != "execute_result":
            raise ValueError(
                f"Invalid output type. Expected `execute_result`, got {v}."
            )
        return v


class CellErrorOutput(DatabooksBase):
    """Cell output of type `error`."""

    output_type: str
    ename: str
    evalue: str
    traceback: List[str]

    @validator("output_type")
    def output_type_must_match(cls, v: str) -> str:
        """Check if stream has `error` type."""
        if v != "error":
            raise ValueError(f"Invalid output type. Expected `error`, got {v}.")
        return v


class CellOutputs(DatabooksBase):
    """Outputs of notebook code cells."""

    __root__: List[
        Union[
            CellStreamOutput,
            CellDisplayDataOutput,
            CellExecuteResultOutput,
            CellErrorOutput,
        ]
    ]

    @property
    def values(
        self,
    ) -> List[
        CellStreamOutput
        | CellDisplayDataOutput
        | CellExecuteResultOutput
        | CellErrorOutput
    ]:
        """Alias `__root__` with outputs for easy referencing."""
        return self.__root__


class CodeCell(Cell):
    """Cell of type `code` - defined for rich displaying in terminal."""

    outputs: CellOutputs
    lang: str = "text"

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich display of code cells."""
        yield Text(f"In [{self.execution_count or ' '}]:", style="in_count")
        yield Panel(
            Syntax(
                "".join(self.source) if isinstance(self.source, list) else self.source,
                "python",  # TODO: change to `self.lang`
            )
        )

    @validator("outputs")
    def get_attr_from_dunder_root(
        cls, v: CellOutputs
    ) -> List[
        Union[
            CellStreamOutput,
            CellDisplayDataOutput,
            CellExecuteResultOutput,
            CellErrorOutput,
        ]
    ]:
        """Extract the list values from the __root__ attribute of `CellOutputs`."""
        return v.__root__
