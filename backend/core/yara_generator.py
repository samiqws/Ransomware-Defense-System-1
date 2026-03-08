"""
YARA Rule Generator for Zero-Day Threats
Generates YARA rules dynamically from confirmed malicious files.
"""

import os
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, List

logger = logging.getLogger(__name__)

class YaraGenerator:
    def __init__(self, rules_dir: str = None):
        if rules_dir is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.rules_dir = os.path.join(backend_dir, "rules", "yara")
        else:
            self.rules_dir = rules_dir
            
        os.makedirs(self.rules_dir, exist_ok=True)
        self.auto_rules_file = os.path.join(self.rules_dir, "auto_generated.yar")
        
    def _calculate_file_hashes(self, file_path: str, chunk_size=8192) -> dict:
        """Calculate fast MD5, SHA1, and SHA256 hashes of a file"""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Read only up to first 50MB to prevent memory/performance issues
                bytes_read = 0
                max_bytes = 50 * 1024 * 1024 
                
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
                    bytes_read += len(chunk)
                    if bytes_read >= max_bytes:
                        break
                        
            return {
                "md5": md5_hash.hexdigest(),
                "sha256": sha256_hash.hexdigest()
            }
        except Exception as e:
            logger.error(f"Failed to calculate hashes for {file_path}: {e}")
            return {}

    def generate_rule_from_file(self, file_path: str, process_name: str = "Unknown") -> bool:
        """
        Dynamically generate a YARA rule for a newly caught zero-day malware.
        Prioritizes speed by using file hashes rather than deep string extraction.
        Checks for duplicates before adding to prevent compilation errors.
        """
        if not os.path.exists(file_path):
            logger.warning(f"Cannot generate YARA rule: File {file_path} no longer exists.")
            return False
            
        try:
            # 1. Calculate File Hashes (Fastest and safest for large binaries)
            hashes = self._calculate_file_hashes(file_path)
            if not hashes:
                return False
                
            md5_str = hashes.get("md5")
            sha256_str = hashes.get("sha256")
            
            # 2. Build the Rule name
            rule_name = f"AutoDetection_{process_name.replace('.exe', '')}_{md5_str[:8]}"
            # Ensure valid YARA identifier
            rule_name = "".join([c if c.isalnum() else "_" for c in rule_name])
            
            # 3. Check for duplicate — read existing file and skip if rule exists
            if os.path.exists(self.auto_rules_file):
                try:
                    with open(self.auto_rules_file, "r", encoding="utf-8") as f:
                        existing_content = f.read()
                    if f"rule {rule_name}" in existing_content:
                        logger.info(f"YARA rule already exists, skipping: {rule_name}")
                        return True  # Not an error, just already exists
                except Exception as e:
                    logger.warning(f"Failed to read existing YARA rules: {e}")
            
            # 4. Build the Rule string
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            yara_rule = f"""
rule {rule_name}
{{
    meta:
        description = "Auto-generated rule for zero-day threat caught by behavioral DB"
        author = "Ransomware Defense System (Auto-Generator)"
        date = "{date_str}"
        original_file = "{os.path.basename(file_path)}"
        process_source = "{process_name}"
        hash_md5 = "{md5_str}"
        hash_sha256 = "{sha256_str}"
    condition:
        hash.md5(0, filesize) == "{md5_str}" or hash.sha256(0, filesize) == "{sha256_str}"
}}
"""
            # 5. If file is new/empty, add the import header first
            needs_header = True
            if os.path.exists(self.auto_rules_file):
                with open(self.auto_rules_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if 'import "hash"' in content:
                        needs_header = False
            
            with open(self.auto_rules_file, "a", encoding="utf-8") as f:
                if needs_header:
                    f.write('// Auto-generated YARA rules\nimport "hash"\n\n')
                f.write(yara_rule + "\n")
                
            logger.info(f"Successfully generated new YARA rule: {rule_name}")
            
            # 6. Trigger re-compilation in the scanner
            try:
                from core.yara_scanner import get_yara_scanner
                scanner = get_yara_scanner()
                scanner.reload_rules()
            except Exception as e:
                logger.warning(f"Could not reload YARA scanner: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating YARA rule for {file_path}: {e}")
            return False

# Singleton instance
_yara_generator = None

def get_yara_generator() -> YaraGenerator:
    """Get or create singleton YaraGenerator instance"""
    global _yara_generator
    if _yara_generator is None:
        _yara_generator = YaraGenerator()
    return _yara_generator
