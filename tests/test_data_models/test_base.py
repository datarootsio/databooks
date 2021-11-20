"""Test base data models and components"""
from databooks.data_models.base import BaseModelWithExtras


def test_base_sub() -> None:
    """Use the `-` operator and resolve the diffs from the base model"""
    model_1 = BaseModelWithExtras(test=0, foo=1, bar="2")
    model_2 = BaseModelWithExtras(bar=4, foo=2, baz=2.3, test=0)
    diff = model_1 - model_2
    assert diff.__class__.__name__ == "DiffBaseModelWithExtras"
    assert diff.dict() == {
        "is_diff": True,
        "test": (0, 0),
        "foo": (1, 2),
        "baz": (None, 2.3),
        "bar": ("2", 4),
    }

    assert diff.resolve(keep_first=True, ignore_none=True) == BaseModelWithExtras(
        is_diff=False, test=0, foo=1, bar="2", baz=2.3
    )
    assert diff.resolve(keep_first=False, ignore_none=True) == BaseModelWithExtras(
        is_diff=False, test=0, foo=2, bar=4, baz=2.3
    )
    assert diff.resolve(keep_first=True, ignore_none=False) == BaseModelWithExtras(
        is_diff=False, test=0, foo=1, bar="2", baz=None
    )
