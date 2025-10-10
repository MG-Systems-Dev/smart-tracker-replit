"""
Sessions Page - View, edit, and manage all learning sessions.
Provides filtering, sorting, and detailed session analytics.
"""

import streamlit as st
import pandas as pd
from src.database.operations import DatabaseStorage
from src.services import CachedQueryService

def show_sessions_page():
    """Display the Personal Development Dashboard / Sessions page."""
    # Header with MG branding
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #FFD700;">
        <h1 style="color: #FFD700; margin: 0; text-align: center;">📚 Sessions Manager</h1>
        <p style="color: #C0C0C0; text-align: center; margin: 0.5rem 0 0 0;">View & Edit Your Learning Sessions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Home", help="Return to main page"):
        st.session_state.current_page = "home_v2"
        st.rerun()
    
    # Initialize database
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseStorage()
    
    db = st.session_state.db
    
    # Load all sessions from database
    all_sessions = db.get_all_sessions()
    
    # Transform for display
    if all_sessions:
        sessions_display = []
        for session in all_sessions:
            sessions_display.append({
                'session_id': session.get('session_id'),
                'date': session.get('session_date', ''),
                'technology': session.get('technology', ''),
                'topic': session.get('skill_topic', ''),
                'type': session.get('session_type', ''),
                'difficulty': session.get('difficulty', ''),
                'status': session.get('status', ''),
                'hours': session.get('hours_spent', 0),
                'tags': session.get('tags', ''),
                'notes': session.get('notes', '')
            })
        
        # Dashboard metrics
        st.markdown("### 📊 Session Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        total_sessions = len(sessions_display)
        total_hours = sum(s['hours'] for s in sessions_display)
        completed_sessions = len([s for s in sessions_display if s.get("status") == "Completed"])
        completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        with col1:
            st.metric("Total Sessions", total_sessions)
        with col2:
            st.metric("Hours Logged", f"{total_hours:.1f}")
        with col3:
            st.metric("Completed", completed_sessions)
        with col4:
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        # Practice vs Studying breakdown
        st.markdown("### 📊 Session Type Breakdown")
        
        studying_hours = sum(s['hours'] for s in sessions_display if s.get('type') == 'Studying')
        practice_hours = sum(s['hours'] for s in sessions_display if s.get('type') == 'Practice')
        total_typed = studying_hours + practice_hours
        
        studying_pct = (studying_hours / total_typed * 100) if total_typed > 0 else 0
        practice_pct = (practice_hours / total_typed * 100) if total_typed > 0 else 0
        
        breakdown_col1, breakdown_col2, breakdown_col3 = st.columns(3)
        
        with breakdown_col1:
            st.metric("Total Hours", f"{total_typed:.1f}h")
        with breakdown_col2:
            st.metric("📚 Studying", f"{studying_hours:.1f}h ({studying_pct:.0f}%)")
        with breakdown_col3:
            st.metric("💪 Practice", f"{practice_hours:.1f}h ({practice_pct:.0f}%)")
        
        st.markdown("---")
        
        # Filters
        st.markdown("### 🔍 Filters & Sorting")
        
        df_temp = pd.DataFrame(sessions_display)
        unique_technologies = ['All'] + sorted(df_temp['technology'].unique().tolist())
        unique_types = ['All'] + sorted(df_temp['type'].unique().tolist())
        unique_statuses = ['All'] + sorted(df_temp['status'].unique().tolist())
        
        col_filter1, col_filter2, col_filter3, col_sort = st.columns(4)
        
        with col_filter1:
            tech_filter = st.selectbox("Technology", unique_technologies, key="tech_filter")
        
        with col_filter2:
            type_filter = st.selectbox("Session Type", unique_types, key="type_filter")
        
        with col_filter3:
            status_filter = st.selectbox("Status", unique_statuses, key="status_filter")
        
        with col_sort:
            sort_options = ['Date (Newest)', 'Date (Oldest)', 'Hours (Most)', 'Hours (Least)']
            sort_by = st.selectbox("Sort By", sort_options, key="sort_filter")
        
        # Apply filters
        filtered_sessions = sessions_display.copy()
        
        if tech_filter != 'All':
            filtered_sessions = [s for s in filtered_sessions if s['technology'] == tech_filter]
        
        if type_filter != 'All':
            filtered_sessions = [s for s in filtered_sessions if s['type'] == type_filter]
        
        if status_filter != 'All':
            filtered_sessions = [s for s in filtered_sessions if s['status'] == status_filter]
        
        # Apply sorting
        if sort_by == 'Date (Newest)':
            filtered_sessions = sorted(filtered_sessions, key=lambda x: x['date'], reverse=True)
        elif sort_by == 'Date (Oldest)':
            filtered_sessions = sorted(filtered_sessions, key=lambda x: x['date'])
        elif sort_by == 'Hours (Most)':
            filtered_sessions = sorted(filtered_sessions, key=lambda x: x['hours'], reverse=True)
        elif sort_by == 'Hours (Least)':
            filtered_sessions = sorted(filtered_sessions, key=lambda x: x['hours'])
        
        # Display sessions
        st.markdown("---")
        st.markdown(f"### 📋 Sessions ({len(filtered_sessions)} shown)")
        
        for session in filtered_sessions:
            with st.expander(f"📅 {session['date']} - {session['technology']} - {session['topic'] or 'No topic'}", expanded=False):
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**Type:** {session['type']} | **Hours:** {session['hours']} | **Status:** {session['status']}")
                    st.write(f"**Difficulty:** {session['difficulty']}")
                    if session.get('tags'):
                        st.write(f"**Tags:** {session['tags']}")
                    if session.get('notes'):
                        st.write(f"**Notes:** {session['notes']}")
                
                with col_actions:
                    if st.button("🗑️ Delete", key=f"delete_{session['session_id']}"):
                        db.delete_session(session['session_id'])
                        CachedQueryService.invalidate_cache()  # Refresh dashboard
                        st.success("Session deleted!")
                        st.rerun()
        
        # Export to CSV
        if st.button("💾 Export to CSV"):
            df_export = pd.DataFrame(filtered_sessions)
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="learning_sessions.csv",
                mime="text/csv"
            )
    else:
        st.info("📚 No sessions found. Go to **Log Session** to add your first session!")
