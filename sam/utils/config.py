from pydantic import BaseModel, Field, ValidationError
import yaml
import sys


class EmbeddingCfg(BaseModel):
    model: str
    dimension: int = Field(gt=0)
    batch_size: int = 16


class MemoryCfg(BaseModel):
    relational_backend: str
    vector_backend: str  # "none" or "lancedb"
    sqlite_path: str
    lancedb_uri: str


class ApiCfg(BaseModel):
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8080


class LoggingCfg(BaseModel):
    level: str = "INFO"
    json: bool = True
    rotate_mb: int = 20
    backups: int = 7


class SecurityCfg(BaseModel):
    keystore_path: str
    key_derivation: str = "argon2id"
    file_cipher: str = "chacha20poly1305"


class AppCfg(BaseModel):
    name: str = "aegis"
    env: str = "dev"


class Cfg(BaseModel):
    app: AppCfg
    logging: LoggingCfg
    api: ApiCfg
    embedding: EmbeddingCfg
    memory: MemoryCfg
    security: SecurityCfg


def load_config(path: str) -> Cfg:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    try:
        cfg = Cfg(**raw)
    except ValidationError as e:
        print("Config validation error:", e, file=sys.stderr)
        raise
    if cfg.memory.vector_backend not in ("none", "lancedb"):
        raise ValueError("memory.vector_backend must be 'none' or 'lancedb'")
    return cfg