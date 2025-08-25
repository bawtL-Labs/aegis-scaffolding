from fastapi import FastAPI
from pydantic import BaseModel
from sam.utils.config import load_config
from sam.memory.rel_sqlite import open_sqlite
from sam.models.embedding_minilm import MiniLMAdapter
from sam.memory.maal import MAAL

app = FastAPI()
cfg = load_config("sam/ops/config.yaml")
conn = open_sqlite(cfg.memory.sqlite_path)
embed = MiniLMAdapter(cfg.embedding.model)
maal = MAAL(cfg, embed, conn, vector_client=None)


class IngestIn(BaseModel):
    id: str
    text: str
    meta: dict = {}


@app.post("/ingest")
def ingest(i: IngestIn):
    # minimal path
    maal.write_document({"id": i.id, "text": i.text, "meta": i.meta})
    return {"status": "ok"}