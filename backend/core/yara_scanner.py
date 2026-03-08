import os
import yara
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class YaraScanner:
    """
    YARA Scanner for detecting known malware signatures.
    Compiles rules from the rules/yara directory on startup.
    """
    def __init__(self, rules_dir: str = None):
        if rules_dir is None:
            # Default to backend/rules/yara
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.rules_dir = os.path.join(backend_dir, "rules", "yara")
        else:
            self.rules_dir = rules_dir
            
        self.rules = None
        self.last_compiled = None
        self._compile_rules()

    def _compile_rules(self) -> bool:
        """Compile all .yar files in the rules directory"""
        try:
            if not os.path.exists(self.rules_dir):
                logger.warning(f"YARA rules directory not found: {self.rules_dir}")
                os.makedirs(self.rules_dir, exist_ok=True)
                return False

            filepaths = {}
            for root, _, files in os.walk(self.rules_dir):
                for file in files:
                    if file.endswith('.yar') or file.endswith('.yara'):
                        rule_path = os.path.join(root, file)
                        # The key is a namespace name
                        namespace = os.path.splitext(file)[0]
                        filepaths[namespace] = rule_path

            if not filepaths:
                logger.info("No YARA rules found to compile.")
                return False

            self.rules = yara.compile(filepaths=filepaths)
            self.last_compiled = datetime.now()
            logger.info(f"YARA rules compiled successfully from {len(filepaths)} files.")
            return True

        except yara.SyntaxError as e:
            logger.error(f"Syntax error compiling YARA rules: {e}")
            self.rules = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error compiling YARA rules: {e}", exc_info=True)
            self.rules = None
            return False

    def reload_rules(self) -> bool:
        """Force a reload of the YARA rules"""
        logger.info("Reloading YARA rules...")
        return self._compile_rules()

    def scan_file(self, file_path: str) -> Dict:
        """
        Scan a file against compiled YARA rules.
        Returns a dict: {"matches": bool, "rules": [rule_name_1, ...]}
        """
        result = {"matches": False, "rules": []}
        
        if not self.rules:
            logger.debug("YARA rules not loaded, skipping scan.")
            return result
            
        if not os.path.exists(file_path):
            logger.debug(f"File not found for YARA scanning: {file_path}")
            return result
            
        try:
            # Limit scan time to prevent performance issues (e.g. 5 seconds)
            matches = self.rules.match(file_path, timeout=5)
            
            if matches:
                result["matches"] = True
                result["rules"] = [match.rule for match in matches]
                logger.warning(f"YARA MATCH DETECTED in {file_path}: {result['rules']}")
                
        except yara.TimeoutError:
            logger.warning(f"YARA scan timeout for file: {file_path}")
        except yara.Error as e:
            # yara.Error could be triggered if file is inaccessible
            logger.debug(f"YARA scan error for {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during YARA scan of {file_path}: {e}")
            
        return result

# Singleton instance
_yara_scanner = None

def get_yara_scanner() -> YaraScanner:
    """Get or create singleton YaraScanner instance"""
    global _yara_scanner
    if _yara_scanner is None:
        _yara_scanner = YaraScanner()
    return _yara_scanner
