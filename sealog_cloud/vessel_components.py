"""
Vessel Streamlit Components
Reusable UI components for vessel management across maritime tools

This module provides standardized Streamlit components for vessel selection,
forms, and management interfaces used in Ships Log, Radio Log, and Crew Log.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
import pandas as pd

from vessel_schema import (
    VesselType, YachtCategory, HullMaterial, PropulsionType, 
    ClassificationSociety, BuildStandard
)
from vessel_service import VesselService
from vessel_schema import get_flag_states, get_design_categories, get_design_category_description

# ============================================================================
# VESSEL SELECTION COMPONENTS
# ============================================================================

def render_vessel_selector(
    vessel_service: VesselService,
    key: str = "vessel_selector",
    label: str = "Select Vessel",
    show_add_button: bool = True,
    user_id: str = None
) -> Optional[Dict[str, Any]]:
    """
    Standard vessel selector dropdown with optional add vessel functionality
    
    Args:
        vessel_service: VesselService instance
        key: Unique key for the component
        label: Label for the selectbox
        show_add_button: Whether to show "Add New Vessel" button
        user_id: User ID for vessel filtering
        
    Returns:
        Selected vessel dictionary or None
    """
    # Get user's vessels
    vessels = vessel_service.get_user_vessels(user_id)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if not vessels:
            st.info("No vessels found. Please add a vessel first.")
            selected_vessel = None
        else:
            # Create options for selectbox
            vessel_options = ["Select a vessel..."] + [
                vessel['display_name'] for vessel in vessels
            ]
            
            selected_index = st.selectbox(
                label,
                options=range(len(vessel_options)),
                format_func=lambda x: vessel_options[x],
                key=key
            )
            
            if selected_index == 0:
                selected_vessel = None
            else:
                selected_vessel = vessels[selected_index - 1]
    
    with col2:
        if show_add_button:
            if st.button(" Add Vessel", key=f"{key}_add_btn"):
                st.session_state[f"{key}_show_add_form"] = True
    
    # Show add vessel form if requested
    if show_add_button and st.session_state.get(f"{key}_show_add_form", False):
        render_add_vessel_modal(vessel_service, key, user_id)
    
    return selected_vessel

def render_vessel_search(
    vessel_service: VesselService,
    key: str = "vessel_search",
    placeholder: str = "Search by name, IMO, MMSI, or call sign...",
    user_only: bool = False,
    user_id: str = None
) -> List[Dict[str, Any]]:
    """
    Vessel search component with live results
    
    Args:
        vessel_service: VesselService instance
        key: Unique key for the component
        placeholder: Search input placeholder
        user_only: Limit search to user's vessels
        user_id: User ID for filtering
        
    Returns:
        List of matching vessels
    """
    search_query = st.text_input(
        "Search Vessels",
        placeholder=placeholder,
        key=f"{key}_input"
    )
    
    if search_query and len(search_query) >= 2:
        search_user_id = user_id if user_only else None
        results = vessel_service.search_vessels(search_query, search_user_id)
        
        if results:
            st.write(f"Found {len(results)} vessel(s):")
            
            # Display results in a nice format
            for vessel in results:
                with st.expander(f" {vessel['display_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Type:** {vessel.get('vessel_type', 'Unknown')}")
                        st.write(f"**Flag:** {vessel.get('flag_state', 'Unknown')}")
                    with col2:
                        if vessel.get('imo_number'):
                            st.write(f"**IMO:** {vessel['imo_number']}")
                        if vessel.get('mmsi_number'):
                            st.write(f"**MMSI:** {vessel['mmsi_number']}")
        else:
            st.info("No vessels found matching your search.")
        
        return results
    
    return []

# ============================================================================
# VESSEL FORM COMPONENTS
# ============================================================================

def render_vessel_form(
    vessel_data: Dict[str, Any] = None,
    mode: str = "create",
    key: str = "vessel_form",
    show_advanced: bool = False
) -> Dict[str, Any]:
    """
    Comprehensive vessel form for creation and editing
    
    Args:
        vessel_data: Existing vessel data for editing
        mode: "create" or "edit"
        key: Unique key for the form
        show_advanced: Whether to show advanced fields
        
    Returns:
        Dictionary of form data
    """
    st.subheader(f"{'Add New' if mode == 'create' else 'Edit'} Vessel")
    
    # Initialize form data
    form_data = vessel_data.copy() if vessel_data else {}
    
    with st.form(f"{key}_form"):
        # Basic Information Section
        st.markdown("###  Basic Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['vessel_name'] = st.text_input(
                "Vessel Name *",
                value=form_data.get('vessel_name', ''),
                help="Official vessel name"
            )
            
            form_data['vessel_type'] = st.selectbox(
                "Vessel Type *",
                options=[vt.value for vt in VesselType],
                index=[vt.value for vt in VesselType].index(form_data.get('vessel_type', 'yacht')),
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            form_data['flag_state'] = st.selectbox(
                "Flag State",
                options=get_flag_states(),  # Remove use_common=True to get full list
                index=get_flag_states().index(form_data.get('flag_state', 'Other')) if form_data.get('flag_state') in get_flag_states() else 0,
                help="Country of registration (type to search)"
            )
            
            form_data['port_of_registry'] = st.text_input(
                "Port of Registry",
                value=form_data.get('port_of_registry', ''),
                help="Official port of registration"
            )
        
        with col2:
            form_data['imo_number'] = st.text_input(
                "IMO Number",
                value=form_data.get('imo_number', ''),
                help="7-digit IMO number",
                max_chars=7
            )
            
            form_data['mmsi_number'] = st.text_input(
                "MMSI Number",
                value=form_data.get('mmsi_number', ''),
                help="9-digit MMSI number",
                max_chars=9
            )
            
            form_data['call_sign'] = st.text_input(
                "Call Sign",
                value=form_data.get('call_sign', ''),
                help="Radio call sign"
            )
            
            form_data['official_number'] = st.text_input(
                "Official Number",
                value=form_data.get('official_number', ''),
                help="Flag state registration number"
            )
        
        # Dimensions Section
        st.markdown("###  Dimensions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            form_data['length_overall'] = st.number_input(
                "Length Overall (m)",
                value=float(form_data.get('length_overall', 0)) if form_data.get('length_overall') else 0.0,
                min_value=0.0,
                step=0.1,
                format="%.1f"
            )
            
            form_data['beam'] = st.number_input(
                "Beam (m)",
                value=float(form_data.get('beam', 0)) if form_data.get('beam') else 0.0,
                min_value=0.0,
                step=0.1,
                format="%.1f"
            )
        
        with col2:
            form_data['draft'] = st.number_input(
                "Draft (m)",
                value=float(form_data.get('draft', 0)) if form_data.get('draft') else 0.0,
                min_value=0.0,
                step=0.1,
                format="%.1f"
            )
            
            form_data['gross_tonnage'] = st.number_input(
                "Gross Tonnage",
                value=float(form_data.get('gross_tonnage', 0)) if form_data.get('gross_tonnage') else 0.0,
                min_value=0.0,
                step=0.1,
                format="%.1f"
            )
        
        with col3:
            form_data['air_draft'] = st.number_input(
                "Air Draft (m)",
                value=float(form_data.get('air_draft', 0)) if form_data.get('air_draft') else 0.0,
                min_value=0.0,
                step=0.1,
                format="%.1f",
                help="Height above waterline"
            )
            
            form_data['displacement'] = st.number_input(
                "Displacement (tonnes)",
                value=float(form_data.get('displacement', 0)) if form_data.get('displacement') else 0.0,
                min_value=0.0,
                step=0.1,
                format="%.1f"
            )
        
        # Construction Information
        st.markdown("###  Construction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['year_built'] = st.number_input(
                "Year Built",
                value=int(form_data.get('year_built', datetime.now().year)) if form_data.get('year_built') else datetime.now().year,
                min_value=1800,
                max_value=datetime.now().year + 5,
                step=1
            )
            
            form_data['builder'] = st.text_input(
                "Builder/Shipyard",
                value=form_data.get('builder', ''),
                help="Shipyard or manufacturer"
            )
            
            form_data['hull_material'] = st.selectbox(
                "Hull Material",
                options=[hm.value for hm in HullMaterial],
                index=[hm.value for hm in HullMaterial].index(form_data.get('hull_material', 'fiberglass')),
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        with col2:
            form_data['build_location'] = st.text_input(
                "Build Location",
                value=form_data.get('build_location', ''),
                help="Country/city where built"
            )
            
            form_data['hull_number'] = st.text_input(
                "Hull Number",
                value=form_data.get('hull_number', ''),
                help="Builder's hull number"
            )
            
            form_data['design_category'] = st.selectbox(
                "Design Category",
                options=get_design_categories(),
                format_func=lambda x: get_design_category_description(x, short=True)
            )
        
        # Radio/Communications Section (for Radio Log integration)
        st.markdown("###  Communications")
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['default_operator_name'] = st.text_input(
                "Default Operator Name",
                value=form_data.get('default_operator_name', ''),
                help="Default radio operator"
            )
        
        with col2:
            form_data['radio_certificate'] = st.text_input(
                "Radio Certificate",
                value=form_data.get('radio_certificate', ''),
                help="Radio license/certificate number"
            )
        
        # Advanced Fields (collapsed by default)
        if show_advanced:
            render_advanced_vessel_fields(form_data, key)
        else:
            if st.checkbox("Show Advanced Fields", key=f"{key}_show_advanced"):
                render_advanced_vessel_fields(form_data, key)
        
        # Form submission
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            submitted = st.form_submit_button(
                f"{'Create' if mode == 'create' else 'Update'} Vessel",
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            return form_data
    
    return {}

def render_advanced_vessel_fields(form_data: Dict[str, Any], key: str):
    """
    Render advanced vessel fields in the form
    
    Args:
        form_data: Form data dictionary to update
        key: Form key for unique components
    """
    st.markdown("###  Advanced Details")
    
    # Yacht-specific fields
    if form_data.get('vessel_type') in ['yacht', 'motor_yacht', 'sailing_yacht', 'superyacht']:
        st.markdown("####  Yacht Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            form_data['yacht_category'] = st.selectbox(
                "Yacht Category",
                options=[''] + [yc.value for yc in YachtCategory],
                index=([''] + [yc.value for yc in YachtCategory]).index(form_data.get('yacht_category', '')),
                format_func=lambda x: x.replace('_', ' ').title() if x else "Not specified"
            )
            
            form_data['guest_cabins'] = st.number_input(
                "Guest Cabins",
                value=int(form_data.get('guest_cabins', 0)) if form_data.get('guest_cabins') else 0,
                min_value=0,
                step=1
            )
            
            form_data['max_speed'] = st.number_input(
                "Max Speed (kts)",
                value=float(form_data.get('max_speed', 0)) if form_data.get('max_speed') else 0.0,
                min_value=0.0,
                step=0.1,
                format="%.1f"
            )
        
        with col2:
            form_data['crew_cabins'] = st.number_input(
                "Crew Cabins",
                value=int(form_data.get('crew_cabins', 0)) if form_data.get('crew_cabins') else 0,
                min_value=0,
                step=1
            )
            
            form_data['guest_capacity'] = st.number_input(
                "Guest Capacity",
                value=int(form_data.get('guest_capacity', 0)) if form_data.get('guest_capacity') else 0,
                min_value=0,
                step=1
            )
            
            form_data['cruise_speed'] = st.number_input(
                "Cruise Speed (kts)",
                value=float(form_data.get('cruise_speed', 0)) if form_data.get('cruise_speed') else 0.0,
                min_value=0.0,
                step=0.1,
                format="%.1f"
            )
        
        with col3:
            form_data['crew_capacity'] = st.number_input(
                "Crew Capacity",
                value=int(form_data.get('crew_capacity', 0)) if form_data.get('crew_capacity') else 0,
                min_value=0,
                step=1
            )
            
            form_data['range_nm'] = st.number_input(
                "Range (nm)",
                value=float(form_data.get('range_nm', 0)) if form_data.get('range_nm') else 0.0,
                min_value=0.0,
                step=1.0,
                format="%.0f"
            )
            
            form_data['fuel_capacity'] = st.number_input(
                "Fuel Capacity (L)",
                value=float(form_data.get('fuel_capacity', 0)) if form_data.get('fuel_capacity') else 0.0,
                min_value=0.0,
                step=1.0,
                format="%.0f"
            )
    
    # Propulsion
    st.markdown("####  Propulsion")
    
    col1, col2 = st.columns(2)
    
    with col1:
        form_data['propulsion_type'] = st.selectbox(
            "Propulsion Type",
            options=[''] + [pt.value for pt in PropulsionType],
            index=([''] + [pt.value for pt in PropulsionType]).index(form_data.get('propulsion_type', '')),
            format_func=lambda x: x.replace('_', ' ').title() if x else "Not specified"
        )
        
        form_data['main_engines'] = st.text_input(
            "Main Engines",
            value=form_data.get('main_engines', ''),
            help="Engine make and model"
        )
    
    with col2:
        form_data['engine_power'] = st.number_input(
            "Engine Power (HP)",
            value=float(form_data.get('engine_power', 0)) if form_data.get('engine_power') else 0.0,
            min_value=0.0,
            step=1.0,
            format="%.0f"
        )
        
        form_data['number_of_engines'] = st.number_input(
            "Number of Engines",
            value=int(form_data.get('number_of_engines', 1)) if form_data.get('number_of_engines') else 1,
            min_value=1,
            step=1
        )
    
    # Classification and Standards
    st.markdown("####  Classification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        form_data['classification_society'] = st.selectbox(
            "Classification Society",
            options=[''] + [cs.value for cs in ClassificationSociety],
            index=([''] + [cs.value for cs in ClassificationSociety]).index(form_data.get('classification_society', '')),
            format_func=lambda x: x.upper() if x else "Not specified"
        )
    
    with col2:
        form_data['class_notation'] = st.text_input(
            "Class Notation",
            value=form_data.get('class_notation', ''),
            help="Specific classification notation"
        )

# ============================================================================
# VESSEL MANAGEMENT COMPONENTS
# ============================================================================

def render_vessel_list(
    vessels: List[Dict[str, Any]],
    key: str = "vessel_list",
    show_actions: bool = True
) -> Optional[str]:
    """
    Render a list of vessels with optional actions
    
    Args:
        vessels: List of vessel dictionaries
        key: Unique key for the component
        show_actions: Whether to show edit/delete actions
        
    Returns:
        Selected vessel ID for actions
    """
    if not vessels:
        st.info("No vessels found.")
        return None
    
    # Create DataFrame for better display
    df_data = []
    for vessel in vessels:
        df_data.append({
            'Name': vessel.get('name', 'Unknown'),
            'Type': vessel.get('vessel_type', '').replace('_', ' ').title(),
            'Flag': vessel.get('flag_state', ''),
            'IMO': vessel.get('imo_number', ''),
            'MMSI': vessel.get('mmsi_number', ''),
            'Call Sign': vessel.get('call_sign', ''),
            'Length (m)': vessel.get('length_overall', ''),
            'Year': vessel.get('year_built', '')
        })
    
    df = pd.DataFrame(df_data)
    
    # Display as interactive table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    if show_actions:
        st.markdown("### Actions")
        selected_vessel_name = st.selectbox(
            "Select vessel for actions:",
            options=["Select vessel..."] + [vessel['name'] for vessel in vessels],
            key=f"{key}_action_select"
        )
        
        if selected_vessel_name != "Select vessel...":
            selected_vessel = next(
                (v for v in vessels if v['name'] == selected_vessel_name), 
                None
            )
            
            if selected_vessel:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(" Edit", key=f"{key}_edit"):
                        return f"edit_{selected_vessel['id']}"
                
                with col2:
                    if st.button(" Details", key=f"{key}_details"):
                        return f"details_{selected_vessel['id']}"
                
                with col3:
                    if st.button(" Delete", key=f"{key}_delete", type="secondary"):
                        return f"delete_{selected_vessel['id']}"
    
    return None

def render_vessel_details(vessel: Dict[str, Any], key: str = "vessel_details"):
    """
    Render detailed vessel information
    
    Args:
        vessel: Vessel dictionary
        key: Unique key for the component
    """
    st.subheader(f" {vessel.get('name', 'Unknown Vessel')}")
    
    # Basic Information
    with st.expander(" Basic Information", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Vessel Type:** {vessel.get('vessel_type', 'Unknown').replace('_', ' ').title()}")
            st.write(f"**Flag State:** {vessel.get('flag_state', 'Unknown')}")
            st.write(f"**Port of Registry:** {vessel.get('port_of_registry', 'Unknown')}")
            st.write(f"**Year Built:** {vessel.get('year_built', 'Unknown')}")
        
        with col2:
            st.write(f"**IMO Number:** {vessel.get('imo_number', 'Not specified')}")
            st.write(f"**MMSI Number:** {vessel.get('mmsi_number', 'Not specified')}")
            st.write(f"**Call Sign:** {vessel.get('call_sign', 'Not specified')}")
            st.write(f"**Builder:** {vessel.get('builder', 'Unknown')}")
    
    # Dimensions
    with st.expander(" Dimensions"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Length Overall", f"{vessel.get('length_overall', 0):.1f} m")
            st.metric("Beam", f"{vessel.get('beam', 0):.1f} m")
        
        with col2:
            st.metric("Draft", f"{vessel.get('draft', 0):.1f} m")
            st.metric("Air Draft", f"{vessel.get('air_draft', 0):.1f} m")
        
        with col3:
            st.metric("Gross Tonnage", f"{vessel.get('gross_tonnage', 0):.1f}")
            st.metric("Displacement", f"{vessel.get('displacement', 0):.1f} t")
    
    # Yacht-specific details
    if vessel.get('vessel_type') in ['yacht', 'motor_yacht', 'sailing_yacht', 'superyacht']:
        with st.expander(" Yacht Details"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Guest Cabins:** {vessel.get('guest_cabins', 'Unknown')}")
                st.write(f"**Crew Cabins:** {vessel.get('crew_cabins', 'Unknown')}")
            
            with col2:
                st.write(f"**Guest Capacity:** {vessel.get('guest_capacity', 'Unknown')}")
                st.write(f"**Crew Capacity:** {vessel.get('crew_capacity', 'Unknown')}")
            
            with col3:
                st.write(f"**Max Speed:** {vessel.get('max_speed', 'Unknown')} kts")
                st.write(f"**Range:** {vessel.get('range_nm', 'Unknown')} nm")

# ============================================================================
# MODAL AND POPUP COMPONENTS
# ============================================================================

def render_add_vessel_modal(vessel_service: VesselService, parent_key: str, user_id: str):
    """
    Render add vessel modal dialog
    
    Args:
        vessel_service: VesselService instance
        parent_key: Parent component key
        user_id: User ID
    """
    st.markdown("---")
    st.markdown("###  Add New Vessel")
    
    # Quick add form
    with st.form(f"{parent_key}_quick_add"):
        col1, col2 = st.columns(2)
        
        with col1:
            vessel_name = st.text_input("Vessel Name *", key=f"{parent_key}_name")
            vessel_type = st.selectbox(
                "Vessel Type",
                options=[vt.value for vt in VesselType],
                key=f"{parent_key}_type"
            )
        
        with col2:
            imo_number = st.text_input("IMO Number", key=f"{parent_key}_imo")
            call_sign = st.text_input("Call Sign", key=f"{parent_key}_call")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.form_submit_button("Add Vessel", type="primary"):
                if vessel_name:
                    vessel_data = {
                        'vessel_name': vessel_name,
                        'vessel_type': vessel_type,
                        'imo_number': imo_number,
                        'call_sign': call_sign
                    }
                    
                    success, message, vessel_id = vessel_service.create_vessel(
                        vessel_data, user_id
                    )
                    
                    if success:
                        st.success(f" {message}")
                        st.session_state[f"{parent_key}_show_add_form"] = False
                        st.rerun()
                    else:
                        st.error(f" {message}")
                else:
                    st.error("Vessel name is required")
        
        with col3:
            if st.form_submit_button("Cancel"):
                st.session_state[f"{parent_key}_show_add_form"] = False
                st.rerun()

def render_delete_confirmation(
    vessel: Dict[str, Any],
    vessel_service: VesselService,
    key: str = "delete_confirm"
) -> bool:
    """
    Render delete confirmation dialog
    
    Args:
        vessel: Vessel to delete
        vessel_service: VesselService instance
        key: Unique key for the component
        
    Returns:
        True if deletion was confirmed and successful
    """
    st.warning(f" Are you sure you want to delete vessel **{vessel.get('name', 'Unknown')}**?")
    st.write("This action cannot be undone.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button(" Delete", key=f"{key}_confirm", type="primary"):
            success, message = vessel_service.delete_vessel(vessel['id'])
            if success:
                st.success(f" {message}")
                return True
            else:
                st.error(f" {message}")
                return False
    
    with col3:
        if st.button("Cancel", key=f"{key}_cancel"):
            return False
    
    return False