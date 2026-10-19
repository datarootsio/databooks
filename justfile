set positional-arguments

# Preview version stamping locally (CI normally does this automatically).
release-prepare VERSION:
    uv run --no-project scripts/release.py prepare "$1"

# Validate merged HEAD and create an annotated version tag.
release-tag VERSION:
    uv run --no-project scripts/release.py tag "$1"

# Revalidate the tagged commit and push only this tag to origin.
release-push VERSION:
    uv run --no-project scripts/release.py push "$1"
