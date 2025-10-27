#!/usr/bin/env python3
"""
Example: How to integrate Drive sync into your existing app.
This shows the recommended pattern for startup/shutdown sync.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

from src.database.drive_db_manager import DriveDBManager
from src.database.operations import DatabaseStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    load_dotenv()
    
    drive_manager = None
    db = None
    
    try:
        if not os.environ.get("DATABASE_URL"):
            logger.info("Running in SQLite mode - Drive sync enabled")
            
            creds_path = os.getenv("GOOGLE_CREDENTIALS")
            file_id = os.getenv("DRIVE_DB_FILE_ID")
            db_path = os.getenv("DB_PATH", "data/smart_tracker.db")
            
            if creds_path and file_id:
                try:
                    drive_manager = DriveDBManager(
                        creds_path=creds_path,
                        file_id=file_id,
                        local_path=db_path
                    )
                    
                    logger.info("⏬ Downloading latest database from Drive...")
                    drive_manager.download_db(force=False)
                    
                    if drive_manager.verify_integrity():
                        logger.info("✅ Database integrity verified")
                    else:
                        logger.error("❌ Database integrity check failed")
                        logger.info("Restoring from backup...")
                        drive_manager.restore_from_backup()
                        
                except Exception as e:
                    logger.warning(f"⚠️ Drive sync unavailable: {e}")
                    logger.info("Continuing with local database...")
            else:
                logger.info("Drive credentials not configured - using local DB only")
        else:
            logger.info("Running in PostgreSQL mode - Drive sync disabled")
        
        db = DatabaseStorage()
        
        logger.info("🚀 Running your app logic...")
        
        projects = db.execute_query_fetchall("SELECT * FROM projects LIMIT 5;")
        logger.info(f"Found {len(projects)} projects")
        
        logger.info("✅ App execution complete")
        
    except KeyboardInterrupt:
        logger.info("⚠️ Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error during execution: {e}", exc_info=True)
    finally:
        if db:
            logger.info("Closing database connection...")
            db.close()
        
        if drive_manager:
            logger.info("⏫ Syncing database to Drive...")
            try:
                drive_manager.checkpoint_wal()
                
                if drive_manager.verify_integrity():
                    drive_manager.upload_db(skip_unchanged=True)
                    logger.info("✅ Database synced to Drive")
                else:
                    logger.error("❌ Database integrity check failed - upload aborted")
            except Exception as e:
                logger.error(f"❌ Error during Drive upload: {e}")


if __name__ == "__main__":
    main()
