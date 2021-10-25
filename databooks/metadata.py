import json

from databooks.common import FilePath
from databooks.data_models import JupyterNotebook


def clear(
    read_path: FilePath,
    write_path: FilePath = None,
    notebook=True,
    cells=True,
    **cell_kwargs
) -> None:
    if write_path is None:
        write_path = read_path
    nb = JupyterNotebook.parse_file(read_path, content_type="json")
    nb.clear_metadata(notebook=notebook, cells=cells, **cell_kwargs)
    clean_nb = nb.dict(
        # include={"metadata", "nbformat", "nbformat_minor", "cells"},
        exclude_none=True
    )
    with open(write_path, "w") as out_file:
        json.dump(clean_nb, fp=out_file, indent=2)
