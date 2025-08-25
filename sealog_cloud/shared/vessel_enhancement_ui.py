"""
Vessel Enhancement UI Components - FIXED VERSION
User interface components for vessel data enhancement and merging

This module provides UI components for vessel enhancement including
"Find on BOAT International" and "Enrich from MarineTraffic" buttons,
data preview interfaces, and merge conflict resolution.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Tuple
import logging
import json

from shared.vessel_enhancement import VesselEnhancementService, EnhancementOpportunity, EnhancementResult
from shared.vessel_merge import VesselDataMerger, MergeResult, MergeConflict
from shared.vessel_service import VesselService

logger = logging.getLogger(__name__)

# ============================================================================
# ENHANCED SESSION STATE MANAGEMENT
# ============================================================================

class EnhancementSessionManager:
    """Manages session state for vessel enhancement operations"""
    
    @staticmethod
    def set_current_vessel(vessel_id: str):
        """Set the current vessel being enhanced"""
        st.session_state['enhancement_current_vessel_id'] = vessel_id
    
    @staticmethod
    def get_current_vessel() -> Optional[str]:
        """Get the current vessel ID being enhanced"""
        return st.session_state.get('enhancement_current_vessel_id')
    
    @staticmethod
    def set_enhancement_request(key: str, request_data: Dict[str, Any]):
        """Set enhancement request data"""
        st.session_state[f'enhancement_request_{key}'] = request_data
    
    @staticmethod
    def get_enhancement_request(key: str) -> Optional[Dict[str, Any]]:
        """Get enhancement request data"""
        return st.session_state.get(f'enhancement_request_{key}')
    
    @staticmethod
    def clear_enhancement_request(key: str):
        """Clear enhancement request data"""
        session_key = f'enhancement_request_{key}'
        if session_key in st.session_state:
            del st.session_state[session_key]
    
    @staticmethod
    def clear_all_enhancement_data():
        """Clear all enhancement-related session data"""
        keys_to_remove = [
            key for key in st.session_state.keys() 
            if key.startswith('enhancement_')
        ]
        for key in keys_to_remove:
            del st.session_state[key]

# ============================================================================
# ENHANCEMENT OPPORTUNITY UI
# ============================================================================

def render_enhancement_opportunities(
    vessel_id: str,
    enhancement_service: VesselEnhancementService,
    key: str = "enhancement_opportunities"
) -> Optional[str]:
    """
    Render available enhancement opportunities for a vessel
    
    Args:
        vessel_id: Vessel ID
        enhancement_service: VesselEnhancementService instance
        key: Unique key for the component
        
    Returns:
        Action string if enhancement requested, None otherwise
    """
    try:
        # Set current vessel in session
        EnhancementSessionManager.set_current_vessel(vessel_id)
        
        # Get enhancement opportunities
        opportunities = enhancement_service.get_enhancement_opportunities(vessel_id)
        
        if not opportunities:
            st.info(" No enhancement opportunities found for this vessel")
            st.markdown("*Enhancement opportunities are identified based on available vessel identifiers (IMO, MMSI, name)*")
            return None
        
        st.subheader(" Available Enhancements")
        st.markdown(f"*Found {len(opportunities)} enhancement opportunity(s)*")
        
        # Display opportunities
        for i, opportunity in enumerate(opportunities):
            with st.expander(f" {opportunity.description}", expanded=i == 0):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Source:** {opportunity.source.value.replace('_', ' ').title()}")
                    st.write(f"**Identifier:** {opportunity.identifier_type.upper()} = {opportunity.identifier_value}")
                    st.write(f"**Confidence:** {opportunity.confidence:.0%}")
                    st.write(f"**Estimated fields:** {opportunity.estimated_fields}")
                
                with col2:
                    if st.button(
                        f" Enhance Now",
                        key=f"{key}_enhance_{i}",
                        use_container_width=True,
                        type="primary"
                    ):
                        # Store enhancement request in session state
                        EnhancementSessionManager.set_enhancement_request(key, {
                            'vessel_id': vessel_id,
                            'source': opportunity.source.value,
                            'identifier_type': opportunity.identifier_type,
                            'identifier_value': opportunity.identifier_value,
                            'opportunity': opportunity
                        })
                        return f"enhance_{opportunity.source.value}"
        
        return None
        
    except Exception as e:
        logger.error(f"Error rendering enhancement opportunities: {e}")
        st.error(f" Error loading enhancement opportunities: {str(e)}")
        return None

def render_enhancement_buttons(
    vessel_id: str,
    vessel_data: Dict[str, Any],
    enhancement_service: VesselEnhancementService,
    key: str = "enhancement_buttons"
) -> Optional[str]:
    """
    Render quick enhancement buttons for common sources
    
    Args:
        vessel_id: Vessel ID
        vessel_data: Vessel data dictionary
        enhancement_service: VesselEnhancementService instance
        key: Unique key for the component
        
    Returns:
        Action string if enhancement requested, None otherwise
    """
    # Set current vessel in session
    EnhancementSessionManager.set_current_vessel(vessel_id)
    
    st.markdown("###  Quick Enhancement")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # MarineTraffic enhancement
        can_enhance_mt = bool(vessel_data.get('imo_number') or vessel_data.get('mmsi_number'))
        mt_disabled = not (enhancement_service.external_apis.marinetraffic.api_key and can_enhance_mt)
        
        if st.button(
            " MarineTraffic",
            key=f"{key}_marinetraffic",
            use_container_width=True,
            disabled=mt_disabled,
            help="Enhance from MarineTraffic using IMO or MMSI"
        ):
            identifier_type = 'imo' if vessel_data.get('imo_number') else 'mmsi'
            identifier_value = vessel_data.get('imo_number') or vessel_data.get('mmsi_number')
            
            EnhancementSessionManager.set_enhancement_request(key, {
                'vessel_id': vessel_id,
                'source': 'marinetraffic',
                'identifier_type': identifier_type,
                'identifier_value': identifier_value
            })
            return "enhance_marinetraffic"
        
        if mt_disabled:
            if not enhancement_service.external_apis.marinetraffic.api_key:
                st.caption(" API key required")
            else:
                st.caption(" IMO/MMSI required")
    
    with col2:
        # BOAT International enhancement
        can_enhance_bi = bool(vessel_data.get('vessel_name') and 
                             vessel_data.get('vessel_type') in ['yacht', 'motor_yacht', 'sailing_yacht', 'superyacht'])
        
        if st.button(
            " BOAT International",
            key=f"{key}_boat_international",
            use_container_width=True,
            disabled=not can_enhance_bi,
            help="Search BOAT International for yacht data"
        ):
            EnhancementSessionManager.set_enhancement_request(key, {
                'vessel_id': vessel_id,
                'source': 'boat_international',
                'identifier_type': 'name',
                'identifier_value': vessel_data.get('vessel_name')
            })
            return "enhance_boat_international"
        
        if not can_enhance_bi:
            st.caption(" Yacht name required")
    
    with col3:
        # Auto-enhance button
        if st.button(
            " Auto-Enhance",
            key=f"{key}_auto_enhance",
            use_container_width=True,
            help="Automatically enhance using best available source"
        ):
            EnhancementSessionManager.set_enhancement_request(key, {
                'vessel_id': vessel_id,
                'source': 'auto'
            })
            return "enhance_auto"
    
    return None

# ============================================================================
# ENHANCEMENT EXECUTION UI
# ============================================================================

def render_enhancement_execution(
    enhancement_service: VesselEnhancementService,
    vessel_service: VesselService,
    user_id: str,
    key: str = "enhancement_execution"
) -> bool:
    """
    Render enhancement execution interface
    
    Args:
        enhancement_service: VesselEnhancementService instance
        vessel_service: VesselService instance
        user_id: User ID
        key: Unique key for the component
        
    Returns:
        True if enhancement was completed
    """
    # Check for enhancement request
    enhance_request = EnhancementSessionManager.get_enhancement_request(key)
    if not enhance_request:
        st.error(" No enhancement request found in session")
        return False
    
    vessel_id = enhance_request.get('vessel_id')
    if not vessel_id:
        st.error(" No vessel ID found in enhancement request")
        return False
    
    st.subheader(" Enhancing Vessel Data")
    
    # Progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Execute enhancement based on source
        source = enhance_request.get('source')
        
        if source == 'marinetraffic':
            status_text.text(" Fetching data from MarineTraffic...")
            progress_bar.progress(25)
            
            identifier_type = enhance_request.get('identifier_type', 'imo')
            identifier_value = enhance_request.get('identifier_value', '')
            
            enhancement_result = enhancement_service.enhance_vessel_from_marinetraffic(
                vessel_id, identifier_type, identifier_value
            )
            
        elif source == 'boat_international':
            status_text.text(" Searching BOAT International...")
            progress_bar.progress(25)
            
            yacht_name = enhance_request.get('identifier_value', '')
            enhancement_result = enhancement_service.enhance_vessel_from_boat_international(
                vessel_id, yacht_name
            )

        elif source == 'auto':
            status_text.text(" Auto-selecting best source...")
            progress_bar.progress(10)
            
            # Get opportunities and use the best one
            opportunities = enhancement_service.get_enhancement_opportunities(vessel_id)
            if not opportunities:
                st.error(" No enhancement opportunities found")
                return False
            
            # Use highest confidence opportunity
            best_opportunity = opportunities[0]
            
            status_text.text(f" Enhancing from {best_opportunity.source.value}...")
            progress_bar.progress(25)
            
            if best_opportunity.source.value == 'marinetraffic':
                enhancement_result = enhancement_service.enhance_vessel_from_marinetraffic(
                    vessel_id, 
                    best_opportunity.identifier_type, 
                    best_opportunity.identifier_value
                )
            else:
                enhancement_result = enhancement_service.enhance_vessel_from_boat_international(
                    vessel_id, 
                    best_opportunity.identifier_value
                )

        elif 'opportunity' in enhance_request:
            # From opportunity selection (fallback)
            opportunity = enhance_request['opportunity']
            status_text.text(f" Enhancing from {opportunity.source.value}...")
            progress_bar.progress(25)
            
            if opportunity.source.value == 'marinetraffic':
                enhancement_result = enhancement_service.enhance_vessel_from_marinetraffic(
                    vessel_id, opportunity.identifier_type, opportunity.identifier_value
                )
            else:
                enhancement_result = enhancement_service.enhance_vessel_from_boat_international(
                    vessel_id, opportunity.identifier_value
                )

        else:
            st.error(" Invalid enhancement request - missing source information")
            return False
        
        progress_bar.progress(50)
        status_text.text(" Processing enhancement data...")
        
        # Handle enhancement result
        if not enhancement_result.success:
            st.error(f" Enhancement failed: {enhancement_result.error_message}")
            return False
        
        progress_bar.progress(75)
        status_text.text(" Analyzing data conflicts...")
        
        # Show enhancement preview
        completed = render_enhancement_preview(
            enhancement_result,
            vessel_service,
            user_id,
            key=f"{key}_preview"
        )
        
        progress_bar.progress(100)
        status_text.text(" Enhancement ready for review")
        
        return completed
        
    except Exception as e:
        logger.error(f"Error in enhancement execution: {e}")
        st.error(f" Enhancement error: {str(e)}")
        return False
    
    finally:
        # Clear enhancement request
        EnhancementSessionManager.clear_enhancement_request(key)

def render_enhancement_preview(
    enhancement_result: EnhancementResult,
    vessel_service: VesselService,
    user_id: str,
    key: str = "enhancement_preview"
) -> bool:
    """
    Render enhancement preview with conflict resolution
    
    Args:
        enhancement_result: EnhancementResult to preview
        vessel_service: VesselService instance
        user_id: User ID
        key: Unique key for the component
        
    Returns:
        True if enhancement was applied
    """
    st.subheader(" Enhancement Preview")
    
    # Show summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Fields Found", len(enhancement_result.fields_updated))
    
    with col2:
        st.metric("Source", enhancement_result.source.value.replace('_', ' ').title())
    
    with col3:
        conflict_count = len(enhancement_result.conflicts)
        st.metric("Conflicts", conflict_count, delta=None if conflict_count == 0 else "")
    
    # Show new data
    if enhancement_result.new_data:
        st.markdown("###  New Data Found")
        
        # Organize data by category
        basic_fields = ['vessel_name', 'vessel_type', 'flag_state', 'call_sign']
        dimension_fields = ['length_overall', 'beam', 'draft', 'gross_tonnage', 'year_built']
        yacht_fields = ['guest_capacity', 'crew_capacity', 'max_speed', 'cruise_speed']
        
        tab1, tab2, tab3, tab4 = st.tabs(["Basic Info", "Dimensions", "Yacht Details", "All Fields"])
        
        with tab1:
            render_data_fields(enhancement_result.new_data, basic_fields, "Basic Information")
        
        with tab2:
            render_data_fields(enhancement_result.new_data, dimension_fields, "Dimensions")
        
        with tab3:
            render_data_fields(enhancement_result.new_data, yacht_fields, "Yacht Details")
        
        with tab4:
            render_data_fields(enhancement_result.new_data, None, "All Fields")
    
    # Show conflicts if any
    if enhancement_result.conflicts:
        st.markdown("###  Data Conflicts")
        st.markdown("*The following fields have different values between existing and new data:*")
        
        conflicts_resolved = render_conflict_resolution(
            enhancement_result.conflicts,
            key=f"{key}_conflicts"
        )
        
        if not conflicts_resolved:
            st.info(" Please resolve conflicts above before applying enhancement")
            return False
    
    # Field selection
    st.markdown("###  Select Fields to Update")
    
    selected_fields = []
    
    # Group fields for selection
    field_groups = {
        "Basic Information": ['vessel_name', 'vessel_type', 'flag_state', 'call_sign'],
        "Dimensions": ['length_overall', 'beam', 'draft', 'gross_tonnage', 'year_built'],
        "Builder Information": ['builder', 'build_location', 'hull_material'],
        "Yacht Details": ['guest_capacity', 'crew_capacity', 'max_speed', 'cruise_speed', 'range_nm'],
        "Other": []
    }
    
    # Categorize fields
    categorized_fields = set()
    for group_fields in field_groups.values():
        categorized_fields.update(group_fields)
    
    # Add uncategorized fields to "Other"
    for field in enhancement_result.fields_updated:
        if field not in categorized_fields:
            field_groups["Other"].append(field)
    
    # Remove empty groups
    field_groups = {k: v for k, v in field_groups.items() if v}
    
    # Render field selection
    for group_name, group_fields in field_groups.items():
        available_fields = [f for f in group_fields if f in enhancement_result.fields_updated]
        
        if available_fields:
            st.markdown(f"**{group_name}**")
            
            # Group select all checkbox
            select_all = st.checkbox(f"Select all {group_name.lower()}", key=f"{key}_select_all_{group_name}")
            
            # Individual field checkboxes
            for field in available_fields:
                field_display = field.replace('_', ' ').title()
                new_value = enhancement_result.new_data.get(field, 'N/A')
                
                # Show conflict indicator
                conflict_indicator = ""
                if any(c.field_name == field for c in enhancement_result.conflicts):
                    conflict_indicator = " "
                
                selected = st.checkbox(
                    f"{field_display}{conflict_indicator}: {new_value}",
                    value=select_all,
                    key=f"{key}_field_{field}"
                )
                
                if selected:
                    selected_fields.append(field)
    
    # Apply enhancement
    if selected_fields:
        st.markdown("###  Apply Enhancement")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.info(f" Ready to update {len(selected_fields)} field(s)")
        
        with col2:
            if st.button(
                "Apply Enhancement",
                key=f"{key}_apply",
                type="primary",
                use_container_width=True
            ):
                # Apply enhancement
                vessel_id = EnhancementSessionManager.get_current_vessel()
                if not vessel_id:
                    st.error(" No vessel ID found in session")
                    return False
                
                success, message = enhancement_service.apply_enhancement(
                    vessel_id,
                    enhancement_result,
                    user_id,
                    selected_fields
                )
                
                if success:
                    st.success(f" {message}")
                    st.balloons()
                    
                    # Log enhancement
                    enhancement_service.log_enhancement(
                        vessel_id,
                        enhancement_result.source,
                        selected_fields,
                        user_id
                    )
                    
                    # Clear session data
                    EnhancementSessionManager.clear_all_enhancement_data()
                    
                    return True
                else:
                    st.error(f" {message}")
                    return False
    else:
        st.info(" Select fields to update above")
    
    return False

# ============================================================================
# CONFLICT RESOLUTION UI
# ============================================================================

def render_conflict_resolution(
    conflicts: List[MergeConflict],
    key: str = "conflict_resolution"
) -> bool:
    """
    Render conflict resolution interface
    
    Args:
        conflicts: List of conflicts to resolve
        key: Unique key for the component
        
    Returns:
        True if all conflicts are resolved
    """
    resolved_count = 0
    
    for i, conflict in enumerate(conflicts):
        st.markdown(f"####  Conflict: {conflict.field_name.replace('_', ' ').title()}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Current Value**")
            st.code(str(conflict.existing_value))
            st.caption(f"Source: {conflict.existing_source} (Reliability: {conflict.existing_reliability.name})")
        
        with col2:
            st.markdown("**New Value**")
            st.code(str(conflict.new_value))
            st.caption(f"Source: {conflict.new_source} (Reliability: {conflict.new_reliability.name})")
        
        # Resolution options
        resolution_options = [
            "Select resolution...",
            f"Keep current ({conflict.existing_value})",
            f"Use new ({conflict.new_value})"
        ]
        
        # Add custom option for manual entry
        if conflict.field_type in ['string', 'text']:
            resolution_options.append("Enter custom value")
        
        # Show suggested resolution
        if hasattr(conflict, 'suggested_resolution'):
            st.info(f" Suggested: {conflict.suggested_resolution} (Confidence: {conflict.confidence:.0%})")
        
        resolution_choice = st.selectbox(
            f"Resolution for {conflict.field_name}",
            options=resolution_options,
            key=f"{key}_resolution_{i}"
        )
        
        if resolution_choice != "Select resolution...":
            if resolution_choice == "Enter custom value":
                custom_value = st.text_input(
                    f"Custom value for {conflict.field_name}",
                    key=f"{key}_custom_{i}"
                )
                if custom_value:
                    resolved_count += 1
            else:
                resolved_count += 1
        
        st.markdown("---")
    
    return resolved_count == len(conflicts)

def render_data_fields(
    data: Dict[str, Any],
    field_list: Optional[List[str]] = None,
    title: str = "Data Fields"
) -> None:
    """
    Render data fields in a formatted way
    
    Args:
        data: Data dictionary
        field_list: Specific fields to show (None for all)
        title: Section title
    """
    if field_list is None:
        field_list = list(data.keys())
    
    # Filter available fields
    available_fields = {k: v for k, v in data.items() if k in field_list and v is not None}
    
    if not available_fields:
        st.info(f"No {title.lower()} found")
        return
    
    # Display fields in a table-like format
    for field, value in available_fields.items():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"**{field.replace('_', ' ').title()}:**")
        
        with col2:
            if isinstance(value, (list, dict)):
                st.code(json.dumps(value, indent=2))
            else:
                st.write(str(value))

# ============================================================================
# ENHANCEMENT HISTORY UI
# ============================================================================

def render_enhancement_history(
    vessel_id: str,
    enhancement_service: VesselEnhancementService,
    key: str = "enhancement_history"
) -> None:
    """
    Render enhancement history for a vessel
    
    Args:
        vessel_id: Vessel ID
        enhancement_service: VesselEnhancementService instance
        key: Unique key for the component
    """
    st.subheader(" Enhancement History")
    
    try:
        history = enhancement_service.get_enhancement_history(vessel_id)
        
        if not history:
            st.info("No enhancement history found for this vessel")
            return
        
        # Display history in reverse chronological order
        for entry in reversed(history):
            with st.expander(f" {entry.get('source', 'Unknown')} - {entry.get('date', 'Unknown date')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Date:** {entry.get('date', 'Unknown')}")
                    st.write(f"**Source:** {entry.get('source', 'Unknown')}")
                    st.write(f"**User:** {entry.get('user_id', 'Unknown')}")
                
                with col2:
                    st.write(f"**Fields Updated:** {len(entry.get('fields_updated', []))}")
                    if entry.get('fields_updated'):
                        st.write(", ".join(entry['fields_updated']))
                
                if entry.get('notes'):
                    st.markdown("**Notes:**")
                    st.write(entry['notes'])
    
    except Exception as e:
        logger.error(f"Error rendering enhancement history: {e}")
        st.error(f" Error loading enhancement history: {str(e)}")

# ============================================================================
# ENHANCEMENT INTEGRATION FUNCTIONS
# ============================================================================

def integrate_enhancement_with_vessel_details(
    vessel_id: str,
    vessel_data: Dict[str, Any],
    enhancement_service: VesselEnhancementService,
    vessel_service: VesselService,
    user_id: str,
    key: str = "vessel_enhancement_integration"
) -> bool:
    """
    Integration function to add enhancement to vessel details page
    
    Args:
        vessel_id: Vessel ID
        vessel_data: Vessel data dictionary
        enhancement_service: VesselEnhancementService instance
        vessel_service: VesselService instance
        user_id: User ID
        key: Unique key for the component
        
    Returns:
        True if enhancement was completed
    """
    st.markdown("---")
    st.subheader(" Vessel Enhancement")
    
    # Set current vessel in session
    EnhancementSessionManager.set_current_vessel(vessel_id)
    
    # Check for active enhancement request
    enhance_request = EnhancementSessionManager.get_enhancement_request(key)
    
    if enhance_request:
        # Show enhancement execution
        completed = render_enhancement_execution(
            enhancement_service,
            vessel_service,
            user_id,
            key=f"{key}_execution"
        )
        
        if completed:
            st.success(" Vessel enhancement completed successfully!")
            # Clear session state
            EnhancementSessionManager.clear_all_enhancement_data()
            st.rerun()
        
        return completed
    
    # Render enhancement buttons
    action = render_enhancement_buttons(
        vessel_id,
        vessel_data,
        enhancement_service,
        key=f"{key}_buttons"
    )
    
    if action:
        st.rerun()
    
    # Show enhancement opportunities
    opportunities_action = render_enhancement_opportunities(
        vessel_id,
        enhancement_service,
        key=f"{key}_opportunities"
    )
    
    if opportunities_action:
        st.rerun()
    
    return False

def add_enhancement_to_admin_vessel_actions(
    vessel: Dict[str, Any],
    enhancement_service: VesselEnhancementService,
    vessel_service: VesselService,
    admin_user_id: str,
    key: str = "admin_enhancement"
) -> None:
    """
    Add enhancement functionality to admin vessel actions
    
    Args:
        vessel: Vessel dictionary
        enhancement_service: VesselEnhancementService instance
        vessel_service: VesselService instance
        admin_user_id: Admin user ID
        key: Unique key for the component
    """
    if st.button(" Enhance Data", key=f"{key}_enhance", use_container_width=True):
        st.session_state[f"{key}_show_enhancement"] = vessel['id']
    
    # Show enhancement interface if requested
    if st.session_state.get(f"{key}_show_enhancement") == vessel['id']:
        st.markdown("###  Vessel Enhancement")
        
        completed = integrate_enhancement_with_vessel_details(
            vessel['id'],
            vessel,
            enhancement_service,
            vessel_service,
            admin_user_id,
            key=f"{key}_details"
        )
        
        if completed:
            if f"{key}_show_enhancement" in st.session_state:
                del st.session_state[f"{key}_show_enhancement"]
            st.rerun()
        
        # Close button
        if st.button("Close Enhancement", key=f"{key}_close"):
            del st.session_state[f"{key}_show_enhancement"]
            # Clear enhancement session data
            EnhancementSessionManager.clear_all_enhancement_data()
            st.rerun()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def cleanup_enhancement_session():
    """Clean up enhancement session data"""
    EnhancementSessionManager.clear_all_enhancement_data()

def get_enhancement_session_info() -> Dict[str, Any]:
    """Get current enhancement session information for debugging"""
    return {
        'current_vessel': EnhancementSessionManager.get_current_vessel(),
        'session_keys': [
            key for key in st.session_state.keys() 
            if key.startswith('enhancement_')
        ],
        'session_data': {
            key: st.session_state[key] 
            for key in st.session_state.keys() 
            if key.startswith('enhancement_')
        }
    }
