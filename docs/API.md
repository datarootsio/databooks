# Overview

Though `databooks` was built to be used as a CLI application, you could also use the
databooks data models to manipulate notebooks in other scripts.

All the data models are based on [Pydantic models](https://pydantic-docs.helpmanual.io/usage/models/).
That means that we have a convenient way to read/write notebooks (JSON files) and ensure
that the JSON is actually a valid notebook.

By using databooks to parse your notebooks, you can also count on IDE support.

Using databooks in python scripts is as simple as

```python3
from databooks import JupyterNotebook

notebook = JupyterNotebook.parse_file(path="path/to/your/notebook")
assert list(dict(notebook).keys()) == ['nbformat', 'nbformat_minor', 'metadata', 'cells']
```

For more information on the internal workings and what is implemented, see [how it works]().
