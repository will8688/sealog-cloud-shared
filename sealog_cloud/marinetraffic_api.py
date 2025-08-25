"""
MarineTraffic API Integration
Handles vessel data retrieval from MarineTraffic API
"""

import requests
import logging
from typing import Dict, Any
from datetime import datetime
from .base_scraper import BaseScraper, APIResponse

logger = logging.getLogger(__name__)

class MarineTrafficAPI(BaseScraper):
    """
    MarineTraffic API integration
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize MarineTraffic API
        
        Args:
            api_key: MarineTraffic API key
        """
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://services.marinetraffic.com/api"
    
    def get_vessel_by_imo(self, imo_number: str) -> APIResponse:
        """
        Get vessel data from MarineTraffic by IMO number
        
        Args:
            imo_number: IMO number
            
        Returns:
            APIResponse with vessel data
        """
        if not self.api_key:
            return APIResponse(
                success=False,
                error="MarineTraffic API key not configured",
                source="marinetraffic"
            )
        
        # Check cache first
        cache_key = f"mt_imo_{imo_number}"
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        try:
            # Rate limiting
            self._enforce_rate_limit("marinetraffic")
            
            # API call
            url = f"{self.base_url}/exportvesseltrack/v:2/imo:{imo_number}/protocol:jsono"
            params = {
                'msg_type': 1,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                vessel_data = self._normalize_marinetraffic_data(data[0])
                api_response = APIResponse(
                    success=True,
                    data=vessel_data,
                    source="marinetraffic"
                )
            else:
                api_response = APIResponse(
                    success=False,
                    error="Vessel not found",
                    source="marinetraffic"
                )
            
            # Cache the response
            self._cache_response(cache_key, api_response)
            return api_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MarineTraffic API error: {e}")
            return APIResponse(
                success=False,
                error=f"API request failed: {str(e)}",
                source="marinetraffic"
            )
        except Exception as e:
            logger.error(f"MarineTraffic processing error: {e}")
            return APIResponse(
                success=False,
                error=f"Data processing error: {str(e)}",
                source="marinetraffic"
            )
    
    def get_vessel_by_mmsi(self, mmsi_number: str) -> APIResponse:
        """
        Get vessel data from MarineTraffic by MMSI number
        
        Args:
            mmsi_number: MMSI number
            
        Returns:
            APIResponse with vessel data
        """
        if not self.api_key:
            return APIResponse(
                success=False,
                error="MarineTraffic API key not configured",
                source="marinetraffic"
            )
        
        # Check cache first
        cache_key = f"mt_mmsi_{mmsi_number}"
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        try:
            # Rate limiting
            self._enforce_rate_limit("marinetraffic")
            
            # API call
            url = f"{self.base_url}/exportvessel/v:5/mmsi:{mmsi_number}/protocol:jsono"
            params = {
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                vessel_data = self._normalize_marinetraffic_data(data[0])
                api_response = APIResponse(
                    success=True,
                    data=vessel_data,
                    source="marinetraffic"
                )
            else:
                api_response = APIResponse(
                    success=False,
                    error="Vessel not found",
                    source="marinetraffic"
                )
            
            # Cache the response
            self._cache_response(cache_key, api_response)
            return api_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MarineTraffic API error: {e}")
            return APIResponse(
                success=False,
                error=f"API request failed: {str(e)}",
                source="marinetraffic"
            )
        except Exception as e:
            logger.error(f"MarineTraffic processing error: {e}")
            return APIResponse(
                success=False,
                error=f"Data processing error: {str(e)}",
                source="marinetraffic"
            )
    
    def _normalize_marinetraffic_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize MarineTraffic API response to our vessel schema
        
        Args:
            raw_data: Raw API response data
            
        Returns:
            Normalized vessel data dictionary
        """
        normalized = {}
        
        # Basic identifiers
        if 'SHIPNAME' in raw_data:
            normalized['vessel_name'] = raw_data['SHIPNAME']
        if 'IMO' in raw_data:
            normalized['imo_number'] = str(raw_data['IMO'])
        if 'MMSI' in raw_data:
            normalized['mmsi_number'] = str(raw_data['MMSI'])
        if 'CALLSIGN' in raw_data:
            normalized['call_sign'] = raw_data['CALLSIGN']
        
        # Classification
        if 'FLAG' in raw_data:
            normalized['flag_state'] = raw_data['FLAG']
        if 'TYPE_NAME' in raw_data:
            normalized['vessel_type'] = self._map_marinetraffic_vessel_type(raw_data['TYPE_NAME'])
        
        # Dimensions
        if 'LENGTH' in raw_data and raw_data['LENGTH']:
            normalized['length_overall'] = float(raw_data['LENGTH'])
        if 'WIDTH' in raw_data and raw_data['WIDTH']:
            normalized['beam'] = float(raw_data['WIDTH'])
        if 'GRT' in raw_data and raw_data['GRT']:
            normalized['gross_tonnage'] = float(raw_data['GRT'])
        if 'DWT' in raw_data and raw_data['DWT']:
            normalized['deadweight'] = float(raw_data['DWT'])
        
        # Construction
        if 'YEAR_BUILT' in raw_data and raw_data['YEAR_BUILT']:
            normalized['year_built'] = int(raw_data['YEAR_BUILT'])
        
        # Add data source metadata
        normalized['data_source'] = 'marinetraffic'
        normalized['data_updated'] = datetime.now().isoformat()
        
        return normalized
    
    def _map_marinetraffic_vessel_type(self, mt_type: str) -> str:
        """Map MarineTraffic vessel types to our schema"""
        type_mapping = {
            'Yacht': 'yacht',
            'Pleasure Craft': 'yacht',
            'Sailing Vessel': 'sailing_yacht',
            'Motor Yacht': 'motor_yacht',
            'Cargo': 'cargo_ship',
            'Tanker': 'tanker',
            'Container Ship': 'container_ship',
            'Bulk Carrier': 'bulk_carrier',
            'Passenger': 'passenger_ship',
            'Ferry': 'ferry',
            'Fishing': 'fishing_vessel',
            'Tug': 'tug_boat'
        }
        
        return type_mapping.get(mt_type, 'other')