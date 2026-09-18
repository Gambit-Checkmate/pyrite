"""The `make_client` fixture must leave no live SQLite connection behind.

This is the regression guard for the defect a cold read found on the branch
that introduced the fixture: `create_app()` eagerly seeds the KB registry,
which opens a SECOND `PyriteDB` on the same file and parks it on
`application.state.pyrite_db`. Nothing in `pyrite/` ever closes that one, and
some routes read it directly rather than through dependency injection, so a
fixture that closes only the DB it constructed itself leaves an open WAL
connection -- the exact leak the fixture was written to eliminate
(`tests-leak-open-pyritedb-connections-into-temporarydirectory-teardown`).

The leak was invisible on the branch because the fixture also moved to
`tmp_path`, which pytest does not delete during the run. That is a real
mitigation but it is a *default* (`tmp_path_retention_policy`), not a
guarantee: flip the policy and every leaked connection is back to racing
`rmtree`. So this asserts on the connection, not on whether a directory
removal happened to survive.

The two tests are ordered on purpose: the first creates a client, the second
inspects the directory AFTER the first test's fixture teardown has run.
Asserting inside the first test would run before teardown and prove nothing.
"""

_state: dict = {}


def test_make_client_app_uses_a_second_connection(make_client):
    """Guard the premise: if this stops being true, the test below is vacuous."""
    client, config, db = make_client()
    assert client.get("/api/kbs").status_code == 200

    app_state_db = client.app.state.pyrite_db
    assert app_state_db is not None, "create_app no longer parks a db on app.state"
    assert app_state_db is not db, (
        "create_app no longer opens its own second connection -- if this is "
        "now intentional, the fixture's app-state tracking can be simplified"
    )

    _state["dir"] = config.settings.index_path.parent


def test_no_wal_files_survive_the_fixture_teardown():
    """Runs after the test above, so `make_client`'s teardown has completed."""
    work_dir = _state.get("dir")
    assert work_dir is not None, "the previous test did not run"

    leftovers = sorted(p.name for p in work_dir.iterdir())
    live = [n for n in leftovers if n.endswith("-wal") or n.endswith("-shm")]
    assert not live, (
        f"SQLite WAL/SHM files are still live after teardown: {leftovers}. "
        "Some connection on this database was not closed -- most likely "
        "application.state.pyrite_db, which create_app opens and nothing in "
        "pyrite/ closes."
    )
