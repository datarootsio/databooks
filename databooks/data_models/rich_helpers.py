"""Rich helpers functions for rich renderables in data models."""
from html.parser import HTMLParser
from typing import Any, List, Optional, Tuple

from rich import box
from rich.table import Table

HtmlAttr = Tuple[str, Optional[str]]


class RichHtmlTableError(Exception):
    """Could not parse HTML table."""

    def __init__(self, msg: str = "", *args: Any):
        """Use class docstring as error 'prefix'."""
        if self.__doc__ is None:
            raise ValueError("Exception docstring required - used in error message.")
        super().__init__(" ".join((self.__doc__, msg)), *args)


class HtmlTable(HTMLParser):
    """Rich table from HTML string."""

    def __init__(self, html: str, *args: Any, **kwargs: Any) -> None:
        """Initialize parser."""
        super().__init__(*args, **kwargs)
        self.table = self.thead = self.tbody = self.body = self.th = self.td = False
        self.headers: List[str] = []
        self.row: List[str] = []
        self.rows: List[List[str]] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: List[HtmlAttr]) -> None:
        """Active tags are indicated via instance boolean properties."""
        if getattr(self, tag, None):
            raise RichHtmlTableError(f"Already in `{tag}`.")
        setattr(self, tag, True)

    def handle_endtag(self, tag: str) -> None:
        """Write table properties when closing tags."""
        if not getattr(self, tag):
            raise RichHtmlTableError(f"Cannot end unopened `{tag}`.")

        # If we are ending a row, either set a table header or row
        if tag == "tr":
            if self.thead:
                self.headers = self.row
            if self.tbody:
                self.rows.append(self.row)
            self.row = []  # restart row values
        setattr(self, tag, False)

    def handle_data(self, data: str) -> None:
        """Append data depending on active tags."""
        if self.table and (self.th or self.td):
            self.row.append(data)

    def rich(self, **tbl_kwargs: Any) -> Optional[Table]:
        """Generate `rich` representation of table."""
        if not self.rows and not self.headers:  # HTML is not a table
            return None

        _ncols = len(self.rows[0])
        _headers = [""] * (_ncols - len(self.headers)) + self.headers
        if any(len(row) != _ncols for row in self.rows):
            raise RichHtmlTableError(f"Expected all rows to have {_ncols} columns.")

        _box = tbl_kwargs.pop("box", box.SIMPLE_HEAVY)
        _row_styles = tbl_kwargs.pop("row_styles", ["on bright_black", ""])

        table = Table(*_headers, box=_box, row_styles=_row_styles, **tbl_kwargs)
        for row in self.rows:
            table.add_row(*row)
        return table
