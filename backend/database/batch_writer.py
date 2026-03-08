"""
Professional Batch Writer for Database Operations
Eliminates "database is locked" errors through queue-based batch inserts
"""

import time
import logging
from typing import List, Dict, Any
from threading import Thread, Lock
from queue import Queue, Empty
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class BatchWriter:
    """
    High-performance batch writer for database operations.
    Queues database writes and flushes them in batches to eliminate locks.
    """
    
    def __init__(self, database, batch_size: int = 100, flush_interval: float = 5.0, event_loop=None):
        """
        Initialize batch writer.
        
        Args:
            database: Database instance
            batch_size: Number of items to batch before auto-flush (default: 100)
            flush_interval: Seconds between auto-flushes (default: 5.0)
            event_loop: The running asyncio event loop (required for async DB calls)
        """
        self.database = database
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.event_loop = event_loop  # Must be set to the main FastAPI event loop
        
        # Separate queues for different data types
        self.alerts_queue: List[Dict] = []
        self.events_queue: List[Dict] = []
        self.incidents_queue: List[Dict] = []
        
        # Thread safety
        self.lock = Lock()
        
        # Auto-flush management
        self.last_flush = time.time()
        self.running = True
        self.flush_thread = Thread(target=self._auto_flush_loop, daemon=True)
        self.flush_thread.start()
        
        # Performance metrics
        self.total_queued = 0
        self.total_flushed = 0
        self.flush_count = 0
        
        logger.info(f"BatchWriter initialized (batch_size={batch_size}, flush_interval={flush_interval}s)")
    
    def add_alert(self, alert_data: Dict):
        """Add alert to batch queue"""
        with self.lock:
            self.alerts_queue.append(alert_data)
            self.total_queued += 1
            
            # Auto-flush if batch size reached
            if len(self.alerts_queue) >= self.batch_size:
                self._flush_alerts()
    
    def add_event(self, event_data: Dict):
        """Add event to batch queue"""
        with self.lock:
            self.events_queue.append(event_data)
            self.total_queued += 1
            
            if len(self.events_queue) >= self.batch_size:
                self._flush_events()
    
    def add_incident(self, incident_data: Dict):
        """Add incident to batch queue"""
        with self.lock:
            self.incidents_queue.append(incident_data)
            self.total_queued += 1
            
            if len(self.incidents_queue) >= self.batch_size:
                self._flush_incidents()
    
    def _flush_alerts(self):
        """Flush alerts queue to database"""
        if not self.alerts_queue:
            return
        
        try:
            batch = self.alerts_queue.copy()
            count = len(batch)
            
            # Batch insert with retry
            success = self._batch_insert_with_retry('alerts', batch)
            
            if success:
                self.alerts_queue.clear()
                self.total_flushed += count
                self.flush_count += 1
                logger.debug(f"Flushed {count} alerts to database")
            else:
                logger.error(f"Failed to flush {count} alerts after retries")
        
        except Exception as e:
            logger.error(f"Error flushing alerts: {e}")
    
    def _flush_events(self):
        """Flush events queue to database"""
        if not self.events_queue:
            return
        
        try:
            batch = self.events_queue.copy()
            count = len(batch)
            
            success = self._batch_insert_with_retry('events', batch)
            
            if success:
                self.events_queue.clear()
                self.total_flushed += count
                self.flush_count += 1
                logger.debug(f"Flushed {count} events to database")
            else:
                logger.error(f"Failed to flush {count} events after retries")
        
        except Exception as e:
            logger.error(f"Error flushing events: {e}")
    
    def _flush_incidents(self):
        """Flush incidents queue to database"""
        if not self.incidents_queue:
            return
        
        try:
            batch = self.incidents_queue.copy()
            count = len(batch)
            
            success = self._batch_insert_with_retry('incidents', batch)
            
            if success:
                self.incidents_queue.clear()
                self.total_flushed += count
                self.flush_count += 1
                logger.debug(f"Flushed {count} incidents to database")
            else:
                logger.error(f"Failed to flush {count} incidents after retries")
        
        except Exception as e:
            logger.error(f"Error flushing incidents: {e}")
    
    def _batch_insert_with_retry(self, table_name: str, items: List[Dict], max_retries: int = 3) -> bool:
        """
        Batch insert with retry logic.
        Calls async database methods safely from the sync background thread
        using asyncio.run_coroutine_threadsafe.
        """
        import asyncio
        
        if self.event_loop is None or not self.event_loop.is_running():
            logger.error("BatchWriter: event_loop not set or not running — cannot flush batch")
            return False
        
        for attempt in range(max_retries):
            try:
                if table_name == 'alerts':
                    coro = self.database.batch_insert_alerts(items)
                elif table_name == 'events':
                    coro = self.database.batch_insert_events(items)
                elif table_name == 'incidents':
                    coro = self.database.batch_insert_incidents(items)
                else:
                    logger.error(f"Unknown table: {table_name}")
                    return False
                
                # Submit the coroutine to the running event loop and wait for result
                future = asyncio.run_coroutine_threadsafe(coro, self.event_loop)
                future.result(timeout=30)  # Wait up to 30s for the insert to complete
                return True
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5
                    logger.warning(f"Batch insert failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Batch insert failed after {max_retries} attempts: {e}")
                    return False
        
        return False
    
    def _auto_flush_loop(self):
        """Background thread for auto-flushing based on time"""
        while self.running:
            try:
                time.sleep(1)  # Check every second
                
                current_time = time.time()
                if current_time - self.last_flush >= self.flush_interval:
                    self.flush_all()
                    self.last_flush = current_time
            
            except Exception as e:
                logger.error(f"Error in auto-flush loop: {e}")
    
    def flush_all(self):
        """Flush all queues immediately"""
        with self.lock:
            self._flush_alerts()
            self._flush_events()
            self._flush_incidents()
        
        logger.debug("All queues flushed")
    
    def get_stats(self) -> Dict:
        """Get batch writer statistics"""
        with self.lock:
            return {
                'total_queued': self.total_queued,
                'total_flushed': self.total_flushed,
                'flush_count': self.flush_count,
                'pending_alerts': len(self.alerts_queue),
                'pending_events': len(self.events_queue),
                'pending_incidents': len(self.incidents_queue),
                'flush_rate': f"{self.total_flushed / self.flush_count:.1f} items/flush" if self.flush_count > 0 else "N/A"
            }
    
    def shutdown(self):
        """Graceful shutdown - flush all pending items"""
        logger.info("BatchWriter shutting down...")
        self.running = False
        
        # Final flush
        self.flush_all()
        
        # Wait for flush thread
        if self.flush_thread.is_alive():
            self.flush_thread.join(timeout=5)
        
        stats = self.get_stats()
        logger.info(f"BatchWriter shutdown complete. Final stats: {stats}")


# Global instance
_batch_writer = None


def get_batch_writer(database=None, batch_size: int = 100, flush_interval: float = 5.0, event_loop=None):
    """Get or create global batch writer instance"""
    global _batch_writer
    
    if _batch_writer is None and database is not None:
        _batch_writer = BatchWriter(
            database=database,
            batch_size=batch_size,
            flush_interval=flush_interval,
            event_loop=event_loop
        )
    
    return _batch_writer
