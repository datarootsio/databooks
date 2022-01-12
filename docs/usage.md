---
hide:
  - navigation
---

# Usage

`databooks` is a CLI tool, but there are many different ways in which one can make use
of the tool - such as CI or hooks.

## CLI tool

The most straightforward way is to use it in the terminal, whenever desired. That can be
error-prone and have "dirty" notebooks in your git repo. Check [CLI documentation](../CLI)
for more information.

A safer alternative is to automate this step, by setting up CI in your repo or a pre-commit hook.

## GitHub Actions

[GitHub Actions](https://github.com/features/actions) are a GitHub-hosted solution for
CI/CD. All you need to get started is a file in `project_root/.github/workflows/nb-meta.yml`.

An example workflow to clean any notebook metadata and commit changes at every push:

```yml
name: 'nb-meta'
on: [push]

jobs:
  nb-meta:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Configure git user
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
      - name: Install dependencies and clean metadata
        run: |
          pip install databooks
          databooks meta . --overwrite
      - name: Commit changes and push
        run: |
          git commit -am "Automated commit - clean notebook metadata"
          git push
```

Alternatively, one can choose to avoid having CI systems making code changes. In that
case, we can only check whether notebooks have any undesired metadata.

```yml
name: 'nb-meta'
on: [push]

jobs:
  nb-meta:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies and check metadata
        run: |
          pip install databooks
          databooks meta . --check
```