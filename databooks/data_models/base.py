"""Data models - Base Pydantic model with custom methods"""
from __future__ import annotations

from typing import Iterable, Tuple

from pydantic import BaseModel, Extra, create_model
from pydantic.generics import GenericModel

T = TypeVar("T")


class DiffModel(Protocol, Iterable):
    """Protocol for mypy static type checking"""

    is_diff: bool


def resolve(
    model: DiffModel, *, keep_first: bool = True, ignore_none: bool = True
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
    if not (hasattr(model, "is_diff") and model.is_diff):
        raise TypeError("Can only resolve 'diff models' (when `is_diff=True`).")

    field_vals = {
        field: value[not keep_first]
        if value[not keep_first] is not None and ignore_none
        else value[keep_first]
        for field, value in model
        if field != "is_diff"
    }

    field_vals["is_diff"] = False

    return model.__class__.__bases__[0](**field_vals)


class BaseModelWithExtras(BaseModel):
    """Base Pydantic class with extras on managing fields."""

    class Config:
        extra = Extra.allow

    def remove_fields(self, fields: Iterable[str], *, recursive: bool = False) -> None:
        """
        Remove selected fields
        :param fields: Fields to remove
        :param recursive: Whether or not to remove the fields recursively in case of
         nested models
        :return:
        """
        for field in fields:
            if recursive and isinstance(getattr(self, field), BaseModelWithExtras):
                getattr(self, field).remove_fields(fields)
            else:
                delattr(self, field)

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
