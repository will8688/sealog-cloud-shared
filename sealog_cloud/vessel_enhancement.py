"""
Vessel Enhancement Service - FIXED VERSION
Core enhancement logic for vessel data enrichment from external sources

This module provides the core enhancement functionality to enrich vessel data
from external APIs like MarineTraffic and BOAT International scraping.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from vessel_service import VesselService
from vessel_external_apis import ExternalVesselAPIs
from vessel_schema import BaseVessel
from vessel_merge import MergeConflict, DataReliability  # FIXED: Import MergeConflict

logger = logging.getLogger(__name__)

class EnhancementSource(Enum):
    """Available enhancement sources"""
    MARINETRAFFIC = "marinetraffic"
    BOAT_INTERNATIONAL = "boat_international"
    WORDPRESS = "wordpress"

@dataclass
class EnhancementOpportunity:
    """Represents an available enhancement opportunity"""
    source: EnhancementSource
    identifier_type: str  # 'imo', 'mmsi', 'name'
    identifier_value: str
    confidence: float  # 0.0 to 1.0
    description: str
    estimated_fields: int  # Number of fields that could be enhanced

@dataclass
class EnhancementResult:
    """Result of an enhancement operation - FIXED VERSION"""
    success: bool
    source: EnhancementSource
    fields_updated: List[str]
    new_data: Dict[str, Any]
    conflicts: List[MergeConflict]  # FIXED: Use List[MergeConflict] instead of Dict
    error_message: Optional[str] = None

class VesselEnhancementService:
    """
    Core vessel enhancement service
    Handles data enrichment from external sources
    """
    
    def __init__(self, vessel_service: VesselService, marine_traffic_api_key: str = None):
        """
        Initialize vessel enhancement service
        
        Args:
            vessel_service: VesselService instance
            marine_traffic_api_key: MarineTraffic API key (optional)
        """
        self.vessel_service = vessel_service
        self.external_apis = ExternalVesselAPIs(marine_traffic_api_key)
        
        # Source reliability mapping
        self.source_reliability = {
            'marinetraffic': DataReliability.HIGH,
            'boat_international': DataReliability.MEDIUM,
            'wordpress': DataReliability.LOW,
            'database': DataReliability.MEDIUM,
            'user_input': DataReliability.LOW
        }
        
        # Field mapping from external sources to vessel schema
        self.marinetraffic_field_mapping = {
            'SHIPNAME': 'vessel_name',
            'IMO': 'imo_number',
            'MMSI': 'mmsi_number',
            'CALLSIGN': 'call_sign',
            'FLAG': 'flag_state',
            'SHIP_TYPE': 'vessel_type',
            'LENGTH': 'length_overall',
            'BEAM': 'beam',
            'DRAFT': 'draft',
            'GROSS_TONNAGE': 'gross_tonnage',
            'YEAR_BUILT': 'year_built',
            'SHIPBUILDER': 'builder',
            'DESTINATION': 'destination',
            'ETA': 'eta'
        }
        
        self.boat_international_field_mapping = {
            'vessel_name': 'vessel_name',  # FIXED: Use consistent field names
            'length_overall': 'length_overall',
            'beam': 'beam',
            'draft': 'draft',
            'year_built': 'year_built',
            'builder': 'builder',
            'description': 'description',
            'max_speed': 'max_speed',
            'cruise_speed': 'cruise_speed',
            'range_nm': 'range_nm',
            'guest_capacity': 'guest_capacity',
            'crew_capacity': 'crew_capacity',
            'guest_cabins': 'guest_cabins',
            'crew_cabins': 'crew_cabins'
        }
    
    # ============================================================================
    # ENHANCEMENT OPPORTUNITY DETECTION
    # ============================================================================
    
    def get_enhancement_opportunities(self, vessel_id: str) -> List[EnhancementOpportunity]:
        """
        Get available enhancement opportunities for a vessel
        
        Args:
            vessel_id: Vessel ID
            
        Returns:
            List of enhancement opportunities
        """
        opportunities = []
        
        try:
            vessel = self.vessel_service.get_vessel_by_id(vessel_id)
            if not vessel:
                return opportunities
            
            # MarineTraffic opportunities
            if self.external_apis.marinetraffic.api_key:
                opportunities.extend(self._get_marinetraffic_opportunities(vessel))
            
            # BOAT International opportunities
            opportunities.extend(self._get_boat_international_opportunities(vessel))
            
            # Sort by confidence (highest first)
            opportunities.sort(key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting enhancement opportunities: {e}")
        
        return opportunities
    
    def _get_marinetraffic_opportunities(self, vessel: BaseVessel) -> List[EnhancementOpportunity]:
        """Get MarineTraffic enhancement opportunities"""
        opportunities = []
        
        # IMO-based enhancement
        if vessel.imo_number:
            opportunities.append(EnhancementOpportunity(
                source=EnhancementSource.MARINETRAFFIC,
                identifier_type='imo',
                identifier_value=vessel.imo_number,
                confidence=0.95,
                description=f"Enhance using IMO number {vessel.imo_number}",
                estimated_fields=8
            ))
        
        # MMSI-based enhancement
        mmsi = getattr(vessel, 'mmsi_number', None)
        if mmsi:
            opportunities.append(EnhancementOpportunity(
                source=EnhancementSource.MARINETRAFFIC,
                identifier_type='mmsi',
                identifier_value=mmsi,
                confidence=0.90,
                description=f"Enhance using MMSI number {mmsi}",
                estimated_fields=7
            ))
        
        return opportunities
    
    def _get_boat_international_opportunities(self, vessel: BaseVessel) -> List[EnhancementOpportunity]:
        """Get BOAT International enhancement opportunities"""
        opportunities = []
        
        # Name-based enhancement (for yachts)
        vessel_type = getattr(vessel, 'vessel_type', None)
        if vessel_type and vessel_type.value in ['yacht', 'motor_yacht', 'sailing_yacht', 'superyacht']:
            if vessel.vessel_name:
                opportunities.append(EnhancementOpportunity(
                    source=EnhancementSource.BOAT_INTERNATIONAL,
                    identifier_type='name',
                    identifier_value=vessel.vessel_name,
                    confidence=0.70,
                    description=f"Search BOAT International for yacht '{vessel.vessel_name}'",
                    estimated_fields=6
                ))
        
        return opportunities
    
    # ============================================================================
    # ENHANCEMENT EXECUTION
    # ============================================================================
    
    def enhance_vessel_from_marinetraffic(
        self, 
        vessel_id: str, 
        identifier_type: str, 
        identifier_value: str
    ) -> EnhancementResult:
        """
        Enhance vessel data from MarineTraffic
        
        Args:
            vessel_id: Vessel ID
            identifier_type: 'imo' or 'mmsi'
            identifier_value: Identifier value
            
        Returns:
            EnhancementResult
        """
        try:
            # Get external data
            if identifier_type == 'imo':
                api_response = self.external_apis.get_vessel_by_imo(identifier_value)
            elif identifier_type == 'mmsi':
                api_response = self.external_apis.get_vessel_by_mmsi(identifier_value)
            else:
                return EnhancementResult(
                    success=False,
                    source=EnhancementSource.MARINETRAFFIC,
                    fields_updated=[],
                    new_data={},
                    conflicts=[],
                    error_message=f"Unsupported identifier type: {identifier_type}"
                )
            
            if not api_response.success:
                return EnhancementResult(
                    success=False,
                    source=EnhancementSource.MARINETRAFFIC,
                    fields_updated=[],
                    new_data={},
                    conflicts=[],
                    error_message=api_response.error
                )
            
            # Map external data to vessel schema
            mapped_data = self._map_marinetraffic_data(api_response.data)
            
            # Get current vessel data
            current_vessel = self.vessel_service.get_vessel_by_id(vessel_id)
            if not current_vessel:
                return EnhancementResult(
                    success=False,
                    source=EnhancementSource.MARINETRAFFIC,
                    fields_updated=[],
                    new_data={},
                    conflicts=[],
                    error_message="Vessel not found"
                )
            
            # Compare and identify conflicts - FIXED: Return MergeConflict objects
            conflicts = self._identify_conflicts(current_vessel, mapped_data, 'marinetraffic')
            
            # Identify fields that would be updated
            fields_updated = list(mapped_data.keys())
            
            return EnhancementResult(
                success=True,
                source=EnhancementSource.MARINETRAFFIC,
                fields_updated=fields_updated,
                new_data=mapped_data,
                conflicts=conflicts
            )
            
        except Exception as e:
            logger.error(f"Error enhancing vessel from MarineTraffic: {e}")
            return EnhancementResult(
                success=False,
                source=EnhancementSource.MARINETRAFFIC,
                fields_updated=[],
                new_data={},
                conflicts=[],
                error_message=str(e)
            )
    
    def enhance_vessel_from_boat_international(
        self, 
        vessel_id: str, 
        yacht_name: str
    ) -> EnhancementResult:
        """
        Enhance vessel data from BOAT International
        
        Args:
            vessel_id: Vessel ID
            yacht_name: Yacht name to search for
            
        Returns:
            EnhancementResult
        """
        try:
            # Search for yacht
            search_response = self.external_apis.search_boat_international_yachts(yacht_name)
            
            if not search_response.success:
                return EnhancementResult(
                    success=False,
                    source=EnhancementSource.BOAT_INTERNATIONAL,
                    fields_updated=[],
                    new_data={},
                    conflicts=[],
                    error_message=search_response.error
                )
            
            # Get search results - FIXED: Use correct field name
            search_results = search_response.data.get('yacht_urls', [])
            
            if not search_results:
                return EnhancementResult(
                    success=False,
                    source=EnhancementSource.BOAT_INTERNATIONAL,
                    fields_updated=[],
                    new_data={},
                    conflicts=[],
                    error_message="No matching yachts found"
                )
            
            # Use first result (highest relevance)
            yacht_url = search_results[0].get('url')
            if not yacht_url:
                return EnhancementResult(
                    success=False,
                    source=EnhancementSource.BOAT_INTERNATIONAL,
                    fields_updated=[],
                    new_data={},
                    conflicts=[],
                    error_message="No yacht URL found in search results"
                )
            
            # Scrape yacht details
            yacht_response = self.external_apis.scrape_boat_international_yacht(yacht_url)
            
            if not yacht_response.success:
                return EnhancementResult(
                    success=False,
                    source=EnhancementSource.BOAT_INTERNATIONAL,
                    fields_updated=[],
                    new_data={},
                    conflicts=[],
                    error_message=yacht_response.error
                )
            
            # Map yacht data to vessel schema
            mapped_data = self._map_boat_international_data(yacht_response.data)
            
            # Get current vessel data
            current_vessel = self.vessel_service.get_vessel_by_id(vessel_id)
            if not current_vessel:
                return EnhancementResult(
                    success=False,
                    source=EnhancementSource.BOAT_INTERNATIONAL,
                    fields_updated=[],
                    new_data={},
                    conflicts=[],
                    error_message="Vessel not found"
                )
            
            # Compare and identify conflicts - FIXED: Return MergeConflict objects
            conflicts = self._identify_conflicts(current_vessel, mapped_data, 'boat_international')
            
            # Identify fields that would be updated
            fields_updated = list(mapped_data.keys())
            
            return EnhancementResult(
                success=True,
                source=EnhancementSource.BOAT_INTERNATIONAL,
                fields_updated=fields_updated,
                new_data=mapped_data,
                conflicts=conflicts
            )
            
        except Exception as e:
            logger.error(f"Error enhancing vessel from BOAT International: {e}")
            return EnhancementResult(
                success=False,
                source=EnhancementSource.BOAT_INTERNATIONAL,
                fields_updated=[],
                new_data={},
                conflicts=[],
                error_message=str(e)
            )
    
    # ============================================================================
    # ENHANCEMENT APPLICATION
    # ============================================================================
    
    def apply_enhancement(
        self, 
        vessel_id: str, 
        enhancement_result: EnhancementResult,
        user_id: str,
        selected_fields: List[str] = None
    ) -> Tuple[bool, str]:
        """
        Apply enhancement to vessel
        
        Args:
            vessel_id: Vessel ID
            enhancement_result: Enhancement result to apply
            user_id: User applying the enhancement
            selected_fields: Specific fields to update (None for all)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not enhancement_result.success:
                return False, "Enhancement result is not successful"
            
            # Filter data if specific fields selected
            data_to_apply = enhancement_result.new_data
            if selected_fields:
                data_to_apply = {
                    field: value for field, value in enhancement_result.new_data.items()
                    if field in selected_fields
                }
            
            # Apply enhancement
            success, message = self.vessel_service.update_vessel(
                vessel_id,
                data_to_apply,
                user_id
            )
            
            if success:
                logger.info(f"Applied enhancement from {enhancement_result.source.value} to vessel {vessel_id}")
                return True, f"Enhancement applied successfully ({len(data_to_apply)} fields updated)"
            else:
                return False, message
                
        except Exception as e:
            logger.error(f"Error applying enhancement: {e}")
            return False, f"Failed to apply enhancement: {str(e)}"
    
    # ============================================================================
    # DATA MAPPING UTILITIES
    # ============================================================================
    
    def _map_marinetraffic_data(self, mt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map MarineTraffic data to vessel schema"""
        mapped_data = {}
        
        for mt_field, vessel_field in self.marinetraffic_field_mapping.items():
            if mt_field in mt_data and mt_data[mt_field]:
                value = mt_data[mt_field]
                
                # Clean and convert data
                if vessel_field in ['length_overall', 'beam', 'draft', 'gross_tonnage']:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        continue
                elif vessel_field == 'year_built':
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        continue
                elif vessel_field == 'vessel_type':
                    # Map MarineTraffic ship types to our vessel types
                    value = self._map_ship_type(value)
                
                mapped_data[vessel_field] = value
        
        return mapped_data
    
    def _map_boat_international_data(self, bi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map BOAT International data to vessel schema"""
        mapped_data = {}
        
        for bi_field, vessel_field in self.boat_international_field_mapping.items():
            if bi_field in bi_data and bi_data[bi_field]:
                value = bi_data[bi_field]
                
                # Clean and convert data
                if vessel_field in ['length_overall', 'beam', 'draft', 'max_speed', 'cruise_speed', 'range_nm']:
                    # Extract numeric values from strings like "45.5 m" or "22 knots"
                    if isinstance(value, str):
                        value = self._extract_numeric_value(value)
                    elif isinstance(value, (int, float)):
                        value = float(value)
                elif vessel_field in ['guest_capacity', 'crew_capacity', 'guest_cabins', 'crew_cabins', 'year_built']:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        continue
                
                if value is not None:
                    mapped_data[vessel_field] = value
        
        return mapped_data
    
    def _identify_conflicts(self, current_vessel: BaseVessel, new_data: Dict[str, Any], source: str) -> List[MergeConflict]:
        """Identify conflicts between current and new data - FIXED: Return MergeConflict objects"""
        conflicts = []
        
        for field, new_value in new_data.items():
            current_value = getattr(current_vessel, field, None)
            
            # Skip if current value is empty/None
            if current_value is None or current_value == '' or current_value == 0:
                continue
            
            # Check if values are different
            if not self._values_equal(current_value, new_value):
                # Create MergeConflict object
                conflict = MergeConflict(
                    field_name=field,
                    existing_value=current_value,
                    new_value=new_value,
                    existing_source='database',
                    new_source=source,
                    existing_reliability=self.source_reliability.get('database', DataReliability.MEDIUM),
                    new_reliability=self.source_reliability.get(source, DataReliability.LOW),
                    field_type=self._get_field_type(field),
                    suggested_resolution=self._get_suggested_resolution(field),
                    confidence=self._calculate_conflict_confidence(current_value, new_value, source)
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _values_equal(self, val1: Any, val2: Any) -> bool:
        """Check if two values are equal with type tolerance"""
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
        
        # Default comparison
        return val1 == val2
    
    def _get_field_type(self, field_name: str) -> str:
        """Get field type for conflict resolution"""
        numeric_fields = ['length_overall', 'beam', 'draft', 'gross_tonnage', 'year_built', 
                         'max_speed', 'cruise_speed', 'guest_capacity', 'crew_capacity']
        
        if field_name in numeric_fields:
            return 'numeric'
        elif field_name in ['description', 'notes']:
            return 'text'
        else:
            return 'string'
    
    def _get_suggested_resolution(self, field_name: str) -> str:
        """Get suggested resolution strategy for field"""
        # Official identifiers - prefer existing
        if field_name in ['imo_number', 'mmsi_number', 'official_number']:
            return 'prefer_existing'
        
        # Technical specs - prefer more reliable source
        elif field_name in ['length_overall', 'beam', 'draft', 'gross_tonnage', 'year_built']:
            return 'prefer_reliable'
        
        # Descriptive fields - prefer more complete
        elif field_name in ['description', 'vessel_name']:
            return 'prefer_complete'
        
        else:
            return 'manual'
    
    def _calculate_conflict_confidence(self, existing_value: Any, new_value: Any, source: str) -> float:
        """Calculate confidence level for conflict resolution"""
        source_reliability = self.source_reliability.get(source, DataReliability.LOW)
        
        # Higher confidence for more reliable sources
        base_confidence = source_reliability.value / 5.0
        
        # Boost confidence if values are similar
        if isinstance(existing_value, (int, float)) and isinstance(new_value, (int, float)):
            diff_ratio = abs(existing_value - new_value) / max(existing_value, new_value)
            if diff_ratio < 0.1:  # Values within 10%
                base_confidence += 0.2
        
        return min(base_confidence, 1.0)
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _map_ship_type(self, mt_ship_type: str) -> str:
        """Map MarineTraffic ship type to our vessel type"""
        mt_type_lower = mt_ship_type.lower()
        
        if 'yacht' in mt_type_lower or 'pleasure' in mt_type_lower:
            return 'yacht'
        elif 'cargo' in mt_type_lower:
            return 'cargo_ship'
        elif 'tanker' in mt_type_lower:
            return 'tanker'
        elif 'passenger' in mt_type_lower:
            return 'passenger_ship'
        elif 'fishing' in mt_type_lower:
            return 'fishing_vessel'
        elif 'tug' in mt_type_lower:
            return 'tug_boat'
        else:
            return 'other'
    
    def _extract_numeric_value(self, value_str: str) -> Optional[float]:
        """Extract numeric value from string like '45.5 m' or '22 knots'"""
        if not isinstance(value_str, str):
            return None
        
        import re
        match = re.search(r'(\d+\.?\d*)', value_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        return None
    
    # ============================================================================
    # ENHANCEMENT HISTORY
    # ============================================================================
    
    def get_enhancement_history(self, vessel_id: str) -> List[Dict[str, Any]]:
        """
        Get enhancement history for a vessel
        
        Args:
            vessel_id: Vessel ID
            
        Returns:
            List of enhancement history entries
        """
        # This would typically be stored in database
        # For now, return empty list as placeholder
        return []
    
    def log_enhancement(
        self, 
        vessel_id: str, 
        source: EnhancementSource,
        fields_updated: List[str],
        user_id: str
    ):
        """
        Log enhancement operation
        
        Args:
            vessel_id: Vessel ID
            source: Enhancement source
            fields_updated: List of fields that were updated
            user_id: User who performed the enhancement
        """
        # This would typically be stored in database
        logger.info(f"Enhancement logged: vessel={vessel_id}, source={source.value}, fields={fields_updated}, user={user_id}")
    
    # ============================================================================
    # BATCH ENHANCEMENT
    # ============================================================================
    
    def get_batch_enhancement_candidates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get vessels that are candidates for batch enhancement
        
        Args:
            limit: Maximum number of candidates to return
            
        Returns:
            List of vessel candidates with enhancement opportunities
        """
        # This would query database for vessels with identifiers but missing data
        # For now, return empty list as placeholder
        return []
    
    def perform_batch_enhancement(
        self, 
        vessel_ids: List[str],
        sources: List[EnhancementSource],
        user_id: str
    ) -> Dict[str, EnhancementResult]:
        """
        Perform batch enhancement on multiple vessels
        
        Args:
            vessel_ids: List of vessel IDs
            sources: Enhancement sources to use
            user_id: User performing the enhancement
            
        Returns:
            Dictionary mapping vessel ID to enhancement result
        """
        results = {}
        
        for vessel_id in vessel_ids:
            try:
                opportunities = self.get_enhancement_opportunities(vessel_id)
                
                for opportunity in opportunities:
                    if opportunity.source in sources:
                        if opportunity.source == EnhancementSource.MARINETRAFFIC:
                            result = self.enhance_vessel_from_marinetraffic(
                                vessel_id,
                                opportunity.identifier_type,
                                opportunity.identifier_value
                            )
                        elif opportunity.source == EnhancementSource.BOAT_INTERNATIONAL:
                            result = self.enhance_vessel_from_boat_international(
                                vessel_id,
                                opportunity.identifier_value
                            )
                        else:
                            continue
                        
                        results[vessel_id] = result
                        break  # Use first successful opportunity
                        
            except Exception as e:
                logger.error(f"Error in batch enhancement for vessel {vessel_id}: {e}")
                results[vessel_id] = EnhancementResult(
                    success=False,
                    source=EnhancementSource.MARINETRAFFIC,
                    fields_updated=[],
                    new_data={},
                    conflicts=[],
                    error_message=str(e)
                )
        
        return results
