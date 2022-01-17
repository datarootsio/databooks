<img alt="logo" width="120" height="120" src="https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/logo.png">

# databooks
[![maintained by dataroots](https://dataroots.io/maintained-rnd.svg)](https://dataroots.io)
[![PyPI](https://img.shields.io/pypi/v/databooks)](https://pypi.org/project/databooks/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-1f5082.svg)](http://mypy-lang.org/)
[![Codecov](https://codecov.io/github/datarootsio/databooks/main/graph/badge.svg)](https://github.com/datarootsio/databooks/actions)
[![tests](https://github.com/datarootsio/databooks/actions/workflows/test.yml/badge.svg)](https://github.com/datarootsio/databooks/actions)
[![Downloads](https://pepy.tech/badge/databooks)](https://pepy.tech/project/databooks)


`databooks` is a package to ease the collaboration between data scientists using
[Jupyter notebooks](https://jupyter.org/), by reducing the number of git conflicts between
different notebooks and resolution of git conflicts when encountered.

The key features include:

- CLI tool
  - Clear notebook metadata
  - Resolve git conflicts
- Simple to use
- Simple API for using modelling and comparing notebooks using [Pydantic](https://pydantic-docs.helpmanual.io/)

## Requirements

`databooks` is built on top of:

- Python 3.8+
- [Typer](https://typer.tiangolo.com/)
- [Rich](https://rich.readthedocs.io/en/latest/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [GitPython](https://gitpython.readthedocs.io/en/stable/tutorial.html)
- [Tomli](https://github.com/hukkin/tomli)

## Installation

```
pip install databooks
```

## Usage

### Clear metadata

Simply specify the paths for notebook files to remove metadata. By doing so, we can 
already avoid many of the conflicts.

```console
$ databooks meta [OPTIONS] PATHS...
```

![databooks meta demo](https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/databooks-meta.gif)

### Fix git conflicts for notebooks

Specify the paths for notebook files with conflicts to be fixed. Then, `databooks` finds
the source notebooks that caused the conflicts and compares them (so no JSON manipulation!)

```console
$ databooks fix [OPTIONS] PATHS...
```

![databooks fix demo](https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/databooks-fix.gif)

## License

This project is licensed under the terms of the MIT license.
