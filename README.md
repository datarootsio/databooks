<img align="left" style="padding: 10px" width="120" height="120" src="https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/logo.png?token=AKUGIEI3HBAW32EUFUD5AT3BXT6BC">

# databooks
[![maintained by dataroots](https://dataroots.io/maintained.svg)](https://dataroots.io)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Codecov](https://codecov.io/github/datarootsio/databooks/badge.svg?branch=main&service=github)](https://github.com/datarootsio/databooks/actions)
[![tests](https://github.com/datarootsio/databooks/workflows/test/badge.svg?branch=main)](https://github.com/datarootsio/databooks/actions)


`databooks` is a package for reducing the friction data scientists while using [Jupyter
notebooks](https://jupyter.org/), by reducing the number of git conflicts between
different notebooks and assisting in the resolution of the conflicts.

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

## Installation

```
pip install --i https://test.pypi.org/simple/ databooks
```

## Usage

### Clear metadata

Simply specify the paths for notebook files to remove metadata. By doing so, we can 
already avoid many of the conflicts.

```console
$ databooks meta [OPTIONS] PATHS...
```

![databooks meta demo](https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/databooks-meta.gif?token=AKUGIEOHIY4XVJK2IRRMNRLBYJBEQ)

### Fix git conflicts for notebooks

Specify the paths for notebook files with conflicts to be fixed. Then, `databooks` finds
the source notebooks that caused the conflicts and compares them (so no JSON manipulation!)

```console
$ databooks fix [OPTIONS] PATHS...
```

![databooks fix demo](https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/databooks-fix.gif?token=AKUGIELRRMXJMU7RSUUGYUDBYJD5G)

## License

This project is licensed under the terms of the MIT license.
