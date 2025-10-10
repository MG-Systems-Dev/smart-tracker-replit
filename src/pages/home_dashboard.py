"""
Home KPI Dashboard - Real-time operations dashboard with system-wide analytics.
No editing functionality - pure KPI and metrics display.
"""

import streamlit as st
from src.database.operations import DatabaseStorage
from src.services import CachedQueryService
from datetime import datetime, timedelta

def show_home_kpi_dashboard():
    """Display the Home page as KPI dashboard only."""
    
    # Header with MG branding
    st.markdown("""
    <div class="main-header" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #FFD700; box-shadow: 0 8px 32px rgba(255, 215, 0, 0.3);">
        <h1 style="color: #FFD700; text-align: center; margin: 0; font-size: 3rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">⚡ MG SMART TRACKER</h1>
        <p style="color: #C0C0C0; text-align: center; margin-top: 0.5rem; font-size: 1.2rem;">Professional Development Tracking Platform</p>
        <p style="color: #FFD700; text-align: center; margin-top: 0.3rem; font-size: 0.9rem;">SYSTEM DEV | Real-Time Operations Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseStorage()
    
    db = st.session_state.db
    
    # ==================== KEY METRICS SECTION ====================
    st.markdown("### 📊 Key Performance Indicators")
    
    # Get core metrics using cached query (ONE batch query instead of multiple)
    metrics = CachedQueryService.get_dashboard_metrics(db)
    tech_stack = CachedQueryService.get_tech_stack_with_metrics(db)
    
    total_sessions = metrics['total_sessions']
    total_hours = metrics['total_hours']
    total_technologies = metrics['tech_count']
    total_goal_hours = sum(tech.get('goal_hours', 0) for tech in tech_stack)
    
    # Display KPI cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.metric("📚 Total Sessions", total_sessions)
    
    with kpi_col2:
        st.metric("⏱️ Total Hours", f"{total_hours:.1f}")
    
    with kpi_col3:
        st.metric("🔧 Technologies", total_technologies)
    
    with kpi_col4:
        completion_pct = (total_hours / total_goal_hours * 100) if total_goal_hours > 0 else 0
        st.metric("✅ Overall Progress", f"{completion_pct:.1f}%")
    
    st.markdown("---")
    
    # ==================== STUDYING VS PRACTICE BREAKDOWN ====================
    st.markdown("### 📊 Session Type Breakdown")
    
    type_breakdown = db.get_session_type_breakdown()
    
    if type_breakdown:
        breakdown_col1, breakdown_col2, breakdown_col3 = st.columns(3)
        
        studying_hours = type_breakdown.get('Studying', 0)
        practice_hours = type_breakdown.get('Practice', 0)
        total_typed = studying_hours + practice_hours
        
        studying_pct = (studying_hours / total_typed * 100) if total_typed > 0 else 0
        practice_pct = (practice_hours / total_typed * 100) if total_typed > 0 else 0
        
        with breakdown_col1:
            st.metric("Total Hours", f"{total_typed:.1f}")
        
        with breakdown_col2:
            st.metric("📚 Studying", f"{studying_hours:.1f}h ({studying_pct:.0f}%)")
        
        with breakdown_col3:
            st.metric("💪 Practice", f"{practice_hours:.1f}h ({practice_pct:.0f}%)")
    
    st.markdown("---")
    
    # ==================== RECENT ACTIVITY FEED ====================
    st.markdown("### 🔔 Recent Activity")
    
    # Get recent sessions using cached query
    recent_sessions = CachedQueryService.get_sessions_with_details(db, limit=5, offset=0)
    
    if recent_sessions:
        
        for session in recent_sessions:
            activity_date = session.get('session_date', 'Unknown')
            tech = session.get('technology', 'Unknown')
            skill = session.get('skill_topic', 'N/A')
            hours = session.get('hours_spent', 0)
            session_type = session.get('session_type', 'Unknown')
            
            # Activity card
            type_icon = "📚" if session_type == "Studying" else "💪"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%); padding: 1rem; border-radius: 10px; border-left: 4px solid #FFD700; margin-bottom: 0.5rem;">
                <p style="color: #FFD700; margin: 0; font-weight: bold;">{type_icon} {tech} • {skill}</p>
                <p style="color: #C0C0C0; margin: 0.3rem 0 0 0; font-size: 0.9rem;">{activity_date} • {hours:.1f} hours • {session_type}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent activity. Start logging sessions to see updates here!")
    
    st.markdown("---")
    
    # ==================== PROGRESS BY CATEGORY ====================
    st.markdown("### 📈 Progress by Category")
    
    # Get category hours using true aggregation (no row limit)
    category_stats = CachedQueryService.get_category_hours_aggregated(db)
    
    if category_stats:
        # Display as collapsible sections (default closed)
        for category, hours in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            # Get goal hours for this category from tech stack
            cat_goal = sum(tech.get('goal_hours', 0) for tech in tech_stack if tech.get('category') == category)
            cat_progress = (hours / cat_goal * 100) if cat_goal > 0 else 0
            
            with st.expander(f"**{category}** - {hours:.1f}h logged ({cat_progress:.1f}% complete)", expanded=False):
                col_cat1, col_cat2, col_cat3 = st.columns(3)
                
                with col_cat1:
                    st.metric("Logged Hours", f"{hours:.1f}")
                
                with col_cat2:
                    st.metric("Goal Hours", f"{cat_goal:.0f}")
                
                with col_cat3:
                    st.metric("Progress", f"{cat_progress:.1f}%")
                
                # Progress bar
                st.progress(min(cat_progress / 100, 1.0))
    else:
        st.info("No category data yet. Add sessions to see progress by category.")
    
    st.markdown("---")
    
    # ==================== QUICK LINKS NAVIGATION ====================
    st.markdown("### 🚀 Quick Actions")
    st.caption("Navigate to key pages to manage your learning journey")
    
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    
    with nav_col1:
        if st.button("🎓 Log Session", use_container_width=True, type="primary"):
            st.session_state.current_page = "learning_tracker"
            st.rerun()
    
    with nav_col2:
        if st.button("🎯 Tech Stack", use_container_width=True):
            st.session_state.current_page = "tech_stack_crud"
            st.rerun()
    
    with nav_col3:
        if st.button("📋 Planning", use_container_width=True):
            st.session_state.current_page = "planning"
            st.rerun()
    
    with nav_col4:
        if st.button("🧮 Calculator", use_container_width=True):
            st.session_state.current_page = "calculator"
            st.rerun()
    
    st.markdown("---")
    
    # ==================== SYSTEM STATUS ====================
    st.markdown("### 🔧 System Status")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.markdown("""
        <div style="background: #0f3460; padding: 1rem; border-radius: 8px; border: 1px solid #FFD700;">
            <p style="color: #FFD700; margin: 0; font-weight: bold;">Database</p>
            <p style="color: #00FF00; margin: 0.5rem 0 0 0;">✅ Connected</p>
        </div>
        """, unsafe_allow_html=True)
    
    with status_col2:
        st.markdown("""
        <div style="background: #0f3460; padding: 1rem; border-radius: 8px; border: 1px solid #FFD700;">
            <p style="color: #FFD700; margin: 0; font-weight: bold;">Last Updated</p>
            <p style="color: #C0C0C0; margin: 0.5rem 0 0 0;">{}</p>
        </div>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M')), unsafe_allow_html=True)
    
    with status_col3:
        st.markdown("""
        <div style="background: #0f3460; padding: 1rem; border-radius: 8px; border: 1px solid #FFD700;">
            <p style="color: #FFD700; margin: 0; font-weight: bold;">Mode</p>
            <p style="color: #C0C0C0; margin: 0.5rem 0 0 0;">Development</p>
        </div>
        """, unsafe_allow_html=True)
