"""Exercise release commands against real repositories and a local bare remote."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[1] / "scripts" / "release.py"


def git(repo: Path, *args: str) -> str:
    """Run Git with isolated identities and configuration."""
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    env.update(
        GIT_AUTHOR_NAME="Release Test",
        GIT_AUTHOR_EMAIL="release@example.com",
        GIT_COMMITTER_NAME="Release Test",
        GIT_COMMITTER_EMAIL="release@example.com",
    )
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        env=env,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def release(
    repo: Path, command: str, version: str, *args: str
) -> subprocess.CompletedProcess:
    """Run the public CLI, keeping errors available for assertions."""
    env = dict(os.environ, VIRTUAL_ENV=sys.prefix)
    env.update(
        GIT_AUTHOR_NAME="Release Test",
        GIT_AUTHOR_EMAIL="release@example.com",
        GIT_COMMITTER_NAME="Release Test",
        GIT_COMMITTER_EMAIL="release@example.com",
    )
    return subprocess.run(
        [sys.executable, str(HELPER), command, version, *args],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
    )


def metadata(repo: Path, package: str = "1.3.11", runtime: str = "1.3.11") -> None:
    """Write independent, minimal package metadata."""
    (repo / "databooks").mkdir(exist_ok=True)
    (repo / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "release-fixture"\nversion = "' + package + '"\n'
        'description = "test"\nauthors = ["Test <test@example.com>"]\n'
        '[tool.poetry.dependencies]\npython = "^3.7"\n'
    )
    (repo / "databooks" / "version.py").write_text('__version__ = "' + runtime + '"\n')


def commit(repo: Path) -> str:
    """Commit fixture changes."""
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Metadata")
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Create main and origin/main in separate local repositories."""
    remote = tmp_path / "origin.git"
    remote.mkdir()
    git(remote, "init", "--bare")
    work = tmp_path / "work"
    work.mkdir()
    git(work, "init", "-b", "main")
    metadata(work)
    commit(work)
    git(work, "remote", "add", "origin", str(remote))
    git(work, "push", "-u", "origin", "main")
    return work


def assert_failed(result: subprocess.CompletedProcess, reason: str) -> None:
    """Require a useful rejection rather than an unrelated exception."""
    assert result.returncode != 0, result.stdout
    assert reason in result.stderr, result.stderr


def test_prepare_updates_both_versions(repo: Path) -> None:
    """Preparation changes exactly the two fields and creates no commit or tag."""
    before = git(repo, "rev-parse", "HEAD")
    result = release(repo, "prepare", "2.0.0")
    assert result.returncode == 0, result.stderr
    assert 'version = "2.0.0"' in (repo / "pyproject.toml").read_text()
    assert '__version__ = "2.0.0"' in (repo / "databooks/version.py").read_text()
    assert git(repo, "rev-parse", "HEAD") == before
    assert git(repo, "tag") == ""


@pytest.mark.parametrize(
    "version",
    [
        "v1.3.11",
        "1.3",
        "1.3.11rc1",
        "1.3.11-dev",
        "01.3.11",
        "1.3.11+build",
        "1.3.11\n",
        "１.3.11",
        "-1.3.11",
        "1.3.11; touch INJECTED",
        "",
    ],
)
@pytest.mark.parametrize("command", ["prepare", "tag", "push", "validate"])
def test_invalid_versions_leave_repository_unchanged(
    repo: Path, version: str, command: str
) -> None:
    """Reject malformed input before any mutation or external Git operation."""
    before = [
        (repo / p).read_bytes() for p in ["pyproject.toml", "databooks/version.py"]
    ]
    result = release(repo, command, version)
    assert result.returncode != 0
    assert [
        (repo / p).read_bytes() for p in ["pyproject.toml", "databooks/version.py"]
    ] == before
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "tag") == ""


@pytest.mark.parametrize("command", ["prepare", "tag"])
@pytest.mark.parametrize("staged", [False, True])
def test_dirty_tracked_files_rejected(repo: Path, command: str, staged: bool) -> None:
    """Neither staged nor unstaged changes may enter a release."""
    (repo / "databooks/version.py").write_text('__version__ = "2.0.0"\n')
    if staged:
        git(repo, "add", ".")
    assert_failed(release(repo, command, "1.3.11"), "clean tracked files")
    assert git(repo, "tag") == ""


def test_tag_is_annotated_and_duplicate_is_rejected(repo: Path) -> None:
    """Tag merged HEAD once and leave unrelated untracked files alone."""
    (repo / "untracked").write_text("unrelated")
    result = release(repo, "tag", "1.3.11")
    assert result.returncode == 0, result.stderr
    assert git(repo, "cat-file", "-t", "refs/tags/1.3.11") == "tag"
    assert git(repo, "rev-parse", "1.3.11^{}") == git(repo, "rev-parse", "HEAD")
    original = git(repo, "rev-parse", "refs/tags/1.3.11")
    assert_failed(release(repo, "tag", "1.3.11"), "already exists")
    assert git(repo, "rev-parse", "refs/tags/1.3.11") == original


@pytest.mark.parametrize("package,runtime", [("2.0.0", "1.3.11"), ("1.3.11", "2.0.0")])
@pytest.mark.parametrize("command", ["tag", "push", "validate"])
def test_metadata_mismatch_rejected(
    repo: Path, package: str, runtime: str, command: str
) -> None:
    """Both committed fields must independently match the requested tag."""
    metadata(repo, package, runtime)
    commit(repo)
    git(repo, "push", "origin", "main")
    if command != "tag":
        git(repo, "tag", "-a", "1.3.11", "-m", "Invalid release")
    assert_failed(release(repo, command, "1.3.11"), "does not match")
    assert git(repo, "ls-remote", "--tags", "origin") == ""


@pytest.mark.parametrize("command", ["tag", "push", "validate"])
def test_unmerged_commit_rejected(repo: Path, command: str) -> None:
    """Local main is insufficient: require the freshly fetched remote history."""
    metadata(repo, "2.0.0", "2.0.0")
    commit(repo)
    if command != "tag":
        git(repo, "tag", "-a", "2.0.0", "-m", "Unmerged release")
    assert_failed(release(repo, command, "2.0.0"), "origin/main")
    assert git(repo, "ls-remote", "--tags", "origin") == ""


def test_push_checks_tagged_commit_and_pushes_only_requested_tag(repo: Path) -> None:
    """Changing branch or metadata after tagging must not change the push target."""
    assert release(repo, "tag", "1.3.11").returncode == 0
    git(repo, "tag", "-a", "unrelated", "-m", "Unrelated tag")
    git(repo, "config", "push.followTags", "true")
    git(repo, "checkout", "-b", "work-in-progress")
    metadata(repo, "2.0.0", "2.0.0")
    commit(repo)
    result = release(repo, "push", "1.3.11")
    assert result.returncode == 0, result.stderr
    refs = git(repo, "ls-remote", "--refs", "origin").splitlines()
    assert sorted(line.split()[1] for line in refs) == [
        "refs/heads/main",
        "refs/tags/1.3.11",
    ]
    assert_failed(release(repo, "push", "1.3.11"), "already exists")


def test_push_revalidates_main_history(repo: Path) -> None:
    """A formerly merged tag must be rejected after remote main is rewritten."""
    initial = git(repo, "rev-parse", "HEAD")
    metadata(repo, "2.0.0", "2.0.0")
    commit(repo)
    git(repo, "push", "origin", "main")
    assert release(repo, "tag", "2.0.0").returncode == 0
    git(repo, "push", "origin", initial + ":refs/heads/main", "--force")
    assert_failed(release(repo, "push", "2.0.0"), "origin/main")


def test_remote_tag_is_never_replaced(repo: Path) -> None:
    """Reject a same-named remote tag even when it points elsewhere."""
    git(repo, "tag", "1.3.11")
    git(repo, "push", "origin", "refs/tags/1.3.11")
    remote_before = git(repo, "ls-remote", "--tags", "origin")
    git(repo, "tag", "-d", "1.3.11")
    assert release(repo, "tag", "1.3.11").returncode == 0
    assert_failed(release(repo, "push", "1.3.11"), "already exists")
    assert git(repo, "ls-remote", "--tags", "origin") == remote_before


@pytest.mark.parametrize("command", ["push", "validate"])
def test_missing_tag_rejected(repo: Path, command: str) -> None:
    """An absent tag is not implicitly created."""
    assert_failed(release(repo, command, "1.3.11"), "does not exist")


def test_ci_validates_event_commit(repo: Path) -> None:
    """Validation binds metadata and main history to the triggering commit."""
    initial = git(repo, "rev-parse", "HEAD")
    assert release(repo, "tag", "1.3.11").returncode == 0
    assert release(repo, "validate", "1.3.11", "--commit", initial).returncode == 0
    metadata(repo, "2.0.0", "2.0.0")
    newer = commit(repo)
    git(repo, "push", "origin", "main")
    assert_failed(
        release(repo, "validate", "1.3.11", "--commit", newer), "event commit"
    )


def test_just_passes_version_as_literal_argument(repo: Path) -> None:
    """Shell syntax in a version must never be executed by Just."""
    if shutil.which("just") is None:
        pytest.skip("Just is only required for local release commands")
    shutil.copy(HELPER.parents[1] / "justfile", repo / "justfile")
    (repo / "scripts").mkdir()
    shutil.copy(HELPER, repo / "scripts/release.py")
    result = subprocess.run(
        ["just", "release-tag", '1.3.11"; touch INJECTED; echo "$(touch INJECTED)'],
        cwd=repo,
        env=dict(os.environ, VIRTUAL_ENV=sys.prefix),
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert not (repo / "INJECTED").exists()
