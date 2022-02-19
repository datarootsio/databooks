# CI/CD

CI/CD essentially runs some code in a remote server, triggered by git events. In these
runs, one could trigger other events or simply check whether the code is up to standards.
This is a nice way to make sure that all the code that is in your git repo passes all
quality checks.

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
