"""
Google Drive SQLite Database Sync Manager.
Safely downloads/uploads SQLite database to Google Drive using service account.
"""

import os
import io
import hashlib
import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError


logger = logging.getLogger(__name__)


class DriveDBManager:
    """Manages safe sync of SQLite database with Google Drive."""
    
    def __init__(self, creds_path: str, file_id: str, local_path: str):
        self.creds_path = creds_path
        self.file_id = file_id
        self.local_path = Path(local_path)
        self.backup_path = self.local_path.with_suffix('.db.bak')
        self.meta_cache = {}
        
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"Credentials file not found: {creds_path}")
        
        self.creds = service_account.Credentials.from_service_account_file(
            creds_path, 
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=self.creds)
        logger.info("DriveDBManager initialized")

    def _hash_file(self, path: Path) -> str:
        """Calculate SHA256 hash of file."""
        if not path.exists():
            return ""
        
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _backup_local_db(self) -> bool:
        """Create backup of current local database."""
        if not self.local_path.exists():
            logger.warning("No local database to backup")
            return False
        
        try:
            shutil.copy2(self.local_path, self.backup_path)
            logger.info(f"Backup created: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def download_db(self, force: bool = False) -> bool:
        """
        Download database from Google Drive.
        
        Args:
            force: Force download even if file exists locally
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            if self.local_path.exists() and not force:
                logger.info("Local database exists. Use force=True to overwrite.")
                return False
            
            if self.local_path.exists():
                self._backup_local_db()
            
            logger.info(f"⏬ Downloading database from Drive (file_id: {self.file_id})...")
            
            request = self.service.files().get_media(fileId=self.file_id)
            
            os.makedirs(self.local_path.parent, exist_ok=True)
            
            fh = io.FileIO(self.local_path, "wb")
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"  Download progress: {progress}%")
            
            fh.close()
            
            file_hash = self._hash_file(self.local_path)
            self.meta_cache["last_download_hash"] = file_hash
            self.meta_cache["last_download_time"] = datetime.now().isoformat()
            
            logger.info("✅ Download complete")
            return True
            
        except HttpError as e:
            logger.error(f"Drive API error during download: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return False

    def checkpoint_wal(self) -> bool:
        """
        Checkpoint WAL (Write-Ahead Log) to main database file.
        This merges all WAL data into the main .db file.
        MUST be called before uploading to ensure data integrity.
        
        Returns:
            True if checkpoint successful, False otherwise
        """
        if not self.local_path.exists():
            logger.warning("Cannot checkpoint: database file does not exist")
            return False
        
        try:
            logger.info("🔄 Checkpointing WAL...")
            
            conn = sqlite3.connect(self.local_path)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.commit()
            conn.close()
            
            logger.info("✅ WAL checkpoint complete")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error during checkpoint: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during checkpoint: {e}")
            return False

    def upload_db(self, skip_unchanged: bool = True) -> bool:
        """
        Upload database to Google Drive.
        
        Args:
            skip_unchanged: Skip upload if file hasn't changed (based on hash)
            
        Returns:
            True if upload successful or skipped, False on error
        """
        if not self.local_path.exists():
            logger.error("Cannot upload: database file does not exist")
            return False
        
        try:
            current_hash = self._hash_file(self.local_path)
            last_hash = self.meta_cache.get("last_upload_hash")
            
            if skip_unchanged and last_hash == current_hash:
                logger.info("⚙️  No changes detected; skipping upload")
                return True
            
            self._backup_local_db()
            
            logger.info(f"⏫ Uploading database to Drive (file_id: {self.file_id})...")
            
            media = MediaFileUpload(
                str(self.local_path), 
                mimetype='application/x-sqlite3',
                resumable=True
            )
            
            updated_file = self.service.files().update(
                fileId=self.file_id,
                media_body=media
            ).execute()
            
            self.meta_cache["last_upload_hash"] = current_hash
            self.meta_cache["last_upload_time"] = datetime.now().isoformat()
            self.meta_cache["drive_revision_id"] = updated_file.get("id")
            
            logger.info("✅ Upload complete")
            return True
            
        except HttpError as e:
            logger.error(f"Drive API error during upload: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return False

    def get_drive_metadata(self) -> Optional[dict]:
        """Fetch metadata about the Drive file."""
        try:
            file_meta = self.service.files().get(
                fileId=self.file_id,
                fields="id,name,size,modifiedTime,md5Checksum"
            ).execute()
            return file_meta
        except HttpError as e:
            logger.error(f"Failed to fetch metadata: {e}")
            return None

    def restore_from_backup(self) -> bool:
        """Restore database from local backup."""
        if not self.backup_path.exists():
            logger.error("No backup file found")
            return False
        
        try:
            shutil.copy2(self.backup_path, self.local_path)
            logger.info(f"✅ Restored from backup: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False

    def verify_integrity(self) -> bool:
        """Verify SQLite database integrity."""
        if not self.local_path.exists():
            logger.error("Database file does not exist")
            return False
        
        try:
            conn = sqlite3.connect(self.local_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()[0]
            conn.close()
            
            if result == "ok":
                logger.info("✅ Database integrity check passed")
                return True
            else:
                logger.error(f"Database integrity check failed: {result}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Database integrity check error: {e}")
            return False
