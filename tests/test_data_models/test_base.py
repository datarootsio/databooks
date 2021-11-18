"""Test base data models and components"""
from databooks.data_models.base import BaseModelWithExtras, DiffList


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

    assert diff.resolve(keep_first=True) == BaseModelWithExtras(  # type: ignore
        is_diff=False, test=0, foo=1, bar="2", baz=2.3
    )


def test_difflists() -> None:
    """Test cell type"""
    dl1 = DiffList((2, 1, 2, 3))
    dl2 = DiffList((1, 2, 3, 4))

    diff = dl1 - dl2
    assert diff == [
        (DiffList([2]), None),
        (DiffList([1, 2, 3]), DiffList([1, 2, 3])),
        (None, DiffList([4])),
    ]
