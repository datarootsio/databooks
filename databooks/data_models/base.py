"""Data models - Base Pydantic model with custom methods."""
from __future__ import annotations

from abc import abstractmethod
from collections import UserList
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Protocol,
    TypeVar,
    cast,
    overload,
    runtime_checkable,
)

from pydantic import BaseModel, Extra, create_model

T = TypeVar("T")


@runtime_checkable
class DiffModel(Protocol, Iterable):
    """Protocol for mypy static type checking."""

    is_diff: bool

    def resolve(self, *args: Any, **kwargs: Any) -> DatabooksBase:
        """Return a valid base object."""
        ...


class BaseCells(UserList, Generic[T]):
    """Base abstract class for notebook cells."""

    @abstractmethod
    def resolve(self, **kwargs: Any) -> list:
        """Return valid notebook cells from differences."""
        raise NotImplementedError

    ...


@overload
def resolve(
    model: DiffModel,
    **kwargs: Any,
) -> DatabooksBase:
    ...


@overload
def resolve(
    model: BaseCells,
    **kwargs: Any,
) -> List[T]:
    ...


def resolve(
    model: DiffModel | BaseCells,
    *,
    keep_first: bool = True,
    ignore_none: bool = True,
    **kwargs: Any,
) -> DatabooksBase | List[T]:
    """
    Resolve differences for 'diff models'.

    Return instance alike the parent class `databooks.data_models.Cell.DatabooksBase`.
    :param model: DiffModel that is to be resolved (self when added as a method to a
     class
    :param keep_first: Whether to keep the information from the prior in the
     'diff model' or the later
    :param ignore_none: Whether or not to ignore `None` values if encountered, and
     use the other field value
    :return: Model with selected fields from the differences
    """
    field_d = dict(model)
    is_diff = field_d.pop("is_diff")
    if not is_diff:
        raise TypeError("Can only resolve dynamic 'diff models' (when `is_diff=True`).")

    res_vals: Dict[str, Any] = {}
    for name, value in field_d.items():
        if isinstance(value, (DiffModel, BaseCells)):
            res_vals[name] = value.resolve(
                keep_first=keep_first, ignore_none=ignore_none, **kwargs
            )
        else:
            res_vals[name] = (
                value[keep_first]
                if value[not keep_first] is None and ignore_none
                else value[not keep_first]
            )

    return type(model).mro()[1](**res_vals)


class DatabooksBase(BaseModel):
    """Base Pydantic class with extras on managing fields."""

    class Config:
        """Default configuration for base class."""

        extra = Extra.allow

    def remove_fields(
        self,
        fields: Iterable[str],
        *,
        recursive: bool = False,
        missing_ok: bool = False,
    ) -> None:
        """
        Remove selected fields.

        :param fields: Fields to remove
        :param recursive: Whether or not to remove the fields recursively in case of
         nested models
        :return:
        """
        d_model = dict(self)
        for field in fields:
            field_val = d_model.get(field) if missing_ok else d_model[field]
            if recursive and isinstance(field_val, DatabooksBase):
                field_val.remove_fields(fields)
            elif field in d_model:
                delattr(self, field)

    def __str__(self) -> str:
        """Return outputs of __repr__."""
        return repr(self)

    def __sub__(self, other: DatabooksBase) -> DiffModel:
        """
        Subtraction between `databooks.data_models.base.DatabooksBase` objects.

        The difference basically return models that replace each fields by a tuple,
         where for each field we have `field = (self_value, other_value)`
        """
        if type(self) != type(other):
            raise TypeError(
                f"Unsupported operand types for `-`: `{type(self).__name__}` and"
                f" `{type(other).__name__}`"
            )

        # Get field and values for each instance
        self_d = dict(self)
        other_d = dict(other)

        # Build dict with {field: (type, value)} for each field
        fields_d: Dict[str, Any] = {}
        for name in self_d.keys() | other_d.keys():
            self_val = self_d.get(name)
            other_val = other_d.get(name)
            if type(self_val) is type(other_val) and all(
                isinstance(val, (DatabooksBase, BaseCells))
                for val in (self_val, other_val)
            ):
                # Recursively get the diffs for nested models
                fields_d[name] = (Any, self_val - other_val)  # type: ignore
            else:
                fields_d[name] = (tuple, (self_val, other_val))

        # Build Pydantic models dynamically
        DiffInstance = create_model(
            "Diff" + type(self).__name__,
            __base__=type(self),
            resolve=resolve,
            is_diff=True,
            **fields_d,
        )
        return cast(DiffModel, DiffInstance())  # it'll be filled in with the defaults
