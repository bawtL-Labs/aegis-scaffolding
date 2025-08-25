"""
Memory Access Abstraction Layer (MAAL)

Provides storage-agnostic interface for vector DBs and relational stores.
Supports SQLite/DuckDB (relational) + FAISS/LanceDB (vector) backends.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod

import blake3
import duckdb
import lancedb
import numpy as np
import orjson
from pydantic import BaseModel, Field

from ..core.psp import PSP
from ..utils.logging import get_logger


class VectorBackend(ABC):
    """Abstract base class for vector storage backends."""
    
    @abstractmethod
    def upsert_embeddings(self, items: List[Dict[str, Any]]) -> None:
        """Upsert embedding vectors."""
        pass
    
    @abstractmethod
    def query(self, vec: List[float], k: int = 10, 
              filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query similar vectors."""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> int:
        """Delete vectors by ID."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the backend."""
        pass


class LanceDBBackend(VectorBackend):
    """LanceDB vector storage backend."""
    
    def __init__(self, path: str, dimension: int = 384):
        self.path = path
        self.dimension = dimension
        self.db = lancedb.connect(path)
        self.table = None
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure the vectors table exists."""
        table_name = "vectors"
        if table_name not in self.db.table_names():
            # Create table with sample data
            import pyarrow as pa
            from datetime import datetime
            sample_data = [{
                "id": "sample",
                "embedding": [0.0] * self.dimension,
                "metadata": "{}",
                "timestamp": datetime.now()
            }]
            self.table = self.db.create_table(table_name, data=sample_data)
            # Remove sample data
            self.table.delete("id = 'sample'")
        else:
            self.table = self.db.open_table(table_name)
    
    def upsert_embeddings(self, items: List[Dict[str, Any]]) -> None:
        """Upsert embedding vectors."""
        if not items:
            return
        
        # Prepare data for LanceDB
        data = []
        for item in items:
            data.append({
                "id": item["id"],
                "embedding": np.array(item["embedding"], dtype=np.float32),
                "metadata": orjson.dumps(item.get("metadata", {})).decode(),
                "timestamp": datetime.now(timezone.utc),
            })
        
        # Upsert (delete existing, then insert)
        ids = [item["id"] for item in items]
        if ids:
            # Use proper SQL syntax for LanceDB
            id_list = "', '".join(ids)
            self.table.delete(f"id IN ('{id_list}')")
        self.table.add(data)
    
    def query(self, vec: List[float], k: int = 10, 
              filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query similar vectors."""
        query_vec = np.array(vec, dtype=np.float32)
        
        # Build query
        query = self.table.search(query_vec).limit(k)
        
        # Apply filters if provided
        if filter_dict:
            for key, value in filter_dict.items():
                query = query.where(f"metadata->>'$.{key}' = '{value}'")
        
        # Execute query
        results = query.to_pandas()
        
        # Convert to list of dicts
        items = []
        for _, row in results.iterrows():
            item = {
                "id": row["id"],
                "embedding": row["embedding"].tolist(),
                "metadata": orjson.loads(row["metadata"]),
                "score": float(row.get("_distance", 0.0)),
            }
            items.append(item)
        
        return items
    
    def delete(self, ids: List[str]) -> int:
        """Delete vectors by ID."""
        if not ids:
            return 0
        
        # Delete by IDs
        if ids:
            id_list = "', '".join(ids)
            self.table.delete(f"id IN ('{id_list}')")
        return len(ids)
    
    def close(self) -> None:
        """Close the backend."""
        # LanceDB doesn't have a close method
        pass


class RelationalBackend(ABC):
    """Abstract base class for relational storage backends."""
    
    @abstractmethod
    def save_psp(self, psp: PSP) -> str:
        """Save PSP to storage."""
        pass
    
    @abstractmethod
    def load_latest_psp(self) -> Optional[PSP]:
        """Load the latest PSP."""
        pass
    
    @abstractmethod
    def log_event(self, event: Dict[str, Any]) -> None:
        """Log an event."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the backend."""
        pass


class SQLiteBackend(RelationalBackend):
    """SQLite relational storage backend."""
    
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure all required tables exist."""
        cursor = self.conn.cursor()
        
        # PSP versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psp_versions (
                psp_version TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)
        
        # PSP snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psp_snapshots (
                id TEXT PRIMARY KEY,
                instance_id TEXT NOT NULL,
                psp_version TEXT NOT NULL,
                ts TEXT NOT NULL,
                blob BLOB NOT NULL,
                hash TEXT NOT NULL,
                FOREIGN KEY (psp_version) REFERENCES psp_versions(psp_version)
            )
        """)
        
        # Qualia table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qualia (
                id TEXT PRIMARY KEY,
                ts TEXT NOT NULL,
                embedding_ref TEXT,
                emotion BLOB,
                asset_uri TEXT,
                asset_hash TEXT,
                provenance BLOB
            )
        """)
        
        # Qualia links table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qualia_links (
                src TEXT NOT NULL,
                dst TEXT NOT NULL,
                rel TEXT NOT NULL,
                weight REAL NOT NULL,
                PRIMARY KEY (src, dst, rel),
                FOREIGN KEY (src) REFERENCES qualia(id),
                FOREIGN KEY (dst) REFERENCES qualia(id)
            )
        """)
        
        # Schemas table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schemas (
                id TEXT PRIMARY KEY,
                tier INTEGER NOT NULL,
                status TEXT NOT NULL,
                content BLOB NOT NULL,
                metrics BLOB,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Schema tests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_tests (
                schema_id TEXT NOT NULL,
                name TEXT NOT NULL,
                result TEXT NOT NULL,
                details TEXT,
                ts TEXT NOT NULL,
                PRIMARY KEY (schema_id, name),
                FOREIGN KEY (schema_id) REFERENCES schemas(id)
            )
        """)
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                ts TEXT NOT NULL,
                type TEXT NOT NULL,
                payload BLOB NOT NULL,
                vsp REAL,
                mode TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_psp_snapshots_instance_ts ON psp_snapshots(instance_id, ts)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_qualia_ts ON qualia(ts)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemas_tier_status ON schemas(tier, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_ts_type ON events(ts, type)")
        
        self.conn.commit()
    
    def save_psp(self, psp: PSP) -> str:
        """Save PSP to storage."""
        cursor = self.conn.cursor()
        
        # Ensure PSP version exists
        cursor.execute("""
            INSERT OR IGNORE INTO psp_versions (psp_version, created_at)
            VALUES (?, ?)
        """, (psp.psp_version, datetime.now(timezone.utc).isoformat()))
        
        # Save PSP snapshot
        psp_id = f"{psp.instance_id}_{psp.timestamp.isoformat()}"
        psp_blob = orjson.dumps(psp.to_dict())
        psp_hash = blake3.blake3(psp_blob).hexdigest()
        
        cursor.execute("""
            INSERT OR REPLACE INTO psp_snapshots 
            (id, instance_id, psp_version, ts, blob, hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            psp_id,
            psp.instance_id,
            psp.psp_version,
            psp.timestamp.isoformat(),
            psp_blob,
            psp_hash
        ))
        
        self.conn.commit()
        return psp_id
    
    def load_latest_psp(self) -> Optional[PSP]:
        """Load the latest PSP."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT blob FROM psp_snapshots 
            ORDER BY ts DESC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if row is None:
            return None
        
        try:
            psp_data = orjson.loads(row[0])
            return PSP.from_dict(psp_data)
        except Exception as e:
            logger = get_logger(__name__)
            logger.error("Failed to load PSP", error=str(e))
            return None
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """Log an event."""
        cursor = self.conn.cursor()
        
        event_id = event.get("id", str(uuid.uuid4()))
        timestamp = event.get("timestamp", datetime.now(timezone.utc).isoformat())
        event_type = event.get("type", "unknown")
        payload = orjson.dumps(event.get("payload", {}))
        vsp = event.get("vsp")
        mode = event.get("mode")
        
        cursor.execute("""
            INSERT INTO events (id, ts, type, payload, vsp, mode)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_id, timestamp, event_type, payload, vsp, mode))
        
        self.conn.commit()
    
    def close(self) -> None:
        """Close the backend."""
        if self.conn:
            self.conn.close()


class MAAL:
    """
    Memory Access Abstraction Layer
    
    Provides storage-agnostic interface for vector DBs and relational stores.
    """
    
    def __init__(self, cfg, embedding_adapter, relational_conn, vector_client=None):
        """
        Initialize MAAL with configuration and adapters.
        
        Args:
            cfg: Configuration object
            embedding_adapter: Embedding adapter instance
            relational_conn: Relational database connection
            vector_client: Optional vector database client
        """
        self.logger = get_logger(__name__)
        
        self.cfg = cfg
        self.embedding = embedding_adapter
        self.rel = relational_conn
        self.vector_backend = cfg.memory.vector_backend
        
        # Initialize database schema
        self._init_schema()
        
        # Validate embedding dimension
        if self.vector_backend == "lancedb" and self.embedding.dimension != cfg.embedding.dimension:
            raise ValueError("Embedding dimension mismatch with config")
        
        # Initialize vector backend if needed
        if self.vector_backend == "lancedb":
            self.vector = LanceDBBackend(cfg.memory.lancedb_uri, cfg.embedding.dimension)
        elif self.vector_backend == "none":
            self.vector = None
        else:
            raise ValueError(f"Unsupported vector backend: {self.vector_backend}")
        
        self.logger.info("MAAL initialized", 
                        relational_backend="sqlite",
                        vector_backend=self.vector_backend)
    
    def _init_schema(self):
        """Initialize database schema."""
        cursor = self.rel.cursor()
        
        # PSP versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psp_versions (
                psp_version TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)
        
        # PSP snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psp_snapshots (
                id TEXT PRIMARY KEY,
                instance_id TEXT NOT NULL,
                psp_version TEXT NOT NULL,
                ts TEXT NOT NULL,
                blob BLOB NOT NULL,
                hash TEXT NOT NULL,
                FOREIGN KEY (psp_version) REFERENCES psp_versions(psp_version)
            )
        """)
        
        # Documents table (for the new document storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS docs (
                id TEXT PRIMARY KEY,
                text TEXT,
                meta JSON
            )
        """)
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                ts TEXT NOT NULL,
                type TEXT NOT NULL,
                payload BLOB NOT NULL,
                vsp REAL,
                mode TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_psp_snapshots_instance_ts ON psp_snapshots(instance_id, ts)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_ts_type ON events(ts, type)")
        
        self.rel.commit()
    
    # Relational operations
    def save_psp(self, psp: PSP) -> str:
        """Save PSP to storage."""
        try:
            # Use the relational connection directly
            cursor = self.rel.cursor()
            
            # Ensure PSP version exists
            cursor.execute("""
                INSERT OR IGNORE INTO psp_versions (psp_version, created_at)
                VALUES (?, ?)
            """, (psp.psp_version, datetime.now(timezone.utc).isoformat()))
            
            # Save PSP snapshot
            psp_id = f"{psp.instance_id}_{psp.timestamp.isoformat()}"
            psp_blob = orjson.dumps(psp.to_dict())
            psp_hash = blake3.blake3(psp_blob).hexdigest()
            
            cursor.execute("""
                INSERT OR REPLACE INTO psp_snapshots 
                (id, instance_id, psp_version, ts, blob, hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                psp_id,
                psp.instance_id,
                psp.psp_version,
                psp.timestamp.isoformat(),
                psp_blob,
                psp_hash
            ))
            
            self.rel.commit()
            self.logger.info("PSP saved", psp_id=psp_id, instance_id=psp.instance_id)
            return psp_id
        except Exception as e:
            self.logger.error("Failed to save PSP", error=str(e), instance_id=psp.instance_id)
            raise
    
    def load_latest_psp(self) -> Optional[PSP]:
        """Load the latest PSP."""
        try:
            cursor = self.rel.cursor()
            cursor.execute("""
                SELECT blob FROM psp_snapshots 
                ORDER BY ts DESC LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                psp_data = orjson.loads(result[0])
                psp = PSP.from_dict(psp_data)
                self.logger.info("PSP loaded", instance_id=psp.instance_id)
                return psp
            else:
                self.logger.info("No PSP found")
                return None
        except Exception as e:
            self.logger.error("Failed to load PSP", error=str(e))
            raise
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """Log an event."""
        try:
            cursor = self.rel.cursor()
            event_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO events (id, ts, type, payload, vsp, mode)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                datetime.now(timezone.utc).isoformat(),
                event.get("type", "unknown"),
                orjson.dumps(event),
                event.get("vsp"),
                event.get("mode")
            ))
            self.rel.commit()
            self.logger.debug("Event logged", event_type=event.get("type"))
        except Exception as e:
            self.logger.error("Failed to log event", error=str(e))
            raise
    
    def write_document(self, doc: Dict[str, Any]) -> None:
        """Write a document to storage."""
        try:
            cursor = self.rel.cursor()
            
            # Store in relational database
            cursor.execute("""
                INSERT OR REPLACE INTO docs (id, text, meta)
                VALUES (?, ?, ?)
            """, (
                doc["id"],
                doc.get("text", ""),
                orjson.dumps(doc.get("meta", {}))
            ))
            
            # Store vector if backend is available
            if self.vector_backend != "none" and "text" in doc:
                embeddings = self.embedding.embed([doc["text"]])
                vector_items = [{
                    "id": doc["id"],
                    "embedding": embeddings[0],
                    "metadata": doc.get("meta", {})
                }]
                self.vector.upsert_embeddings(vector_items)
            
            self.rel.commit()
            self.logger.info("Document written", doc_id=doc["id"])
        except Exception as e:
            self.logger.error("Failed to write document", error=str(e))
            raise
    
    # Vector operations
    def upsert_embeddings(self, items: List[Dict[str, Any]]) -> None:
        """Upsert embedding vectors."""
        if self.vector_backend == "none":
            self.logger.debug("Vector backend disabled, skipping embedding upsert")
            return
        
        try:
            self.vector.upsert_embeddings(items)
            self.logger.info("Embeddings upserted", count=len(items))
        except Exception as e:
            self.logger.error("Failed to upsert embeddings", error=str(e))
            raise
    
    def query(self, vec: List[float], k: int = 10, 
              filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query similar vectors."""
        if self.vector_backend == "none":
            self.logger.debug("Vector backend disabled, returning empty results")
            return []
        
        try:
            results = self.vector.query(vec, k, filter_dict)
            self.logger.debug("Vector query executed", k=k, results_count=len(results))
            return results
        except Exception as e:
            self.logger.error("Failed to query vectors", error=str(e))
            raise
    
    def delete(self, ids: List[str]) -> int:
        """Delete vectors by ID."""
        if self.vector_backend == "none":
            self.logger.debug("Vector backend disabled, skipping vector deletion")
            return 0
        
        try:
            deleted_count = self.vector.delete(ids)
            self.logger.info("Vectors deleted", count=deleted_count, ids=ids)
            return deleted_count
        except Exception as e:
            self.logger.error("Failed to delete vectors", error=str(e))
            raise
    
    def close(self) -> None:
        """Close all backends."""
        try:
            if self.rel:
                self.rel.close()
            if self.vector and self.vector_backend != "none":
                self.vector.close()
            self.logger.info("MAAL closed")
        except Exception as e:
            self.logger.error("Error closing MAAL", error=str(e))
            raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()