"""
BOAT International Web Scraper
Handles respectful scraping of yacht data from BOAT International website
"""

import requests
import json
import logging
import re
import random
from typing import Dict, Any, List
from datetime import datetime
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from .base_scraper import BaseScraper, APIResponse

logger = logging.getLogger(__name__)

class BoatInternationalScraper(BaseScraper):
    """
    BOAT International web scraper
    Respectfully scrapes yacht data from boatinternational.com
    """
    
    def __init__(self):
        """Initialize BOAT International scraper"""
        super().__init__()
    
    def scrape_boat_international_yacht(self, yacht_url: str) -> APIResponse:
        """
        Scrape individual yacht page from BOAT International
        Updated to handle superyacht directory URLs
        """
        # Validate URL - now accepts directory URLs too
        if 'boatinternational.com' not in yacht_url:
            return APIResponse(
                success=False,
                error="URL must be from boatinternational.com",
                source="boat_international"
            )
        
        # Check cache first
        cache_key = f"boat_intl_{yacht_url.split('/')[-1]}"
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        try:
            # Rate limiting - be respectful to BOAT International
            self._enforce_rate_limit("boat_international", min_interval=3)
            
            # Headers to appear as regular browser
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
            
            response = requests.get(yacht_url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                yacht_data = self._parse_boat_international_directory_page(response.text, yacht_url)
                api_response = APIResponse(
                    success=True,
                    data=yacht_data,
                    source="boat_international"
                )
            else:
                api_response = APIResponse(
                    success=False,
                    error=f"Failed to load page: HTTP {response.status_code}",
                    source="boat_international"
                )
            
            # Cache the response
            self._cache_response(cache_key, api_response)
            return api_response
            
        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False,
                error=f"Request failed: {str(e)}",
                source="boat_international"
            )
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Scraping error: {str(e)}",
                source="boat_international"
            )

    def search_boat_international_yachts(self, yacht_name: str) -> APIResponse:
        """
        Improved search for BOAT International yachts
        Uses multiple search strategies to find yacht profiles
        """
        try:
            # Rate limiting
            self._enforce_rate_limit("boat_international", min_interval=3)
            
            # Try multiple search strategies
            all_results = []
            
            # Strategy 1: Directory search
            try:
                directory_results = self._search_superyacht_directory(yacht_name)
                if directory_results:
                    all_results.extend(directory_results)
                    logger.info(f"Found {len(directory_results)} results from directory search")
            except Exception as e:
                logger.warning(f"Directory search failed: {e}")
            
            # Strategy 2: Site-wide search
            try:
                site_results = self._search_site_wide(yacht_name)
                if site_results:
                    all_results.extend(site_results)
                    logger.info(f"Found {len(site_results)} results from site search")
            except Exception as e:
                logger.warning(f"Site search failed: {e}")
            
            # Strategy 3: Alternate terms
            try:
                alt_results = self._search_with_alternate_terms(yacht_name)
                if alt_results:
                    all_results.extend(alt_results)
                    logger.info(f"Found {len(alt_results)} results from alternate terms")
            except Exception as e:
                logger.warning(f"Alternate terms search failed: {e}")
            
            # Remove duplicates and rank results
            unique_results = self._deduplicate_and_rank_results(all_results, yacht_name)
            
            return APIResponse(
                success=True,
                data={
                    'search_query': yacht_name,
                    'results_count': len(unique_results),
                    'yacht_urls': unique_results[:15],  # Top 15 results
                    'data_source': 'boat_international',
                    'search_type': 'multi_strategy',
                    'confidence': self._calculate_search_confidence(unique_results, yacht_name)
                },
                source="boat_international"
            )
            
        except Exception as e:
            logger.error(f"Search failed for yacht '{yacht_name}': {e}")
            return APIResponse(
                success=False,
                error=f"Search error: {str(e)}",
                source="boat_international"
            )

    def _search_superyacht_directory(self, yacht_name: str) -> List[Dict[str, Any]]:
        """
        Search specifically in the superyacht directory
        """
        # Try different search URL patterns
        search_urls = [
            f"https://www.boatinternational.com/yachts/the-superyacht-directory?search={quote(yacht_name)}",
            f"https://www.boatinternational.com/yachts/the-superyacht-directory?q={quote(yacht_name)}",
            f"https://www.boatinternational.com/yachts/the-superyacht-directory?name={quote(yacht_name)}"
        ]
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate'
        }
        
        for search_url in search_urls:
            try:
                response = requests.get(search_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    results = self._parse_directory_search_results(response.text, yacht_name)
                    if results:
                        return results
                        
            except Exception as e:
                logger.warning(f"Directory search URL failed: {search_url} - {e}")
                continue
        
        return []

    def _search_site_wide(self, yacht_name: str) -> List[Dict[str, Any]]:
        """
        Perform site-wide search using BOAT International's main search
        """
        search_url = f"https://www.boatinternational.com/search?q={quote(yacht_name)}"
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.boatinternational.com/'
        }
        
        try:
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self._parse_site_search_results(response.text, yacht_name)
                
        except Exception as e:
            logger.warning(f"Site-wide search failed: {e}")
        
        return []

    def _search_with_alternate_terms(self, yacht_name: str) -> List[Dict[str, Any]]:
        """
        Search with alternate yacht name formats
        """
        # Generate alternate search terms
        alternate_terms = self._generate_alternate_yacht_names(yacht_name)
        
        results = []
        for term in alternate_terms[:3]:  # Try top 3 alternates
            if term != yacht_name:  # Don't repeat the original search
                try:
                    alt_results = self._search_superyacht_directory(term)
                    if alt_results:
                        results.extend(alt_results)
                except Exception as e:
                    logger.warning(f"Alternate term search failed for '{term}': {e}")
                    continue
        
        return results

    def _parse_directory_search_results(self, html_content: str, yacht_name: str) -> List[Dict[str, Any]]:
        """
        Parse search results from the superyacht directory
        Updated to handle the actual URL structure: yacht-name--yacht-id
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        yacht_links = []
        
        # More specific selectors for the superyacht directory
        link_selectors = [
            # Direct links to yacht profiles
            'a[href*="/the-superyacht-directory/"][href*="--"]',
            # Links within yacht result cards
            '.yacht-card a[href*="/the-superyacht-directory/"]',
            '.search-result a[href*="/the-superyacht-directory/"]',
            '.yacht-listing a[href*="/the-superyacht-directory/"]',
            # Generic yacht directory links
            'a[href*="/yachts/the-superyacht-directory/"][href*="--"]',
            # Links in result containers
            '.result a[href*="--"]',
            '.listing a[href*="--"]'
        ]
        
        for selector in link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and self._is_valid_yacht_url(href):
                    # Ensure full URL
                    if not href.startswith('http'):
                        href = urljoin('https://www.boatinternational.com', href)
                    
                    # Extract yacht name from link text or URL
                    link_text = self._extract_yacht_name_from_link(link, href)
                    
                    if link_text and len(link_text) > 2:
                        yacht_links.append({
                            'url': href,
                            'title': link_text,
                            'similarity': self._calculate_name_similarity(yacht_name, link_text),
                            'source': 'directory_search'
                        })
        
        return yacht_links

    def _parse_site_search_results(self, html_content: str, yacht_name: str) -> List[Dict[str, Any]]:
        """
        Parse results from site-wide search
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        yacht_links = []
        
        # Look for any yacht directory links in search results
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            if href and self._is_valid_yacht_url(href):
                # Ensure full URL
                if not href.startswith('http'):
                    href = urljoin('https://www.boatinternational.com', href)
                
                link_text = self._extract_yacht_name_from_link(link, href)
                
                if link_text:
                    yacht_links.append({
                        'url': href,
                        'title': link_text,
                        'similarity': self._calculate_name_similarity(yacht_name, link_text),
                        'source': 'site_search'
                    })
        
        return yacht_links

    def _is_valid_yacht_url(self, url: str) -> bool:
        """
        Check if URL matches the yacht profile pattern
        URL structure: /yachts/the-superyacht-directory/yacht-name--yacht-id
        """
        if not url:
            return False
        
        # Check for the specific yacht directory pattern
        yacht_pattern = r'/yachts/the-superyacht-directory/[^/]+--\d+/?$'
        
        return bool(re.search(yacht_pattern, url))

    def _extract_yacht_name_from_link(self, link_element, url: str) -> str:
        """
        Extract yacht name from link text or URL
        """
        # First try to get from link text
        link_text = link_element.get_text().strip()
        
        # Clean up common prefixes/suffixes
        if link_text:
            # Remove common yacht prefixes
            link_text = re.sub(r'^(M/Y|S/Y|Motor Yacht|Sailing Yacht)\s+', '', link_text, flags=re.IGNORECASE)
            link_text = re.sub(r'\s+(M/Y|S/Y|Motor Yacht|Sailing Yacht)$', '', link_text, flags=re.IGNORECASE)
            
            # Remove extra whitespace
            link_text = re.sub(r'\s+', ' ', link_text).strip()
            
            # If reasonable length, use it
            if 2 <= len(link_text) <= 50:
                return link_text
        
        # If no good link text, extract from URL
        # URL format: /yachts/the-superyacht-directory/yacht-name--yacht-id
        url_match = re.search(r'/the-superyacht-directory/([^/]+)--\d+', url)
        if url_match:
            yacht_name = url_match.group(1)
            # Convert hyphens to spaces and title case
            yacht_name = yacht_name.replace('-', ' ').title()
            return yacht_name
        
        return link_text or "Unknown"

    def _generate_alternate_yacht_names(self, yacht_name: str) -> List[str]:
        """
        Generate alternate yacht name formats for searching
        """
        alternates = []
        
        # Original name
        alternates.append(yacht_name)
        
        # With common prefixes
        prefixes = ['M/Y', 'S/Y', 'Motor Yacht', 'Sailing Yacht']
        for prefix in prefixes:
            alternates.append(f"{prefix} {yacht_name}")
        
        # Without common prefixes (if they exist)
        cleaned = re.sub(r'^(M/Y|S/Y|Motor Yacht|Sailing Yacht)\s+', '', yacht_name, flags=re.IGNORECASE)
        if cleaned != yacht_name:
            alternates.append(cleaned)
        
        # With/without spaces and hyphens
        alternates.append(yacht_name.replace(' ', '-'))
        alternates.append(yacht_name.replace('-', ' '))
        
        # Remove duplicates while preserving order
        unique_alternates = []
        seen = set()
        for alt in alternates:
            if alt not in seen:
                unique_alternates.append(alt)
                seen.add(alt)
        
        return unique_alternates

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two yacht names
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize names for comparison
        name1_norm = self._normalize_yacht_name(name1)
        name2_norm = self._normalize_yacht_name(name2)
        
        # Calculate multiple similarity metrics
        sequence_match = SequenceMatcher(None, name1_norm, name2_norm).ratio()
        
        # Bonus for exact matches after normalization
        if name1_norm == name2_norm:
            return 1.0
        
        # Bonus for one name being contained in the other
        if name1_norm in name2_norm or name2_norm in name1_norm:
            sequence_match += 0.2
        
        # Bonus for word matches
        words1 = set(name1_norm.split())
        words2 = set(name2_norm.split())
        word_intersection = len(words1 & words2)
        word_union = len(words1 | words2)
        
        if word_union > 0:
            word_similarity = word_intersection / word_union
            sequence_match = (sequence_match + word_similarity) / 2
        
        return min(sequence_match, 1.0)

    def _normalize_yacht_name(self, name: str) -> str:
        """
        Normalize yacht name for comparison
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common prefixes
        normalized = re.sub(r'^(m/y|s/y|motor yacht|sailing yacht)\s+', '', normalized)
        
        # Remove special characters except spaces and hyphens
        normalized = re.sub(r'[^\w\s\-]', '', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

    def _deduplicate_and_rank_results(self, results: List[Dict[str, Any]], yacht_name: str) -> List[Dict[str, Any]]:
        """
        Remove duplicates and rank results by relevance
        """
        # Remove duplicates by URL
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # Sort by similarity score (descending)
        unique_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        # Boost results that are exact or very close matches
        for result in unique_results:
            if result.get('similarity', 0) > 0.9:
                result['boost'] = True
        
        return unique_results

    def _calculate_search_confidence(self, results: List[Dict[str, Any]], yacht_name: str) -> float:
        """
        Calculate overall confidence in search results
        """
        if not results:
            return 0.0
        
        # Base confidence on number of results and similarity scores
        num_results = len(results)
        avg_similarity = sum(r.get('similarity', 0) for r in results) / num_results
        
        # Higher confidence for more results and higher similarity
        confidence = min(0.5 + (num_results * 0.1) + (avg_similarity * 0.4), 1.0)
        
        # Boost confidence if we have high-similarity matches
        if any(r.get('similarity', 0) > 0.9 for r in results):
            confidence += 0.2
        
        return min(confidence, 1.0)

    def _parse_boat_international_directory_page(self, html_content: str, yacht_url: str) -> Dict[str, Any]:
        """
        Parse BOAT International superyacht directory page
        Specifically designed for directory URLs like /the-superyacht-directory/yacht-name--id
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            yacht_data = {
                'data_source': 'boat_international',
                'source_url': yacht_url,
                'scraped_date': datetime.now().isoformat(),
                'vessel_type': 'superyacht'  # Default for directory entries
            }
            
            # Extract yacht name - try multiple selectors for directory pages
            name_selectors = [
                'h1.yacht-profile__title',
                'h1.profile-header__title',
                'h1[class*="yacht"]',
                'h1[class*="profile"]',
                '.yacht-name',
                'h1.page-title',
                'h1',
                '[data-yacht-name]'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    yacht_name = name_elem.get_text().strip()
                    # Clean up common prefixes/suffixes
                    yacht_name = re.sub(r'^(Motor Yacht|Sailing Yacht|M/Y|S/Y)\s+', '', yacht_name, flags=re.IGNORECASE)
                    yacht_name = re.sub(r'\s+(Motor Yacht|Sailing Yacht|M/Y|S/Y)$', '', yacht_name, flags=re.IGNORECASE)
                    yacht_data['vessel_name'] = yacht_name.strip()
                    break
            
            # Look for specifications section - directory pages often have structured specs
            spec_sections = [
                '.yacht-specs',
                '.yacht-details',
                '.profile-specs',
                '.specifications',
                '[class*="spec"]',
                '[class*="detail"]'
            ]
            
            for section_selector in spec_sections:
                sections = soup.select(section_selector)
                for section in sections:
                    self._extract_directory_specs_from_section(section, yacht_data)
            
            # Look for definition lists (common in directory pages)
            spec_lists = soup.select('dl, .spec-list, .details-list')
            for dl in spec_lists:
                self._extract_specs_from_definition_list(dl, yacht_data)
            
            # Look for table-based specifications
            spec_tables = soup.select('table, .spec-table, .yacht-table')
            for table in spec_tables:
                self._extract_specs_from_table(table, yacht_data)
            
            # Extract from structured data and meta tags
            self._extract_structured_data(soup, yacht_data)
            
            # Try to extract from all text if structured data not sufficient
            if len([k for k, v in yacht_data.items() if v and k not in ['data_source', 'source_url', 'scraped_date', 'vessel_type']]) < 3:
                self._extract_directory_specs_from_text(soup.get_text(), yacht_data)
            
            # Set confidence based on how much data we extracted
            confidence = self._calculate_directory_extraction_confidence(yacht_data)
            yacht_data['confidence_score'] = confidence
            
            return yacht_data
            
        except Exception as e:
            logger.error(f"Error parsing BOAT International directory page: {e}")
            return {
                'data_source': 'boat_international',
                'source_url': yacht_url,
                'error': f"Parsing error: {str(e)}",
                'confidence_score': 0
            }

    def _extract_directory_specs_from_section(self, section, yacht_data: Dict[str, Any]):
        """Extract specifications from directory page sections"""
        text = section.get_text()
        
        # Enhanced patterns for directory pages
        spec_patterns = {
            'length_overall': [
                r'Length[:\s]*(\d+(?:\.\d+)?)\s*m',
                r'LOA[:\s]*(\d+(?:\.\d+)?)\s*m',
                r'Overall[:\s]*(\d+(?:\.\d+)?)\s*m',
                r'(\d+(?:\.\d+)?)\s*m\s*(?:LOA|length|overall)',
                r'(\d+(?:\.\d+)?)\s*metres?\s*(?:long|length)'
            ],
            'beam': [
                r'Beam[:\s]*(\d+(?:\.\d+)?)\s*m',
                r'Width[:\s]*(\d+(?:\.\d+)?)\s*m',
                r'(\d+(?:\.\d+)?)\s*m\s*beam'
            ],
            'year_built': [
                r'Built[:\s]*(\d{4})',
                r'Year[:\s]*(\d{4})',
                r'Delivered[:\s]*(\d{4})',
                r'Launched[:\s]*(\d{4})',
                r'(\d{4})\s*(?:built|delivered|launched)'
            ],
            'builder': [
                r'Builder[:\s]*([A-Za-z\s&\-]+?)(?:\n|\r|$|[0-9])',
                r'Shipyard[:\s]*([A-Za-z\s&\-]+?)(?:\n|\r|$|[0-9])',
                r'Built\s+by[:\s]*([A-Za-z\s&\-]+?)(?:\n|\r|$|[0-9])'
            ],
            'guest_capacity': [
                r'Guests[:\s]*(\d+)',
                r'Sleeps[:\s]*(\d+)',
                r'(\d+)\s*guests?'
            ],
            'crew_capacity': [
                r'Crew[:\s]*(\d+)',
                r'(\d+)\s*crew'
            ],
            'draft': [
                r'Draft[:\s]*(\d+(?:\.\d+)?)\s*m',
                r'Draught[:\s]*(\d+(?:\.\d+)?)\s*m'
            ],
            'gross_tonnage': [
                r'(?:Gross\s+)?Tonnage[:\s]*(\d+(?:,\d+)?)',
                r'GT[:\s]*(\d+(?:,\d+)?)',
                r'(\d+(?:,\d+)?)\s*GT'
            ]
        }
        
        for field, patterns in spec_patterns.items():
            if field not in yacht_data or not yacht_data[field]:  # Don't overwrite existing data
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        try:
                            value = match.group(1).replace(',', '')  # Remove commas from numbers
                            if field in ['length_overall', 'beam', 'draft']:
                                yacht_data[field] = float(value)
                            elif field in ['year_built', 'guest_capacity', 'crew_capacity', 'gross_tonnage']:
                                yacht_data[field] = int(value)
                            else:
                                # Clean up builder names
                                if field == 'builder':
                                    value = re.sub(r'\s+', ' ', value.strip())
                                    if len(value) > 2 and len(value) < 50:  # Reasonable builder name length
                                        yacht_data[field] = value
                                else:
                                    yacht_data[field] = value.strip()
                            break
                        except (ValueError, IndexError):
                            continue

    def _extract_specs_from_definition_list(self, dl_element, yacht_data: Dict[str, Any]):
        """Extract specs from definition list (dl/dt/dd structure)"""
        terms = dl_element.find_all('dt')
        definitions = dl_element.find_all('dd')
        
        for i, term in enumerate(terms):
            if i < len(definitions):
                term_text = term.get_text().strip().lower()
                definition_text = definitions[i].get_text().strip()
                
                # Map common terms to our schema
                field_mapping = {
                    'length': 'length_overall',
                    'loa': 'length_overall',
                    'beam': 'beam',
                    'year': 'year_built',
                    'built': 'year_built',
                    'builder': 'builder',
                    'shipyard': 'builder',
                    'guests': 'guest_capacity',
                    'crew': 'crew_capacity'
                }
                
                for term_key, field_name in field_mapping.items():
                    if term_key in term_text and field_name not in yacht_data:
                        # Extract numeric values
                        if field_name in ['length_overall', 'beam']:
                            match = re.search(r'(\d+(?:\.\d+)?)', definition_text)
                            if match:
                                yacht_data[field_name] = float(match.group(1))
                        elif field_name in ['year_built', 'guest_capacity', 'crew_capacity']:
                            match = re.search(r'(\d+)', definition_text)
                            if match:
                                yacht_data[field_name] = int(match.group(1))
                        else:
                            yacht_data[field_name] = definition_text
                        break

    def _extract_specs_from_table(self, table_element, yacht_data: Dict[str, Any]):
        """Extract specs from table elements"""
        rows = table_element.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key_text = cells[0].get_text().strip().lower()
                value_text = cells[1].get_text().strip()
                
                # Map table headers to our schema
                field_mapping = {
                    'length': 'length_overall',
                    'loa': 'length_overall',
                    'beam': 'beam',
                    'year': 'year_built',
                    'built': 'year_built',
                    'builder': 'builder',
                    'shipyard': 'builder',
                    'guests': 'guest_capacity',
                    'crew': 'crew_capacity',
                    'draft': 'draft',
                    'tonnage': 'gross_tonnage',
                    'gt': 'gross_tonnage'
                }
                
                for key_match, field_name in field_mapping.items():
                    if key_match in key_text and (field_name not in yacht_data or not yacht_data[field_name]):
                        # Extract numeric values
                        if field_name in ['length_overall', 'beam', 'draft']:
                            match = re.search(r'(\d+(?:\.\d+)?)', value_text)
                            if match:
                                yacht_data[field_name] = float(match.group(1))
                        elif field_name in ['year_built', 'guest_capacity', 'crew_capacity', 'gross_tonnage']:
                            match = re.search(r'(\d+)', value_text.replace(',', ''))
                            if match:
                                yacht_data[field_name] = int(match.group(1))
                        else:
                            if len(value_text) > 2 and len(value_text) < 100:
                                yacht_data[field_name] = value_text
                        break

    def _extract_structured_data(self, soup, yacht_data: Dict[str, Any]):
        """Extract data from JSON-LD or meta tags"""
        # Look for JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Map schema.org properties to our fields
                    if data.get('@type') in ['Boat', 'Product']:
                        if 'name' in data and 'vessel_name' not in yacht_data:
                            yacht_data['vessel_name'] = data['name']
                        
                        # Extract other properties if available
                        if 'manufacturer' in data and 'builder' not in yacht_data:
                            yacht_data['builder'] = data['manufacturer']
                            
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Extract from meta tags
        meta_mappings = {
            'og:title': 'vessel_name',
            'twitter:title': 'vessel_name'
        }
        
        for meta_property, field_name in meta_mappings.items():
            if field_name not in yacht_data:
                meta_tag = soup.find('meta', property=meta_property) or soup.find('meta', attrs={'name': meta_property})
                if meta_tag and meta_tag.get('content'):
                    yacht_data[field_name] = meta_tag['content'].strip()

    def _extract_directory_specs_from_text(self, full_text: str, yacht_data: Dict[str, Any]):
        """Extract specs from full page text for directory pages"""
        
        # More aggressive length extraction for directory pages
        if 'length_overall' not in yacht_data or not yacht_data['length_overall']:
            length_patterns = [
                r'(\d+(?:\.\d+)?)\s*(?:meters?|metres?|m)\s*(?:long|length|overall|LOA)',
                r'(?:length|LOA)(?:\s*:)?\s*(\d+(?:\.\d+)?)\s*(?:m|meters?|metres?)',
                r'(\d{2,3}(?:\.\d+)?)\s*m(?:\s|$)',  # Simple "45m" pattern
                r'(\d{2,3}(?:\.\d+)?)\s*metres?(?:\s|$)'
            ]
            
            for pattern in length_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    try:
                        length = float(match.group(1))
                        if 20 <= length <= 200:  # Reasonable superyacht length range
                            yacht_data['length_overall'] = length
                            break
                    except ValueError:
                        continue
        
        # Extract year if not found
        if 'year_built' not in yacht_data or not yacht_data['year_built']:
            year_patterns = [
                r'(?:built|delivered|launched)(?:\s+in)?\s+(19\d{2}|20\d{2})',
                r'(19\d{2}|20\d{2})(?:\s+(?:built|delivered|launched))',
                r'\b(19\d{2}|20\d{2})\b'  # Any 4-digit year
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    try:
                        year = int(match if isinstance(match, str) else match[0])
                        if 1980 <= year <= datetime.now().year + 2:  # Reasonable yacht year range
                            yacht_data['year_built'] = year
                            break
                    except (ValueError, IndexError):
                        continue
                if yacht_data.get('year_built'):
                    break

    def _calculate_directory_extraction_confidence(self, yacht_data: Dict[str, Any]) -> float:
        """Calculate confidence score for directory page extraction"""
        confidence = 0.0
        
        # Essential fields with higher weights
        if yacht_data.get('vessel_name'):
            confidence += 0.4  # Name is very important
        if yacht_data.get('length_overall'):
            confidence += 0.3  # Length is crucial for yachts
        if yacht_data.get('year_built'):
            confidence += 0.1
        if yacht_data.get('builder'):
            confidence += 0.1
        
        # Additional fields
        additional_fields = ['beam', 'guest_capacity', 'crew_capacity', 'draft', 'gross_tonnage']
        for field in additional_fields:
            if yacht_data.get(field):
                confidence += 0.02  # Small bonus for each additional field
        
        return min(confidence, 1.0)  # Cap at 1.0