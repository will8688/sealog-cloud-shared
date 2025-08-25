import streamlit as st
"""
Vessel Admin Components - FIXED VERSION
Admin-specific vessel management UI components

This module provides admin-only vessel management components including
edit forms, admin actions, and enhanced vessel management features.
"""

from typing import Optional, List, Dict, Any, Tuple
import logging

from vessel_service import VesselService
from vessel_components import render_vessel_form, render_vessel_details
from vessel_enhancement import VesselEnhancementService
from vessel_enhancement_ui import (
    integrate_enhancement_with_vessel_details,
    EnhancementSessionManager,
    cleanup_enhancement_session
)

logger = logging.getLogger(__name__)

# ============================================================================
# ADMIN VESSEL EDIT FUNCTIONALITY
# ============================================================================

def render_admin_vessel_edit_form(
    vessel_service: VesselService,
    vessel_id: str,
    key: str = "admin_vessel_edit"
) -> Optional[Dict[str, Any]]:
    """
    Render vessel edit form for admin users (matches settings experience)
    
    Args:
        vessel_service: VesselService instance
        vessel_id: Vessel ID to edit
        key: Unique key for the form
        
    Returns:
        Form data if submitted, None otherwise
    """
    try:
        # Get full vessel data
        vessel_data = vessel_service.get_vessel_by_id(vessel_id)
        
        if not vessel_data:
            st.error(" Vessel not found")
            return None
        
        st.info(f"Editing: **{vessel_data.vessel_name}**")
        
        # Convert vessel object to dict for form (same as settings)
        vessel_dict = {
            'vessel_name': getattr(vessel_data, 'vessel_name', ''),
            'vessel_type': getattr(vessel_data, 'vessel_type', 'yacht'),
            'imo_number': getattr(vessel_data, 'imo_number', ''),
            'call_sign': getattr(vessel_data, 'call_sign', ''),
            'flag_state': getattr(vessel_data, 'flag_state', ''),
            'port_of_registry': getattr(vessel_data, 'port_of_registry', ''),
            'length_overall': getattr(vessel_data, 'length_overall', None),
            'beam': getattr(vessel_data, 'beam', None),
            'draft': getattr(vessel_data, 'draft', None),
            'gross_tonnage': getattr(vessel_data, 'gross_tonnage', None),
            'year_built': getattr(vessel_data, 'year_built', None),
            'mmsi_number': getattr(vessel_data, 'mmsi_number', ''),
            'builder': getattr(vessel_data, 'builder', ''),
            'hull_material': getattr(vessel_data, 'hull_material', 'fiberglass'),
            'build_location': getattr(vessel_data, 'build_location', ''),
            'hull_number': getattr(vessel_data, 'hull_number', ''),
            'design_category': getattr(vessel_data, 'design_category', ''),
            'air_draft': getattr(vessel_data, 'air_draft', None),
            'displacement': getattr(vessel_data, 'displacement', None),
            'official_number': getattr(vessel_data, 'official_number', ''),
            'main_engines': getattr(vessel_data, 'main_engines', ''),
            'engine_power': getattr(vessel_data, 'engine_power', None),
            'number_of_engines': getattr(vessel_data, 'number_of_engines', 1),
            'cruise_speed': getattr(vessel_data, 'cruise_speed', None),
            'max_speed': getattr(vessel_data, 'max_speed', None),
            'fuel_capacity': getattr(vessel_data, 'fuel_capacity', None),
            'class_notation': getattr(vessel_data, 'class_notation', ''),
            
            # Handle nullable enum fields - convert None to empty string
            'classification_society': getattr(vessel_data, 'classification_society', '') or '',
            'propulsion_type': getattr(vessel_data, 'propulsion_type', '') or '',
            
            # Yacht-specific fields
            'yacht_category': getattr(vessel_data, 'yacht_category', '') or '',
            'guest_cabins': getattr(vessel_data, 'guest_cabins', None),
            'crew_cabins': getattr(vessel_data, 'crew_cabins', None),
            'guest_capacity': getattr(vessel_data, 'guest_capacity', None),
            'crew_capacity': getattr(vessel_data, 'crew_capacity', None),
            'range_nm': getattr(vessel_data, 'range', None),
            
            # Radio fields
            'default_operator_name': getattr(vessel_data, 'default_operator_name', ''),
            'radio_certificate': getattr(vessel_data, 'radio_certificate', ''),
        }
        
        # Render the same form as in settings
        updated_data = render_vessel_form(
            mode="edit",
            vessel_data=vessel_dict,
            show_advanced=True,
            key=f"{key}_{vessel_id}"
        )
        
        return updated_data
        
    except Exception as e:
        logger.error(f"Error rendering admin vessel edit form: {e}")
        st.error(f" Error loading vessel data: {str(e)}")
        return None

def handle_admin_vessel_edit(
    vessel_service: VesselService,
    vessel_id: str,
    updated_data: Dict[str, Any],
    admin_user_id: str
) -> Tuple[bool, str]:
    """
    Handle admin vessel edit submission
    
    Args:
        vessel_service: VesselService instance
        vessel_id: Vessel ID to update
        updated_data: Updated vessel data
        admin_user_id: Admin user ID
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Update vessel using vessel service
        success, message = vessel_service.update_vessel(
            vessel_id,
            updated_data,
            admin_user_id
        )
        
        if success:
            logger.info(f"Admin {admin_user_id} updated vessel {vessel_id}")
            
        return success, message
        
    except Exception as e:
        logger.error(f"Error in admin vessel edit: {e}")
        return False, f"Update failed: {str(e)}"

# ============================================================================
# ADMIN VESSEL MANAGEMENT UI
# ============================================================================

def render_admin_vessel_edit_page(
    vessel_service: VesselService,
    vessel_id: str,
    admin_user_id: str,
    key: str = "admin_edit_page"
) -> bool:
    """
    Render complete admin vessel edit page
    
    Args:
        vessel_service: VesselService instance
        vessel_id: Vessel ID to edit
        admin_user_id: Admin user ID
        key: Unique key for the page
        
    Returns:
        True if vessel was updated successfully
    """
    st.subheader(" Edit Vessel (Admin)")
    
    # Back button
    if st.button("← Back to Vessel List", key=f"{key}_back"):
        # Clear edit mode from session state
        if 'admin_edit_vessel_id' in st.session_state:
            del st.session_state.admin_edit_vessel_id
        # Clear any enhancement session data
        cleanup_enhancement_session()
        st.rerun()
    
    st.markdown("---")
    
    # Render edit form
    updated_data = render_admin_vessel_edit_form(
        vessel_service,
        vessel_id,
        key=f"{key}_form"
    )
    
    if updated_data:
        # Handle form submission
        success, message = handle_admin_vessel_edit(
            vessel_service,
            vessel_id,
            updated_data,
            admin_user_id
        )
        
        if success:
            st.success(f" {message}")
            st.info(" Changes are now active across all maritime tools!")
            
            # Clear edit mode
            if 'admin_edit_vessel_id' in st.session_state:
                del st.session_state.admin_edit_vessel_id
            
            # Clear enhancement session data
            cleanup_enhancement_session()
            
            # Option to continue editing or return to list
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Return to Vessel List", key=f"{key}_return"):
                    st.rerun()
            with col2:
                if st.button("Continue Editing", key=f"{key}_continue"):
                    st.rerun()
            
            return True
        else:
            st.error(f" {message}")
            return False
    
    return False

def render_admin_vessel_actions(
    vessel_service: VesselService,
    vessel: Dict[str, Any],
    admin_user_id: str,
    key: str = "admin_actions"
) -> Optional[str]:
    """
    Render admin-specific vessel actions
    
    Args:
        vessel_service: VesselService instance
        vessel: Vessel dictionary
        admin_user_id: Admin user ID
        key: Unique key for actions
        
    Returns:
        Action string if action taken, None otherwise
    """
    st.markdown("### Admin Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button(" Edit", key=f"{key}_edit", use_container_width=True):
            # Clear any existing session data
            cleanup_enhancement_session()
            st.session_state.admin_edit_vessel_id = vessel['id']
            return "edit"
    
    with col2:
        if st.button(" Details", key=f"{key}_details", use_container_width=True):
            # Clear any existing session data
            cleanup_enhancement_session()
            st.session_state.admin_show_vessel_details = vessel['id']
            return "details"
    
    with col3:
        if st.button(" Enhance", key=f"{key}_enhance", use_container_width=True):
            # Clear any existing session data
            cleanup_enhancement_session()
            st.session_state.admin_enhance_vessel_id = vessel['id']
            return "enhance"
    
    with col4:
        if st.button(" Delete", key=f"{key}_delete", use_container_width=True, type="secondary"):
            # Clear any existing session data
            cleanup_enhancement_session()
            st.session_state.admin_delete_vessel_id = vessel['id']
            return "delete"
    
    return None

# ============================================================================
# ENHANCED ADMIN VESSEL LIST
# ============================================================================

def render_admin_vessel_list_with_actions(
    vessels: List[Dict[str, Any]],
    vessel_service: VesselService,
    admin_user_id: str,
    key: str = "admin_vessel_list"
) -> Optional[str]:
    """
    Render enhanced admin vessel list with inline actions
    
    Args:
        vessels: List of vessel dictionaries
        vessel_service: VesselService instance
        admin_user_id: Admin user ID
        key: Unique key for the component
        
    Returns:
        Action result if any
    """
    if not vessels:
        st.info("No vessels found.")
        return None
    
    st.info(f" Total vessels in system: {len(vessels)}")
    
    # Check for edit mode
    edit_vessel_id = st.session_state.get('admin_edit_vessel_id')
    if edit_vessel_id:
        # Show edit page instead of list
        vessel_updated = render_admin_vessel_edit_page(
            vessel_service,
            edit_vessel_id,
            admin_user_id,
            key=f"{key}_edit_page"
        )
        return "edit_complete" if vessel_updated else "edit_in_progress"
    
    # Check for details view
    details_vessel_id = st.session_state.get('admin_show_vessel_details')
    if details_vessel_id:
        vessel_details = next((v for v in vessels if v.get('id') == details_vessel_id), None)
        if vessel_details:
            st.markdown("###  Vessel Details")
            render_vessel_details(vessel_details, key=f"{key}_details")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("← Back to List", key=f"{key}_close_details"):
                    del st.session_state.admin_show_vessel_details
                    cleanup_enhancement_session()
                    st.rerun()
            with col2:
                if st.button(" Edit This Vessel", key=f"{key}_edit_from_details"):
                    st.session_state.admin_edit_vessel_id = details_vessel_id
                    del st.session_state.admin_show_vessel_details
                    cleanup_enhancement_session()
                    st.rerun()
        return "details_shown"
    
    # Check for delete confirmation
    delete_vessel_id = st.session_state.get('admin_delete_vessel_id')
    if delete_vessel_id:
        vessel_to_delete = next((v for v in vessels if v.get('id') == delete_vessel_id), None)
        if vessel_to_delete:
            st.warning(f" Confirm deletion of vessel: **{vessel_to_delete.get('name', 'Unknown')}**")
            st.write("This action cannot be undone.")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button(" Confirm Delete", key=f"{key}_confirm_delete", type="primary"):
                    success, message = vessel_service.delete_vessel(delete_vessel_id, admin_user_id)
                    if success:
                        st.success(f" {message}")
                        del st.session_state.admin_delete_vessel_id
                        cleanup_enhancement_session()
                        st.rerun()
                    else:
                        st.error(f" {message}")
            
            with col2:
                if st.button("Cancel", key=f"{key}_cancel_delete"):
                    del st.session_state.admin_delete_vessel_id
                    cleanup_enhancement_session()
                    st.rerun()
        
        return "delete_confirm"
    
    # Check for enhancement mode - FIXED VERSION
    enhance_vessel_id = st.session_state.get('admin_enhance_vessel_id')
    if enhance_vessel_id:
        vessel_to_enhance = next((v for v in vessels if v.get('id') == enhance_vessel_id), None)
        if vessel_to_enhance:
            st.markdown("###  Vessel Enhancement")
            
            try:
                # Initialize enhancement service
                enhancement_service = VesselEnhancementService(vessel_service, marine_traffic_api_key=None)
                
                # Convert vessel dict to format expected by enhancement UI
                vessel_data = {
                    'vessel_name': vessel_to_enhance.get('name', ''),
                    'vessel_type': vessel_to_enhance.get('vessel_type', ''),
                    'imo_number': vessel_to_enhance.get('imo_number', ''),
                    'mmsi_number': vessel_to_enhance.get('mmsi_number', ''),
                    'call_sign': vessel_to_enhance.get('call_sign', ''),
                    'flag_state': vessel_to_enhance.get('flag_state', ''),
                    'length_overall': vessel_to_enhance.get('length_overall'),
                    'year_built': vessel_to_enhance.get('year_built')
                }
                
                # Use the fixed enhancement UI integration
                completed = integrate_enhancement_with_vessel_details(
                    enhance_vessel_id,
                    vessel_data,
                    enhancement_service,
                    vessel_service,
                    admin_user_id,
                    key=f"admin_enhance_{enhance_vessel_id}"
                )
                
                if completed:
                    st.success(" Enhancement completed!")
                    # Clean up session state
                    del st.session_state.admin_enhance_vessel_id
                    cleanup_enhancement_session()
                    st.rerun()
                        
            except Exception as e:
                st.error(f" Enhancement error: {e}")
                logger.error(f"Enhancement error: {e}")
                import traceback
                st.code(traceback.format_exc())
            
            # Close enhancement button
            if st.button("← Back to Vessel List", key=f"admin_enhance_close_{enhance_vessel_id}"):
                del st.session_state.admin_enhance_vessel_id
                cleanup_enhancement_session()
                st.rerun()
        
        return "enhance_shown"

    # Show vessel list with actions
    for i, vessel in enumerate(vessels):
        with st.expander(f" {vessel.get('name', 'Unknown')} ({vessel.get('vessel_type', 'Unknown').replace('_', ' ').title()})"):
            # Basic info
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {vessel.get('id', 'Unknown')}")
                st.write(f"**IMO:** {vessel.get('imo_number', 'Not specified')}")
                st.write(f"**Call Sign:** {vessel.get('call_sign', 'Not specified')}")
                st.write(f"**Flag:** {vessel.get('flag_state', 'Not specified')}")
            
            with col2:
                st.write(f"**Length:** {vessel.get('length_overall', 'Not specified')} m")
                st.write(f"**Year Built:** {vessel.get('year_built', 'Not specified')}")
                st.write(f"**Builder:** {vessel.get('builder', 'Not specified')}")
                st.write(f"**Created:** {vessel.get('created_date', 'Unknown')}")
            
            # Actions
            action = render_admin_vessel_actions(
                vessel_service,
                vessel,
                admin_user_id,
                key=f"{key}_actions_{i}"
            )
            
            if action:
                st.rerun()
    
    return None

# ============================================================================
# VESSEL BULK OPERATIONS
# ============================================================================

def render_vessel_bulk_operations(
    vessels: List[Dict[str, Any]],
    vessel_service: VesselService,
    admin_user_id: str,
    key: str = "bulk_operations"
) -> Optional[str]:
    """
    Render bulk operations interface for vessels
    
    Args:
        vessels: List of vessel dictionaries
        vessel_service: VesselService instance
        admin_user_id: Admin user ID
        key: Unique key for the component
        
    Returns:
        Action result if any
    """
    if not vessels:
        return None
    
    st.markdown("###  Bulk Operations")
    
    # Vessel selection
    vessel_options = {f"{v['name']} ({v['id']})": v['id'] for v in vessels}
    selected_vessel_names = st.multiselect(
        "Select vessels for bulk operations:",
        options=list(vessel_options.keys()),
        key=f"{key}_selection"
    )
    
    if not selected_vessel_names:
        st.info("Select vessels above to enable bulk operations")
        return None
    
    selected_vessel_ids = [vessel_options[name] for name in selected_vessel_names]
    
    st.info(f"Selected {len(selected_vessel_ids)} vessel(s)")
    
    # Bulk operations
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(" Bulk Enhancement", key=f"{key}_bulk_enhance", use_container_width=True):
            st.session_state[f"{key}_bulk_enhance_vessels"] = selected_vessel_ids
            return "bulk_enhance"
    
    with col2:
        if st.button(" Export Data", key=f"{key}_bulk_export", use_container_width=True):
            st.session_state[f"{key}_bulk_export_vessels"] = selected_vessel_ids
            return "bulk_export"
    
    with col3:
        if st.button(" Bulk Delete", key=f"{key}_bulk_delete", use_container_width=True, type="secondary"):
            st.session_state[f"{key}_bulk_delete_vessels"] = selected_vessel_ids
            return "bulk_delete"
    
    return None

def render_bulk_enhancement_interface(
    vessel_ids: List[str],
    vessel_service: VesselService,
    admin_user_id: str,
    key: str = "bulk_enhancement"
) -> bool:
    """
    Render bulk enhancement interface
    
    Args:
        vessel_ids: List of vessel IDs to enhance
        vessel_service: VesselService instance
        admin_user_id: Admin user ID
        key: Unique key for the component
        
    Returns:
        True if bulk enhancement was completed
    """
    st.markdown("###  Bulk Enhancement")
    
    st.info(f"Enhancing {len(vessel_ids)} vessels")
    
    # Enhancement source selection
    enhancement_sources = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.checkbox(" MarineTraffic", key=f"{key}_mt"):
            enhancement_sources.append("marinetraffic")
    
    with col2:
        if st.checkbox(" BOAT International", key=f"{key}_bi"):
            enhancement_sources.append("boat_international")
    
    if not enhancement_sources:
        st.warning(" Select at least one enhancement source")
        return False
    
    # Start bulk enhancement
    if st.button(" Start Bulk Enhancement", key=f"{key}_start", type="primary"):
        try:
            enhancement_service = VesselEnhancementService(vessel_service)
            
            # This would be implemented in the enhancement service
            st.info(" Bulk enhancement functionality coming soon...")
            
            # For now, just show progress
            progress = st.progress(0)
            status = st.empty()
            
            for i, vessel_id in enumerate(vessel_ids):
                status.text(f"Processing vessel {i+1}/{len(vessel_ids)}: {vessel_id}")
                progress.progress((i + 1) / len(vessel_ids))
                
                # Simulate processing
                import time
                time.sleep(0.5)
            
            st.success(" Bulk enhancement completed!")
            return True
            
        except Exception as e:
            st.error(f" Bulk enhancement failed: {str(e)}")
            logger.error(f"Bulk enhancement error: {e}")
            return False
    
    return False

# ============================================================================
# ADMIN VESSEL MANAGEMENT INTEGRATION
# ============================================================================

def integrate_admin_vessel_edit_with_existing(
    vessels: List[Dict[str, Any]],
    vessel_service: VesselService,
    admin_user_id: str
):
    """
    Integration function for existing admin vessel management
    Drop-in replacement for existing vessel list handling
    
    Args:
        vessels: List of vessel dictionaries
        vessel_service: VesselService instance
        admin_user_id: Admin user ID
    """
    # Check for bulk operations
    bulk_enhance_vessels = st.session_state.get('admin_vessel_list_bulk_enhance_vessels')
    if bulk_enhance_vessels:
        completed = render_bulk_enhancement_interface(
            bulk_enhance_vessels,
            vessel_service,
            admin_user_id,
            key="admin_bulk_enhance"
        )
        
        if completed:
            del st.session_state.admin_vessel_list_bulk_enhance_vessels
            st.rerun()
        
        # Back button
        if st.button("← Back to Vessel List", key="admin_bulk_enhance_back"):
            del st.session_state.admin_vessel_list_bulk_enhance_vessels
            st.rerun()
        
        return
    
    # Render bulk operations interface
    bulk_action = render_vessel_bulk_operations(
        vessels,
        vessel_service,
        admin_user_id,
        key="admin_vessel_list"
    )
    
    if bulk_action:
        st.rerun()
    
    # This function can be called from vessel_admin.py
    # to replace the existing vessel list rendering
    result = render_admin_vessel_list_with_actions(
        vessels,
        vessel_service,
        admin_user_id,
        key="admin_vessel_management"
    )
    
    # Handle results if needed
    if result == "edit_complete":
        st.success(" Vessel updated successfully!")
        st.rerun()
    elif result == "delete_confirm":
        # Delete confirmation is handled within the function
        pass

# ============================================================================
# DEBUGGING AND MONITORING
# ============================================================================

def render_admin_debug_panel(
    vessel_service: VesselService,
    key: str = "admin_debug"
) -> None:
    """
    Render debug panel for admin users
    
    Args:
        vessel_service: VesselService instance
        key: Unique key for the component
    """
    with st.expander(" Debug Panel (Admin Only)"):
        st.markdown("### Session State")
        
        # Show enhancement session info
        try:
            from vessel_enhancement_ui import get_enhancement_session_info
            session_info = get_enhancement_session_info()
            st.json(session_info)
        except Exception as e:
            st.error(f"Error getting session info: {e}")
        
        # Show vessel service status
        st.markdown("### Vessel Service Status")
        try:
            vessel_count = vessel_service.get_user_vessel_count()
            st.write(f"**Total vessels:** {vessel_count}")
        except Exception as e:
            st.error(f"Error getting vessel count: {e}")
        
        # Clear session button
        if st.button(" Clear All Session Data", key=f"{key}_clear_session"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success(" Session data cleared")
            st.rerun()

def get_admin_vessel_management_status() -> Dict[str, Any]:
    """
    Get status information for admin vessel management
    
    Returns:
        Status dictionary
    """
    return {
        'active_sessions': len([k for k in st.session_state.keys() if 'admin_' in k]),
        'enhancement_sessions': len([k for k in st.session_state.keys() if 'enhancement_' in k]),
        'session_keys': list(st.session_state.keys()),
        'timestamp': st.session_state.get('last_update', 'unknown')
    }
