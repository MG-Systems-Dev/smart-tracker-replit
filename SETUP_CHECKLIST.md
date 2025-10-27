# Google Drive Sync - Setup Checklist

Use this checklist to set up Google Drive sync for your SQLite database.

## ✅ Pre-Setup (Already Done)

- [x] Drive sync implementation installed
- [x] Dependencies added to requirements.txt
- [x] .gitignore updated for security
- [x] Documentation created

## 📋 Setup Steps (You Need to Complete)

### Step 1: Google Cloud Console Setup

- [ ] Go to [Google Cloud Console](https://console.cloud.google.com)
- [ ] Create or select a project
- [ ] Enable Google Drive API
  - [ ] Navigate to: APIs & Services → Library
  - [ ] Search for "Google Drive API"
  - [ ] Click "Enable"
- [ ] Create Service Account
  - [ ] Navigate to: APIs & Services → Credentials
  - [ ] Click "Create Credentials" → "Service Account"
  - [ ] Name: `mg-smart-tracker-sync` (or your choice)
  - [ ] Click "Create and Continue"
  - [ ] Skip optional steps, click "Done"
- [ ] Download Service Account Key
  - [ ] Click on the created service account
  - [ ] Go to "Keys" tab
  - [ ] Click "Add Key" → "Create new key"
  - [ ] Select "JSON"
  - [ ] Click "Create" (JSON file downloads)
- [ ] Copy the `client_email` from JSON file
  - Example: `mg-smart-tracker-sync@your-project.iam.gserviceaccount.com`

### Step 2: Google Drive File Sharing

- [ ] Upload database to Google Drive (if not already there)
  - File: `data/smart_tracker.db`
- [ ] Share file with service account
  - [ ] Right-click file in Drive → "Share"
  - [ ] Paste the service account email from Step 1
  - [ ] Change permission to **Editor**
  - [ ] Uncheck "Notify people"
  - [ ] Click "Share"
- [ ] Copy file ID from URL
  - URL format: `https://drive.google.com/file/d/FILE_ID_HERE/view`
  - [ ] Copy the FILE_ID_HERE part

### Step 3: Local Project Setup

- [ ] Create credentials folder
  ```bash
  mkdir credentials
  ```
- [ ] Move service account JSON to credentials folder
  ```bash
  mv ~/Downloads/your-service-account-*.json credentials/service-account.json
  ```
- [ ] Create .env file
  ```bash
  cp .env.example .env
  ```
- [ ] Edit .env file with your values:
  ```env
  GOOGLE_CREDENTIALS=credentials/service-account.json
  DRIVE_DB_FILE_ID=your-file-id-from-step-2
  DB_PATH=data/smart_tracker.db
  ```

### Step 4: Test Connection

- [ ] Test Drive API connection
  ```bash
  python scripts/sync_drive.py metadata
  ```
  Expected: Shows file name, size, modified time

- [ ] Test download
  ```bash
  python scripts/sync_drive.py download --force
  ```
  Expected: "✅ Download complete"

- [ ] Verify database integrity
  ```bash
  python scripts/sync_drive.py verify
  ```
  Expected: "✅ Database integrity check passed"

- [ ] Test upload
  ```bash
  python scripts/sync_drive.py upload
  ```
  Expected: "✅ Upload complete" or "⚙️ No changes detected"

### Step 5: Integration (Optional)

- [ ] Review example integration
  ```bash
  cat example_drive_integration.py
  ```

- [ ] Test example integration
  ```bash
  python example_drive_integration.py
  ```

- [ ] Decide integration approach:
  - [ ] Option A: Manual sync (use CLI commands)
  - [ ] Option B: Automatic sync (integrate into main.py)

- [ ] If Option B, add sync code to main.py (see example_drive_integration.py)

## 🔒 Security Verification

- [ ] Verify credentials not in git
  ```bash
  git status --ignored | grep credentials
  ```
  Should show: `credentials/` (ignored)

- [ ] Verify .env not in git
  ```bash
  git status --ignored | grep .env
  ```
  Should show: `.env` (ignored)

- [ ] Verify service account has minimal permissions
  - Only "Google Drive API" scope
  - No other APIs enabled

- [ ] Verify file sharing is private
  - Only service account email has access
  - Not shared with "Anyone with the link"

## 🧪 Testing

- [ ] Download works
- [ ] Upload works
- [ ] Metadata retrieval works
- [ ] Integrity check works
- [ ] Backup creation works (.bak file appears)
- [ ] WAL checkpoint works (no -wal file after checkpoint)
- [ ] Skip unchanged works (second upload skips)

## 📚 Documentation Review

- [ ] Read [QUICK_START_DRIVE_SYNC.md](QUICK_START_DRIVE_SYNC.md)
- [ ] Bookmark [DRIVE_SYNC_GUIDE.md](DRIVE_SYNC_GUIDE.md) for reference
- [ ] Understand safety features
- [ ] Know how to restore from backup

## 🎯 Usage Decision

Choose your workflow:

### Workflow A: Manual Sync (Recommended for Start)
```bash
# Before work session
python scripts/sync_drive.py download

# Work on your app
python main.py

# After work session
python scripts/sync_drive.py upload
```

### Workflow B: Automatic Sync
- Integrate sync into main.py using example_drive_integration.py pattern
- Sync happens automatically on startup/shutdown

### Workflow C: Scheduled Sync
- Set up cron job or Task Scheduler
- Run `python scripts/sync_drive.py upload` daily

- [ ] Decided on workflow
- [ ] Tested chosen workflow

## ✅ Final Verification

- [ ] All setup steps completed
- [ ] Security checks passed
- [ ] Tests successful
- [ ] Documentation reviewed
- [ ] Workflow chosen and tested
- [ ] Ready to use!

## 🆘 Troubleshooting

If anything fails, check:

1. **File not found error**
   - Verify DRIVE_DB_FILE_ID is correct
   - Check file is shared with service account

2. **Permission denied**
   - Ensure service account has Editor (not Viewer) permissions
   - Verify Drive API is enabled

3. **Credentials error**
   - Check GOOGLE_CREDENTIALS path is correct
   - Verify JSON file exists and is valid

4. **Database errors**
   - Run integrity check: `python scripts/sync_drive.py verify`
   - Check database file exists: `ls -la data/smart_tracker.db`

See [DRIVE_SYNC_GUIDE.md](DRIVE_SYNC_GUIDE.md) for detailed troubleshooting.

## 📞 Quick Reference

**Download latest DB:**
```bash
python scripts/sync_drive.py download
```

**Upload current DB:**
```bash
python scripts/sync_drive.py upload
```

**Check file info:**
```bash
python scripts/sync_drive.py metadata
```

**Verify DB health:**
```bash
python scripts/sync_drive.py verify
```

**Force download (overwrite local):**
```bash
python scripts/sync_drive.py download --force
```

---

**Once you've completed this checklist, your Google Drive sync is ready to use! 🎉**
