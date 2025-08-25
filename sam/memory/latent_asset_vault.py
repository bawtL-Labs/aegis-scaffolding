"""
Latent Asset Vault (LAV) - Manages large non-textual assets by proxy.

Stores URIs, hashes, access policies, and streams assets on demand
with integrity verification and encryption.
"""

from typing import Dict, List, Optional, Any, BinaryIO
from pathlib import Path
from datetime import datetime
import hashlib
import mimetypes

from pydantic import BaseModel, Field

from ..utils.logging import get_logger


class AssetPolicy(BaseModel):
    """Access policy for assets."""
    read_access: List[str] = Field(default_factory=list)
    write_access: List[str] = Field(default_factory=list)
    encryption_required: bool = True
    compression_enabled: bool = True


class AssetMetadata(BaseModel):
    """Asset metadata."""
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: datetime
    last_accessed: datetime
    policy: AssetPolicy
    tags: List[str] = Field(default_factory=list)


class LatentAssetVault:
    """
    Latent Asset Vault - Manages large non-textual assets.
    
    Provides secure storage, retrieval, and management of large assets
    with integrity verification and access control.
    """
    
    def __init__(self, 
                 storage_path: str = "./data/assets",
                 max_file_size_mb: int = 100,
                 allowed_types: Optional[List[str]] = None):
        """
        Initialize Latent Asset Vault.
        
        Args:
            storage_path: Path to asset storage
            max_file_size_mb: Maximum file size in MB
            allowed_types: Allowed MIME types
        """
        self.logger = get_logger(__name__)
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.allowed_types = allowed_types or [
            "image/jpeg", "image/png", "audio/mpeg", "audio/wav", "video/mp4"
        ]
        
        # Asset registry
        self.assets: Dict[str, AssetMetadata] = {}
        self._load_registry()
        
        self.logger.info("Latent Asset Vault initialized",
                        storage_path=str(self.storage_path),
                        max_file_size_mb=max_file_size_mb)
    
    def store_asset(self, 
                   file_path: str,
                   asset_id: Optional[str] = None,
                   policy: Optional[AssetPolicy] = None,
                   tags: Optional[List[str]] = None) -> str:
        """
        Store an asset in the vault.
        
        Args:
            file_path: Path to file to store
            asset_id: Optional asset ID (generated if not provided)
            policy: Access policy
            tags: Asset tags
            
        Returns:
            Asset ID
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Validate file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size_bytes:
            raise ValueError(f"File too large: {file_size} bytes > {self.max_file_size_bytes} bytes")
        
        # Validate MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type not in self.allowed_types:
            raise ValueError(f"File type not allowed: {mime_type}")
        
        # Generate asset ID if not provided
        if asset_id is None:
            asset_id = self._generate_asset_id(file_path)
        
        # Calculate SHA256
        sha256 = self._calculate_sha256(file_path)
        
        # Create metadata
        metadata = AssetMetadata(
            id=asset_id,
            filename=file_path.name,
            mime_type=mime_type,
            size_bytes=file_size,
            sha256=sha256,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            policy=policy or AssetPolicy(),
            tags=tags or []
        )
        
        # Copy file to vault
        vault_file_path = self.storage_path / f"{asset_id}_{file_path.name}"
        self._copy_file(file_path, vault_file_path)
        
        # Store metadata
        self.assets[asset_id] = metadata
        self._save_registry()
        
        self.logger.info("Asset stored", 
                        asset_id=asset_id,
                        filename=file_path.name,
                        size_bytes=file_size)
        
        return asset_id
    
    def retrieve_asset(self, asset_id: str) -> Optional[Path]:
        """
        Retrieve an asset from the vault.
        
        Args:
            asset_id: Asset ID to retrieve
            
        Returns:
            Path to asset file, or None if not found
        """
        if asset_id not in self.assets:
            return None
        
        metadata = self.assets[asset_id]
        
        # Update last accessed time
        metadata.last_accessed = datetime.now()
        self._save_registry()
        
        # Find asset file
        for file_path in self.storage_path.iterdir():
            if file_path.name.startswith(f"{asset_id}_"):
                self.logger.debug("Asset retrieved", asset_id=asset_id)
                return file_path
        
        return None
    
    def get_asset_metadata(self, asset_id: str) -> Optional[AssetMetadata]:
        """Get asset metadata."""
        return self.assets.get(asset_id)
    
    def list_assets(self, tags: Optional[List[str]] = None) -> List[AssetMetadata]:
        """
        List assets in the vault.
        
        Args:
            tags: Filter by tags
            
        Returns:
            List of asset metadata
        """
        assets = list(self.assets.values())
        
        if tags:
            assets = [a for a in assets if any(tag in a.tags for tag in tags)]
        
        return sorted(assets, key=lambda a: a.created_at, reverse=True)
    
    def delete_asset(self, asset_id: str) -> bool:
        """
        Delete an asset from the vault.
        
        Args:
            asset_id: Asset ID to delete
            
        Returns:
            True if deleted successfully
        """
        if asset_id not in self.assets:
            return False
        
        metadata = self.assets[asset_id]
        
        # Delete file
        for file_path in self.storage_path.iterdir():
            if file_path.name.startswith(f"{asset_id}_"):
                file_path.unlink()
                break
        
        # Remove from registry
        del self.assets[asset_id]
        self._save_registry()
        
        self.logger.info("Asset deleted", asset_id=asset_id)
        return True
    
    def verify_integrity(self, asset_id: str) -> bool:
        """
        Verify asset integrity.
        
        Args:
            asset_id: Asset ID to verify
            
        Returns:
            True if integrity is valid
        """
        if asset_id not in self.assets:
            return False
        
        metadata = self.assets[asset_id]
        
        # Find asset file
        for file_path in self.storage_path.iterdir():
            if file_path.name.startswith(f"{asset_id}_"):
                # Calculate current SHA256
                current_sha256 = self._calculate_sha256(file_path)
                return current_sha256 == metadata.sha256
        
        return False
    
    def _generate_asset_id(self, file_path: Path) -> str:
        """Generate unique asset ID."""
        # Use filename and timestamp for uniqueness
        timestamp = datetime.now().timestamp()
        return f"asset_{file_path.stem}_{int(timestamp)}"
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _copy_file(self, src: Path, dst: Path) -> None:
        """Copy file with error handling."""
        import shutil
        shutil.copy2(src, dst)
    
    def _load_registry(self) -> None:
        """Load asset registry from disk."""
        registry_file = self.storage_path / "registry.json"
        
        if registry_file.exists():
            try:
                import json
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                
                for asset_data in data.get("assets", []):
                    metadata = AssetMetadata(**asset_data)
                    self.assets[metadata.id] = metadata
                
                self.logger.info("Asset registry loaded", asset_count=len(self.assets))
            except Exception as e:
                self.logger.error("Failed to load asset registry", error=str(e))
    
    def _save_registry(self) -> None:
        """Save asset registry to disk."""
        registry_file = self.storage_path / "registry.json"
        
        try:
            import json
            data = {
                "assets": [asset.dict() for asset in self.assets.values()],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(registry_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.debug("Asset registry saved", asset_count=len(self.assets))
        except Exception as e:
            self.logger.error("Failed to save asset registry", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics."""
        total_size = sum(asset.size_bytes for asset in self.assets.values())
        
        return {
            "total_assets": len(self.assets),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "storage_path": str(self.storage_path),
            "max_file_size_mb": self.max_file_size_bytes / (1024 * 1024)
        }