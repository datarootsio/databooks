set positional-arguments

# Preview version stamping locally (CI normally does this automatically).
release-prepare VERSION:
    poetry run python scripts/release.py prepare "$1"

# Validate merged HEAD and create an annotated version tag.
release-tag VERSION:
    poetry run python scripts/release.py tag "$1"

# Revalidate the tagged commit and push only this tag to origin.
release-push VERSION:
    poetry run python scripts/release.py push "$1"
