"""
Database storage layer for Smart Tracker v2.0.
Provides persistent storage with structured tables and relationships.
Supports both PostgreSQL (production/Replit) and SQLite (local development).
"""

import psycopg2
import psycopg2.extras
import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging


class DatabaseStorage:
    """Database storage manager for Smart Tracker - supports PostgreSQL and SQLite."""

    def __init__(self):
        """Initialize database connection - PostgreSQL for production, SQLite for local."""
        self.database_url = os.environ.get("DATABASE_URL")
        self.use_postgresql = bool(self.database_url)

        if self.use_postgresql:
            # PostgreSQL mode (Replit/production)
            self.conn = None
        else:
            # SQLite mode (local development)
            self.db_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "data", "smart_tracker.db"
            )
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = None

        self._initialize_database()

    def _get_connection(self):
        """Get database connection with appropriate cursor type."""
        if self.use_postgresql:
            try:
                # Test if connection is still valid
                if self.conn is not None:
                    self.conn.cursor().execute('SELECT 1')
                    return self.conn
            except (psycopg2.OperationalError, psycopg2.InterfaceError, AttributeError):
                pass
            # Create new connection
            self.conn = psycopg2.connect(self.database_url)
            return self.conn
        else:
            if self.conn is None:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row  # Enable dict-like access
                # Enable WAL mode for better concurrency
                self.conn.execute("PRAGMA journal_mode=WAL;")
                self.conn.execute("PRAGMA busy_timeout=5000;")
            return self.conn

    def _get_cursor(self, conn):
        """Get appropriate cursor for the database type."""
        if self.use_postgresql:
            return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            return conn.cursor()

    def _get_primary_key_sql(self):
        """Get the correct primary key SQL for the database type."""
        if self.use_postgresql:
            return "SERIAL PRIMARY KEY"
        else:
            return "INTEGER PRIMARY KEY AUTOINCREMENT"

    def _get_timestamp_sql(self):
        """Get the correct timestamp SQL for the database type."""
        if self.use_postgresql:
            return "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        else:
            return "DATETIME DEFAULT CURRENT_TIMESTAMP"
    
    def execute_query_fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return all results as list of dicts."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        
        # Replace %s with appropriate placeholder for the database type
        if placeholder != "%s":
            formatted_query = query.replace("%s", placeholder)
        else:
            formatted_query = query
            
        cursor.execute(formatted_query, params)
        results = cursor.fetchall()
        return [dict(row) for row in results]
    
    def execute_query_fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute a query and return one result as dict or None."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        
        # Replace %s with appropriate placeholder for the database type
        if placeholder != "%s":
            formatted_query = query.replace("%s", placeholder)
        else:
            formatted_query = query
            
        cursor.execute(formatted_query, params)
        result = cursor.fetchone()
        return dict(result) if result else None

    def _initialize_database(self):
        """Create database tables if they don't exist."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)

        primary_key = self._get_primary_key_sql()
        timestamp = self._get_timestamp_sql()

        # Sessions table - main learning session data
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id {primary_key},
                session_date TEXT NOT NULL,
                session_type TEXT NOT NULL,
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
                created_at {timestamp},
                updated_at {timestamp}
            )
        """)

        # Tech stack table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS tech_stack (
                id {primary_key},
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                goal_hours REAL DEFAULT 50,
                date_added TEXT NOT NULL,
                created_at {timestamp}
            )
        """)

        # Dropdowns table - hierarchical dropdown values
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS dropdowns (
                id {primary_key},
                field_name TEXT NOT NULL,
                field_value TEXT NOT NULL,
                parent_field TEXT,
                parent_value TEXT,
                created_at {timestamp},
                UNIQUE(field_name, field_value, parent_field, parent_value)
            )
        """)

        # Categories table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS categories (
                id {primary_key},
                category_name TEXT UNIQUE NOT NULL,
                is_custom INTEGER DEFAULT 0,
                date_added TEXT NOT NULL,
                created_at {timestamp}
            )
        """)

        # Work items table - manually defined work items linked to technologies
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS work_items (
                id {primary_key},
                name TEXT NOT NULL,
                technology TEXT NOT NULL,
                created_at {timestamp},
                UNIQUE(name, technology)
            )
        """)

        # Skills table - manually defined skills linked to work items
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS skills (
                id {primary_key},
                name TEXT NOT NULL,
                work_item TEXT NOT NULL,
                created_at {timestamp},
                UNIQUE(name, work_item)
            )
        """)

        # Category Sources table - learning platforms/sources
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS category_sources (
                id {primary_key},
                name TEXT UNIQUE NOT NULL,
                created_at {timestamp}
            )
        """)

        # App state table - persist UI state across restarts
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at {timestamp}
            )
        """)

        # Create indexes for better query performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_tech ON sessions(technology)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_category ON sessions(category_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_dropdowns_field ON dropdowns(field_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_dropdowns_parent ON dropdowns(parent_field, parent_value)"
        )

        conn.commit()
        db_type = "PostgreSQL" if self.use_postgresql else "SQLite"
        logging.info(f"{db_type} database initialized successfully")

    def _get_placeholder(self):
        """Get the correct parameter placeholder for the database type."""
        if self.use_postgresql:
            return "%s"
        else:
            return "?"

    # ==================== SESSION OPERATIONS ====================

    def add_session(self, session_data: Dict[str, Any]) -> int:
        """Add a new learning session and return its ID."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()

        if self.use_postgresql:
            cursor.execute(
                f"""
                INSERT INTO sessions (
                    session_date, session_type, category_name, technology,
                    work_item, skill_topic, category_source, difficulty,
                    status, hours_spent, tags, notes
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                RETURNING session_id
            """,
                (
                    session_data.get("session_date"),
                    session_data.get("session_type"),
                    session_data.get("category_name"),
                    session_data.get("technology"),
                    session_data.get("work_item"),
                    session_data.get("skill_topic"),
                    session_data.get("category_source"),
                    session_data.get("difficulty"),
                    session_data.get("status"),
                    session_data.get("hours_spent"),
                    session_data.get("tags"),
                    session_data.get("notes"),
                ),
            )
            result = cursor.fetchone()
            session_id = dict(result)["session_id"] if result else 0
        else:
            cursor.execute(
                f"""
                INSERT INTO sessions (
                    session_date, session_type, category_name, technology,
                    work_item, skill_topic, category_source, difficulty,
                    status, hours_spent, tags, notes
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
                (
                    session_data.get("session_date"),
                    session_data.get("session_type"),
                    session_data.get("category_name"),
                    session_data.get("technology"),
                    session_data.get("work_item"),
                    session_data.get("skill_topic"),
                    session_data.get("category_source"),
                    session_data.get("difficulty"),
                    session_data.get("status"),
                    session_data.get("hours_spent"),
                    session_data.get("tags"),
                    session_data.get("notes"),
                ),
            )
            session_id = cursor.lastrowid

        conn.commit()
        if session_id is None:
            session_id = 0
        logging.info(
            f"Added session ID {session_id}: {session_data.get('technology')} - {session_data.get('skill_topic')}"
        )
        return int(session_id)

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Retrieve all learning sessions."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("SELECT * FROM sessions ORDER BY session_date DESC")

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_session_by_id(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific session by ID."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(
            f"SELECT * FROM sessions WHERE session_id = {placeholder}", (session_id,)
        )

        row = cursor.fetchone()
        return dict(row) if row else None

    def update_session(self, session_id: int, session_data: Dict[str, Any]) -> bool:
        """Update an existing session."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()

        cursor.execute(
            f"""
            UPDATE sessions SET
                session_date = {placeholder},
                session_type = {placeholder},
                category_name = {placeholder},
                technology = {placeholder},
                work_item = {placeholder},
                skill_topic = {placeholder},
                category_source = {placeholder},
                difficulty = {placeholder},
                status = {placeholder},
                hours_spent = {placeholder},
                tags = {placeholder},
                notes = {placeholder},
                updated_at = CURRENT_TIMESTAMP
            WHERE session_id = {placeholder}
        """,
            (
                session_data.get("session_date"),
                session_data.get("session_type"),
                session_data.get("category_name"),
                session_data.get("technology"),
                session_data.get("work_item"),
                session_data.get("skill_topic"),
                session_data.get("category_source"),
                session_data.get("difficulty"),
                session_data.get("status"),
                session_data.get("hours_spent"),
                session_data.get("tags"),
                session_data.get("notes"),
                session_id,
            ),
        )

        conn.commit()
        logging.info(f"Updated session ID {session_id}")
        return cursor.rowcount > 0

    def delete_session(self, session_id: int) -> bool:
        """Delete a session by ID."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(f"DELETE FROM sessions WHERE session_id = {placeholder}", (session_id,))
        conn.commit()
        logging.info(f"Deleted session ID {session_id}")
        return cursor.rowcount > 0

    # ==================== ANALYTICS & METRICS ====================

    def get_total_sessions(self) -> int:
        """Get total number of sessions."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("SELECT COUNT(*) FROM sessions")
        row = cursor.fetchone()
        if row:
            return row[0]
        return 0

    def get_total_hours(self) -> float:
        """Get total hours spent across all sessions."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("SELECT COALESCE(SUM(hours_spent), 0) FROM sessions")
        row = cursor.fetchone()
        if row:
            return row[0]
        return 0.0

    def get_total_technologies(self) -> int:
        """Get total number of unique technologies."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("SELECT COUNT(DISTINCT technology) FROM sessions")
        row = cursor.fetchone()
        if row:
            return row[0]
        return 0

    def get_overall_progress(self) -> float:
        """Calculate overall progress percentage based on total hours vs total goals."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)

        cursor.execute("SELECT COALESCE(SUM(goal_hours), 0) FROM tech_stack")
        row = cursor.fetchone()
        if row:
            total_goal = row[0]
        else:
            total_goal = 0

        if total_goal == 0:
            return 0.0

        total_hours = self.get_total_hours()
        return round((total_hours / total_goal) * 100, 1)

    # ==================== TECH STACK OPERATIONS ====================

    def add_technology(
        self, name: str, category: str, goal_hours: float, date_added: str
    ) -> int:
        """Add a new technology to the tech stack."""
        conn = self._get_connection()
        try:
            cursor = self._get_cursor(conn)
            placeholder = self._get_placeholder()
            
            if self.use_postgresql:
                cursor.execute(
                    f"""
                    INSERT INTO tech_stack (name, category, goal_hours, date_added)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                    RETURNING id
                """,
                    (name, category, goal_hours, date_added),
                )
                result = cursor.fetchone()
                tech_id = dict(result)["id"] if result else 0
            else:
                cursor.execute(
                    f"""
                    INSERT INTO tech_stack (name, category, goal_hours, date_added)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                    (name, category, goal_hours, date_added),
                )
                tech_id = cursor.lastrowid or 0

            conn.commit()
            logging.info(f"Added technology: {name} (ID: {tech_id})")
            return int(tech_id)
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            conn.rollback()
            logging.warning(f"Technology {name} already exists")
            return -1

    def get_all_tech_stack(self) -> List[Dict[str, Any]]:
        """Retrieve all technologies in the tech stack."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("SELECT * FROM tech_stack ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def get_technology_by_id(self, tech_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific technology by ID."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(f"SELECT * FROM tech_stack WHERE id = {placeholder}", (tech_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_tech_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific technology by name."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(f"SELECT * FROM tech_stack WHERE name = {placeholder}", (name,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def update_technology(
        self, tech_id: int, name: str, category: str, goal_hours: float
    ) -> bool:
        """Update an existing technology."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()

        cursor.execute(
            f"""
            UPDATE tech_stack 
            SET name = {placeholder}, category = {placeholder}, goal_hours = {placeholder}
            WHERE id = {placeholder}
        """,
            (name, category, goal_hours, tech_id),
        )

        conn.commit()
        logging.info(f"Updated technology ID {tech_id}: {name}")
        return cursor.rowcount > 0

    def delete_technology(self, tech_id: int) -> bool:
        """Delete a technology from the tech stack."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(f"DELETE FROM tech_stack WHERE id = {placeholder}", (tech_id,))
        conn.commit()
        logging.info(f"Deleted technology ID {tech_id}")
        return cursor.rowcount > 0

    # ==================== CATEGORY OPERATIONS ====================

    def add_category(self, category_name: str, is_custom: bool = True) -> bool:
        """Add a new category."""
        conn = self._get_connection()
        try:
            cursor = self._get_cursor(conn)
            placeholder = self._get_placeholder()
            date_added = datetime.now().strftime("%Y-%m-%d")

            cursor.execute(
                f"""
                INSERT INTO categories (category_name, is_custom, date_added)
                VALUES ({placeholder}, {placeholder}, {placeholder})
            """,
                (category_name, 1 if is_custom else 0, date_added),
            )

            conn.commit()
            logging.info(f"Added category: {category_name}")
            return True
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            conn.rollback()
            logging.warning(f"Category {category_name} already exists")
            return False

    def get_all_categories(self) -> List[str]:
        """Get all category names."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("SELECT category_name FROM categories ORDER BY category_name")
        return [row[0] for row in cursor.fetchall()]

    def get_custom_categories(self) -> List[str]:
        """Get custom (user-added) categories only."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute(
            "SELECT category_name FROM categories WHERE is_custom = 1 ORDER BY category_name"
        )
        return [row[0] for row in cursor.fetchall()]

    def delete_category(self, category_name: str) -> bool:
        """Delete a category."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(
            f"DELETE FROM categories WHERE category_name = {placeholder}", (category_name,)
        )
        conn.commit()
        logging.info(f"Deleted category: {category_name}")
        return cursor.rowcount > 0

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """Rename a category."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(
            f"""
            UPDATE categories 
            SET category_name = {placeholder}
            WHERE category_name = {placeholder}
        """,
            (new_name, old_name),
        )
        conn.commit()
        logging.info(f"Renamed category: {old_name} -> {new_name}")
        return cursor.rowcount > 0

    def category_exists(self, category_name: str) -> bool:
        """Check if a category exists."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(
            f"SELECT 1 FROM categories WHERE category_name = {placeholder}", (category_name,)
        )
        return cursor.fetchone() is not None
    
    def count_sessions_by_category(self, category_name: str) -> int:
        """Count sessions using a specific category."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(
            f"SELECT COUNT(*) FROM sessions WHERE category_name = {placeholder}",
            (category_name,)
        )
        row = cursor.fetchone()
        return row[0] if row else 0
    
    def update_tech_stack_category(self, old_name: str, new_name: str) -> bool:
        """Update category name in tech_stack table."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(
            f"UPDATE tech_stack SET category = {placeholder} WHERE category = {placeholder}",
            (new_name, old_name)
        )
        conn.commit()
        logging.info(f"Updated tech_stack category: {old_name} -> {new_name}")
        return cursor.rowcount > 0

    # ==================== DROPDOWN OPERATIONS ====================

    def add_dropdown_value(
        self,
        field_name: str,
        field_value: str,
        parent_field: Optional[str] = None,
        parent_value: Optional[str] = None,
    ) -> bool:
        """Add a new dropdown value with optional parent relationship."""
        conn = self._get_connection()
        try:
            cursor = self._get_cursor(conn)
            placeholder = self._get_placeholder()

            cursor.execute(
                f"""
                INSERT INTO dropdowns (field_name, field_value, parent_field, parent_value)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
                (field_name, field_value, parent_field, parent_value),
            )

            conn.commit()
            logging.info(f"Added dropdown: {field_name} = {field_value}")
            return True
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            conn.rollback()
            return False

    def get_dropdown_values(
        self, field_name: str, parent_value: Optional[str] = None
    ) -> List[str]:
        """Get dropdown values for a specific field, optionally filtered by parent."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()

        if parent_value:
            cursor.execute(
                f"""
                SELECT DISTINCT field_value FROM dropdowns
                WHERE field_name = {placeholder} AND parent_value = {placeholder}
                ORDER BY field_value
            """,
                (field_name, parent_value),
            )
        else:
            cursor.execute(
                f"""
                SELECT DISTINCT field_value FROM dropdowns
                WHERE field_name = {placeholder}
                ORDER BY field_value
            """,
                (field_name,),
            )

        return [row[0] for row in cursor.fetchall()]

    def delete_dropdown_value(self, field_name: str, field_value: str) -> bool:
        """Delete a specific dropdown value."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        placeholder = self._get_placeholder()
        cursor.execute(
            f"""
            DELETE FROM dropdowns 
            WHERE field_name = {placeholder} AND field_value = {placeholder}
        """,
            (field_name, field_value),
        )
        conn.commit()
        return cursor.rowcount > 0

    # ==================== STATISTICS & BREAKDOWNS ====================

    def get_hours_by_technology(self) -> Dict[str, float]:
        """Get total hours spent per technology."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("""
            SELECT technology, SUM(hours_spent) as total_hours
            FROM sessions
            GROUP BY technology
            ORDER BY total_hours DESC
        """)

        breakdown = {}
        for row in cursor.fetchall():
            breakdown[row[0]] = row[1]

        return breakdown

    def get_hours_by_category(self) -> Dict[str, float]:
        """Get total hours spent per category."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("""
            SELECT category_name, SUM(hours_spent) as total_hours
            FROM sessions
            GROUP BY category_name
            ORDER BY total_hours DESC
        """)

        breakdown = {}
        for row in cursor.fetchall():
            breakdown[row[0]] = row[1]

        return breakdown

    def get_hours_by_work_item(self) -> Dict[str, float]:
        """Get total hours spent per work item."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("""
            SELECT work_item, SUM(hours_spent) as total_hours
            FROM sessions
            WHERE work_item IS NOT NULL AND work_item != ''
            GROUP BY work_item
            ORDER BY total_hours DESC
        """)

        breakdown = {}
        for row in cursor.fetchall():
            breakdown[row[0]] = row[1]

        return breakdown

    # ==================== DIRECT CASCADING DROPDOWN QUERIES ====================

    def get_technologies_by_category(self, category: str) -> List[str]:
        """Get all technologies for a specific category from tech_stack table."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute(
            f"""
            SELECT name FROM tech_stack
            WHERE category = {placeholder}
            ORDER BY name
        """,
            (category,),
        )

        return [row[0] for row in cursor.fetchall()]

    def get_work_items_by_technology(self, technology: str) -> List[str]:
        """Get work items for a technology - merges manual + auto-populated from sessions."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        cursor = self._get_cursor(conn)

        # Get manually defined work items
        cursor.execute(
            f"""
            SELECT name FROM work_items
            WHERE technology = {placeholder}
            ORDER BY name
        """,
            (technology,),
        )
        manual_items = [row[0] for row in cursor.fetchall()]

        # Get auto-populated from sessions
        cursor.execute(
            f"""
            SELECT DISTINCT work_item FROM sessions
            WHERE technology = {placeholder} AND work_item IS NOT NULL AND work_item != ''
            ORDER BY work_item
        """,
            (technology,),
        )
        auto_items = [row[0] for row in cursor.fetchall()]

        # Merge and deduplicate
        combined = list(set(manual_items + auto_items))
        return sorted(combined)

    def get_skills_by_work_item(self, work_item: str) -> List[str]:
        """Get skills for a work item - merges manual + auto-populated from sessions."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        cursor = self._get_cursor(conn)

        # Get manually defined skills
        cursor.execute(
            f"""
            SELECT name FROM skills
            WHERE work_item = {placeholder}
            ORDER BY name
        """,
            (work_item,),
        )
        manual_skills = [row[0] for row in cursor.fetchall()]

        # Get auto-populated from sessions
        cursor.execute(
            f"""
            SELECT DISTINCT skill_topic FROM sessions
            WHERE work_item = {placeholder} AND skill_topic IS NOT NULL AND skill_topic != ''
            ORDER BY skill_topic
        """,
            (work_item,),
        )
        auto_skills = [row[0] for row in cursor.fetchall()]

        # Merge and deduplicate
        combined = list(set(manual_skills + auto_skills))
        return sorted(combined)

    # ==================== WORK ITEMS OPERATIONS ====================

    def add_work_item(self, name: str, technology: str) -> bool:
        """Add a manually defined work item linked to a technology."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        try:
            cursor = self._get_cursor(conn)
            cursor.execute(
                f"""
                INSERT INTO work_items (name, technology)
                VALUES ({placeholder}, {placeholder})
            """,
                (name, technology),
            )
            conn.commit()
            logging.info(f"Added work item: {name} → {technology}")
            return True
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            conn.rollback()
            logging.warning(f"Work item {name} already exists for {technology}")
            return False

    def delete_work_item(self, name: str, technology: str) -> bool:
        """Delete a manually defined work item."""
        placeholder = self._get_placeholder()
        try:
            conn = self._get_connection()
            cursor = self._get_cursor(conn)
            cursor.execute(
                f"""
                DELETE FROM work_items
                WHERE name = {placeholder} AND technology = {placeholder}
            """,
                (name, technology),
            )
            conn.commit()
            logging.info(f"Deleted work item: {name} → {technology}")
            return True
        except Exception as e:
            logging.error(f"Error deleting work item: {e}")
            return False

    def get_all_work_items(self) -> List[Dict[str, str]]:
        """Get all manually defined work items with their technologies."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, technology FROM work_items
            ORDER BY technology, name
        """)

        return [{"name": row[0], "technology": row[1]} for row in cursor.fetchall()]

    # ==================== SKILLS OPERATIONS ====================

    def add_skill(self, name: str, work_item: str) -> bool:
        """Add a manually defined skill linked to a work item."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        try:
            cursor = self._get_cursor(conn)
            cursor.execute(
                f"""
                INSERT INTO skills (name, work_item)
                VALUES ({placeholder}, {placeholder})
            """,
                (name, work_item),
            )
            conn.commit()
            logging.info(f"Added skill: {name} → {work_item}")
            return True
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            conn.rollback()
            logging.warning(f"Skill {name} already exists for {work_item}")
            return False

    def delete_skill(self, name: str, work_item: str) -> bool:
        """Delete a manually defined skill."""
        placeholder = self._get_placeholder()
        try:
            conn = self._get_connection()
            cursor = self._get_cursor(conn)
            cursor.execute(
                f"""
                DELETE FROM skills
                WHERE name = {placeholder} AND work_item = {placeholder}
            """,
                (name, work_item),
            )
            conn.commit()
            logging.info(f"Deleted skill: {name} → {work_item}")
            return True
        except Exception as e:
            logging.error(f"Error deleting skill: {e}")
            return False

    def get_all_skills(self) -> List[Dict[str, str]]:
        """Get all manually defined skills with their work items."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, work_item FROM skills
            ORDER BY work_item, name
        """)

        return [{"name": row[0], "work_item": row[1]} for row in cursor.fetchall()]

    # ==================== CATEGORY SOURCES OPERATIONS ====================

    def add_category_source(self, name: str) -> bool:
        """Add a new category source (learning platform)."""
        placeholder = self._get_placeholder()
        try:
            conn = self._get_connection()
            cursor = self._get_cursor(conn)
            cursor.execute(
                f"""
                INSERT INTO category_sources (name)
                VALUES ({placeholder})
            """,
                (name,),
            )
            conn.commit()
            logging.info(f"Added category source: {name}")
            return True
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            conn.rollback()
            logging.warning(f"Category source {name} already exists")
            return False

    def delete_category_source(self, name: str) -> bool:
        """Delete a category source."""
        placeholder = self._get_placeholder()
        try:
            conn = self._get_connection()
            cursor = self._get_cursor(conn)
            cursor.execute(
                f"""
                DELETE FROM category_sources
                WHERE name = {placeholder}
            """,
                (name,),
            )
            conn.commit()
            logging.info(f"Deleted category source: {name}")
            return True
        except Exception as e:
            logging.error(f"Error deleting category source: {e}")
            return False

    def get_all_category_sources(self) -> List[str]:
        """Get all category sources."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM category_sources
            ORDER BY name
        """)

        return [row[0] for row in cursor.fetchall()]

    # ==================== APP STATE OPERATIONS ====================

    def save_app_state(self, key: str, value: str) -> bool:
        """Save app state for persistence across restarts."""
        placeholder = self._get_placeholder()
        try:
            conn = self._get_connection()
            cursor = self._get_cursor(conn)
            
            if self.use_postgresql:
                cursor.execute(
                    f"""
                    INSERT INTO app_state (key, value)
                    VALUES ({placeholder}, {placeholder})
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """,
                    (key, value),
                )
            else:
                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO app_state (key, value)
                    VALUES ({placeholder}, {placeholder})
                """,
                    (key, value),
                )
            
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error saving app state: {e}")
            return False

    def get_app_state(self, key: str, default: str = None) -> Optional[str]:
        """Get app state value by key."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT value FROM app_state WHERE key = {placeholder}",
            (key,),
        )
        
        row = cursor.fetchone()
        return row[0] if row else default

    # ==================== SESSION TYPE OPERATIONS ====================

    def get_session_type_breakdown(self) -> Dict[str, float]:
        """Get total hours spent per session type."""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute("""
            SELECT session_type, SUM(hours_spent) as total_hours
            FROM sessions
            GROUP BY session_type
            ORDER BY total_hours DESC
        """)

        breakdown = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            breakdown[row_dict['session_type']] = row_dict['total_hours']

        return breakdown

    # ==================== SYNC SERVICE SUPPORT METHODS ====================

    def count_sessions_by_technology(self, technology: str) -> int:
        """Count sessions for a specific technology."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute(
            f"SELECT COUNT(*) FROM sessions WHERE technology = {placeholder}", (technology,)
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        return 0

    def update_sessions_technology(self, old_name: str, new_name: str) -> bool:
        """Update technology name in all sessions."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute(
            f"""
            UPDATE sessions
            SET technology = {placeholder}
            WHERE technology = {placeholder}
        """,
            (new_name, old_name),
        )
        conn.commit()
        return cursor.rowcount > 0

    def update_sessions_category(self, old_name: str, new_name: str) -> bool:
        """Update category name in all sessions."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        cursor.execute(
            f"""
            UPDATE sessions
            SET category_name = {placeholder}
            WHERE category_name = {placeholder}
        """,
            (new_name, old_name),
        )
        conn.commit()
        return cursor.rowcount > 0

    def merge_categories(self, source: str, target: str) -> bool:
        """Merge source category into target category."""
        placeholder = self._get_placeholder()
        conn = self._get_connection()
        cursor = self._get_cursor(conn)

        # Update all sessions
        cursor.execute(
            f"""
            UPDATE sessions
            SET category_name = {placeholder}
            WHERE category_name = {placeholder}
        """,
            (target, source),
        )

        # Update all technologies
        cursor.execute(
            f"""
            UPDATE tech_stack
            SET category = {placeholder}
            WHERE category = {placeholder}
        """,
            (target, source),
        )

        # Delete source category
        cursor.execute(f"DELETE FROM categories WHERE category_name = {placeholder}", (source,))

        conn.commit()
        logging.info(f"Merged category: {source} -> {target}")
        return True

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")
