"""`settings.auto_embed` switches write-time embedding off.

Every entry write called into the embedding service, which imports torch and
loads the sentence-transformers model (~3 s) and asks the Hugging Face hub for
metadata over the network. That is the right default for a server with the
model cached; it is the wrong default for the test suite (every xdist worker
and every spawned subprocess paid it, and ten copies of torch thrashed the
machine), for `pyrite init` on a fresh install (#13), and for anyone who does
not want semantic search. `PYRITE_AUTO_EMBED=0` turns it off.
"""

import sys

from pyrite.config import KBConfig, PyriteConfig, Settings, _apply_env_overrides
from pyrite.services.kb_service import KBService
from pyrite.storage.database import PyriteDB


def _svc(tmp_path, **settings):
    kb = KBConfig(name="t", path=tmp_path / "kb", kb_type="generic")
    (tmp_path / "kb").mkdir()
    config = PyriteConfig(
        knowledge_bases=[kb], settings=Settings(index_path=tmp_path / "i.db", **settings)
    )
    return KBService(config, PyriteDB(config.settings.index_path))


def test_auto_embed_off_never_touches_the_embedding_stack(tmp_path, monkeypatch):
    svc = _svc(tmp_path, auto_embed=False)
    before = set(sys.modules)
    svc.create_entry("t", "plain", "Plain", "note", "no embedding for me")
    assert svc._get_embedding_svc() is None
    assert not {
        m for m in set(sys.modules) - before if m.startswith(("torch", "sentence_transformers"))
    }


def test_auto_embed_defaults_on():
    assert Settings(index_path="x").auto_embed is True


def test_env_override_turns_it_off(monkeypatch):
    monkeypatch.setenv("PYRITE_AUTO_EMBED", "0")
    config = PyriteConfig(knowledge_bases=[], settings=Settings(index_path="x"))
    _apply_env_overrides(config)
    assert config.settings.auto_embed is False
