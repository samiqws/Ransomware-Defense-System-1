import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
import json


class RansomwareLogger:
    """Advanced logging system for ransomware detection events"""
    
    def __init__(self, log_dir='logs', max_size_mb=100, backup_count=5):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Main logger
        self.logger = logging.getLogger('RansomwareDefense')
        self.logger.setLevel(logging.INFO)
        
        # File handler with rotation
        log_file = os.path.join(log_dir, 'ransomware_defense.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Incident logger (JSON format)
        self.incident_log_file = os.path.join(log_dir, 'incidents.jsonl')
        
    def log_incident(self, incident_data: dict):
        """Log incident in JSON format for analysis"""
        try:
            with open(self.incident_log_file, 'a', encoding='utf-8') as f:
                incident_entry = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    **incident_data
                }
                f.write(json.dumps(incident_entry) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to log incident: {e}")
    
    def log_file_event(self, event_type: str, file_path: str, details: dict = None):
        """Log file system event"""
        message = f"File Event: {event_type} - {file_path}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_detection(self, threat_level: str, indicators: list, details: dict):
        """Log ransomware detection"""
        self.logger.warning(
            f"DETECTION: Threat Level={threat_level}, "
            f"Indicators={', '.join(indicators)}, "
            f"Details={details}"
        )
        
        # Also log to incident file
        self.log_incident({
            'type': 'detection',
            'threat_level': threat_level,
            'indicators': indicators,
            'details': details
        })
    
    def log_containment(self, action: str, target: str, success: bool):
        """Log containment action"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.warning(f"CONTAINMENT [{status}]: {action} - {target}")
        
        self.log_incident({
            'type': 'containment',
            'action': action,
            'target': target,
            'success': success
        })
    
    def log_decoy_access(self, decoy_path: str, compromised: bool):
        """Log decoy file access"""
        if compromised:
            self.logger.critical(f"DECOY COMPROMISED: {decoy_path}")
            self.log_incident({
                'type': 'decoy_breach',
                'path': decoy_path,
                'compromised': True
            })
        else:
            self.logger.info(f"Decoy accessed (integrity intact): {decoy_path}")


# Global logger instance
ransomware_logger = RansomwareLogger()
