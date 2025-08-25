"""
Vessel Data Merging Utilities - FIXED VERSION
Smart merge algorithms and conflict resolution for vessel data enhancement

This module provides utilities for merging vessel data from multiple sources,
handling conflicts intelligently, and maintaining data integrity.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime, date
from enum import Enum
from dataclasses import dataclass

from vessel_schema import BaseVessel, VesselType, YachtSchema, HullMaterial, PropulsionType, ClassificationSociety
from vessel_validation import VesselValidator

logger = logging.getLogger(__name__)

class MergeStrategy(Enum):
    """Strategies for handling merge conflicts"""
    PREFER_EXISTING = "prefer_existing"      # Keep existing value
    PREFER_NEW = "prefer_new"                # Use new value
    PREFER_NEWER = "prefer_newer"            # Use newer timestamp
    PREFER_RELIABLE = "prefer_reliable"      # Use more reliable source
    PREFER_COMPLETE = "prefer_complete"      # Use more complete data
    MANUAL = "manual"                        # Require manual resolution

class DataReliability(Enum):
    """Source reliability levels"""
    VERY_HIGH = 5    # Official registries, IMO
    HIGH = 4         # MarineTraffic, Lloyd's
    MEDIUM = 3       # BOAT International
    LOW = 2          # Wikipedia, forums
    VERY_LOW = 1     # User input, unverified

@dataclass
class MergeConflict:
    """Represents a merge conflict between two data values"""
    field_name: str
    existing_value: Any
    new_value: Any
    existing_source: str
    new_source: str
    existing_reliability: DataReliability
    new_reliability: DataReliability
    field_type: str
    suggested_resolution: str  # FIXED: Use string instead of MergeStrategy enum for UI compatibility
    confidence: float  # 0.0 to 1.0

@dataclass
class MergeResult:
    """Result of a merge operation"""
    success: bool
    merged_data: Dict[str, Any]
    conflicts: List[MergeConflict]
    auto_resolved: List[str]  # Fields resolved automatically
    manual_required: List[str]  # Fields requiring manual resolution
    warnings: List[str]
    error_message: Optional[str] = None

class VesselDataMerger:
    """
    Smart vessel data merger with conflict resolution
    """
    
    def __init__(self):
        self.validator = VesselValidator()
        
        # Source reliability mapping
        self.source_reliability = {
            'marinetraffic': DataReliability.HIGH,
            'boat_international': DataReliability.MEDIUM,
            'wordpress': DataReliability.LOW,
            'user_input': DataReliability.LOW,
            'manual_entry': DataReliability.LOW,
            'imo_registry': DataReliability.VERY_HIGH,
            'lloyds': DataReliability.HIGH,
            'classification_society': DataReliability.HIGH,
            'database': DataReliability.MEDIUM
        }
        
        # Field-specific merge strategies
        self.field_merge_strategies = {
            # Official identifiers - prefer existing (prevent corruption)
            'imo_number': MergeStrategy.PREFER_EXISTING,
            'mmsi_number': MergeStrategy.PREFER_EXISTING,
            'official_number': MergeStrategy.PREFER_EXISTING,
            
            # Basic info - prefer more reliable source
            'vessel_name': MergeStrategy.PREFER_RELIABLE,
            'call_sign': MergeStrategy.PREFER_RELIABLE,
            'flag_state': MergeStrategy.PREFER_RELIABLE,
            
            # Technical specs - prefer more reliable
            'length_overall': MergeStrategy.PREFER_RELIABLE,
            'beam': MergeStrategy.PREFER_RELIABLE,
            'draft': MergeStrategy.PREFER_RELIABLE,
            'gross_tonnage': MergeStrategy.PREFER_RELIABLE,
            'year_built': MergeStrategy.PREFER_RELIABLE,
            
            # Descriptive fields - prefer more complete
            'description': MergeStrategy.PREFER_COMPLETE,
            'builder': MergeStrategy.PREFER_COMPLETE,
            'build_location': MergeStrategy.PREFER_COMPLETE,
            
            # Operational data - prefer newer
            'last_port': MergeStrategy.PREFER_NEWER,
            'destination': MergeStrategy.PREFER_NEWER,
            'eta': MergeStrategy.PREFER_NEWER,
            
            # Yacht-specific - prefer more complete
            'guest_capacity': MergeStrategy.PREFER_COMPLETE,
            'crew_capacity': MergeStrategy.PREFER_COMPLETE,
            'max_speed': MergeStrategy.PREFER_COMPLETE,
            'cruise_speed': MergeStrategy.PREFER_COMPLETE,
            'range_nm': MergeStrategy.PREFER_COMPLETE,
            
            # Complex fields - require manual review
            'classification_society': MergeStrategy.MANUAL,
            'class_notation': MergeStrategy.MANUAL
        }
        
        # Field type mapping for vessel schema
        self.field_types = {
            # Numeric fields
            'length_overall': 'numeric',
            'beam': 'numeric',
            'draft': 'numeric',
            'gross_tonnage': 'numeric',
            'net_tonnage': 'numeric',
            'deadweight': 'numeric',
            'displacement': 'numeric',
            'year_built': 'numeric',
            'max_speed': 'numeric',
            'cruise_speed': 'numeric',
            'range_nm': 'numeric',
            'guest_capacity': 'numeric',
            'crew_capacity': 'numeric',
            'guest_cabins': 'numeric',
            'crew_cabins': 'numeric',
            'engine_power': 'numeric',
            'fuel_capacity': 'numeric',
            'water_capacity': 'numeric',
            
            # String fields
            'vessel_name': 'string',
            'imo_number': 'string',
            'mmsi_number': 'string',
            'call_sign': 'string',
            'official_number': 'string',
            'flag_state': 'string',
            'port_of_registry': 'string',
            'builder': 'string',
            'build_location': 'string',
            'hull_number': 'string',
            'main_engines': 'string',
            'class_notation': 'string',
            'home_port': 'string',
            'radio_certificate': 'string',
            'default_operator_name': 'string',
            
            # Text fields
            'description': 'text',
            'notes': 'text',
            
            # Enum fields
            'vessel_type': 'enum',
            'hull_material': 'enum',
            'propulsion_type': 'enum',
            'classification_society': 'enum',
            'yacht_category': 'enum',
            'design_category': 'enum',
            
            # Boolean fields
            'superyacht_status': 'boolean',
            'commercial_operation': 'boolean',
            'is_active': 'boolean',
            
            # Date fields
            'survey_date': 'date',
            'certificate_expiry': 'date',
            'created_date': 'date',
            'updated_date': 'date',
            
            # List fields
            'images': 'list',
            'certificates': 'list',
            'build_standards': 'list',
            'cruising_areas': 'list'
        }
    
    # ============================================================================
    # MAIN MERGE FUNCTIONS
    # ============================================================================
    
    def merge_vessel_data(
        self,
        existing_vessel: BaseVessel,
        new_data: Dict[str, Any],
        new_source: str,
        existing_source: str = "database",
        auto_resolve: bool = True
    ) -> MergeResult:
        """
        Merge new data into existing vessel data
        
        Args:
            existing_vessel: Current vessel object
            new_data: New data to merge
            new_source: Source of new data
            existing_source: Source of existing data
            auto_resolve: Whether to auto-resolve conflicts
            
        Returns:
            MergeResult with merge outcome
        """
        try:
            conflicts = []
            merged_data = {}
            auto_resolved = []
            manual_required = []
            warnings = []
            
            # Convert vessel object to dict for comparison
            existing_data = self._vessel_to_dict(existing_vessel)
            
            # Process each field in new data
            for field_name, new_value in new_data.items():
                if new_value is None or new_value == '':
                    continue  # Skip empty values
                
                existing_value = existing_data.get(field_name)
                
                # If no existing value, use new value
                if existing_value is None or existing_value == '' or existing_value == 0:
                    merged_data[field_name] = new_value
                    continue
                
                # Check if values are the same
                if self._values_equal(existing_value, new_value):
                    merged_data[field_name] = existing_value
                    continue
                
                # Create conflict for different values
                conflict = self._create_conflict(
                    field_name, existing_value, new_value,
                    existing_source, new_source
                )
                conflicts.append(conflict)
                
                # Auto-resolve if enabled
                if auto_resolve:
                    resolution = self._resolve_conflict(conflict)
                    if resolution is not None:
                        merged_data[field_name] = resolution
                        auto_resolved.append(field_name)
                    else:
                        manual_required.append(field_name)
                        merged_data[field_name] = existing_value  # Keep existing for now
                else:
                    manual_required.append(field_name)
                    merged_data[field_name] = existing_value
            
            # Add any existing data that wasn't in new data
            for field_name, existing_value in existing_data.items():
                if field_name not in merged_data and existing_value is not None:
                    merged_data[field_name] = existing_value
            
            # Validate merged data
            validation_warnings = self._validate_merged_data(merged_data)
            warnings.extend(validation_warnings)
            
            return MergeResult(
                success=True,
                merged_data=merged_data,
                conflicts=conflicts,
                auto_resolved=auto_resolved,
                manual_required=manual_required,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Error merging vessel data: {e}")
            return MergeResult(
                success=False,
                merged_data={},
                conflicts=[],
                auto_resolved=[],
                manual_required=[],
                warnings=[],
                error_message=str(e)
            )
    
    def merge_multiple_sources(
        self,
        existing_vessel: BaseVessel,
        data_sources: List[Tuple[Dict[str, Any], str]],  # (data, source_name)
        auto_resolve: bool = True
    ) -> MergeResult:
        """
        Merge data from multiple sources
        
        Args:
            existing_vessel: Current vessel object
            data_sources: List of (data_dict, source_name) tuples
            auto_resolve: Whether to auto-resolve conflicts
            
        Returns:
            MergeResult with merge outcome
        """
        try:
            # Start with existing vessel data
            current_data = self._vessel_to_dict(existing_vessel)
            all_conflicts = []
            all_auto_resolved = []
            all_manual_required = []
            all_warnings = []
            
            # Merge each source sequentially
            for new_data, source_name in data_sources:
                # Create a temporary vessel object for this merge
                temp_vessel = self._create_vessel_from_dict(current_data)
                
                merge_result = self.merge_vessel_data(
                    temp_vessel,
                    new_data,
                    source_name,
                    auto_resolve=auto_resolve
                )
                
                if not merge_result.success:
                    return merge_result
                
                # Update current data with merged result
                current_data = merge_result.merged_data
                
                # Accumulate results
                all_conflicts.extend(merge_result.conflicts)
                all_auto_resolved.extend(merge_result.auto_resolved)
                all_manual_required.extend(merge_result.manual_required)
                all_warnings.extend(merge_result.warnings)
            
            return MergeResult(
                success=True,
                merged_data=current_data,
                conflicts=all_conflicts,
                auto_resolved=all_auto_resolved,
                manual_required=all_manual_required,
                warnings=all_warnings
            )
            
        except Exception as e:
            logger.error(f"Error merging multiple sources: {e}")
            return MergeResult(
                success=False,
                merged_data={},
                conflicts=[],
                auto_resolved=[],
                manual_required=[],
                warnings=[],
                error_message=str(e)
            )
    
    # ============================================================================
    # CONFLICT RESOLUTION
    # ============================================================================
    
    def _create_conflict(
        self,
        field_name: str,
        existing_value: Any,
        new_value: Any,
        existing_source: str,
        new_source: str
    ) -> MergeConflict:
        """Create a merge conflict object"""
        
        existing_reliability = self.source_reliability.get(existing_source, DataReliability.LOW)
        new_reliability = self.source_reliability.get(new_source, DataReliability.LOW)
        
        # Determine suggested resolution
        strategy = self.field_merge_strategies.get(field_name, MergeStrategy.PREFER_RELIABLE)
        
        # Calculate confidence based on reliability difference
        reliability_diff = abs(existing_reliability.value - new_reliability.value)
        confidence = min(0.9, max(0.1, (5 - reliability_diff) / 5))
        
        return MergeConflict(
            field_name=field_name,
            existing_value=existing_value,
            new_value=new_value,
            existing_source=existing_source,
            new_source=new_source,
            existing_reliability=existing_reliability,
            new_reliability=new_reliability,
            field_type=self._get_field_type(field_name),
            suggested_resolution=strategy.value,  # FIXED: Use string value for UI compatibility
            confidence=confidence
        )
    
    def _resolve_conflict(self, conflict: MergeConflict) -> Optional[Any]:
        """
        Automatically resolve a conflict based on strategy
        
        Args:
            conflict: MergeConflict to resolve
            
        Returns:
            Resolved value or None if manual resolution required
        """
        # Convert string back to enum for processing
        strategy = MergeStrategy(conflict.suggested_resolution)
        
        if strategy == MergeStrategy.PREFER_EXISTING:
            return conflict.existing_value
        
        elif strategy == MergeStrategy.PREFER_NEW:
            return conflict.new_value
        
        elif strategy == MergeStrategy.PREFER_RELIABLE:
            if conflict.new_reliability.value > conflict.existing_reliability.value:
                return conflict.new_value
            else:
                return conflict.existing_value
        
        elif strategy == MergeStrategy.PREFER_COMPLETE:
            # Choose more complete value
            if self._is_more_complete(conflict.new_value, conflict.existing_value):
                return conflict.new_value
            else:
                return conflict.existing_value
        
        elif strategy == MergeStrategy.PREFER_NEWER:
            # For now, prefer new value (assume it's newer)
            return conflict.new_value
        
        elif strategy == MergeStrategy.MANUAL:
            return None  # Requires manual resolution
        
        return None
    
    def resolve_conflict_manually(
        self,
        conflict: MergeConflict,
        chosen_value: Any,
        user_id: str
    ) -> Any:
        """
        Manually resolve a conflict
        
        Args:
            conflict: MergeConflict to resolve
            chosen_value: Value chosen by user
            user_id: User making the choice
            
        Returns:
            Resolved value
        """
        logger.info(f"Manual conflict resolution: {conflict.field_name} = {chosen_value} by user {user_id}")
        return chosen_value
    
    # ============================================================================
    # SMART MERGE STRATEGIES
    # ============================================================================
    
    def smart_merge_dimensions(
        self,
        existing_dimensions: Dict[str, float],
        new_dimensions: Dict[str, float],
        tolerance: float = 0.1
    ) -> Dict[str, float]:
        """
        Smart merge for vessel dimensions with tolerance checking
        
        Args:
            existing_dimensions: Current dimensions
            new_dimensions: New dimensions
            tolerance: Tolerance for accepting differences (as fraction)
            
        Returns:
            Merged dimensions
        """
        merged = {}
        
        for field in ['length_overall', 'beam', 'draft', 'gross_tonnage']:
            existing_val = existing_dimensions.get(field)
            new_val = new_dimensions.get(field)
            
            if existing_val is None:
                merged[field] = new_val
            elif new_val is None:
                merged[field] = existing_val
            else:
                # Check if values are within tolerance
                diff_ratio = abs(existing_val - new_val) / max(existing_val, new_val)
                
                if diff_ratio <= tolerance:
                    # Use average if within tolerance
                    merged[field] = (existing_val + new_val) / 2
                else:
                    # Use more reliable source (for now, prefer existing)
                    merged[field] = existing_val
        
        return merged
    
    def smart_merge_text_fields(
        self,
        existing_text: str,
        new_text: str,
        field_name: str
    ) -> str:
        """
        Smart merge for text fields
        
        Args:
            existing_text: Current text
            new_text: New text
            field_name: Field name for context
            
        Returns:
            Merged text
        """
        if not existing_text:
            return new_text
        if not new_text:
            return existing_text
        
        # For descriptions, combine if different
        if field_name == 'description':
            if existing_text.lower() not in new_text.lower() and new_text.lower() not in existing_text.lower():
                return f"{existing_text}\n\n[Additional info]: {new_text}"
            else:
                # Return longer description
                return new_text if len(new_text) > len(existing_text) else existing_text
        
        # For other fields, prefer more complete
        return new_text if len(new_text) > len(existing_text) else existing_text
    
    def smart_merge_lists(
        self,
        existing_list: List[Any],
        new_list: List[Any],
        field_name: str
    ) -> List[Any]:
        """
        Smart merge for list fields
        
        Args:
            existing_list: Current list
            new_list: New list
            field_name: Field name for context
            
        Returns:
            Merged list
        """
        if not existing_list:
            return new_list
        if not new_list:
            return existing_list
        
        # For images, combine and deduplicate
        if field_name == 'images':
            combined = existing_list + new_list
            # Remove duplicates while preserving order
            seen = set()
            unique_images = []
            for img in combined:
                if img not in seen:
                    seen.add(img)
                    unique_images.append(img)
            return unique_images[:10]  # Limit to 10 images
        
        # For other lists, combine
        return list(set(existing_list + new_list))
    
    # ============================================================================
    # VALIDATION AND UTILITIES
    # ============================================================================
    
    def _validate_merged_data(self, merged_data: Dict[str, Any]) -> List[str]:
        """Validate merged data and return warnings"""
        warnings = []
        
        # Check for logical inconsistencies
        if 'length_overall' in merged_data and 'beam' in merged_data:
            loa = merged_data['length_overall']
            beam = merged_data['beam']
            
            if loa and beam and beam > loa:
                warnings.append("Beam is greater than length overall - please verify")
        
        # Check for unrealistic values
        if 'max_speed' in merged_data:
            max_speed = merged_data['max_speed']
            if max_speed and max_speed > 70:
                warnings.append(f"Maximum speed ({max_speed} knots) seems very high")
        
        # Check identifier consistency
        if 'imo_number' in merged_data:
            imo = merged_data['imo_number']
            if imo:
                is_valid, error = self.validator.validate_imo_number(imo)
                if not is_valid:
                    warnings.append(f"IMO number validation failed: {error}")
        
        return warnings
    
    def _vessel_to_dict(self, vessel: BaseVessel) -> Dict[str, Any]:
        """Convert vessel object to dictionary - FIXED VERSION"""
        vessel_dict = {}
        
        # Get all non-private, non-method attributes
        for attr in dir(vessel):
            if not attr.startswith('_') and not callable(getattr(vessel, attr)):
                value = getattr(vessel, attr, None)
                if value is not None:
                    # Handle enum values
                    if hasattr(value, 'value'):
                        vessel_dict[attr] = value.value
                    elif hasattr(value, '__dict__'):
                        # Skip complex objects that aren't basic types
                        continue
                    else:
                        vessel_dict[attr] = value
        
        return vessel_dict
    
    def _create_vessel_from_dict(self, data: Dict[str, Any]) -> BaseVessel:
        """Create a vessel object from dictionary data"""
        # Determine vessel type
        vessel_type = data.get('vessel_type', 'yacht')
        
        # Create appropriate vessel object
        if vessel_type in ['yacht', 'motor_yacht', 'sailing_yacht', 'superyacht']:
            vessel = YachtSchema()
        else:
            vessel = BaseVessel()
        
        # Populate with data
        for field, value in data.items():
            if hasattr(vessel, field):
                setattr(vessel, field, value)
        
        return vessel
    
    def _values_equal(self, val1: Any, val2: Any) -> bool:
        """Check if two values are equal with type tolerance"""
        # Handle None values
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False
        
        # Handle numeric values with tolerance
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return abs(val1 - val2) < 0.01
        
        # Handle strings (case-insensitive)
        if isinstance(val1, str) and isinstance(val2, str):
            return val1.strip().lower() == val2.strip().lower()
        
        # Handle enum values
        if hasattr(val1, 'value') and hasattr(val2, 'value'):
            return val1.value == val2.value
        if hasattr(val1, 'value'):
            return val1.value == val2
        if hasattr(val2, 'value'):
            return val1 == val2.value
        
        # Handle dates
        if isinstance(val1, (date, datetime)) and isinstance(val2, (date, datetime)):
            return val1 == val2
        
        # Default comparison
        return val1 == val2
    
    def _is_more_complete(self, val1: Any, val2: Any) -> bool:
        """Check if val1 is more complete than val2"""
        if val1 is None:
            return False
        if val2 is None:
            return True
        
        # For strings, longer is more complete
        if isinstance(val1, str) and isinstance(val2, str):
            return len(val1.strip()) > len(val2.strip())
        
        # For numbers, non-zero is more complete
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return val1 != 0 and val2 == 0
        
        # For lists, longer is more complete
        if isinstance(val1, list) and isinstance(val2, list):
            return len(val1) > len(val2)
        
        return False
    
    def _get_field_type(self, field_name: str) -> str:
        """Get field type for conflict resolution"""
        return self.field_types.get(field_name, 'string')
    
    # ============================================================================
    # MERGE REPORTING
    # ============================================================================
    
    def generate_merge_report(self, merge_result: MergeResult) -> str:
        """
        Generate human-readable merge report
        
        Args:
            merge_result: MergeResult to report on
            
        Returns:
            Formatted report string
        """
        report = []
        
        report.append("=== VESSEL DATA MERGE REPORT ===\n")
        
        if merge_result.success:
            report.append(f" Merge completed successfully")
            report.append(f" Total conflicts: {len(merge_result.conflicts)}")
            report.append(f" Auto-resolved: {len(merge_result.auto_resolved)}")
            report.append(f" Manual required: {len(merge_result.manual_required)}")
            
            if merge_result.auto_resolved:
                report.append(f"\n Auto-resolved fields:")
                for field in merge_result.auto_resolved:
                    report.append(f"  - {field}")
            
            if merge_result.manual_required:
                report.append(f"\n Manual resolution required:")
                for field in merge_result.manual_required:
                    report.append(f"  - {field}")
            
            if merge_result.warnings:
                report.append(f"\n Warnings:")
                for warning in merge_result.warnings:
                    report.append(f"  - {warning}")
        else:
            report.append(f" Merge failed: {merge_result.error_message}")
        
        return "\n".join(report)
    
    def get_conflict_summary(self, conflicts: List[MergeConflict]) -> Dict[str, Any]:
        """
        Get summary of conflicts
        
        Args:
            conflicts: List of conflicts
            
        Returns:
            Summary dictionary
        """
        summary = {
            'total_conflicts': len(conflicts),
            'by_strategy': {},
            'by_field_type': {},
            'high_confidence': 0,
            'low_confidence': 0
        }
        
        for conflict in conflicts:
            # Count by strategy
            strategy = conflict.suggested_resolution
            summary['by_strategy'][strategy] = summary['by_strategy'].get(strategy, 0) + 1
            
            # Count by field type
            field_type = conflict.field_type
            summary['by_field_type'][field_type] = summary['by_field_type'].get(field_type, 0) + 1
            
            # Count by confidence
            if conflict.confidence > 0.7:
                summary['high_confidence'] += 1
            else:
                summary['low_confidence'] += 1
        
        return summary
