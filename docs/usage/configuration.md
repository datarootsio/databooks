# Configuration

Instead of passing the same parameters every time when running a command, it is also
possible to set up a configuration that will be read and override the defaults. The order
of priority (from higher priority to lower)

1. User input arguments in the CLI
2. Configuration file
3. Defaults

So it's still possible to override the configuration file via CLI parameters (as expected).

## What can I configure?

All CLI parameters are actually configurable, so you can pass specify anything that is
also available to you via the UI, with one exception: the required `PATHS` argument.
This is because the `PATHS` argument is also used for finding your configuration (see
[how can I use it](#how-can-i-use-it) for more information).

!!! info
    Remember that flags are parsed as boolean values. So you can specify `--verbose` on
    the configuration as `verbose=true`.

## How does it look like?

The configuration file is a `pyproject.toml` file that you can place at the root of your
project. There, you can specify values for either command under the `[tool.databooks.<command>]`.

So if, for example, the desired behavior is

- `databooks meta`
  - Remove outputs
  - Don't remove execution count
  - Always overwrite files
- `databooks fix`
  - Keep notebook metadata from `base` (not `head`)

The `pyproject.toml` file would look like

```toml
[tool.databooks.meta]
rm-outs = true
rm_exec = false
overwrite = true

[tool.databooks.fix]
metadata-head = false
```

## How can I use it?

There are 2 ways to specify the configuration file: explicitly and implicitly. You can
explicitly specify the `pyproject.toml` via the `--config` parameter. If none is specified,
then `databooks` will look for a `pyproject.toml` in your project.

`databooks` will look for the configuration file by first finding the common directory
between all the target paths and from there recursively go to the parent directories
until either finding the configuration file or the root of the git repo. That way, you can
have multiple configuration files and depending on where your notebooks are located the
correct values will be used (think [monorepo](https://en.wikipedia.org/wiki/Monorepo)).

!!! tip
    `databooks` has a `verbose` concept that will print more information to the terminal
    if desired. For debugging purposes one can still increase the verbosity by setting
    and environment variable `LOG_LEVEL` to `DEBUG`. That way, one can get information,
    among many other things, of the configuration file used.
