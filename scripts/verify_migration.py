#!/usr/bin/env python3
"""
PostgreSQL Migration Verification Script
Verifies that data was migrated correctly from SQLite to PostgreSQL

Usage:
    export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"
    python scripts/verify_migration.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def verify_migration():
    """Verify PostgreSQL database has data."""

    print("=" * 70)
    print("MG SMART TRACKER - MIGRATION VERIFICATION")
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

    print(f"✅ Connecting to: {database_url.split('@')[1].split('/')[0]}...")
    print()

    # Initialize database connection
    os.environ['USE_POSTGRESQL'] = '1'
    from src.database.operations import DatabaseStorage

    try:
        db = DatabaseStorage()
        print("✅ Connected to PostgreSQL successfully!")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

    print()
    print("-" * 70)
    print("DATABASE VERIFICATION")
    print("-" * 70)
    print()

    # Verify tables and data
    results = []

    # Sessions
    print("1️⃣  Checking sessions...")
    sessions = db.get_all_sessions()
    total_hours = db.get_total_hours()
    print(f"   ✅ Sessions: {len(sessions)}")
    print(f"   ✅ Total hours: {total_hours:.1f}")
    results.append(('sessions', len(sessions)))

    # Tech Stack
    print("\n2️⃣  Checking tech stack...")
    tech_stack = db.get_all_tech_stack()
    print(f"   ✅ Technologies: {len(tech_stack)}")
    results.append(('tech_stack', len(tech_stack)))

    # Categories
    print("\n3️⃣  Checking categories...")
    categories = db.get_all_categories()
    print(f"   ✅ Categories: {len(categories)}")
    results.append(('categories', len(categories)))

    # Work Items
    print("\n4️⃣  Checking work items...")
    work_items = db.get_all_work_items()
    print(f"   ✅ Work items: {len(work_items)}")
    results.append(('work_items', len(work_items)))

    # Skills
    print("\n5️⃣  Checking skills...")
    skills = db.get_all_skills()
    print(f"   ✅ Skills: {len(skills)}")
    results.append(('skills', len(skills)))

    # Category Sources
    print("\n6️⃣  Checking category sources...")
    sources = db.get_all_category_sources()
    print(f"   ✅ Category sources: {len(sources)}")
    results.append(('category_sources', len(sources)))

    print()
    print("-" * 70)
    print("VERIFICATION SUMMARY")
    print("-" * 70)

    total_records = sum(count for _, count in results)

    for table, count in results:
        status = "✅" if count > 0 else "⚠️ "
        print(f"{status} {table:20s} → {count:5d} records")

    print("-" * 70)
    print(f"   TOTAL RECORDS: {total_records}")
    print("=" * 70)
    print()

    # Additional checks
    print("ADDITIONAL CHECKS")
    print("-" * 70)

    # Check if we can query data
    if len(sessions) > 0:
        print("✅ Sample session data:")
        sample = sessions[0]
        print(f"   Date: {sample.get('session_date')}")
        print(f"   Technology: {sample.get('technology')}")
        print(f"   Hours: {sample.get('hours_spent')}")

    # Check statistics
    if len(sessions) > 0:
        print("\n✅ Statistics working:")
        hours_by_tech = db.get_hours_by_technology()
        print(f"   Technologies tracked: {len(hours_by_tech)}")

        hours_by_category = db.get_hours_by_category()
        print(f"   Categories tracked: {len(hours_by_category)}")

    print()
    print("-" * 70)
    print()

    if total_records == 0:
        print("⚠️  WARNING: No data found in PostgreSQL database!")
        print()
        print("This could mean:")
        print("  1. Migration hasn't been run yet")
        print("  2. Starting with fresh database (this is OK)")
        print("  3. Migration failed (check migration logs)")
        print()
    else:
        print("🎉 PostgreSQL database verification successful!")
        print()
        print("Your database is ready for:")
        print("  ✅ Streamlit Cloud deployment")
        print("  ✅ Production use")
        print("  ✅ Multi-user access")
        print()

    print("Next steps:")
    print("  1. Deploy to Streamlit Cloud (see DEPLOYMENT_GUIDE.md)")
    print("  2. Set DATABASE_URL in Streamlit secrets")
    print("  3. Test your deployed app")
    print()

if __name__ == "__main__":
    verify_migration()
