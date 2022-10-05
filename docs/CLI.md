---
hide:
  - navigation
---
<!-- [[[cog
import subprocess
import cog

result = subprocess.run(
    [
        "python",
        "-m",
        "typer_cli",
        "databooks.cli",
        "utils",
        "docs",
        "--name",
        "databooks",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding="utf-8",
)
cog.out(result.stdout)
]]] -->
# `databooks`

CLI tool to resolve git conflicts and remove metadata in notebooks.

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

* `assert`: Assert notebook metadata has desired values.
* `diff`: Show differences between notebooks (not...
* `fix`: Fix git conflicts for notebooks.
* `meta`: Clear both notebook and cell metadata.

## `databooks assert`

Assert notebook metadata has desired values.

Pass one (or multiple) strings or recipes. The available variables in scope include
 `nb` (notebook), `raw_cells` (notebook cells of `raw` type), `md_cells` (notebook
 cells of `markdown` type), `code_cells` (notebook cells of `code` type) and
 `exec_cells` (notebook cells of `code` type that were executed - have an `execution
 count` value). Recipes can be found on `databooks.recipes.CookBook`.

**Usage**:

```console
$ databooks assert [OPTIONS] PATHS...
```

**Arguments**:

* `PATHS...`: Path(s) of notebook files  [required]

**Options**:

* `--ignore TEXT`: Glob expression(s) of files to ignore  [default: !*]
* `-x, --expr TEXT`: Expressions to assert on notebooks  [default: ]
* `-r, --recipe [has-tags|has-tags-code|max-cells|no-empty-code|seq-exec|seq-increase|startswith-md]`: Common recipes of expressions - see https://databooks.dev/0.1.15/usage/overview/#recipes  [default: ]
* `-v, --verbose`: Log processed files in console  [default: False]
* `-c, --config PATH`: Get CLI options from configuration file
* `--help`: Show this message and exit

## `databooks diff`

Show differences between notebooks (not implemented).

**Usage**:

```console
$ databooks diff [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `databooks fix`

Fix git conflicts for notebooks.

Perform by getting the unmerged blobs from git index, comparing them and returning
 a valid notebook summarizing the differences - see
 [git docs](https://git-scm.com/docs/git-ls-files).

**Usage**:

```console
$ databooks fix [OPTIONS] PATHS...
```

**Arguments**:

* `PATHS...`: Path(s) of notebook files with conflicts  [required]

**Options**:

* `--ignore TEXT`: Glob expression(s) of files to ignore  [default: !*]
* `--metadata-head / --no-metadata-head`: Whether or not to keep the metadata from the head/current notebook  [default: True]
* `--cells-head / --no-cells-head`: Whether to keep the cells from the head/base notebook. Omit to keep both
* `--cell-fields-ignore TEXT`: Cell fields to remove before comparing cells  [default: id, execution_count]
* `-i, --interactive`: Interactively resolve the conflicts (not implemented)  [default: False]
* `--verbose / --no-verbose`: Log processed files in console  [default: False]
* `-c, --config PATH`: Get CLI options from configuration file
* `--help`: Show this message and exit

## `databooks meta`

Clear both notebook and cell metadata.

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
* `--cell-fields-keep TEXT`: Other (excluding `execution_counts` and `outputs`) cell fields to keep  [default: ]
* `-y, --yes`: Confirm overwrite of files  [default: False]
* `--check`: Don't write files but check whether there is unwanted metadata  [default: False]
* `-v, --verbose`: Log processed files in console  [default: False]
* `-c, --config PATH`: Get CLI options from configuration file
* `--help`: Show this message and exit

<!-- [[[end]]] -->
