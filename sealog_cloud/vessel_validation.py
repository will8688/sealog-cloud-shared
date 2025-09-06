"""
Vessel Data Validation
Comprehensive validation logic for vessel data integrity

This module provides validation functions for vessel data to ensure
compliance with IMO standards, data integrity, and business rules
across the maritime application suite.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date
import logging

from schemas.vessel_schema import VesselType, BaseVessel, YachtSchema

logger = logging.getLogger(__name__)

class VesselValidator:
    """
    Comprehensive vessel data validation
    Ensures data integrity and compliance with maritime standards
    """
    
    def __init__(self):
        # IMO check digit algorithm weights
        self.imo_weights = [7, 1, 3, 1, 7, 1, 3]
        
        # Country code mappings for validation
        self.valid_country_codes = {
            # Major maritime nations (expandable)
            'GB': 'United Kingdom', 'US': 'United States', 'IT': 'Italy',
            'FR': 'France', 'DE': 'Germany', 'NL': 'Netherlands',
            'GR': 'Greece', 'NO': 'Norway', 'DK': 'Denmark',
            'ES': 'Spain', 'PT': 'Portugal', 'MT': 'Malta',
            'CY': 'Cyprus', 'PA': 'Panama', 'LR': 'Liberia',
            'MH': 'Marshall Islands', 'BS': 'Bahamas', 'KY': 'Cayman Islands'
        }
        
        # MMSI Maritime Identification Digits (MID)
        self.valid_mids = {
            '232': 'United Kingdom', '338': 'United States', '247': 'Italy',
            '227': 'France', '211': 'Germany', '244': 'Netherlands',
            '237': 'Greece', '257': 'Norway', '219': 'Denmark',
            '224': 'Spain', '263': 'Portugal', '215': 'Malta',
            '209': 'Cyprus', '351': 'Panama', '636': 'Liberia',
            '538': 'Marshall Islands', '311': 'Bahamas', '319': 'Cayman Islands'
        }
    
    # ============================================================================
    # MAIN VALIDATION FUNCTIONS
    # ============================================================================
    
    def validate_vessel(self, vessel: BaseVessel) -> Tuple[bool, List[str]]:
        """
        Comprehensive vessel validation
        
        Args:
            vessel: Vessel object to validate
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Basic required field validation
        errors.extend(self._validate_required_fields(vessel))
        
        # Identifier validation
        errors.extend(self._validate_identifiers(vessel))
        
        # Dimension validation
        errors.extend(self._validate_dimensions(vessel))
        
        # Date validation
        errors.extend(self._validate_dates(vessel))
        
        # Business logic validation
        errors.extend(self._validate_business_rules(vessel))
        
        # Type-specific validation
        if isinstance(vessel, YachtSchema):
            errors.extend(self._validate_yacht_specific(vessel))
        
        return len(errors) == 0, errors
    
    def validate_vessel_data(self, vessel_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate vessel data dictionary (before creating vessel object)
        
        Args:
            vessel_data: Dictionary of vessel data
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Basic field validation
        errors.extend(self._validate_vessel_data_fields(vessel_data))
        
        # Identifier validation from dict
        errors.extend(self._validate_identifiers_from_dict(vessel_data))
        
        # Dimension validation from dict
        errors.extend(self._validate_dimensions_from_dict(vessel_data))
        
        return len(errors) == 0, errors
    
    # ============================================================================
    # REQUIRED FIELDS VALIDATION
    # ============================================================================
    
    def _validate_required_fields(self, vessel: BaseVessel) -> List[str]:
        """Validate required fields are present"""
        errors = []
        
        if not vessel.vessel_name or vessel.vessel_name.strip() == '':
            errors.append("Vessel name is required")
        
        if not vessel.vessel_type:
            errors.append("Vessel type is required")
        
        # At least one identifier should be present
        identifiers = [
            vessel.imo_number,
            getattr(vessel, 'mmsi_number', None),
            vessel.call_sign,
            vessel.official_number
        ]
        
        if not any(id for id in identifiers if id and id.strip()):
            errors.append("At least one vessel identifier (IMO, MMSI, Call Sign, or Official Number) is required")
        
        return errors
    
    def _validate_vessel_data_fields(self, vessel_data: Dict[str, Any]) -> List[str]:
        """Validate required fields from dictionary"""
        errors = []
        
        if not vessel_data.get('vessel_name', '').strip():
            errors.append("Vessel name is required")
        
        if not vessel_data.get('vessel_type'):
            errors.append("Vessel type is required")
        
        # Check vessel type is valid
        vessel_type = vessel_data.get('vessel_type')
        if vessel_type:
            valid_types = [vt.value for vt in VesselType]
            if vessel_type not in valid_types:
                errors.append(f"Invalid vessel type: {vessel_type}")
        
        return errors
    
    # ============================================================================
    # IDENTIFIER VALIDATION
    # ============================================================================
    
    def validate_imo_number(self, imo_number: str) -> Tuple[bool, str]:
        """
        Validate IMO number using check digit algorithm
        
        Args:
            imo_number: IMO number string
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not imo_number:
            return True, ""  # Optional field
        
        # Remove any spaces or formatting
        imo_clean = re.sub(r'[^\d]', '', imo_number)
        
        # Must be exactly 7 digits
        if len(imo_clean) != 7:
            return False, "IMO number must be exactly 7 digits"
        
        # Check digit validation
        if not self._validate_imo_check_digit(imo_clean):
            return False, "Invalid IMO number - check digit verification failed"
        
        return True, ""
    
    def validate_mmsi_number(self, mmsi_number: str) -> Tuple[bool, str]:
        """
        Validate MMSI number format and MID
        
        Args:
            mmsi_number: MMSI number string
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not mmsi_number:
            return True, ""  # Optional field
        
        # Remove any spaces or formatting
        mmsi_clean = re.sub(r'[^\d]', '', mmsi_number)
        
        # Must be exactly 9 digits
        if len(mmsi_clean) != 9:
            return False, "MMSI number must be exactly 9 digits"
        
        # First three digits are Maritime Identification Digits (MID)
        mid = mmsi_clean[:3]
        
        # Basic MID validation (not exhaustive but catches common errors)
        if mid.startswith('0'):
            return False, "MMSI number cannot start with 0"
        
        # Optional: Validate against known MIDs
        # (This is informational, not strictly required)
        if mid in self.valid_mids:
            logger.debug(f"MMSI MID {mid} corresponds to {self.valid_mids[mid]}")
        
        return True, ""
    
    def validate_call_sign(self, call_sign: str) -> Tuple[bool, str]:
        """
        Validate radio call sign format
        
        Args:
            call_sign: Call sign string
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not call_sign:
            return True, ""  # Optional field
        
        # Basic format validation - alphanumeric, 3-7 characters
        if not re.match(r'^[A-Z0-9]{3,7}$', call_sign.upper()):
            return False, "Call sign must be 3-7 alphanumeric characters"
        
        return True, ""
    
    def _validate_identifiers(self, vessel: BaseVessel) -> List[str]:
        """Validate all vessel identifiers"""
        errors = []
        
        # IMO validation
        is_valid, error = self.validate_imo_number(vessel.imo_number)
        if not is_valid:
            errors.append(error)
        
        # MMSI validation
        mmsi = getattr(vessel, 'mmsi_number', None)
        is_valid, error = self.validate_mmsi_number(mmsi)
        if not is_valid:
            errors.append(error)
        
        # Call sign validation
        is_valid, error = self.validate_call_sign(vessel.call_sign)
        if not is_valid:
            errors.append(error)
        
        return errors
    
    def _validate_identifiers_from_dict(self, vessel_data: Dict[str, Any]) -> List[str]:
        """Validate identifiers from dictionary"""
        errors = []
        
        # IMO validation
        imo = vessel_data.get('imo_number')
        if imo:
            is_valid, error = self.validate_imo_number(imo)
            if not is_valid:
                errors.append(error)
        
        # MMSI validation
        mmsi = vessel_data.get('mmsi_number')
        if mmsi:
            is_valid, error = self.validate_mmsi_number(mmsi)
            if not is_valid:
                errors.append(error)
        
        # Call sign validation
        call_sign = vessel_data.get('call_sign')
        if call_sign:
            is_valid, error = self.validate_call_sign(call_sign)
            if not is_valid:
                errors.append(error)
        
        return errors
    
    def _validate_imo_check_digit(self, imo_number: str) -> bool:
        """
        Validate IMO number using check digit algorithm
        
        Args:
            imo_number: 7-digit IMO number string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Calculate check digit
            total = 0
            for i in range(6):  # First 6 digits
                digit = int(imo_number[i])
                weight = self.imo_weights[i]
                total += digit * weight
            
            # Check digit is the last digit of the total
            calculated_check_digit = total % 10
            actual_check_digit = int(imo_number[6])
            
            return calculated_check_digit == actual_check_digit
            
        except (ValueError, IndexError):
            return False
    
    # ============================================================================
    # DIMENSION VALIDATION
    # ============================================================================
    
    def _validate_dimensions(self, vessel: BaseVessel) -> List[str]:
        """Validate vessel dimensions for logical consistency"""
        errors = []
        
        # All dimensions must be positive if provided
        dimension_fields = [
            ('length_overall', 'Length overall'),
            ('length_waterline', 'Length waterline'),
            ('beam', 'Beam'),
            ('draft', 'Draft'),
            ('depth', 'Depth'),
            ('air_draft', 'Air draft'),
            ('gross_tonnage', 'Gross tonnage'),
            ('net_tonnage', 'Net tonnage'),
            ('deadweight', 'Deadweight'),
            ('displacement', 'Displacement')
        ]
        
        for field_name, display_name in dimension_fields:
            value = getattr(vessel, field_name, None)
            if value is not None and value < 0:
                errors.append(f"{display_name} must be positive")
        
        # Logical dimension relationships
        if vessel.length_overall and vessel.length_waterline:
            if vessel.length_waterline > vessel.length_overall:
                errors.append("Length waterline cannot be greater than length overall")
        
        if vessel.gross_tonnage and vessel.net_tonnage:
            if vessel.net_tonnage > vessel.gross_tonnage:
                errors.append("Net tonnage cannot be greater than gross tonnage")
        
        # Reasonable limits (these can be adjusted)
        if vessel.length_overall:
            if vessel.length_overall > 500:  # 500m is extremely large
                errors.append("Length overall seems unreasonably large (>500m)")
            elif vessel.length_overall < 1:  # Less than 1m is too small
                errors.append("Length overall must be at least 1 meter")
        
        if vessel.beam and vessel.length_overall:
            if vessel.beam > vessel.length_overall:
                errors.append("Beam cannot be greater than length overall")
        
        return errors
    
    def _validate_dimensions_from_dict(self, vessel_data: Dict[str, Any]) -> List[str]:
        """Validate dimensions from dictionary"""
        errors = []
        
        # Check positive values
        numeric_fields = [
            'length_overall', 'length_waterline', 'beam', 'draft', 'depth',
            'air_draft', 'gross_tonnage', 'net_tonnage', 'deadweight', 'displacement'
        ]
        
        for field in numeric_fields:
            value = vessel_data.get(field)
            if value is not None:
                try:
                    numeric_value = float(value)
                    if numeric_value < 0:
                        errors.append(f"{field.replace('_', ' ').title()} must be positive")
                except (ValueError, TypeError):
                    errors.append(f"{field.replace('_', ' ').title()} must be a valid number")
        
        # Logical relationships
        loa = vessel_data.get('length_overall')
        lwl = vessel_data.get('length_waterline')
        beam = vessel_data.get('beam')
        
        if loa and lwl:
            try:
                if float(lwl) > float(loa):
                    errors.append("Length waterline cannot be greater than length overall")
            except (ValueError, TypeError):
                pass
        
        if loa and beam:
            try:
                if float(beam) > float(loa):
                    errors.append("Beam cannot be greater than length overall")
            except (ValueError, TypeError):
                pass
        
        return errors
    
    # ============================================================================
    # DATE VALIDATION
    # ============================================================================
    
    def _validate_dates(self, vessel: BaseVessel) -> List[str]:
        """Validate date fields"""
        errors = []
        
        current_year = datetime.now().year
        
        # Year built validation
        if vessel.year_built:
            if vessel.year_built < 1800:
                errors.append("Year built cannot be before 1800")
            elif vessel.year_built > current_year + 5:
                errors.append(f"Year built cannot be more than 5 years in the future ({current_year + 5})")
        
        # Survey date validation
        if vessel.survey_date:
            if vessel.survey_date > date.today():
                errors.append("Survey date cannot be in the future")
        
        # Certificate expiry validation
        if vessel.certificate_expiry:
            if vessel.certificate_expiry < date.today():
                errors.append("Certificate has expired")
        
        # Survey vs expiry relationship
        if vessel.survey_date and vessel.certificate_expiry:
            if vessel.survey_date > vessel.certificate_expiry:
                errors.append("Survey date cannot be after certificate expiry")
        
        return errors
    
    # ============================================================================
    # BUSINESS RULES VALIDATION
    # ============================================================================
    
    def _validate_business_rules(self, vessel: BaseVessel) -> List[str]:
        """Validate business logic rules"""
        errors = []
        
        # Flag state validation
        if vessel.flag_state:
            # Convert common country names to codes for validation
            flag_upper = vessel.flag_state.upper()
            valid_flags = list(self.valid_country_codes.keys()) + list(self.valid_country_codes.values())
            valid_flags_upper = [f.upper() for f in valid_flags]
            
            if flag_upper not in valid_flags_upper:
                # This is a warning, not an error - new countries possible
                logger.warning(f"Unknown flag state: {vessel.flag_state}")
        
        # Vessel name validation
        if vessel.vessel_name:
            if len(vessel.vessel_name) > 255:
                errors.append("Vessel name cannot exceed 255 characters")
            
            # Check for reasonable characters
            if not re.match(r"^[a-zA-Z0-9\s\-'\"\.]+$", vessel.vessel_name):
                errors.append("Vessel name contains invalid characters")
        
        return errors
    
    # ============================================================================
    # YACHT-SPECIFIC VALIDATION
    # ============================================================================
    
    def _validate_yacht_specific(self, yacht: YachtSchema) -> List[str]:
        """Validate yacht-specific fields"""
        errors = []
        
        # Capacity validation
        if yacht.guest_capacity and yacht.crew_capacity:
            total_capacity = yacht.guest_capacity + yacht.crew_capacity
            if total_capacity > 500:  # Reasonable upper limit
                errors.append("Total capacity (guests + crew) seems unreasonably high")
        
        # Cabin validation
        if yacht.guest_cabins and yacht.guest_capacity:
            if yacht.guest_capacity < yacht.guest_cabins:
                errors.append("Guest capacity cannot be less than number of guest cabins")
        
        if yacht.crew_cabins and yacht.crew_capacity:
            if yacht.crew_capacity < yacht.crew_cabins:
                errors.append("Crew capacity cannot be less than number of crew cabins")
        
        # Speed validation
        if yacht.max_speed and yacht.cruise_speed:
            if yacht.cruise_speed > yacht.max_speed:
                errors.append("Cruise speed cannot be greater than maximum speed")
        
        if yacht.max_speed:
            if yacht.max_speed > 100:  # 100 knots is extremely fast for most yachts
                errors.append("Maximum speed seems unreasonably high (>100 knots)")
        
        # Range and fuel validation
        if yacht.range and yacht.fuel_capacity:
            # Basic sanity check - very rough estimate
            if yacht.range > yacht.fuel_capacity * 0.1:  # Very rough fuel efficiency check
                logger.warning("Range vs fuel capacity ratio seems optimistic")
        
        # Superyacht classification
        if yacht.superyacht_status and yacht.length_overall:
            if yacht.length_overall < 24:  # 24m is typical superyacht threshold
                errors.append("Vessels under 24m are typically not classified as superyachts")
        
        return errors
    
    # ============================================================================
    # UTILITY VALIDATION FUNCTIONS
    # ============================================================================
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """Validate email address format"""
        if not email:
            return True, ""  # Optional field
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email address format"
        
        return True, ""
    
    def validate_phone_number(self, phone: str) -> Tuple[bool, str]:
        """Validate phone number format"""
        if not phone:
            return True, ""  # Optional field
        
        # Remove common formatting characters
        phone_clean = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        # Must be digits and + for international
        if not re.match(r'^\+?[\d]{7,15}$', phone_clean):
            return False, "Phone number must be 7-15 digits, optionally starting with +"
        
        return True, ""
    
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate URL format"""
        if not url:
            return True, ""  # Optional field
        
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url, re.IGNORECASE):
            return False, "Invalid URL format"
        
        return True, ""
    
    def get_vessel_type_recommendations(self, vessel_data: Dict[str, Any]) -> List[str]:
        """
        Suggest appropriate vessel type based on dimensions and features
        
        Args:
            vessel_data: Dictionary of vessel data
            
        Returns:
            List of recommended vessel types
        """
        recommendations = []
        
        length = vessel_data.get('length_overall', 0)
        
        try:
            length = float(length) if length else 0
        except (ValueError, TypeError):
            return recommendations
        
        # Length-based recommendations
        if length >= 24:
            recommendations.append("superyacht")
        elif length >= 12:
            recommendations.append("yacht")
        elif length >= 8:
            recommendations.append("motor_yacht")
        
        # Feature-based recommendations
        guest_cabins = vessel_data.get('guest_cabins', 0)
        if guest_cabins and int(guest_cabins) > 6:
            recommendations.append("superyacht")
        
        # Propulsion-based
        propulsion = vessel_data.get('propulsion_type', '')
        if propulsion == 'sail':
            recommendations.append("sailing_yacht")
        
        return recommendations
    
    # ============================================================================
    # BATCH VALIDATION
    # ============================================================================
    
    def validate_multiple_vessels(
        self, 
        vessels_data: List[Dict[str, Any]]
    ) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate multiple vessels and check for duplicates
        
        Args:
            vessels_data: List of vessel data dictionaries
            
        Returns:
            Dictionary mapping vessel index to validation results
        """
        results = {}
        seen_identifiers = {}
        
        for i, vessel_data in enumerate(vessels_data):
            # Individual validation
            is_valid, errors = self.validate_vessel_data(vessel_data)
            
            # Duplicate checking
            identifiers = [
                ('imo_number', vessel_data.get('imo_number')),
                ('mmsi_number', vessel_data.get('mmsi_number')),
                ('call_sign', vessel_data.get('call_sign'))
            ]
            
            for id_type, id_value in identifiers:
                if id_value and id_value.strip():
                    if id_value in seen_identifiers:
                        errors.append(f"Duplicate {id_type}: {id_value} (also in vessel {seen_identifiers[id_value]})")
                        is_valid = False
                    else:
                        seen_identifiers[id_value] = i
            
            results[str(i)] = (is_valid, errors)
        
        return results