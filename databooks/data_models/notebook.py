"""Data models - Jupyter Notebooks and components"""
from __future__ import annotations

from difflib import SequenceMatcher
from itertools import chain
from typing import Any, Callable, Generator, Optional, Sequence, TypeVar, Union

from pydantic import BaseModel, Extra, root_validator, validator
from pydantic.generics import GenericModel

from databooks.data_models.base import BaseCells, BaseModelWithExtras


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


# https://github.com/python/mypy/issues/9459
T = TypeVar("T", Cell, tuple[Optional[list[Cell]], ...])  # type: ignore


class Cells(GenericModel, BaseCells[T]):
    """Similar to `list`, with `-` operator using `difflib.SequenceMatcher`"""

    __root__: Sequence[T] = []

    def __init__(self, elements: Sequence[T] = ()) -> None:
        """Allow passing data as a positional argument when instantiating class"""
        super(Cells, self).__init__(__root__=elements)

    @property
    def data(self) -> list[T]:  # type: ignore
        """Define property `data` required for `collections.UserList` class"""
        return list(self.__root__)

    def __iter__(self) -> Generator[Any, None, None]:
        """Use list property as iterable"""
        return (el for el in self.data)

    def __sub__(
        self: Cells[Cell], other: Cells[Cell]
    ) -> Cells[tuple[Optional[list[Cell]], ...]]:
        """Return the difference using `difflib.SequenceMatcher`"""
        if type(self) != type(other):
            raise TypeError(
                f"Unsupported operand types for `-`: `{type(self).__name__}` and"
                f" `{type(other).__name__}`"
            )
        s = SequenceMatcher(isjunk=None, a=self, b=other)
        pairs = [
            (self.data[i1:j1], other.data[i2:j2])
            for _, i1, j1, i2, j2 in s.get_opcodes()
        ]
        # https://github.com/python/mypy/issues/9459
        return Cells[tuple[Optional[list[Cell]], ...]](  # type: ignore
            [tuple(el if len(el) > 0 else None for el in pair) for pair in pairs]
        )

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, v: list[T]) -> Cells[T]:
        if not isinstance(v, cls):
            return cls(v)
        else:
            return v

    @classmethod
    def wrap_git(
        cls,
        first_cells: list[Cell],
        last_cells: list[Cell],
        hash_first: Optional[str] = None,
        hash_last: Optional[str] = None,
    ) -> list[Cell]:
        """Wrap git-diff cells in existing notebook"""
        return (
            [
                Cell(
                    metadata=CellMetadata(git_hash=hash_first),
                    source=[f"`<<<<<<< {hash_first}`"],
                    cell_type="markdown",
                )
            ]
            + first_cells
            + [
                Cell(
                    source=["`=======`"],
                    cell_type="markdown",
                    metadata=CellMetadata(),
                )
            ]
            + last_cells
            + [
                Cell(
                    metadata=CellMetadata(git_hash=hash_last),
                    source=[f"`>>>>>>> {hash_last}`"],
                    cell_type="markdown",
                )
            ]
        )

    def resolve(
        self: Cells[tuple[Optional[list[Cell]], ...]],
        *,
        keep_first_cells: Optional[bool] = None,
        first_id: Optional[str] = None,
        last_id: Optional[str] = None,
        **kwargs: Any,
    ) -> list[Cell]:
        """
        Resolve differences between `databooks.data_models.notebook.Cells`
        :param keep_first_cells: Whether to keep the cells of the first notebook or not.
         If `None`, then keep both wrapping the git-diff tags
        :param first_id: Git hash of first file in conflict
        :param last_id: Git hash of last file in conflict
        :param kwargs: (Unused) keyword arguments to keep compatibility with
         `databooks.data_models.base.resolve`
        :return: List of cells
        """
        if keep_first_cells is not None:
            return list(
                chain.from_iterable(
                    pairs[not keep_first_cells]  # type: ignore
                    for pairs in self.data
                    if pairs[not keep_first_cells] is not None
                )
            )
        pairs = [tuple(v if v is not None else [] for v in pair) for pair in self.data]
        return list(
            chain.from_iterable(
                Cells.wrap_git(
                    first_cells=val[0],
                    last_cells=val[1],
                    hash_first=first_id,
                    hash_last=last_id,
                )
                if val[0] != val[1]
                else val[0]
                for val in pairs
            )
        )


class JupyterNotebook(BaseModelWithExtras, extra=Extra.ignore):
    nbformat: int
    nbformat_minor: int
    metadata: NotebookMetadata
    cells: Cells[Cell]

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
            _nb_cells: Cells[Cell] = Cells()
            for cell in self.cells:
                cell.clear_metadata(**cell_kwargs)
                _nb_cells.append(cell)
            self.cells = _nb_cells
