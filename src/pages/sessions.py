"""
Sessions Page - View, edit, and manage all learning sessions.
Provides filtering, sorting, and detailed session analytics.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.core.app import get_database
from src.database.operations import DatabaseStorage
from src.services import CachedQueryService
from src.utils.dropdowns import DropdownManager
from src.utils.navigation import navigate_to

def show_edit_session_form(db: DatabaseStorage, session_id: int):
    """Display edit form for a specific session."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #FFD700;">
        <h1 style="color: #FFD700; margin: 0; text-align: center;">✏️ Edit Session</h1>
        <p style="color: #C0C0C0; text-align: center; margin: 0.5rem 0 0 0;">Update Learning Session Details</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Sessions"):
        st.session_state.editing_session_id = None
        # Clear edit state
        for key in ['session_type_edit', 'difficulty_edit', 'status_edit']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    # Get session data
    session = db.get_session_by_id(session_id)
    
    if not session:
        st.error(f"Session ID {session_id} not found!")
        if st.button("← Return to Sessions"):
            st.session_state.editing_session_id = None
            st.rerun()
        return
    
    st.markdown("---")
    
    dropdown_manager = DropdownManager(db)
    
    # Pre-populate session state with current values BEFORE rendering widgets
    if f"session_type_edit" not in st.session_state:
        st.session_state[f"session_type_edit"] = session.get('session_type', 'Studying')
    if f"difficulty_edit" not in st.session_state:
        st.session_state[f"difficulty_edit"] = session.get('difficulty', 'Beginner')
    if f"status_edit" not in st.session_state:
        st.session_state[f"status_edit"] = session.get('status', 'In Progress')
    
    # Category selection OUTSIDE form for reactivity
    st.markdown("### 📝 Edit Session Details")
    st.markdown("**📂 Category Name**")
    all_categories = db.get_all_categories()
    
    current_category = session.get('category_name', '')
    category_index = all_categories.index(current_category) if current_category in all_categories else 0
    
    selected_category = st.selectbox(
        "category_dropdown_edit",
        options=all_categories,
        index=category_index,
        key="category_edit_outside",
        label_visibility="collapsed",
        help="Select the category"
    )
    
    with st.form("edit_session_form"):
        # Basic fields
        col1, col2 = st.columns(2)
        
        with col1:
            session_date_str = session.get('session_date', '')
            try:
                session_date = datetime.strptime(session_date_str.split()[0], '%Y-%m-%d').date()
            except:
                from datetime import date
                session_date = date.today()
            
            session_date = st.date_input("📅 Session Date", value=session_date)
        
        with col2:
            session_type = dropdown_manager.render_independent_dropdown('session_type', key_suffix="edit")
        
        st.markdown("---")
        
        # Technology
        st.markdown("**🔧 Technology**")
        all_techs_data = db.get_all_tech_stack()
        
        if selected_category:
            filtered_techs = [tech['name'] for tech in all_techs_data if tech.get('category') == selected_category]
        else:
            filtered_techs = [tech['name'] for tech in all_techs_data]
        
        current_tech = session.get('technology', '')
        tech_index = filtered_techs.index(current_tech) if current_tech in filtered_techs else 0
        
        technology = st.selectbox(
            "technology_dropdown_edit",
            options=filtered_techs,
            index=tech_index,
            label_visibility="collapsed"
        )
        
        # Work Item - Show ALL work items (cascading from technology)
        st.markdown("**📋 Work Item**")
        all_work_items = []
        if technology:
            all_work_items = db.get_work_items_by_technology(technology)
        
        current_work_item = session.get('work_item', '')
        
        if all_work_items:
            work_item_options = [""] + sorted(list(set(all_work_items)))
            work_item_index = work_item_options.index(current_work_item) if current_work_item in work_item_options else 0
            
            work_item = st.selectbox(
                "work_item_dropdown_edit",
                options=work_item_options,
                index=work_item_index,
                label_visibility="collapsed",
                help="Work items for selected technology"
            )
        else:
            work_item = st.text_input("Work Item (custom)", value=current_work_item, label_visibility="collapsed", placeholder="No work items found - enter custom")
        
        # Skill/Topic - FILTERED by selected work item
        st.markdown("**🎯 Skill / Topic**")
        
        filtered_skills = []
        if work_item and work_item.strip():
            filtered_skills = db.get_skills_by_work_item(work_item)
        
        current_skill = session.get('skill_topic', '')
        
        if filtered_skills:
            skill_options = [""] + sorted(list(set(filtered_skills)))
            skill_index = skill_options.index(current_skill) if current_skill in skill_options else 0
            
            skill_topic = st.selectbox(
                "skill_dropdown_edit",
                options=skill_options,
                index=skill_index,
                label_visibility="collapsed",
                help="Skills for selected work item"
            )
        else:
            skill_topic = st.text_input("Skill/Topic (custom)", value=current_skill, label_visibility="collapsed", placeholder="No skills found - enter custom")
        
        # Additional Context
        st.markdown("---")
        st.markdown("#### 📊 Additional Context")
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Category Source - dropdown from database
            all_sources = db.get_all_category_sources()
            current_source = session.get('category_source', '')
            
            if all_sources:
                # Try to find current source in list
                source_index = all_sources.index(current_source) if current_source in all_sources else 0
                category_source = st.selectbox("📚 Category Source", options=all_sources, index=source_index, key="category_source_edit")
            else:
                st.info("💡 No sources available. Add them in Dropdown Manager → Category Sources tab.")
                category_source = st.text_input("📚 Category Source (custom)", value=current_source, key="category_source_edit_custom")
            
            difficulty = dropdown_manager.render_independent_dropdown('difficulty', key_suffix="edit")
        
        with col4:
            hours_spent = st.number_input("⏱️ Hours Spent", min_value=0.0, max_value=12.0, value=float(session.get('hours_spent', 1.0)), step=0.25)
            status = dropdown_manager.render_independent_dropdown('status', key_suffix="edit")
        
        # Optional fields
        st.markdown("---")
        tags = st.text_area("🏷️ Tags", value=session.get('tags', ''), placeholder="Enter tags separated by commas...")
        notes = st.text_area("📝 Notes", value=session.get('notes', ''), placeholder="Detailed notes about this session...")
        
        # Submit buttons
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
        
        with col_cancel:
            cancelled = st.form_submit_button("❌ Cancel")
        
        if cancelled:
            st.session_state.editing_session_id = None
            # Clear edit state
            for key in ['session_type_edit', 'difficulty_edit', 'status_edit']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        if submitted:
            # Update session data
            session_data = {
                'session_date': str(session_date),
                'session_type': session_type,
                'category_name': selected_category,
                'technology': technology,
                'work_item': work_item,
                'skill_topic': skill_topic,
                'category_source': category_source,
                'difficulty': difficulty,
                'status': status,
                'hours_spent': hours_spent,
                'tags': tags,
                'notes': notes
            }
            
            success = db.update_session(session_id, session_data)
            
            if success:
                # Clear edit state
                st.session_state.editing_session_id = None
                for key in ['session_type_edit', 'difficulty_edit', 'status_edit']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                CachedQueryService.invalidate_cache()
                st.success("✅ Session updated successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to update session")

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
        navigate_to("home_v2")
    
    # Initialize database (singleton)
    db = get_database()
    
    # Check if we're editing a session
    if 'editing_session_id' in st.session_state and st.session_state.editing_session_id:
        show_edit_session_form(db, st.session_state.editing_session_id)
        return
    
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
        
        # Display sessions grouped by year
        st.markdown("---")
        st.markdown(f"### 📋 Sessions ({len(filtered_sessions)} shown)")
        
        # Group sessions by year
        from datetime import datetime
        sessions_by_year = {}
        for session in filtered_sessions:
            try:
                year = datetime.strptime(session['date'].split()[0], '%Y-%m-%d').year
            except:
                year = "Unknown"
            
            if year not in sessions_by_year:
                sessions_by_year[year] = []
            sessions_by_year[year].append(session)
        
        # Display each year in an expandable box (newest first)
        for year in sorted(sessions_by_year.keys(), reverse=True):
            year_sessions = sessions_by_year[year]
            year_hours = sum(s['hours'] for s in year_sessions)
            
            with st.expander(f"📅 **{year}** ({len(year_sessions)} sessions, {year_hours:.1f} hours)", expanded=False):
                
                # Group year sessions by month
                sessions_by_month = {}
                for session in year_sessions:
                    try:
                        date_obj = datetime.strptime(session['date'].split()[0], '%Y-%m-%d')
                        month = date_obj.strftime('%B')  # Full month name
                        month_num = date_obj.month  # For sorting
                    except:
                        month = "Unknown"
                        month_num = 0
                    
                    if month not in sessions_by_month:
                        sessions_by_month[month] = {'sessions': [], 'month_num': month_num}
                    sessions_by_month[month]['sessions'].append(session)
                
                # Display each month in an expandable box (newest first)
                for month in sorted(sessions_by_month.keys(), key=lambda m: sessions_by_month[m]['month_num'], reverse=True):
                    month_sessions = sessions_by_month[month]['sessions']
                    month_hours = sum(s['hours'] for s in month_sessions)
                    
                    with st.expander(f"📆 **{month}** ({len(month_sessions)} sessions, {month_hours:.1f} hours)", expanded=False):
                        for session in month_sessions:
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
                                    if st.button("✏️ Edit", key=f"edit_{session['session_id']}", type="primary"):
                                        st.session_state.editing_session_id = session['session_id']
                                        st.rerun()
                                    
                                    if st.button("🗑️ Delete", key=f"delete_{session['session_id']}"):
                                        db.delete_session(session['session_id'])
                                        CachedQueryService.invalidate_cache()
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
