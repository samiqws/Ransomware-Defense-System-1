import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.file_monitor import FileSystemMonitor
from core.decoy_manager import DecoyFileManager
from core.file_protector import FileProtector
from core.usb_monitor import USBDriveMonitor
from core.monitoring_config import MonitoringConfig
from detection.detector import RansomwareDetector
from containment.containment import ContainmentEngine
from database.database import db
from database.batch_writer import get_batch_writer
from database.models import (
    FileEvent, DecoyFile, Incident, ContainmentAction,
    SystemHealth, Alert
)

# Create necessary directories first
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ransomware_defense.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Configure console handler to handle unicode properly
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.INFO)
        # Use a formatter that avoids unicode issues
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
logger = logging.getLogger(__name__)

# Load configuration
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Global state
active_incidents: Dict[str, dict] = {}
connected_clients: Set[WebSocket] = set()
system_running: bool = True  # System monitoring state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Ransomware Detection Engine...")
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Initialize database
    await db.init_db()
    
    # Initialize BatchWriter with the running event loop for async-safe batch inserts
    loop = asyncio.get_event_loop()
    app.state.batch_writer = get_batch_writer(
        database=db,
        batch_size=50,
        flush_interval=5.0,
        event_loop=loop
    )
    logger.info("BatchWriter initialized for high-performance batch database writes")
    
    # Initialize monitoring configuration
    app.state.monitoring_config = MonitoringConfig(config_path=config_path)
    logger.info(f"Monitoring configuration loaded: {app.state.monitoring_config.get_all_modes()}")
    
    # Initialize components
    app.state.decoy_manager = DecoyFileManager(config.get("decoys", {}))
    app.state.detector = RansomwareDetector(config, app.state.decoy_manager)
    app.state.containment = ContainmentEngine(config)
    
    # Initialize file protection system
    protection_config = config.get("protection", {
        "backup_dir": "data/file_backups",
        "max_versions": 5,
        "protected_extensions": [".docx", ".xlsx", ".pdf", ".txt", ".jpg", ".png"]
    })
    app.state.file_protector = FileProtector(protection_config)
    logger.info("File protection system initialized")
    
    # Create decoy files (only if decoy monitoring is enabled)
    if app.state.monitoring_config.is_decoy_files_enabled():
        if config.get("monitoring", {}).get("enable_decoys", True):
            decoy_count = config.get("monitoring", {}).get("decoy_count", 50)
            decoys = app.state.decoy_manager.create_decoy_files(decoy_count)
            logger.info(f"Deployed {len(decoys)} decoy files")
    else:
        logger.info("Decoy file monitoring is disabled")
    
    # Auto-detect user folders for comprehensive protection
    import getpass
    username = getpass.getuser()
    user_folders = [
        f"C:\\Users\\{username}\\Documents",
        f"C:\\Users\\{username}\\Desktop",
        f"C:\\Users\\{username}\\Pictures",
        f"C:\\Users\\{username}\\Downloads",
        f"C:\\Users\\{username}\\Videos"
    ]
    
    # Create protected directories if they don't exist
    protected_paths = config.get("monitoring", {}).get("protected_paths", [])
    
    # Add user folders to protected paths (excluding project directory)
    project_dir = os.path.dirname(os.path.dirname(__file__))
    for folder in user_folders:
        if os.path.exists(folder) and folder not in protected_paths:
            # Don't monitor the project's own directory
            if not folder.startswith(project_dir):
                protected_paths.append(folder)
                logger.info(f"Auto-added user folder: {folder}")
    
    # Initialize USB monitor and add removable drives
    usb_monitor = USBDriveMonitor()
    app.state.usb_monitor = usb_monitor
    
    # Add USB drives to monitoring
    usb_drives = usb_monitor.get_drives_to_monitor()
    for drive in usb_drives:
        if drive not in protected_paths:
            protected_paths.append(drive)
            logger.info(f"Auto-added USB/External drive: {drive}")
    
    # Auto-detect VM shared folders and other user folders
    vm_paths = []
    
    # Check for VirtualBox shared folders (usually mounted as network drives)
    try:
        for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                # Check if it's a network/VM shared drive
                try:
                    import subprocess
                    result = subprocess.run(
                        ['wmic', 'logicaldisk', 'where', f'DeviceID="{letter}:"', 'get', 'DriveType'],
                        capture_output=True, text=True, timeout=2
                    )
                    if '4' in result.stdout:  # Network drive
                        vm_paths.append(drive)
                        logger.info(f"Detected VM/Network drive: {drive}")
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"VM drive detection skipped: {e}")
    
    # Check for other users' folders (for VM testing scenarios)
    try:
        users_dir = "C:\\Users"
        if os.path.exists(users_dir):
            for user_folder in os.listdir(users_dir):
                user_path = os.path.join(users_dir, user_folder)
                if os.path.isdir(user_path) and user_folder not in ["Public", "Default", "All Users", username]:
                    # Add Desktop and Documents for other users (VM scenario)
                    for subfolder in ["Desktop", "Documents", "Pictures", "Downloads"]:
                        other_user_path = os.path.join(user_path, subfolder)
                        if os.path.exists(other_user_path) and other_user_path not in vm_paths:
                            vm_paths.append(other_user_path)
                            logger.info(f"Auto-added VM/Other user folder: {other_user_path}")
    except Exception as e:
        logger.debug(f"Other users folder detection skipped: {e}")
    
    # Add detected VM paths
    for vm_path in vm_paths:
        if vm_path not in protected_paths:
            protected_paths.append(vm_path)
    for path in protected_paths:
        try:
            os.makedirs(path, exist_ok=True)
            logger.info(f"Protected path ready: {path}")
        except Exception as e:
            logger.warning(f"Could not create path {path}: {e}")
    
    # Start file monitoring
    loop = asyncio.get_event_loop()
    
    def file_event_callback(event):
        """Callback that schedules async task from sync context"""
        future = asyncio.run_coroutine_threadsafe(handle_file_event(event), loop)
        # Log errors from the future so events are never silently lost
        def _on_done(f):
            exc = f.exception()
            if exc:
                logger.error(f"Async file event handler failed: {exc}")
        future.add_done_callback(_on_done)
    
    app.state.monitor = FileSystemMonitor(
        protected_paths,
        file_event_callback,
        loop=loop,
        file_protector=app.state.file_protector,
        monitoring_config=app.state.monitoring_config
    )
    app.state.monitor.start()
    
    # Initialize monitored files cache
    app.state.monitored_files_cache = 0
    app.state.cache_update_task = None
    
    # Start background task to update file count cache
    async def update_monitored_files_cache():
        """Background task to count monitored files periodically"""
        while True:
            try:
                await asyncio.sleep(60)  # Update every 60 seconds
                
                count = 0
                monitoring_modes = app.state.monitoring_config.get_all_modes()
                protected_extensions = {'.docx', '.xlsx', '.pdf', '.txt', '.jpg', '.png', '.pptx', '.zip', '.rar', '.doc', '.xls'}
                
                for path in app.state.monitor.protected_paths[:5]:  # Limit to first 5 paths for speed
                    if os.path.exists(path) and os.path.isdir(path):
                        depth = 0
                        for root, dirs, files in os.walk(path):
                            # Limit depth to 3 levels
                            depth = root.replace(path, '').count(os.sep)
                            if depth > 3:
                                dirs[:] = []  # Don't go deeper
                                continue
                            
                            # Skip unnecessary directories
                            dirs[:] = [d for d in dirs if d not in ['file_backups', 'logs', '__pycache__', '.git', 'node_modules']]
                            
                            # Quick count without detailed checks
                            count += sum(1 for f in files if os.path.splitext(f)[1].lower() in protected_extensions)
                            
                            # Stop if taking too long
                            if count > 10000:
                                break
                
                app.state.monitored_files_cache = count
                logger.debug(f"Updated monitored files cache: {count}")
                
            except Exception as e:
                logger.error(f"Error updating file count cache: {e}")
    
    # Start the cache update task
    app.state.cache_update_task = asyncio.create_task(update_monitored_files_cache())
    
    logger.info("Ransomware Detection Engine is running and ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    app.state.monitor.stop()
    
    # Flush remaining batch data before exit
    if hasattr(app.state, 'batch_writer') and app.state.batch_writer:
        app.state.batch_writer.shutdown()
    
    await db.close()


app = FastAPI(
    title="Ransomware Detection & Containment Engine",
    description="Professional ransomware honeynet system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("api", {}).get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def handle_file_event(event_data: dict):
    """Process file system events"""
    try:
        # Run detection analysis
        detection_result = await app.state.detector.analyze_event(event_data)
        
        # Ensure detection_result is not None
        if detection_result is None:
            logger.error("Detection result is None, using default values")
            detection_result = {
                "suspicious": False,
                "threat_level": "none",
                "confidence": 0.0,
                "indicators": [],
                "recommended_action": "monitor"
            }
        
        # Store event in database with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with db.async_session() as session:
                    file_event = FileEvent(
                        event_type=event_data.get("type"),
                        file_path=event_data.get("path"),
                        file_hash=event_data.get("integrity", {}).get("current_hash") if event_data.get("integrity") else None,
                        entropy=event_data.get("integrity", {}).get("current_entropy") if event_data.get("integrity") else None,
                        process_name=event_data.get("process", {}).get("name") if event_data.get("process") else None,
                        process_id=event_data.get("process", {}).get("pid") if event_data.get("process") else None,
                        suspicious=detection_result.get("suspicious", False),
                        threat_level=detection_result.get("threat_level", "none"),
                        is_decoy=app.state.decoy_manager.is_decoy_file(event_data.get("path"))
                    )
                    session.add(file_event)
                    await session.commit()
                    break  # Success, exit retry loop
            except Exception as db_error:
                if "locked" in str(db_error).lower() and attempt < max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                elif attempt == max_retries - 1:
                    logger.warning(f"Failed to store event after {max_retries} attempts: {db_error}")
                    break
        
        # Handle threats
        if detection_result.get("suspicious"):
            await handle_threat(event_data, detection_result)
        
        # Broadcast to connected clients
        await broadcast_event({
            "type": "file_event",
            "data": {
                "path": event_data.get("path"),
                "event_type": event_data.get("type"),
                "threat_level": detection_result.get("threat_level"),
                "indicators": detection_result.get("indicators"),
                "timestamp": event_data.get("timestamp").isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error handling file event: {e}")


async def handle_threat(event_data: dict, detection_result: dict):
    """Handle detected threats"""
    try:
        incident_id = str(uuid.uuid4())
        threat_level = detection_result.get("threat_level")
        
        # Print alert to console
        process_info = event_data.get('process', {})
        process_name = process_info.get('name', 'Unknown')
        process_pid = process_info.get('pid', 0)
        process_exe = process_info.get('exe', '')
        
        print("\n" + "="*80)
        print(f"🚨 RANSOMWARE THREAT DETECTED! 🚨")
        print("="*80)
        print(f"Threat Level: {threat_level.upper()}")
        print(f"File: {event_data.get('path')}")
        print(f"Process: {process_name} (PID: {process_pid})")
        if process_exe and process_exe != "Unknown Process":
            print(f"Process Path: {process_exe}")
        print(f"Indicators: {', '.join(detection_result.get('indicators', []))}")
        print(f"Confidence: {detection_result.get('confidence', 0) * 100:.1f}%")
        print(f"Threat Score: {detection_result.get('threat_score', 0)}/100")
        print(f"Incident ID: {incident_id}")
        print("="*80 + "\n")
        
        # Create incident with retry logic to prevent DB locking
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with db.async_session() as session:
                    incident = Incident(
                        incident_id=incident_id,
                        status="active",
                        severity=threat_level,
                        process_name=event_data.get("process", {}).get("name"),
                        process_id=event_data.get("process", {}).get("pid"),
                        attack_vector=json.dumps(detection_result.get("indicators")),
                        detection_methods=json.dumps({"methods": detection_result.get("indicators")}),
                        confidence_score=detection_result.get("confidence"),
                        affected_files_count=1
                    )
                    session.add(incident)
                    
                    # Create alert
                    alert = Alert(
                        alert_type="ransomware_detected",
                        severity=threat_level,
                        message=f"Ransomware detected: {', '.join(detection_result.get('indicators', []))}",
                        details=json.dumps({
                            "file_path": event_data.get("path"),
                            "process": event_data.get("process"),
                            "detection": detection_result
                        }),
                        incident_id=incident_id
                    )
                    session.add(alert)
                    await session.commit()
                    break  # Success
            except Exception as db_error:
                if "locked" in str(db_error).lower() and attempt < max_retries - 1:
                    await asyncio.sleep(0.2 * (attempt + 1))
                    continue
                else:
                    logger.error(f"Failed to save incident after {attempt + 1} attempts: {db_error}")
                    break
        
        active_incidents[incident_id] = {
            "id": incident_id,
            "start_time": datetime.now(timezone.utc),
            "threat_level": threat_level,
            "severity": threat_level,
            "status": "active",
            "process": event_data.get("process", {}),
            "indicators": detection_result.get("indicators", []),
            "file_path": event_data.get("path")
        }
        
        # Execute containment if recommended
        if detection_result.get("recommended_action") == "contain":
            containment_result = await app.state.containment.execute_containment(
                active_incidents[incident_id],
                auto=True
            )
            
            # Log containment actions
            async with db.async_session() as session:
                for action in containment_result.get("actions_taken", []):
                    containment_action = ContainmentAction(
                        incident_id=incident_id,
                        action_type=action.get("action"),
                        target=action.get("target", ""),
                        success=action.get("success"),
                        auto_triggered=True
                    )
                    session.add(containment_action)
                await session.commit()
        
        # Broadcast alert
        await broadcast_event({
            "type": "threat_detected",
            "data": {
                "incident_id": incident_id,
                "severity": threat_level,
                "indicators": detection_result.get("indicators"),
                "file_path": event_data.get("path")
            }
        })
        
    except Exception as e:
        logger.error(f"Error handling threat: {e}")


async def broadcast_event(event: dict):
    """Broadcast event to all connected WebSocket clients"""
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_json(event)
        except Exception:
            disconnected.add(client)
    
    connected_clients.difference_update(disconnected)


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"WebSocket client connected. Total: {len(connected_clients)}")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(connected_clients)}")


# REST API Endpoints

@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "running",
        "monitoring": app.state.monitor.is_running,
        "system_running": system_running,
        "protected_paths": len(app.state.monitor.protected_paths),
        "decoy_files": len(app.state.decoy_manager.decoy_registry),
        "active_incidents": len(active_incidents),
        "connected_clients": len(connected_clients)
    }


@app.post("/api/system/start")
async def start_system():
    """Start system monitoring"""
    global system_running
    
    try:
        if system_running and app.state.monitor.is_running:
            return {
                "success": False,
                "message": "System is already running",
                "system_running": True
            }
        
        # Start the file monitor
        if not app.state.monitor.is_running:
            app.state.monitor.start()
        
        system_running = True
        logger.info("System monitoring started")
        
        # Broadcast event to all clients
        await broadcast_event({
            "type": "system_started",
            "data": {
                "message": "System monitoring has been started",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        return {
            "success": True,
            "message": "System monitoring started successfully",
            "system_running": True
        }
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start system: {str(e)}")


@app.post("/api/system/stop")
async def stop_system():
    """Stop system monitoring"""
    global system_running
    
    try:
        if not system_running:
            return {
                "success": False,
                "message": "System is already stopped",
                "system_running": False
            }
        
        # Stop the file monitor
        if app.state.monitor.is_running:
            app.state.monitor.stop()
        
        system_running = False
        logger.info("System monitoring stopped")
        
        # Broadcast event to all clients
        await broadcast_event({
            "type": "system_stopped",
            "data": {
                "message": "System monitoring has been stopped",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        return {
            "success": True,
            "message": "System monitoring stopped successfully",
            "system_running": False
        }
    except Exception as e:
        logger.error(f"Failed to stop system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop system: {str(e)}")


@app.get("/api/incidents")
async def get_incidents(limit: int = 50):
    """Get recent incidents with containment information"""
    async with db.async_session() as session:
        result = await session.execute(
            select(Incident).order_by(desc(Incident.start_time)).limit(limit)
        )
        incidents = result.scalars().all()
        
        # Get containment actions for each incident
        incidents_data = []
        for inc in incidents:
            # Get containment actions from database
            containment_result = await session.execute(
                select(ContainmentAction).where(ContainmentAction.incident_id == inc.incident_id)
            )
            containment_actions = containment_result.scalars().all()
            
            # Check if incident was contained
            is_contained = len(containment_actions) > 0
            successful_actions = [a for a in containment_actions if a.success]
            
            incidents_data.append({
                "id": inc.incident_id,
                "start_time": inc.start_time.isoformat(),
                "severity": inc.severity,
                "status": inc.status,
                "process_name": inc.process_name,
                "affected_files": inc.affected_files_count,
                "is_contained": is_contained,
                "containment_actions_count": len(containment_actions),
                "successful_actions_count": len(successful_actions),
                "containment_actions": [
                    {
                        "action_type": action.action_type,
                        "success": action.success,
                        "target": action.target,
                        "timestamp": action.timestamp.isoformat(),
                        "auto_triggered": action.auto_triggered
                    }
                    for action in containment_actions
                ]
            })
        
        return incidents_data


@app.get("/api/events")
async def get_events(limit: int = 100):
    """Get recent file events"""
    async with db.async_session() as session:
        result = await session.execute(
            select(FileEvent).order_by(desc(FileEvent.timestamp)).limit(limit)
        )
        events = result.scalars().all()
        return [
            {
                "id": evt.id,
                "timestamp": evt.timestamp.isoformat(),
                "type": evt.event_type,
                "path": evt.file_path,
                "threat_level": evt.threat_level,
                "suspicious": evt.suspicious
            }
            for evt in events
        ]


@app.get("/api/alerts")
async def get_alerts(unacknowledged_only: bool = False):
    """Get alerts"""
    async with db.async_session() as session:
        query = select(Alert).order_by(desc(Alert.timestamp))
        if unacknowledged_only:
            query = query.where(Alert.acknowledged == False)
        
        result = await session.execute(query.limit(50))
        alerts = result.scalars().all()
        return [
            {
                "id": alert.id,
                "timestamp": alert.timestamp.isoformat(),
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "acknowledged": alert.acknowledged
            }
            for alert in alerts
        ]


@app.delete("/api/alerts/{alert_id}")
async def delete_alert(alert_id: int):
    """Delete a specific alert"""
    try:
        async with db.async_session() as session:
            # Get the alert
            result = await session.execute(select(Alert).where(Alert.id == alert_id))
            alert = result.scalar_one_or_none()
            
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            # Delete the alert
            await session.delete(alert)
            await session.commit()
            
            logger.info(f"Deleted alert ID: {alert_id}")
            
            return {
                "success": True,
                "message": "Alert deleted successfully",
                "deleted_id": alert_id
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")


@app.post("/api/alerts/delete-all")
async def delete_all_alerts():
    """Delete all alerts"""
    try:
        async with db.async_session() as session:
            # Get all alerts
            result = await session.execute(select(Alert))
            alerts = result.scalars().all()
            
            deleted_count = 0
            for alert in alerts:
                await session.delete(alert)
                deleted_count += 1
            
            await session.commit()
            
            logger.info(f"Deleted {deleted_count} alerts")
            
            return {
                "success": True,
                "message": f"Deleted {deleted_count} alerts",
                "deleted_count": deleted_count
            }
    except Exception as e:
        logger.error(f"Failed to delete all alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete alerts: {str(e)}")


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Mark an alert as acknowledged"""
    try:
        async with db.async_session() as session:
            # Get the alert
            result = await session.execute(select(Alert).where(Alert.id == alert_id))
            alert = result.scalar_one_or_none()
            
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            # Mark as acknowledged
            alert.acknowledged = True
            alert.acknowledged_at = datetime.now(timezone.utc)
            await session.commit()
            
            logger.info(f"Acknowledged alert ID: {alert_id}")
            
            return {
                "success": True,
                "message": "Alert acknowledged",
                "alert_id": alert_id
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


# Quarantine API Endpoints

@app.get("/api/quarantine")
async def get_quarantined_items():
    """Get all quarantined items"""
    from database.models import QuarantineItem
    async with db.async_session() as session:
        result = await session.execute(select(QuarantineItem).order_by(desc(QuarantineItem.timestamp)))
        items = result.scalars().all()
        return [
            {
                "id": item.id,
                "incident_id": item.incident_id,
                "original_path": item.original_path,
                "quarantine_path": item.quarantine_path,
                "file_hash": item.file_hash,
                "process_name": item.process_name,
                "timestamp": item.timestamp.isoformat(),
                "status": item.status
            }
            for item in items
        ]

@app.post("/api/quarantine/{item_id}/restore")
async def restore_quarantined_item(item_id: int):
    """Restore a quarantined item to its original location"""
    from database.models import QuarantineItem
    from core.quarantiner import get_quarantiner
    
    try:
        async with db.async_session() as session:
            result = await session.execute(select(QuarantineItem).where(QuarantineItem.id == item_id))
            item = result.scalar_one_or_none()
            
            if not item:
                raise HTTPException(status_code=404, detail="Quarantined item not found")
                
            if item.status != "quarantined":
                raise HTTPException(status_code=400, detail=f"Item is already {item.status}")
                
            quarantiner = get_quarantiner()
            success = quarantiner.restore_file(item.quarantine_path, item.original_path)
            
            if success:
                item.status = "restored"
                await session.commit()
                return {"success": True, "message": "File restored successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to restore file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring quarantine item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/quarantine/{item_id}")
async def delete_quarantined_item(item_id: int):
    """Permanently delete a quarantined item"""
    from database.models import QuarantineItem
    from core.quarantiner import get_quarantiner
    
    try:
        async with db.async_session() as session:
            result = await session.execute(select(QuarantineItem).where(QuarantineItem.id == item_id))
            item = result.scalar_one_or_none()
            
            if not item:
                raise HTTPException(status_code=404, detail="Quarantined item not found")
                
            if item.status == "deleted":
                return {"success": True, "message": "Item already deleted"}
                
            quarantiner = get_quarantiner()
            success = quarantiner.delete_file(item.quarantine_path)
            
            if success:
                item.status = "deleted"
                await session.commit()
                return {"success": True, "message": "File permanently deleted"}
            else:
                raise HTTPException(status_code=500, detail="Failed to delete file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting quarantine item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/containment/{incident_id}")
async def trigger_containment(incident_id: str):
    """Manually trigger containment for an incident"""
    try:
        if incident_id not in active_incidents:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        incident = active_incidents[incident_id]
        logger.info(f"Manual containment triggered for incident: {incident_id}")
        
        result = await app.state.containment.execute_containment(incident, auto=False)
        
        # Log containment actions to database
        async with db.async_session() as session:
            for action in result.get("actions_taken", []):
                containment_action = ContainmentAction(
                    incident_id=incident_id,
                    action_type=action.get("action"),
                    target=action.get("target", ""),
                    success=action.get("success"),
                    auto_triggered=False
                )
                session.add(containment_action)
            
            for action in result.get("actions_failed", []):
                containment_action = ContainmentAction(
                    incident_id=incident_id,
                    action_type=action.get("action"),
                    target=action.get("target", ""),
                    success=False,
                    auto_triggered=False
                )
                session.add(containment_action)
            
            await session.commit()
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual containment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Containment failed: {str(e)}")


@app.post("/api/containment/disable-lockdown")
async def disable_system_lockdown():
    """
    إيقاف العزل الشامل للنظام - Disable System Lockdown
    يقوم بإعادة تفعيل الشبكة وإلغاء جميع إجراءات العزل
    """
    try:
        logger.info("Disabling system lockdown - restoring network and system access")
        
        actions_taken = []
        actions_failed = []
        
        # 1. إعادة تفعيل محولات الشبكة
        network_result = await app.state.containment.restore_network()
        if network_result["success"]:
            actions_taken.append(network_result)
            logger.info("Network adapters restored successfully")
        else:
            actions_failed.append(network_result)
            logger.warning(f"Failed to restore network: {network_result.get('error')}")
        
        # 2. تحديث حالة جميع الحوادث النشطة إلى "resolved"
        resolved_incidents = []
        for incident_id, incident in list(active_incidents.items()):
            incident["status"] = "resolved"
            resolved_incidents.append(incident_id)
        
        # 3. تحديث قاعدة البيانات
        async with db.async_session() as session:
            # تحديث حالة الحوادث في قاعدة البيانات
            for incident_id in resolved_incidents:
                result = await session.execute(
                    select(Incident).where(Incident.incident_id == incident_id)
                )
                db_incident = result.scalar_one_or_none()
                if db_incident:
                    db_incident.status = "resolved"
                    db_incident.end_time = datetime.now(timezone.utc)
            
            # تسجيل إجراء إلغاء العزل
            lockdown_action = ContainmentAction(
                incident_id="system_lockdown_disable",
                action_type="disable_lockdown",
                target="system",
                success=True,
                auto_triggered=False
            )
            session.add(lockdown_action)
            await session.commit()
        
        # 4. إرسال إشعار للعملاء المتصلين
        await broadcast_event({
            "type": "lockdown_disabled",
            "data": {
                "message": "System lockdown has been disabled",
                "network_restored": network_result["success"],
                "resolved_incidents": resolved_incidents,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        result = {
            "success": True,
            "message": "System lockdown disabled successfully",
            "actions_taken": actions_taken,
            "actions_failed": actions_failed,
            "resolved_incidents": resolved_incidents,
            "network_restored": network_result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"System lockdown disabled: {len(actions_taken)} actions successful, {len(actions_failed)} failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to disable system lockdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to disable lockdown: {str(e)}")


@app.get("/api/decoys")
async def get_decoys():
    """Get decoy file information"""
    return {
        "total": len(app.state.decoy_manager.decoy_registry),
        "decoys": [
            {
                **decoy_info,
                "compromised": False  # Check if file hash changed
            }
            for decoy_info in app.state.decoy_manager.decoy_registry.values()
        ]
    }


@app.post("/api/decoys/deploy")
async def deploy_decoys(count: int = 10):
    """Deploy new decoy files and save to database"""
    try:
        if count < 1 or count > 100:
            raise HTTPException(status_code=400, detail="Count must be between 1 and 100")
        
        # Create decoy files
        created_decoys = app.state.decoy_manager.create_decoy_files(count=count)
        
        # Save to database
        async with db.async_session() as session:
            for decoy_info in created_decoys:
                # Check if already exists
                result = await session.execute(
                    select(DecoyFile).where(DecoyFile.file_path == decoy_info["path"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    db_decoy = DecoyFile(
                        file_path=decoy_info["path"],
                        file_hash=decoy_info["hash"],
                        file_type=decoy_info["type"],
                        is_compromised=False,
                        access_count=0
                    )
                    session.add(db_decoy)
            
            await session.commit()
            logger.info(f"Saved {len(created_decoys)} decoys to database")
        
        logger.info(f"Deployed {len(created_decoys)} new decoy files")
        
        return {
            "success": True,
            "message": f"Successfully deployed {len(created_decoys)} decoy files",
            "deployed_count": len(created_decoys),
            "total_decoys": len(app.state.decoy_manager.decoy_registry),
            "decoys": created_decoys
        }
    except Exception as e:
        logger.error(f"Failed to deploy decoys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deploy decoys: {str(e)}")


@app.delete("/api/decoys/{decoy_path:path}")
async def delete_decoy(decoy_path: str):
    """Delete a specific decoy file from filesystem, registry, and database"""
    try:
        
        # Check if decoy exists in registry
        if decoy_path not in app.state.decoy_manager.decoy_registry:
            raise HTTPException(status_code=404, detail="Decoy not found")
        
        # Delete from database
        async with db.async_session() as session:
            result = await session.execute(
                select(DecoyFile).where(DecoyFile.file_path == decoy_path)
            )
            db_decoy = result.scalar_one_or_none()
            
            if db_decoy:
                await session.delete(db_decoy)
                await session.commit()
                logger.info(f"Deleted decoy from database: {decoy_path}")
        
        # Delete the physical file
        if os.path.exists(decoy_path):
            os.remove(decoy_path)
            logger.info(f"Deleted decoy file: {decoy_path}")
        
        # Remove from in-memory registry
        del app.state.decoy_manager.decoy_registry[decoy_path]
        
        logger.info(f"Deleted decoy completely: {decoy_path}")
        
        return {
            "success": True,
            "message": "Decoy file deleted successfully",
            "deleted_path": decoy_path,
            "remaining_decoys": len(app.state.decoy_manager.decoy_registry)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete decoy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete decoy: {str(e)}")


@app.post("/api/decoys/delete-all")
async def delete_all_decoys():
    """Delete all decoy files from filesystem, registry, and database"""
    try:
        
        deleted_count = 0
        failed_count = 0
        
        # Copy registry keys to avoid modification during iteration
        decoy_paths = list(app.state.decoy_manager.decoy_registry.keys())
        
        # Delete all from database first
        async with db.async_session() as session:
            result = await session.execute(select(DecoyFile))
            db_decoys = result.scalars().all()
            
            for db_decoy in db_decoys:
                await session.delete(db_decoy)
            
            await session.commit()
            logger.info(f"Deleted {len(db_decoys)} decoys from database")
        
        # Delete physical files and from registry
        for decoy_path in decoy_paths:
            try:
                # Delete physical file
                if os.path.exists(decoy_path):
                    os.remove(decoy_path)
                
                # Remove from registry
                del app.state.decoy_manager.decoy_registry[decoy_path]
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete file {decoy_path}: {e}")
                failed_count += 1
        
        logger.info(f"Deleted {deleted_count} decoy files from filesystem ({failed_count} failed)")
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} decoy files",
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "remaining_decoys": len(app.state.decoy_manager.decoy_registry)
        }
    except Exception as e:
        logger.error(f"Failed to delete all decoys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete decoys: {str(e)}")


@app.delete("/api/events/{event_id}")
async def delete_event(event_id: int):
    """Delete a specific event"""
    try:
        async with db.async_session() as session:
            result = await session.execute(select(FileEvent).where(FileEvent.id == event_id))
            event = result.scalar_one_or_none()
            
            if not event:
                raise HTTPException(status_code=404, detail="Event not found")
            
            await session.delete(event)
            await session.commit()
            
            logger.info(f"Deleted event ID: {event_id}")
            
            return {
                "success": True,
                "message": "Event deleted successfully",
                "deleted_id": event_id
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")


@app.post("/api/events/delete-all")
async def delete_all_events():
    """Delete all events"""
    try:
        async with db.async_session() as session:
            result = await session.execute(select(FileEvent))
            events = result.scalars().all()
            
            deleted_count = 0
            for event in events:
                await session.delete(event)
                deleted_count += 1
            
            await session.commit()
            
            logger.info(f"Deleted {deleted_count} events")
            
            return {
                "success": True,
                "message": f"Deleted {deleted_count} events",
                "deleted_count": deleted_count
            }
    except Exception as e:
        logger.error(f"Failed to delete all events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete events: {str(e)}")


@app.get("/api/stats")
async def get_statistics():
    """Get system statistics"""
    from sqlalchemy import func
    async with db.async_session() as session:
        # Use SQL COUNT for performance — avoid loading all rows into RAM
        total_events = await session.scalar(select(func.count(FileEvent.id)))
        suspicious_count = await session.scalar(
            select(func.count(FileEvent.id)).where(FileEvent.suspicious == True)
        )
        
        # Get cached monitored files count (faster)
        monitored_files_count = getattr(app.state, 'monitored_files_cache', 0)
        
        return {
            "total_events": total_events or 0,
            "suspicious_events": suspicious_count or 0,
            "active_incidents": len(active_incidents),
            "decoy_files": len(app.state.decoy_manager.decoy_registry),
            "monitored_files": monitored_files_count
        }


@app.get("/api/settings/containment")
async def get_containment_settings():
    """Get current containment settings"""
    return {
        "auto_contain": app.state.containment.auto_contain,
        "isolate_network": app.state.containment.containment_config.get("isolate_network", True),
        "kill_process": app.state.containment.containment_config.get("kill_process", True),
        "disable_network_drives": app.state.containment.containment_config.get("disable_network_drives", True),
        "lock_system": app.state.containment.containment_config.get("lock_system", False),
        "enable_backup": getattr(app.state.file_protector, "enabled", True)
    }


@app.post("/api/settings/containment")
async def update_containment_settings(settings: dict):
    """Update containment settings"""
    try:
        # Update in-memory settings
        if "auto_contain" in settings:
            app.state.containment.auto_contain = settings["auto_contain"]
            app.state.containment.containment_config["auto_contain"] = settings["auto_contain"]
        
        if "isolate_network" in settings:
            app.state.containment.containment_config["isolate_network"] = settings["isolate_network"]
        
        if "kill_process" in settings:
            app.state.containment.containment_config["kill_process"] = settings["kill_process"]
        
        if "disable_network_drives" in settings:
            app.state.containment.containment_config["disable_network_drives"] = settings["disable_network_drives"]
        
        if "lock_system" in settings:
            app.state.containment.containment_config["lock_system"] = settings["lock_system"]
            
        if "enable_backup" in settings:
            app.state.file_protector.enabled = settings["enable_backup"]
            if "protection" not in config:
                config["protection"] = {}
            config["protection"]["enabled"] = settings["enable_backup"]
        
        # Update config file
        config["containment"].update({k: v for k, v in settings.items() if k in config["containment"]})
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Containment settings updated: {settings}")
        
        return {
            "success": True,
            "message": "Settings updated successfully",
            "settings": await get_containment_settings()
        }
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/report")
async def export_report(days: int = 7):
    """Export comprehensive security report"""
    try:
        from fastapi.responses import JSONResponse
        
        # Get incidents from database
        async with db.async_session() as session:
            result = await session.execute(
                select(Incident).order_by(desc(Incident.start_time)).limit(500)
            )
            incidents = result.scalars().all()
            
            # Get events
            events_result = await session.execute(
                select(FileEvent).order_by(desc(FileEvent.timestamp)).limit(1000)
            )
            events = events_result.scalars().all()
            
            # Get alerts
            alerts_result = await session.execute(
                select(Alert).order_by(desc(Alert.timestamp)).limit(100)
            )
            alerts = alerts_result.scalars().all()
        
        # Calculate statistics
        total_incidents = len(incidents)
        active_incidents_count = len([i for i in incidents if i.status == 'active'])
        contained_incidents = len([i for i in incidents if i.status == 'contained'])
        
        total_events = len(events)
        suspicious_events = len([e for e in events if e.suspicious])
        
        # Get containment actions
        async with db.async_session() as session:
            containment_result = await session.execute(
                select(ContainmentAction).order_by(desc(ContainmentAction.timestamp)).limit(500)
            )
            containment_actions = containment_result.scalars().all()
        
        successful_containments = len([a for a in containment_actions if a.success])
        failed_containments = len([a for a in containment_actions if not a.success])
        
        # Build comprehensive report
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period_days": days,
            "system_info": {
                "monitoring_active": app.state.monitor.is_running,
                "protected_paths": len(app.state.monitor.protected_paths),
                "decoy_files": len(app.state.decoy_manager.decoy_registry),
                "auto_containment": app.state.containment.auto_contain
            },
            "summary": {
                "total_incidents": total_incidents,
                "active_incidents": active_incidents_count,
                "contained_incidents": contained_incidents,
                "total_events": total_events,
                "suspicious_events": suspicious_events,
                "detection_rate": round((suspicious_events / total_events * 100) if total_events > 0 else 0, 2),
                "containment_success_rate": round((successful_containments / len(containment_actions) * 100) if containment_actions else 0, 2)
            },
            "incidents": [
                {
                    "id": inc.incident_id,
                    "start_time": inc.start_time.isoformat(),
                    "severity": inc.severity,
                    "status": inc.status,
                    "process_name": inc.process_name,
                    "affected_files": inc.affected_files_count
                }
                for inc in incidents[:100]  # Top 100 incidents
            ],
            "top_threats": {
                "by_severity": {},
                "by_process": {}
            },
            "containment_actions": {
                "total": len(containment_actions),
                "successful": successful_containments,
                "failed": failed_containments,
                "by_type": {}
            },
            "alerts": [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message
                }
                for alert in alerts[:50]  # Top 50 alerts
            ]
        }
        
        # Calculate threat distribution
        severity_count = {}
        process_count = {}
        action_type_count = {}
        
        for inc in incidents:
            severity_count[inc.severity] = severity_count.get(inc.severity, 0) + 1
            if inc.process_name:
                process_count[inc.process_name] = process_count.get(inc.process_name, 0) + 1
        
        for action in containment_actions:
            action_type_count[action.action_type] = action_type_count.get(action.action_type, 0) + 1
        
        report["top_threats"]["by_severity"] = severity_count
        report["top_threats"]["by_process"] = dict(sorted(process_count.items(), key=lambda x: x[1], reverse=True)[:10])
        report["containment_actions"]["by_type"] = action_type_count
        
        return JSONResponse(content=report)
        
    except Exception as e:
        logger.error(f"Failed to export report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= File Protection API Endpoints =============

@app.get("/api/protection/stats")
async def get_protection_stats():
    """الحصول على إحصائيات النسخ الاحتياطية"""
    try:
        stats = app.state.file_protector.get_statistics()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Failed to get protection stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/protection/backups/{file_path:path}")
async def get_file_backups(file_path: str):
    """الحصول على جميع النسخ الاحتياطية لملف معين"""
    try:
        backups = app.state.file_protector.get_backup_info(file_path)
        return JSONResponse(content={"file": file_path, "backups": backups})
    except Exception as e:
        logger.error(f"Failed to get file backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/protection/restore")
async def restore_file(file_path: str, version_index: int = -1):
    """استرجاع ملف من النسخة الاحتياطية"""
    try:
        success = app.state.file_protector.restore_file(file_path, version_index)
        
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": f"File restored: {file_path}",
                "file_path": file_path
            })
        else:
            raise HTTPException(status_code=404, detail="Backup not found or restore failed")
            
    except Exception as e:
        logger.error(f"Failed to restore file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/protection/restore-all")
async def restore_all_files():
    """استرجاع جميع الملفات من النسخ الاحتياطية"""
    try:
        results = app.state.file_protector.restore_all_files()
        
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        return JSONResponse(content={
            "status": "completed",
            "total_files": len(results),
            "successful": successful,
            "failed": failed,
            "details": results
        })
        
    except Exception as e:
        logger.error(f"Failed to restore all files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/protection/manual-backup")
async def create_manual_backup(file_path: str):
    """إنشاء نسخة احتياطية يدوية لملف"""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        backup_info = app.state.file_protector.create_backup(file_path)
        
        if backup_info:
            return JSONResponse(content={
                "status": "success",
                "message": "Backup created successfully",
                "backup": backup_info
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to create backup")
            
    except Exception as e:
        logger.error(f"Failed to create manual backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Drive Monitoring API Endpoints =============

@app.get("/api/drives/stats")
async def get_drives_stats():
    """الحصول على إحصائيات الأقراص المراقبة"""
    try:
        stats = app.state.usb_monitor.get_drive_statistics()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Failed to get drive stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/drives/list")
async def list_monitored_drives():
    """قائمة الأقراص المراقبة"""
    try:
        all_drives = app.state.usb_monitor.get_all_drives()
        removable = app.state.usb_monitor.get_removable_drives()
        
        drives_info = []
        for drive in all_drives:
            drives_info.append({
                "path": drive,
                "type": "USB/Removable" if drive in removable else "Fixed",
                "monitored": drive in app.state.monitor.protected_paths
            })
        
        return JSONResponse(content={"drives": drives_info})
    except Exception as e:
        logger.error(f"Failed to list drives: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Monitoring Configuration API Endpoints =============

@app.get("/api/monitoring/modes")
async def get_monitoring_modes():
    """الحصول على أوضاع المراقبة الحالية"""
    try:
        modes = app.state.monitoring_config.get_all_modes()
        descriptions = {
            "user_files": app.state.monitoring_config.get_description("user_files"),
            "decoy_files": app.state.monitoring_config.get_description("decoy_files"),
            "system_files": app.state.monitoring_config.get_description("system_files")
        }
        
        return JSONResponse(content={
            "modes": modes,
            "descriptions": descriptions
        })
    except Exception as e:
        logger.error(f"Failed to get monitoring modes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitoring/modes/set")
async def set_monitoring_mode(mode: str, enabled: bool):
    """تفعيل/تعطيل وضع مراقبة معين"""
    try:
        success = app.state.monitoring_config.set_monitoring_mode(mode, enabled)
        
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": f"Monitoring mode '{mode}' set to {enabled}",
                "modes": app.state.monitoring_config.get_all_modes()
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to set monitoring mode")
            
    except Exception as e:
        logger.error(f"Failed to set monitoring mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitoring/modes/update-all")
async def update_all_monitoring_modes(modes: dict):
    """تحديث جميع أوضاع المراقبة"""
    try:
        success = app.state.monitoring_config.set_all_modes(modes)
        
        if success:
            # إعادة تشغيل المراقبة لتطبيق التغييرات
            logger.info("Restarting monitoring with new configuration...")
            
            return JSONResponse(content={
                "status": "success",
                "message": "Monitoring modes updated successfully",
                "current_modes": app.state.monitoring_config.get_all_modes(),
                "note": "Changes will take effect immediately"
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to update monitoring modes")
            
    except Exception as e:
        logger.error(f"Failed to update all monitoring modes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Serve frontend if built
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

@app.get("/")
async def root():
    """Serve dashboard or API info"""
    frontend_index = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build", "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    
    return {
        "name": "Ransomware Detection & Containment Engine",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "status": "/api/status",
            "incidents": "/api/incidents",
            "events": "/api/events",
            "alerts": "/api/alerts",
            "decoys": "/api/decoys",
            "stats": "/api/stats",
            "websocket": "/ws"
        },
        "dashboard": "Build frontend with 'npm run build' in frontend directory"
    }

@app.get("/dashboard")
async def serve_dashboard():
    """Serve dashboard (alias to root)"""
    frontend_index = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build", "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    
    return {"error": "Dashboard not built. Run 'npm run build' in frontend directory."}


if __name__ == "__main__":
    import uvicorn
    
    host = config.get("api", {}).get("host", "0.0.0.0")
    port = config.get("api", {}).get("port", 8000)
    
    uvicorn.run(app, host=host, port=port)
