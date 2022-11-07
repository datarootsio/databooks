"""Test data models for notebook components."""
import json
import logging
from copy import deepcopy
from importlib import resources
from pathlib import Path
from typing import List, Tuple

import pytest
from _pytest.logging import LogCaptureFixture

from databooks.data_models.cell import (
    CellMetadata,
    CellOutputs,
    CodeCell,
    MarkdownCell,
    RawCell,
)
from databooks.data_models.notebook import (
    Cell,
    Cells,
    JupyterNotebook,
    NotebookMetadata,
)


class TestNotebookMetadata:
    """Tests related to notebook metadata fields."""

    @property
    def notebook_metadata(self) -> NotebookMetadata:
        """`NotebookMetadata` property to test on."""
        return NotebookMetadata(
            kernelspec=dict(display_name="kernel_display_name", name="kernel_name"),
            field_to_remove="Field to remove",
            tags=[],
        )

    def test_remove_fields__missing_ok(self) -> None:
        """Remove fields specified from NotebookMetadata model (ignore if missing)."""
        metadata = deepcopy(self.notebook_metadata)
        assert hasattr(metadata, "field_to_remove")
        extra_fields = [
            field for field, _ in metadata if field not in metadata.__fields__
        ]

        with pytest.raises(KeyError):
            metadata.remove_fields(["missing_field"], missing_ok=False)

        metadata.remove_fields(["missing_field"], missing_ok=True)
        metadata.remove_fields(extra_fields, missing_ok=True)

        assert not hasattr(metadata, "field_to_remove")

    def test_remove_fields(self) -> None:
        """Remove fields specified from NotebookMetadata model."""
        metadata = deepcopy(self.notebook_metadata)
        assert hasattr(metadata, "field_to_remove")
        assert hasattr(metadata, "tags")
        extra_fields = [
            field for field, _ in metadata if field not in metadata.__fields__
        ]
        metadata.remove_fields(extra_fields)
        assert not hasattr(metadata, "field_to_remove")
        assert not hasattr(metadata, "tags")


class TestCell:
    """Tests related to notebook cell fields."""

    @property
    def cell_metadata(self) -> CellMetadata:
        """`CellMetadata` property to test on."""
        return CellMetadata(field_to_remove="Field to remove")

    @property
    def cell(self) -> CodeCell:
        """`CodeCell` property to test on."""
        return CodeCell(
            cell_type="code",
            metadata=self.cell_metadata,
            source=["test_source"],
            execution_count=1,
            outputs=[
                {"name": "stdout", "output_type": "stream", "text": ["test text\n"]}
            ],
        )

    def test_cell_metadata(self) -> None:
        """Remove fields specified from `CellMetadata` model."""
        metadata = self.cell_metadata
        extra_fields = [
            field for field, _ in metadata if field not in metadata.__fields__
        ]
        metadata.remove_fields(extra_fields)
        assert metadata.dict() == {}
        assert metadata == CellMetadata()

    def test_clear(self, caplog: LogCaptureFixture) -> None:
        """Remove metadata specified from notebook `CodeCell`."""
        caplog.set_level(logging.DEBUG)

        cell = self.cell

        assert cell.metadata is not None

        cell.clear_fields(
            cell_metadata_keep=[],
            cell_remove_fields=["execution_count", "outputs", "source"],
        )
        logs = list(caplog.records)

        assert cell == CodeCell(
            cell_type="code",
            metadata=CellMetadata(),
            outputs=CellOutputs(__root__=[]),
            source=["test_source"],
            execution_count=None,
        )
        assert len(logs) == 1
        assert logs[0].message == (
            "Ignoring removal of required fields ['source'] in `CodeCell`."
        )

    def test_cells_sub(self) -> None:
        """Get the diff from different `Cells`."""
        dl1 = Cells[Cell]([self.cell])
        dl2 = Cells[Cell]([self.cell] * 2)

        diff = dl1 - dl2

        assert type(dl1) == type(dl2) == Cells[Cell]
        assert type(diff) == Cells[Tuple[List[Cell], List[Cell]]]
        assert diff == Cells(  # type: ignore
            [([self.cell], [self.cell]), ([], [self.cell])]
        )

    def test_cell_remove_fields(self, caplog: LogCaptureFixture) -> None:
        """Test remove fields with logs."""
        caplog.set_level(logging.DEBUG)
        cell = deepcopy(self.cell)
        cell.remove_fields(["cell_type", "outputs"])
        logs = list(caplog.records)

        assert cell.dict() == dict(
            cell_type="code",
            metadata=self.cell_metadata,
            source=["test_source"],
            execution_count=1,
            outputs=[],
        )
        assert len(logs) == 1
        assert logs[0].message == (
            "Ignoring removal of required fields ['cell_type'] in `CodeCell`."
        )


class TestJupyterNotebook(TestNotebookMetadata, TestCell):
    """Tests related to notebooks."""

    @property
    def jupyter_notebook(self) -> JupyterNotebook:
        """`JupyterNotebook` property to test on."""
        return JupyterNotebook(
            metadata=self.notebook_metadata,
            nbformat=4,
            nbformat_minor=4,
            cells=[self.cell] * 2,
        )

    def test_clear_metadata(self) -> None:
        """Remove metadata specified in JupyterNotebook - cells and notebook levels."""
        notebook = self.jupyter_notebook
        notebook.clear_metadata(
            notebook_metadata_keep=[],
            cell_metadata_keep=[],
            cell_remove_fields=["outputs", "execution_count"],
        )

        assert all(cell.metadata == CellMetadata() for cell in notebook.cells)
        assert all(
            cell.outputs == CellOutputs(__root__=[])
            for cell in notebook.cells
            if cell.cell_type == "code"
        )
        assert all(
            cell.execution_count is None
            for cell in notebook.cells
            if cell.cell_type == "code"
        )

    def test_notebook_sub(self) -> None:
        """
        Compute and resolve diffs of notebooks.

        Use the `-` operator and resolve the diffs from the child classes with nested
         models
        """
        notebook_1 = deepcopy(self.jupyter_notebook)
        notebook_2 = deepcopy(self.jupyter_notebook)
        notebook_1.metadata = NotebookMetadata(
            kernelspec=dict(
                display_name="different_kernel_display_name", name="kernel_name"
            ),
            field_to_remove=["Field to remove"],
            another_field_to_remove="another field",
        )
        extra_cell = RawCell(
            cell_type="raw",
            metadata=CellMetadata(random_meta=["meta"]),
            source="extra",
        )
        notebook_2.cells = notebook_2.cells + [extra_cell]

        diff = notebook_1 - notebook_2
        notebook = deepcopy(notebook_1)

        # add `tags` since we resolve with default `ignore_none = True`
        notebook.metadata = NotebookMetadata(
            **notebook_1.metadata.dict(), **{"tags": []}
        )

        assert diff.resolve(keep_first_cells=True) == notebook

        notebook.cells = notebook_2.cells
        assert diff.resolve(keep_first_cells=False) == notebook

        notebook.cells = notebook_1.cells + [
            MarkdownCell(
                metadata=CellMetadata(git_hash=None),
                source=["`<<<<<<< None`"],
                cell_type="markdown",
            ),
            MarkdownCell(
                source=["`=======`"],
                cell_type="markdown",
                metadata=CellMetadata(),
            ),
            extra_cell,
            MarkdownCell(
                metadata=CellMetadata(git_hash=None),
                source=["`>>>>>>> None`"],
                cell_type="markdown",
            ),
        ]
        assert diff.resolve(keep_first_cells=None) == notebook


def test_parse_file() -> None:
    """Deserialize `ipynb` file to `databooks.JupyterNotebook` models."""
    with resources.path("tests.files", "demo.ipynb") as nb_path:
        notebook = JupyterNotebook.parse_file(nb_path)

    assert notebook.nbformat == 4
    assert notebook.nbformat_minor == 5
    assert notebook.metadata == NotebookMetadata(
        kernelspec={
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3",
        },
        language_info={
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        **{
            "toc-showtags": False,
            "toc-showmarkdowntxt": False,
            "toc-showcode": True,
            "toc-autonumbering": False,
        },
    )
    assert notebook.cells == Cells(
        [
            MarkdownCell(
                metadata=CellMetadata(tags=[]),
                source=["# `databooks` demo!"],
                cell_type="markdown",
                id="9adc7c77-95f1-4cb9-b987-1411e28f2976",
            ),
            CodeCell(
                metadata=CellMetadata(tags=["random-tag"]),
                source=["from random import random  # cell with tags"],
                cell_type="code",
                outputs=[],
                execution_count=1,
                id="6a6eafec-a799-455b-8c1b-fd43a0a1f3ca",
            ),
            CodeCell(
                metadata=CellMetadata(tags=[]),
                source=["random()"],
                cell_type="code",
                outputs=[
                    {
                        "data": {"text/plain": ["0.9995123767309688"]},
                        "execution_count": 2,
                        "metadata": {},
                        "output_type": "execute_result",
                    }
                ],
                execution_count=2,
                id="8b852d3e-5482-4feb-8bd1-e902ed6ecaff",
            ),
            CodeCell(
                metadata=CellMetadata(),
                source=['print("notebooks + git ❤️")'],
                cell_type="code",
                outputs=[
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": ["notebooks + git ❤️\n"],
                    }
                ],
                execution_count=3,
                id="4dcb36c4-d671-4ec9-9bff-87857b3f718a",
            ),
            CodeCell(
                metadata=CellMetadata(),
                source=["throw error"],
                cell_type="code",
                outputs=[
                    {
                        "ename": "SyntaxError",
                        "evalue": "invalid syntax (1516912967.py, line 1)",
                        "output_type": "error",
                        "traceback": [
                            '\x1b[0;36m  File \x1b[0;32m"/var/folders/_r/'
                            "_8qwqbqn4_gdj4m3gb6_t0540000gn/T/ipykernel_3501/"
                            '1516912967.py"\x1b[0;36m, line \x1b[0;32m1\x1b[0m\n\x1b'
                            "[0;31m    throw error\x1b[0m\n\x1b[0m"
                            "          ^\x1b[0m\n\x1b[0;31mSyntaxError"
                            "\x1b[0m\x1b[0;31m:\x1b[0m invalid syntax\n"
                        ],
                    }
                ],
                execution_count=4,
                id="53cd4d06-b52e-4fbb-9ae1-d55babe2f3a2",
            ),
            RawCell(
                metadata=CellMetadata(),
                source=["This is a raw cell! 🚀"],
                cell_type="raw",
                id="b2cf154d-0d1d-44d1-9ab8-7ee4b3d37f12",
            ),
        ]
    )


def test_write_file(tmp_path: Path) -> None:
    """Check that serialization and deserialization are valid."""
    write_path = tmp_path / "serialized_demo.ipynb"
    with resources.path("tests.files", "demo.ipynb") as nb_path:
        notebook = JupyterNotebook.parse_file(nb_path)
        in_json_str = nb_path.read_text(encoding="utf-8")

    notebook.write(write_path)
    out_json_str = write_path.read_text(encoding="utf-8")
    assert json.loads(in_json_str) == json.loads(out_json_str)
    assert in_json_str != out_json_str
