"""`pyrite.__version__` must not drift from the packaged version.

It sat at 0.12.0 while pyproject.toml reached 0.24.1: a hand-maintained copy
that nothing checked. See
kb/backlog/single-source-of-truth-for-the-version-asserted-by-a-test.md.
"""

import re
import tomllib
from importlib import metadata
from pathlib import Path

import pyrite

REPO = Path(__file__).resolve().parent.parent


def test_dunder_version_matches_pyproject():
    declared = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["version"]
    assert pyrite.__version__ == declared


def test_dunder_version_is_not_a_hardcoded_literal():
    source = (REPO / "pyrite" / "__init__.py").read_text()
    assert not re.search(r'^__version__\s*=\s*["\']', source, re.MULTILINE)


def test_falls_back_to_installed_metadata_outside_a_checkout(monkeypatch, tmp_path):
    # Simulate site-packages: no pyproject.toml beside the package.
    monkeypatch.setattr(pyrite, "__file__", str(tmp_path / "pyrite" / "__init__.py"))
    assert pyrite._read_version() == metadata.version("pyrite")
