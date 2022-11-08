"""Configuration functions, and settings objects."""
from pathlib import Path
from typing import Any, Dict, List, Optional

from databooks.common import find_common_parent, find_obj
from databooks.git_utils import get_repo
from databooks.logging import get_logger

TOML_CONFIG_FILE = "pyproject.toml"

ConfigFields = Dict[str, Any]

logger = get_logger(__file__)


def get_config(target_paths: List[Path], config_filename: str) -> Optional[Path]:
    """Find configuration file from CLI target paths."""
    common_path = find_common_parent(paths=target_paths)
    repo = get_repo(common_path)
    repo_dir = getattr(repo, "working_dir", None)

    return find_obj(
        obj_name=config_filename,
        start=Path(repo_dir) if repo_dir is not None else Path(common_path.anchor),
        finish=common_path,
    )
