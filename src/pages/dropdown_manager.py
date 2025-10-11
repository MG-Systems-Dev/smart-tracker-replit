"""
Dropdown Manager Page - Centralized management of all dropdown data.
Allows users to view, edit, and delete dropdown values across the system.
Uses sync services to ensure data consistency across all tables.
"""

import streamlit as st
from src.utils.dropdowns import DropdownManager
from src.database.operations import DatabaseStorage
from src.services.sync_service import TechnologySyncService, CategorySyncService
from src.services.cached_queries import CachedQueryService
from datetime import datetime
import logging

def show_dropdown_manager_page():
    """Display the Dropdown Manager page."""
    
    # Header with MG branding
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #FFD700;">
        <h1 style="color: #FFD700; margin: 0; text-align: center;">📝 Dropdown Manager</h1>
        <p style="color: #C0C0C0; text-align: center; margin: 0.5rem 0 0 0;">Centralized Data Management Hub</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Home", help="Return to main page"):
        st.session_state.current_page = "home_v2"
        st.rerun()
    
    # Initialize database and services
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseStorage()
    
    db = st.session_state.db
    dropdown_manager = DropdownManager(db)
    tech_service = TechnologySyncService(db)
    category_service = CategorySyncService(db)
    
    st.markdown("---")
    
    # Get all dropdown data
    all_dropdowns = dropdown_manager.get_all_dropdown_data()
    
    # Create tabs for different management sections
    tabs = st.tabs([
        "📁 Manage Categories", 
        "🔧 Manage Technologies",
        "📋 Manage Dropdowns",
        "📊 Statistics"
    ])
    
    # ==================== TAB 1: MANAGE CATEGORIES ====================
    with tabs[0]:
        st.markdown("### Category Management")
        st.caption("Add, edit, and organize learning categories")
        
        # Add new category section
        st.markdown("#### ➕ Add New Category")
        with st.form("add_category_form"):
            new_category = st.text_input("Category Name", placeholder="e.g., ⚙️ DevOps, 🎨 Design, 📱 Mobile Dev")
            submitted_cat = st.form_submit_button("💾 Add Category", type="primary")
            
            if submitted_cat:
                if new_category and new_category.strip():
                    result = category_service.add_category(new_category.strip(), is_custom=True)
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        CachedQueryService.invalidate_cache()
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
                else:
                    st.error("Please enter a category name")
        
        st.markdown("---")
        
        # Manage existing categories
        st.markdown("#### 📋 Existing Categories")
        
        custom_categories = db.get_custom_categories()
        all_categories = db.get_all_categories()
        
        if not custom_categories:
            st.info("No custom categories yet. Add one above to get started!")
        else:
            st.markdown(f"**Your Custom Categories:** ({len(custom_categories)})")
            
            for cat in custom_categories:
                # Count technologies in this category
                tech_stack = db.get_all_tech_stack()
                tech_count = sum(1 for tech in tech_stack if tech.get('category') == cat)
                
                with st.expander(f"**{cat}** ({tech_count} technologies)", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("✏️ Rename", key=f"rename_cat_{cat}", use_container_width=True):
                            st.session_state.renaming_category = cat
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_cat_{cat}", use_container_width=True):
                            st.session_state.deleting_category = cat
                            st.rerun()
                    
                    with col3:
                        if st.button("🔀 Merge", key=f"merge_cat_{cat}", use_container_width=True):
                            st.session_state.merging_category = cat
                            st.rerun()
                    
                    # Rename form
                    if st.session_state.get('renaming_category') == cat:
                        with st.form(f"rename_form_{cat}"):
                            new_cat_name = st.text_input("New Category Name", value=cat)
                            col_save, col_cancel = st.columns(2)
                            
                            with col_save:
                                if st.form_submit_button("💾 Save", use_container_width=True):
                                    if new_cat_name and new_cat_name.strip():
                                        result = category_service.rename_category(cat, new_cat_name.strip())
                                        if result['success']:
                                            st.success(f"✅ {result['message']}")
                                            CachedQueryService.invalidate_cache()
                                            st.session_state.renaming_category = None
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {result['message']}")
                                    else:
                                        st.error("Please enter a valid name")
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Cancel", use_container_width=True):
                                    st.session_state.renaming_category = None
                                    st.rerun()
                    
                    # Delete confirmation
                    if st.session_state.get('deleting_category') == cat:
                        st.warning(f"⚠️ Delete category '{cat}'?")
                        if tech_count > 0:
                            st.info(f"📝 {tech_count} technologies will be moved to '❓ Uncategorized'")
                        
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("🗑️ Yes, Delete", key=f"confirm_del_cat_{cat}", use_container_width=True, type="primary"):
                                result = category_service.delete_category(cat)
                                if result['success']:
                                    st.success(f"✅ {result['message']}")
                                    CachedQueryService.invalidate_cache()
                                    st.session_state.deleting_category = None
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result['message']}")
                        
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"cancel_del_cat_{cat}", use_container_width=True):
                                st.session_state.deleting_category = None
                                st.rerun()
                    
                    # Merge form
                    if st.session_state.get('merging_category') == cat:
                        with st.form(f"merge_form_{cat}"):
                            st.caption(f"Merge '{cat}' into another category")
                            target_categories = [c for c in all_categories if c != cat]
                            merge_target = st.selectbox("Target Category", options=target_categories)
                            
                            col_merge, col_cancel = st.columns(2)
                            with col_merge:
                                if st.form_submit_button("🔀 Merge", use_container_width=True, type="primary"):
                                    if db.merge_categories(cat, merge_target):
                                        st.success(f"✅ Merged '{cat}' into '{merge_target}'")
                                        CachedQueryService.invalidate_cache()
                                        st.session_state.merging_category = None
                                        st.rerun()
                                    else:
                                        st.error("Failed to merge categories")
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Cancel", use_container_width=True):
                                    st.session_state.merging_category = None
                                    st.rerun()
    
    # ==================== TAB 2: MANAGE TECHNOLOGIES ====================
    with tabs[1]:
        st.markdown("### Technology Management")
        st.caption("Add and edit technologies in your learning stack")
        
        # Add new technology
        st.markdown("#### ➕ Add New Technology")
        
        with st.form("add_tech_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                tech_name = st.text_input("Technology Name *", placeholder="e.g., Python, React, PostgreSQL")
                goal_hours = st.number_input("Goal Hours *", min_value=1.0, value=50.0, step=5.0)
            
            with col2:
                categories = db.get_all_categories()
                category = st.selectbox("Category *", options=categories)
                date_added = st.date_input("Date Added", value=datetime.now())
            
            submitted = st.form_submit_button("💾 Add Technology", type="primary")
            
            if submitted:
                if tech_name and tech_name.strip():
                    result = tech_service.add_technology(
                        name=tech_name.strip(),
                        category=category,
                        goal_hours=goal_hours,
                        date_added=str(date_added)
                    )
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        CachedQueryService.invalidate_cache()
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
                else:
                    st.error("Please enter a technology name")
        
        st.markdown("---")
        
        # Manage existing technologies
        st.markdown("#### 📋 Current Technologies")
        
        tech_stack = db.get_all_tech_stack()
        
        if not tech_stack:
            st.info("📚 No technologies in your stack yet. Add your first one!")
        else:
            st.caption(f"Total: {len(tech_stack)} technologies")
            
            # Group by category
            by_category = {}
            for tech in tech_stack:
                cat = tech.get('category', 'Uncategorized')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(tech)
            
            # Display by category
            for category, techs in sorted(by_category.items()):
                with st.expander(f"**{category}** ({len(techs)} technologies)", expanded=False):
                    for tech in sorted(techs, key=lambda x: x['name']):
                        tech_id = tech['id']
                        tech_name = tech['name']
                        goal_hours = tech.get('goal_hours', 50)
                        date_added = tech.get('date_added', 'Unknown')
                        
                        st.markdown(f"**{tech_name}** • Goal: {goal_hours}h • Added: {date_added}")
                        
                        col_edit, col_del = st.columns(2)
                        
                        with col_edit:
                            if st.button(f"✏️ Edit", key=f"edit_{tech_id}", use_container_width=True):
                                st.session_state.editing_tech = tech_id
                                st.rerun()
                        
                        with col_del:
                            if st.button(f"🗑️ Delete", key=f"del_{tech_id}", use_container_width=True):
                                st.session_state.deleting_tech = tech_id
                                st.rerun()
                        
                        # Edit form
                        if st.session_state.get('editing_tech') == tech_id:
                            with st.form(f"edit_form_{tech_id}"):
                                st.markdown("##### Edit Technology")
                                
                                edit_name = st.text_input("Name", value=tech_name, key=f"edit_name_{tech_id}")
                                edit_category = st.selectbox("Category", options=db.get_all_categories(), 
                                                            index=db.get_all_categories().index(tech.get('category', 'Uncategorized')) if tech.get('category') in db.get_all_categories() else 0,
                                                            key=f"edit_cat_{tech_id}")
                                edit_goal = st.number_input("Goal Hours", value=float(goal_hours), min_value=1.0, step=5.0, key=f"edit_goal_{tech_id}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                        result = tech_service.update_technology(
                                            tech_id, 
                                            name=edit_name, 
                                            category=edit_category, 
                                            goal_hours=edit_goal
                                        )
                                        
                                        if result['success']:
                                            st.success(f"✅ {result['message']}")
                                            logging.info(f"Updated technology ID {tech_id}: {edit_name}")
                                            CachedQueryService.invalidate_cache()
                                            st.session_state.editing_tech = None
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {result['message']}")
                                
                                with col_cancel:
                                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                                        st.session_state.editing_tech = None
                                        st.rerun()
                        
                        # Delete confirmation
                        if st.session_state.get('deleting_tech') == tech_id:
                            result = tech_service.delete_technology(tech_id)
                            
                            if result.get('requires_confirmation'):
                                st.warning(f"⚠️ {result['message']}")
                                st.info("💡 Choose: Delete anyway (marks sessions as [Deleted]) or Cancel")
                                
                                col_force, col_cancel_del = st.columns(2)
                                
                                with col_force:
                                    if st.button("🗑️ Delete Anyway", key=f"force_del_{tech_id}", use_container_width=True, type="primary"):
                                        force_result = tech_service.force_delete_technology(tech_id)
                                        if force_result['success']:
                                            st.success(f"✅ {force_result['message']}")
                                            CachedQueryService.invalidate_cache()
                                            st.session_state.deleting_tech = None
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {force_result['message']}")
                                
                                with col_cancel_del:
                                    if st.button("❌ Cancel", key=f"cancel_force_{tech_id}", use_container_width=True):
                                        st.session_state.deleting_tech = None
                                        st.rerun()
                            else:
                                st.warning(f"⚠️ Delete {tech_name}?")
                                col_confirm, col_cancel_del = st.columns(2)
                                
                                with col_confirm:
                                    if st.button("✅ Yes, Delete", key=f"confirm_del_{tech_id}", use_container_width=True, type="primary"):
                                        if result['success']:
                                            st.success(f"🗑️ {result['message']}")
                                            logging.info(f"Deleted technology ID {tech_id}: {tech_name}")
                                            CachedQueryService.invalidate_cache()
                                            st.session_state.deleting_tech = None
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {result['message']}")
                            
                                with col_cancel_del:
                                    if st.button("❌ Cancel", key=f"cancel_del_{tech_id}", use_container_width=True):
                                        st.session_state.deleting_tech = None
                                        st.rerun()
                        
                        st.markdown("---")
    
    # ==================== TAB 3: MANAGE DROPDOWNS ====================
    with tabs[2]:
        st.markdown("### Work Items & Skills Management")
        st.caption("Pre-define work items and skills, or let them auto-populate from sessions")
        
        # ========== WORK ITEMS SECTION ==========
        st.markdown("#### 📋 Work Items")
        st.caption("Work items are linked to technologies")
        
        # Add new work item
        st.markdown("##### ➕ Add Work Item")
        
        # Category selection OUTSIDE form for cascading
        all_categories = db.get_all_categories()
        selected_category_work = st.selectbox(
            "Filter by Category",
            options=["All Categories"] + all_categories,
            key="category_filter_work_item"
        )
        
        with st.form("add_work_item_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Select parent technology - filtered by category
                all_techs_data = db.get_all_tech_stack()
                
                if selected_category_work != "All Categories":
                    filtered_techs = [tech['name'] for tech in all_techs_data if tech.get('category') == selected_category_work]
                else:
                    filtered_techs = [tech['name'] for tech in all_techs_data]
                
                if filtered_techs:
                    parent_tech = st.selectbox("Technology", options=filtered_techs)
                else:
                    if selected_category_work != "All Categories":
                        st.warning(f"⚠️ No technologies in '{selected_category_work}'")
                    else:
                        st.warning("⚠️ Add technologies first in the Manage Technologies tab")
                    parent_tech = None
            
            with col2:
                # Work item name
                work_item_name = st.text_input("Work Item Name", placeholder="e.g., Authentication, API Design")
            
            submitted_work_item = st.form_submit_button("💾 Add Work Item", type="primary")
            
            if submitted_work_item:
                if work_item_name and work_item_name.strip() and parent_tech:
                    if db.add_work_item(work_item_name.strip(), parent_tech):
                        st.success(f"✅ Added work item: {work_item_name.strip()} → {parent_tech}")
                        CachedQueryService.invalidate_cache()
                        st.rerun()
                    else:
                        st.error("❌ Work item already exists for this technology")
                else:
                    st.error("Please fill in all fields")
        
        st.markdown("---")
        
        # Show existing work items
        st.markdown("##### 📋 Existing Work Items")
        all_work_items = db.get_all_work_items()
        
        if not all_work_items:
            st.info("No manually defined work items yet. They will also auto-populate when you log sessions.")
        else:
            st.caption(f"Total: {len(all_work_items)} manually defined work items")
            
            # Group by technology
            by_tech = {}
            for item in all_work_items:
                tech = item['technology']
                if tech not in by_tech:
                    by_tech[tech] = []
                by_tech[tech].append(item)
            
            for tech, items in sorted(by_tech.items()):
                with st.expander(f"**{tech}** ({len(items)} work items)", expanded=False):
                    for item in sorted(items, key=lambda x: x['name']):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{item['name']}**")
                        with col2:
                            if st.button("🗑️", key=f"del_work_item_{item['name']}_{tech}", help="Delete this work item"):
                                if db.delete_work_item(item['name'], tech):
                                    st.success(f"Deleted: {item['name']}")
                                    CachedQueryService.invalidate_cache()
                                    st.rerun()
                                else:
                                    st.error("Failed to delete")
        
        st.markdown("---")
        st.markdown("---")
        
        # ========== SKILLS SECTION ==========
        st.markdown("#### 🎯 Skills / Topics")
        st.caption("Skills are linked to work items")
        
        # Add new skill
        st.markdown("##### ➕ Add Skill")
        
        # Cascading filters OUTSIDE form
        col_cat, col_tech = st.columns(2)
        
        with col_cat:
            selected_category_skill = st.selectbox(
                "Filter by Category",
                options=["All Categories"] + all_categories,
                key="category_filter_skill"
            )
        
        with col_tech:
            # Filter technologies by category
            all_techs_data = db.get_all_tech_stack()
            if selected_category_skill != "All Categories":
                filtered_techs_skill = [tech['name'] for tech in all_techs_data if tech.get('category') == selected_category_skill]
            else:
                filtered_techs_skill = [tech['name'] for tech in all_techs_data]
            
            if filtered_techs_skill:
                selected_tech_skill = st.selectbox(
                    "Filter by Technology",
                    options=["All Technologies"] + filtered_techs_skill,
                    key="tech_filter_skill"
                )
            else:
                st.warning("⚠️ No technologies available")
                selected_tech_skill = None
        
        with st.form("add_skill_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Select parent work item - filtered by selected technology
                all_work_items_list = db.get_all_work_items()
                
                if selected_tech_skill and selected_tech_skill != "All Technologies":
                    # Filter work items by selected technology
                    filtered_work_items = [item for item in all_work_items_list if item['technology'] == selected_tech_skill]
                else:
                    # Show all work items
                    filtered_work_items = all_work_items_list
                
                if filtered_work_items:
                    work_item_options = [f"{item['name']} ({item['technology']})" for item in filtered_work_items]
                    selected_work_item = st.selectbox("Work Item", options=work_item_options)
                    # Extract just the work item name (before parentheses)
                    parent_work_item = selected_work_item.split(" (")[0] if selected_work_item else None
                else:
                    if selected_tech_skill and selected_tech_skill != "All Technologies":
                        st.warning(f"⚠️ No work items for '{selected_tech_skill}'. Add one in the Work Items section above.")
                    else:
                        st.warning("⚠️ Add work items first above")
                    parent_work_item = None
            
            with col2:
                # Skill name
                skill_name = st.text_input("Skill Name", placeholder="e.g., JWT Tokens, OAuth2")
            
            submitted_skill = st.form_submit_button("💾 Add Skill", type="primary")
            
            if submitted_skill:
                if skill_name and skill_name.strip() and parent_work_item:
                    if db.add_skill(skill_name.strip(), parent_work_item):
                        st.success(f"✅ Added skill: {skill_name.strip()} → {parent_work_item}")
                        CachedQueryService.invalidate_cache()
                        st.rerun()
                    else:
                        st.error("❌ Skill already exists for this work item")
                else:
                    st.error("Please fill in all fields")
        
        st.markdown("---")
        
        # Show existing skills
        st.markdown("##### 🎯 Existing Skills")
        all_skills = db.get_all_skills()
        
        if not all_skills:
            st.info("No manually defined skills yet. They will also auto-populate when you log sessions.")
        else:
            st.caption(f"Total: {len(all_skills)} manually defined skills")
            
            # Group by work item
            by_work_item = {}
            for skill in all_skills:
                work_item = skill['work_item']
                if work_item not in by_work_item:
                    by_work_item[work_item] = []
                by_work_item[work_item].append(skill)
            
            for work_item, skills in sorted(by_work_item.items()):
                with st.expander(f"**{work_item}** ({len(skills)} skills)", expanded=False):
                    for skill in sorted(skills, key=lambda x: x['name']):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{skill['name']}**")
                        with col2:
                            if st.button("🗑️", key=f"del_skill_{skill['name']}_{work_item}", help="Delete this skill"):
                                if db.delete_skill(skill['name'], work_item):
                                    st.success(f"Deleted: {skill['name']}")
                                    CachedQueryService.invalidate_cache()
                                    st.rerun()
                                else:
                                    st.error("Failed to delete")
    
    # ==================== TAB 4: STATISTICS ====================
    with tabs[3]:
        st.markdown("### 📊 Data Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Categories & Technologies")
            all_categories = db.get_all_categories()
            tech_stack = db.get_all_tech_stack()
            
            st.metric("Total Categories", len(all_categories))
            st.metric("Total Technologies", len(tech_stack))
            st.metric("Custom Categories", len(db.get_custom_categories()))
        
        with col2:
            st.markdown("#### Dropdown Values")
            total_work_items = len(all_dropdowns.get('work_item', []))
            total_skills = len(all_dropdowns.get('skill_topic', []))
            total_sources = len(all_dropdowns.get('category_source', []))
            
            st.metric("Work Items", total_work_items)
            st.metric("Skills/Topics", total_skills)
            st.metric("Category Sources", total_sources)
