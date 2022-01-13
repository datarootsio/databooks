"""Data models - Jupyter Notebooks and components."""
from __future__ import annotations

from copy import deepcopy
from difflib import SequenceMatcher
from itertools import chain
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from pydantic import Extra, PositiveInt, root_validator, validator
from pydantic.generics import GenericModel

from databooks.data_models.base import BaseCells, DatabooksBase
from databooks.logging import get_logger

logger = get_logger(__file__)


class NotebookMetadata(DatabooksBase):
    """Notebook metadata. Empty by default but can accept extra fields."""

    ...


class CellMetadata(DatabooksBase):
    """Cell metadata. Empty by default but can accept extra fields."""

    ...


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
            self.outputs: List[Dict[str, Any]] = (
                [] if "outputs" not in dict(self) else self.outputs
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
    def must_not_be_list_for_code_cells(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Check that code cells have list-type outputs."""
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
        """Check that only code cells have outputs and execution count."""
        if values["cell_type"] != "code" and (
            ("outputs" in values) or ("execution_count" in values)
        ):
            raise ValueError(
                "Found `outputs` or `execution_count` for cell of type"
                f" `{values['cell_type']}`"
            )
        return values


T = TypeVar("T", Cell, Tuple[List[Cell], List[Cell]])


class Cells(GenericModel, BaseCells[T]):
    """Similar to `list`, with `-` operator using `difflib.SequenceMatcher`."""

    __root__: Sequence[T] = []

    def __init__(self, elements: Sequence[T] = ()) -> None:
        """Allow passing data as a positional argument when instantiating class."""
        super(Cells, self).__init__(__root__=elements)

    @property
    def data(self) -> List[T]:  # type: ignore
        """Define property `data` required for `collections.UserList` class."""
        return list(self.__root__)

    def __iter__(self) -> Generator[Any, None, None]:
        """Use list property as iterable."""
        return (el for el in self.data)

    def __sub__(
        self: Cells[Cell], other: Cells[Cell]
    ) -> Cells[Tuple[List[Cell], List[Cell]]]:
        """Return the difference using `difflib.SequenceMatcher`."""
        if type(self) != type(other):
            raise TypeError(
                f"Unsupported operand types for `-`: `{type(self).__name__}` and"
                f" `{type(other).__name__}`"
            )

        # By setting the context to the max number of cells and using
        #  `pathlib.SequenceMatcher.get_grouped_opcodes` we essentially get the same
        #  result as `pathlib.SequenceMatcher.get_opcodes` but in smaller chunks
        n_context = max(len(self), len(other))
        diff_opcodes = list(
            SequenceMatcher(
                isjunk=None, a=self, b=other, autojunk=False
            ).get_grouped_opcodes(n_context)
        )

        if len(diff_opcodes) > 1:
            raise RuntimeError(
                "Expected one group for opcodes when context size is "
                f" {n_context} for {len(self)} and {len(other)} cells in"
                " notebooks."
            )
        return Cells[Tuple[List[Cell], List[Cell]]](
            [
                # https://github.com/python/mypy/issues/9459
                tuple((self.data[i1:j1], other.data[i2:j2]))  # type: ignore
                for _, i1, j1, i2, j2 in chain.from_iterable(diff_opcodes)
            ]
        )

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
        """Get validators for custom class."""
        yield cls.validate

    @classmethod
    def validate(cls, v: List[T]) -> Cells[T]:
        """Ensure object is custom defined container."""
        if not isinstance(v, cls):
            return cls(v)
        else:
            return v

    @classmethod
    def wrap_git(
        cls,
        first_cells: List[Cell],
        last_cells: List[Cell],
        hash_first: Optional[str] = None,
        hash_last: Optional[str] = None,
    ) -> List[Cell]:
        """Wrap git-diff cells in existing notebook."""
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
        self: Cells[Tuple[List[Cell], List[Cell]]],
        *,
        keep_first_cells: Optional[bool] = None,
        first_id: Optional[str] = None,
        last_id: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Cell]:
        """
        Resolve differences between `databooks.data_models.notebook.Cells`.

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
                chain.from_iterable(pairs[not keep_first_cells] for pairs in self.data)
            )
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
                for val in self.data
            )
        )


class JupyterNotebook(DatabooksBase, extra=Extra.forbid):
    """Jupyter notebook. Extra fields yield invalid notebook."""

    nbformat: int
    nbformat_minor: int
    metadata: NotebookMetadata
    cells: Cells[Cell]

    @classmethod
    def parse_file(cls, path: Path | str, **parse_kwargs: Any) -> JupyterNotebook:
        """Parse notebook from a path."""
        content_arg = parse_kwargs.pop("content_type", None)
        if content_arg is not None:
            raise ValueError(
                f"Value of `content_type` must be `json` (default), got `{content_arg}`"
            )
        return super(JupyterNotebook, cls).parse_file(
            path=path, content_type="json", **parse_kwargs
        )

    def clear_metadata(
        self,
        *,
        notebook_metadata_keep: Sequence[str] = None,
        notebook_metadata_remove: Sequence[str] = None,
        **cell_kwargs: Any,
    ) -> None:
        """
        Clear notebook and cell metadata.

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
            _clean_cells = deepcopy(self.cells)
            for cell in _clean_cells:
                cell.clear_fields(**cell_kwargs)
            self.cells = _clean_cells
