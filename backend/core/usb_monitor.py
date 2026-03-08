"""
USB Drive Monitor - مراقب الأقراص الخارجية
يراقب الأقراص USB والخارجية لحمايتها من الفدية
"""

import os
import string
import logging
from typing import List
import psutil

logger = logging.getLogger(__name__)


class USBDriveMonitor:
    """مراقبة الأقراص الخارجية USB وحمايتها"""
    
    def __init__(self):
        self.monitored_drives: List[str] = []
        self.drive_info: dict = {}
    
    def get_all_drives(self) -> List[str]:
        """الحصول على جميع الأقراص المتصلة"""
        drives = []
        
        # Windows: فحص جميع الحروف A-Z
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        
        return drives
    
    def get_removable_drives(self) -> List[str]:
        """الحصول على الأقراص القابلة للإزالة فقط (USB)"""
        removable_drives = []
        
        try:
            partitions = psutil.disk_partitions(all=True)
            for partition in partitions:
                # التحقق من نوع القرص
                if 'removable' in partition.opts.lower():
                    removable_drives.append(partition.mountpoint)
                    logger.info(f"USB drive detected: {partition.mountpoint}")
        except Exception as e:
            # Downgraded to debug as this is expected on systems with Arabic drive labels
            logger.debug(f"Failed to detect removable drives with psutil: {e}")
            logger.info("Falling back to ctypes for removable drive detection")
            # Fallback for Windows if psutil fails due to encoding errors (e.g. Arabic volume labels)
            try:
                import ctypes
                for letter in string.ascii_uppercase:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        # 2 is DRIVE_REMOVABLE in Windows API
                        if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2:
                            removable_drives.append(drive)
                            logger.info(f"USB drive detected (fallback): {drive}")
            except Exception as fallback_e:
                logger.error(f"Fallback detection also failed: {fallback_e}")
        
        return removable_drives
    
    def get_network_drives(self) -> List[str]:
        """الحصول على الأقراص الشبكية"""
        network_drives = []
        
        try:
            partitions = psutil.disk_partitions(all=True)
            for partition in partitions:
                if partition.fstype == 'nfs' or 'remote' in partition.opts.lower():
                    network_drives.append(partition.mountpoint)
        except Exception as e:
            # Downgraded to debug as this is expected on systems with Arabic drive labels
            logger.debug(f"Failed to detect network drives with psutil: {e}")
            logger.info("Falling back to ctypes for network drive detection")
            # Fallback for Windows if psutil fails due to encoding errors
            try:
                import ctypes
                for letter in string.ascii_uppercase:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        # 4 is DRIVE_REMOTE in Windows API
                        if ctypes.windll.kernel32.GetDriveTypeW(drive) == 4:
                            network_drives.append(drive)
                            logger.info(f"Network drive detected (fallback): {drive}")
            except Exception as fallback_e:
                logger.error(f"Fallback detection also failed: {fallback_e}")
        
        return network_drives
    
    def should_monitor_drive(self, drive_path: str) -> bool:
        """تحديد ما إذا كان يجب مراقبة القرص"""
        # استثناء أقراص النظام
        system_drives = ['C:\\']
        
        if drive_path in system_drives:
            return False
        
        # مراقبة جميع الأقراص الأخرى
        return True
    
    def get_drives_to_monitor(self) -> List[str]:
        """الحصول على قائمة الأقراص التي يجب مراقبتها"""
        all_drives = self.get_all_drives()
        removable = self.get_removable_drives()
        
        drives_to_monitor = []
        
        for drive in all_drives:
            if self.should_monitor_drive(drive):
                drives_to_monitor.append(drive)
                
                drive_type = "USB" if drive in removable else "Fixed"
                self.drive_info[drive] = {
                    "type": drive_type,
                    "path": drive
                }
        
        return drives_to_monitor
    
    def get_drive_statistics(self) -> dict:
        """إحصائيات الأقراص"""
        all_drives = self.get_all_drives()
        removable = self.get_removable_drives()
        
        return {
            "total_drives": len(all_drives),
            "removable_drives": len(removable),
            "monitored_drives": len(self.monitored_drives),
            "drives": [
                {
                    "path": drive,
                    "type": self.drive_info.get(drive, {}).get("type", "Unknown")
                }
                for drive in all_drives
            ]
        }
