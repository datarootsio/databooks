"""Terminal user interface (TUI) helper functions and components."""
from rich.console import Console
from rich.theme import Theme

DATABOOKS_TUI = Theme({"in_count": "blue", "out_count": "orange3", "error": "on red"})

databooks_console = Console(theme=DATABOOKS_TUI)
