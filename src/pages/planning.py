"""
Planning Page - Learning roadmap showing technologies grouped by category.
Displays progress, goals, and completion tracking.
"""

import streamlit as st
from src.database.operations import DatabaseStorage

def show_planning_page():
    """Display dynamic learning roadmap grouped by category."""
    # Header with MG branding
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #FFD700;">
        <h1 style="color: #FFD700; margin: 0; text-align: center;">📋 Learning Roadmap</h1>
        <p style="color: #C0C0C0; text-align: center; margin: 0.5rem 0 0 0;">Your Technologies Grouped by Category</p>
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
    
    st.markdown("---")
    
    # Get data from database
    tech_stack = db.get_all_tech_stack()
    
    if not tech_stack:
        st.info("📚 No technologies added yet. Visit the **Tech Stack** page to add your first technology!")
        return
    
    # Calculate hours for each technology from sessions
    tech_hours = {}
    all_sessions = db.get_all_sessions()
    for session in all_sessions:
        tech_name = session.get('technology', '')
        hours = session.get('hours_spent', 0)
        tech_hours[tech_name] = tech_hours.get(tech_name, 0) + hours
    
    # Group technologies by category
    categories_data = {}
    for tech in tech_stack:
        tech_name = tech['name']
        category = tech.get('category', '❓ Uncategorized')
        
        if category not in categories_data:
            categories_data[category] = []
        
        categories_data[category].append({
            'name': tech_name,
            'logged_hours': tech_hours.get(tech_name, 0),
            'goal_hours': tech.get('goal_hours', 50)
        })
    
    # Overall breakdown
    st.markdown("### 📊 Overall Session Type Breakdown")
    
    studying_hours = sum(s.get('hours_spent', 0) for s in all_sessions if s.get('session_type') == 'Studying')
    practice_hours = sum(s.get('hours_spent', 0) for s in all_sessions if s.get('session_type') == 'Practice')
    total_typed = studying_hours + practice_hours
    
    if total_typed > 0:
        studying_pct = (studying_hours / total_typed * 100)
        practice_pct = (practice_hours / total_typed * 100)
        
        breakdown_col1, breakdown_col2, breakdown_col3 = st.columns(3)
        
        with breakdown_col1:
            st.metric("Total Hours", f"{total_typed:.1f}h")
        with breakdown_col2:
            st.metric("📚 Studying", f"{studying_hours:.1f}h ({studying_pct:.0f}%)")
        with breakdown_col3:
            st.metric("💪 Practice", f"{practice_hours:.1f}h ({practice_pct:.0f}%)")
    
    st.markdown("---")
    
    # Display categories
    st.markdown("### 🗂️ Technologies by Category")
    
    for category, techs in sorted(categories_data.items()):
        # Calculate category totals
        category_logged = sum(t['logged_hours'] for t in techs)
        category_goal = sum(t['goal_hours'] for t in techs)
        category_progress = (category_logged / category_goal * 100) if category_goal > 0 else 0
        
        with st.expander(f"{category} ({len(techs)} technologies - {category_progress:.0f}% complete)", expanded=False):
            st.markdown(f"**Category Progress:** {category_logged:.1f}h / {category_goal:.1f}h")
            st.progress(min(category_progress / 100, 1.0))
            
            st.markdown("---")
            
            # Display each technology in the category
            for tech in sorted(techs, key=lambda x: x['name']):
                tech_progress = (tech['logged_hours'] / tech['goal_hours'] * 100) if tech['goal_hours'] > 0 else 0
                remaining_hours = max(0, tech['goal_hours'] - tech['logged_hours'])
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**{tech['name']}**")
                    st.progress(min(tech_progress / 100, 1.0))
                    st.caption(f"{tech['logged_hours']:.1f}h logged / {tech['goal_hours']:.1f}h goal ({tech_progress:.0f}%)")
                
                with col2:
                    if remaining_hours > 0:
                        st.metric("Remaining", f"{remaining_hours:.1f}h")
                    else:
                        st.success("✅ Complete!")
    
    # Overall summary
    st.markdown("---")
    st.markdown("### 📊 Overall Summary")
    
    total_logged = sum(tech_hours.values())
    total_goal = sum(tech.get('goal_hours', 0) for tech in tech_stack)
    total_progress = (total_logged / total_goal * 100) if total_goal > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Technologies", len(tech_stack))
    with col2:
        st.metric("Hours Logged", f"{total_logged:.1f}h")
    with col3:
        st.metric("Goal Hours", f"{total_goal:.1f}h")
    with col4:
        st.metric("Overall Progress", f"{total_progress:.0f}%")
