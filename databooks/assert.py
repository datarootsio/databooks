"""Functions to safely evaluate strings and inspect notebook."""
import ast
from enum import Enum
from itertools import compress
from pathlib import Path
from typing import Any, Dict, List, Union

from databooks import JupyterNotebook
from databooks.logging import get_logger, set_verbose

logger = get_logger(__file__)

_SAFE_BUILTINS = (all, any, enumerate, filter, len, range)
_SAFE_NODES = (
    ast.Add,
    ast.And,
    ast.BinOp,
    ast.BitAnd,
    ast.BitOr,
    ast.BitXor,
    ast.BoolOp,
    ast.boolop,
    ast.cmpop,
    ast.Compare,
    ast.Constant,
    ast.Dict,
    ast.Eq,
    ast.Expr,
    ast.expr,
    ast.expr_context,
    ast.Expression,
    ast.For,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.Is,
    ast.IsNot,
    ast.List,
    ast.Load,
    ast.LShift,
    ast.Lt,
    ast.LtE,
    ast.Mod,
    ast.Name,
    ast.Not,
    ast.NotEq,
    ast.NotIn,
    ast.Num,
    ast.operator,
    ast.Or,
    ast.RShift,
    ast.Set,
    ast.Slice,
    ast.slice,
    ast.Str,
    ast.Sub,
    ast.Tuple,
    ast.UAdd,
    ast.UnaryOp,
    ast.unaryop,
    ast.USub,
)


class Recipe(Enum):
    """Common user recipes for the `assert` command."""

    seq_exec = (
        "[c.execution_count for c in exec_cells] == list(range(1, len(exec_cells) + 1))"
    )
    seq_increase = (
        "[c.execution_count for c in exec_cells] =="
        " sorted([c.execution_count for c in exec_cells])"
    )
    has_tags = "any('tags' in cell.metadata for cell in nb.cells)"
    max_cells = "len(nb.cells) < 128"


def safe_eval(src: str, /, _globals: Dict[str, Any]) -> Any:
    """
    Safely evaluate a string containing a Python expression.

    The string or node provided may only consist of `databooks.assert._SAFE_NODES`.
    Inspired by https://stackoverflow.com/a/48135793/9436980.
    """
    node = ast.parse(src, mode="eval")
    for subnode in ast.walk(node):
        if isinstance(subnode, _SAFE_NODES):
            raise ValueError(
                f"Unsafe expression {src} - contains {type(subnode).__name__}."
            )
        if isinstance(subnode, ast.Name) and subnode.id not in _globals:
            raise ValueError(
                f"Unsafe expression {src} - contains unknown variable `{subnode.id}`."
            )

    # https://github.com/python/mypy/issues/3728
    safe_globals = {
        **_globals,
        "__builtins__": {b.__name__: b for b in _SAFE_BUILTINS},  # type: ignore
    }
    return eval(src, safe_globals)


def ensure(
    nb_path: Path, exprs: List[Union[str, Recipe]], verbose: bool = False
) -> bool:
    """
    Return whether notebook passed all checks (expressions).

    :param nb_path: Path of notebook file
    :param exprs: Expression with check to be evaluated on notebook
    :param verbose: Log failed tests for notebook
    :return:
    """
    if verbose:
        set_verbose(logger)

    nb = JupyterNotebook.parse_file(nb_path)
    variables = {
        "nb": nb,
        "raw_cells": [c for c in nb.cells if c.cell_type == "raw"],
        "markdown_cells": [c for c in nb.cells if c.cell_type == "markdown"],
        "code_cells": [c for c in nb.cells if c.cell_type == "code"],
        "exec_cells": [
            c
            for c in nb.cells
            if c.cell_type == "code" and c.execution_count is not None
        ],
    }

    is_ok = [
        bool(safe_eval(expr if isinstance(expr, str) else expr.value, variables))
        for expr in exprs
    ]
    logger.info(
        f"{nb_path} failed {sum([not ok for ok in is_ok])} of {len(is_ok)} checks."
    )
    logger.debug(f"{nb_path} failed {compress(exprs, (not ok for ok in is_ok))}.")
    return all(is_ok)
