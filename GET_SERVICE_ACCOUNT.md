# How to Create Service Account Credentials (Step-by-Step)

## 🎯 Goal
Create a **Service Account** (not OAuth Client) for automated Drive sync.

## 📝 Step-by-Step Instructions

### 1. Go to Google Cloud Console
- Open: https://console.cloud.google.com
- Sign in with your Google account

### 2. Select or Create Project
- Click project dropdown at top
- Either select existing project or click "New Project"
- If new: Name it "MG Smart Tracker" → Create

### 3. Enable Google Drive API
- Click ☰ menu → "APIs & Services" → "Library"
- Search: "Google Drive API"
- Click on it → Click "Enable"

### 4. Create Service Account (IMPORTANT - Not OAuth Client!)
- Click ☰ menu → "APIs & Services" → "Credentials"
- Click "**+ CREATE CREDENTIALS**" button at top
- Select "**Service account**" (NOT "OAuth client ID")

### 5. Fill Service Account Details
- **Service account name:** `mg-smart-tracker-sync`
- **Service account ID:** (auto-filled) `mg-smart-tracker-sync`
- **Description:** `SQLite database sync to Google Drive`
- Click "**CREATE AND CONTINUE**"

### 6. Grant Permissions (Optional - Skip)
- Click "**CONTINUE**" (no roles needed for Drive file access)

### 7. Grant Users Access (Optional - Skip)
- Click "**DONE**"

### 8. Create JSON Key
- You'll see your service account in the list
- Click on the service account email (looks like: `mg-smart-tracker-sync@your-project.iam.gserviceaccount.com`)
- Go to "**KEYS**" tab
- Click "**Add Key**" → "**Create new key**"
- Select "**JSON**"
- Click "**CREATE**"
- JSON file downloads automatically

### 9. Identify the Correct File
The downloaded file should:
- Be named like: `your-project-name-abc123.json`
- Contain a field: `"type": "service_account"`
- Contain a field: `"client_email": "...@...iam.gserviceaccount.com"`

**NOT** like:
- ❌ `client_secret_*.json` (that's OAuth, wrong type)
- ❌ Contains `"client_secret"` field (wrong type)

### 10. Copy the Client Email
Open the JSON file and find the `client_email` field:
```json
{
  "type": "service_account",
  "client_email": "mg-smart-tracker-sync@your-project.iam.gserviceaccount.com"
}
```

Copy that email - you'll need it in the next step.

## ✅ Verification Checklist

Your service account JSON should have these fields:
- [x] `"type": "service_account"`
- [x] `"project_id": "..."`
- [x] `"private_key_id": "..."`
- [x] `"private_key": "-----BEGIN PRIVATE KEY-----..."`
- [x] `"client_email": "...@...iam.gserviceaccount.com"`
- [x] `"client_id": "..."`
- [x] `"auth_uri": "https://accounts.google.com/o/oauth2/auth"`
- [x] `"token_uri": "https://oauth2.googleapis.com/token"`

Should **NOT** have:
- [ ] `"client_secret"` (that's OAuth, wrong type)
- [ ] `"redirect_uris"` (that's OAuth, wrong type)

## 🔄 If You Already Created OAuth Client

You can keep both, but for this project:
1. Create the Service Account as described above
2. Use the Service Account JSON (not the OAuth client secret)
3. The OAuth client won't be used

## ➡️ Next Steps After Creating Service Account

1. Move JSON to project:
   ```bash
   mv ~/Downloads/your-project-*.json credentials/service-account.json
   ```

2. Copy the `client_email` from the JSON

3. Share your Google Drive file with that email (Editor permissions)

4. Continue with [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)

## 🆘 Still Confused?

**Quick test:** Open your downloaded JSON and check the first line:
- ✅ If it says `"type": "service_account"` → Correct!
- ❌ If it doesn't have that → Wrong type, follow steps above
