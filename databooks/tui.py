"""Terminal user interface (TUI) helper functions and components."""
from contextlib import AbstractContextManager, nullcontext
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, overload

from rich.columns import Columns
from rich.console import Console
from rich.rule import Rule
from rich.theme import Theme

from databooks.data_models.notebook import JupyterNotebook, NotebookMetadata
from databooks.git_utils import DiffContents

DATABOOKS_TUI = Theme({"in_count": "blue", "out_count": "orange3", "kernel": "bold"})

ImgFmt = Enum("ImgFmt", {"html": "HTML", "svg": "SVG", "text": "TXT"})


def nb2rich(
    path: Path,
    console: Console = Console(),
) -> None:
    """Show rich representation of notebook in terminal."""
    notebook = JupyterNotebook.parse_file(path)
    console.print(Rule(path.resolve().name), notebook)


@overload
def nbs2rich(
    paths: List[Path],
    *,
    context: ImgFmt,
    **kwargs: Any,
) -> str:
    ...


@overload
def nbs2rich(
    paths: List[Path],
    *,
    context: bool,
    **kwargs: Any,
) -> None:
    ...


def nbs2rich(
    paths: List[Path],
    *,
    context: Union[ImgFmt, bool] = False,
    export_kwargs: Optional[Dict[str, Any]] = None,
    **console_kwargs: Any,
) -> Optional[str]:
    """
    Show rich representation of notebooks in terminal.

    :param paths: notebook paths to print
    :param context: specify context - `ImgFmt` to export outputs, `True` for `pager`
    :param export_kwargs: keyword arguments for exporting prints (as a dictionary)
    :param console_kwargs: keyword arguments to be passed to `Console`
    :return: console output if `context` is `ImgFmt`, else `None`
    """
    if "record" in console_kwargs:
        raise ValueError(
            "Specify `record` parameter of console via `context` argument."
        )
    theme = console_kwargs.pop("theme", DATABOOKS_TUI)
    console = Console(record=isinstance(context, ImgFmt), theme=theme, **console_kwargs)
    ctx_map: Dict[Union[ImgFmt, bool], AbstractContextManager] = {
        True: console.pager(styles=True),
        False: nullcontext(),
    }
    with ctx_map.get(context, console.capture()):
        for path in paths:
            nb2rich(path, console=console)
    if isinstance(context, ImgFmt):
        return getattr(console, f"export_{context.name}")(**(export_kwargs or {}))


def diff2rich(
    diff: DiffContents,
    *,
    console: Console = Console(),
) -> None:
    """Show rich representation of notebook diff in terminal."""
    a_nb, b_nb = (
        JupyterNotebook.parse_raw(c)
        if c is not None
        else JupyterNotebook(
            nbformat=0, nbformat_minor=0, metadata=NotebookMetadata(), cells=[]
        )
        for c in (diff.a.contents, diff.b.contents)
    )
    cols = Columns(
        [
            Rule(
                f"{ab}/{c['path'].resolve().name if c['path'] is not None else 'null'}"
            )
            for ab, c in asdict(diff).items()
            if ab in ("a", "b")
        ],
        width=console.width // 2,
        padding=(0, 0),
    )
    console.print(cols, a_nb - b_nb)


@overload
def diffs2rich(
    diffs: List[DiffContents],
    *,
    context: ImgFmt,
    **kwargs: Any,
) -> str:
    ...


@overload
def diffs2rich(
    diffs: List[DiffContents],
    *,
    context: bool,
    **kwargs: Any,
) -> None:
    ...


def diffs2rich(
    diffs: List[DiffContents],
    *,
    context: Union[ImgFmt, bool] = False,
    export_kwargs: Optional[Dict[str, Any]] = None,
    **console_kwargs: Any,
) -> Optional[str]:
    """
    Show rich representation of notebook diff in terminal.

    :param diffs: `databooks.git_utils.DiffContents` for rendering
    :param context: specify context - `ImgFmt` to export outputs, `True` for `pager`
    :param export_kwargs: keyword arguments for exporting prints (as a dictionary)
    :param console_kwargs: keyword arguments to be passed to `Console`
    :return: console output if `context` is `ImgFmt`, else `None`
    """
    theme = console_kwargs.pop("theme", DATABOOKS_TUI)
    console = Console(record=isinstance(context, ImgFmt), theme=theme, **console_kwargs)
    ctx_map: Dict[Union[ImgFmt, bool], AbstractContextManager] = {
        True: console.pager(styles=True),
        False: nullcontext(),
    }
    with ctx_map.get(context, console.capture()):
        for diff in diffs:
            diff2rich(diff, console=console)
    if isinstance(context, ImgFmt):
        return getattr(console, f"export_{context.name}")(**(export_kwargs or {}))
