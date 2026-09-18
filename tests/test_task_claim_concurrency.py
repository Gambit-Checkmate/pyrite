"""Concurrency test for the task-claim CAS (task-claim-concurrency-test).

`KBService.claim_entry()`'s compare-and-swap is the one concurrency
guard the whole multi-agent fleet depends on, and until now it had
never actually been executed concurrently -- only sequential
simulation (claim, then a second claim observes the conflict). This
races N real OS processes (not threads -- agents are processes, each
with its own SQLite connection) against a single open task and
asserts exactly one winner.
"""

import multiprocessing
import tempfile
from pathlib import Path

import pytest

from pyrite.config import KBConfig, PyriteConfig, Settings
from pyrite.services.task_service import TaskService
from pyrite.storage.database import PyriteDB

N_CLAIMANTS = 8

# Wall-clock budgets. Each worker is a fresh interpreter that imports pyrite;
# under `pytest -n auto` they compete with every xdist worker for the cores, and
# a fixed 30 s per-process join once reported a merely slow worker as "crashed"
# (exitcode None). One deadline for the whole group, generous, and a distinct
# failure message for "still running" vs "exited non-zero".
_GROUP_DEADLINE = 180.0
_BARRIER_TIMEOUT = 150.0


def _join_all(processes, deadline=_GROUP_DEADLINE):
    import time

    end = time.monotonic() + deadline
    for p in processes:
        p.join(timeout=max(0.0, end - time.monotonic()))
    still_running = [p.pid for p in processes if p.exitcode is None]
    for p in processes:
        if p.exitcode is None:
            p.kill()
    assert not still_running, (
        f"{len(still_running)} worker(s) still running after {deadline:.0f}s: {still_running}"
    )
    crashed = [(p.pid, p.exitcode) for p in processes if p.exitcode != 0]
    assert not crashed, f"worker process(es) crashed instead of returning a clean result: {crashed}"


def _make_config(tmpdir: Path) -> tuple[PyriteConfig, KBConfig]:
    tasks_path = tmpdir / "tasks-kb"
    kb_config = KBConfig(
        name="test-tasks",
        path=tasks_path,
        kb_type="task",
        description="Concurrency test task KB",
    )
    config = PyriteConfig(
        knowledge_bases=[kb_config],
        settings=Settings(index_path=tmpdir / "index.db"),
    )
    return config, kb_config


def _claim_worker(tmpdir_str: str, task_id: str, assignee: str, result_queue, barrier) -> None:
    """Run in a separate process: open a fresh DB connection and race the claim.

    The barrier makes it a race: without it, under a loaded machine (xdist
    saturating every core) spawn start-up skew turns N "concurrent" claims into
    a sequence, and the CAS is never actually contended.
    """
    tmpdir = Path(tmpdir_str)
    config, _ = _make_config(tmpdir)
    db = PyriteDB(config.settings.index_path)
    svc = TaskService(config, db)
    try:
        barrier.wait(timeout=_BARRIER_TIMEOUT)
        result = svc.claim_task(task_id, "test-tasks", assignee)
        result_queue.put((assignee, result))
    finally:
        db.close()


def _reset_worker(tmpdir_str: str, task_id: str, result_queue, barrier) -> None:
    """Run in a separate process: race a stale-claim reset against a claim."""
    tmpdir = Path(tmpdir_str)
    config, _ = _make_config(tmpdir)
    db = PyriteDB(config.settings.index_path)
    svc = TaskService(config, db)
    try:
        barrier.wait(timeout=_BARRIER_TIMEOUT)
        result = svc.reset_task(task_id, "test-tasks", reason="stale worker")
        result_queue.put(("reset", result))
    except Exception as e:
        result_queue.put(("reset", {"error": str(e)}))
    finally:
        db.close()


@pytest.fixture
def concurrency_env():
    with tempfile.TemporaryDirectory() as d:
        tmpdir = Path(d)
        config, kb_config = _make_config(tmpdir)
        kb_config.path.mkdir()
        (kb_config.path / "tasks").mkdir()

        db = PyriteDB(config.settings.index_path)
        db.register_kb(
            name="test-tasks",
            kb_type="task",
            path=str(kb_config.path),
            description="Concurrency test task KB",
        )
        svc = TaskService(config, db)
        yield {"tmpdir": tmpdir, "config": config, "kb_config": kb_config, "svc": svc, "db": db}
        db.close()


class TestClaimTaskConcurrency:
    def test_n_processes_race_claim_exactly_one_wins(self, concurrency_env):
        svc = concurrency_env["svc"]
        tmpdir = concurrency_env["tmpdir"]

        created = svc.create_task(kb_name="test-tasks", title="Race me")
        task_id = created["entry_id"]

        ctx = multiprocessing.get_context("spawn")
        result_queue = ctx.Queue()
        barrier = ctx.Barrier(N_CLAIMANTS)
        processes = [
            ctx.Process(
                target=_claim_worker,
                args=(str(tmpdir), task_id, f"agent:{i}", result_queue, barrier),
            )
            for i in range(N_CLAIMANTS)
        ]
        for p in processes:
            p.start()
        _join_all(processes)

        results = [result_queue.get(timeout=10) for _ in processes]

        winners = [(assignee, r) for assignee, r in results if r["claimed"] is True]
        losers = [(assignee, r) for assignee, r in results if r["claimed"] is False]

        assert len(winners) == 1, f"expected exactly one winner, got {winners}"
        assert len(losers) == N_CLAIMANTS - 1

        # Every loser must be a clean CONFLICT-class response, not a crash/corruption.
        for _assignee, r in losers:
            assert "error" in r
            assert r.get("current_status") == "claimed"

        # The on-disk file must match the winning claimant, not just the index.
        from pyrite.storage.repository import KBRepository

        entry = KBRepository(concurrency_env["kb_config"]).load(task_id)
        winning_assignee = winners[0][0]
        assert entry.assignee == winning_assignee
        assert entry.status == "claimed"

    def test_stale_claim_reset_races_an_active_claimer(self, concurrency_env):
        """The release/reset path (task-claim-concurrency-test's second
        acceptance criterion): a reset racing an active re-claim must not
        leave the entry in an inconsistent state -- exactly one of
        (reset-to-open, claimed-by-racer) applies to both index and file."""
        svc = concurrency_env["svc"]
        tmpdir = concurrency_env["tmpdir"]

        created = svc.create_task(kb_name="test-tasks", title="Stale claim")
        task_id = created["entry_id"]
        svc.claim_task(task_id, "test-tasks", "agent:original")
        svc.update_task(task_id, "test-tasks", status="in_progress")

        ctx = multiprocessing.get_context("spawn")
        result_queue = ctx.Queue()
        barrier = ctx.Barrier(2)
        processes = [
            ctx.Process(target=_reset_worker, args=(str(tmpdir), task_id, result_queue, barrier)),
            ctx.Process(
                target=_claim_worker,
                args=(str(tmpdir), task_id, "agent:racer", result_queue, barrier),
            ),
        ]
        for p in processes:
            p.start()
        _join_all(processes)

        results = dict(result_queue.get(timeout=10) for _ in processes)

        from pyrite.storage.repository import KBRepository

        entry = KBRepository(concurrency_env["kb_config"]).load(task_id)

        # The claim only succeeds if it raced in after the reset landed
        # (from_status="open"); if the reset hadn't landed yet, the racer's
        # claim correctly fails (task was still "in_progress", not "open").
        # Either way, index and file must agree on the final state.
        reset_result = results.get("reset")
        claim_result = results.get("agent:racer")
        context = f"file={{status={entry.status!r}, assignee={entry.assignee!r}}} reset={reset_result} claim={claim_result}"
        assert entry.status in ("open", "claimed"), context
        if entry.status == "claimed":
            assert entry.assignee == "agent:racer", context
            assert claim_result.get("claimed") is True, context
        else:
            assert reset_result.get("status") == "open" or "error" not in reset_result, context
            assert claim_result.get("claimed") is False, context
        # Index and file must agree on the final state.
        row = concurrency_env["db"].execute_sql(
            "SELECT status, assignee FROM entry WHERE id = :id", {"id": task_id}
        )[0]
        assert row["status"] == entry.status, context + f" index={dict(row)}"
