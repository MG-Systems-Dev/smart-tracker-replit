# Quick Start: Google Drive Sync Setup

**⏱️ 10 minutes to set up safe cloud backup for your SQLite database**

## Step 1: Enable Google Drive API (5 min)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable **Google Drive API**:
   - APIs & Services → Library → Search "Drive API" → Enable
4. Create **Service Account**:
   - APIs & Services → Credentials → Create Credentials → Service Account
   - Download JSON key file
5. Copy the `client_email` from the JSON (looks like `xxx@xxx.iam.gserviceaccount.com`)

## Step 2: Share Database File (1 min)

1. Upload `data/smart_tracker.db` to Google Drive (or use existing file)
2. Right-click file → Share
3. Paste the service account email from Step 1
4. Grant **Editor** permissions
5. Copy the file ID from URL: `https://drive.google.com/file/d/FILE_ID_HERE/view`

## Step 3: Configure Project (2 min)

```bash
# Create credentials folder
mkdir credentials

# Move your service account JSON
mv ~/Downloads/service-account-xxxxx.json credentials/service-account.json

# Copy environment template
cp .env.example .env
```

Edit `.env`:
```env
GOOGLE_CREDENTIALS=credentials/service-account.json
DRIVE_DB_FILE_ID=your-file-id-from-step-2
DB_PATH=data/smart_tracker.db
```

## Step 4: Test Connection (2 min)

```bash
# Download from Drive (test)
python scripts/sync_drive.py download

# View metadata
python scripts/sync_drive.py metadata

# Upload to Drive (test)
python scripts/sync_drive.py upload
```

## ✅ Done!

Your database is now synced with Google Drive. 

### Next Steps:

**Manual sync anytime:**
```bash
python scripts/sync_drive.py download  # Before work
python scripts/sync_drive.py upload    # After work
```

**Automatic sync in your app:**
See `example_drive_integration.py` for integration pattern.

**Full documentation:**
See [DRIVE_SYNC_GUIDE.md](DRIVE_SYNC_GUIDE.md) for detailed info.

## 🔒 Security Checklist

- ✅ `credentials/` folder is in `.gitignore`
- ✅ `.env` file is in `.gitignore`  
- ✅ Service account has minimal permissions (Drive API only)
- ✅ File shared with service account only (not public)
- ✅ Backups created automatically before sync operations

## 🆘 Troubleshooting

**"File not found" error:**
- Check `DRIVE_DB_FILE_ID` matches URL file ID
- Verify file is shared with service account email

**"Permission denied":**
- Ensure service account has Editor (not Viewer) access
- Check Drive API is enabled in Cloud Console

**Need help?**
See [DRIVE_SYNC_GUIDE.md](DRIVE_SYNC_GUIDE.md) for full troubleshooting guide.
