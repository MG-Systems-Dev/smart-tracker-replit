# Database Implementation - Fixes Checklist

## Priority 1: CRITICAL (Do First)

### Issue 1.1: Fix Multiple Database Instances
- **File**: All page files in `src/pages/`
- **Affected Files**:
  - [ ] `src/pages/log_session.py` - Line 30
  - [ ] `src/pages/sessions.py` - Line 250
  - [ ] `src/pages/calculator.py` - Line 27
  - [ ] `src/pages/home_dashboard.py` - Line 26
  - [ ] `src/pages/tech_stack.py` - Line 29
  - [ ] `src/pages/analytics.py` - Line 28
  - [ ] `src/pages/dropdown_manager.py` - Line 33
  - [ ] `src/pages/planning.py` - Line 26
  - [ ] `src/pages/learning_sources.py` - Line 26

- **Current Code** (WRONG):
```python
if 'db' not in st.session_state:
    st.session_state.db = DatabaseStorage()
db = st.session_state.db
```

- **Correct Code**:
```python
from src.core.app import get_database
db = get_database()
```

- **Checklist**:
  - [ ] Replace code in all 9 page files
  - [ ] Test that all pages still work
  - [ ] Run `test_database.py` to verify
  - [ ] Commit changes with message: "fix: Use singleton DatabaseStorage in all pages"

---

### Issue 1.2: Add Cache Invalidation on Database Writes
- **File**: `src/services/cached_queries.py`
- **Method to Implement**: Automatic cache invalidation

- **Step 1**: Create wrapper methods that invalidate cache
```python
# In cached_queries.py, add:
@staticmethod
def invalidate_on_write(func):
    """Decorator to invalidate cache after write operations."""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        CachedQueryService.invalidate_cache()
        return result
    return wrapper
```

- **Step 2**: Call invalidation in all pages after writes
  - [ ] In `log_session.py`: After `db.add_session()` → call `CachedQueryService.invalidate_cache()`
  - [ ] In `sessions.py`: After `db.delete_session()` → call invalidate
  - [ ] In `tech_stack.py`: After `db.add_technology()` → call invalidate
  - [ ] In `dropdown_manager.py`: After any dropdown add → call invalidate
  - [ ] In `home_dashboard.py`: After any update → call invalidate

- **Pattern**:
```python
from src.services.cached_queries import CachedQueryService

# After database write:
db.add_session(session_data)
CachedQueryService.invalidate_cache()
```

- **Checklist**:
  - [ ] Add invalidation to all 5+ pages that write data
  - [ ] Test that data shows updated values immediately
  - [ ] Verify no more 30-60 second delays in data display
  - [ ] Commit: "fix: Add cache invalidation on database writes"

---

### Issue 1.3: Fix Inconsistent Cursor Usage
- **File**: `src/database/operations.py`
- **Methods to Fix** (lines 720-770):
  - [ ] `get_hours_by_technology()` - Line 723
  - [ ] `get_hours_by_category()` - Line 740
  - [ ] `get_hours_by_work_item()` - Line 757
  - [ ] `get_session_type_breakdown()` - Line 1067

- **Current (WRONG)**:
```python
def get_hours_by_technology(self):
    conn = self._get_connection()
    cursor = conn.cursor()  # ❌ Wrong
```

- **Correct**:
```python
def get_hours_by_technology(self):
    conn = self._get_connection()
    cursor = self._get_cursor(conn)  # ✅ Right
```

- **Checklist**:
  - [ ] Change all 4 methods to use `_get_cursor()`
  - [ ] Test with PostgreSQL mode (if possible)
  - [ ] Verify SQLite mode still works
  - [ ] Commit: "fix: Use _get_cursor() consistently in statistics methods"

---

## Priority 2: HIGH (Fix Soon)

### Issue 2.1: Bootstrap Initial Data on First Run
- **File**: `src/core/app.py`
- **Function**: `main()` function

- **Step 1**: Add check for empty database
```python
def main():
    # ... existing code ...
    
    # Check if database is empty and bootstrap if needed
    if db.get_total_sessions() == 0 and db.get_total_categories() == 0:
        bootstrap_initial_data(db)
```

- **Step 2**: Create bootstrap function
```python
def bootstrap_initial_data(db):
    """Bootstrap initial categories and tech stack on first run."""
    from src.core.config import PLANNING_BLUEPRINT
    
    # Add default categories
    for category_name in PLANNING_BLUEPRINT.keys():
        db.add_category(category_name, is_custom=False)
    
    # Add technologies from blueprint
    for category, section in PLANNING_BLUEPRINT.items():
        for subsection in section['subsections']:
            for tool in subsection['tools']:
                tech_name = tool['name']
                goal_hours = tool.get('max_hours', 50)
                db.add_technology(tech_name, category, goal_hours, str(datetime.now().date()))
    
    logging.info("Bootstrapped initial learning blueprint data")
```

- **Checklist**:
  - [ ] Add `get_total_categories()` method to DatabaseStorage
  - [ ] Implement `bootstrap_initial_data()` function
  - [ ] Test on fresh database
  - [ ] Verify categories and tech stack appear
  - [ ] Commit: "feat: Add automatic data bootstrap on first run"

---

### Issue 2.2: Add Foreign Key Constraints
- **File**: `src/database/operations.py`
- **Method**: `_initialize_database()`

- **Add constraints** to sessions table:
```sql
CREATE TABLE IF NOT EXISTS sessions (
    -- ... existing columns ...
    FOREIGN KEY (category_name) REFERENCES categories(category_name),
    FOREIGN KEY (technology) REFERENCES tech_stack(name),
    FOREIGN KEY (work_item) REFERENCES work_items(name),
    FOREIGN KEY (category_source) REFERENCES category_sources(name)
)
```

- **Enable foreign keys** for SQLite:
```python
def _get_connection(self):
    # ... existing code ...
    if not self.use_postgresql:
        # ... existing code ...
        self.conn.execute("PRAGMA foreign_keys=ON;")  # Add this
```

- **Checklist**:
  - [ ] Add PRAGMA foreign_keys=ON for SQLite
  - [ ] Update session table definition with FK constraints
  - [ ] Update tech_stack table definition with FK constraints
  - [ ] Test that delete operations cascade properly
  - [ ] Document FK relationships in README
  - [ ] Commit: "refactor: Add foreign key constraints for referential integrity"

---

### Issue 2.3: Add Database Migration System
- **Tool**: Alembic (database migration tool)

- **Step 1**: Install Alembic
```bash
pip install alembic
alembic init migrations
```

- **Step 2**: Create initial migration
```bash
alembic revision --autogenerate -m "Initial schema"
```

- **Step 3**: Configure for PostgreSQL and SQLite
- **Step 4**: Document migration process

- **Checklist**:
  - [ ] Install Alembic
  - [ ] Initialize migration directory
  - [ ] Create first migration for current schema
  - [ ] Test migration on fresh database
  - [ ] Document in README
  - [ ] Commit: "feat: Add database migration system with Alembic"

---

## Priority 3: MEDIUM (Plan for Next Sprint)

### Issue 3.1: Add Database Health Check
- [ ] Create endpoint: `/api/health/db`
- [ ] Check: Connection works
- [ ] Check: Tables exist
- [ ] Check: Can read/write

### Issue 3.2: Fix Date Field Type
- [ ] Change `session_date` from TEXT to DATE
- [ ] Add migration for existing data
- [ ] Update date validation

### Issue 3.3: Add Connection Pooling
- [ ] For PostgreSQL: Use pgbouncer or sqlalchemy pooling
- [ ] For SQLite: Connection reuse (already done)
- [ ] Add pool statistics endpoint

### Issue 3.4: Add Query Performance Monitoring
- [ ] Log slow queries (>100ms)
- [ ] Add query execution time tracking
- [ ] Create performance dashboard

---

## Priority 4: LOW (Nice to Have)

### Issue 4.1: Cascade Delete for Related Records
- [ ] Update delete_category() to cascade delete tech_stack records
- [ ] Update delete_technology() to cascade delete work_items
- [ ] Update delete_work_item() to cascade delete skills

### Issue 4.2: Full-Text Search
- [ ] Add FTS5 table for sessions notes/tags
- [ ] Create search method in DatabaseStorage
- [ ] Add search UI to sessions page

### Issue 4.3: Automated Backup Scheduling
- [ ] Set up cron job for `scripts/sync_drive.py upload`
- [ ] Add backup health monitoring
- [ ] Create backup statistics endpoint

### Issue 4.4: Pagination Optimization
- [ ] Implement cursor-based pagination
- [ ] Add limit/offset to session queries
- [ ] Update analytics to use aggregates only

---

## Testing Checklist

### After Priority 1 Fixes (Critical)
- [ ] Run `test_database.py` - all tests pass
- [ ] Log multiple sessions - verify they appear immediately
- [ ] Update a session - verify change shows immediately
- [ ] Delete a session - verify it's gone immediately
- [ ] Navigate between pages - verify no stale data
- [ ] Check logs for errors
- [ ] No duplicate database instances
- [ ] Memory usage stable

### After Priority 2 Fixes (High)
- [ ] Fresh database has initial categories
- [ ] Fresh database has initial tech stack
- [ ] Foreign keys prevent orphaned records
- [ ] Migration system works
- [ ] Can migrate between PostgreSQL and SQLite

### Performance Tests
- [ ] Load 100 sessions - verify fast load
- [ ] Load 50 technologies - verify fast dropdown
- [ ] Create 10 new sessions - verify no slowdown
- [ ] Analytics page - no timeout

---

## Deployment Checklist

### Before Production
- [ ] All Priority 1 fixes completed
- [ ] Database backup tested
- [ ] Google Drive sync tested
- [ ] SQLite WAL file handled (not committed)
- [ ] PostgreSQL connection pooling configured
- [ ] Backups scheduled
- [ ] Health checks set up
- [ ] Performance baseline established

### Deployment Steps
```bash
# 1. Backup current database
python scripts/sync_drive.py upload

# 2. Run migrations (if any)
alembic upgrade head

# 3. Run tests
python test_database.py

# 4. Verify cache invalidation
# Manual test: Add session, verify shows immediately

# 5. Monitor logs for 24 hours
tail -f logs/activity.log

# 6. Verify no concurrency issues
# Check: Multiple users, no data corruption
```

---

## Quick Status Tracker

### Critical Issues
- [ ] Issue 1.1: Multiple DB instances - Status: TODO
- [ ] Issue 1.2: Cache invalidation - Status: TODO
- [ ] Issue 1.3: Cursor consistency - Status: TODO

### High Priority
- [ ] Issue 2.1: Bootstrap data - Status: TODO
- [ ] Issue 2.2: Foreign keys - Status: TODO
- [ ] Issue 2.3: Migrations - Status: TODO

### Medium Priority
- [ ] Issue 3.1: Health check - Status: TODO
- [ ] Issue 3.2: Date field - Status: TODO
- [ ] Issue 3.3: Connection pooling - Status: TODO
- [ ] Issue 3.4: Query monitoring - Status: TODO

### Low Priority
- [ ] Issue 4.1: Cascade delete - Status: TODO
- [ ] Issue 4.2: Full-text search - Status: TODO
- [ ] Issue 4.3: Automated backups - Status: TODO
- [ ] Issue 4.4: Pagination - Status: TODO

---

## Resources

### Documentation
- Full Analysis: `DATABASE_ANALYSIS_REPORT.md`
- Quick Summary: `DATABASE_QUICK_SUMMARY.md`
- This Checklist: `DATABASE_FIXES_CHECKLIST.md`

### Files to Reference
- Database layer: `/home/user/MG-smart-tracker/src/database/operations.py`
- Drive sync: `/home/user/MG-smart-tracker/src/database/drive_db_manager.py`
- Services: `/home/user/MG-smart-tracker/src/services/sync_service.py`
- Config: `/home/user/MG-smart-tracker/src/core/config.py`

### Commands
```bash
# Test database
python test_database.py

# Sync with Google Drive
python scripts/sync_drive.py download
python scripts/sync_drive.py upload
python scripts/sync_drive.py verify

# View logs
tail -f logs/activity.log
```

---

## Notes

- Estimated time to fix all Priority 1 issues: 2-3 hours
- Estimated time for all fixes: 2-3 days
- Highest risk area: Cache invalidation timing
- Most important fix: Use singleton DatabaseStorage
- Easiest fix to verify: Cache invalidation (immediate UX improvement)

---

Generated: 2025-11-17
Last Updated: 2025-11-17
Status: Ready for Implementation
