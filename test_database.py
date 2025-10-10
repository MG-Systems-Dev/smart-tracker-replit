#!/usr/bin/env python3
"""
Database validation test script for Smart Tracker
Tests all database operations with both PostgreSQL (if available) and SQLite
"""

import os
import sys
import traceback
from datetime import datetime

# Add src to path
sys.path.append('src')

def test_database_operations():
    """Test all database operations"""
    
    print("=== Smart Tracker Database Validation Test ===")
    
    try:
        from database.operations import DatabaseStorage
        
        # Test 1: Database Initialization
        print("\n1. Testing Database Initialization...")
        db = DatabaseStorage()
        db_type = "PostgreSQL" if db.use_postgresql else "SQLite"
        print(f"   ✅ Database initialized successfully ({db_type})")
        
        # Test 2: Basic Session Operations
        print("\n2. Testing Session Operations...")
        
        # Add a test session
        test_session = {
            'session_date': '2025-01-01',
            'session_type': 'Learning',
            'category_name': 'Programming',
            'technology': 'Python',
            'work_item': 'Testing',
            'skill_topic': 'Unit Tests',
            'category_source': 'Manual',
            'difficulty': 'Medium',
            'status': 'Completed',
            'hours_spent': 2.5,
            'tags': 'testing,python',
            'notes': 'Test session for validation'
        }
        
        try:
            session_id = db.add_session(test_session)
            print(f"   ✅ Add session successful (ID: {session_id})")
        except Exception as e:
            print(f"   ❌ Add session failed: {e}")
        
        # Get all sessions
        try:
            sessions = db.get_all_sessions()
            print(f"   ✅ Get all sessions successful ({len(sessions)} sessions)")
        except Exception as e:
            print(f"   ❌ Get all sessions failed: {e}")
        
        # Test 3: Tech Stack Operations
        print("\n3. Testing Tech Stack Operations...")
        
        try:
            tech_stack = db.get_all_tech_stack()
            print(f"   ✅ Get tech stack successful ({len(tech_stack)} technologies)")
        except Exception as e:
            print(f"   ❌ Get tech stack failed: {e}")
        
        # Add a test technology
        try:
            tech_id = db.add_technology("Test Tech", "Testing", 10.0, "2025-01-01")
            print(f"   ✅ Add technology successful (ID: {tech_id})")
        except Exception as e:
            print(f"   ❌ Add technology failed: {e}")
        
        # Test 4: Analytics Operations
        print("\n4. Testing Analytics Operations...")
        
        try:
            total_sessions = db.get_total_sessions()
            print(f"   ✅ Get total sessions successful ({total_sessions} sessions)")
        except Exception as e:
            print(f"   ❌ Get total sessions failed: {e}")
            
        try:
            total_hours = db.get_total_hours()
            print(f"   ✅ Get total hours successful ({total_hours} hours)")
        except Exception as e:
            print(f"   ❌ Get total hours failed: {e}")
        
        print(f"\n🎉 Database validation completed for {db_type}")
        return True
        
    except Exception as e:
        print(f"\n💥 Critical error during database validation:")
        print(f"   Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_operations()
    sys.exit(0 if success else 1)