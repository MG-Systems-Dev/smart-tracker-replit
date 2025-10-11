"""
Unified Dropdown Manager - Handles all cascading dropdown logic.
Supports both hierarchical management (with auto-save) and simplified session entry (deferred save).
"""

import streamlit as st
from typing import List, Dict, Optional, Tuple
from src.database.operations import DatabaseStorage


class DropdownManager:
    """
    Unified dropdown manager supporting two modes:
    1. Hierarchical Management Mode (auto-save) - for Dropdown Manager page
    2. Simplified Session Entry Mode (deferred save) - for Log Session page
    """
    
    def __init__(self, db: DatabaseStorage):
        self.db = db
        
        # Define the dependency hierarchy
        self.hierarchy = {
            'category_name': {'parent': None, 'label': '📂 Category Name', 'placeholder': 'Select or type category...'},
            'technology': {'parent': 'category_name', 'label': '🔧 Technology', 'placeholder': 'Select or type technology...'},
            'work_item': {'parent': 'technology', 'label': '📋 Work Item', 'placeholder': 'Select or type work item...'},
            'skill_topic': {'parent': 'work_item', 'label': '🎯 Skill / Topic', 'placeholder': 'Select or type skill...'}
        }
        
        # Independent dropdown fields
        self.independent_fields = {
            'session_type': {'label': '📝 Session Type', 'options': ['Studying', 'Practice']},
            'category_source': {'label': '📚 Category Source', 'placeholder': 'Course, docs, project...'},
            'difficulty': {'label': '⚡ Difficulty', 'options': ['Beginner', 'Intermediate', 'Advanced', 'Expert']},
            'status': {'label': '✅ Status', 'options': ['Planned', 'In Progress', 'Completed', 'Blocked']}
        }
    
    # ========== HIERARCHICAL MANAGEMENT MODE (Auto-save) ==========
    
    def render_cascading_dropdown(
        self, 
        field_name: str, 
        parent_value: Optional[str] = None,
        key_suffix: str = "",
        allow_new: bool = True,
        auto_save: bool = True
    ) -> str:
        """
        Render a single cascading dropdown with type-to-add functionality.
        
        Args:
            field_name: Name of the dropdown field
            parent_value: Value of parent dropdown (for filtering)
            key_suffix: Unique suffix for widget keys
            allow_new: Whether to allow adding new values
            auto_save: Whether to save immediately (True) or defer (False)
        """
        
        if field_name not in self.hierarchy:
            return ""
        
        field_config = self.hierarchy[field_name]
        parent_field = field_config['parent']
        
        # Get existing values from database
        if parent_field and parent_value:
            existing_values = self.db.get_dropdown_values(field_name, parent_value)
        elif parent_field and not parent_value:
            existing_values = self.db.get_dropdown_values(field_name)
        else:
            existing_values = self.db.get_dropdown_values(field_name)
        
        # Display label
        st.markdown(f"**{field_config['label']}**")
        
        if allow_new:
            options = ["➕ Type New..."] + existing_values if existing_values else ["➕ Type New..."]
            
            help_text = None
            if parent_field and not parent_value:
                help_text = f"Select {parent_field.replace('_', ' ')} first for filtered options"
            
            selected = st.selectbox(
                f"{field_name}_dropdown_{key_suffix}",
                options=options,
                label_visibility="collapsed",
                key=f"{field_name}_select_{key_suffix}",
                help=help_text
            )
            
            if selected == "➕ Type New...":
                new_value = st.text_input(
                    f"New {field_config['label']}",
                    placeholder=field_config['placeholder'],
                    key=f"{field_name}_new_{key_suffix}",
                    label_visibility="collapsed"
                )
                
                if new_value and new_value.strip():
                    if auto_save:
                        # Auto-save mode (for Dropdown Manager)
                        if parent_field and parent_value:
                            self.db.add_dropdown_value(field_name, new_value.strip(), parent_field, parent_value)
                        else:
                            self.db.add_dropdown_value(field_name, new_value.strip())
                    else:
                        # Deferred save mode (for Session Entry)
                        pending_key = f"pending_{field_name}_{key_suffix}"
                        st.session_state[pending_key] = {
                            'field_name': field_name,
                            'field_value': new_value.strip(),
                            'parent_field': parent_field,
                            'parent_value': parent_value
                        }
                    return new_value.strip()
                return ""
            else:
                return selected
        else:
            if existing_values:
                return st.selectbox(
                    field_config['label'],
                    options=existing_values,
                    key=f"{field_name}_select_{key_suffix}"
                )
            else:
                st.info(f"No {field_config['label'].lower()} available. Add from parent dropdown.")
                return ""
    
    def render_hierarchical_form(self, key_suffix: str = "") -> Dict[str, str]:
        """Render complete hierarchical dropdown form with all fields visible (Excel-style)."""
        
        selected_values = {}
        
        # Category Name (root) - Always visible
        category = self.render_cascading_dropdown('category_name', key_suffix=key_suffix)
        selected_values['category_name'] = category
        
        # Technology (depends on Category) - Always visible, filtered by category
        technology = self.render_cascading_dropdown('technology', parent_value=category if category else None, key_suffix=key_suffix)
        selected_values['technology'] = technology
        
        # Work Item (depends on Technology) - Always visible, filtered by technology
        work_item = self.render_cascading_dropdown('work_item', parent_value=technology if technology else None, key_suffix=key_suffix)
        selected_values['work_item'] = work_item
        
        # Skill/Topic (depends on Work Item) - Always visible, filtered by work item
        skill_topic = self.render_cascading_dropdown('skill_topic', parent_value=work_item if work_item else None, key_suffix=key_suffix)
        selected_values['skill_topic'] = skill_topic
        
        return selected_values
    
    # ========== SIMPLIFIED SESSION ENTRY MODE (Deferred save) ==========
    
    def render_simplified_dropdown(
        self,
        field_name: str,
        parent_value: Optional[str] = None,
        key_suffix: str = "",
        allow_new: bool = True
    ) -> str:
        """Render cascading dropdown reading directly from source tables (no auto-save)."""
        
        if field_name not in self.hierarchy:
            return ""
        
        field_config = self.hierarchy[field_name]
        parent_field = field_config['parent']
        
        # Get existing values from source tables (not dropdowns table)
        if field_name == 'category_name':
            existing_values = self.db.get_all_categories()
        elif field_name == 'technology':
            if parent_value:
                existing_values = self.db.get_technologies_by_category(parent_value)
            else:
                existing_values = []
        elif field_name == 'work_item':
            if parent_value:
                existing_values = self.db.get_work_items_by_technology(parent_value)
            else:
                existing_values = []
        elif field_name == 'skill_topic':
            if parent_value:
                existing_values = self.db.get_skills_by_work_item(parent_value)
            else:
                existing_values = []
        else:
            existing_values = []
        
        st.markdown(f"**{field_config['label']}**")
        
        if allow_new:
            options = ["➕ Type New..."] + existing_values if existing_values else ["➕ Type New..."]
            
            help_text = None
            if parent_field and not parent_value:
                help_text = f"Select {parent_field.replace('_', ' ')} first for filtered options"
            
            selected = st.selectbox(
                f"{field_name}_dropdown_{key_suffix}",
                options=options,
                label_visibility="collapsed",
                key=f"{field_name}_select_{key_suffix}",
                help=help_text
            )
            
            if selected == "➕ Type New...":
                new_value = st.text_input(
                    f"New {field_config['label']}",
                    placeholder=field_config['placeholder'],
                    key=f"{field_name}_new_{key_suffix}",
                    label_visibility="collapsed"
                )
                
                # Store in session state for later save (NO AUTO-SAVE)
                if new_value and new_value.strip():
                    pending_key = f"pending_{field_name}_{key_suffix}"
                    st.session_state[pending_key] = {
                        'field_name': field_name,
                        'field_value': new_value.strip(),
                        'parent_field': parent_field,
                        'parent_value': parent_value
                    }
                    return new_value.strip()
                return ""
            else:
                return selected
        else:
            if existing_values:
                return st.selectbox(
                    field_config['label'],
                    options=existing_values,
                    key=f"{field_name}_select_{key_suffix}"
                )
            else:
                st.info(f"No {field_config['label'].lower()} available. Add from parent dropdown.")
                return ""
    
    def render_simplified_form(self, key_suffix: str = "", selected_category: str = "") -> Dict[str, str]:
        """
        Render simplified form - ALL options shown, NO parent filtering.
        Relationships are auto-paired in the background from database lookups.
        
        Args:
            key_suffix: Unique suffix for widget keys
            selected_category: Pre-selected category (from outside form for reactivity)
        """
        
        selected_values = {}
        
        # Store the category passed from outside the form
        selected_values['category_name'] = selected_category
        
        # Technology - Show ALL, optionally filtered by selected category
        st.markdown("**🔧 Technology**")
        
        all_techs_data = self.db.get_all_tech_stack()
        
        if selected_category:
            # Filter by selected category
            filtered_techs = [tech['name'] for tech in all_techs_data if tech.get('category') == selected_category]
        else:
            # Show ALL technologies if no category selected
            filtered_techs = [tech['name'] for tech in all_techs_data]
        
        if filtered_techs:
            # Add index parameter to reset when category changes
            default_index = 0
            # Check if previously selected tech is still in filtered list
            prev_tech_key = f"prev_tech_{key_suffix}"
            if prev_tech_key in st.session_state and st.session_state[prev_tech_key] in filtered_techs:
                try:
                    default_index = filtered_techs.index(st.session_state[prev_tech_key])
                except ValueError:
                    default_index = 0
            
            technology = st.selectbox(
                "technology_dropdown",
                options=filtered_techs,
                index=default_index,
                key=f"technology_simple_{key_suffix}",
                label_visibility="collapsed",
                help=f"Technologies in '{selected_category}'" if selected_category else "All technologies (select category to filter)"
            )
            selected_values['technology'] = technology
            st.session_state[prev_tech_key] = technology
        else:
            if selected_category:
                st.warning(f"⚠️ No technologies found for '{selected_category}'. Add them in Dropdown Manager first.")
            else:
                st.warning("⚠️ No technologies available. Add them in Dropdown Manager first.")
            selected_values['technology'] = ''
        
        # Work Item - Show ALL work items (no technology filter) 
        st.markdown("**📋 Work Item**")
        all_work_items = []
        all_techs_list = [tech['name'] for tech in self.db.get_all_tech_stack()]
        for tech in all_techs_list:
            all_work_items.extend(self.db.get_work_items_by_technology(tech))
        all_work_items = sorted(list(set(all_work_items)))
        
        if all_work_items:
            work_item = st.selectbox(
                "work_item_dropdown",
                options=[""] + all_work_items,
                key=f"work_item_simple_{key_suffix}",
                label_visibility="collapsed",
                help="Select a work item or leave empty"
            )
            selected_values['work_item'] = work_item if work_item else ''
        else:
            selected_values['work_item'] = ''
        
        # Skill/Topic - FILTERED by selected work item (or show all if no work item selected)
        st.markdown("**🎯 Skill / Topic**")
        
        # Get skills based on selected work item
        selected_work_item = selected_values.get('work_item', '')
        if selected_work_item:
            # Show only skills for the selected work item
            filtered_skills = self.db.get_skills_by_work_item(selected_work_item)
            filtered_skills = sorted(list(set(filtered_skills)))
        else:
            # No work item selected - show ALL skills
            all_skills = []
            for tech in all_techs_list:
                work_items_for_tech = self.db.get_work_items_by_technology(tech)
                for wi in work_items_for_tech:
                    all_skills.extend(self.db.get_skills_by_work_item(wi))
            filtered_skills = sorted(list(set(all_skills)))
        
        if filtered_skills:
            skill = st.selectbox(
                "skill_dropdown",
                options=[""] + filtered_skills,
                key=f"skill_simple_{key_suffix}",
                label_visibility="collapsed",
                help="Select a skill/topic (filtered by work item)" if selected_work_item else "Select a skill/topic"
            )
            selected_values['skill_topic'] = skill if skill else ''
        else:
            # Allow manual entry if no skills in database
            st.info("💡 No skills found. Enter a custom skill below:")
            custom_skill = st.text_input(
                "Custom skill",
                key=f"custom_skill_{key_suffix}",
                label_visibility="collapsed",
                placeholder="Enter skill/topic name..."
            )
            selected_values['skill_topic'] = custom_skill if custom_skill else ''
        
        return selected_values
    
    def render_independent_dropdown(self, field_name: str, key_suffix: str = "") -> str:
        """Render independent dropdown fields (not part of hierarchy)."""
        
        if field_name not in self.independent_fields:
            return ""
        
        field_config = self.independent_fields[field_name]
        
        if 'options' in field_config:
            # Fixed options dropdown
            return st.selectbox(
                field_config['label'],
                options=field_config['options'],
                key=f"{field_name}_{key_suffix}"
            )
        else:
            # Text input with placeholder
            return st.text_input(
                field_config['label'],
                placeholder=field_config.get('placeholder', ''),
                key=f"{field_name}_{key_suffix}"
            )
    
    def save_pending_dropdowns(self, key_suffix: str = "") -> int:
        """Save all pending dropdown values stored in session state. Returns count of saved items."""
        
        saved_count = 0
        pending_keys = [k for k in st.session_state.keys() if isinstance(k, str) and k.startswith(f'pending_') and k.endswith(f'_{key_suffix}')]
        
        for pending_key in pending_keys:
            pending_data = st.session_state[pending_key]
            field_name = pending_data['field_name']
            field_value = pending_data['field_value']
            parent_field = pending_data.get('parent_field')
            parent_value = pending_data.get('parent_value')
            
            if parent_field and parent_value:
                self.db.add_dropdown_value(field_name, field_value, parent_field, parent_value)
            else:
                self.db.add_dropdown_value(field_name, field_value)
            
            saved_count += 1
            del st.session_state[pending_key]
        
        return saved_count
    
    def get_all_dropdown_data(self) -> Dict[str, List[str]]:
        """Get all dropdown data organized by field name for statistics view."""
        dropdown_data = {}
        
        for field_name in self.hierarchy.keys():
            dropdown_data[field_name] = self.db.get_dropdown_values(field_name)
        
        for field_name in self.independent_fields.keys():
            if 'options' not in self.independent_fields[field_name]:
                dropdown_data[field_name] = self.db.get_dropdown_values(field_name)
        
        return dropdown_data
