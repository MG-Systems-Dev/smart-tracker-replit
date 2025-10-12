"""
Learning Sources Dashboard - KPI analysis of learning platforms and sources.
Analyze effectiveness, time investment, and ROI across different learning platforms.
"""

import streamlit as st
from datetime import datetime, timedelta
from src.database.operations import DatabaseStorage
from src.services.cached_queries import CachedQueryService
from src.utils.navigation import navigate_to

def show_learning_sources_page():
    """Display Learning Sources KPI Dashboard."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #FFD700;">
        <h1 style="color: #FFD700; margin: 0; text-align: center;">📚 Learning Sources Dashboard</h1>
        <p style="color: #C0C0C0; text-align: center; margin: 0.5rem 0 0 0;">Platform Effectiveness & ROI Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Back to Home", help="Return to main page"):
        navigate_to("home_v2")
    
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseStorage()
    
    db = st.session_state.db
    
    st.markdown("---")
    
    all_sessions = db.get_all_sessions()
    
    if not all_sessions:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 2rem; border-radius: 15px; border: 2px solid #FFD700; text-align: center;">
            <h3 style="color: #FFD700; margin: 0;">📚 No Sessions Yet</h3>
            <p style="color: #C0C0C0; margin: 1rem 0;">Log your first session to start tracking learning sources!</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    source_data = {}
    
    for session in all_sessions:
        source = session.get('category_source', 'Unknown')
        if not source or source.strip() == '':
            source = 'Not Specified'
        
        if source not in source_data:
            source_data[source] = {
                'hours': 0,
                'sessions': 0,
                'technologies': set(),
                'session_types': {'Studying': 0, 'Practice': 0},
                'recent_sessions': []
            }
        
        hours = session.get('hours_spent', 0)
        source_data[source]['hours'] += hours
        source_data[source]['sessions'] += 1
        source_data[source]['technologies'].add(session.get('technology', 'Unknown'))
        
        session_type = session.get('session_type', 'Unknown')
        if session_type in source_data[source]['session_types']:
            source_data[source]['session_types'][session_type] += hours
        
        session_date_str = session.get('session_date', '')
        if session_date_str:
            try:
                session_date = datetime.strptime(session_date_str.split()[0], '%Y-%m-%d')
                source_data[source]['recent_sessions'].append({
                    'date': session_date,
                    'hours': hours,
                    'technology': session.get('technology', '')
                })
            except:
                pass
    
    st.markdown("### 📊 Overall Source Statistics")
    
    total_sources = len(source_data)
    total_hours = sum(s['hours'] for s in source_data.values())
    total_sessions = sum(s['sessions'] for s in source_data.values())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Learning Sources", total_sources, help="Number of different platforms used")
    with col2:
        st.metric("Total Hours", f"{total_hours:.1f}h", help="Combined hours across all sources")
    with col3:
        st.metric("Total Sessions", total_sessions, help="All sessions logged")
    with col4:
        avg_hours_per_source = total_hours / total_sources if total_sources > 0 else 0
        st.metric("Avg per Source", f"{avg_hours_per_source:.1f}h", help="Average hours per source")
    
    st.markdown("---")
    
    sorted_sources = sorted(source_data.items(), key=lambda x: x[1]['hours'], reverse=True)
    
    if sorted_sources:
        most_used_source = sorted_sources[0]
        
        st.markdown("### 🏆 Top Performing Source")
        
        top_source_name = most_used_source[0]
        top_source_info = most_used_source[1]
        top_source_pct = (top_source_info['hours'] / total_hours * 100) if total_hours > 0 else 0
        
        top_col1, top_col2, top_col3, top_col4 = st.columns(4)
        
        with top_col1:
            st.metric("🥇 Source", top_source_name)
        with top_col2:
            st.metric("⏱️ Hours", f"{top_source_info['hours']:.1f}h", f"{top_source_pct:.1f}% of total")
        with top_col3:
            st.metric("📝 Sessions", top_source_info['sessions'])
        with top_col4:
            avg_hours = top_source_info['hours'] / top_source_info['sessions'] if top_source_info['sessions'] > 0 else 0
            st.metric("⚡ Avg/Session", f"{avg_hours:.1f}h")
        
        st.markdown("---")
    
    st.markdown("### 📈 Source Breakdown")
    
    for source_name, info in sorted_sources:
        source_pct = (info['hours'] / total_hours * 100) if total_hours > 0 else 0
        
        with st.expander(f"**{source_name}** - {info['hours']:.1f}h ({source_pct:.1f}%)", expanded=False):
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric("⏱️ Total Hours", f"{info['hours']:.1f}h")
            with metric_col2:
                st.metric("📝 Sessions", info['sessions'])
            with metric_col3:
                st.metric("🎯 Technologies", len(info['technologies']))
            with metric_col4:
                avg_session = info['hours'] / info['sessions'] if info['sessions'] > 0 else 0
                st.metric("📊 Avg Session", f"{avg_session:.1f}h")
            
            st.markdown("**Session Type Distribution:**")
            studying_h = info['session_types']['Studying']
            practice_h = info['session_types']['Practice']
            total_typed = studying_h + practice_h
            
            if total_typed > 0:
                studying_pct = (studying_h / total_typed * 100)
                practice_pct = (practice_h / total_typed * 100)
                
                type_col1, type_col2 = st.columns(2)
                with type_col1:
                    st.metric("📚 Studying", f"{studying_h:.1f}h", f"{studying_pct:.0f}%")
                with type_col2:
                    st.metric("💪 Practice", f"{practice_h:.1f}h", f"{practice_pct:.0f}%")
            
            st.markdown("**Technologies Learned:**")
            st.caption(", ".join(sorted(info['technologies'])))
            
            if info['recent_sessions']:
                now = datetime.now()
                last_30_days = now - timedelta(days=30)
                last_7_days = now - timedelta(days=7)
                
                recent_30d = [s for s in info['recent_sessions'] if s['date'] >= last_30_days]
                recent_7d = [s for s in info['recent_sessions'] if s['date'] >= last_7_days]
                
                hours_30d = sum(s['hours'] for s in recent_30d)
                hours_7d = sum(s['hours'] for s in recent_7d)
                
                st.markdown("---")
                st.markdown("**Recent Activity:**")
                
                activity_col1, activity_col2, activity_col3 = st.columns(3)
                
                with activity_col1:
                    st.metric("Last 7 Days", f"{hours_7d:.1f}h")
                with activity_col2:
                    st.metric("Last 30 Days", f"{hours_30d:.1f}h")
                with activity_col3:
                    velocity = hours_30d / 4 if hours_30d > 0 else 0
                    st.metric("Weekly Avg", f"{velocity:.1f}h")
                
                if recent_7d:
                    last_session = max(info['recent_sessions'], key=lambda x: x['date'])
                    days_ago = (now - last_session['date']).days
                    st.caption(f"🕐 Last session: {days_ago} days ago ({last_session['technology']})")
    
    st.markdown("---")
    st.markdown("### 🎯 Source Recommendations")
    
    if len(sorted_sources) > 1:
        most_efficient = max(sorted_sources, key=lambda x: x[1]['hours'] / x[1]['sessions'] if x[1]['sessions'] > 0 else 0)
        most_consistent = None
        
        for source_name, info in sorted_sources:
            if info['recent_sessions']:
                now = datetime.now()
                last_30_days = now - timedelta(days=30)
                recent = [s for s in info['recent_sessions'] if s['date'] >= last_30_days]
                if len(recent) >= 3:
                    most_consistent = (source_name, info)
                    break
        
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            st.info(f"**💡 Most Efficient:** {most_efficient[0]} ({most_efficient[1]['hours'] / most_efficient[1]['sessions']:.1f}h avg per session)")
        
        with rec_col2:
            if most_consistent:
                st.success(f"**🔥 Most Consistent:** {most_consistent[0]} (active in last 30 days)")
            else:
                st.warning("**📌 Tip:** Try to maintain consistency with at least one source")
