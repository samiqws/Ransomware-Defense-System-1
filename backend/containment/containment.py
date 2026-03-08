import os
import time
import subprocess
import psutil
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ContainmentEngine:
    """Automated containment and response actions"""
    
    def __init__(self, config: dict):
        self.config = config
        self.containment_config = config.get("containment", {})
        self.auto_contain = self.containment_config.get("auto_contain", False)
        self.containment_log = []
        # Cache to prevent repeated slow searches after a kill
        self._last_kill_time = 0
        self._last_killed_name = ""
    
    async def execute_containment(self, incident_data: dict, auto: bool = False) -> dict:
        """
        Execute containment protocols based on incident severity.
        Returns summary of actions taken.
        """
        if auto and not self.auto_contain:
            logger.info("Auto-containment is disabled")
            return {"status": "skipped", "reason": "auto_contain_disabled"}
        
        actions_taken = []
        actions_failed = []
        
        threat_level = incident_data.get("threat_level", "low")
        process_info = incident_data.get("process", {})
        indicators = incident_data.get("indicators", [])
        
        logger.warning(f"Initiating containment for {threat_level} threat")
        
        # 1. Kill suspicious process to release locks and get exe path
        if self.containment_config.get("kill_process", True):
            # Pass file_path to help find the real process if PID is unknown
            process_info["file_path"] = incident_data.get("file_path", "")
            
            # Kill process first to release file locks and populate process_info["exe"]
            result = await self.kill_process(process_info)
            if result["success"]:
                actions_taken.append(result)
                if result.get("exe") and not process_info.get("exe"):
                    process_info["exe"] = result["exe"]
            else:
                actions_failed.append(result)
                
        # 0. Generate YARA Rule for Zero-Day threats (if Critical or High and not caught by YARA already)
        if threat_level in ["high", "critical"] and "yara_match" not in str(indicators):
            process_exe = process_info.get("exe")
            if process_exe and os.path.exists(process_exe):
                try:
                    from core.yara_generator import get_yara_generator
                    generator = get_yara_generator()
                    logger.info(f"Attempting to generate YARA rule for zero-day threat: {process_exe}")
                    
                    success = generator.generate_rule_from_file(process_exe, process_info.get("name", "Unknown"))
                    if success:
                        logger.warning(f"Successfully generated dynamic YARA rule for zero-day threat: {process_exe}")
                        actions_taken.append({
                            "action": "yara_rule_generation",
                            "success": True,
                            "target": process_exe
                        })
                except Exception as e:
                    logger.error(f"Failed to generate dynamic YARA rule: {e}")
                
        # QUARANTINE: Quarantine the executable
        process_exe = process_info.get("exe") or incident_data.get("file_path", "")
        if process_exe and os.path.exists(process_exe):
            # SECURITY: Do not attempt to quarantine core Windows system files!
            # These will cause 'Access is denied' errors and shouldn't be moved.
            is_system_binary = False
            try:
                lower_exe = process_exe.lower()
                if 'c:\\windows\\' in lower_exe or 'system32' in lower_exe:
                    is_system_binary = True
            except Exception:
                pass
                
            if is_system_binary:
                logger.warning(f"Skipping quarantine for core system binary: {process_exe}")
            else:
                try:
                    from core.quarantiner import get_quarantiner
                    quarantiner = get_quarantiner()
                    q_result = quarantiner.quarantine_file(process_exe, incident_data.get("id", "unknown"))
                    
                    if q_result["success"]:
                        logger.warning(f"Successfully quarantined malicious file: {process_exe}")
                        actions_taken.append({
                            "action": "quarantine_file",
                            "success": True,
                            "target": process_exe,
                            "quarantine_path": q_result.get("quarantine_path")
                        })
                        
                        # Add to Database
                        from database.database import db
                        from database.models import QuarantineItem
                        import asyncio
                        
                        async def save_quarantine():
                            try:
                                async with db.async_session() as session:
                                    q_item = QuarantineItem(
                                        incident_id=incident_data.get("id", "unknown"),
                                        original_path=process_exe,
                                        quarantine_path=q_result.get("quarantine_path"),
                                        file_hash=q_result.get("file_hash"),
                                        process_name=process_info.get("name", "Unknown")
                                    )
                                    session.add(q_item)
                                    await session.commit()
                            except Exception as db_e:
                                logger.error(f"Failed to save quarantine record to DB: {db_e}")
                                
                        asyncio.create_task(save_quarantine())
                    else:
                        logger.error(f"Failed to quarantine {process_exe}: {q_result.get('error')}")
                        actions_failed.append({
                            "action": "quarantine_file",
                            "success": False,
                            "target": process_exe,
                            "error": q_result.get("error")
                        })
                except Exception as e:
                    logger.error(f"Error during quarantine process: {e}")
        
        # 2. Isolate network (for high/critical threats)
        if threat_level in ["high", "critical"] and self.containment_config.get("isolate_network", True):
            result = await self.isolate_network()
            if result["success"]:
                actions_taken.append(result)
            else:
                actions_failed.append(result)
        
        # 3. Disable network drives
        if self.containment_config.get("disable_network_drives", True):
            result = await self.disable_network_drives()
            if result["success"]:
                actions_taken.append(result)
            else:
                actions_failed.append(result)
        
        # 4. Lock system (for high/critical threats if enabled)
        if threat_level in ["high", "critical"] and self.containment_config.get("lock_system", False):
            result = await self.lock_workstation()
            if result["success"]:
                actions_taken.append(result)
            else:
                actions_failed.append(result)
        
        summary = {
            "status": "completed",
            "actions_taken": actions_taken,
            "actions_failed": actions_failed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "auto_triggered": auto
        }
        
        self.containment_log.append(summary)
        return summary
    
    async def kill_process(self, process_info: dict) -> dict:
        """Terminate a suspicious process. If PID is unknown, attempt to find it."""
        pid = process_info.get("pid", 0)
        process_name = process_info.get("name", "unknown")
        file_path = process_info.get("file_path", "")
        
        # If PID is invalid, try to find the real process
        if pid <= 0:
            # Skip search if we already killed a process recently (30s cooldown)
            if time.time() - self._last_kill_time < 30:
                logger.info(f"Skipping process search — already killed {self._last_killed_name} {time.time()-self._last_kill_time:.0f}s ago")
                return {
                    "action": "process_kill",
                    "success": True,
                    "target": self._last_killed_name,
                    "message": f"Already killed {self._last_killed_name} recently"
                }
            
            logger.warning(f"Invalid PID ({pid}) for process {process_name} — searching for real process...")
            found = self._find_suspicious_process(file_path)
            if found:
                pid = found["pid"]
                process_name = found["name"]
                if found.get("exe"):
                    process_info["exe"] = found["exe"]
                logger.warning(f"Found suspicious process: {process_name} (PID: {pid})")
            else:
                logger.warning(f"Could not find suspicious process for {file_path}")
                return {
                    "action": "process_kill",
                    "success": False,
                    "error": "process_not_found",
                    "target": process_name,
                    "message": "Could not identify the malicious process"
                }
        
        try:
            process = psutil.Process(pid)
            
            # Retrieve exe path before termination if possible
            try:
                exe_path = process.exe()
            except Exception:
                exe_path = process_info.get("exe", "")
                
            # Phase 2 EDR: Terminate the Parent Process (Kill the root cause)
            # If Ransomware spawns PowerShell, we MUST kill the Ransomware first, otherwise it just spawns another PowerShell!
            try:
                ppid = process.ppid()
                if ppid > 0:
                    parent_proc = psutil.Process(ppid)
                    p_name = parent_proc.name().lower()
                    trusted_parents = ["explorer.exe", "svchost.exe", "services.exe", "wininit.exe", "taskmgr.exe"]
                    
                    if not any(tp in p_name for tp in trusted_parents):
                        logger.critical(f"PHASE 2 EDR: Neutralizing Parent Process '{p_name}' (PID: {ppid}) before killing child payload '{process_name}'!")
                        parent_proc.terminate()
                        parent_proc.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass # Parent already dead or access denied (System process)
                
            process.terminate()
            process.wait(timeout=5)
            
            # Cache the kill so we don't search again for 30s
            self._last_kill_time = time.time()
            self._last_killed_name = process_name
            
            logger.info(f"Terminated process: {process_name} (PID: {pid})")
            return {
                "action": "process_kill",
                "success": True,
                "target": process_name,
                "pid": pid,
                "exe": exe_path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except psutil.NoSuchProcess:
            return {
                "action": "process_kill",
                "success": False,
                "error": "process_not_found",
                "target": process_name
            }
        except psutil.AccessDenied:
            return {
                "action": "process_kill",
                "success": False,
                "error": "access_denied",
                "target": process_name,
                "message": "Requires administrator privileges"
            }
        except Exception as e:
            logger.error(f"Failed to kill process {process_name}: {e}")
            return {
                "action": "process_kill",
                "success": False,
                "error": str(e),
                "target": process_name
            }
    
    def _find_suspicious_process(self, file_path: str) -> Optional[dict]:
        """
        Find the real suspicious process when PID is unknown.
        FAST: Only uses process name/path filtering + creation time.
        Does NOT use open_files() which causes 40s freezes on Windows.
        """
        if not file_path:
            return None
        
        import getpass
        try:
            current_user = getpass.getuser().lower()
        except:
            return None
        
        # Known safe process names (lowercase)
        safe_names = frozenset({
            'explorer.exe', 'svchost.exe', 'system', 'csrss.exe',
            'python.exe', 'pythonw.exe', 'python3.exe',  # RESTORED: User requested python immunity
            'lsass.exe', 'winlogon.exe', 'dwm.exe', 'smss.exe',
            'taskhostw.exe', 'conhost.exe', 'cmd.exe', 'powershell.exe',
            'devenv.exe', 'searchindexer.exe',
            'runtimebroker.exe', 'sihost.exe', 'fontdrvhost.exe',
            'ctfmon.exe', 'dllhost.exe', 'wininit.exe', 'services.exe',
            'spoolsv.exe', 'audiodg.exe', 'registry',
            'msedge.exe', 'chrome.exe', 'firefox.exe', 'taskmgr.exe',
            'shellexperiencehost.exe', 'startmenuexperiencehost.exe',
            'securityhealthservice.exe', 'securityhealthsystray.exe',
            'textinputhost.exe', 'windowsterminal.exe', 'wt.exe',
            'msedgewebview2.exe', 'gamebar.exe', 'gamebarftserver.exe',
            'searchprotocolhost.exe', 'searchfilterhost.exe',
            'applicationframehost.exe', 'systemsettings.exe',
            'lockapp.exe', 'smartscreen.exe', 'mpcmdrun.exe',
            'wmiprvse.exe', 'wudfhost.exe', 'dashost.exe',
            'unsecapp.exe', 'msiexec.exe', 'tiworker.exe',
            'musnotification.exe', 'backgroundtaskhost.exe',
            'securityhealthhost.exe', 'phoneexperiencehost.exe',
            'widgets.exe', 'widgetservice.exe', 'ccastorage.exe',
            'video.ui.exe', 'yourphone.exe', 'gamingservices.exe',
            'antiquity.exe', 'antigravity.exe',
        })
        
        # Safe directory prefixes
        safe_dirs = (
            'c:\\windows\\',
            'c:\\program files\\',
            'c:\\program files (x86)\\',
        )
        
        suspicious_candidates = []
        
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'username', 'create_time']):
            try:
                pname = (proc.info.get('name') or '').lower()
                uname = (proc.info.get('username') or '').lower()
                exe_path = (proc.info.get('exe') or '').lower()
                
                if current_user not in uname:
                    continue
                if proc.info['pid'] == os.getpid() or proc.info['pid'] == os.getppid():
                    continue  # SUPER CRITICAL: Never target ourselves or our parent console!
                if pname in safe_names:
                    continue
                if any(exe_path.startswith(sd) for sd in safe_dirs):
                    continue
                
                create_time = proc.info.get('create_time', 0)
                suspicious_candidates.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'exe': proc.info.get('exe') or 'Unknown',
                    'create_time': create_time
                })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Pick the most recently started suspicious process (within 120s)
        if suspicious_candidates:
            suspicious_candidates.sort(key=lambda x: x['create_time'], reverse=True)
            best = suspicious_candidates[0]
            if time.time() - best['create_time'] < 120:
                logger.info(f"CONTAINMENT: Targeting newest suspicious process: {best['name']} (PID: {best['pid']}, age: {time.time()-best['create_time']:.0f}s)")
                return best
        
        return None
    
    async def isolate_network(self) -> dict:
        """Disable network adapters to isolate the system"""
        try:
            # Windows command to disable network adapters
            cmd = 'powershell "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Disable-NetAdapter -Confirm:$false"'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.warning("Network adapters disabled - System isolated")
                return {
                    "action": "network_isolation",
                    "success": True,
                    "message": "All network adapters disabled",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "action": "network_isolation",
                    "success": False,
                    "error": result.stderr,
                    "message": "Requires administrator privileges"
                }
        except Exception as e:
            logger.error(f"Network isolation failed: {e}")
            return {
                "action": "network_isolation",
                "success": False,
                "error": str(e)
            }
    
    async def disable_network_drives(self) -> dict:
        """Disconnect all network drives"""
        try:
            # Windows command to disconnect network drives
            cmd = 'net use * /delete /yes'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            logger.info("Network drives disconnected")
            return {
                "action": "disable_network_drives",
                "success": True,
                "message": "All network drives disconnected",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to disconnect network drives: {e}")
            return {
                "action": "disable_network_drives",
                "success": False,
                "error": str(e)
            }
    
    async def lock_workstation(self) -> dict:
        """Lock the workstation"""
        try:
            # Method 1: Try ctypes (more reliable)
            try:
                import ctypes
                result = ctypes.windll.user32.LockWorkStation()
                if result != 0:
                    logger.warning("Workstation locked via ctypes")
                    return {
                        "action": "lock_workstation",
                        "success": True,
                        "message": "Workstation locked",
                        "method": "ctypes",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
            except Exception as e:
                logger.warning(f"ctypes lock failed, trying subprocess: {e}")
            
            # Method 2: Fallback to subprocess
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], timeout=5)
            
            logger.warning("Workstation locked via subprocess")
            return {
                "action": "lock_workstation",
                "success": True,
                "message": "Workstation locked",
                "method": "subprocess",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to lock workstation: {e}")
            return {
                "action": "lock_workstation",
                "success": False,
                "error": str(e),
                "message": "Lock failed - both methods unsuccessful"
            }
    
    async def restore_network(self) -> dict:
        """Re-enable network adapters"""
        try:
            cmd = 'powershell "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("Network adapters re-enabled")
                return {
                    "action": "restore_network",
                    "success": True,
                    "message": "Network adapters restored"
                }
            else:
                return {
                    "action": "restore_network",
                    "success": False,
                    "error": result.stderr
                }
        except Exception as e:
            return {
                "action": "restore_network",
                "success": False,
                "error": str(e)
            }
    
    def get_containment_history(self) -> List[dict]:
        """Get history of containment actions"""
        return self.containment_log
