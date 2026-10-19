set positional-arguments

# Update both version fields for review and commit.
release-prepare VERSION:
    poetry run python scripts/release.py prepare "$1"

# Validate merged, committed metadata and create an annotated tag at HEAD.
release-tag VERSION:
    poetry run python scripts/release.py tag "$1"

# Revalidate the tagged commit and push only this tag to origin.
release-push VERSION:
    poetry run python scripts/release.py push "$1"
