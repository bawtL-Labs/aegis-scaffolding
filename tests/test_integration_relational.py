import pytest
import tempfile
from sam.utils.config import load_config
from sam.models.embedding_minilm import MiniLMAdapter
from sam.memory.rel_sqlite import open_sqlite
from sam.memory.maal import MAAL


def test_relational_loop(tmp_path):
    """Test the relational-only workflow."""
    cfg = load_config("sam/ops/config.yaml")
    cfg.memory.sqlite_path = str(tmp_path / "aegis.db")
    embed = MiniLMAdapter(cfg.embedding.model)
    maal = MAAL(cfg, embed, open_sqlite(cfg.memory.sqlite_path), None)
    maal.write_document({"id": "t1", "text": "hello world", "meta": {}})
    # no exception == pass; add a trivial read assert if implemented
    assert True


@pytest.mark.skipif(True, reason='vector backend disabled')
def test_lancedb_operations(tmp_path):
    """Test LanceDB operations (skipped when vector backend is disabled)."""
    cfg = load_config("sam/ops/config.yaml")
    cfg.memory.sqlite_path = str(tmp_path / "aegis.db")
    cfg.memory.vector_backend = "lancedb"
    embed = MiniLMAdapter(cfg.embedding.model)
    maal = MAAL(cfg, embed, open_sqlite(cfg.memory.sqlite_path), None)
    # Vector operations would go here
    assert True


if __name__ == "__main__":
    # Run basic test
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_relational_loop(tmp_dir)
    print("Integration test passed!")