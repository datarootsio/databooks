from pathlib import Path

from databooks.common import find_obj


def test_find_obj(tmp_path: Path) -> None:
    """Find file based on name, and search path."""
    filename = "SAMPLE_FILE.ext"

    start_dir = tmp_path
    end_dir = start_dir / "to" / "some" / "dir"
    end_dir.mkdir(parents=True)
    (start_dir / "to" / filename).touch()

    filepath = find_obj(obj_name=filename, start=start_dir, finish=end_dir)
    assert filepath == start_dir / "to" / filename
    assert filepath.is_file()


def test_find_obj__missing(tmp_path: Path) -> None:
    """Return `None` when looking for file along path."""
    filename = "SAMPLE_FILE.ext"

    start_dir = tmp_path
    end_dir = start_dir / "to" / "some" / "dir"
    end_dir.mkdir(parents=True)

    filepath = find_obj(obj_name=filename, start=start_dir, finish=end_dir)
    assert filepath is None
