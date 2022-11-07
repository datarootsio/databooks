"""Data models - Jupyter Notebooks and components."""
from __future__ import annotations

import json
from copy import deepcopy
from difflib import SequenceMatcher
from itertools import chain
from pathlib import Path
from typing import (
    Any,
    Callable,
    Generator,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from pydantic import Extra, validate_model
from pydantic.generics import GenericModel
from rich import box
from rich.columns import Columns
from rich.console import Console, ConsoleOptions, Group, RenderableType, RenderResult
from rich.panel import Panel
from rich.text import Text

from databooks.data_models.base import BaseCells, DatabooksBase
from databooks.data_models.cell import CellMetadata, CodeCell, MarkdownCell, RawCell
from databooks.logging import get_logger

logger = get_logger(__file__)

Cell = Union[CodeCell, RawCell, MarkdownCell]
CellsPair = Tuple[List[Cell], List[Cell]]
T = TypeVar("T", Cell, CellsPair)


class Cells(GenericModel, BaseCells[T]):
    """Similar to `list`, with `-` operator using `difflib.SequenceMatcher`."""

    __root__: Sequence[T] = ()

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

    def __sub__(self: Cells[Cell], other: Cells[Cell]) -> Cells[CellsPair]:
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
        return Cells[CellsPair](
            [
                # https://github.com/python/mypy/issues/9459
                tuple((self.data[i1:j1], other.data[i2:j2]))  # type: ignore
                for _, i1, j1, i2, j2 in chain.from_iterable(diff_opcodes)
            ]
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich display of all cells in notebook."""
        yield from self._get_renderables(expand=True, width=options.max_width // 3)

    def _get_renderables(self, **wrap_cols_kwargs: Any) -> Iterable[RenderableType]:
        """Get the Rich renderables, depending on whether `Cells` is a diff or not."""
        if all(isinstance(el, tuple) for el in self.data):
            return chain.from_iterable(
                Cells.wrap_cols(val[0], val[1], **wrap_cols_kwargs)
                if val[0] != val[1]
                else val[0]
                for val in cast(List[CellsPair], self.data)
            )
        return cast(List[Cell], self.data)

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
    def wrap_cols(
        cls, first_cells: List[Cell], last_cells: List[Cell], **cols_kwargs: Any
    ) -> Sequence[Columns]:
        """Wrap the first and second cells into colunmns for iterable."""
        _empty = [Panel(Text("<None>", justify="center"), box=box.SIMPLE)]
        _first = Group(*first_cells or _empty)
        _last = Group(*last_cells or _empty)
        return [Columns([_first, _last], **cols_kwargs)]

    @staticmethod
    def wrap_git(
        first_cells: List[Cell],
        last_cells: List[Cell],
        hash_first: Optional[str] = None,
        hash_last: Optional[str] = None,
    ) -> Sequence[Cell]:
        """Wrap git-diff cells in existing notebook."""
        return [
            MarkdownCell(
                metadata=CellMetadata(git_hash=hash_first),
                source=[f"`<<<<<<< {hash_first}`"],
                cell_type="markdown",
            ),
            *first_cells,
            MarkdownCell(
                source=["`=======`"],
                cell_type="markdown",
                metadata=CellMetadata(),
            ),
            *last_cells,
            MarkdownCell(
                metadata=CellMetadata(git_hash=hash_last),
                source=[f"`>>>>>>> {hash_last}`"],
                cell_type="markdown",
            ),
        ]

    def resolve(
        self: Cells[CellsPair],
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


class NotebookMetadata(DatabooksBase):
    """Notebook metadata. Empty by default but can accept extra fields."""


class JupyterNotebook(DatabooksBase, extra=Extra.forbid):
    """Jupyter notebook. Extra fields yield invalid notebook."""

    nbformat: int
    nbformat_minor: int
    metadata: NotebookMetadata
    cells: Cells[Cell]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich display notebook."""

        def _rich(kernel: str) -> Text:
            """Display with `kernel` theme, horizontal padding and right-justified."""
            return Text(kernel, style="kernel", justify="right")

        kernelspec = self.metadata.dict().get("kernelspec", {})
        if isinstance(kernelspec, tuple):  # check if this is a `DiffCells`
            kernelspec = tuple(
                ks or {"language": "text", "display_name": "null"} for ks in kernelspec
            )
            lang_first, lang_last = (ks.get("language", "text") for ks in kernelspec)
            nb_lang = lang_first if lang_first == lang_last else "text"
            if any("display_name" in ks.keys() for ks in kernelspec):
                kernel_first, kernel_last = [
                    _rich(ks["display_name"]) for ks in kernelspec
                ]
                yield Columns(
                    [kernel_first, kernel_last],
                    expand=True,
                    width=options.max_width // 3,
                ) if kernel_first != kernel_last else kernel_first
        else:
            nb_lang = kernelspec.get("language", "text")
            if "display_name" in kernelspec.keys():
                yield _rich(kernelspec["display_name"])

        for cell in self.cells:
            if isinstance(cell, CodeCell):
                cell.metadata = CellMetadata(**cell.metadata.dict(), lang=nb_lang)
        yield self.cells

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

    def write(
        self, path: Path | str, overwrite: bool = False, **json_kwargs: Any
    ) -> None:
        """Write notebook to disk."""
        path = Path(path) if not isinstance(path, Path) else path
        json_kwargs = {"indent": 2, **json_kwargs}
        if path.is_file() and not overwrite:
            raise ValueError(
                f"File exists at {path} exists. Specify `overwrite = True`."
            )

        _, _, validation_error = validate_model(self.__class__, self.dict())
        if validation_error:
            raise validation_error
        with path.open("w") as f:
            json.dump(self.dict(), fp=f, **json_kwargs)

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
         `databooks.data_models.cell.BaseCell.clear_metadata`
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
