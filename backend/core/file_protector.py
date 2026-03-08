"""
File Protection System - نظام حماية الملفات
يقوم بإنشاء نسخ احتياطية تلقائية للملفات المهمة
"""

import os
import shutil
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FileProtector:
    """نظام حماية الملفات بالنسخ الاحتياطي التلقائي"""
    
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", True)
        self.backup_dir = config.get("backup_dir", "data/file_backups")
        self.max_versions = config.get("max_versions", 5)
        self.protected_extensions = config.get("protected_extensions", [
            ".docx", ".xlsx", ".pdf", ".txt", ".jpg", ".png"
        ])
        self.backup_registry: Dict[str, List[dict]] = {}
        
        # إنشاء مجلد النسخ الاحتياطي
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # تحميل السجل
        self._load_registry()
    
    def should_protect_file(self, file_path: str) -> bool:
        """تحديد ما إذا كان يجب حماية الملف"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.protected_extensions
    
    def create_backup(self, file_path: str) -> Optional[dict]:
        """إنشاء نسخة احتياطية من الملف"""
        try:
            if not self.enabled:
                return None
                
            # Don't backup files in the backup directory itself!
            if "file_backups" in file_path or "\\data\\backup" in file_path.lower():
                return None
            
            if not os.path.exists(file_path):
                return None
            
            if not self.should_protect_file(file_path):
                return None
            
            # حساب hash الملف
            file_hash = self._calculate_hash(file_path)
            
            # إنشاء اسم فريد للنسخة الاحتياطية
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            backup_name = f"{timestamp}_{file_hash[:8]}_{filename}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # نسخ الملف
            shutil.copy2(file_path, backup_path)
            
            backup_info = {
                "original_path": file_path,
                "backup_path": backup_path,
                "timestamp": timestamp,
                "file_hash": file_hash,
                "file_size": os.path.getsize(file_path)
            }
            
            # تحديث السجل
            if file_path not in self.backup_registry:
                self.backup_registry[file_path] = []
            
            self.backup_registry[file_path].append(backup_info)
            
            # الاحتفاظ بعدد محدود من النسخ
            self._cleanup_old_backups(file_path)
            
            # حفظ السجل
            self._save_registry()
            
            logger.info(f"Backup created: {file_path} -> {backup_name}")
            return backup_info
            
        except Exception as e:
            logger.error(f"Backup failed for {file_path}: {e}")
            return None
    
    def restore_file(self, file_path: str, version_index: int = -1) -> bool:
        """استرجاع ملف من النسخة الاحتياطية"""
        try:
            if file_path not in self.backup_registry:
                logger.warning(f"No backups found for {file_path}")
                return False
            
            backups = self.backup_registry[file_path]
            if not backups:
                return False
            
            backup_info = backups[version_index]
            backup_path = backup_info["backup_path"]
            
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # استرجاع الملف
            shutil.copy2(backup_path, file_path)
            
            logger.info(f"File restored: {file_path} from {backup_info['timestamp']}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed for {file_path}: {e}")
            return False
    
    def get_backup_info(self, file_path: str) -> List[dict]:
        """الحصول على معلومات النسخ الاحتياطية لملف"""
        return self.backup_registry.get(file_path, [])
    
    def restore_all_files(self) -> Dict[str, bool]:
        """استرجاع جميع الملفات التي لها نسخ احتياطية"""
        results = {}
        for file_path in self.backup_registry.keys():
            success = self.restore_file(file_path)
            results[file_path] = success
        return results
    
    def get_statistics(self) -> dict:
        """الحصول على إحصائيات النسخ الاحتياطية"""
        total_files = len(self.backup_registry)
        total_backups = sum(len(backups) for backups in self.backup_registry.values())
        total_size = 0
        
        for backups in self.backup_registry.values():
            for backup in backups:
                if os.path.exists(backup['backup_path']):
                    total_size += os.path.getsize(backup['backup_path'])
        
        return {
            "protected_files": total_files,
            "total_backups": total_backups,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    def _calculate_hash(self, file_path: str) -> str:
        """حساب SHA-256 hash للملف"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _cleanup_old_backups(self, file_path: str):
        """حذف النسخ القديمة الزائدة"""
        if file_path not in self.backup_registry:
            return
        
        backups = self.backup_registry[file_path]
        
        if len(backups) > self.max_versions:
            old_backups = backups[:-self.max_versions]
            
            for backup in old_backups:
                try:
                    if os.path.exists(backup["backup_path"]):
                        os.remove(backup["backup_path"])
                except Exception as e:
                    logger.error(f"Failed to remove old backup: {e}")
            
            self.backup_registry[file_path] = backups[-self.max_versions:]
    
    def _load_registry(self):
        """تحميل سجل النسخ الاحتياطية"""
        registry_file = os.path.join(self.backup_dir, "backup_registry.json")
        
        if os.path.exists(registry_file):
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    self.backup_registry = json.load(f)
                logger.info(f"Backup registry loaded: {len(self.backup_registry)} files")
            except Exception as e:
                logger.error(f"Failed to load backup registry: {e}")
    
    def _save_registry(self):
        """حفظ سجل النسخ الاحتياطية"""
        registry_file = os.path.join(self.backup_dir, "backup_registry.json")
        
        try:
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save backup registry: {e}")
