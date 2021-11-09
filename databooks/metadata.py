import json

from databooks.common import FilePath
from databooks.data_models import JupyterNotebook


def clear(
    read_path: FilePath,
    write_path: FilePath = None,
    notebook_metadata_keep=(),
    cell_metadata_keep=(),
    **kwargs
) -> None:
    """
    Clear Jupyter Notebook metadata (at notebook and cell level) and write clean
     notebook. By default remove all metadata.
    :param read_path: Path of notebook file with metadata to be cleaned
    :param write_path: Path of notebook file with metadata to be cleaned
    :param notebook_metadata_keep: Notebook metadata fields to keep
    :param cell_metadata_keep: Cell metadata fields to keep
    :param kwargs: Additional keyword arguments to pass to
     `databooks.data_models.JupyterNotebook.clear_metadata`
    :return:
    """
    if write_path is None:
        write_path = read_path
    nb = JupyterNotebook.parse_file(read_path, content_type="json")
    nb.clear_metadata(
        notebook_metadata_keep=notebook_metadata_keep,
        cell_metadata_keep=cell_metadata_keep,
        **kwargs
    )
    with open(write_path, "w") as out_file:
        json.dump(nb.dict(), fp=out_file, indent=2)
