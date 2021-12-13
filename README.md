<img align="left" style="padding: 10px" width="120" height="120" src="https://raw.githubusercontent.com/datarootsio/databooks/main/docs/images/logo.png?token=AKUGIEI3HBAW32EUFUD5AT3BXT6BC">

# databooks
[![maintained by dataroots](https://img.shields.io/badge/maintained%20by-dataroots-38b580?style=flat-square&link=https://github.com/datarootsio&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAANCAMAAACXZR4WAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAABlVBMVEUAAAAAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYgAsYj///9qxc/YAAAAhXRSTlMAABEYAgAAGqbSk04aAgloaSoGHbH++/raXQqF+P/ptMXIVHrGqgQOi/rmtOH9yyss6dMZmPvjTwUfhpwADMTxPbp0NfLGDRK+bYKFGNjwbCIXm/3dRU34uhEEbvP94s782kIk3vrEfoXz8Jav59U8CH/X+u5mAwYoYDMCGEuQw18CAg8DU/ll7AAAAAFiS0dEhozeO10AAAAJcEhZcwAACxIAAAsSAdLdfvwAAAAHdElNRQflDAoJHymgKYCJAAAAxklEQVQI12NggABGRiZmFkYom5WNkZGRnYOTi5uHFyjGyMcvICgkLCIq1iouIcnIwCglLSMrJ6/QqqikrNKqqsagrqGppa2j26qnz8hoYGhkzGBiamZuYWnVam3DyGhrZ+/A4NjqBDTS2cXVjZHR3aPVk8Gr1Rso4OPr5x8QGBQcEsoQFh4RyRgVHdMaGxefkJjEyJCckpqWnpGZlZ2T25qXz8jIUFBYVNzaWlJaVl5RWcUIcld1TW1dfUMj1NkQtzc1t8D5AMHbKKfw3g4nAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDIxLTEyLTEwVDA5OjMxOjQxLTA1OjAwv87lcAAAACV0RVh0ZGF0ZTptb2RpZnkAMjAyMS0xMi0xMFQwOTozMTo0MS0wNTowMM6TXcwAAAAASUVORK5CYII=)](https://dataroots.io)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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
pip install databooks
```

## Usage

### Clear metadata

Simply specify the paths for notebook files to remove metadata. By doing so, we can 
already avoid many of the conflicts.

```console
$ databooks meta [OPTIONS] PATHS...
```

<video controls>
  <source src="docs/images/databooks_meta.mov" type="video/quicktime">
  Embedded videos not supported by the browser.
</video>

### Fix git conflicts for notebooks

Specify the paths for notebook files with conflicts to be fixed. Then, `databooks` finds
the source notebooks that caused the conflicts and compares them (so no JSON manipulation!)

```console
$ databooks fix [OPTIONS] PATHS...
```

<video controls>
  <source src="docs/images/databooks_fix.mov" type="video/quicktime">
  Embedded videos not supported by the browser.
</video>

## License

This project is licensed under the terms of the MIT license.