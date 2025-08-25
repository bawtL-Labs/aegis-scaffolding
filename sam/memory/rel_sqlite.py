import sqlite3
import os

DDL = """
CREATE TABLE IF NOT EXISTS docs(
  id TEXT PRIMARY KEY,
  text TEXT,
  meta JSON
);
"""


def open_sqlite(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(DDL)
    return conn