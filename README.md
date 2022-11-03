<p align="center">
  <a href="https://datarootsio.github.io/databooks/"><img alt="logo" src="https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/logo.png"></a>
</p>
<p align="center">
  <a href="https://dataroots.io"><img alt="Maintained by dataroots" src="https://dataroots.io/maintained-rnd.svg" /></a>
  <a href="https://pypi.org/project/databooks/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/databooks" /></a>
  <a href="https://pypi.org/project/databooks/"><img alt="PiPy" src="https://img.shields.io/pypi/v/databooks" /></a>
  <a href="https://pepy.tech/project/databooks"><img alt="Downloads" src="https://pepy.tech/badge/databooks" /></a>
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg" /></a>
  <a href="http://mypy-lang.org/"><img alt="Mypy checked" src="https://img.shields.io/badge/mypy-checked-1f5082.svg" /></a>
  <a href="https://pepy.tech/project/databooks"><img alt="Codecov" src="https://codecov.io/github/datarootsio/databooks/main/graph/badge.svg" /></a>
  <a href="https://github.com/datarootsio/databooks/actions"><img alt="test" src="https://github.com/datarootsio/databooks/actions/workflows/test.yml/badge.svg" /></a>
</p>


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

- Python 3.7+
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

### Assert notebook metadata

Specify paths of notebooks to be checked, an expression or recipe of what you'd like to
enforce. `databooks` will run your checks and raise errors if any notebook does not
comply with the desired metadata values. This advanced feature allows users to enforce
cell tags, sequential cell execution, maximum number of cells, among many other things!

Check out our [docs](https://databooks.dev/latest/usage/overview/#databooks-assert) for more!

```console
$ databooks assert [OPTIONS] PATHS...
```

![databooks assert demo](https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/databooks-assert.gif)

### Show rich notebook

Instead of launching Jupyter and opening the browser to inspect notebooks, have a quick
look at them in the terminal. All you need is to specify the path(s) of the notebook(s).

```console
$ databooks show [OPTIONS] PATHS...
```

![databooks show demo](https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/databooks-show.gif)

### Show rich notebook diffs

Similar to git diff, but for notebooks! Show a rich diff of the notebooks in the
terminal. Works for comparing git index with the current working directory, comparing
branches or blobs.

```console
$ databooks diff [OPTIONS] [REF_BASE] [REF_REMOTE] [PATHS]...
```

![databooks diff demo](https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/databooks-diff.gif)

## License

This project is licensed under the terms of the MIT license.
