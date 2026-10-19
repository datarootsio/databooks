"""Prepare, validate, tag, and push releases with CI version stamping."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

STABLE_VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")


class ReleaseError(Exception):
    """A release precondition was not met."""


def git(*args: str) -> str:
    """Run Git without a shell and report failures to the caller."""
    return subprocess.check_output(
        ["git", *args], text=True, stderr=subprocess.PIPE
    ).strip()


def require_clean() -> None:
    """Ignore untracked files but reject staged and unstaged tracked changes."""
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ReleaseError(
            "Release preparation and tagging require clean tracked files."
        )


def validate_commit(commit: str) -> None:
    """Fetch main and require the release commit to belong to its history."""
    git("fetch", "--no-tags", "origin", "+refs/heads/main:refs/remotes/origin/main")
    try:
        git("merge-base", "--is-ancestor", commit, "refs/remotes/origin/main")
    except subprocess.CalledProcessError:
        raise ReleaseError("Release commit must belong to the history of origin/main.")


def tagged_commit(version: str) -> str:
    """Resolve an exact local tag, independent of the current branch."""
    try:
        return git("rev-parse", "--verify", "refs/tags/" + version + "^{commit}")
    except subprocess.CalledProcessError:
        raise ReleaseError(
            "Local tag {} does not exist or does not point to a commit.".format(version)
        )


def prepare(version: str) -> None:
    """Stamp both version fields for CI builds or an optional local preview."""
    require_clean()
    # Poetry preserves the TOML structure and validates the existing project.
    subprocess.run(["poetry", "version", version], check=True)
    Path("databooks/version.py").write_text(
        '"""Package version information."""\n__version__ = "{}"\n'.format(version),
        encoding="utf-8",
    )


def tag(version: str) -> None:
    """Create an annotated tag at a clean, merged HEAD, without replacing tags."""
    require_clean()
    existing = git("tag", "--list", version)
    if existing:
        raise ReleaseError(
            "Local tag {} already exists; tags are never replaced.".format(version)
        )
    commit = git("rev-parse", "HEAD")
    validate_commit(commit)
    git("tag", "-a", version, "-m", "Release " + version, commit)


def push(version: str) -> None:
    """Revalidate the tagged commit and push only the explicitly requested tag."""
    commit = tagged_commit(version)
    validate_commit(commit)
    ref = "refs/tags/" + version
    if git("ls-remote", "--tags", "origin", ref):
        raise ReleaseError(
            "Remote tag {} already exists; tags are never replaced.".format(version)
        )
    # Disable followTags even if enabled in the user's Git configuration.
    # An empty expected value also rejects a tag created remotely since ls-remote.
    git(
        "-c",
        "push.followTags=false",
        "push",
        "--force-with-lease=" + ref + ":",
        "origin",
        ref + ":" + ref,
    )


def main() -> int:
    """Provide the shared local and CI release interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "tag", "push", "validate"])
    parser.add_argument("version")
    parser.add_argument(
        "--commit", help="CI event commit that must match the local tag"
    )
    args = parser.parse_args()
    try:
        if STABLE_VERSION.fullmatch(args.version) is None:
            raise ReleaseError("Expected a stable X.Y.Z version (for example, 1.3.11).")
        root = git("rev-parse", "--show-toplevel")
        if Path.cwd().resolve() != Path(root).resolve():
            raise ReleaseError("Run release commands from the repository root.")
        if args.command == "validate":
            commit = tagged_commit(args.version)
            if args.commit and commit != git(
                "rev-parse", "--verify", args.commit + "^{commit}"
            ):
                raise ReleaseError("Tag does not match the CI event commit.")
            validate_commit(commit)
        else:
            actions = {"prepare": prepare, "tag": tag, "push": push}
            actions[args.command](args.version)
    except (
        ReleaseError,
        KeyError,
        ValueError,
        SyntaxError,
        OSError,
        subprocess.CalledProcessError,
    ) as exc:
        detail = (
            exc.stderr
            if isinstance(exc, subprocess.CalledProcessError) and exc.stderr
            else str(exc)
        )
        sys.stderr.write("Release error: {}\n".format(detail.strip()))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
