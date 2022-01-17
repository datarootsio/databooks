"""Enable CLI to be called as a Python module (`python -m databooks ...`)."""
from databooks.cli import app

app(prog_name="databooks")
