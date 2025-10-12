"""
Navigation utilities for persistent page navigation.
"""

import streamlit as st

def navigate_to(page: str):
    """Navigate to a page and persist the choice to database."""
    from src.database.operations import DatabaseStorage
    
    st.session_state.current_page = page
    
    # Save to database if db is initialized
    if 'db' in st.session_state and st.session_state.db:
        st.session_state.db.save_app_state("current_page", page)
    
    st.rerun()
