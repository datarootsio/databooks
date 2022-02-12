from pathlib import Path

from py._path.local import LocalPath

from databooks.common import find_obj, get_keys


def test_find_obj(tmpdir: LocalPath) -> None:
    """Find file based on name, and search path."""
    filename = "SAMPLE_FILE.ext"

    start_dir = Path(tmpdir)
    end_dir = start_dir / "to" / "some" / "dir"
    end_dir.mkdir(parents=True)
    (start_dir / "to" / filename).touch()

    filepath = find_obj(obj_name=filename, start=start_dir, finish=end_dir)
    assert filepath == start_dir / "to" / filename
    assert filepath.is_file()


def test_find_obj__missing(tmpdir: LocalPath) -> None:
    """Return `None` when looking for file along path."""
    filename = "SAMPLE_FILE.ext"

    start_dir = Path(tmpdir)
    end_dir = start_dir / "to" / "some" / "dir"
    end_dir.mkdir(parents=True)

    filepath = find_obj(obj_name=filename, start=start_dir, finish=end_dir)
    assert filepath is None


def test_get_keys() -> None:
    """Get keys from neted dictionary."""
    assert get_keys({"a": 1, "b": {"c": 2, "d": {"e": 3}}}) == {"a", "b", "c", "d", "e"}
