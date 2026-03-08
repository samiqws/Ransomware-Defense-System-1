import logging
import os
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class RansomwareDetector:
    """Advanced ransomware detection engine with multiple heuristics"""
    
    def __init__(self, config: dict, decoy_manager):
        self.config = config
        self.decoy_manager = decoy_manager
        
        # Detection thresholds
        self.entropy_threshold = config.get("detection", {}).get("entropy_threshold", 7.0)
        self.rapid_change_threshold = config.get("detection", {}).get("rapid_change_threshold", 50)
        self.extension_change_threshold = config.get("detection", {}).get("extension_change_threshold", 10)
        
        # Tracking structures
        self.file_modifications = defaultdict(list)
        self.process_activity = defaultdict(int)
        self.extension_changes = defaultdict(int)
        self.suspicious_processes = set()
        
        # Detection window (5 minutes)
        self.detection_window = timedelta(minutes=5)
    
    async def analyze_event(self, event_data: dict) -> dict:
        """
        Analyze a file system event for ransomware indicators.
        Returns detection result with threat assessment.
        """
        try:
            file_path = event_data.get("path")
            event_type = event_data.get("type")
            timestamp = event_data.get("timestamp", datetime.now(timezone.utc))
            process_info = event_data.get("process", {})
            integrity_info = event_data.get("integrity", {})
            
            detection_result = {
                "suspicious": False,
                "threat_level": "none",
                "confidence": 0.0,
                "indicators": [],
                "recommended_action": "monitor"
            }
            
            indicators = []
            threat_score = 0
            
            # 1. Check if decoy file was accessed
            decoy_check = self.decoy_manager.verify_decoy(file_path)
            if decoy_check.get("is_decoy") and decoy_check.get("compromised"):
                indicators.append("decoy_file_compromised")
                threat_score += 50
                logger.warning(f"DECOY FILE COMPROMISED: {file_path}")
                
            # 1.5. Check YARA malware scan results
            yara_check = event_data.get("yara", {})
            if yara_check.get("matches"):
                matched_rules = yara_check.get("rules", [])
                indicators.append(f"yara_match:{','.join(matched_rules)}")
                threat_score += 80  # YARA signatures are highly confident
                logger.critical(f"YARA MALWARE SIGNATURE DETECTED: {file_path} [{matched_rules}]")
            
            # Skip checking heuristics for known benign OS system processes ONLY
            # SECURITY: Never trust unknown processes or path-based checks
            benign_system_processes = ["system", "svchost.exe", "explorer.exe"]
            process_name_lower = process_info.get("name", "unknown").lower()
            
            is_benign = False
            if process_name_lower in benign_system_processes:
                is_benign = True

            # 2. Check Magic Bytes (Instant Encryption Indicator)
            if integrity_info and not is_benign:
                if integrity_info.get("magic_bytes_valid") is False:
                    indicators.append("corrupted_magic_bytes")
                    threat_score += 60
                    logger.critical(f"Magic bytes completely corrupted for {file_path}! High probability of encryption.")

            # 3. Check entropy (encryption indicator)
            if integrity_info and not is_benign:
                current_entropy = integrity_info.get("current_entropy", 0)
                # Ignore entropy for naturally compressed files (images, archives, video)
                compressed_exts = ['.png', '.jpg', '.jpeg', '.zip', '.rar', '.7z', '.mp4', '.mkv', '.mp3']
                ext = process_info.get("file_path", file_path).lower()
                is_compressed = any(ext.endswith(ce) for ce in compressed_exts)
                
                if current_entropy and current_entropy > self.entropy_threshold and not is_compressed:
                    indicators.append("high_entropy")
                    threat_score += 30
            
            # 3. Check for extension changes
            if integrity_info and integrity_info.get("extension_changed") and not is_benign:
                indicators.append("extension_changed")
                threat_score += 20
                process_name = process_info.get("name", "unknown")
                self.extension_changes[process_name] += 1
            
            # 4. Track rapid file modifications
            process_name = process_info.get("name", "unknown")
            
            # Skip tracking for benign system processes and our own processes
            if is_benign:
                return detection_result
            
            # Clean old entries and handle inactivity
            cutoff_time = timestamp - self.detection_window
            
            # If the process hasn't done anything in the last 60 seconds, reset its history
            # to prevent old attacks (like a previous ransomware test) from haunting new benign actions
            if self.file_modifications[process_name]:
                last_activity = self.file_modifications[process_name][-1]
                if (timestamp - last_activity).total_seconds() > 60:
                    self.file_modifications[process_name] = []
                    self.extension_changes[process_name] = 0
            
            self.file_modifications[process_name].append(timestamp)
            
            self.file_modifications[process_name] = [
                t for t in self.file_modifications[process_name] if t > cutoff_time
            ]
            
            modification_rate = len(self.file_modifications[process_name])
            
            # Check if this is an archive extraction/compression process
            # (which naturally creates/modifies files very rapidly)
            archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz']
            is_archive_operation = any(file_path.lower().endswith(ext) for ext in archive_exts)
            
            if modification_rate > self.rapid_change_threshold:
                if "rapid_file_modifications" not in indicators:
                    indicators.append("rapid_file_modifications")
                    if not is_archive_operation:
                        threat_score += 20  # Reduced from 60 to 20 to act as a synergy score, eliminating False Positives
                    else:
                        logger.debug(f"Archive operation detected ({file_path}), exempting from 20 point rapid modification penalty.")
                logger.warning(f"Rapid modifications detected: {process_name} - {modification_rate} files")
            
            # Phase 2 EDR: Process Tree Anomaly Detection (Living-off-the-Land)
            # Catch ransomware simulating via trusted tools like powershell, cmd, wscript, cscript
            lol_bins = ["powershell.exe", "cmd.exe", "wscript.exe", "cscript.exe"]
            process_exe_lower = process_info.get("exe", "unknown").lower()
            parent_name = str(process_info.get("parent_name", "")).lower()
            
            # If the process modifying files is a known LOLBin (like powershell)
            if any(lol_bin in process_exe_lower for lol_bin in lol_bins):
                # And its parent is NOT a trusted Windows utility (explorer.exe etc.)
                trusted_parents = ["explorer.exe", "svchost.exe", "services.exe", "wininit.exe"]
                if parent_name and not any(tp in parent_name for tp in trusted_parents):
                    indicators.append(f"malicious_parent_child: {parent_name} -> {process_name}")
                    threat_score += 75  # Massive penalty for Process Tree Injection/Abuse
                    logger.critical(f"PROCESS TREE ANOMALY DETECTED: {parent_name} spawned {process_name} to modify files! (Living-off-the-Land attack)")
            
            # 5. Check for mass extension changes
            if self.extension_changes[process_name] > self.extension_change_threshold:
                indicators.append("mass_extension_changes")
                threat_score += 35
            
            # 6. Check for suspicious file patterns
            if any(ext in file_path.lower() for ext in self.config.get("detection", {}).get("suspicious_extensions", [])):
                indicators.append("suspicious_extension")
                threat_score += 25
            
            # Determine threat level
            if threat_score >= 70:
                detection_result["threat_level"] = "critical"
                detection_result["recommended_action"] = "contain"
                logger.critical(f"[CRITICAL THREAT] Score: {threat_score} | File: {file_path} | Process: {process_name} | Indicators: {indicators}")
            elif threat_score >= 50:
                detection_result["threat_level"] = "high"
                detection_result["recommended_action"] = "contain"
                logger.error(f"[HIGH THREAT] Score: {threat_score} | File: {file_path} | Process: {process_name} | Indicators: {indicators}")
            elif threat_score >= 30:
                detection_result["threat_level"] = "medium"
                detection_result["recommended_action"] = "monitor"
                logger.warning(f"[MEDIUM THREAT] Score: {threat_score} | File: {file_path} | Process: {process_name} | Indicators: {indicators}")
            elif threat_score >= 15:
                detection_result["threat_level"] = "low"
                detection_result["recommended_action"] = "log"
                logger.info(f"[LOW THREAT] Score: {threat_score} | File: {file_path}")
            
            detection_result["suspicious"] = threat_score >= 30
            detection_result["confidence"] = min(threat_score / 100.0, 1.0)
            detection_result["indicators"] = indicators
            detection_result["threat_score"] = threat_score
            detection_result["process"] = process_info
            
            # Log all detections for debugging
            if threat_score > 0:
                logger.info(f"Detection analysis - File: {os.path.basename(file_path)} | Score: {threat_score} | Indicators: {indicators}")
            
            return detection_result
        
        except Exception as e:
            logger.error(f"Error analyzing event: {e}")
            # Return safe default result
            return {
                "suspicious": False,
                "threat_level": "none",
                "confidence": 0.0,
                "indicators": [],
                "recommended_action": "monitor"
            }
    
    def get_suspicious_processes(self) -> List[dict]:
        """Get list of processes with suspicious activity"""
        suspicious = []
        
        for process_name, count in self.extension_changes.items():
            if count > self.extension_change_threshold:
                suspicious.append({
                    "process": process_name,
                    "extension_changes": count,
                    "file_modifications": len(self.file_modifications.get(process_name, []))
                })
        
        return suspicious
    
    def reset_tracking(self):
        """Reset all tracking data"""
        self.file_modifications.clear()
        self.process_activity.clear()
        self.extension_changes.clear()
        self.suspicious_processes.clear()
        logger.info("Detection tracking data reset")
