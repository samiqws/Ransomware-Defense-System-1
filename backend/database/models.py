from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, Index
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass

class FileEvent(Base):
    """Records all file system events"""
    __tablename__ = "file_events"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    event_type = Column(String(50))  # modified, created, deleted, moved
    file_path = Column(String(500), index=True)
    file_hash = Column(String(64))
    file_size = Column(Integer)
    entropy = Column(Float)
    is_decoy = Column(Boolean, default=False)
    process_name = Column(String(255))
    process_id = Column(Integer)
    suspicious = Column(Boolean, default=False, index=True)
    threat_level = Column(String(20))  # low, medium, high, critical
    
    # Composite indexes for faster queries
    __table_args__ = (
        Index('idx_file_events_timestamp_suspicious', 'timestamp', 'suspicious'),
        Index('idx_file_events_process', 'process_name', 'process_id'),
        Index('idx_file_events_threat_level', 'threat_level'),
    )
    

class DecoyFile(Base):
    """Tracks deployed decoy/honeypot files"""
    __tablename__ = "decoy_files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(500), unique=True, index=True)
    file_hash = Column(String(64))
    file_type = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_verified = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_compromised = Column(Boolean, default=False)
    access_count = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        Index('idx_decoy_is_compromised', 'is_compromised'),
    )


class Incident(Base):
    """Ransomware incident records"""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(36), unique=True, index=True)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20))  # active, contained, resolved, false_positive
    severity = Column(String(20))  # low, medium, high, critical
    affected_files_count = Column(Integer, default=0)
    process_name = Column(String(255))
    process_id = Column(Integer)
    attack_vector = Column(Text)
    containment_actions = Column(JSON)
    detection_methods = Column(JSON)
    entropy_score = Column(Float)
    confidence_score = Column(Float)
    notes = Column(Text)
    
    # Composite indexes for faster incident queries
    __table_args__ = (
        Index('idx_incidents_status_severity', 'status', 'severity'),
        Index('idx_incidents_process', 'process_name', 'process_id'),
        Index('idx_incidents_time_range', 'start_time', 'end_time'),
    )


class ContainmentAction(Base):
    """Log of all containment actions taken"""
    __tablename__ = "containment_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(36), index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    action_type = Column(String(50))  # network_isolate, process_kill, drive_disable, etc.
    target = Column(String(255))
    success = Column(Boolean)
    error_message = Column(Text, nullable=True)
    auto_triggered = Column(Boolean, default=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_containment_timestamp', 'timestamp'),
        Index('idx_containment_success', 'success'),
    )


class SystemHealth(Base):
    """System health and performance metrics"""
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    monitored_files_count = Column(Integer)
    active_incidents = Column(Integer)
    events_per_minute = Column(Integer)
    detection_engine_status = Column(String(20))


class Alert(Base):
    """Security alerts and notifications"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    alert_type = Column(String(50))  # ransomware_detected, decoy_accessed, rapid_encryption, etc.
    severity = Column(String(20))
    message = Column(Text)
    details = Column(JSON)
    incident_id = Column(String(36), nullable=True, index=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Composite indexes for alert management
    __table_args__ = (
        Index('idx_alerts_severity_ack', 'severity', 'acknowledged'),
        Index('idx_alerts_type_time', 'alert_type', 'timestamp'),
    )


class QuarantineItem(Base):
    """Quarantined malicious files awaiting user review"""
    __tablename__ = "quarantine_items"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(36), index=True)
    original_path = Column(String(500))
    quarantine_path = Column(String(500), unique=True)
    file_hash = Column(String(64))
    process_name = Column(String(255))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status = Column(String(20), default="quarantined")  # quarantined, restored, deleted
    
    # Indexes
    __table_args__ = (
        Index('idx_quarantine_status', 'status'),
    )
