#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Migrates all data from local SQLite database to PostgreSQL (Neon, Supabase, etc.)

Usage:
    export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"
    python scripts/migrate_to_postgres.py
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def migrate_data():
    """Migrate data from SQLite to PostgreSQL."""

    print("=" * 70)
    print("MG SMART TRACKER - DATABASE MIGRATION")
    print("SQLite → PostgreSQL")
    print("=" * 70)
    print()

    # Check for DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print()
        print("Please set it first:")
        print('   export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"')
        print()
        sys.exit(1)

    # Check for psycopg2
    try:
        import psycopg2
        from psycopg2.extras import DictCursor
    except ImportError:
        print("❌ ERROR: psycopg2 not installed!")
        print()
        print("Install it with:")
        print("   pip install psycopg2-binary")
        print()
        sys.exit(1)

    # Paths
    sqlite_db_path = "data/smart_tracker.db"

    # Check if SQLite database exists
    if not os.path.exists(sqlite_db_path):
        print(f"❌ ERROR: SQLite database not found at: {sqlite_db_path}")
        print()
        print("Options:")
        print("  1. Start with fresh PostgreSQL database (no migration needed)")
        print("  2. Create SQLite database first by running the app locally")
        print()
        sys.exit(1)

    print(f"✅ Found SQLite database: {sqlite_db_path}")
    print(f"✅ Target PostgreSQL: {database_url.split('@')[1].split('/')[0]}...")
    print()

    # Connect to SQLite
    print("📂 Connecting to SQLite...")
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    print("🐘 Connecting to PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(database_url)
        pg_cursor = pg_conn.cursor(cursor_factory=DictCursor)
        print("✅ Connected successfully!")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

    print()
    print("-" * 70)
    print("MIGRATION PLAN")
    print("-" * 70)

    # Get table counts from SQLite
    tables_to_migrate = [
        'sessions',
        'tech_stack',
        'categories',
        'dropdowns',
        'work_items',
        'skills',
        'category_sources',
        'app_state'
    ]

    table_counts = {}
    for table in tables_to_migrate:
        try:
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = sqlite_cursor.fetchone()[0]
            table_counts[table] = count
            print(f"  • {table:20s} → {count:5d} rows")
        except sqlite3.OperationalError:
            table_counts[table] = 0
            print(f"  • {table:20s} → (table doesn't exist)")

    total_rows = sum(table_counts.values())
    print(f"\n  TOTAL: {total_rows} rows to migrate")
    print("-" * 70)
    print()

    if total_rows == 0:
        print("⚠️  No data to migrate. PostgreSQL will use empty tables.")
        print()
        response = input("Continue with empty migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)
    else:
        response = input("Proceed with migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)

    print()
    print("=" * 70)
    print("STARTING MIGRATION")
    print("=" * 70)
    print()

    # Initialize PostgreSQL database (creates tables)
    print("1️⃣  Initializing PostgreSQL tables...")
    from src.database.operations import DatabaseStorage

    # Force PostgreSQL mode
    os.environ['USE_POSTGRESQL'] = '1'
    db = DatabaseStorage()
    print("✅ Tables created successfully!")
    print()

    # Migrate data table by table
    migrated_counts = {}

    # Helper function to migrate a table
    def migrate_table(table_name, columns, primary_key=None):
        """Migrate a single table from SQLite to PostgreSQL."""
        print(f"2️⃣  Migrating {table_name}...")

        # Get data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()

        if len(rows) == 0:
            print(f"   ⚠️  No rows to migrate")
            migrated_counts[table_name] = 0
            return

        # Clear existing data in PostgreSQL (optional)
        pg_cursor.execute(f"DELETE FROM {table_name}")

        # Build INSERT query
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        # Insert data
        count = 0
        for row in rows:
            values = [row[col] for col in columns]
            try:
                pg_cursor.execute(insert_query, values)
                count += 1
            except Exception as e:
                print(f"   ⚠️  Error inserting row: {e}")
                print(f"   Row data: {dict(row)}")

        pg_conn.commit()
        migrated_counts[table_name] = count
        print(f"   ✅ Migrated {count} rows")

    # Migrate each table
    try:
        # Categories
        if table_counts.get('categories', 0) > 0:
            migrate_table('categories', ['category_name', 'is_custom', 'created_at'])

        # Tech Stack
        if table_counts.get('tech_stack', 0) > 0:
            migrate_table('tech_stack', ['name', 'category', 'goal_hours', 'start_date', 'notes', 'created_at'])

        # Dropdowns
        if table_counts.get('dropdowns', 0) > 0:
            migrate_table('dropdowns', ['dropdown_type', 'value', 'parent_value', 'created_at'])

        # Work Items
        if table_counts.get('work_items', 0) > 0:
            migrate_table('work_items', ['name', 'technology', 'created_at'])

        # Skills
        if table_counts.get('skills', 0) > 0:
            migrate_table('skills', ['name', 'work_item', 'created_at'])

        # Category Sources
        if table_counts.get('category_sources', 0) > 0:
            migrate_table('category_sources', ['name', 'created_at'])

        # Sessions (most important!)
        if table_counts.get('sessions', 0) > 0:
            migrate_table('sessions', [
                'session_date', 'session_type', 'category_name', 'technology',
                'work_item', 'skill_topic', 'category_source', 'difficulty',
                'status', 'hours_spent', 'tags', 'notes', 'created_at', 'updated_at'
            ])

        # App State
        if table_counts.get('app_state', 0) > 0:
            migrate_table('app_state', ['key', 'value', 'updated_at'])

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        pg_conn.rollback()
        sys.exit(1)

    print()
    print("=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)

    total_migrated = sum(migrated_counts.values())

    for table, count in migrated_counts.items():
        status = "✅" if count > 0 else "⚠️ "
        print(f"{status} {table:20s} → {count:5d} rows")

    print("-" * 70)
    print(f"   TOTAL MIGRATED: {total_migrated} rows")
    print("=" * 70)
    print()

    # Close connections
    sqlite_conn.close()
    pg_conn.close()

    print("🎉 Migration completed successfully!")
    print()
    print("Next steps:")
    print("  1. Verify migration: python scripts/verify_migration.py")
    print("  2. Test your app with PostgreSQL")
    print("  3. Deploy to Streamlit Cloud")
    print()

    # Create migration log
    log_file = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, 'w') as f:
        f.write(f"Migration completed: {datetime.now()}\n")
        f.write(f"Source: {sqlite_db_path}\n")
        f.write(f"Target: PostgreSQL\n")
        f.write(f"Total rows: {total_migrated}\n\n")
        for table, count in migrated_counts.items():
            f.write(f"{table}: {count} rows\n")

    print(f"📄 Migration log saved to: {log_file}")
    print()

if __name__ == "__main__":
    migrate_data()
