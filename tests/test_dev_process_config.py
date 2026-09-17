"""The commit/push/CI split is load-bearing, so it is pinned by tests.

See kb/backlog/fast-commit-hooks-full-suite-at-pre-push-ci-is-the-gate.md.

Commit-stage hooks stash every unstaged edit in the working tree while they
run. With several sessions sharing one tree, a multi-minute hook makes other
sessions' edits vanish for minutes and lets one session's untracked RED test
block everyone's commits. So: nothing slow at the commit stage, the full
suite at pre-push, CI as the authority.
"""

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def precommit() -> dict:
    return yaml.safe_load((REPO / ".pre-commit-config.yaml").read_text())


@pytest.fixture(scope="module")
def ci() -> dict:
    return yaml.safe_load((REPO / ".github" / "workflows" / "ci.yml").read_text())


def _hooks(config: dict) -> list[dict]:
    return [hook for repo in config["repos"] for hook in repo["hooks"]]


def _stages(hook: dict, config: dict) -> set[str]:
    # A hook with no `stages` runs at every installed stage.
    return set(hook.get("stages") or config.get("default_stages") or ["pre-commit"])


def _local_hooks(config: dict) -> list[dict]:
    return [h for repo in config["repos"] if repo["repo"] == "local" for h in repo["hooks"]]


class TestPreCommitConfig:
    def test_no_commit_stage_hook_runs_pytest(self, precommit):
        offenders = [
            hook["id"]
            for hook in _hooks(precommit)
            if "pytest" in str(hook.get("entry", "")) and "pre-commit" in _stages(hook, precommit)
        ]
        assert offenders == [], f"pytest must not run at the commit stage: {offenders}"

    def test_full_suite_runs_at_pre_push(self, precommit):
        pushed = [
            hook
            for hook in _hooks(precommit)
            if "pytest" in str(hook.get("entry", "")) and _stages(hook, precommit) == {"pre-push"}
        ]
        assert len(pushed) == 1, "expected exactly one pre-push pytest hook"

    def test_pre_push_suite_is_scoped_to_code_changes(self, precommit):
        (hook,) = [h for h in _hooks(precommit) if "pytest" in str(h.get("entry", ""))]
        assert not hook.get("always_run"), "always_run defeats the docs-only skip"
        assert hook.get("files"), "pre-push pytest needs a `files:` filter"

    def test_local_hooks_do_not_discard_output(self, precommit):
        offenders = [h["id"] for h in _local_hooks(precommit) if "/dev/null" in h["entry"]]
        assert offenders == [], f"hooks must show why they failed: {offenders}"

    def test_local_hooks_do_not_require_an_activated_venv(self, precommit):
        offenders = [h["id"] for h in _local_hooks(precommit) if "activate" in h["entry"]]
        assert offenders == [], f"`source .venv/bin/activate` is not portable: {offenders}"

    def test_all_three_hook_types_install_by_default(self, precommit):
        # Without this, plain `pre-commit install` skips commit-msg and pre-push,
        # and the fix-commit-has-tests rule silently never runs for new clones.
        assert set(precommit.get("default_install_hook_types", [])) >= {
            "pre-commit",
            "commit-msg",
            "pre-push",
        }

    def test_kb_schema_validation_stays_at_commit_stage(self, precommit):
        (hook,) = [h for h in _hooks(precommit) if h["id"] == "pyrite-schema-validate"]
        assert "pre-commit" in _stages(hook, precommit)


class TestCIWorkflow:
    def test_superseded_runs_are_cancelled(self, ci):
        assert ci["concurrency"]["cancel-in-progress"] is True

    def test_ci_runs_the_checks_that_local_hooks_run(self, ci):
        # Outside contributors' PRs never run local hooks; CI has to.
        steps = "\n".join(
            str(step.get("run", "")) for job in ci["jobs"].values() for step in job["steps"]
        )
        assert "check_import_cycles.py" in steps
        assert "pyrite schema validate" in steps

    def test_no_duplicate_full_suite_job(self, ci):
        assert "test-optional-deps" not in ci["jobs"]

    def test_python_312_always_runs(self, ci):
        # `test (3.12)` is the required status check on main (ADR-0025).
        matrix = str(ci["jobs"]["test"]["strategy"]["matrix"]["python-version"])
        assert "3.12" in matrix
