from pathlib import Path

from py._path.local import LocalPath

from databooks.config import _find_file


def test__find_file(tmpdir: LocalPath) -> None:
    """Find file based on name, and search path."""
    filename = "SAMPLE_FILE.ext"

    start_dir = Path(tmpdir)
    end_dir = start_dir / "to" / "some" / "dir"
    end_dir.mkdir(parents=True)
    (start_dir / "to" / filename).touch()

    filepath = _find_file(filename=filename, start=start_dir, finish=end_dir)
    assert filepath == start_dir / "to" / filename
    assert filepath.is_file()
