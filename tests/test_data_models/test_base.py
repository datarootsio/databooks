from typing import cast

from databooks.data_models.base import DatabooksBase, DiffModel


def test_base_sub() -> None:
    """Use the `-` operator and resolve the diffs from the base model."""
    model_1 = DatabooksBase(test=0, foo=1, bar="2")
    model_2 = DatabooksBase(bar=4, foo=2, baz=2.3, test=0)
    diff = cast(DiffModel, model_1 - model_2)
    assert diff.__class__.__name__ == "DiffDatabooksBase"
    assert dict(diff) == {
        "is_diff": True,
        "test": (0, 0),
        "foo": (1, 2),
        "baz": (None, 2.3),
        "bar": ("2", 4),
    }

    assert diff.resolve(keep_first=True, ignore_none=True) == DatabooksBase(
        test=0, foo=1, bar="2", baz=2.3
    )
    assert diff.resolve(keep_first=False, ignore_none=True) == DatabooksBase(
        test=0, foo=2, bar=4, baz=2.3
    )
    assert diff.resolve(keep_first=True, ignore_none=False) == DatabooksBase(
        test=0, foo=1, bar="2", baz=None
    )
