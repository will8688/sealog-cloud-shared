"""
Vessel Service - Core Business Logic
Centralized vessel management for maritime applications

This service provides the main interface for vessel operations across
Ships Log, Radio Log, Crew Log, and future maritime tools.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging
from dataclasses import asdict

# Import your existing vessel schema
from vessel_schema import (
    BaseVessel, YachtSchema, VesselType, create_vessel_from_type,
    validate_vessel_data, export_vessel_to_json
)

# Import separate modules (to be created next)
from vessel_database import VesselDatabase
from vessel_validation import VesselValidator
from vessel_external_apis import ExternalVesselAPIs

logger = logging.getLogger(__name__)

class VesselService:
    """
    Core vessel management service
    Handles all vessel operations across maritime tools
    """
    
    def __init__(self, db_manager, user_id: str = None):
        """
        Initialize vessel service
        
        Args:
            db_manager: Database manager instance
            user_id: Current user ID for user-specific operations
        """
        self.db = VesselDatabase(db_manager)
        self.validator = VesselValidator()
        self.external_apis = ExternalVesselAPIs()
        self.current_user_id = user_id
        
    # ============================================================================
    # USER VESSEL OPERATIONS
    # ============================================================================
    
    def get_user_vessels(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all vessels associated with a user
        
        Args:
            user_id: User ID (uses current_user_id if not provided)
            
        Returns:
            List of vessel dictionaries with basic info
        """
        user_id = user_id or self.current_user_id
        if not user_id:
            raise ValueError("User ID required")
            
        try:
            vessels = self.db.get_vessels_by_user(user_id)
            return [self._format_vessel_summary(vessel) for vessel in vessels]
        except Exception as e:
            logger.error(f"Error getting user vessels: {e}")
            return []
    
    def get_user_vessel_count(self, user_id: str = None) -> int:
        """Get count of vessels for user"""
        user_id = user_id or self.current_user_id
        vessels = self.get_user_vessels(user_id)
        return len(vessels)
    
    def has_multiple_vessels(self, user_id: str = None) -> bool:
        """Check if user has multiple vessels"""
        return self.get_user_vessel_count(user_id) > 1
    
    # ============================================================================
    # VESSEL RETRIEVAL
    # ============================================================================
    
    def get_vessel_by_id(self, vessel_id: str) -> Optional[BaseVessel]:
        """
        Get complete vessel data by ID
        
        Args:
            vessel_id: Vessel database ID
            
        Returns:
            BaseVessel or YachtSchema object, or None if not found
        """
        try:
            vessel_data = self.db.get_vessel_by_id(vessel_id)
            if vessel_data:
                return self._create_vessel_object(vessel_data)
            return None
        except Exception as e:
            logger.error(f"Error getting vessel by ID {vessel_id}: {e}")
            return None
    
    def find_vessel_by_identifier(
        self, 
        imo_number: str = None, 
        mmsi_number: str = None,
        call_sign: str = None,
        vessel_name: str = None
    ) -> Optional[BaseVessel]:
        """
        Find vessel by any unique identifier
        Prevents duplicate vessel creation
        
        Args:
            imo_number: IMO number
            mmsi_number: MMSI number  
            call_sign: Call sign
            vessel_name: Vessel name
            
        Returns:
            BaseVessel object or None
        """
        try:
            vessel_data = self.db.find_vessel_by_identifier(
                imo_number, mmsi_number, call_sign, vessel_name
            )
            if vessel_data:
                return self._create_vessel_object(vessel_data)
            return None
        except Exception as e:
            logger.error(f"Error finding vessel: {e}")
            return None
    
    def search_vessels(self, query: str, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Search vessels by name, IMO, MMSI, or call sign
        
        Args:
            query: Search query
            user_id: Limit to user's vessels (optional)
            
        Returns:
            List of matching vessel summaries
        """
        try:
            vessels = self.db.search_vessels(query, user_id)
            return [self._format_vessel_summary(vessel) for vessel in vessels]
        except Exception as e:
            logger.error(f"Error searching vessels: {e}")
            return []
    
    # ============================================================================
    # VESSEL CREATION AND UPDATES
    # ============================================================================
    
    def create_vessel(
        self, 
        vessel_data: Dict[str, Any], 
        user_id: str = None,
        auto_enrich: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create new vessel with validation and optional data enrichment
        
        Args:
            vessel_data: Dictionary of vessel data
            user_id: User to associate vessel with
            auto_enrich: Whether to enrich data from external APIs
            
        Returns:
            Tuple of (success: bool, message: str, vessel_id: str)
        """
        user_id = user_id or self.current_user_id
        if not user_id:
            return False, "User ID required", None
            
        try:
            # Create vessel object from data
            vessel_type = VesselType(vessel_data.get('vessel_type', 'yacht'))
            vessel = create_vessel_from_type(vessel_type)
            
            # Populate vessel object
            self._populate_vessel_from_dict(vessel, vessel_data)
            
            # Validate vessel data
            is_valid, validation_errors = validate_vessel_data(vessel)
            if not is_valid:
                return False, f"Validation errors: {'; '.join(validation_errors)}", None
            
            # Check for duplicates
            existing = self.find_vessel_by_identifier(
                vessel.imo_number, 
                getattr(vessel, 'mmsi_number', None),
                vessel.call_sign,
                vessel.vessel_name
            )
            if existing:
                return False, "Vessel already exists with these identifiers", None
            
            # Enrich data from external sources if requested
            if auto_enrich:
                enriched_vessel = self._enrich_vessel_data(vessel)
                if enriched_vessel:
                    vessel = enriched_vessel
            
            # Save to database
            vessel_id = self.db.create_vessel(vessel, user_id)
            
            logger.info(f"Created vessel {vessel.vessel_name} with ID {vessel_id}")
            return True, "Vessel created successfully", vessel_id
            
        except Exception as e:
            logger.error(f"Error creating vessel: {e}")
            return False, f"Failed to create vessel: {str(e)}", None

    def create_vessel_from_dict(
        self, 
        vessel_data: Dict[str, Any], 
        user_id: str = None,
        auto_enrich: bool = False,
        skip_validation: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """Create vessel directly from dictionary data (for simple forms)"""
        user_id = user_id or self.current_user_id
        if not user_id:
            return False, "User ID required", None
            
        try:
            # Validate required fields
            if not vessel_data.get('vessel_name', '').strip():
                return False, "Vessel name is required", None
            
            if not vessel_data.get('vessel_type'):
                return False, "Vessel type is required", None
            
            # Convert vessel_type string to enum if needed
            vessel_type = vessel_data.get('vessel_type')
            if isinstance(vessel_type, str):
                try:
                    vessel_type_enum = VesselType(vessel_type)
                    vessel_data['vessel_type'] = vessel_type_enum
                except ValueError:
                    return False, f"Invalid vessel type: {vessel_type}", None
            
            # Create vessel object
            vessel_type_enum = vessel_data['vessel_type']
            vessel = create_vessel_from_type(vessel_type_enum)
            
            # Populate vessel object from dictionary
            self._populate_vessel_from_dict(vessel, vessel_data)
            
            # Skip validation if requested (for imports without identifiers)
            if not skip_validation:
                # Basic validation
                is_valid, validation_errors = self.validator.validate_vessel(vessel)
                if not is_valid:
                    return False, f"Validation errors: {'; '.join(validation_errors)}", None
            
            # Check for duplicates only if we have identifiers
            if vessel_data.get('imo_number'):
                existing = self.find_vessel_by_identifier(imo_number=vessel_data['imo_number'])
                if existing:
                    return False, "Vessel with this IMO number already exists", None
            
            # Enrich data if requested
            if auto_enrich:
                enriched_vessel = self._enrich_vessel_data(vessel)
                if enriched_vessel:
                    vessel = enriched_vessel
            
            # Save to database
            vessel_id = self.db.create_vessel(vessel, user_id)
            
            logger.info(f"Created vessel {vessel.vessel_name} with ID {vessel_id}")
            return True, "Vessel created successfully", vessel_id
            
        except Exception as e:
            logger.error(f"Error creating vessel from dictionary: {e}")
            return False, f"Failed to create vessel: {str(e)}", None
    
    def update_vessel(
        self, 
        vessel_id: str, 
        updated_data: Dict[str, Any],
        user_id: str = None
    ) -> Tuple[bool, str]:
        """
        Update existing vessel
        
        Args:
            vessel_id: Vessel ID to update
            updated_data: Dictionary of fields to update
            user_id: User making the update
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        user_id = user_id or self.current_user_id
        
        try:
            # Get existing vessel
            vessel = self.get_vessel_by_id(vessel_id)
            if not vessel:
                return False, "Vessel not found"
            
            # Check user has permission to update
            if not self._user_can_modify_vessel(user_id, vessel_id):
                return False, "Permission denied"
            
            # Update vessel object
            self._populate_vessel_from_dict(vessel, updated_data)
            
            # Validate updated data
            is_valid, validation_errors = validate_vessel_data(vessel)
            if not is_valid:
                return False, f"Validation errors: {'; '.join(validation_errors)}"
            
            # Update in database
            success = self.db.update_vessel(vessel_id, vessel)
            
            if success:
                logger.info(f"Updated vessel {vessel_id}")
                return True, "Vessel updated successfully"
            else:
                return False, "Failed to update vessel"
                
        except Exception as e:
            logger.error(f"Error updating vessel {vessel_id}: {e}")
            return False, f"Update failed: {str(e)}"
    
    def delete_vessel(self, vessel_id: str, user_id: str = None) -> Tuple[bool, str]:
        """
        Delete vessel (soft delete - mark as inactive)
        
        Args:
            vessel_id: Vessel ID to delete
            user_id: User requesting deletion
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        user_id = user_id or self.current_user_id
        
        try:
            # Check permissions
            if not self._user_can_modify_vessel(user_id, vessel_id):
                return False, "Permission denied"
            
            # Check if vessel is being used in logs
            usage_count = self.db.get_vessel_usage_count(vessel_id)
            if usage_count > 0:
                return False, f"Cannot delete vessel - used in {usage_count} log entries"
            
            # Soft delete
            success = self.db.delete_vessel(vessel_id)
            
            if success:
                logger.info(f"Deleted vessel {vessel_id}")
                return True, "Vessel deleted successfully"
            else:
                return False, "Failed to delete vessel"
                
        except Exception as e:
            logger.error(f"Error deleting vessel {vessel_id}: {e}")
            return False, f"Delete failed: {str(e)}"
    
    # ============================================================================
    # VESSEL ASSOCIATION MANAGEMENT
    # ============================================================================
    
    def associate_user_with_vessel(
        self, 
        user_id: str, 
        vessel_id: str, 
        role: str = "operator"
    ) -> Tuple[bool, str]:
        """
        Associate user with vessel
        
        Args:
            user_id: User ID
            vessel_id: Vessel ID
            role: User role (owner, operator, crew)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.db.associate_user_with_vessel(user_id, vessel_id, role)
            if success:
                return True, "User associated with vessel"
            else:
                return False, "Failed to associate user with vessel"
        except Exception as e:
            logger.error(f"Error associating user {user_id} with vessel {vessel_id}: {e}")
            return False, f"Association failed: {str(e)}"
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _format_vessel_summary(self, vessel_data: Dict) -> Dict[str, Any]:
        """Format vessel data for display in dropdowns/lists"""
        return {
            'id': vessel_data.get('id'),
            'name': vessel_data.get('vessel_name', 'Unknown'),
            'imo_number': vessel_data.get('imo_number'),
            'mmsi_number': vessel_data.get('mmsi_number'),
            'call_sign': vessel_data.get('call_sign'),
            'vessel_type': vessel_data.get('vessel_type'),
            'flag_state': vessel_data.get('flag_state'),
            'display_name': self._create_display_name(vessel_data)
        }
    
    def _create_display_name(self, vessel_data: Dict) -> str:
        """Create user-friendly display name for vessel selection"""
        name = vessel_data.get('vessel_name', 'Unknown Vessel')
        identifiers = []
        
        if vessel_data.get('imo_number'):
            identifiers.append(f"IMO: {vessel_data['imo_number']}")
        elif vessel_data.get('mmsi_number'):
            identifiers.append(f"MMSI: {vessel_data['mmsi_number']}")
        elif vessel_data.get('call_sign'):
            identifiers.append(f"Call: {vessel_data['call_sign']}")
        
        if identifiers:
            return f"{name} ({identifiers[0]})"
        return name
    
    def _create_vessel_object(self, vessel_data: Dict) -> BaseVessel:
        """Create appropriate vessel object from database data"""
        vessel_type = VesselType(vessel_data.get('vessel_type', 'yacht'))
        vessel = create_vessel_from_type(vessel_type)
        self._populate_vessel_from_dict(vessel, vessel_data)
        return vessel
    
    def _populate_vessel_from_dict(self, vessel: BaseVessel, data: Dict):
        """Populate vessel object from dictionary data"""
        for key, value in data.items():
            if hasattr(vessel, key) and value is not None:
                setattr(vessel, key, value)
    
    def _enrich_vessel_data(self, vessel: BaseVessel) -> Optional[BaseVessel]:
        """Enrich vessel data from external APIs"""
        try:
            if vessel.imo_number:
                enriched_data = self.external_apis.get_vessel_by_imo(vessel.imo_number)
                if enriched_data and enriched_data.success:
                    self._populate_vessel_from_dict(vessel, enriched_data.data)
                    return vessel
        except Exception as e:
            logger.warning(f"Failed to enrich vessel data: {e}")
        
        return vessel
    
    def _user_can_modify_vessel(self, user_id: str, vessel_id: str) -> bool:
        """Check if user has permission to modify vessel"""
        try:
            return self.db.user_has_vessel_access(user_id, vessel_id)
        except Exception:
            return False