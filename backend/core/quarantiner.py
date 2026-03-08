import os
import shutil
import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class Quarantiner:
    """
    Handles safe quarantine, restoration, and permanent deletion of malicious files.
    """
    def __init__(self, quarantine_dir: str = None):
        if quarantine_dir is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.quarantine_dir = os.path.join(backend_dir, "data", "quarantine")
        else:
            self.quarantine_dir = quarantine_dir
            
        os.makedirs(self.quarantine_dir, exist_ok=True)
        # To prevent accidental execution, we can use a custom extension
        self.q_ext = ".quarantine"

    def _hash_file(self, file_path: str) -> str:
        """Calculate SHA256 of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""

    def quarantine_file(self, file_path: str, incident_id: str) -> dict:
        """
        Moves a malicious file to the quarantine directory to prevent execution.
        Returns details of the quarantine action.
        """
        if not file_path or not os.path.exists(file_path):
            return {
                "success": False,
                "error": "File not found",
                "original_path": file_path
            }
            
        try:
            file_hash = self._hash_file(file_path)
            base_name = os.path.basename(file_path)
            timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            
            # Create safe quarantine name: incident_timestamp_hash.quarantine
            safe_name = f"{incident_id}_{timestamp_str}_{file_hash[:8]}{self.q_ext}"
            quarantine_path = os.path.join(self.quarantine_dir, safe_name)
            
            # Move file to quarantine
            shutil.move(file_path, quarantine_path)
            logger.warning(f"File quarantined: {file_path} -> {quarantine_path}")
            
            return {
                "success": True,
                "original_path": file_path,
                "quarantine_path": quarantine_path,
                "file_hash": file_hash
            }
            
        except Exception as e:
            logger.error(f"Failed to quarantine file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_path": file_path
            }

    def restore_file(self, quarantine_path: str, original_path: str) -> bool:
        """
        Restore a file from quarantine to its original location.
        """
        if not os.path.exists(quarantine_path):
            logger.error(f"Quarantined file not found: {quarantine_path}")
            return False
            
        try:
            # Ensure target directory exists
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            
            # Don't overwrite existing files with the same name during restore without care
            # If the file already exists, we might need to suffix it, but for a true restore we move it back
            if os.path.exists(original_path):
                logger.warning(f"File already exists at {original_path}, overwriting during restore.")
                
            shutil.move(quarantine_path, original_path)
            logger.info(f"File restored successfully: {quarantine_path} -> {original_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore file {quarantine_path}: {e}")
            return False

    def delete_file(self, quarantine_path: str) -> bool:
        """
        Permanently delete a quarantined file.
        """
        if not os.path.exists(quarantine_path):
            logger.warning(f"Quarantined file already deleted or missing: {quarantine_path}")
            return True # Consider it a success if it's already gone
            
        try:
            os.remove(quarantine_path)
            logger.info(f"Permanently deleted quarantined file: {quarantine_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete quarantined file {quarantine_path}: {e}")
            return False

# Singleton instance
_quarantiner = None

def get_quarantiner() -> Quarantiner:
    """Get or create singleton Quarantiner instance"""
    global _quarantiner
    if _quarantiner is None:
        _quarantiner = Quarantiner()
    return _quarantiner
