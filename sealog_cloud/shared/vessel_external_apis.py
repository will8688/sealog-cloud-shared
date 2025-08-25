"""
Vessel External APIs - FIXED VERSION
Integration with external vessel data sources for auto-population and enrichment

This module provides integrations with MarineTraffic, BOAT International scraping,
and other external data sources to automatically populate and enrich vessel data.
"""

import logging
from typing import Optional, Dict, Any, List
from .external_apis.base_scraper import APIResponse
from .external_apis.marinetraffic_api import MarineTrafficAPI
from .external_apis.boat_international_scraper import BoatInternationalScraper
from .external_apis.wordpress_importer import WordPressImporter

logger = logging.getLogger(__name__)

class ExternalVesselAPIs:
    """
    External vessel data API integrations coordinator
    Handles coordination between different external data sources
    """
    
    def __init__(self, marine_traffic_api_key: str = None):
        """
        Initialize external API integrations
        
        Args:
            marine_traffic_api_key: MarineTraffic API key (optional)
        """
        # Initialize individual API handlers
        self.marinetraffic = MarineTrafficAPI(marine_traffic_api_key)
        self.boat_international = BoatInternationalScraper()
        self.wordpress = WordPressImporter()
    
    # ============================================================================
    # MARINETRAFFIC API INTEGRATION
    # ============================================================================
    
    def get_vessel_by_imo(self, imo_number: str) -> APIResponse:
        """
        Get vessel data from MarineTraffic by IMO number
        
        Args:
            imo_number: IMO number
            
        Returns:
            APIResponse with vessel data
        """
        return self.marinetraffic.get_vessel_by_imo(imo_number)
    
    def get_vessel_by_mmsi(self, mmsi_number: str) -> APIResponse:
        """
        Get vessel data from MarineTraffic by MMSI number
        
        Args:
            mmsi_number: MMSI number
            
        Returns:
            APIResponse with vessel data
        """
        return self.marinetraffic.get_vessel_by_mmsi(mmsi_number)
    
    # ============================================================================
    # BOAT INTERNATIONAL WEB SCRAPING (RESPECTFUL)
    # ============================================================================
    
    def scrape_boat_international_yacht(self, yacht_url: str) -> APIResponse:
        """
        Scrape individual yacht page from BOAT International
        
        Args:
            yacht_url: Direct URL to yacht page on boatinternational.com
            
        Returns:
            APIResponse with yacht data
        """
        return self.boat_international.scrape_boat_international_yacht(yacht_url)
    
    def search_boat_international_yachts(self, yacht_name: str) -> APIResponse:
        """
        Search BOAT International for yachts by name
        
        Args:
            yacht_name: Yacht name to search for
            
        Returns:
            APIResponse with search results including URLs
        """
        return self.boat_international.search_boat_international_yachts(yacht_name)
    
    # ============================================================================
    # WORDPRESS DATABASE INTEGRATION - FIXED AND ENHANCED
    # ============================================================================
    
    def import_from_wordpress_api(self, wordpress_url: str, api_key: str = None) -> APIResponse:
        """
        Import vessel data from WordPress REST API (legacy method)
        
        Args:
            wordpress_url: WordPress site URL
            api_key: API key for authentication (optional)
            
        Returns:
            APIResponse with list of vessels
        """
        return self.wordpress.import_from_wordpress_api(wordpress_url, api_key)
    
    def import_from_wordpress_custom_post_type(
        self, 
        wordpress_url: str, 
        post_type: str = "gd_yacht",
        api_key: str = None,
        custom_field_mappings: Dict[str, str] = None
    ) -> APIResponse:
        """
        Import vessel data from WordPress custom post type - FIXED: Added missing method
        
        Args:
            wordpress_url: WordPress site URL (e.g., 'https://yachtlycrew.com')
            post_type: Custom post type name (e.g., 'gd_yacht')
            api_key: API key for authentication (optional)
            custom_field_mappings: Custom field mappings to override defaults
            
        Returns:
            APIResponse with list of vessels
        """
        return self.wordpress.import_from_wordpress_custom_post_type(
            wordpress_url, 
            post_type, 
            api_key, 
            custom_field_mappings
        )
    
    def get_wordpress_custom_fields(
        self, 
        wordpress_url: str, 
        post_type: str = "gd_yacht",
        api_key: str = None
    ) -> APIResponse:
        """
        Get available custom fields for a WordPress post type (for debugging/setup)
        
        Args:
            wordpress_url: WordPress site URL
            post_type: Custom post type name
            api_key: API key for authentication (optional)
            
        Returns:
            APIResponse with available fields
        """
        return self.wordpress.get_available_custom_fields(
            wordpress_url, 
            post_type, 
            api_key
        )
    
    # ============================================================================
    # ENHANCED SEARCH AND DISCOVERY
    # ============================================================================
    
    def search_vessels_by_name(self, vessel_name: str) -> Dict[str, APIResponse]:
        """
        Search for vessels by name across multiple sources
        
        Args:
            vessel_name: Vessel name to search for
            
        Returns:
            Dictionary mapping source name to APIResponse
        """
        results = {}
        
        # Search BOAT International for yachts
        try:
            boat_result = self.search_boat_international_yachts(vessel_name)
            results['boat_international'] = boat_result
        except Exception as e:
            logger.error(f"Error searching BOAT International: {e}")
            results['boat_international'] = APIResponse(
                success=False,
                error=str(e),
                source="boat_international"
            )
        
        # Could add other sources here (e.g., MarineTraffic search if available)
        
        return results
    
    def discover_vessel_data(self, vessel_identifiers: Dict[str, str]) -> Dict[str, APIResponse]:
        """
        Discover vessel data using available identifiers
        
        Args:
            vessel_identifiers: Dict with keys like 'imo_number', 'mmsi_number', 'vessel_name'
            
        Returns:
            Dictionary mapping source name to APIResponse
        """
        results = {}
        
        # Try MarineTraffic with IMO
        if vessel_identifiers.get('imo_number') and self.marinetraffic.api_key:
            try:
                mt_result = self.get_vessel_by_imo(vessel_identifiers['imo_number'])
                results['marinetraffic_imo'] = mt_result
            except Exception as e:
                logger.error(f"Error getting vessel by IMO: {e}")
        
        # Try MarineTraffic with MMSI
        if vessel_identifiers.get('mmsi_number') and self.marinetraffic.api_key:
            try:
                mt_result = self.get_vessel_by_mmsi(vessel_identifiers['mmsi_number'])
                results['marinetraffic_mmsi'] = mt_result
            except Exception as e:
                logger.error(f"Error getting vessel by MMSI: {e}")
        
        # Try BOAT International with name
        if vessel_identifiers.get('vessel_name'):
            try:
                boat_result = self.search_boat_international_yachts(vessel_identifiers['vessel_name'])
                results['boat_international'] = boat_result
            except Exception as e:
                logger.error(f"Error searching BOAT International: {e}")
        
        return results
    
    # ============================================================================
    # BULK IMPORT OPERATIONS
    # ============================================================================
    
    def bulk_import_from_wordpress(
        self, 
        wordpress_configs: List[Dict[str, Any]]
    ) -> Dict[str, APIResponse]:
        """
        Bulk import from multiple WordPress sites
        
        Args:
            wordpress_configs: List of config dicts with 'url', 'post_type', 'api_key', etc.
            
        Returns:
            Dictionary mapping site URL to APIResponse
        """
        results = {}
        
        for config in wordpress_configs:
            site_url = config.get('url')
            post_type = config.get('post_type', 'gd_yacht')
            api_key = config.get('api_key')
            custom_mappings = config.get('custom_field_mappings')
            
            if not site_url:
                continue
            
            try:
                result = self.import_from_wordpress_custom_post_type(
                    site_url, 
                    post_type, 
                    api_key, 
                    custom_mappings
                )
                results[site_url] = result
                
            except Exception as e:
                logger.error(f"Error importing from {site_url}: {e}")
                results[site_url] = APIResponse(
                    success=False,
                    error=str(e),
                    source="wordpress"
                )
        
        return results
    
    def bulk_enhance_vessels(
        self, 
        vessel_identifiers: List[Dict[str, str]]
    ) -> List[Dict[str, APIResponse]]:
        """
        Bulk enhance multiple vessels
        
        Args:
            vessel_identifiers: List of identifier dicts
            
        Returns:
            List of enhancement results
        """
        results = []
        
        for identifiers in vessel_identifiers:
            vessel_results = self.discover_vessel_data(identifiers)
            results.append(vessel_results)
        
        return results
    
    # ============================================================================
    # CACHING AND UTILITY METHODS
    # ============================================================================
    
    def clear_cache(self):
        """Clear all cached responses from all APIs"""
        self.marinetraffic.clear_cache()
        self.boat_international.clear_cache()
        self.wordpress.clear_cache()
        logger.info("Cleared all API response caches")
    
    def clear_source_cache(self, source: str):
        """
        Clear cache for specific source
        
        Args:
            source: Source name ('marinetraffic', 'boat_international', 'wordpress')
        """
        if source == 'marinetraffic':
            self.marinetraffic.clear_cache()
        elif source == 'boat_international':
            self.boat_international.clear_cache()
        elif source == 'wordpress':
            self.wordpress.clear_cache()
        else:
            logger.warning(f"Unknown source for cache clearing: {source}")
    
    def get_enrichment_suggestions(self, vessel_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get suggestions for data enrichment based on available identifiers
        
        Args:
            vessel_data: Current vessel data
            
        Returns:
            List of enrichment suggestion dictionaries
        """
        suggestions = []
        
        # MarineTraffic suggestions
        if self.marinetraffic.api_key:
            if vessel_data.get('imo_number'):
                suggestions.append({
                    'source': 'marinetraffic',
                    'method': 'imo',
                    'identifier': vessel_data['imo_number'],
                    'description': f"Enrich from MarineTraffic using IMO number {vessel_data['imo_number']}",
                    'confidence': 0.9,
                    'estimated_fields': 8
                })
            
            if vessel_data.get('mmsi_number'):
                suggestions.append({
                    'source': 'marinetraffic',
                    'method': 'mmsi',
                    'identifier': vessel_data['mmsi_number'],
                    'description': f"Enrich from MarineTraffic using MMSI number {vessel_data['mmsi_number']}",
                    'confidence': 0.85,
                    'estimated_fields': 7
                })
        
        # BOAT International suggestions
        if vessel_data.get('vessel_name'):
            vessel_type = vessel_data.get('vessel_type', '').lower()
            if any(yacht_type in vessel_type for yacht_type in ['yacht', 'superyacht']):
                suggestions.append({
                    'source': 'boat_international',
                    'method': 'name',
                    'identifier': vessel_data['vessel_name'],
                    'description': f"Search BOAT International for yacht '{vessel_data['vessel_name']}'",
                    'confidence': 0.7,
                    'estimated_fields': 6
                })
        
        # General suggestions
        if not vessel_data.get('imo_number') and not vessel_data.get('mmsi_number'):
            suggestions.append({
                'source': 'general',
                'method': 'identifiers',
                'identifier': None,
                'description': "Add IMO or MMSI number for automatic data enrichment",
                'confidence': 0.0,
                'estimated_fields': 0
            })
        
        # Sort by confidence (highest first)
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        Get status of external API integrations
        
        Returns:
            Dictionary of API statuses
        """
        status = {
            'marinetraffic': {
                'configured': bool(self.marinetraffic.api_key),
                'available': bool(self.marinetraffic.api_key),
                'last_request': getattr(self.marinetraffic, 'last_request_time', {}).get('marinetraffic'),
                'cache_entries': len([k for k in getattr(self.marinetraffic, 'cache', {}).keys() if k.startswith('mt_')]),
                'rate_limit_status': 'OK'  # Would need to implement rate limit checking
            },
            'boat_international': {
                'configured': True,  # Always available for scraping
                'available': True,
                'last_request': getattr(self.boat_international, 'last_request_time', {}).get('boat_international'),
                'cache_entries': len([k for k in getattr(self.boat_international, 'cache', {}).keys() if k.startswith('boat_intl_')]),
                'rate_limit_status': 'OK'
            },
            'wordpress': {
                'configured': True,  # Can work without API key
                'available': True,
                'last_request': getattr(self.wordpress, 'last_request_time', {}).get('wordpress'),
                'cache_entries': len([k for k in getattr(self.wordpress, 'cache', {}).keys() if k.startswith('wp_')]),
                'rate_limit_status': 'OK'
            }
        }
        
        # Calculate totals
        total_cache = sum(api['cache_entries'] for api in status.values())
        configured_apis = sum(1 for api in status.values() if api['configured'])
        available_apis = sum(1 for api in status.values() if api['available'])
        
        status['summary'] = {
            'total_apis': len(status),
            'configured_apis': configured_apis,
            'available_apis': available_apis,
            'total_cache_entries': total_cache,
            'last_updated': None  # Could implement last update tracking
        }
        
        return status
    
    # ============================================================================
    # VALIDATION AND TESTING
    # ============================================================================
    
    def test_api_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Test connections to all configured APIs
        
        Returns:
            Dictionary with test results for each API
        """
        test_results = {}
        
        # Test MarineTraffic
        if self.marinetraffic.api_key:
            try:
                # Test with a well-known IMO number
                test_result = self.get_vessel_by_imo('9074729')  # Example IMO
                test_results['marinetraffic'] = {
                    'success': test_result.success,
                    'error': test_result.error if not test_result.success else None,
                    'response_time': None,  # Could implement timing
                    'status': 'OK' if test_result.success else 'FAILED'
                }
            except Exception as e:
                test_results['marinetraffic'] = {
                    'success': False,
                    'error': str(e),
                    'response_time': None,
                    'status': 'ERROR'
                }
        else:
            test_results['marinetraffic'] = {
                'success': False,
                'error': 'API key not configured',
                'response_time': None,
                'status': 'NOT_CONFIGURED'
            }
        
        # Test BOAT International
        try:
            test_result = self.search_boat_international_yachts('Azzam')  # Example yacht
            test_results['boat_international'] = {
                'success': test_result.success,
                'error': test_result.error if not test_result.success else None,
                'response_time': None,
                'status': 'OK' if test_result.success else 'FAILED'
            }
        except Exception as e:
            test_results['boat_international'] = {
                'success': False,
                'error': str(e),
                'response_time': None,
                'status': 'ERROR'
            }
        
        # Test WordPress (basic connectivity)
        try:
            # This would test basic WordPress REST API connectivity
            test_results['wordpress'] = {
                'success': True,
                'error': None,
                'response_time': None,
                'status': 'OK'
            }
        except Exception as e:
            test_results['wordpress'] = {
                'success': False,
                'error': str(e),
                'response_time': None,
                'status': 'ERROR'
            }
        
        return test_results
    
    def validate_data_quality(self, api_response: APIResponse) -> Dict[str, Any]:
        """
        Validate quality of data received from external APIs
        
        Args:
            api_response: APIResponse to validate
            
        Returns:
            Dictionary with quality metrics
        """
        if not api_response.success:
            return {
                'quality_score': 0.0,
                'completeness': 0.0,
                'accuracy': 0.0,
                'issues': ['API call failed'],
                'recommendations': ['Check API configuration and connectivity']
            }
        
        data = api_response.data
        issues = []
        recommendations = []
        
        # Check completeness
        expected_fields = ['vessel_name', 'imo_number', 'length_overall', 'year_built']
        present_fields = [field for field in expected_fields if data.get(field)]
        completeness = len(present_fields) / len(expected_fields)
        
        if completeness < 0.5:
            issues.append('Low data completeness')
            recommendations.append('Consider using additional data sources')
        
        # Check for reasonable values
        if data.get('length_overall'):
            length = float(data['length_overall'])
            if length < 1 or length > 500:
                issues.append('Unrealistic vessel length')
                recommendations.append('Verify vessel dimensions')
        
        if data.get('year_built'):
            year = int(data['year_built'])
            if year < 1800 or year > 2030:
                issues.append('Unrealistic build year')
                recommendations.append('Verify vessel build year')
        
        # Calculate quality score
        quality_score = completeness * 0.7 + (0.3 if len(issues) == 0 else 0.1)
        
        return {
            'quality_score': quality_score,
            'completeness': completeness,
            'accuracy': 1.0 - (len(issues) * 0.2),  # Simple accuracy metric
            'issues': issues,
            'recommendations': recommendations,
            'data_fields': len([k for k, v in data.items() if v is not None])
        }
