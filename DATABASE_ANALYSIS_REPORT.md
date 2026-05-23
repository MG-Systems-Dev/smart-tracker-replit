# MG Smart Tracker - Database Implementation Analysis

## Executive Summary

The MG Smart Tracker application uses a **dual-mode database architecture** supporting both PostgreSQL (for production/Replit) and SQLite (for local development). The implementation is comprehensive, well-documented, and includes a recent Google Drive sync feature for database backup and synchronization.

---

## 1. DATABASE TECHNOLOGY & ARCHITECTURE

### Current Technology
- **Primary**: SQLite 3 (local development)
- **Secondary**: PostgreSQL (production/Replit)
- **Mode Selection**: Automatic based on `DATABASE_URL` environment variable
  - If `DATABASE_URL` is set → Uses PostgreSQL
  - If empty → Uses SQLite at `data/smart_tracker.db`

### Database File Location
- **SQLite**: `/home/user/MG-smart-tracker/data/smart_tracker.db` (created on first run)
- **Associated files** (SQLite specific):
  - `smart_tracker.db-wal` (Write-Ahead Log)
  - `smart_tracker.db-shm` (Shared Memory)
  - `smart_tracker.db.bak` (Automatic backup)

### Configuration
**File**: `src/database/operations.py` (1,167 lines)
- Main class: `DatabaseStorage`
- Initialization: `_initialize_database()` method
- Connection management: `_get_connection()` and `_get_cursor()`

---

## 2. DATABASE INITIALIZATION & CONFIGURATION

### Entry Points
1. **Main App**: `src/core/app.py`
   ```python
   @st.cache_resource
   def get_database():
       return DatabaseStorage()  # Singleton pattern
   ```

2. **Individual Pages**: Each page creates `DatabaseStorage()` (non-optimal)
   - `src/pages/log_session.py`
   - `src/pages/sessions.py`
   - `src/pages/calculator.py`
   - `src/pages/home_dashboard.py`
   - `src/pages/tech_stack.py`
   - `src/pages/analytics.py`
   - `src/pages/dropdown_manager.py`
   - `src/pages/planning.py`
   - `src/pages/learning_sources.py`

### Initialization Process
```python
def __init__(self):
    self.database_url = os.environ.get("DATABASE_URL")
    self.use_postgresql = bool(self.database_url)
    
    if self.use_postgresql:
        self.conn = None  # Lazy connection for PostgreSQL
    else:
        self.db_path = "data/smart_tracker.db"
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = None
    
    self._initialize_database()  # Creates tables
```

### SQLite Configuration Features
- **WAL Mode**: `PRAGMA journal_mode=WAL;` - Improves concurrency
- **Timeout**: `PRAGMA busy_timeout=5000;` - 5-second timeout for locks
- **Thread Safety**: `check_same_thread=False` - Allows multi-threaded access
- **Row Factory**: `sqlite3.Row` - Dict-like row access

---

## 3. DATABASE SCHEMA

### Tables Created (8 Total)

#### 1. **sessions** (Main learning sessions table)
```sql
CREATE TABLE sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_date TEXT NOT NULL,
    session_type TEXT NOT NULL,          -- 'Studying' or 'Practice'
    category_name TEXT NOT NULL,
    technology TEXT NOT NULL,
    work_item TEXT,
    skill_topic TEXT,
    category_source TEXT,
    difficulty TEXT,
    status TEXT,
    hours_spent REAL NOT NULL,
    tags TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 2. **tech_stack** (Technology definitions with goals)
```sql
CREATE TABLE tech_stack (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    goal_hours REAL DEFAULT 50,
    date_added TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 3. **dropdowns** (Hierarchical dropdown values)
```sql
CREATE TABLE dropdowns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT NOT NULL,
    field_value TEXT NOT NULL,
    parent_field TEXT,
    parent_value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(field_name, field_value, parent_field, parent_value)
)
```

#### 4. **categories** (Learning categories)
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL,
    is_custom INTEGER DEFAULT 0,
    date_added TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 5. **work_items** (Manually defined work items)
```sql
CREATE TABLE work_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    technology TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, technology)
)
```

#### 6. **skills** (Manually defined skills)
```sql
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    work_item TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, work_item)
)
```

#### 7. **category_sources** (Learning platforms/sources)
```sql
CREATE TABLE category_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 8. **app_state** (Persistent UI state)
```sql
CREATE TABLE app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Database Indexes (5 Total)
```sql
CREATE INDEX idx_sessions_date ON sessions(session_date)
CREATE INDEX idx_sessions_tech ON sessions(technology)
CREATE INDEX idx_sessions_category ON sessions(category_name)
CREATE INDEX idx_dropdowns_field ON dropdowns(field_name)
CREATE INDEX idx_dropdowns_parent ON dropdowns(parent_field, parent_value)
```

### Schema Relationships
```
categories ─────────┐
                    ├──> tech_stack
tech_stack ─────────┤
                    ├──> dropdowns (technology values)
                    └──> sessions (category_name field)

technology ────────────> work_items ────────> skills
                              │
                              └──> sessions (work_item field)
```

---

## 4. DATABASE OPERATIONS & CRUD

### Session Operations (12 methods)
- `add_session()` - Insert new session
- `get_all_sessions()` - Retrieve all sessions
- `get_session_by_id()` - Get specific session
- `update_session()` - Modify session
- `delete_session()` - Remove session
- `get_total_sessions()` - Count sessions
- `get_total_hours()` - Sum hours
- `get_total_technologies()` - Count distinct techs

### Tech Stack Operations (7 methods)
- `add_technology()`
- `get_all_tech_stack()`
- `get_technology_by_id()`
- `get_tech_by_name()`
- `update_technology()`
- `delete_technology()`
- `get_overall_progress()` - Calculate progress %

### Category Operations (7 methods)
- `add_category()`
- `get_all_categories()`
- `get_custom_categories()`
- `delete_category()`
- `rename_category()`
- `category_exists()`
- `count_sessions_by_category()`

### Dropdown Operations (3 methods)
- `add_dropdown_value()`
- `get_dropdown_values()`
- `delete_dropdown_value()`

### Analytics Operations (6 methods)
- `get_hours_by_technology()` - Dict: tech → hours
- `get_hours_by_category()` - Dict: category → hours
- `get_hours_by_work_item()` - Dict: work_item → hours
- `get_session_type_breakdown()` - Dict: type → hours
- `get_technologies_by_category()`
- `get_work_items_by_technology()`
- `get_skills_by_work_item()`

### Work Items & Skills (6 methods)
- `add_work_item()` / `delete_work_item()` / `get_all_work_items()`
- `add_skill()` / `delete_skill()` / `get_all_skills()`

### Category Sources (3 methods)
- `add_category_source()`
- `delete_category_source()`
- `get_all_category_sources()`

### App State Operations (2 methods)
- `save_app_state()` - Persist UI state
- `get_app_state()` - Retrieve UI state (used for page navigation)

---

## 5. GOOGLE DRIVE SYNC INTEGRATION

### Recent Implementation (Commit: 5440b5e)
Date: October 27, 2025

### Core Component: `DriveDBManager`
**File**: `src/database/drive_db_manager.py` (251 lines)

#### Key Features
1. **Download Database** - From Google Drive to local
   - Automatic backup creation
   - Progress tracking
   - SHA256 hash tracking for change detection
   - Force override capability

2. **Upload Database** - From local to Google Drive
   - WAL checkpoint (ensures all data in main file)
   - Change detection (skip upload if unchanged)
   - Resumable uploads for large files
   - Automatic backup before upload

3. **Safety Mechanisms**
   - Automatic `.db.bak` backups
   - `PRAGMA integrity_check` before uploads
   - SHA256 hash-based change detection
   - WAL checkpoint to prevent file fragmentation
   - Restore from backup capability

4. **Configuration (`.env`)**
   ```env
   GOOGLE_CREDENTIALS=credentials/service-account.json
   DRIVE_DB_FILE_ID=your-file-id-here
   DB_PATH=data/smart_tracker.db
   DATABASE_URL=  # Leave empty for SQLite
   ```

### Command-Line Tool
**File**: `scripts/sync_drive.py` (109 lines)

Usage:
```bash
python scripts/sync_drive.py download       # Download from Drive
python scripts/sync_drive.py upload         # Upload to Drive (with integrity check)
python scripts/sync_drive.py metadata       # Show file info
python scripts/sync_drive.py verify         # Check DB integrity
```

### Integration Example
**File**: `example_drive_integration.py` (96 lines)

Shows recommended pattern:
1. Download on startup
2. Run app normally
3. Checkpoint and upload on shutdown

### Key Methods in DriveDBManager
```python
download_db(force=False)           # Download from Drive
upload_db(skip_unchanged=True)     # Upload to Drive
checkpoint_wal()                   # Merge WAL into main file
verify_integrity()                 # Check DB integrity
get_drive_metadata()               # Fetch file info
restore_from_backup()              # Restore from .bak
_hash_file()                       # SHA256 hash calculation
_backup_local_db()                 # Create .db.bak
```

---

## 6. EXISTING DATABASE-RELATED ERRORS & ISSUES

### Issues Found

#### 1. **CRITICAL: Multiple Database Instances (Potential Concurrency Issues)**
**Status**: Active Issue
**Location**: All page files (`src/pages/*.py`)
**Problem**: Each page creates its own `DatabaseStorage()` instance instead of using the singleton
```python
# In app.py (CORRECT)
@st.cache_resource
def get_database():
    return DatabaseStorage()  # Singleton

# In each page (WRONG - creates new instance)
if 'db' not in st.session_state:
    st.session_state.db = DatabaseStorage()  # NEW instance!
```
**Impact**: 
- Potential data race conditions in SQLite WAL mode
- Multiple connections competing for same database
- Increased memory usage
- Cache invalidation issues with Streamlit

**Recommendation**: Use the cached singleton from `app.py` instead of creating new instances

---

#### 2. **WARNING: Cache Invalidation Not Triggered on Writes**
**Status**: Active Issue
**Location**: `src/services/cached_queries.py` + all pages
**Problem**: `CachedQueryService.invalidate_cache()` is defined but never called after database modifications
```python
# After add_session(), update_session(), delete_session()
# Should call: CachedQueryService.invalidate_cache()
# But it's not being called anywhere
```
**Impact**: 
- Stale cached data displayed after modifications
- Users see old values until cache TTL expires (60-30 seconds)
- Confusing UX when user makes changes

**Recommendation**: Call `CachedQueryService.invalidate_cache()` after all write operations

---

#### 3. **WARNING: Data Not Initialized on Fresh Start**
**Status**: Active Issue
**Location**: `src/core/app.py`
**Problem**: No bootstrap of initial categories/tech stack on first run
```python
# Current: Database created but empty
# Missing: Initial categories, tech stack, dropdowns
```
**Impact**: 
- App shows empty state until user adds data
- New users see confusing empty dropdowns
- No pre-populated learning blueprint

**Recommendation**: Add optional bootstrap script or first-run setup

---

#### 4. **BUG: Transaction Handling Inconsistency**
**Status**: Moderate Issue
**Location**: `src/database/operations.py` - Statistics methods
**Problem**: Methods like `get_hours_by_technology()` get cursor directly without `_get_cursor()`
```python
def get_hours_by_technology(self):
    cursor = conn.cursor()  # ❌ Direct cursor, not _get_cursor()
    # vs.
def add_session(self):
    cursor = self._get_cursor(conn)  # ✅ Uses wrapper
```
**Impact**: 
- Inconsistent error handling
- Missing special cursor handling for PostgreSQL
- Row dictionary access may fail in some cases

**Recommendation**: Use `_get_cursor()` consistently throughout

---

#### 5. **WARNING: SQL Placeholder Logic**
**Status**: Minor Issue
**Location**: `src/database/operations.py` lines 84-108
**Problem**: Parameter placeholder replacement in application code
```python
placeholder = self._get_placeholder()
if placeholder != "%s":
    formatted_query = query.replace("%s", placeholder)
# Risk: Simple string replace could break if SQL has strings with "%s"
```
**Impact**: 
- Potential SQL injection if query string contains "%s" in literals
- Workaround works but not ideal

**Recommendation**: Use prepared statements exclusively (already mostly done)

---

#### 6. **WARNING: No NULL Column Defaults**
**Status**: Design Issue
**Location**: `src/database/operations.py`
**Problem**: Optional fields like `work_item`, `skill_topic` default to NULL but treated inconsistently
```sql
work_item TEXT,           -- Can be NULL
skill_topic TEXT,         -- Can be NULL
```
**Impact**: 
- Need to check both `IS NULL` and `!= ''` in queries
- Inconsistent filtering logic
- Could cause issues with GROUP BY

**Recommendation**: Use empty string as default instead of NULL

---

#### 7. **WARNING: Missing Foreign Key Constraints**
**Status**: Design Issue
**Location**: Schema definition
**Problem**: No FOREIGN KEY constraints defined
```sql
-- sessions.technology references tech_stack.name
-- But NO CONSTRAINT to enforce referential integrity
```
**Impact**: 
- Orphaned records possible (delete tech_stack but sessions remain)
- Data consistency not guaranteed at database level
- Relies entirely on application logic

**Recommendation**: Add FOREIGN KEY constraints (if compatible with app logic)

---

### Potential Issues (Not Yet Manifested)

#### 8. **POTENTIAL: WAL File Lock Issues**
**Status**: Latent Risk
**Location**: SQLite configuration
**Problem**: WAL mode enabled with `check_same_thread=False`
**Risk**: Race conditions between Streamlit reruns

#### 9. **POTENTIAL: Date Format Inconsistency**
**Status**: Latent Risk
**Location**: `session_date` field uses TEXT, not DATE
**Problem**: Stored as "2025-01-01" string, not proper date
**Impact**: Sorting, filtering by date range less efficient

#### 10. **POTENTIAL: Missing Cascade Delete**
**Status**: Latent Risk
**Location**: All delete operations
**Problem**: Deleting category doesn't cascade to tech_stack and sessions
**Workaround**: Service classes handle this (`sync_service.py`)
**Risk**: If database accessed directly, referential integrity violated

---

## 7. GOOGLE DRIVE SYNC ISSUES & CONSIDERATIONS

### Implemented Safely
✅ WAL checkpoint before upload
✅ Integrity check before upload
✅ Automatic backups
✅ Hash-based change detection
✅ Error handling and rollback

### Not Yet Implemented (Design Notes)
- ❌ Automatic scheduled sync
- ❌ Conflict resolution for simultaneous edits
- ❌ Multi-file versioning
- ❌ Incremental sync (only changed tables)
- ❌ Encryption at rest
- ❌ Web UI for sync management

### Risk Areas
1. **Network Failures**: If download/upload fails mid-operation
   - Mitigated by: Backup creation, verify_integrity()

2. **Large Database**: No progress indication in Streamlit integration
   - Mitigated by: resumable uploads in DriveDBManager

3. **Simultaneous Access**: If database accessed while syncing
   - Risk: SQLite locks, file corruption
   - Recommendation: Only sync during app startup/shutdown

---

## 8. DATABASE MIGRATION & INITIALIZATION ISSUES

### Current State
- **No migration system**: Tables created on first init, never altered
- **No version tracking**: Can't distinguish schema versions
- **No seed data**: Empty database on fresh start

### Bootstrap Script
**File**: `scripts/bootstrap_blueprint.py`
- Seeds initial tech stack from PLANNING_BLUEPRINT
- Optional, manual activation needed

### App State Persistence
- Uses `app_state` table to persist current page
- Allows resuming to last page on restart
- Good UX pattern

### Observations
1. Database schema is stable (no migrations needed)
2. No ALTER TABLE statements found
3. CREATE TABLE IF NOT EXISTS handles re-initialization
4. Schema additions would require manual deployment care

---

## 9. DATABASE UTILITIES & HELPERS

### Main Utility Classes

#### `DatabaseStorage` (src/database/operations.py)
- 1,167 lines
- 40+ public methods
- Supports PostgreSQL/SQLite

#### `DriveDBManager` (src/database/drive_db_manager.py)
- 251 lines
- 7 public methods
- Google Drive sync capability

#### `TechnologySyncService` (src/services/sync_service.py)
- Maintains consistency between tech_stack and dropdowns
- Cascades updates to sessions

#### `CategorySyncService` (src/services/sync_service.py)
- Maintains consistency across categories table
- Handles category deletion with data migration

#### `CachedQueryService` (src/services/cached_queries.py)
- 372 lines
- 10 cached query methods
- Uses Streamlit's @st.cache_data (TTL: 30-60 seconds)
- Provides batch queries to avoid N+1 problem

#### `DropdownManager` (src/utils/dropdowns.py)
- Hierarchical dropdown rendering
- Cascading selection logic
- Type-to-add functionality

---

## 10. COMPREHENSIVE FINDINGS SUMMARY

### Strengths
✅ Dual-mode database (PostgreSQL/SQLite) - excellent flexibility
✅ Comprehensive schema with proper indexes
✅ Transactions and error handling for critical operations
✅ Google Drive sync implementation is production-ready
✅ Well-documented with multiple guides
✅ Cached queries to prevent N+1 issues
✅ Service classes for data consistency
✅ WAL mode for better concurrency
✅ Integrity checks and backups
✅ App state persistence for UX

### Critical Issues
❌ Multiple DatabaseStorage instances (concurrency risk)
❌ Cache invalidation not triggered on writes (stale data)
❌ Direct cursor access in some methods (consistency issue)
❌ No initial data on first run (poor onboarding)

### Warnings
⚠️ No foreign key constraints (referential integrity risk)
⚠️ No database versioning or migration system
⚠️ Text-based date fields (less efficient)
⚠️ Some transaction handling inconsistencies
⚠️ No cascade deletes for related records

### Opportunities
💡 Add database migration system (Alembic)
💡 Implement proper dependency injection
💡 Add database health check endpoint
💡 Automatic cache invalidation on writes
💡 Connection pooling for PostgreSQL
💡 Query performance monitoring
💡 Automated backup scheduling

---

## 11. RECOMMENDATIONS (Priority Order)

### Priority 1 (Critical - Fix Immediately)
1. Use singleton DatabaseStorage instance everywhere
2. Add cache invalidation after write operations
3. Use _get_cursor() consistently in all methods

### Priority 2 (High - Fix Soon)
4. Add foreign key constraints to schema
5. Bootstrap initial data on first run
6. Add database migration system
7. Add date validation for session_date field

### Priority 3 (Medium - Plan for Next)
8. Add database versioning
9. Add connection pooling for PostgreSQL
10. Implement automatic cache invalidation triggers
11. Add query performance monitoring

### Priority 4 (Low - Nice to Have)
12. Cascade delete for related records
13. Full-text search on notes/tags
14. Database backup scheduling
15. Query result pagination optimization

---

## Conclusion

The MG Smart Tracker database implementation is **well-designed at the schema level** with comprehensive CRUD operations and excellent Google Drive sync support. However, there are **critical runtime issues** with multiple database instances and missing cache invalidation that could cause data consistency problems.

**Immediate action recommended**: Consolidate to a single DatabaseStorage instance and implement cache invalidation on writes.

The database is **production-ready** for Google Drive sync but needs **architectural improvements** for optimal performance and reliability in Streamlit's dynamic rerun environment.

