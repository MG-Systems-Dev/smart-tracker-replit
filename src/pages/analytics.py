"""
Analytics Dashboard Page - Advanced data analysis and KPI breakdowns.
Shows detailed metrics for categories, technologies, and work items.
"""

import streamlit as st
from src.core.app import get_database
from src.services.cached_queries import CachedQueryService
from src.utils.navigation import navigate_to

def show_analytics_page():
    """Display the Analytics Dashboard page."""
    
    # Header with MG branding
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #FFD700;">
        <h1 style="color: #FFD700; margin: 0; text-align: center;">📊 Analytics Dashboard</h1>
        <p style="color: #C0C0C0; text-align: center; margin: 0.5rem 0 0 0;">Advanced Performance Metrics & Data Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Home", help="Return to main page"):
        navigate_to("home_v2")
    
    # Initialize database (singleton)
    db = get_database()
    
    st.markdown("---")
    
    # ==================== CATEGORIES ANALYTICS ====================
    st.markdown("### 📂 Categories Analytics")
    st.caption("Time distribution and technology breakdown by category")
    
    categories_data = CachedQueryService.get_category_analytics(db)
    
    if categories_data:
        # Sort by total hours descending
        categories_data.sort(key=lambda x: x['total_hours'], reverse=True)
        
        for cat_data in categories_data:
            with st.expander(f"📂 {cat_data['category']} - {cat_data['total_hours']:.1f}h total", expanded=False):
                # Category KPI metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Hours", f"{cat_data['total_hours']:.1f}h")
                
                with col2:
                    st.metric("Total Sessions", cat_data['total_sessions'])
                
                # Practice vs Studying for this category
                cat_sessions = [s for s in db.get_all_sessions() if s.get('category_name') == cat_data['category']]
                studying_h = sum(s.get('hours_spent', 0) for s in cat_sessions if s.get('session_type') == 'Studying')
                practice_h = sum(s.get('hours_spent', 0) for s in cat_sessions if s.get('session_type') == 'Practice')
                total_t = studying_h + practice_h
                
                with col3:
                    if total_t > 0:
                        studying_pct = (studying_h / total_t * 100)
                        practice_pct = (practice_h / total_t * 100)
                        st.metric("📊 Type Split", f"📚 {studying_pct:.0f}% / 💪 {practice_pct:.0f}%")
                
                st.markdown("---")
                st.markdown("**🔧 Technology Breakdown:**")
                
                # Technology breakdown cards
                for tech in cat_data['technologies']:
                    tech_pct = (tech['hours'] / cat_data['total_hours'] * 100) if cat_data['total_hours'] > 0 else 0
                    
                    st.markdown(f"""
                    <div style="background: #16213e; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #FFD700;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <p style="color: #FFD700; margin: 0; font-weight: bold;">{tech['name']}</p>
                                <p style="color: #C0C0C0; margin: 0.3rem 0 0 0; font-size: 0.9rem;">{tech['sessions']} sessions</p>
                            </div>
                            <div style="text-align: right;">
                                <p style="color: #FFD700; margin: 0; font-size: 1.2rem; font-weight: bold;">{tech['hours']:.1f}h</p>
                                <p style="color: #C0C0C0; margin: 0.3rem 0 0 0; font-size: 0.9rem;">{tech_pct:.1f}%</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("📚 No category data available. Start logging sessions to see analytics!")
    
    st.markdown("---")
    
    # ==================== TECHNOLOGIES ANALYTICS ====================
    st.markdown("### 🔧 Technologies Analytics")
    st.caption("Work item distribution and performance metrics by technology")
    
    technologies_data = CachedQueryService.get_technology_analytics(db)
    
    if technologies_data:
        # Sort by total hours descending
        technologies_data.sort(key=lambda x: x['total_hours'], reverse=True)
        
        for tech_data in technologies_data:
            with st.expander(f"🔧 {tech_data['technology']} ({tech_data['category']}) - {tech_data['total_hours']:.1f}h total", expanded=False):
                # Technology KPI metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Hours", f"{tech_data['total_hours']:.1f}h")
                
                with col2:
                    st.metric("Total Sessions", tech_data['total_sessions'])
                
                with col3:
                    st.markdown(f"**Category**")
                    st.caption(tech_data['category'])
                
                # Study vs Practice for this technology
                tech_sessions = [s for s in db.get_all_sessions() if s.get('technology') == tech_data['technology']]
                studying_h = sum(s.get('hours_spent', 0) for s in tech_sessions if s.get('session_type') == 'Studying')
                practice_h = sum(s.get('hours_spent', 0) for s in tech_sessions if s.get('session_type') == 'Practice')
                total_typed = studying_h + practice_h
                
                with col4:
                    if total_typed > 0:
                        studying_pct = (studying_h / total_typed * 100)
                        practice_pct = (practice_h / total_typed * 100)
                        st.metric("📊 Type Split", f"📚 {studying_pct:.0f}% / 💪 {practice_pct:.0f}%")
                
                st.markdown("---")
                st.markdown("**📋 Work Item Breakdown:**")
                
                # Work item breakdown cards
                for item in tech_data['work_items']:
                    item_pct = (item['hours'] / tech_data['total_hours'] * 100) if tech_data['total_hours'] > 0 else 0
                    
                    # Calculate study vs practice for this work item
                    work_item_sessions = [s for s in tech_sessions if s.get('work_item') == item['name']]
                    wi_studying_h = sum(s.get('hours_spent', 0) for s in work_item_sessions if s.get('session_type') == 'Studying')
                    wi_practice_h = sum(s.get('hours_spent', 0) for s in work_item_sessions if s.get('session_type') == 'Practice')
                    wi_total = wi_studying_h + wi_practice_h
                    wi_study_pct = (wi_studying_h / wi_total * 100) if wi_total > 0 else 0
                    wi_practice_pct = (wi_practice_h / wi_total * 100) if wi_total > 0 else 0
                    
                    st.markdown(f"""
                    <div style="background: #16213e; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #FFD700;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <p style="color: #FFD700; margin: 0; font-weight: bold;">{item['name']}</p>
                                <p style="color: #C0C0C0; margin: 0.3rem 0 0 0; font-size: 0.9rem;">{item['sessions']} sessions • 📚 {wi_study_pct:.0f}% / 💪 {wi_practice_pct:.0f}%</p>
                            </div>
                            <div style="text-align: right;">
                                <p style="color: #FFD700; margin: 0; font-size: 1.2rem; font-weight: bold;">{item['hours']:.1f}h</p>
                                <p style="color: #C0C0C0; margin: 0.3rem 0 0 0; font-size: 0.9rem;">{item_pct:.1f}%</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("📚 No technology data available. Start logging sessions to see analytics!")
    
    st.markdown("---")
    
    # ==================== WORK ITEMS ANALYTICS ====================
    st.markdown("### 📋 Work Items Analytics")
    st.caption("Skill breakdown and session type distribution by work item")
    
    work_items_data = CachedQueryService.get_work_item_analytics(db)
    
    if work_items_data:
        # Group work items by technology
        work_items_by_tech = {}
        for item_data in work_items_data:
            tech = item_data['technology']
            if tech not in work_items_by_tech:
                work_items_by_tech[tech] = []
            work_items_by_tech[tech].append(item_data)
        
        # Display grouped by technology
        for tech, items in sorted(work_items_by_tech.items()):
            tech_total_hours = sum(item['total_hours'] for item in items)
            tech_total_sessions = sum(item['total_sessions'] for item in items)
            
            with st.expander(f"🔧 **{tech}** ({len(items)} work items, {tech_total_hours:.1f}h)", expanded=False):
                # Sort items by hours
                items.sort(key=lambda x: x['total_hours'], reverse=True)
                
                for item_data in items:
                    with st.expander(f"📋 {item_data['work_item']} - {item_data['total_hours']:.1f}h total", expanded=False):
                        # Work item KPI metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Hours", f"{item_data['total_hours']:.1f}h")
                        
                        with col2:
                            st.metric("Sessions", item_data['total_sessions'])
                        
                        with col3:
                            study_pct = (item_data['studying_hours'] / item_data['total_hours'] * 100) if item_data['total_hours'] > 0 else 0
                            st.metric("📚 Studying", f"{item_data['studying_hours']:.1f}h ({study_pct:.0f}%)")
                        
                        with col4:
                            practice_pct = (item_data['practice_hours'] / item_data['total_hours'] * 100) if item_data['total_hours'] > 0 else 0
                            st.metric("💪 Practice", f"{item_data['practice_hours']:.1f}h ({practice_pct:.0f}%)")
                        
                        st.markdown("---")
                        st.markdown(f"**🎯 Skills Practiced:**")
                        
                        # Skill breakdown cards
                        for skill in item_data['skills']:
                            skill_pct = (skill['hours'] / item_data['total_hours'] * 100) if item_data['total_hours'] > 0 else 0
                            
                            # Calculate study vs practice for this skill
                            skill_sessions = [s for s in db.get_all_sessions() if s.get('work_item') == item_data['work_item'] and s.get('skill_topic') == skill['name']]
                            skill_studying_h = sum(s.get('hours_spent', 0) for s in skill_sessions if s.get('session_type') == 'Studying')
                            skill_practice_h = sum(s.get('hours_spent', 0) for s in skill_sessions if s.get('session_type') == 'Practice')
                            skill_total = skill_studying_h + skill_practice_h
                            skill_study_pct = (skill_studying_h / skill_total * 100) if skill_total > 0 else 0
                            skill_practice_pct = (skill_practice_h / skill_total * 100) if skill_total > 0 else 0
                            
                            st.markdown(f"""
                            <div style="background: #16213e; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #FFD700;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <p style="color: #FFD700; margin: 0; font-weight: bold;">{skill['name']}</p>
                                        <p style="color: #C0C0C0; margin: 0.3rem 0 0 0; font-size: 0.9rem;">{skill['sessions']} sessions • 📚 {skill_study_pct:.0f}% / 💪 {skill_practice_pct:.0f}%</p>
                                    </div>
                                    <div style="text-align: right;">
                                        <p style="color: #FFD700; margin: 0; font-size: 1.2rem; font-weight: bold;">{skill['hours']:.1f}h</p>
                                        <p style="color: #C0C0C0; margin: 0.3rem 0 0 0; font-size: 0.9rem;">{skill_pct:.1f}%</p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
    else:
        st.info("📚 No work item data available. Start logging sessions with work items to see analytics!")
    
    st.markdown("---")
    
    # Summary stats
    st.markdown("### 📈 Summary Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Categories Tracked", len(categories_data))
    
    with col2:
        st.metric("Technologies Analyzed", len(technologies_data))
    
    with col3:
        st.metric("Work Items Monitored", len(work_items_data))
