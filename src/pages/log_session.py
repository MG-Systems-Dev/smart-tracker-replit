"""
Log Session Page - Create new learning sessions with cascading dropdowns.
Uses the new hierarchical dropdown system for data entry.
"""

import streamlit as st
from datetime import date
from src.database.operations import DatabaseStorage
from src.utils.dropdowns import DropdownManager
from src.services import CachedQueryService
import logging

def show_log_session_page():
    """Display the Log Session page for creating new sessions."""
    # Header with MG branding
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #FFD700;">
        <h1 style="color: #FFD700; margin: 0; text-align: center;">🎓 Log New Session</h1>
        <p style="color: #C0C0C0; text-align: center; margin: 0.5rem 0 0 0;">Track Your Learning Progress</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Home"):
        st.session_state.current_page = "home_v2"
        st.rerun()
    
    # Initialize database
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseStorage()
    
    db = st.session_state.db
    dropdown_manager = DropdownManager(db)
    
    st.markdown("---")
    
    # Session Entry Form
    st.markdown("### 📝 Session Entry")
    
    with st.form("session_entry_form"):
        # Basic fields
        col1, col2 = st.columns(2)
        
        with col1:
            session_date = st.date_input("📅 Session Date", value=date.today())
        
        with col2:
            session_type = dropdown_manager.render_independent_dropdown('session_type', key_suffix="entry")
        
        # Simplified dropdowns - NO parent filtering, auto-paired in background
        st.markdown("---")
        st.markdown("#### 🎯 Learning Details")
        
        selected_values = dropdown_manager.render_simplified_form(key_suffix="entry")
        
        # Independent context fields
        st.markdown("---")
        st.markdown("#### 📊 Additional Context")
        
        col3, col4 = st.columns(2)
        
        with col3:
            category_source = dropdown_manager.render_independent_dropdown('category_source', key_suffix="entry")
            difficulty = dropdown_manager.render_independent_dropdown('difficulty', key_suffix="entry")
        
        with col4:
            hours_spent = st.number_input("⏱️ Hours Spent", min_value=0.0, max_value=12.0, value=1.0, step=0.25)
            status = dropdown_manager.render_independent_dropdown('status', key_suffix="entry")
        
        # Optional fields
        st.markdown("---")
        tags = st.text_area("🏷️ Tags", placeholder="Enter tags separated by commas...", help="Optional tags for categorization")
        notes = st.text_area("📝 Notes", placeholder="Detailed notes about this session...", help="Optional notes or reflections")
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Session", type="primary")
        
        if submitted:
            # Validation
            if hours_spent < 0 or hours_spent > 12:
                st.error("⚠️ Hours must be between 0 and 12")
            elif session_date > date.today():
                st.error("⚠️ Cannot log sessions for future dates")
            elif not selected_values.get('technology'):
                st.error("⚠️ Technology is required")
            else:
                # FIRST: Save all pending dropdown values (batch save)
                dropdown_manager.save_pending_dropdowns(key_suffix="entry")
                
                # THEN: Create session data
                session_data = {
                    'session_date': str(session_date),
                    'session_type': session_type,
                    'category_name': selected_values.get('category_name', ''),
                    'technology': selected_values.get('technology', ''),
                    'work_item': selected_values.get('work_item', ''),
                    'skill_topic': selected_values.get('skill_topic', ''),
                    'category_source': category_source,
                    'difficulty': difficulty,
                    'status': status,
                    'hours_spent': hours_spent,
                    'tags': tags,
                    'notes': notes
                }
                
                # FINALLY: Save session to database
                session_id = db.add_session(session_data)
                
                if session_id:
                    # CRITICAL: Invalidate cache so dashboard refreshes immediately
                    CachedQueryService.invalidate_cache()
                    
                    st.success(f"✅ Session saved successfully! (ID: {session_id})")
                    st.balloons()
                    logging.info(f"Added session ID {session_id}: {selected_values.get('technology')} - {hours_spent}h")
                else:
                    st.error("❌ Failed to save session")
    
    # Quick Stats
    st.markdown("---")
    st.markdown("### 📈 Quick Stats")
    
    all_sessions = db.get_all_sessions()
    total_sessions = len(all_sessions)
    total_hours = db.get_total_hours()
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.metric("Total Sessions", total_sessions)
    with col_stat2:
        st.metric("Total Hours", f"{total_hours:.1f}")
    with col_stat3:
        tech_count = len(db.get_all_tech_stack())
        st.metric("Technologies", tech_count)
