"""An entry id becomes a filename, so it must never be able to leave the KB.

Ids reach the repository from places the caller controls: the REST import
endpoint takes `id` from the uploaded file, and `pyrite rename` takes the new id
from argv. Before this guard, `../../x` wrote `x.md` two levels above the KB.
"""

import pytest

from pyrite.config import KBConfig
from pyrite.exceptions import ValidationError
from pyrite.models.core_types import NoteEntry
from pyrite.storage.repository import KBRepository

HOSTILE_IDS = [
    "../../escape",
    "..",
    "../sibling",
    "a/../../b",
    "nested/dir",
    "back\\slash",
    "/etc/passwd",
    ".hidden",
    "nul\x00byte",
    "",
    "   ",
]


@pytest.fixture
def repo(tmp_path):
    kb = tmp_path / "outer" / "kb"
    kb.mkdir(parents=True)
    return KBRepository(KBConfig(path=kb, name="t", kb_type="generic"))


def _md_files(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*.md"))


@pytest.mark.parametrize("bad_id", HOSTILE_IDS)
def test_save_refuses_ids_that_are_not_plain_filenames(repo, tmp_path, bad_id):
    entry = NoteEntry(id=bad_id, title="x", body="x")
    with pytest.raises(ValidationError):
        repo.save(entry)
    assert _md_files(tmp_path) == []


@pytest.mark.parametrize("bad_id", [i for i in HOSTILE_IDS if i.strip()])
def test_rename_refuses_hostile_target_ids(repo, tmp_path, bad_id):
    repo.save(NoteEntry(id="victim", title="Victim", body="keep me"))
    with pytest.raises(ValidationError):
        repo.rename("victim", bad_id)
    assert _md_files(tmp_path) == ["outer/kb/notes/victim.md"]


def test_subdir_argument_cannot_escape_either(repo, tmp_path):
    with pytest.raises(ValidationError):
        repo.save(NoteEntry(id="fine", title="x", body="x"), subdir="../../elsewhere")
    assert _md_files(tmp_path) == []


@pytest.mark.parametrize(
    "good_id",
    [
        "plain-slug",
        "2026-09-17--dated-event",
        "adr-0032",
        "v0.24.1-notes",
        "snake_case_id",
        "MixedCase",
    ],
)
def test_ordinary_ids_still_save(repo, good_id):
    path = repo.save(NoteEntry(id=good_id, title="x", body="x"))
    assert path.name == f"{good_id}.md"
    assert repo.path.resolve() in path.resolve().parents
