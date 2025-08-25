import os
from sam.utils.config import load_config


def bootstrap(cfg_path: str = "sam/ops/config.yaml"):
    cfg = load_config(cfg_path)
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    return cfg