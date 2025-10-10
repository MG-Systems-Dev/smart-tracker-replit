"""
Smart Tracker Streamlit Web Application.

A web-based interface for the Smart Tracker application using Streamlit.
"""

import streamlit as st
import logging
import os
import sys
from pathlib import Path
from datetime import date
from src.database.operations import DatabaseStorage
from src.core.config import __version__

# Add project root to Python path for Streamlit Community Cloud
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/activity.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def validate_session(session_date, technology, hours):
    """Validate session data. Returns (is_valid, error_message)."""
    # Check hours
    if hours < 0 or hours > 12:
        return False, "⚠️ Hours must be between 0 and 12 (inclusive)"
    
    # Check future date
    if session_date > date.today():
        return False, "⚠️ Cannot log sessions for future dates"
    
    # Check technology not empty
    if not technology or not technology.strip():
        return False, "⚠️ Technology cannot be empty"
    
    return True, ""

def get_tech_list(tech_stack):
    """Get list of technology names from tech stack."""
    if not tech_stack:
        return ["Python", "Pandas", "Streamlit", "FastAPI", "SQL", "AI/ML"]
    return [tech['name'] for tech in tech_stack]

def ensure_tech_in_stack(technology, tech_stack, storage, category="❓ Uncategorized"):
    """Add technology to tech stack if it doesn't exist."""
    tech_names = [tech['name'] for tech in tech_stack]
    if technology not in tech_names:
        new_tech = {
            "name": technology,
            "category": category,
            "goal_hours": 50,
            "date_added": str(date.today())
        }
        tech_stack.append(new_tech)
        storage.save_tech_stack(tech_stack)
        logging.info(f"Auto-added technology to stack: {technology} in category: {category}")
        return True
    return False

def get_studying_practice_breakdown(sessions, technology=None):
    """Calculate studying vs practice hours breakdown.
    
    Args:
        sessions: List of session dictionaries
        technology: Optional technology name to filter by
    
    Returns:
        dict with total_hours, studying_hours, studying_pct, practice_hours, practice_pct
    """
    # Filter sessions if technology is specified
    if technology:
        sessions = [s for s in sessions if s.get('technology') == technology]
    
    total_hours = sum(s.get('hours', 0) for s in sessions)
    studying_hours = sum(s.get('hours', 0) for s in sessions if s.get('type') == 'Studying')
    practice_hours = sum(s.get('hours', 0) for s in sessions if s.get('type') == 'Practice')
    
    # Calculate percentages
    studying_pct = (studying_hours / total_hours * 100) if total_hours > 0 else 0
    practice_pct = (practice_hours / total_hours * 100) if total_hours > 0 else 0
    
    return {
        'total_hours': total_hours,
        'studying_hours': studying_hours,
        'studying_pct': studying_pct,
        'practice_hours': practice_hours,
        'practice_pct': practice_pct
    }

def main():
    """Main Streamlit application function."""
    # Page configuration
    st.set_page_config(
        page_title="MG Smart Tracker v2.0 | System Dev",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Hide default Streamlit page navigation
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize database (v2.0)
    if "db" not in st.session_state:
        st.session_state.db = DatabaseStorage()
    
    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home_v2"
    
    # Load learning sessions from database
    if "learning_sessions" not in st.session_state:
        all_sessions = st.session_state.db.get_all_sessions()
        # Transform to old format for compatibility with legacy dashboard code
        transformed_sessions = []
        for session in all_sessions:
            transformed_sessions.append({
                'date': session.get('session_date', session.get('date', '')),
                'technology': session.get('technology', ''),
                'topic': session.get('skill_topic', session.get('topic', '')),
                'notes': session.get('notes', ''),
                'tags': session.get('tags', ''),
                'type': session.get('session_type', session.get('type', '')),
                'difficulty': session.get('difficulty', ''),
                'status': session.get('status', ''),
                'hours': session.get('hours_spent', session.get('hours', 0))
            })
        st.session_state.learning_sessions = transformed_sessions
    
    # Load tech stack from database
    if "tech_stack_loaded" not in st.session_state:
        tech_stack = st.session_state.db.get_all_tech_stack()
        st.session_state.tech_stack = tech_stack if tech_stack else []
        st.session_state.tech_stack_loaded = True
    
    # Main header with MG branding
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%); border-radius: 10px; margin-bottom: 1rem;">
        <h1 style="color: #FFD700; margin: 0; font-size: 2.5rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">⚡ MG SMART TRACKER</h1>
        <p style="color: #C0C0C0; margin: 0.5rem 0 0 0; font-size: 1.1rem;">Professional Development Tracking Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Professional sidebar with MG branding
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 1rem; border-radius: 10px; border: 1px solid #FFD700; margin-bottom: 1rem;">
            <h3 style="color: #FFD700; text-align: center; margin: 0;">⚡ MG SYSTEM</h3>
            <p style="color: #C0C0C0; text-align: center; margin: 0.5rem 0 0 0; font-size: 0.9rem;">v{}</p>
        </div>
        """.format(__version__), unsafe_allow_html=True)
        
        st.markdown("### 🎯 Navigation")
        
        # Navigation buttons with professional styling
        if st.button("🏠 Home Dashboard", width="stretch"):
            st.session_state.current_page = "home_v2"
            st.rerun()
        
        if st.button("📚 Sessions", width="stretch"):
            st.session_state.current_page = "clean_dashboard"
            st.rerun()
            
        if st.button("🎓 Log Session", width="stretch"):
            st.session_state.current_page = "learning_tracker"
            st.rerun()
        
        if st.button("🎯 Tech Stack CRUD", width="stretch"):
            st.session_state.current_page = "tech_stack_crud"
            st.rerun()
        
        if st.button("📋 Planning", width="stretch"):
            st.session_state.current_page = "planning"
            st.rerun()
        
        if st.button("🧮 Calculator", width="stretch"):
            st.session_state.current_page = "calculator"
            st.rerun()
        
        if st.button("📝 Dropdown Manager", width="stretch"):
            st.session_state.current_page = "dropdown_manager"
            st.rerun()
        
        if st.button("📊 Analytics", width="stretch"):
            st.session_state.current_page = "analytics"
            st.rerun()
        
        st.markdown("---")
        
        # Professional info section
        st.markdown("""
        <div style="background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%); padding: 1rem; border-radius: 8px; border: 1px solid #C0C0C0;">
            <h4 style="color: #FFD700; margin-top: 0;">🔧 System Status</h4>
            <p style="color: #00CED1; margin: 0.5rem 0;"><strong>Status:</strong> <span style="color: #90EE90;">Online</span></p>
            <p style="color: #00CED1; margin: 0.5rem 0;"><strong>Mode:</strong> Development</p>
            <p style="color: #00CED1; margin: 0.5rem 0;"><strong>Build:</strong> Professional</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #C0C0C0; font-size: 0.9rem;">
            <p><strong style="color: #FFD700;">MG System Dev</strong></p>
            <p>Personal learning & development tracking</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display the appropriate page
    if st.session_state.current_page == "home_v2":
        # Import and show new Home KPI Dashboard
        from src.pages.home_dashboard import show_home_kpi_dashboard
        show_home_kpi_dashboard()
    elif st.session_state.current_page == "tech_stack_crud":
        # Import and show Tech Stack CRUD page
        from src.pages.tech_stack import show_tech_stack_crud_page
        show_tech_stack_crud_page()
    elif st.session_state.current_page == "calculator":
        # Import and show Calculator page
        from src.pages.calculator import show_calculator_page
        show_calculator_page()
    elif st.session_state.current_page == "dropdown_manager":
        # Import and show Dropdown Manager page
        from src.pages.dropdown_manager import show_dropdown_manager_page
        show_dropdown_manager_page()
    elif st.session_state.current_page == "clean_dashboard":
        from src.pages.sessions import show_sessions_page
        show_sessions_page()
    elif st.session_state.current_page == "learning_tracker":
        from src.pages.log_session import show_log_session_page
        show_log_session_page()
    elif st.session_state.current_page == "planning":
        from src.pages.planning import show_planning_page
        show_planning_page()
    elif st.session_state.current_page == "analytics":
        from src.pages.analytics import show_analytics_page
        show_analytics_page()

if __name__ == "__main__":
    main()