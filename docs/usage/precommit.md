# Pre-commit hooks

Another alternative is to try to catch code quality issues before any code is even sent
to the remote git repo. `Pre-commit hooks` are essentially actions that are taken right
before code is committed to your (local) repo.

[![Pre-commit illustrated](https://ljvmiranda921.github.io/assets/png/tuts/precommit_pipeline.png)](https://ljvmiranda921.github.io/notebook/2018/06/21/precommits-using-black-and-flake8/)

## `Pre-commit` package

There are different ways to create new hooks to your git repo. [`pre-commit`](https://pre-commit.com/)
is a package to easily config pre-commit hooks, and store them in a very readable manner.

### Installation

To install, simply run:

```bash
pip install pre-commit
```

## Usage

### Configuration

#### `databooks meta`

To use `pre-commit` with `databooks meta`, create a `.pre-commit-config.yaml` in the root of your project.
There, include

```yaml
repos:
-   repo: https://github.com/datarootsio/databooks
    rev: 1.0.1
    hooks:
    -   id: databooks-meta
```

[`databooks` repo](https://github.com/datarootsio/databooks) has minimal configuration
(such as the `meta` command). The `rev` parameter indicates the version to use and `args`
indicate additional arguments to pass to the tool.

The `pre-commit` tool doesn't actually commit any changes if the staged files are modified.
Therefore, if there **is** any unwanted metadata at the time of committing the changes,
the files would be modified, no commit would be made, and it'd be up to the developer to
inspect the changes, add them and commit. That's why we specify `args: ["--overwrite"]`
by default.

#### `databooks assert`

To use `databooks assert` you must pass similar values, added with an `args` field to
write your checks. Those can be a `recipe` or an `expression`, similarly to what would
be done via the CLI. The difference here is that we pass an "extra check" that evaluates
to `True` (namely `databooks assert --expr "True"`) to allow a user to commit in case
there are no tests in the configuration file.

```yaml
repos:
-   repo: https://github.com/datarootsio/databooks
    rev: 1.0.1
    hooks:
    -   id: databooks-assert
        args: ['--expr', 'len(nb.cells) < 10', '--recipe', 'seq-exec']
```

### Running

Once the configuration is in place all the user needs to do to trigger `pre-commit` is
to commit changes normally

```bash
$ git add path/to/notebook.ipynb
$ git commit -m 'a clear message'
databooks-assert.........................................................Failed
- hook id: databooks-assert
- exit code: 1

[12:24:10] INFO     path/to/notebook.ipynb failed 0 of 3 checks.  affirm.py:214
  Running assert checks ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
           INFO     Found issues in notebook metadata for 1 out of 1  cli.py:257
                    notebooks.

databooks-meta...........................................................Failed
- hook id: databooks-meta
- files were modified by this hook

[23:24:11] WARNING  1 files will be overwritten                       cli.py:149
  Removing metadata ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
           INFO     The metadata of 1 out of 1 notebooks were         cli.py:185
                    removed!
```

Alternatively, one could run `pre-commit run` to manually run the same command that is
triggered right before committing changes. Or, one could run `pre-commit run --all-files`
to run the pre-commit hooks in all files (regardless if the files have been staged or not).
The latter is useful as a first-run to ensure consistency across the git repo or in CI.
