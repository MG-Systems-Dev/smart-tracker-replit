"""
Calculator Page - Workload & time estimation with flexible unit conversion.
Calculates completion time based on total hours and work schedule.
"""

import streamlit as st
from src.database.operations import DatabaseStorage

def show_calculator_page():
    """Display the Calculator page for workload estimation."""
    
    # Header with MG branding
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #FFD700;">
        <h1 style="color: #FFD700; margin: 0; text-align: center;">🧮 Workload Calculator</h1>
        <p style="color: #C0C0C0; text-align: center; margin: 0.5rem 0 0 0;">Time Estimation & Completion Metrics</p>
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
    
    # Get total hours from tech stack and planning
    tech_stack = db.get_all_tech_stack()
    total_goal_hours = sum(tech.get('goal_hours', 0) for tech in tech_stack)
    total_logged_hours = db.get_total_hours()
    remaining_hours = max(0, total_goal_hours - total_logged_hours)
    
    # Display current workload summary
    st.markdown("### 📊 Current Workload Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Goal", f"{total_goal_hours:.0f} hrs")
    with col2:
        st.metric("Logged", f"{total_logged_hours:.1f} hrs")
    with col3:
        st.metric("Remaining", f"{remaining_hours:.1f} hrs")
    with col4:
        completion_pct = (total_logged_hours / total_goal_hours * 100) if total_goal_hours > 0 else 0
        st.metric("Complete", f"{completion_pct:.1f}%")
    
    # Practice vs Studying breakdown
    st.markdown("### 📊 Session Type Breakdown")
    
    all_sessions = db.get_all_sessions()
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
    
    # Calculator Input Section
    st.markdown("### ⏱️ Time Estimation Calculator")
    st.info("💡 Enter your daily/weekly work hours to estimate completion time")
    
    # Input bar with unit selector
    col_input, col_unit = st.columns([3, 1])
    
    with col_input:
        work_input = st.number_input("Work Hours", min_value=0.1, value=40.0, step=0.5, 
                                     help="Enter how many hours you plan to work")
    
    with col_unit:
        time_unit = st.selectbox("Per", options=["Week", "Day", "Month"], 
                                help="Select time unit")
    
    # Convert input to hours per week for calculations
    if time_unit == "Day":
        hours_per_week = work_input * 5  # Assuming 5-day work week
        hours_per_day = work_input
    elif time_unit == "Month":
        hours_per_week = work_input / 4.33  # Average weeks per month
        hours_per_day = hours_per_week / 5
    else:  # Week
        hours_per_week = work_input
        hours_per_day = work_input / 5
    
    st.markdown("---")
    
    # Calculate completion metrics
    if hours_per_week > 0 and remaining_hours > 0:
        weeks_to_complete = remaining_hours / hours_per_week
        days_to_complete = remaining_hours / hours_per_day
        months_to_complete = weeks_to_complete / 4.33
        
        # Display KPI cards
        st.markdown("### 📅 Estimated Completion Time")
        
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        with kpi_col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #16213e 0%, #0f3460 100%); padding: 1.5rem; border-radius: 12px; border: 2px solid #FFD700; text-align: center;">
                <h3 style="color: #FFD700; margin: 0;">⏰ Hours</h3>
                <p style="color: #FFFFFF; font-size: 2rem; font-weight: bold; margin: 1rem 0 0 0;">{:.1f}</p>
            </div>
            """.format(remaining_hours), unsafe_allow_html=True)
        
        with kpi_col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #16213e 0%, #0f3460 100%); padding: 1.5rem; border-radius: 12px; border: 2px solid #FFD700; text-align: center;">
                <h3 style="color: #FFD700; margin: 0;">📆 Days</h3>
                <p style="color: #FFFFFF; font-size: 2rem; font-weight: bold; margin: 1rem 0 0 0;">{:.1f}</p>
            </div>
            """.format(days_to_complete), unsafe_allow_html=True)
        
        with kpi_col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #16213e 0%, #0f3460 100%); padding: 1.5rem; border-radius: 12px; border: 2px solid #FFD700; text-align: center;">
                <h3 style="color: #FFD700; margin: 0;">📅 Weeks</h3>
                <p style="color: #FFFFFF; font-size: 2rem; font-weight: bold; margin: 1rem 0 0 0;">{:.1f}</p>
            </div>
            """.format(weeks_to_complete), unsafe_allow_html=True)
        
        with kpi_col4:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #16213e 0%, #0f3460 100%); padding: 1.5rem; border-radius: 12px; border: 2px solid #FFD700; text-align: center;">
                <h3 style="color: #FFD700; margin: 0;">🗓️ Months</h3>
                <p style="color: #FFFFFF; font-size: 2rem; font-weight: bold; margin: 1rem 0 0 0;">{:.1f}</p>
            </div>
            """.format(months_to_complete), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Detailed breakdown
        st.markdown("### 📈 Detailed Breakdown")
        
        col_detail1, col_detail2 = st.columns(2)
        
        with col_detail1:
            st.markdown("#### Work Schedule")
            st.write(f"• **Hours per day:** {hours_per_day:.1f}")
            st.write(f"• **Hours per week:** {hours_per_week:.1f}")
            st.write(f"• **Hours per month:** {hours_per_week * 4.33:.1f}")
        
        with col_detail2:
            st.markdown("#### Completion Estimates")
            # Calculate calendar dates if possible
            from datetime import datetime, timedelta
            completion_date = datetime.now() + timedelta(days=days_to_complete)
            st.write(f"• **Estimated completion:** {completion_date.strftime('%B %d, %Y')}")
            st.write(f"• **Working days:** {days_to_complete:.0f} days")
            st.write(f"• **Calendar days:** {days_to_complete * 1.4:.0f} days (including weekends)")
        
        # Progress visualization
        st.markdown("---")
        st.markdown("### 📊 Progress Visualization")
        
        progress_bar_value = min(total_logged_hours / total_goal_hours, 1.0) if total_goal_hours > 0 else 0
        st.progress(progress_bar_value)
        st.caption(f"You've completed {total_logged_hours:.1f} of {total_goal_hours:.0f} hours ({completion_pct:.1f}%)")
        
    elif remaining_hours <= 0:
        st.success("🎉 Congratulations! You've completed all your goal hours!")
        st.balloons()
    else:
        st.warning("⚠️ Please enter work hours greater than 0 to calculate completion time")
    
    st.markdown("---")
    
    # Alternative scenarios
    st.markdown("### 🔄 Quick Scenarios")
    st.caption("See completion time under different work schedules")
    
    scenarios = [
        ("💼 Full Time (40 hrs/week)", 40),
        ("⏰ Part Time (20 hrs/week)", 20),
        ("🚀 Intensive (60 hrs/week)", 60),
        ("🎯 Focused (10 hrs/week)", 10)
    ]
    
    scenario_cols = st.columns(4)
    for idx, (label, hours) in enumerate(scenarios):
        with scenario_cols[idx]:
            if hours > 0 and remaining_hours > 0:
                weeks = remaining_hours / hours
                months = weeks / 4.33
                st.metric(label, f"{months:.1f} months", f"{weeks:.1f} weeks")
