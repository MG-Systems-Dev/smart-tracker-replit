#!/usr/bin/env python3
"""
Google Drive Database Sync Script.
Use this to manually download/upload your database to/from Google Drive.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.drive_db_manager import DriveDBManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    load_dotenv()
    
    creds_path = os.getenv("GOOGLE_CREDENTIALS")
    file_id = os.getenv("DRIVE_DB_FILE_ID")
    db_path = os.getenv("DB_PATH", "data/smart_tracker.db")
    
    if not creds_path:
        logger.error("GOOGLE_CREDENTIALS not set in .env")
        sys.exit(1)
    
    if not file_id:
        logger.error("DRIVE_DB_FILE_ID not set in .env")
        sys.exit(1)
    
    db_path_abs = project_root / db_path
    
    mgr = DriveDBManager(
        creds_path=creds_path,
        file_id=file_id,
        local_path=str(db_path_abs)
    )
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/sync_drive.py download  # Download DB from Drive")
        print("  python scripts/sync_drive.py upload    # Upload DB to Drive")
        print("  python scripts/sync_drive.py metadata  # Show Drive file info")
        print("  python scripts/sync_drive.py verify    # Check DB integrity")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "download":
        force = "--force" in sys.argv
        success = mgr.download_db(force=force)
        if success:
            logger.info("Database downloaded successfully")
            mgr.verify_integrity()
        else:
            logger.error("Download failed")
            sys.exit(1)
    
    elif command == "upload":
        mgr.checkpoint_wal()
        
        if mgr.verify_integrity():
            success = mgr.upload_db(skip_unchanged=True)
            if success:
                logger.info("Database uploaded successfully")
            else:
                logger.error("Upload failed")
                sys.exit(1)
        else:
            logger.error("Database integrity check failed. Upload aborted.")
            sys.exit(1)
    
    elif command == "metadata":
        meta = mgr.get_drive_metadata()
        if meta:
            print("\n📁 Drive File Metadata:")
            print(f"  Name: {meta.get('name')}")
            print(f"  ID: {meta.get('id')}")
            print(f"  Size: {int(meta.get('size', 0)) / 1024:.2f} KB")
            print(f"  Modified: {meta.get('modifiedTime')}")
            print(f"  MD5: {meta.get('md5Checksum')}")
        else:
            logger.error("Failed to fetch metadata")
            sys.exit(1)
    
    elif command == "verify":
        if mgr.verify_integrity():
            logger.info("✅ Database integrity verified")
        else:
            logger.error("❌ Database integrity check failed")
            sys.exit(1)
    
    else:
        logger.error(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
