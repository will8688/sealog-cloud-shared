"""
Enhanced WordPress Database Integration
Handles importing vessel data from WordPress REST API with custom post types and custom fields
"""

import requests
import logging
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from .base_scraper import BaseScraper, APIResponse

logger = logging.getLogger(__name__)

class WordPressImporter(BaseScraper):
    """
    Enhanced WordPress REST API integration for vessel data import
    Supports custom post types and custom fields
    """
    
    def __init__(self):
        """Initialize WordPress importer"""
        super().__init__()
        
        # Default field mappings - can be customized
        self.field_mappings = {
            # WordPress custom field -> Our vessel schema field
            'vessel_name': 'vessel_name',
            'yacht_name': 'vessel_name',
            'boat_name': 'vessel_name',
            'name': 'vessel_name',
            
            # Identifiers
            'imo_number': 'imo_number',
            'imo': 'imo_number',
            'mmsi_number': 'mmsi_number',
            'mmsi': 'mmsi_number',
            'call_sign': 'call_sign',
            'callsign': 'call_sign',
            'official_number': 'official_number',
            
            # Basic info
            'vessel_type': 'vessel_type',
            'yacht_type': 'vessel_type',
            'boat_type': 'vessel_type',
            'type': 'vessel_type',
            'flag_state': 'flag_state',
            'flag': 'flag_state',
            'port_of_registry': 'port_of_registry',
            'home_port': 'home_port',
            
            # Dimensions
            'length_overall': 'length_overall',
            'length': 'length_overall',
            'loa': 'length_overall',
            'beam': 'beam',
            'width': 'beam',
            'draft': 'draft',
            'draught': 'draft',
            'gross_tonnage': 'gross_tonnage',
            'tonnage': 'gross_tonnage',
            'gt': 'gross_tonnage',
            
            # Construction
            'year_built': 'year_built',
            'built': 'year_built',
            'year': 'year_built',
            'builder': 'builder',
            'shipyard': 'builder',
            'manufacturer': 'builder',
            'hull_material': 'hull_material',
            'material': 'hull_material',
            
            # Yacht specific
            'guest_capacity': 'guest_capacity',
            'guests': 'guest_capacity',
            'crew_capacity': 'crew_capacity',
            'crew': 'crew_capacity',
            'guest_cabins': 'guest_cabins',
            'crew_cabins': 'crew_cabins',
            'max_speed': 'max_speed',
            'cruise_speed': 'cruise_speed',
            'range': 'range_nm',
            'fuel_capacity': 'fuel_capacity',
            'water_capacity': 'water_capacity',
            
            # Propulsion
            'propulsion_type': 'propulsion_type',
            'propulsion': 'propulsion_type',
            'engines': 'main_engines',
            'main_engines': 'main_engines',
            'engine_power': 'engine_power',
            'power': 'engine_power',
            
            # Description fields
            'description': 'description',
            'overview': 'description',
            'summary': 'description'
        }
    
    def import_from_wordpress_custom_post_type(
        self, 
        wordpress_url: str, 
        post_type: str = "gd_yacht",
        api_key: str = None,
        custom_field_mappings: Dict[str, str] = None
    ) -> APIResponse:
        """
        Import vessel data from WordPress custom post type
        
        Args:
            wordpress_url: WordPress site URL (e.g., 'https://yachtlycrew.com')
            post_type: Custom post type name (e.g., 'gd_yacht')
            api_key: API key for authentication (optional)
            custom_field_mappings: Custom field mappings to override defaults
            
        Returns:
            APIResponse with list of vessels
        """
        try:
            # Update field mappings if provided
            if custom_field_mappings:
                self.field_mappings.update(custom_field_mappings)
            
            # Get all posts of the custom post type
            vessels = []
            page = 1
            per_page = 50
            
            while True:
                posts_response = self._get_wordpress_posts(
                    wordpress_url, post_type, page, per_page, api_key
                )
                
                if not posts_response.success:
                    return posts_response
                
                posts = posts_response.data
                
                if not posts:
                    break  # No more posts
                
                # Process each post
                for post in posts:
                    vessel_data = self._extract_vessel_from_custom_post(
                        wordpress_url, post, api_key
                    )
                    if vessel_data:
                        vessels.append(vessel_data)
                
                # Check if we have more pages
                if len(posts) < per_page:
                    break
                
                page += 1
            
            return APIResponse(
                success=True,
                data={
                    'vessels': vessels,
                    'count': len(vessels),
                    'post_type': post_type,
                    'source_url': wordpress_url
                },
                source="wordpress"
            )
            
        except Exception as e:
            logger.error(f"WordPress custom post type import error: {e}")
            return APIResponse(
                success=False,
                error=f"WordPress import failed: {str(e)}",
                source="wordpress"
            )
    
    def _get_wordpress_posts(
        self, 
        wordpress_url: str, 
        post_type: str, 
        page: int, 
        per_page: int, 
        api_key: str = None
    ) -> APIResponse:
        """
        Get WordPress posts for a specific custom post type
        """
        try:
            # WordPress REST API endpoint for custom post types
            api_url = urljoin(wordpress_url, f'/wp-json/wp/v2/{post_type}')
            
            headers = {
                'User-Agent': 'Vessel Management System/1.0',
                'Accept': 'application/json'
            }
            
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            params = {
                'per_page': per_page,
                'page': page,
                'status': 'publish',
                '_embed': True  # Include embedded data like featured images
            }
            
            response = requests.get(api_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 404:
                return APIResponse(
                    success=False,
                    error=f"Custom post type '{post_type}' not found or not accessible via REST API",
                    source="wordpress"
                )
            
            response.raise_for_status()
            posts = response.json()
            
            return APIResponse(
                success=True,
                data=posts,
                source="wordpress"
            )
            
        except Exception as e:
            logger.error(f"Error fetching WordPress posts: {e}")
            return APIResponse(
                success=False,
                error=f"Failed to fetch posts: {str(e)}",
                source="wordpress"
            )
    
    def _extract_vessel_from_custom_post(
        self, 
        wordpress_url: str, 
        post: Dict[str, Any], 
        api_key: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract vessel data from WordPress custom post with custom fields
        """
        try:
            post_id = post.get('id')
            
            # Initialize vessel data with basic post information
            vessel_data = {
                'vessel_name': self._clean_html(post.get('title', {}).get('rendered', '')),
                'data_source': 'wordpress',
                'wordpress_id': post_id,
                'wordpress_url': post.get('link', ''),
                'created_date': post.get('date'),
                'updated_date': post.get('modified'),
                'slug': post.get('slug', ''),
                'description': self._clean_html(post.get('excerpt', {}).get('rendered', ''))
            }
            
            # Get custom fields (meta data)
            custom_fields = self._get_post_custom_fields(wordpress_url, post_id, api_key)
            
            if custom_fields:
                # Map custom fields to our vessel schema
                self._map_custom_fields_to_vessel_data(custom_fields, vessel_data)
            
            # Also try to extract from content as fallback
            content = self._clean_html(post.get('content', {}).get('rendered', ''))
            if content:
                self._extract_specs_from_content(content, vessel_data)
            
            # Get featured image if available
            if post.get('featured_media'):
                vessel_data['featured_image'] = self._get_featured_image_url(post)
            
            # Clean and validate the data
            vessel_data = self._clean_and_validate_vessel_data(vessel_data)
            
            return vessel_data if vessel_data.get('vessel_name') else None
            
        except Exception as e:
            logger.error(f"Error extracting vessel from custom post {post.get('id')}: {e}")
            return None
    
    def _get_post_custom_fields(
        self, 
        wordpress_url: str, 
        post_id: int, 
        api_key: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get custom fields (meta data) for a WordPress post
        """
        try:
            # WordPress REST API endpoint for post meta
            meta_url = urljoin(wordpress_url, f'/wp-json/wp/v2/posts/{post_id}/meta')
            
            headers = {
                'User-Agent': 'Vessel Management System/1.0',
                'Accept': 'application/json'
            }
            
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            response = requests.get(meta_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"Could not fetch custom fields for post {post_id}: {response.status_code}")
                return None
            
            meta_data = response.json()
            
            # Convert meta array to dictionary
            custom_fields = {}
            for meta in meta_data:
                key = meta.get('key', '')
                value = meta.get('value', '')
                
                # Skip WordPress internal fields
                if not key.startswith('_') and value:
                    custom_fields[key] = value
            
            return custom_fields
            
        except Exception as e:
            logger.error(f"Error fetching custom fields for post {post_id}: {e}")
            return None
    
    def _map_custom_fields_to_vessel_data(
        self, 
        custom_fields: Dict[str, Any], 
        vessel_data: Dict[str, Any]
    ):
        """
        Map WordPress custom fields to our vessel data structure
        """
        for wp_field, wp_value in custom_fields.items():
            # Normalize field name for matching
            normalized_field = wp_field.lower().replace('-', '_').replace(' ', '_')
            
            # Check if we have a mapping for this field
            if normalized_field in self.field_mappings:
                target_field = self.field_mappings[normalized_field]
                
                # Convert and validate the value
                converted_value = self._convert_field_value(target_field, wp_value)
                
                if converted_value is not None:
                    vessel_data[target_field] = converted_value
            else:
                # Store unmapped fields for debugging
                if 'custom_fields' not in vessel_data:
                    vessel_data['custom_fields'] = {}
                vessel_data['custom_fields'][wp_field] = wp_value
    
    def _convert_field_value(self, field_name: str, value: Any) -> Any:
        """
        Convert WordPress field value to appropriate type for our schema
        """
        if not value or value == '':
            return None
        
        try:
            # Numeric fields
            if field_name in ['length_overall', 'beam', 'draft', 'max_speed', 'cruise_speed', 'engine_power']:
                return float(str(value).replace(',', ''))
            
            elif field_name in ['year_built', 'guest_capacity', 'crew_capacity', 'guest_cabins', 'crew_cabins', 'gross_tonnage']:
                return int(str(value).replace(',', ''))
            
            # String fields - clean HTML and trim
            elif field_name in ['vessel_name', 'builder', 'flag_state', 'home_port', 'description']:
                cleaned = self._clean_html(str(value))
                return cleaned.strip() if cleaned else None
            
            # Enum fields that need normalization
            elif field_name == 'vessel_type':
                return self._normalize_vessel_type(str(value))
            
            elif field_name == 'hull_material':
                return self._normalize_hull_material(str(value))
            
            elif field_name == 'propulsion_type':
                return self._normalize_propulsion_type(str(value))
            
            # Default: return as string
            else:
                return str(value).strip()
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not convert field {field_name} with value {value}: {e}")
            return None
    
    def _normalize_vessel_type(self, value: str) -> str:
        """Normalize vessel type to our schema values"""
        value_lower = value.lower()
        
        if 'motor' in value_lower or 'power' in value_lower:
            return 'motor_yacht'
        elif 'sail' in value_lower:
            return 'sailing_yacht'
        elif 'super' in value_lower or 'mega' in value_lower:
            return 'superyacht'
        elif 'yacht' in value_lower:
            return 'yacht'
        else:
            return value_lower.replace(' ', '_')
    
    def _normalize_hull_material(self, value: str) -> str:
        """Normalize hull material to our schema values"""
        value_lower = value.lower()
        
        if 'fiber' in value_lower or 'glass' in value_lower:
            return 'fiberglass'
        elif 'alumin' in value_lower:
            return 'aluminum'
        elif 'steel' in value_lower:
            return 'steel'
        elif 'wood' in value_lower:
            return 'wood'
        elif 'carbon' in value_lower:
            return 'carbon_fiber'
        else:
            return value_lower.replace(' ', '_')
    
    def _normalize_propulsion_type(self, value: str) -> str:
        """Normalize propulsion type to our schema values"""
        value_lower = value.lower()
        
        if 'diesel' in value_lower:
            return 'diesel'
        elif 'electric' in value_lower:
            return 'electric'
        elif 'hybrid' in value_lower:
            return 'hybrid'
        elif 'sail' in value_lower:
            return 'sail'
        else:
            return value_lower.replace(' ', '_')
    
    def _extract_specs_from_content(self, content: str, vessel_data: Dict[str, Any]):
        """
        Extract vessel specifications from post content as fallback
        """
        # Only extract if not already set from custom fields
        if not vessel_data.get('imo_number'):
            imo_match = re.search(r'IMO[:\s]*(\d{7})', content, re.I)
            if imo_match:
                vessel_data['imo_number'] = imo_match.group(1)
        
        if not vessel_data.get('length_overall'):
            length_match = re.search(r'Length[:\s]*(\d+(?:\.\d+)?)\s*(?:m|meter|ft|feet)', content, re.I)
            if length_match:
                length = float(length_match.group(1))
                # Convert feet to meters if needed
                if 'ft' in length_match.group(0).lower():
                    length = length * 0.3048
                vessel_data['length_overall'] = length
        
        if not vessel_data.get('year_built'):
            year_match = re.search(r'(?:Built|Year)[:\s]*(19\d{2}|20\d{2})', content, re.I)
            if year_match:
                vessel_data['year_built'] = int(year_match.group(1))
    
    def _get_featured_image_url(self, post: Dict[str, Any]) -> Optional[str]:
        """
        Extract featured image URL from WordPress post
        """
        try:
            if post.get('_embedded', {}).get('wp:featuredmedia'):
                featured_media = post['_embedded']['wp:featuredmedia'][0]
                return featured_media.get('source_url')
        except (KeyError, IndexError, TypeError):
            pass
        
        return None
    
    def _clean_html(self, html_content: str) -> str:
        """
        Clean HTML content to plain text
        """
        if not html_content:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#039;', "'")
        clean_text = clean_text.replace('&nbsp;', ' ')
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()
    
    def _clean_and_validate_vessel_data(self, vessel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and validate vessel data before returning
        """
        # Remove empty values
        cleaned_data = {k: v for k, v in vessel_data.items() if v is not None and v != ''}
        
        # Ensure required fields have reasonable values
        if cleaned_data.get('vessel_name'):
            cleaned_data['vessel_name'] = cleaned_data['vessel_name'][:255]  # Limit length
        
        # Validate numeric fields
        if cleaned_data.get('length_overall'):
            length = cleaned_data['length_overall']
            if not (1 <= length <= 500):  # Reasonable range
                logger.warning(f"Invalid length_overall: {length}")
                del cleaned_data['length_overall']
        
        if cleaned_data.get('year_built'):
            year = cleaned_data['year_built']
            if not (1800 <= year <= 2030):  # Reasonable range
                logger.warning(f"Invalid year_built: {year}")
                del cleaned_data['year_built']
        
        return cleaned_data
    
    def get_available_custom_fields(
        self, 
        wordpress_url: str, 
        post_type: str = "gd_yacht",
        api_key: str = None
    ) -> APIResponse:
        """
        Get list of available custom fields for a post type (for debugging/setup)
        """
        try:
            # Get a few sample posts to see what fields are available
            posts_response = self._get_wordpress_posts(wordpress_url, post_type, 1, 5, api_key)
            
            if not posts_response.success:
                return posts_response
            
            posts = posts_response.data
            all_fields = set()
            
            for post in posts:
                custom_fields = self._get_post_custom_fields(wordpress_url, post['id'], api_key)
                if custom_fields:
                    all_fields.update(custom_fields.keys())
            
            return APIResponse(
                success=True,
                data={
                    'available_fields': sorted(list(all_fields)),
                    'post_type': post_type,
                    'sample_posts_checked': len(posts)
                },
                source="wordpress"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Could not get custom fields: {str(e)}",
                source="wordpress"
            )


# Example usage
if __name__ == "__main__":
    # Initialize the importer
    importer = WordPressImporter()
    
    # Import from yachtlycrew.com
    result = importer.import_from_wordpress_custom_post_type(
        wordpress_url="https://yachtlycrew.com",
        post_type="gd_yacht"
    )
    
    if result.success:
        print(f"Successfully imported {result.data['count']} yachts")
        for yacht in result.data['vessels'][:3]:  # Show first 3
            print(f"- {yacht.get('vessel_name', 'Unknown')} ({yacht.get('year_built', 'Unknown year')})")
    else:
        print(f"Import failed: {result.error}")