"""
Crew Settings - Management Panel
# ==============================
Crew management integration for settings panel
"""

import streamlit as st
from typing import List, Dict, Any, Optional

from tools.crew_management.core.models import CrewMember
from tools.crew_management.core.constants import SESSION_KEYS
from tools.crew_management.services.crew_service import CrewService
from tools.crew_management.forms.basic_crew_form import (
    BasicCrewForm, render_crew_invitation_form, render_crew_delete_confirmation
)
from tools.crew_management.data.schema import initialize_crew_database_silent

class CrewManagementPanel:
    """Crew management panel for settings"""
     
    def __init__(self, user_id: str, db_manager, vessel_service):
        """
        Initialize crew management panel
            
        Args:
            user_id: Current user ID
            db_manager: Database manager instance from settings
            vessel_service: VesselService instance from settings
        """
        self.user_id = user_id
        self.db_manager = db_manager
        self.vessel_service = vessel_service
            
        try:
            # Ensure db is in session state for CrewService
            if not hasattr(st.session_state, 'db') or st.session_state.db is None:
                st.session_state.db = self.db_manager
            
            # Initialize crew service (gets db from session state)
            self.crew_service = CrewService()
                
            # Initialize crew database if needed
            if not hasattr(st.session_state, 'crew_db_initialized'):
                if initialize_crew_database_silent():
                    st.session_state.crew_db_initialized = True
            
        except Exception as e:
            st.error(f" Error initializing crew management: {str(e)}")
            self.crew_service = None
    
    def render(self) -> None:
        """Render the crew management panel"""
        try:
            # Check if services are available
            if not self.crew_service or not self.vessel_service:
                st.error(" Crew management services not available")
                return
            
            # Get user's vessels
            vessels = self.vessel_service.get_user_vessels(self.user_id)
            
            if not vessels:
                st.info(" **No vessels found**\n\nAdd a vessel first to manage crew members.")
                return
            
            # Handle vessels as dictionaries or objects
            vessel_options = {}
            for v in vessels:
                if hasattr(v, 'vessel_name'):
                    # Object access
                    vessel_options[v.vessel_name] = v
                elif isinstance(v, dict):
                    # Dictionary access - try multiple possible keys
                    name = v.get('vessel_name') or v.get('name') or v.get('display_name') or str(v.get('id', 'Unknown Vessel'))
                    vessel_options[name] = v
                else:
                    # Fallback
                    vessel_options[f"Vessel {id(v)}"] = v
            
            selected_vessel_name = st.selectbox(
                "Select Vessel",
                options=list(vessel_options.keys()),
                key=SESSION_KEYS.get('vessel_select', 'crew_vessel_select')
            )
            
            if not selected_vessel_name:
                return
            
            selected_vessel = vessel_options[selected_vessel_name]
            
            # Main crew management interface
            self._render_crew_management(selected_vessel)
        
        except Exception as e:
            st.error(f" Error rendering crew management panel: {str(e)}")
    
    def _render_crew_management(self, vessel) -> None:
        """
        Render crew management for selected vessel
        
        Args:
            vessel: Selected vessel object or dictionary
        """
        try:
            # Safe vessel ID and name access
            if hasattr(vessel, 'id'):
                vessel_id = vessel.id
                vessel_name = vessel.vessel_name
            elif isinstance(vessel, dict):
                vessel_id = vessel.get('id')
                vessel_name = vessel.get('vessel_name') or vessel.get('name') or vessel.get('display_name') or 'Unknown Vessel'
            else:
                st.error(" Invalid vessel data format")
                return
            
            # Get current crew
            crew_list = self.crew_service.get_vessel_crew_list(
                vessel_id, 
                include_assignments=True
            )
            
            # Tabs for different crew management functions
            tab1, tab2, tab3 = st.tabs([" Crew List", " Add Crew", " Invitations"])
            
            with tab1:
                self._render_crew_list_tab(vessel, crew_list)
            
            with tab2:
                self._render_add_crew_tab(vessel)
            
            with tab3:
                self._render_invitations_tab(vessel)
        
        except Exception as e:
            st.error(f" Error rendering crew management: {str(e)}")
    
    def _render_crew_list_tab(self, vessel, crew_list: List[Dict[str, Any]]) -> None:
        """Render crew list tab"""
        try:
            # Safe vessel name access
            if hasattr(vessel, 'vessel_name'):
                vessel_name = vessel.vessel_name
            elif isinstance(vessel, dict):
                vessel_name = vessel.get('vessel_name') or vessel.get('name') or vessel.get('display_name') or 'Unknown Vessel'
            else:
                vessel_name = 'Unknown Vessel'
            
            if not crew_list:
                st.info(" **No crew members added yet**\n\n"
                       "Use the 'Add Crew' tab to add your first crew member.")
                return
            
            st.write(f"**{len(crew_list)} crew members on {vessel_name}**")
            
            # Crew statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                officers = len([c for c in crew_list if c.get('is_officer', False)])
                st.metric("Officers", officers)
            
            with col2:
                platform_users = len([c for c in crew_list if c.get('has_platform_access', False)])
                st.metric("Platform Access", platform_users)
            
            with col3:
                cert_warnings = len([c for c in crew_list if 'EXPIRES' in c.get('certificate_status', '')])
                st.metric("Cert Warnings", cert_warnings)
            
            st.divider()
            
            # Crew list with actions
            for idx, crew_info in enumerate(crew_list):
                try:
                    with st.container():
                        # Get full crew member object for actions
                        crew_member = self.crew_service.repo.get_crew_member(crew_info['id'])
                        if not crew_member:
                            continue
                        
                        # Render crew member with actions
                        form = BasicCrewForm()
                        action = form.render_crew_list_item(crew_member, show_actions=True)
                        
                        # Handle actions using SESSION_KEYS consistently
                        if action == "edit":
                            st.session_state[SESSION_KEYS.get('editing_crew_id', 'editing_crew_id')] = crew_member.id
                            st.rerun()
                        
                        elif action == "invite":
                            st.session_state[SESSION_KEYS.get('inviting_crew_id', 'inviting_crew_id')] = crew_member.id
                            st.rerun()
                        
                        elif action == "delete":
                            st.session_state[SESSION_KEYS.get('deleting_crew_id', 'deleting_crew_id')] = crew_member.id
                            st.rerun()
                        
                        # Show platform access status
                        if crew_info.get('has_platform_access'):
                            permissions = crew_info.get('permissions', [])
                            if permissions:
                                st.success(f" Platform Access: {', '.join(permissions)}")
                            else:
                                st.warning(" Platform access granted but no log permissions")
                        
                        st.divider()
                
                except Exception as e:
                    st.error(f" Error displaying crew member: {str(e)}")
            
            # Handle modals
            editing_key = SESSION_KEYS.get('editing_crew_id', 'editing_crew_id')
            inviting_key = SESSION_KEYS.get('inviting_crew_id', 'inviting_crew_id')
            deleting_key = SESSION_KEYS.get('deleting_crew_id', 'deleting_crew_id')
            
            if editing_key in st.session_state:
                self._handle_edit_crew_modal(vessel)
            
            if inviting_key in st.session_state:
                self._handle_invite_crew_modal(vessel)
            
            if deleting_key in st.session_state:
                self._handle_delete_crew_modal(vessel)
        
        except Exception as e:
            st.error(f" Error rendering crew list: {str(e)}")
    
    def _render_add_crew_tab(self, vessel) -> None:
        """Render add crew tab"""
        try:
            st.write("Add new crew members to your vessel.")
            
            # Safe vessel access
            if hasattr(vessel, 'id'):
                vessel_id = vessel.id
                vessel_name = vessel.vessel_name
            elif isinstance(vessel, dict):
                vessel_id = vessel.get('id')
                vessel_name = vessel.get('vessel_name') or vessel.get('name') or vessel.get('display_name') or 'Unknown Vessel'
            else:
                st.error(" Invalid vessel data")
                return
            
            # Basic crew form
            form = BasicCrewForm()
            result = form.render(vessel_id, vessel_name)
            
            if result:
                if result.get("action") == "submit":
                    try:
                        # Add crew member
                        crew_id = self.crew_service.add_crew_member(
                            result["data"], 
                            self.user_id
                        )
                        
                        if crew_id:
                            st.success(f" **{result['data']['full_name']}** added to crew!")
                            st.info(" Use the 'Invitations' tab to invite them to the platform.")
                            st.rerun()
                        else:
                            st.error(" Failed to add crew member. Please try again.")
                    
                    except Exception as e:
                        st.error(f" Error adding crew member: {str(e)}")
                
                elif result.get("action") == "cancel":
                    st.info(" Crew member addition cancelled.")
        
        except Exception as e:
            st.error(f" Error rendering add crew tab: {str(e)}")
    
    def _render_invitations_tab(self, vessel) -> None:
        """Render invitations tab"""
        try:
            st.write("Invite crew members to join the platform.")
            
            # Safe vessel access
            if hasattr(vessel, 'id'):
                vessel_id = vessel.id
                vessel_name = vessel.vessel_name
            elif isinstance(vessel, dict):
                vessel_id = vessel.get('id')
                vessel_name = vessel.get('vessel_name') or vessel.get('name') or vessel.get('display_name') or 'Unknown Vessel'
            else:
                st.error(" Invalid vessel data")
                return
            
            # Get invitation status
            try:
                invitation_status = self.crew_service.get_invitation_status(vessel_id)
                
                if invitation_status:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Sent", invitation_status.get('total_sent', 0))
                    with col2:
                        st.metric("Pending", invitation_status.get('pending', 0))
                    with col3:
                        st.metric("Accepted", invitation_status.get('accepted', 0))
            
            except Exception as e:
                st.warning(f"Could not load invitation status: {str(e)}")
            
            # Get pending invitations
            try:
                pending_invites = self.crew_service.repo.get_vessel_invitations(
                    vessel_id, 
                    pending_only=True
                )
                
                if pending_invites:
                    st.subheader(" Pending Invitations")
                    
                    for invite in pending_invites:
                        try:
                            with st.container():
                                col1, col2, col3 = st.columns([2, 2, 1])
                                
                                with col1:
                                    st.write(f"**{invite.email}**")
                                    if invite.crew_member_id:
                                        crew_member = self.crew_service.repo.get_crew_member(invite.crew_member_id)
                                        if crew_member:
                                            st.caption(f"For: {crew_member.full_name} ({crew_member.rank_position})")
                                
                                with col2:
                                    days_left = invite.days_until_expiry
                                    if days_left > 0:
                                        st.write(f" Expires in {days_left} days")
                                    else:
                                        st.write(" Expired")
                                
                                with col3:
                                    if st.button("", key=f"resend_{invite.id}", help="Resend invitation"):
                                        st.info("Resend feature coming soon!")
                            
                            st.divider()
                        
                        except Exception as e:
                            st.error(f"Error displaying invitation: {str(e)}")
            
            except Exception as e:
                st.error(f" Error loading pending invitations: {str(e)}")
            
            # Quick invite section
            st.subheader(" Send New Invitation")
            
            with st.form("quick_invite_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    email = st.text_input("Email Address", placeholder="crew@example.com")
                
                with col2:
                    try:
                        # Optional crew member selection
                        crew_list = self.crew_service.repo.get_vessel_crew(vessel_id)
                        crew_options = {"None - General Invitation": None}
                        crew_options.update({
                            f"{c.full_name} ({c.rank_position})": c.id 
                            for c in crew_list
                        })
                        
                        selected_crew = st.selectbox(
                            "Link to Crew Member (Optional)",
                            options=list(crew_options.keys())
                        )
                    
                    except Exception as e:
                        st.error(f"Error loading crew options: {str(e)}")
                        crew_options = {"None - General Invitation": None}
                        selected_crew = "None - General Invitation"
                
                if st.form_submit_button(" Send Invitation"):
                    if email and "@" in email:
                        try:
                            crew_member_id = crew_options.get(selected_crew)
                            
                            invite_id = self.crew_service.send_crew_invitation(
                                email=email,
                                vessel_id=vessel_id,
                                vessel_name=vessel_name,
                                invited_by=self.user_id,
                                crew_member_id=crew_member_id
                            )
                            
                            if invite_id:
                                st.success(f" Invitation sent to {email}")
                                st.rerun()
                            else:
                                st.error(" Failed to send invitation. They may already have a pending invitation.")
                        
                        except Exception as e:
                            st.error(f" Error sending invitation: {str(e)}")
                    else:
                        st.error(" Please enter a valid email address")
        
        except Exception as e:
            st.error(f" Error rendering invitations tab: {str(e)}")
    
    def _handle_edit_crew_modal(self, vessel) -> None:
        """Handle edit crew modal"""
        editing_key = SESSION_KEYS.get('editing_crew_id', 'editing_crew_id')
        
        try:
            crew_id = st.session_state[editing_key]
            crew_member = self.crew_service.repo.get_crew_member(crew_id)
            
            if not crew_member:
                del st.session_state[editing_key]
                st.rerun()
                return
            
            # Safe vessel access for modal
            if hasattr(vessel, 'id'):
                vessel_id = vessel.id
                vessel_name = vessel.vessel_name
            elif isinstance(vessel, dict):
                vessel_id = vessel.get('id')
                vessel_name = vessel.get('vessel_name') or vessel.get('name') or vessel.get('display_name') or 'Unknown Vessel'
            else:
                st.error(" Invalid vessel data")
                return
            
            with st.container():
                st.subheader(f" Edit {crew_member.full_name}")
                
                form = BasicCrewForm(crew_member)
                result = form.render(vessel_id, vessel_name)
                
                if result:
                    if result.get("action") == "submit":
                        try:
                            # Update crew member
                            success = self.crew_service.update_crew_member(
                                crew_id,
                                result["data"]
                            )
                            
                            if success:
                                st.success(" Crew member updated successfully!")
                                del st.session_state[editing_key]
                                st.rerun()
                            else:
                                st.error(" Failed to update crew member.")
                        
                        except Exception as e:
                            st.error(f" Error updating crew member: {str(e)}")
                    
                    elif result.get("action") == "cancel":
                        del st.session_state[editing_key]
                        st.rerun()
        
        except Exception as e:
            st.error(f" Error handling edit modal: {str(e)}")
            # Clean up session state on error
            if editing_key in st.session_state:
                del st.session_state[editing_key]
    
    def _handle_invite_crew_modal(self, vessel) -> None:
        """Handle invite crew modal"""
        inviting_key = SESSION_KEYS.get('inviting_crew_id', 'inviting_crew_id')
        
        try:
            crew_id = st.session_state[inviting_key]
            crew_member = self.crew_service.repo.get_crew_member(crew_id)
            
            if not crew_member:
                del st.session_state[inviting_key]
                st.rerun()
                return
            
            # Safe vessel access for modal
            if hasattr(vessel, 'id'):
                vessel_id = vessel.id
                vessel_name = vessel.vessel_name
            elif isinstance(vessel, dict):
                vessel_id = vessel.get('id')
                vessel_name = vessel.get('vessel_name') or vessel.get('name') or vessel.get('display_name') or 'Unknown Vessel'
            else:
                st.error(" Invalid vessel data")
                return
            
            with st.container():
                email = render_crew_invitation_form(crew_member)
                
                if email == "cancel":
                    del st.session_state[inviting_key]
                    st.rerun()
                
                elif email:
                    try:
                        invite_id = self.crew_service.send_crew_invitation(
                            email=email,
                            vessel_id=vessel_id,
                            vessel_name=vessel_name,
                            invited_by=self.user_id,
                            crew_member_id=crew_id
                        )
                        
                        if invite_id:
                            st.success(f" Invitation sent to {email}")
                            del st.session_state[inviting_key]
                            st.rerun()
                        else:
                            st.error(" Failed to send invitation. They may already have a pending invitation.")
                    
                    except Exception as e:
                        st.error(f" Error sending invitation: {str(e)}")
        
        except Exception as e:
            st.error(f" Error handling invite modal: {str(e)}")
            # Clean up session state on error
            if inviting_key in st.session_state:
                del st.session_state[inviting_key]
    
    def _handle_delete_crew_modal(self, vessel) -> None:
        """Handle delete crew modal"""
        deleting_key = SESSION_KEYS.get('deleting_crew_id', 'deleting_crew_id')
        
        try:
            crew_id = st.session_state[deleting_key]
            crew_member = self.crew_service.repo.get_crew_member(crew_id)
            
            if not crew_member:
                del st.session_state[deleting_key]
                st.rerun()
                return
            
            with st.container():
                confirmed = render_crew_delete_confirmation(crew_member)
                
                if confirmed is True:
                    try:
                        # Remove crew member
                        success = self.crew_service.remove_crew_member(crew_id)
                        
                        if success:
                            st.success(f" {crew_member.full_name} removed from crew")
                            del st.session_state[deleting_key]
                            st.rerun()
                        else:
                            st.error(" Failed to remove crew member")
                    
                    except Exception as e:
                        st.error(f" Error removing crew member: {str(e)}")
                
                elif confirmed is False:
                    del st.session_state[deleting_key]
                    st.rerun()
        
        except Exception as e:
            st.error(f" Error handling delete modal: {str(e)}")
            # Clean up session state on error
            if deleting_key in st.session_state:
                del st.session_state[deleting_key]


def render_crew_management_panel(user_id: str) -> None:
    """
    Render crew management panel for settings
    Updated to work consistently with settings.py integration
    
    Args:
        user_id: Current user ID
    """
    try:
        # Get database manager from settings.py import
        from database_manager import db_manager
        
        # Check if VesselService is already initialized in settings
        if hasattr(st.session_state, 'settings_vessel_service'):
            # Reuse the vessel service from settings
            vessel_service = st.session_state.settings_vessel_service
        else:
            # Import and create vessel service if needed
            from shared.vessel_service import VesselService
            vessel_service = VesselService(db_manager, user_id)
            # Store for reuse
            st.session_state.settings_vessel_service = vessel_service
        
        # Ensure db is in session state for CrewService
        if not hasattr(st.session_state, 'db') or st.session_state.db is None:
            st.session_state.db = db_manager
        
        # Create and render panel with consistent services
        panel = CrewManagementPanel(user_id, db_manager, vessel_service)
        panel.render()
        
    except Exception as e:
        st.error(f" Error loading crew management: {str(e)}")
        st.info(" Please refresh the page or contact support if the problem persists.")