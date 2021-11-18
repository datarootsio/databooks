"""Data models - Base Pydantic model with custom methods"""
from __future__ import annotations

from collections import UserList
from collections.abc import Generator, Iterable, MutableSequence, Sequence
from difflib import SequenceMatcher
from typing import Any, Callable, Generic, Optional, Protocol, TypeVar, cast

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
            raise TypeError(
                f"Unsupported operand types for `-`: `{type(self).__name__}` and"
                f" `{type(other).__name__}`"
            )

        # Get field and values for each instance
        self_d = dict(self)
        other_d = dict(other)

        # Build dict with {field: (type, value)} for each field
        fields_d = {}
        for name in self_d.keys() | other_d.keys():
            self_val = self_d.get(name)
            other_val = other_d.get(name)
            if type(self_val) is type(other_val) and all(
                isinstance(val, (BaseModelWithExtras, DiffList))
                for val in (self_val, other_val)
            ):
                # Recursively get the diffs for nested models
                fields_d[name] = (Any, self_val - other_val)  # type: ignore
            else:
                fields_d[name] = (tuple, (self_val, other_val))

        # Build Pydantic models dynamically
        DiffModel = create_model(
            "Diff" + self.__class__.__name__,
            __base__=self.__class__,
            resolve=resolve,
            is_diff=True,
            **cast(dict[str, Any], fields_d),
        )
        return DiffModel()


class DiffList(GenericModel, UserList[T], Generic[T]):
    """Similar to `list`, with `-` operator using `difflib.SequenceMatcher`"""

    __root__: list[T] = []

    def __init__(self, elements: Sequence[T] = ()) -> None:
        """Allow passing data as a positional argument when instantiating class"""
        super(DiffList, self).__init__(__root__=elements)

    @property
    def data(self) -> list[T]:  # type: ignore
        """Define property `data` required for `collections.UserList` class"""
        return self.__root__

    def __iter__(self) -> Generator[Any, None, None]:
        """Use list property as iterable"""
        return (el for el in self.data)

    def __sub__(
        self, other: UserList[Any]
    ) -> list[tuple[Optional[MutableSequence[Any]], ...]]:
        """Return the difference using `difflib.SequenceMatcher`"""
        if type(self) != type(other):
            raise TypeError(
                f"Unsupported operand types for `-`: `{type(self).__name__}` and"
                f" `{type(other).__name__}`"
            )
        s = SequenceMatcher(isjunk=None, a=self, b=other)
        pairs = [(self[i1:j1], other[i2:j2]) for _, i1, j1, i2, j2 in s.get_opcodes()]
        return [tuple(el if len(el) > 0 else None for el in pair) for pair in pairs]

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, v: list[T]) -> DiffList[T]:
        if not isinstance(v, cls):
            return cls(v)
        else:
            return v
