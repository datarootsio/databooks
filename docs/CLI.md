---
hide:
  - navigation
---

# `databooks`

Databooks - set of helpers to ease collaboration of data scientists
 using Jupyter Notebooks. Easily resolve git conflicts and remove metadata to reduce
 the number of conflicts.

**Usage**:

```console
$ databooks [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--version`
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `diff`: Show differences between notebooks (not...
* `fix`: Fix git conflicts for notebooks by getting...
* `meta`: Clear both notebook and cell metadata

## `databooks diff`

Show differences between notebooks (not implemented)

**Usage**:

```console
$ databooks diff [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `databooks fix`

Fix git conflicts for notebooks by getting unmerged blobs from git index
 comparing them and returning a valid notebook with the differences -
 see [git docs](https://git-scm.com/docs/git-ls-files)

**Usage**:

```console
$ databooks fix [OPTIONS] PATHS...
```

**Arguments**:

* `PATHS...`: Path(s) of notebook files with conflicts  [required]

**Options**:

* `--ignore TEXT`: Glob expression(s) of files to ignore  [default: !*]
* `--metadata-first / --no-metadata-first`: Whether or not to keep the metadata from the first/current notebook  [default: True]
* `--cells-first / --no-cells-first`: Whether to keep the cells from the first or last notebook. Omit to keep both
* `-i, --interactive`: Interactively resolve the conflicts (not implemented)  [default: False]
* `--verbose / --no-verbose`: Log processed files in console  [default: False]
* `--help`: Show this message and exit.

## `databooks meta`

Clear both notebook and cell metadata

**Usage**:

```console
$ databooks meta [OPTIONS] PATHS...
```

**Arguments**:

* `PATHS...`: Path(s) of notebook files  [required]

**Options**:

* `--ignore TEXT`: Glob expression(s) of files to ignore  [default: !*]
* `--prefix TEXT`: Prefix to add to filepath when writing files  [default: ]
* `--suffix TEXT`: Suffix to add to filepath when writing files  [default: ]
* `--rm-outs / --no-rm-outs`: Whether to remove cell outputs  [default: False]
* `--rm-exec / --no-rm-exec`: Whether to remove the cell execution counts  [default: True]
* `--nb-meta-keep TEXT`: Notebook metadata fields to keep  [default: ]
* `--cell-meta-keep TEXT`: Cells metadata fields to keep  [default: ]
* `-w, --overwrite`: Confirm overwrite of files  [default: False]
* `--check`: Don't write files but check whether there is unwanted metadata  [default: False]
* `-v, --verbose`: Log processed files in console  [default: False]
* `--help`: Show this message and exit.
