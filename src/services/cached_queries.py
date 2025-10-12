"""
Cached Query Service - Eliminates N+1 queries with batch operations and caching.
Uses Streamlit's @st.cache_data decorator for performance optimization.
"""

import streamlit as st
from typing import Dict, List, Any
from src.database.operations import DatabaseStorage
import logging

class CachedQueryService:
    """Provides cached and batched database queries."""
    
    def __init__(self, db: DatabaseStorage):
        self.db = db
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_tech_stack_with_metrics(_db: DatabaseStorage) -> List[Dict[str, Any]]:
        """
        Get tech stack with logged hours in ONE batch query.
        Eliminates N+1 query pattern.
        """
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        
        # Single JOIN query instead of N individual queries
        cursor.execute('''
            SELECT 
                ts.id,
                ts.name,
                ts.category,
                ts.goal_hours,
                ts.date_added,
                COALESCE(SUM(s.hours_spent), 0) as logged_hours,
                COUNT(s.session_id) as session_count
            FROM tech_stack ts
            LEFT JOIN sessions s ON ts.name = s.technology
            GROUP BY ts.id, ts.name, ts.category, ts.goal_hours, ts.date_added
            ORDER BY ts.category, ts.name
        ''')
        
        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            results.append({
                'id': row_dict['id'],
                'name': row_dict['name'],
                'category': row_dict['category'],
                'goal_hours': row_dict['goal_hours'],
                'date_added': row_dict['date_added'],
                'logged_hours': row_dict['logged_hours'],
                'session_count': row_dict['session_count'],
                'progress_pct': (row_dict['logged_hours'] / row_dict['goal_hours'] * 100) if row_dict['goal_hours'] > 0 else 0
            })
        
        logging.info(f"CachedQueryService: Fetched {len(results)} tech stack entries with metrics (cached)")
        return results
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_all_dropdown_data(_db: DatabaseStorage) -> Dict[str, List[str]]:
        """Get all dropdown data at once (cached)."""
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        
        cursor.execute('''
            SELECT field_name, field_value 
            FROM dropdowns 
            ORDER BY field_name, field_value
        ''')
        
        all_data = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            field_name = row_dict['field_name']
            field_value = row_dict['field_value']
            
            if field_name not in all_data:
                all_data[field_name] = []
            
            if field_value not in all_data[field_name]:
                all_data[field_name].append(field_value)
        
        return all_data
    
    @staticmethod
    @st.cache_data(ttl=30, show_spinner=False)
    def get_dashboard_metrics(_db: DatabaseStorage) -> Dict[str, Any]:
        """Get all dashboard metrics in one batch query."""
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        
        # Get aggregated stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT session_id) as total_sessions,
                SUM(hours_spent) as total_hours,
                COUNT(DISTINCT technology) as tech_count,
                COUNT(DISTINCT category_name) as category_count
            FROM sessions
        ''')
        
        row = cursor.fetchone()
        row_dict = dict(row)
        
        return {
            'total_sessions': row_dict['total_sessions'] or 0,
            'total_hours': row_dict['total_hours'] or 0.0,
            'tech_count': row_dict['tech_count'] or 0,
            'category_count': row_dict['category_count'] or 0
        }
    
    @staticmethod
    def invalidate_cache():
        """Clear all cached data (call after database writes)."""
        st.cache_data.clear()
        logging.info("CachedQueryService: Cache invalidated")
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_sessions_with_details(_db: DatabaseStorage, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get sessions with pagination (cached)."""
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        placeholder = _db._get_placeholder()
        
        cursor.execute(f'''
            SELECT * FROM sessions 
            ORDER BY session_date DESC, created_at DESC
            LIMIT {placeholder} OFFSET {placeholder}
        ''', (limit, offset))
        
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_technology_session_counts(_db: DatabaseStorage) -> Dict[str, int]:
        """Get session counts by technology (for delete safety checks)."""
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        
        cursor.execute('''
            SELECT technology, COUNT(*) as count
            FROM sessions
            GROUP BY technology
        ''')
        
        return {dict(row)['technology']: dict(row)['count'] for row in cursor.fetchall()}
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_category_usage_stats(_db: DatabaseStorage) -> Dict[str, Dict[str, int]]:
        """Get usage statistics for categories."""
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        
        # Get tech count and session count per category
        cursor.execute('''
            SELECT 
                category,
                COUNT(*) as tech_count
            FROM tech_stack
            GROUP BY category
        ''')
        
        tech_counts = {dict(row)['category']: dict(row)['tech_count'] for row in cursor.fetchall()}
        
        cursor.execute('''
            SELECT 
                category_name,
                COUNT(*) as session_count
            FROM sessions
            GROUP BY category_name
        ''')
        
        session_counts = {dict(row)['category_name']: dict(row)['session_count'] for row in cursor.fetchall()}
        
        # Combine results
        all_categories = set(tech_counts.keys()) | set(session_counts.keys())
        
        return {
            cat: {
                'tech_count': tech_counts.get(cat, 0),
                'session_count': session_counts.get(cat, 0)
            }
            for cat in all_categories
        }
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_category_hours_aggregated(_db: DatabaseStorage) -> Dict[str, float]:
        """Get hours by category using true aggregation (no row limit)."""
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        
        cursor.execute('''
            SELECT 
                category_name,
                SUM(hours_spent) as total_hours
            FROM sessions
            GROUP BY category_name
        ''')
        
        return {dict(row)['category_name']: dict(row)['total_hours'] for row in cursor.fetchall()}
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_category_analytics(_db: DatabaseStorage) -> List[Dict[str, Any]]:
        """Get category analytics with technology breakdown."""
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        
        # Get category totals with technology breakdown
        cursor.execute('''
            SELECT 
                s.category_name,
                s.technology,
                SUM(s.hours_spent) as hours,
                COUNT(s.session_id) as sessions
            FROM sessions s
            WHERE s.category_name != ''
            GROUP BY s.category_name, s.technology
            ORDER BY s.category_name, hours DESC
        ''')
        
        # Organize by category
        category_data = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            cat_name = row_dict['category_name']
            tech_name = row_dict['technology']
            hours = row_dict['hours']
            sessions = row_dict['sessions']
            
            if cat_name not in category_data:
                category_data[cat_name] = {
                    'category': cat_name,
                    'total_hours': 0,
                    'total_sessions': 0,
                    'technologies': []
                }
            
            category_data[cat_name]['total_hours'] += hours
            category_data[cat_name]['total_sessions'] += sessions
            category_data[cat_name]['technologies'].append({
                'name': tech_name,
                'hours': hours,
                'sessions': sessions
            })
        
        return list(category_data.values())
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_technology_analytics(_db: DatabaseStorage) -> List[Dict[str, Any]]:
        """Get technology analytics with work item breakdown."""
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        
        # Get technology totals with work item breakdown
        cursor.execute('''
            SELECT 
                s.technology,
                s.category_name,
                s.work_item,
                SUM(s.hours_spent) as hours,
                COUNT(s.session_id) as sessions
            FROM sessions s
            WHERE s.technology != ''
            GROUP BY s.technology, s.category_name, s.work_item
            ORDER BY s.technology, hours DESC
        ''')
        
        # Organize by technology
        tech_data = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            tech_name = row_dict['technology']
            cat_name = row_dict['category_name']
            work_item = row_dict['work_item'] if row_dict['work_item'] else 'General Practice'
            hours = row_dict['hours']
            sessions = row_dict['sessions']
            
            if tech_name not in tech_data:
                tech_data[tech_name] = {
                    'technology': tech_name,
                    'category': cat_name,
                    'total_hours': 0,
                    'total_sessions': 0,
                    'work_items': []
                }
            
            tech_data[tech_name]['total_hours'] += hours
            tech_data[tech_name]['total_sessions'] += sessions
            tech_data[tech_name]['work_items'].append({
                'name': work_item,
                'hours': hours,
                'sessions': sessions
            })
        
        return list(tech_data.values())
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_work_item_analytics(_db: DatabaseStorage) -> List[Dict[str, Any]]:
        """Get work item analytics with skill breakdown."""
        conn = _db._get_connection()
        cursor = _db._get_cursor(conn)
        
        # Get work item totals with skill breakdown
        cursor.execute('''
            SELECT 
                s.work_item,
                s.technology,
                s.skill_topic,
                s.session_type,
                SUM(s.hours_spent) as hours,
                COUNT(s.session_id) as sessions
            FROM sessions s
            WHERE s.work_item != '' AND s.work_item IS NOT NULL
            GROUP BY s.work_item, s.technology, s.skill_topic, s.session_type
            ORDER BY s.work_item, hours DESC
        ''')
        
        # Organize by work item + technology (unique key)
        work_item_data = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            work_item = row_dict['work_item']
            tech_name = row_dict['technology']
            skill = row_dict['skill_topic'] if row_dict['skill_topic'] else 'General'
            session_type = row_dict['session_type']
            hours = row_dict['hours']
            sessions = row_dict['sessions']
            
            # Use combination of work_item + technology as unique key
            unique_key = f"{work_item}|{tech_name}"
            
            if unique_key not in work_item_data:
                work_item_data[unique_key] = {
                    'work_item': work_item,
                    'technology': tech_name,
                    'total_hours': 0,
                    'total_sessions': 0,
                    'studying_hours': 0,
                    'practice_hours': 0,
                    'skills': []
                }
            
            work_item_data[unique_key]['total_hours'] += hours
            work_item_data[unique_key]['total_sessions'] += sessions
            
            if session_type == 'Studying':
                work_item_data[unique_key]['studying_hours'] += hours
            elif session_type == 'Practice':
                work_item_data[unique_key]['practice_hours'] += hours
            
            # Add skill if not already there
            existing_skill = next((s for s in work_item_data[unique_key]['skills'] if s['name'] == skill), None)
            if existing_skill:
                existing_skill['hours'] += hours
                existing_skill['sessions'] += sessions
            else:
                work_item_data[unique_key]['skills'].append({
                    'name': skill,
                    'hours': hours,
                    'sessions': sessions
                })
        
        return list(work_item_data.values())
