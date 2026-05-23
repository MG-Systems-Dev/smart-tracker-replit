# 🚀 Deployment Checklist - Quick Reference

Use this checklist to deploy your app in 15 minutes.

---

## ☑️ Pre-Deployment (2 minutes)

- [ ] Code is on GitHub (`mgsystemsdev/MG-smart-tracker`)
- [ ] All changes committed and pushed
- [ ] SQLite database exists locally (if migrating data)
- [ ] Have GitHub account ready
- [ ] Have email for Neon signup

---

## ☑️ Step 1: Create Neon Database (5 minutes)

- [ ] Go to [neon.tech](https://neon.tech)
- [ ] Sign up with GitHub
- [ ] Click "Create Project"
- [ ] Name: `mg-smart-tracker`
- [ ] Region: Choose closest to you
- [ ] Copy connection string (save it securely!)

**Connection string format:**
```
postgresql://user:password@ep-xyz-123.region.aws.neon.tech/neondb?sslmode=require
```

---

## ☑️ Step 2: Deploy to Streamlit Cloud (3 minutes)

- [ ] Go to [share.streamlit.io](https://share.streamlit.io)
- [ ] Sign in with GitHub
- [ ] Click "New app"
- [ ] Repository: `mgsystemsdev/MG-smart-tracker`
- [ ] Branch: `main`
- [ ] Main file: `app.py`
- [ ] App URL: `mg-smart-tracker` (or custom name)
- [ ] Python version: `3.11`
- [ ] Click "Deploy"

---

## ☑️ Step 3: Configure Secrets (2 minutes)

While app is deploying:

- [ ] Click "⚙️ Settings" (bottom right)
- [ ] Click "Secrets" tab
- [ ] Paste configuration:

```toml
DATABASE_URL = "postgresql://YOUR_CONNECTION_STRING_HERE"
```

- [ ] Replace with YOUR actual Neon connection string
- [ ] Click "Save"
- [ ] App will auto-restart

---

## ☑️ Step 4: Migrate Data (Optional - 5 minutes)

**Skip this if starting fresh!**

If you have existing SQLite data:

```bash
# Set environment variable
export DATABASE_URL="postgresql://YOUR_CONNECTION_STRING"

# Run migration
python scripts/migrate_to_postgres.py

# Verify
python scripts/verify_migration.py
```

- [ ] Migration completed successfully
- [ ] Verification shows correct row counts
- [ ] No errors in migration log

---

## ☑️ Step 5: Test Deployment (3 minutes)

- [ ] Visit your app URL: `https://mg-smart-tracker.streamlit.app`
- [ ] Home page loads correctly
- [ ] Log a test session
- [ ] Verify session appears on home page
- [ ] Check sessions list page
- [ ] Refresh page - data persists
- [ ] No errors in app

---

## ☑️ Post-Deployment Verification

### Database Connection
- [ ] Logs show: "Connected to PostgreSQL database"
- [ ] No "sqlite" mentions in logs
- [ ] Data persists after app restart

### Functionality
- [ ] Can add sessions
- [ ] Can view analytics
- [ ] Can manage tech stack
- [ ] Can use dropdowns
- [ ] All pages load

### Performance
- [ ] Pages load in < 3 seconds
- [ ] No timeout errors
- [ ] Charts render correctly

---

## ☑️ Optional Enhancements

- [ ] Set up custom domain (Streamlit Teams required)
- [ ] Configure Google Drive sync for backups
- [ ] Set up monitoring/alerts
- [ ] Add Google Analytics
- [ ] Share URL with team

---

## 🆘 Troubleshooting

### App won't start
- Check `requirements.txt` has all dependencies
- Verify Python version is 3.11
- Check Streamlit Cloud logs for errors

### Database connection fails
- Verify `DATABASE_URL` in secrets (no extra spaces)
- Check connection string includes `?sslmode=require`
- Verify Neon database is active

### Data not showing
- Check if using PostgreSQL (not SQLite)
- Verify migration completed
- Check app logs for SQL errors

### App is slow
- Free tier has resource limits
- Consider upgrading to Streamlit Teams
- Optimize queries (already done!)

---

## 📊 Resources

- **Full Guide:** `DEPLOYMENT_GUIDE.md`
- **Database Docs:** `DATABASE_ANALYSIS_REPORT.md`
- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)
- **Neon Docs:** [neon.tech/docs](https://neon.tech/docs)

---

## ✅ Success Criteria

You're done when:

✅ App is live at public URL
✅ Database connection working
✅ Can add and view sessions
✅ Data persists after refresh
✅ No errors in logs

---

**Estimated Total Time:** 15-20 minutes

**Need help?** Check `DEPLOYMENT_GUIDE.md` for detailed instructions.
