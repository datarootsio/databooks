"""Functions to safely evaluate strings and inspect notebook."""
import ast
from copy import deepcopy
from itertools import chain, compress, zip_longest
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union

from databooks import JupyterNotebook
from databooks.common import get_keys
from databooks.data_models.base import DatabooksBase
from databooks.logging import get_logger, set_verbose
from databooks.recipes import Recipe

logger = get_logger(__file__)

_ALLOWED_BUILTINS = (all, any, enumerate, filter, len, range, sorted)
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
    ast.Tuple,
    ast.UAdd,
    ast.UnaryOp,
    ast.unaryop,
    ast.USub,
)


class DatabooksParser:
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

    def _get_iter(self, node: Union[ast.Attribute, ast.Call, ast.Name]) -> Iterable:
        if not isinstance(node, (ast.Attribute, ast.Call, ast.Name)):
            raise ValueError(
                "Expected comprehension to be of an  `ast.Name` or `ast.Attribute`, got"
                f" `ast.{type(node).__name__}`."
            )
        tree = ast.Expression(body=node)
        return iter(self.safe_eval_ast(tree))

    @staticmethod
    def generic_visit(node: ast.AST) -> ast.AST:
        """Raise error if AST node is not amongst allowed ones."""
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"Invalid node `{node}`.")
        return node

    def visit_comprehension(self, node: ast.comprehension) -> ast.comprehension:
        """Add variable from a comprehension to list of allowed names."""
        if not isinstance(node.target, ast.Name):
            raise RuntimeError(
                "Expected `ast.comprehension`'s target to be `ast.Name`, got"
                f" `ast.{type(node.target).__name__}`."
            )
        # If any elements in the comprehension are a `DatabooksBase` instance, then
        #  pass down the attributes as valid
        if not isinstance(node.iter, (ast.Attribute, ast.Call, ast.Name)):
            raise RuntimeError(
                "Expected comprehension iterator to be of an  `ast.Name` or"
                f" `ast.Attribute`, got `ast.{type(node.iter).__name__}`."
            )
        iterable = self._get_iter(node.iter)
        has_databooks = any(isinstance(el, DatabooksBase) for el in iterable)
        if has_databooks:
            attrs = chain.from_iterable(
                dict(el).keys() for el in iterable if isinstance(el, DatabooksBase)
            )
            d_attrs = dict(zip_longest(attrs, (), fillvalue=...))
        self.names[node.target.id] = DatabooksBase(**d_attrs) if has_databooks else ...
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        """Allow attributes for Pydantic fields only."""
        if not isinstance(node.value, (ast.Attribute, ast.Name)):
            raise ValueError(
                "Expected attribute to be one of `ast.Name` or `ast.Attribute`, got"
                f" `ast.{type(node.value).__name__}`"
            )
        if isinstance(node.value, ast.Attribute):
            return node
        obj = self.names[node.value.id]
        allowed_attrs = get_keys(obj.dict()) if isinstance(obj, DatabooksBase) else ()
        if node.attr not in allowed_attrs:
            raise ValueError(
                "Expected attribute to be one of"
                f" `{allowed_attrs}`, got `{node.attr}`"
            )
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Only allow names from scope or comprehension variables."""
        names = list(self.names.keys())
        builtins = list(self.builtins.keys())
        if node.id not in names + builtins:
            raise ValueError(
                f"Expected `name` to be one of `{names + builtins}`, got `{node.id}`."
            )
        return node

    def visit(self, node: ast.AST) -> ast.AST:
        """Visit an AST node."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def validate(self, ast_tree: ast.AST) -> List[ast.AST]:
        """Visit every node in tree recursively and ensure that AST tree is safe."""
        nodes = ast.walk(ast_tree)
        return [self.visit(node) for node in nodes]

    def safe_eval_ast(self, ast_tree: ast.AST) -> Any:
        """Evaluate safe AST trees only (raise errors otherwise)."""
        self.validate(ast_tree=ast_tree)
        exe = compile(ast_tree, filename="_", mode="eval")
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


def affirm(
    nb_path: Path, exprs: List[Union[str, Recipe]], verbose: bool = False
) -> bool:
    """
    Return whether notebook passed all checks (expressions).

    :param nb_path: Path of notebook file
    :param exprs: Expression with check to be evaluated on notebook
    :param verbose: Log failed tests for notebook
    :return: Evaluated expression casted as a `bool`
    """
    if verbose:
        set_verbose(logger)

    nb = JupyterNotebook.parse_file(nb_path)
    variables: Dict[str, Any] = {
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
    databooks_parser = DatabooksParser(**variables)
    is_ok = [
        bool(
            databooks_parser.safe_eval(
                expr if isinstance(expr, str) else expr.src,
            )
        )
        for expr in exprs
    ]
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
