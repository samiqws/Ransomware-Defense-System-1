"""
Professional Whitelist Manager
Reduces false positives by maintaining a list of trusted processes
"""

import logging
import json
import os
from typing import List, Dict, Optional, Set
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class WhitelistManager:
    """
    Manages a whitelist of trusted processes and executables.
    Reduces false positives by skipping analysis for known safe processes.
    """
    
    # Default trusted processes (common legitimate software)
    DEFAULT_WHITELIST = {
        # Microsoft Office
        'winword.exe': 'Microsoft Word',
        'excel.exe': 'Microsoft Excel',
        'powerpnt.exe': 'Microsoft PowerPoint',
        'outlook.exe': 'Microsoft Outlook',
        'onenote.exe': 'Microsoft OneNote',
        
        # Browsers
        'chrome.exe': 'Google Chrome',
        'firefox.exe': 'Mozilla Firefox',
        'msedge.exe': 'Microsoft Edge',
        'brave.exe': 'Brave Browser',
        
        # Code Editors
        'code.exe': 'Visual Studio Code',
        'devenv.exe': 'Visual Studio',
        'pycharm64.exe': 'PyCharm',
        'sublime_text.exe': 'Sublime Text',
        'notepad++.exe': 'Notepad++',
        
        # Media Players
        'vlc.exe': 'VLC Media Player',
        'spotify.exe': 'Spotify',
        
        # System Tools
        'explorer.exe': 'Windows Explorer',
        'taskmgr.exe': 'Task Manager',
        'filesystem': 'Windows File System Operations',
        'system': 'Windows System Process',
        'svchost.exe': 'Service Host Process',
        
        # Compression Tools
        'winrar.exe': 'WinRAR',
        '7zg.exe': '7-Zip',
        
        # Adobe
        'acrobat.exe': 'Adobe Acrobat',
        'photoshop.exe': 'Adobe Photoshop',
    }
    
    def __init__(self, whitelist_file: str = None):
        """
        Initialize whitelist manager.
        
        Args:
            whitelist_file: Path to JSON file storing whitelist (optional)
        """
        self.whitelist_file = whitelist_file or "data/whitelist.json"
        self.whitelist: Dict[str, Dict] = {}
        self.whitelist_paths: Set[str] = set()  # Full executable paths
        
        # Performance metrics
        self.checks_performed = 0
        self.whitelist_hits = 0
        
        # Load whitelist
        self._load_whitelist()
        
        logger.info(f"WhitelistManager initialized with {len(self.whitelist)} entries")
    
    def _load_whitelist(self):
        """Load whitelist from file or use defaults"""
        try:
            if os.path.exists(self.whitelist_file):
                with open(self.whitelist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.whitelist = data.get('processes', {})
                    self.whitelist_paths = set(data.get('paths', []))
                logger.info(f"Loaded whitelist from {self.whitelist_file}")
            else:
                # Use defaults
                self.whitelist = {
                    name: {
                        'description': desc,
                        'added_date': datetime.now(timezone.utc).isoformat(),
                        'auto_detected': True
                    }
                    for name, desc in self.DEFAULT_WHITELIST.items()
                }
                self._save_whitelist()
                logger.info("Created default whitelist")
        
        except Exception as e:
            logger.error(f"Failed to load whitelist: {e}")
            # Fallback to defaults
            self.whitelist = {
                name: {'description': desc, 'auto_detected': True}
                for name, desc in self.DEFAULT_WHITELIST.items()
            }
    
    def _save_whitelist(self):
        """Save whitelist to file"""
        try:
            # Ensure directory exists (handle case where dirname returns "")
            dir_path = os.path.dirname(os.path.abspath(self.whitelist_file))
            os.makedirs(dir_path, exist_ok=True)
            
            data = {
                'processes': self.whitelist,
                'paths': list(self.whitelist_paths),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Whitelist saved to {self.whitelist_file}")
        
        except Exception as e:
            logger.error(f"Failed to save whitelist: {e}")
    
    def is_whitelisted(self, process_name: str = None, process_path: str = None) -> bool:
        """
        Check if a process is whitelisted.
        
        Args:
            process_name: Name of the process (e.g., 'chrome.exe')
            process_path: Full path to executable
        
        Returns:
            True if whitelisted, False otherwise
        """
        self.checks_performed += 1
        
        # Check by process name
        if process_name:
            process_name_lower = process_name.lower()
            if process_name_lower in self.whitelist:
                self.whitelist_hits += 1
                logger.debug(f"Process whitelisted: {process_name}")
                return True
        
        # Check by full path
        if process_path:
            process_path_normalized = os.path.normpath(process_path).lower()
            if process_path_normalized in self.whitelist_paths:
                self.whitelist_hits += 1
                logger.debug(f"Path whitelisted: {process_path}")
                return True
        
        return False
    
    def add_to_whitelist(self, process_name: str, description: str = "", 
                        process_path: str = None, auto_detected: bool = False) -> bool:
        """
        Add a process to whitelist.
        
        Args:
            process_name: Name of the process
            description: Human-readable description
            process_path: Optional full path
            auto_detected: Whether automatically detected
        
        Returns:
            True if added successfully
        """
        try:
            process_name_lower = process_name.lower()
            
            self.whitelist[process_name_lower] = {
                'description': description or process_name,
                'added_date': datetime.now(timezone.utc).isoformat(),
                'auto_detected': auto_detected
            }
            
            if process_path:
                self.whitelist_paths.add(os.path.normpath(process_path).lower())
            
            self._save_whitelist()
            logger.info(f"Added to whitelist: {process_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to add to whitelist: {e}")
            return False
    
    def remove_from_whitelist(self, process_name: str = None, 
                             process_path: str = None) -> bool:
        """
        Remove a process from whitelist.
        
        Args:
            process_name: Name of the process
            process_path: Full path to remove
        
        Returns:
            True if removed successfully
        """
        try:
            removed = False
            
            if process_name:
                process_name_lower = process_name.lower()
                if process_name_lower in self.whitelist:
                    del self.whitelist[process_name_lower]
                    removed = True
            
            if process_path:
                process_path_normalized = os.path.normpath(process_path).lower()
                if process_path_normalized in self.whitelist_paths:
                    self.whitelist_paths.remove(process_path_normalized)
                    removed = True
            
            if removed:
                self._save_whitelist()
                logger.info(f"Removed from whitelist: {process_name or process_path}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to remove from whitelist: {e}")
            return False
    
    def get_all(self) -> Dict:
        """Get all whitelist entries"""
        return {
            'processes': self.whitelist,
            'paths': list(self.whitelist_paths),
            'count': len(self.whitelist) + len(self.whitelist_paths)
        }
    
    def clear_whitelist(self, keep_defaults: bool = True):
        """
        Clear whitelist.
        
        Args:
            keep_defaults: If True, keep default trusted processes
        """
        if keep_defaults:
            self.whitelist = {
                name: {'description': desc, 'auto_detected': True}
                for name, desc in self.DEFAULT_WHITELIST.items()
            }
        else:
            self.whitelist.clear()
        
        self.whitelist_paths.clear()
        self._save_whitelist()
        logger.info("Whitelist cleared")
    
    def get_stats(self) -> Dict:
        """Get whitelist statistics"""
        hit_rate = (self.whitelist_hits / self.checks_performed * 100) \
                   if self.checks_performed > 0 else 0
        
        return {
            'total_entries': len(self.whitelist) + len(self.whitelist_paths),
            'process_entries': len(self.whitelist),
            'path_entries': len(self.whitelist_paths),
            'checks_performed': self.checks_performed,
            'whitelist_hits': self.whitelist_hits,
            'hit_rate': f"{hit_rate:.2f}%"
        }
    
    def auto_detect_and_add(self, process_info: Dict) -> bool:
        """
        Auto-detect and add common legitimate processes.
        
        Args:
            process_info: Dict with 'name', 'exe' keys
        
        Returns:
            True if auto-added
        """
        process_name = process_info.get('name', '').lower()
        process_exe = process_info.get('exe', '').lower()
        
        # Check if it's a known legitimate software
        common_paths = [
            'program files',
            'program files (x86)',
            'microsoft',
            'google',
            'mozilla',
        ]
        
        # If executable is in a trusted location
        if any(path in process_exe for path in common_paths):
            # SECURITY: Never auto-whitelist python, powershell, cmd, or other script engines
            # even if they are in trusted locations!
            dangerous_interpreters = ['python.exe', 'pythonw.exe', 'powershell.exe', 'cmd.exe', 'cscript.exe', 'wscript.exe']
            if any(interpreter in process_name for interpreter in dangerous_interpreters):
                return False
                
            # Check if not already whitelisted
            if not self.is_whitelisted(process_name):
                self.add_to_whitelist(
                    process_name,
                    description=f"Auto-detected: {process_name}",
                    process_path=process_exe,
                    auto_detected=True
                )
                return True
        
        return False


# Global instance
_whitelist_manager = None


def get_whitelist_manager(whitelist_file: str = None) -> WhitelistManager:
    """Get or create global whitelist manager instance"""
    global _whitelist_manager
    
    if _whitelist_manager is None:
        _whitelist_manager = WhitelistManager(whitelist_file=whitelist_file)
    
    return _whitelist_manager
