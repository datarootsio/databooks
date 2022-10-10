"""Functions to safely evaluate strings and inspect notebook."""
import ast
from collections import abc
from copy import deepcopy
from itertools import compress
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple

from databooks import JupyterNotebook
from databooks.data_models.base import DatabooksBase
from databooks.logging import get_logger, set_verbose

logger = get_logger(__file__)

_ALLOWED_BUILTINS = (
    all,
    any,
    enumerate,
    filter,
    getattr,
    hasattr,
    len,
    list,
    range,
    sorted,
)
_ALLOWED_NODES = (
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
    ast.comprehension,
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
    ast.ListComp,
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
    ast.Subscript,
    ast.Tuple,
    ast.UAdd,
    ast.UnaryOp,
    ast.unaryop,
    ast.USub,
)


class DatabooksParser(ast.NodeVisitor):
    """AST parser that disallows unsafe nodes/values."""

    def __init__(self, **variables: Any) -> None:
        """Instantiate with variables and callables (built-ins) scope."""
        # https://github.com/python/mypy/issues/3728
        self.builtins = {b.__name__: b for b in _ALLOWED_BUILTINS}  # type: ignore
        self.names = deepcopy(variables) or {}
        self.scope = {
            **self.names,
            "__builtins__": self.builtins,
        }

    @staticmethod
    def _prioritize(field: Tuple[str, Any]) -> bool:
        """Prioritize `ast.comprehension` nodes when expanding the AST tree."""
        _, value = field
        if not isinstance(value, list):
            return True
        return not any(isinstance(f, ast.comprehension) for f in value)

    @staticmethod
    def _allowed_attr(obj: Any, attr: str, is_dynamic: bool = False) -> None:
        """
        Check that attribute is a key of `databooks.data_models.base.DatabooksBase`.

        If `obj` is an iterable and was computed dynamically (that is, not originally in
         scope but computed from a comprehension), check attributes for all elements in
         the iterable.
        """
        allowed_attrs = list(dict(obj).keys()) if isinstance(obj, DatabooksBase) else ()
        if isinstance(obj, abc.Iterable) and is_dynamic:
            for el in obj:
                DatabooksParser._allowed_attr(obj=el, attr=attr)
        else:
            if attr not in allowed_attrs:
                raise ValueError(
                    "Expected attribute to be one of"
                    f" `{allowed_attrs}`, got `{attr}` for {obj}."
                )

    def _get_iter(self, node: ast.AST) -> Iterable:
        """Use `DatabooksParser.safe_eval_ast` to get the iterable object."""
        tree = ast.Expression(body=node)
        return iter(self.safe_eval_ast(tree))

    def generic_visit(self, node: ast.AST) -> None:
        """
        Prioritize `ast.comprehension` nodes when expanding tree.

        Similar to `NodeVisitor.generic_visit`, but favor comprehensions when multiple
         nodes on the same level. In comprehensions, we have a generator argument that
         includes names that are stored. By visiting them first we avoid 'running into'
         unknown names.
        """
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"Invalid node `{node}`.")

        for field, value in sorted(ast.iter_fields(node), key=self._prioritize):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        """Add variable from a comprehension to list of allowed names."""
        if not isinstance(node.target, ast.Name):
            raise RuntimeError(
                "Expected `ast.comprehension`'s target to be `ast.Name`, got"
                f" `ast.{type(node.target).__name__}`."
            )
        self.names[node.target.id] = self._get_iter(node.iter)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Allow attributes for Pydantic fields only."""
        if not isinstance(node.value, (ast.Attribute, ast.Name, ast.Subscript)):
            raise ValueError(
                "Expected attribute to be one of `ast.Name`, `ast.Attribute` or"
                f" `ast.Subscript`, got `ast.{type(node.value).__name__}`."
            )
        if isinstance(node.value, ast.Name):
            self._allowed_attr(
                obj=self.names[node.value.id],
                attr=node.attr,
                is_dynamic=node.value.id in (self.names.keys() - self.scope.keys()),
            )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Only allow names from scope or comprehension variables."""
        valid_names = {**self.names, **self.builtins}
        if node.id not in valid_names:
            raise ValueError(
                f"Expected `name` to be one of `{valid_names.keys()}`, got `{node.id}`."
            )
        self.generic_visit(node)

    def safe_eval_ast(self, ast_tree: ast.AST) -> Any:
        """Evaluate safe AST trees only (raise errors otherwise)."""
        self.visit(ast_tree)
        exe = compile(ast_tree, filename="", mode="eval")
        return eval(exe, self.scope)

    def safe_eval(self, src: str) -> Any:
        """
        Evaluate strings that are safe only (raise errors otherwise).

        A "safe" string or node provided may only consist of nodes in
         `databooks.affirm._ALLOWED_NODES` and built-ins from
         `databooks.affirm._ALLOWED_BUILTINS`.
        """
        ast_tree = ast.parse(src, mode="eval")
        return self.safe_eval_ast(ast_tree)


def affirm(nb_path: Path, exprs: List[str], verbose: bool = False) -> bool:
    """
    Return whether notebook passed all checks (expressions).

    :param nb_path: Path of notebook file
    :param exprs: Expression with check to be evaluated on notebook
    :param verbose: Log failed tests for notebook
    :return: Evaluated expression cast as a `bool`
    """
    if verbose:
        set_verbose(logger)

    nb = JupyterNotebook.parse_file(nb_path)
    variables: Dict[str, Any] = {
        "nb": nb,
        "raw_cells": [c for c in nb.cells if c.cell_type == "raw"],
        "md_cells": [c for c in nb.cells if c.cell_type == "markdown"],
        "code_cells": [c for c in nb.cells if c.cell_type == "code"],
        "exec_cells": [
            c
            for c in nb.cells
            if c.cell_type == "code" and c.execution_count is not None
        ],
    }
    databooks_parser = DatabooksParser(**variables)
    is_ok = [bool(databooks_parser.safe_eval(expr)) for expr in exprs]
    n_fail = sum([not ok for ok in is_ok])

    logger.info(f"{nb_path} failed {n_fail} of {len(is_ok)} checks.")
    logger.debug(
        str(nb_path)
        + (
            f" failed {list(compress(exprs, (not ok for ok in is_ok)))}."
            if n_fail > 0
            else " succeeded all checks."
        )
    )
    return all(is_ok)


def affirm_all(
    nb_paths: List[Path],
    *,
    progress_callback: Callable[[], None] = lambda: None,
    **affirm_kwargs: Any,
) -> List[bool]:
    """
    Clear metadata for multiple notebooks at notebooks and cell level.

    :param nb_paths: Paths of notebooks to assert metadata
    :param progress_callback: Callback function to report progress
    :param affirm_kwargs: Keyword arguments to be passed to `databooks.affirm.affirm`
    :return: Whether the notebooks contained or not the desired metadata
    """
    checks = []
    for nb_path in nb_paths:
        checks.append(affirm(nb_path, **affirm_kwargs))
        progress_callback()
    return checks
