# Alternatives and comparisons
There are many tools to improve the development experience with notebooks. `databooks`
also takes inspiration from other existing packages.

## `nb-clean`
[`nb-clean`](https://github.com/srstevenson/nb-clean) provides a CLI tool to clear
notebook metadata from Jupyter notebooks.

**Differences:** `nb-clean` does not offer a way to resolve conflicts.

## `nbdime`
[`nbdime`](https://github.com/jupyter/nbdime) stands for "notebook diff and merge".
It offers a way to compare and display the differences in the terminal. It offers a way
to gracefully merge notebooks.

**Differences:** `nb-dime` does not offer a way to remove metadata. `databooks` also
fixes git merge conflicts instead of offering a way to do git merges ("ask for forgiveness
not permission").

## `nbdev`
[`nbdev`](https://github.com/fastai/nbdev) offers a way to use notebooks to develop
python packages, converting notebooks to python scripts and documentation. Also offers
installation of pre-commit hooks to remove notebook metadata and a way to resolve git
conflicts.

**Differences:** `nbdev` is closer to an opinionated template for developing packages
with notebooks. `databooks` is a configurable CLI tool for metadata removal and conflict
resolution.
