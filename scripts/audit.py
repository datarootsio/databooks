"""Audit frozen project environments and initialized Python hooks."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Query the target interpreter without importing the project or site customizations.
INVENTORY = """
import importlib.metadata as metadata
import json
print(json.dumps([
    {"name": dist.metadata["Name"], "version": dist.version}
    for dist in metadata.distributions()
]))
"""


def canonical(name: str) -> str:
    """Normalize distribution names as PyPI does."""
    return re.sub(r"[-_.]+", "-", name).lower()


def validate_report(report: dict[str, Any], inventory: list[dict[str, str]]) -> None:
    """Reject skipped, missing, duplicate, or vulnerable dependencies."""
    dependencies = report["dependencies"]
    for dependency in dependencies:
        if "skip_reason" in dependency:
            raise ValueError(f"Skipped dependency: {dependency}")
        if dependency["vulns"]:
            raise ValueError(f"Vulnerabilities found: {dependency['name']}")
    expected = {(canonical(p["name"]), p["version"]) for p in inventory}
    actual = {(canonical(p["name"]), p["version"]) for p in dependencies}
    if (
        not expected
        or actual != expected
        or len(dependencies) != len(expected)
        or len(inventory) != len(expected)
    ):
        raise ValueError("Audit report does not match the complete frozen inventory")


def hook_pythons(cache: Path) -> list[Path]:
    """Require initialized Python hooks and include every environment in this cache."""
    environments = sorted(cache.glob("repo*/py_env-*"))
    if not environments:
        raise ValueError(f"No initialized Python hook environments in {cache}")
    interpreters = [env / "bin" / "python" for env in environments]
    if any(not interpreter.is_file() for interpreter in interpreters):
        raise ValueError("Incomplete Python hook environment initialization")
    return interpreters


def audit_environment(python: Path, output: Path) -> None:
    """Freeze and audit one interpreter, retaining inputs and reports on failure."""
    output.mkdir(parents=True, exist_ok=True)
    status: dict[str, Any] = {"python": str(python), "passed": False}
    try:
        result = subprocess.run(
            [str(python), "-I", "-c", INVENTORY],
            check=True,
            capture_output=True,
            text=True,
        )
        inventory = json.loads(result.stdout)
        (output / "inventory.json").write_text(
            json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
        )
        # This repository's own distribution has no PyPI advisory identity.
        # Keep it in the inventory artifact; audit every third-party distribution.
        dependencies = [p for p in inventory if canonical(p["name"]) != "databooks"]
        frozen = output / "requirements.txt"
        lines = []
        for package in dependencies:
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", package["name"]):
                raise ValueError(f"Invalid distribution name: {package['name']!r}")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]*", package["version"]):
                raise ValueError(
                    f"Invalid distribution version: {package['version']!r}"
                )
            lines.append(f"{package['name']}=={package['version']}\n")
        frozen.write_text("".join(sorted(lines)), encoding="utf-8")
        report = output / "audit.json"
        command = [
            sys.executable,
            "-m",
            "pip_audit",
            "--requirement",
            str(frozen),
            "--no-deps",
            "--disable-pip",
            "--strict",
            "--progress-spinner",
            "off",
            "--format",
            "json",
            "--output",
            str(report),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        (output / "audit.log").write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        if result.returncode:
            raise ValueError(f"pip-audit exited {result.returncode}; see {output}")
        validate_report(json.loads(report.read_text(encoding="utf-8")), dependencies)
        status["passed"] = True
        status["packages"] = len(dependencies)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as exc:
        status["error"] = str(exc)
        raise
    finally:
        (output / "status.json").write_text(
            json.dumps(status, indent=2) + "\n", encoding="utf-8"
        )


def main() -> int:
    """Audit explicit interpreters and/or all initialized Python pre-commit hooks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, action="append", default=[])
    parser.add_argument("--hooks", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pythons = args.python
    failures = []
    if args.hooks:
        try:
            pythons += hook_pythons(args.hooks)
        except ValueError as exc:
            failures.append(str(exc))
    if not pythons:
        failures.append("No environments selected for audit")
    for index, python in enumerate(pythons):
        try:
            audit_environment(python.absolute(), args.output / f"environment-{index}")
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            subprocess.SubprocessError,
        ) as exc:
            failures.append(str(exc))
    (args.output / "summary.json").write_text(
        json.dumps({"environments": len(pythons), "failures": failures}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    for failure in failures:
        sys.stderr.write(failure + "\n")
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
