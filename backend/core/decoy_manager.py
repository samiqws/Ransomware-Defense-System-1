import os
import random
import string
import hashlib
import logging
from typing import List, Dict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class DecoyFileManager:
    """Creates and manages decoy/honeypot files to detect ransomware"""
    
    def __init__(self, decoy_config: dict):
        self.config = decoy_config
        self.decoy_registry: Dict[str, dict] = {}
        # Allow config to override the decoy directory, otherwise use a safe default
        self.decoy_dir = decoy_config.get(
            "decoy_dir",
            "C:\\Users\\Public\\Documents\\RansomwareDefense\\Decoys"
        )
        
    def create_decoy_files(self, count: int = 50) -> List[dict]:
        """Create multiple decoy files across different locations"""
        os.makedirs(self.decoy_dir, exist_ok=True)
        
        created_decoys = []
        file_types = self.config.get("file_types", ["pdf", "docx", "xlsx", "jpg", "txt"])
        naming_patterns = self.config.get("naming_patterns", ["Document", "File", "Data"])
        
        for i in range(count):
            file_type = random.choice(file_types)
            name_pattern = random.choice(naming_patterns)
            
            filename = f"{name_pattern}_{random.randint(1000, 9999)}.{file_type}"
            file_path = os.path.join(self.decoy_dir, filename)
            
            try:
                # Create decoy with realistic content
                content = self._generate_decoy_content(file_type)
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Calculate hash
                file_hash = hashlib.sha256(content).hexdigest()
                
                decoy_info = {
                    "path": file_path,
                    "hash": file_hash,
                    "type": file_type,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "size": len(content)
                }
                
                self.decoy_registry[file_path] = decoy_info
                created_decoys.append(decoy_info)
                
            except Exception as e:
                logger.error(f"Failed to create decoy {file_path}: {e}")
        
        logger.info(f"Created {len(created_decoys)} decoy files")
        return created_decoys
    
    def _generate_decoy_content(self, file_type: str) -> bytes:
        """Generate realistic decoy file content"""
        
        if file_type == "txt":
            content = "CONFIDENTIAL DOCUMENT\n\n"
            content += "Financial Records 2024\n"
            content += "Employee Database\n"
            content += "\n".join([f"Record {i}: {self._random_string(20)}" for i in range(50)])
            return content.encode('utf-8')
        
        elif file_type == "pdf":
            # Minimal PDF structure
            pdf_content = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj
4 0 obj << /Length 44 >> stream
BT /F1 12 Tf 100 700 Td (Confidential Data) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000314 00000 n
trailer << /Size 5 /Root 1 0 R >>
startxref
407
%%EOF"""
            return pdf_content
        
        elif file_type in ["docx", "xlsx"]:
            # Random binary data mimicking Office files
            return os.urandom(random.randint(1024, 4096))
        
        elif file_type == "jpg":
            # Minimal JPEG header
            jpg_header = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            return jpg_header + os.urandom(2048) + b'\xFF\xD9'
        
        else:
            # Generic binary content
            return os.urandom(random.randint(512, 2048))
    
    def _random_string(self, length: int) -> str:
        """Generate random string"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def verify_decoy(self, file_path: str) -> dict:
        """Verify if a decoy file has been tampered with"""
        if file_path not in self.decoy_registry:
            return {"is_decoy": False, "compromised": False}
        
        original_info = self.decoy_registry[file_path]
        
        try:
            if not os.path.exists(file_path):
                return {
                    "is_decoy": True,
                    "compromised": True,
                    "reason": "deleted",
                    "original_hash": original_info["hash"]
                }
            
            with open(file_path, 'rb') as f:
                current_content = f.read()
            
            current_hash = hashlib.sha256(current_content).hexdigest()
            
            if current_hash != original_info["hash"]:
                return {
                    "is_decoy": True,
                    "compromised": True,
                    "reason": "modified",
                    "original_hash": original_info["hash"],
                    "current_hash": current_hash
                }
            
            return {
                "is_decoy": True,
                "compromised": False,
                "hash": current_hash
            }
            
        except Exception as e:
            logger.error(f"Decoy verification error for {file_path}: {e}")
            return {
                "is_decoy": True,
                "compromised": True,
                "reason": "verification_error",
                "error": str(e)
            }
    
    def is_decoy_file(self, file_path: str) -> bool:
        """Check if a file is a decoy"""
        return file_path in self.decoy_registry
    
    def cleanup_decoys(self):
        """Remove all decoy files"""
        removed = 0
        for file_path in list(self.decoy_registry.keys()):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                removed += 1
            except Exception as e:
                logger.error(f"Failed to remove decoy {file_path}: {e}")
        
        self.decoy_registry.clear()
        logger.info(f"Removed {removed} decoy files")
        return removed
