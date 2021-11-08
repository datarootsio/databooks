import json

from databooks.common import FilePath
from databooks.data_models import JupyterNotebook


def clear(
    read_path: FilePath, write_path: FilePath = None, notebook=True, **cell_kwargs
) -> None:
    if write_path is None:
        write_path = read_path
    nb = JupyterNotebook.parse_file(read_path, content_type="json")
    nb.clear_metadata(notebook_metadata=notebook, **cell_kwargs)
    with open(write_path, "w") as out_file:
        json.dump(nb.dict(), fp=out_file, indent=2)
