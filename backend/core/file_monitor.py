import hashlib
import math
import os
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import psutil
import logging
from core.process_cache import get_process_cache
from core.async_entropy import get_entropy_calculator
from core.whitelist_manager import get_whitelist_manager
from core.magic_bytes import verify_file_header

logger = logging.getLogger(__name__)


class FileIntegrityMonitor:
    """File Integrity Monitoring with hash tracking and entropy analysis"""
    
    def __init__(self):
        self.file_hashes: Dict[str, str] = {}
        self.file_metadata: Dict[str, dict] = {}
        self.monitored_paths: Set[str] = set()
    
    def calculate_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of file (OPTIMIZED - uses async calculator)"""
        try:
            entropy_calc = get_entropy_calculator()
            result = entropy_calc.calculate_entropy_sync(file_path)
            return result['hash'] if result else None
        except Exception as e:
            logger.error(f"Hash calculation failed for {file_path}: {e}")
            return None
    
    def calculate_entropy(self, file_path: str) -> Optional[float]:
        """
        Calculate Shannon entropy of file contents (OPTIMIZED - async with caching).
        High entropy (>7.0) suggests encryption or compression.
        """
        try:
            entropy_calc = get_entropy_calculator()
            result = entropy_calc.calculate_entropy_sync(file_path)
            return result['entropy'] if result else None
        except Exception as e:
            logger.error(f"Entropy calculation failed for {file_path}: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> dict:
        """Get comprehensive file information"""
        try:
            stat_info = os.stat(file_path)
            file_hash = self.calculate_hash(file_path)
            entropy = self.calculate_entropy(file_path)
            
            return {
                "path": file_path,
                "hash": file_hash,
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime),
                "created": datetime.fromtimestamp(stat_info.st_ctime),
                "entropy": entropy,
                "extension": os.path.splitext(file_path)[1].lower(),
                "magic_bytes_valid": verify_file_header(file_path)
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    def update_baseline(self, file_path: str):
        """Update baseline hash for a file"""
        info = self.get_file_info(file_path)
        if info and info["hash"]:
            self.file_hashes[file_path] = info["hash"]
            self.file_metadata[file_path] = info
    
    def verify_integrity(self, file_path: str) -> dict:
        """
        Verify file integrity against baseline.
        Returns detection results.
        """
        if file_path not in self.file_hashes:
            # New file
            self.update_baseline(file_path)
            return {
                "status": "new",
                "compromised": False,
                "entropy_suspicious": False
            }
        
        current_info = self.get_file_info(file_path)
        if not current_info or not current_info["hash"]:
            return {
                "status": "error",
                "compromised": False,
                "entropy_suspicious": False
            }
        
        original_hash = self.file_hashes.get(file_path)
        original_info = self.file_metadata.get(file_path, {})
        
        # Check for modifications
        hash_changed = current_info["hash"] != original_hash
        
        # Check for high entropy (encryption indicator)
        entropy_suspicious = current_info["entropy"] and current_info["entropy"] > 7.0
        
        # Check for extension change
        extension_changed = (
            original_info.get("extension") != current_info["extension"]
        )
        
        result = {
            "status": "modified" if hash_changed else "unchanged",
            "compromised": hash_changed,
            "entropy_suspicious": entropy_suspicious,
            "extension_changed": extension_changed,
            "original_hash": original_hash,
            "current_hash": current_info["hash"],
            "original_entropy": original_info.get("entropy"),
            "current_entropy": current_info["entropy"],
            "original_extension": original_info.get("extension"),
            "current_extension": current_info["extension"],
            "magic_bytes_valid": current_info.get("magic_bytes_valid", True)
        }
        
        # Update baseline if changed
        if hash_changed:
            self.update_baseline(file_path)
        
        return result


class RansomwareEventHandler(FileSystemEventHandler):
    """Custom event handler for file system monitoring"""
    
    def __init__(self, callback, file_protector=None, monitoring_config=None):
        super().__init__()
        self.callback = callback
        self.file_monitor = FileIntegrityMonitor()
        self.file_protector = file_protector
        self.monitoring_config = monitoring_config
        self.process_cache = {}  # Cache recent processes
        self.cache_time = 10  # Cache for 10 seconds (increased for performance)
        self.directory_activity = {}  # Track which processes are active in which directories
        self.last_process_per_dir = {}  # Remember last known process per directory
    
    def get_process_info(self, file_path: str = None) -> dict:
        """Get information about the process that triggered the event (OPTIMIZED)"""
        try:
            # Use professional ProcessCache for 10x performance improvement
            process_cache = get_process_cache()
            result = process_cache.get_process_by_path(file_path, timeout=1.5)
            
            if result:
                return result
            
            # Fallback
            return {"name": "FileSystem", "pid": 0, "exe": "Unknown Process"}
            
        except Exception as e:
            logger.error(f"Failed to get process info: {e}")
            return {"name": "Unknown", "pid": 0, "exe": ""}
    
    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event("modified", event.src_path)
    
    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event("created", event.src_path)
    
    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event("deleted", event.src_path)
    
    def on_moved(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event("moved", event.dest_path, event.src_path)
    
    def _handle_event(self, event_type: str, file_path: str, old_path: str = None):
        """Handle file system event"""
        try:
            # Skip temporary, system files, and database files
            skip_patterns = [
                'tmp', 'temp', '$recycle',
                '.db-shm', '.db-wal', '.db-journal',  # SQLite temp files
                '.db',  # All database files
                'ransomware_defense.db',  # Our own database
                'file_backups',  # Don't monitor backup folder itself!
                '\\logs\\',  # Skip log files
                '__pycache__',  # Skip Python cache
                '.git',  # Skip git files
                '\\backend\\data\\'  # Skip backend data folder only
            ]
            
            # Skip only files matching noise patterns above
            if any(x in file_path.lower() for x in skip_patterns):
                return
            
            # فحص نوع المراقبة المفعل
            if self.monitoring_config:
                # إذا كان الملف من ملفات النظام
                is_system_file = any(sys_path in file_path for sys_path in [
                    'C:\\Windows', 'C:\\Program Files'
                ])
                
                if is_system_file and not self.monitoring_config.is_system_files_enabled():
                    return  # تجاهل ملفات النظام إذا كانت معطلة
                
                # إذا كان الملف من ملفات المستخدم
                is_user_file = any(user_path in file_path for user_path in [
                    '\\Documents\\', '\\Desktop\\', '\\Pictures\\', 
                    '\\Downloads\\', '\\Videos\\'
                ])
                
                if is_user_file and not self.monitoring_config.is_user_files_enabled():
                    return  # تجاهل ملفات المستخدم إذا كانت معطلة
            
            # النسخ الاحتياطي التلقائي قبل التعديل
            if self.file_protector and event_type == "modified" and os.path.exists(file_path):
                self.file_protector.create_backup(file_path)
            
            # Get actual process that modified the file
            process_info = self.get_process_info(file_path)
            
            # ✅ SECURITY: Ignore events generated by our own backend process (e.g. UI file deletions, decoy management)
            if process_info.get('pid') == os.getpid():
                logger.debug("Ignoring event generated by the defense system itself")
                return
            
            # ✅ WHITELIST CHECK - Skip analysis for trusted processes
            whitelist = get_whitelist_manager()
            if whitelist.is_whitelisted(
                process_name=process_info.get('name'),
                process_path=process_info.get('exe')
            ):
                logger.debug(f"Whitelisted process {process_info.get('name')} - skipping analysis")
                return  # Skip analysis for trusted process
            
            # Verify file integrity and run YARA scan
            integrity_result = None
            yara_result = {"matches": False, "rules": []}
            
            if event_type in ["modified", "created"] and os.path.exists(file_path):
                integrity_result = self.file_monitor.verify_integrity(file_path)
                # Run YARA malware scan if enabled
                try:
                    is_yara_enabled = True
                    if self.monitoring_config:
                        is_yara_enabled = self.monitoring_config.is_yara_scanning_enabled()
                        
                    if is_yara_enabled:
                        from core.yara_scanner import get_yara_scanner
                        yara_scanner = get_yara_scanner()
                        yara_result = yara_scanner.scan_file(file_path)
                except Exception as e:
                    logger.error(f"Failed to run YARA scan on {file_path}: {e}")
            
            event_data = {
                "type": event_type,
                "path": file_path,
                "old_path": old_path,
                "timestamp": datetime.now(timezone.utc),
                "process": process_info,
                "integrity": integrity_result,
                "yara": yara_result
            }
            
            # Call the callback (it will handle async execution)
            if self.callback:
                self.callback(event_data)
        except Exception as e:
            logger.error(f"Event handling error: {e}")


class FileSystemMonitor:
    """Main file system monitoring orchestrator"""
    
    def __init__(self, protected_paths: List[str], callback, loop=None, file_protector=None, monitoring_config=None):
        self.protected_paths = protected_paths
        self.callback = callback
        self.loop = loop
        self.file_protector = file_protector
        self.monitoring_config = monitoring_config
        self.observers: List[Observer] = []
        self.event_handler = None
        self.is_running = False
    
    def start(self):
        """Start monitoring protected paths"""
        logger.info(f"Starting file system monitoring for {len(self.protected_paths)} paths")
        
        # Log monitoring modes
        if self.monitoring_config:
            modes = self.monitoring_config.get_all_modes()
            logger.info(f"Monitoring modes: User Files={modes['user_files']}, "
                       f"Decoy Files={modes['decoy_files']}, System Files={modes['system_files']}")
        
        # Create event handler if not already created
        if self.event_handler is None:
            self.event_handler = RansomwareEventHandler(
                self.callback, 
                self.file_protector,
                self.monitoring_config
            )
        
        for path in self.protected_paths:
            if os.path.exists(path):
                observer = Observer()
                observer.schedule(
                    self.event_handler,
                    path,
                    recursive=True
                )
                observer.start()
                self.observers.append(observer)
                logger.info(f"Monitoring: {path}")
            else:
                logger.warning(f"Path does not exist: {path}")
        
        self.is_running = True
    
    def stop(self):
        """Stop all monitoring"""
        logger.info("Stopping file system monitoring")
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers.clear()
        self.is_running = False
    
    def add_path(self, path: str):
        """Add a new path to monitor"""
        if path not in self.protected_paths and os.path.exists(path):
            self.protected_paths.append(path)
            if self.is_running:
                observer = Observer()
                observer.schedule(
                    self.event_handler,
                    path,
                    recursive=True
                )
                observer.start()
                self.observers.append(observer)
                logger.info(f"Added monitoring for: {path}")
