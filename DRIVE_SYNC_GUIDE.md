# Google Drive Database Sync Setup Guide

This guide explains how to safely sync your SQLite database with Google Drive using a service account.

## 🎯 Overview

The Drive sync system allows you to:
- Download the latest database from Google Drive before running your app
- Upload updated database to Drive after operations complete
- Maintain data integrity with WAL checkpointing and verification
- Keep local backups for rollback capability

## 📋 Prerequisites

1. Google Cloud Console account
2. Project with Drive API enabled
3. Service account with credentials
4. Shared Drive file with service account email

## 🔧 Setup Steps

### 1. Create Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Navigate to **APIs & Services** → **Enable APIs and Services**
4. Search for "Google Drive API" and enable it
5. Go to **APIs & Services** → **Credentials**
6. Click **Create Credentials** → **Service Account**
7. Fill in service account details and create
8. Click on the created service account
9. Go to **Keys** tab → **Add Key** → **Create new key** → **JSON**
10. Download the JSON file

### 2. Share Drive File with Service Account

1. Upload your `smart_tracker.db` to Google Drive
2. Open the file in Drive and click **Share**
3. Copy the `client_email` from your service account JSON (looks like `xxx@xxx.iam.gserviceaccount.com`)
4. Share the file with this email address with **Editor** permissions
5. Copy the file ID from the URL: `https://drive.google.com/file/d/FILE_ID_HERE/view`

### 3. Configure Your Project

1. Create a `credentials` folder in your project root:
   ```bash
   mkdir credentials
   ```

2. Move your service account JSON to `credentials/service-account.json`

3. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and fill in:
   ```env
   GOOGLE_CREDENTIALS=credentials/service-account.json
   DRIVE_DB_FILE_ID=your-file-id-from-step-2
   DB_PATH=data/smart_tracker.db
   ```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Manual Sync Commands

**Download database from Drive:**
```bash
python scripts/sync_drive.py download
```

**Download with force (overwrite local):**
```bash
python scripts/sync_drive.py download --force
```

**Upload database to Drive:**
```bash
python scripts/sync_drive.py upload
```

**View Drive file metadata:**
```bash
python scripts/sync_drive.py metadata
```

**Verify database integrity:**
```bash
python scripts/sync_drive.py verify
```

### Programmatic Usage

```python
from dotenv import load_dotenv
import os
from src.database.drive_db_manager import DriveDBManager

load_dotenv()

mgr = DriveDBManager(
    creds_path=os.getenv("GOOGLE_CREDENTIALS"),
    file_id=os.getenv("DRIVE_DB_FILE_ID"),
    local_path=os.getenv("DB_PATH")
)

# Download before app starts
mgr.download_db(force=False)

# Your app logic here
# ...

# Upload after app finishes
mgr.checkpoint_wal()
mgr.upload_db()
```

### Integration with Main App

Add to your `main.py` or startup script:

```python
import os
from dotenv import load_dotenv
from src.database.drive_db_manager import DriveDBManager

load_dotenv()

# Initialize Drive manager (only in SQLite mode)
drive_manager = None
if not os.environ.get("DATABASE_URL"):  # SQLite mode
    try:
        drive_manager = DriveDBManager(
            creds_path=os.getenv("GOOGLE_CREDENTIALS"),
            file_id=os.getenv("DRIVE_DB_FILE_ID"),
            local_path=os.getenv("DB_PATH", "data/smart_tracker.db")
        )
        # Download latest DB
        drive_manager.download_db(force=False)
        print("✅ Database synced from Drive")
    except Exception as e:
        print(f"⚠️ Drive sync unavailable: {e}")

# Your main app code here
# ...

# On shutdown (add to cleanup/exit handler)
if drive_manager:
    drive_manager.checkpoint_wal()
    drive_manager.upload_db()
    print("✅ Database uploaded to Drive")
```

## 🔒 Safety Features

### Automatic Backups
Before any download or upload, the system creates a `.bak` file:
```
data/smart_tracker.db.bak
```

### WAL Checkpointing
Before upload, all Write-Ahead Log data is merged into the main file:
```python
mgr.checkpoint_wal()
```

### Integrity Verification
Verify database health before upload:
```python
mgr.verify_integrity()  # Returns True if OK
```

### Change Detection
Uploads are skipped if database hasn't changed (SHA256 hash comparison)

### Restore from Backup
If something goes wrong:
```python
mgr.restore_from_backup()
```

## ⚠️ Important Notes

### SQLite WAL Files
- **Never** upload `.db-wal` or `.db-shm` files separately
- Always call `checkpoint_wal()` before upload
- WAL files are local-only transaction logs

### Single Writer Constraint
- Only one process should write to the database at a time
- Multiple readers are safe in WAL mode
- For multi-writer, use PostgreSQL instead

### PostgreSQL Mode
Drive sync is automatically disabled when `DATABASE_URL` is set. PostgreSQL databases should use `pg_dump` for backups instead.

### Security
- **Never** commit `credentials/*.json` to git
- **Never** commit `.env` to git
- Service account has minimal permissions (Drive API only)
- File-level sharing (not org-wide)

## 🔍 Troubleshooting

### "File not found" error
- Check that `DRIVE_DB_FILE_ID` is correct
- Verify file is shared with service account email
- Ensure service account has Editor permissions

### "Credentials file not found"
- Check path in `GOOGLE_CREDENTIALS` is correct
- Verify JSON file exists at that path
- Use absolute path if needed

### "Permission denied" errors
- Ensure service account email has Editor access
- Check file sharing settings in Drive
- Verify Drive API is enabled in Cloud Console

### Database integrity check fails
- Run `python scripts/sync_drive.py verify`
- Check logs for SQLite errors
- Restore from backup if needed: `mgr.restore_from_backup()`

### Upload always skipped
- Hash-based change detection may be too aggressive
- Use `upload_db(skip_unchanged=False)` to force upload
- Check if database is actually changing

## 📊 Best Practices

1. **Always checkpoint before upload**: `mgr.checkpoint_wal()`
2. **Verify before upload**: `mgr.verify_integrity()`
3. **Close all connections**: Ensure no active DB connections during sync
4. **Monitor logs**: Check for errors in sync operations
5. **Test restore**: Periodically test backup restoration
6. **Periodic full backups**: Keep manual backups outside of Drive sync

## 🔄 Workflow Example

```python
# === Safe Drive Sync Lifecycle ===

# 1. Download latest version
mgr.download_db(force=False)

# 2. Verify integrity
if not mgr.verify_integrity():
    mgr.restore_from_backup()
    raise Exception("Database corrupt")

# 3. Run your app
from src.database.operations import DatabaseStorage
db = DatabaseStorage()
# ... your operations ...
db.close()

# 4. Checkpoint WAL
mgr.checkpoint_wal()

# 5. Upload changes
mgr.upload_db(skip_unchanged=True)

# 6. Done!
```

## 📝 File Structure

```
MG_Smart_Tracker/
├── credentials/
│   └── service-account.json      # Your service account credentials
├── data/
│   ├── smart_tracker.db           # Main database file
│   ├── smart_tracker.db.bak       # Auto-backup
│   ├── smart_tracker.db-wal       # WAL file (don't upload)
│   └── smart_tracker.db-shm       # Shared memory (don't upload)
├── scripts/
│   └── sync_drive.py              # Manual sync tool
├── src/
│   └── database/
│       ├── drive_db_manager.py    # Drive sync manager
│       └── operations.py          # Database operations
├── .env                           # Your configuration (not in git)
├── .env.example                   # Template
└── DRIVE_SYNC_GUIDE.md           # This file
```
