"""Regression tests for complete, blocking dependency audits."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def audit_module() -> ModuleType:
    """Load audit tooling without installing scripts as a package."""
    spec = importlib.util.spec_from_file_location(
        "audit", Path(__file__).parents[1] / "scripts" / "audit.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_rejects_skipped_package() -> None:
    """An unscanned package must block CI even if pip-audit exits successfully."""
    audit = audit_module()
    with pytest.raises(ValueError, match="Skipped"):
        audit.validate_report(
            {"dependencies": [{"name": "example", "skip_reason": "not on PyPI"}]},
            [{"name": "example", "version": "1.0"}],
        )


def test_audit_rejects_missing_package() -> None:
    """A partial report cannot pass as a clean environment."""
    audit = audit_module()
    with pytest.raises(ValueError, match="inventory"):
        audit.validate_report(
            {"dependencies": []}, [{"name": "example", "version": "1.0"}]
        )


def test_audit_rejects_vulnerability() -> None:
    """Advisories block CI without suppressions."""
    audit = audit_module()
    with pytest.raises(ValueError, match="Vulnerabilities"):
        audit.validate_report(
            {
                "dependencies": [
                    {"name": "example", "version": "1.0", "vulns": [{"id": "TEST"}]}
                ]
            },
            [{"name": "example", "version": "1.0"}],
        )


def test_audit_accepts_complete_report() -> None:
    """Canonical package names match the frozen inventory."""
    audit_module().validate_report(
        {"dependencies": [{"name": "Example_Name", "version": "1.0", "vulns": []}]},
        [{"name": "example-name", "version": "1.0"}],
    )


def test_audit_requires_hook_environments(tmp_path: Path) -> None:
    """Missing hook initialization must fail closed."""
    with pytest.raises(ValueError, match="No initialized"):
        audit_module().hook_pythons(tmp_path)


def test_audit_rejects_duplicate_inventory() -> None:
    """Duplicate installed metadata must not disappear during comparison."""
    package = {"name": "example", "version": "1.0"}
    with pytest.raises(ValueError, match="inventory"):
        audit_module().validate_report(
            {"dependencies": [{**package, "vulns": []}]}, [package, package]
        )


def test_audit_retains_collection_failure(tmp_path: Path) -> None:
    """Interpreter collection failures leave a JSON artifact and block CI."""
    import json

    output = tmp_path / "report"
    with pytest.raises(OSError):
        audit_module().audit_environment(tmp_path / "missing-python", output)
    status = json.loads((output / "status.json").read_text(encoding="utf-8"))
    assert status["passed"] is False
    assert status["error"]


def test_audit_rejects_incomplete_hook_environment(tmp_path: Path) -> None:
    """A discovered hook directory without Python is a collection failure."""
    (tmp_path / "repo-example" / "py_env-python3.11").mkdir(parents=True)
    with pytest.raises(ValueError, match="Incomplete"):
        audit_module().hook_pythons(tmp_path)
