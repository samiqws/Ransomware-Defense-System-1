import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_directories():
    """Create necessary directories for the application"""
    directories = [
        'data',
        'logs',
        'C:\\Users\\Public\\Documents\\RansomwareDefense\\Protected',
        'C:\\Users\\Public\\Documents\\RansomwareDefense\\Decoys',
        'C:\\Users\\Public\\Documents\\TestArea',
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✓ Created directory: {directory}")
        except Exception as e:
            logger.error(f"✗ Failed to create directory {directory}: {e}")


def initialize_database():
    """Initialize the database"""
    try:
        import asyncio
        from database.database import db
        
        async def init():
            await db.init_db()
            logger.info("✓ Database initialized successfully")
        
        asyncio.run(init())
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")


def check_admin_privileges():
    """Check if running with administrator privileges"""
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if is_admin:
            logger.info("✓ Running with administrator privileges")
        else:
            logger.warning("⚠ Not running as administrator. Some containment features may not work.")
            logger.warning("  Please restart as administrator for full functionality.")
        return is_admin
    except Exception as e:
        logger.warning(f"⚠ Could not check admin privileges: {e}")
        return False


def main():
    """Main setup function"""
    print("=" * 60)
    print("Ransomware Detection & Containment Engine - Setup")
    print("=" * 60)
    print()
    
    # Check admin privileges
    check_admin_privileges()
    print()
    
    # Create directories
    logger.info("Creating required directories...")
    create_directories()
    print()
    
    # Initialize database
    logger.info("Initializing database...")
    initialize_database()
    print()
    
    print("=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    print()
    print("To start the detection engine, run:")
    print("  python main.py")
    print()
    print("Then access the dashboard at:")
    print("  http://localhost:8000")
    print()


if __name__ == "__main__":
    main()
