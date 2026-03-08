from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from .models import Base
import os

class Database:
    def __init__(self, db_path: str = "data/ransomware_defense.db"):
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # SQLite async connection with optimizations for concurrent writes
        self.database_url = f"sqlite+aiosqlite:///{db_path}"
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            future=True,
            connect_args={
                "timeout": 60,
                "check_same_thread": False
            }
        )
        
        # Session factory
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def init_db(self):
        """Initialize database tables"""
        async with self.engine.begin() as conn:
            # Enable WAL mode for better concurrent access
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA synchronous=NORMAL"))
            await conn.execute(text("PRAGMA cache_size=-64000"))  # 64MB cache
            await conn.execute(text("PRAGMA busy_timeout=60000"))  # 60 second timeout
            
            await conn.run_sync(Base.metadata.create_all)
    
    # NOTE: Use db.async_session() directly as a context manager:
    # async with db.async_session() as session:
    #     ...
    
    async def batch_insert_alerts(self, alerts_list: list):
        """
        Batch insert multiple alerts in a single transaction.
        Eliminates database locked errors through bulk operations.
        """
        if not alerts_list:
            return
        
        async with self.async_session() as session:
            try:
                from .models import Alert
                
                # Use bulk_insert_mappings for performance
                session.add_all([Alert(**alert_data) for alert_data in alerts_list])
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                raise e
    
    async def batch_insert_events(self, events_list: list):
        """Batch insert multiple events in a single transaction"""
        if not events_list:
            return
        
        async with self.async_session() as session:
            try:
                from .models import FileEvent
                
                session.add_all([FileEvent(**event_data) for event_data in events_list])
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                raise e
    
    async def batch_insert_incidents(self, incidents_list: list):
        """Batch insert multiple incidents in a single transaction"""
        if not incidents_list:
            return
        
        async with self.async_session() as session:
            try:
                from .models import Incident
                
                session.add_all([Incident(**incident_data) for incident_data in incidents_list])
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                raise e
    
    async def close(self):
        """Close database connection"""
        await self.engine.dispose()


# Global database instance
db = Database()
