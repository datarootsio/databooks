# Usage

`databooks` is a tool designed to make the life of Jupyter notebook users easier,
especially when it comes to sharing and versioning notebooks. That is because Jupyter
notebooks are actually JSON files, with extra metadata that are useful for Jupyter but
unnecessary for many users. When committing notebooks you commit all the metadata that
may cause some issues down the line. This is where `databooks` comes in.

The package currently has 3 main features, exposed as CLI commands
1. `databooks meta`: to remove unnecessary notebook metadata that can cause git conflicts
2. `databooks fix`: to fix conflicts after they've occurred, by parsing versions of the
conflicting file and computing its difference in a Jupyter-friendly way, so you (user) can
manually resolve them in the Jupyter terminal
3. `databooks assert`: to assert that the notebook metadata actually conforms to desired
values - ensure that notebook has sequential execution count, tags, etc.

## `databooks meta`

The only thing you need to pass is a path. We have sensible defaults to do the rest.

```bash
databooks meta path/to/notebooks
```

With that, for each notebook in the path, by default:

- It will remove execution counts
- It **won't** remove cell outputs
- It will remove metadata from all cells (like cell tags or ids)
- It will remove all metadata from your notebook (including kernel information)
- It **won't** overwrite files for you

Nonetheless, the tool is highly configurable. You could choose to remove cell outputs by
passing `--rm-outs`. Or if there is some metadata you'd like to keep, such as cell tags,
you can do so by passing `--cell-meta-keep tags`. Also, if you do want to save the clean
notebook you can either pass a prefix (`--prefix ...`) or a suffix (`--suffix ...`) that
will be added before writing the file, or you can simply overwrite the source file
(`--overwrite`).

## `databooks fix`

In `datbooks meta` we try to avoid git conflicts. In `databooks fix` we fix conflicts after
they have occurred. Similarly to `databooks meta ...`, the only required argument here
is a path.

```bash
databooks fix path/to/notebooks
```

For each notebook in the path _that has git conflicts_:

- It will keep the metadata from the notebook in [`HEAD`](https://stackoverflow.com/questions/2304087/what-is-head-in-git)
- For the conflicting cells, it will wrap some special cells around the differences, like
in normal git conflicts

Similarly to what we saw above, the default behavior can be changed by passing a
configuration `pyproject.toml` file or specifying the CLI arguments. You could, for
instance, keep the metadata from the notebook in `BASE` (as opposed to `HEAD`). If you
know you only care about the notebook cells in `HEAD` or `BASE`, then you could pass
`--cells-head` or `--no-cells-head` and not worry about fixing conflicted cells in Jupyter.

You can also pass a special `--cell-fields-ignore parameter`, that will remove the cell
metadata from both versions fo the conflicting notebook before comparing them. This is
because depending on your Jupyter version you may have an `id` field, that will be unique
for each cell. That is, all the cells will be considered different even if they have the
same `source` and `outputs` as their `id`s are different. By removing `id` and
`execution_count` (we'll do this by default) we only compare the actual code and outputs
to determine if the cells have changed or not.

!!! note

    If a notebook with conflicts (i.e.: not valid JSON/Jupyter) is committed to the repo,
    `databooks fix` will not consider the file as something to fix - same behavior as `git`.

!!! info "Fun fact"

    "Fix" may be a misnomer: the "broken" JSON in the notebook is not actually fixed -
    instead we compare the versions of the notebook that caused the conflict.

## `databooks assert`

In `databooks meta`, we remove unwanted metadata. But sometimes we may still want some
metadata (such as cell tags), or more than that, we may want the metadata to have
certain values. This is where `databooks assert` comes in. We can use this command to
ensure that the metadata is present and has the desired values.

`databooks assert` is akin (and inspired by) to Python's `assert`. Therefore, the user
must pass a path and a string with the expression to be evaluated for each notebook.

```bash
databooks assert path/to/notebooks --expr "python expression to assert on notebooks"
```

This can be used, for example, to make sure that the notebook cells were executed in
order. Or that we have `markdown` cells, or to set a maximum number of cells for each
notebook.

Evidently, there are some limitations to the expressions that a user can pass.

**Variables in scope:**

All the variables in scope are a subclass of Pydantic models. Therefore, you can use them
as regular python objects (i.e.: to access the cell types, one could write
`[cell.cell_type for cell in nb.cells]`). For convenience, are available the variables
in scope:

- `nb`: Jupyter notebook found in path
- `raw_cells`: notebook cells of raw type
- `md_cells`: notebook cells of markdown type
- `code_cells`: notebook cells of code type
- `exec_cells`: notebook cells of executed code type

**Built-in functions:**
<!-- [[[cog
import ast
from pathlib import Path
import cog

SRC_FILE = Path("databooks/affirm.py")
DOC_TEMPLATE = "- [`{func}`](https://docs.python.org/3/library/functions.html#{func})"

ast_tree = ast.parse(SRC_FILE.read_text("utf-8"))
allowed_builtins_node = next(
    node
    for node in ast.walk(ast_tree)
    if isinstance(node, ast.Assign) and node.targets[0].id == "_ALLOWED_BUILTINS"
)

try:
    allowed_builtins = [func.id for func in allowed_builtins_node.value.elts]
except AttributeError:
    raise ValueError("Could not find assignment of builtins.")

cog.out("\n".join(DOC_TEMPLATE.format(func=func) for func in allowed_builtins))
]]] -->
- [`all`](https://docs.python.org/3/library/functions.html#all)
- [`any`](https://docs.python.org/3/library/functions.html#any)
- [`enumerate`](https://docs.python.org/3/library/functions.html#enumerate)
- [`filter`](https://docs.python.org/3/library/functions.html#filter)
- [`getattr`](https://docs.python.org/3/library/functions.html#getattr)
- [`hasattr`](https://docs.python.org/3/library/functions.html#hasattr)
- [`len`](https://docs.python.org/3/library/functions.html#len)
- [`list`](https://docs.python.org/3/library/functions.html#list)
- [`range`](https://docs.python.org/3/library/functions.html#range)
- [`sorted`](https://docs.python.org/3/library/functions.html#sorted)
<!-- [[[end]]] -->

These limitations are designed to allow anyone to use `databooks assert` freely. This is
because we use built-in's `eval`, and [`eval` is really dangerous](https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html).
To mitigate that (and for your safety), we actually parse the string and only allow a
couple of operations to happen. Check out our [tests](https://github.com/datarootsio/databooks/blob/main/tests/test_affirm.py)
to see what is and isn't allowed and see the [source](https://github.com/datarootsio/databooks/blob/main/databooks/affirm.py)
to see how that happens!

It's also relevant to mention that to avoid repetitive typing one configure the tool to
omit the source string. Even more powerful is to combine it with [`pre-commit`](https://pre-commit.com/)
or CI/CD. Check out the rest of the "Usage" section for more info!

### Recipes

It can be a bit repetitive and tedious to write out expressions to be asserted. Or
even hard to think of how to express these assertions about notebooks. With that in mind,
we also include "user recipes". These recipes store some useful expressions to be checked,
to be used both as short-hand of other expressions and inspiration for you to come up
with your own recipe! Feel free to submit a PR with your recipe or open an issue if
you're  having issues coming up with it.

<!-- [[[cog
import importlib.util
from collections import namedtuple
import cog

spec = importlib.util.spec_from_file_location("databooks", "databooks/recipes.py")
recipes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipes)

RecipeDoc = namedtuple("RecipeDoc", ["name", "src", "desc"])

DOC_TEMPLATE = """#### `{recipe.name}`
- **Description:** {recipe.desc}
- **Source:** `{recipe.src}`
"""

recipe_names = [name for name in dir(recipes.CookBook) if not name.startswith("_")]
recipe_infos = [getattr(recipes.CookBook, recipe) for recipe in recipe_names]
recipe_docs = [
    RecipeDoc(name=name.replace("_","-"), src=info.src, desc=info.description)
    for name, info in zip(recipe_names, recipe_infos)
]

cog.out("\n".join(DOC_TEMPLATE.format(recipe=recipe) for recipe in recipe_docs))

]]] -->
#### `has-tags`
- **Description:** Assert that there is at least one cell with tags.
- **Source:** `any(getattr(cell.metadata, 'tags', []) for cell in nb.cells)`

#### `has-tags-code`
- **Description:** Assert that there is at least one code cell with tags.
- **Source:** `any(getattr(cell.metadata, 'tags', []) for cell in code_cells)`

#### `max-cells`
- **Description:** Assert that there are less than 128 cells in the notebook.
- **Source:** `len(nb.cells) < 128`

#### `no-empty-code`
- **Description:** Assert that there are no empty code cells in the notebook.
- **Source:** `all(cell.source for cell in code_cells)`

#### `seq-exec`
- **Description:** Assert that the executed code cells were executed sequentially (similar effect to when you 'restart kernel and run all cells').
- **Source:** `[c.execution_count for c in exec_cells] == list(range(1, len(exec_cells) + 1))`

#### `seq-increase`
- **Description:** Assert that the executed code cells were executed in increasing order.
- **Source:** `[c.execution_count for c in exec_cells] == sorted([c.execution_count for c in exec_cells])`

#### `startswith-md`
- **Description:** Assert that the first cell in notebook is a markdown cell.
- **Source:** `nb.cells[0].cell_type == 'markdown'`
<!-- [[[end]]] -->

!!! tip

    If your use case is more complex and cannot be translated into a single expression,
    you can always download `databooks` and use it as a part of your script!
