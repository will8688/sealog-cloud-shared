"""
Base scraper with common functionality for all external APIs
"""

import requests
import time
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import re
import random

logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """Standardized API response format"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source: Optional[str] = None
    cached: bool = False

class BaseScraper:
    """
    Base class for external API integrations
    Handles rate limiting, caching, and common utilities
    """
    
    def __init__(self):
        """Initialize base scraper"""
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 2  # seconds between requests
        
        # Caching
        self.cache = {}
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        
        # User agents for web scraping
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
    
    def _enforce_rate_limit(self, service: str, min_interval: int = None):
        """Enforce rate limiting for API requests"""
        interval = min_interval or self.min_request_interval
        
        if service in self.last_request_time:
            elapsed = time.time() - self.last_request_time[service]
            if elapsed < interval:
                sleep_time = interval - elapsed
                logger.debug(f"Rate limiting {service}: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.last_request_time[service] = time.time()
    
    def _get_cached_response(self, cache_key: str) -> Optional[APIResponse]:
        """Get cached API response if still valid"""
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                cached_data.cached = True
                logger.debug(f"Using cached response for {cache_key}")
                return cached_data
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        
        return None
    
    def _cache_response(self, cache_key: str, response: APIResponse):
        """Cache API response"""
        self.cache[cache_key] = (response, datetime.now())
        logger.debug(f"Cached response for {cache_key}")
    
    def clear_cache(self):
        """Clear all cached responses"""
        self.cache.clear()
        logger.info("Cleared API response cache")
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity score between vessel names"""
        if not name1 or not name2:
            return 0.0
        
        name1_clean = re.sub(r'[^\w\s]', '', name1.lower())
        name2_clean = re.sub(r'[^\w\s]', '', name2.lower())
        
        # Simple word overlap scoring
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Jaccard similarity
        jaccard_score = len(intersection) / len(union) if union else 0.0
        
        # Bonus for exact substring matches
        substring_bonus = 0.0
        if name1_clean in name2_clean or name2_clean in name1_clean:
            substring_bonus = 0.2
        
        # Bonus for similar length names
        length_similarity = 1 - abs(len(name1_clean) - len(name2_clean)) / max(len(name1_clean), len(name2_clean))
        length_bonus = length_similarity * 0.1
        
        total_score = jaccard_score + substring_bonus + length_bonus
        return min(total_score, 1.0)  # Cap at 1.0
    
    def _extract_length_from_text(self, text: str) -> Optional[float]:
        """Extract length in meters from text"""
        if not text:
            return None
        
        # Look for patterns like "45 ft", "15 m", "120 feet", "30.5 meters"
        length_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:ft|feet|foot)\b',  # Feet
            r'(\d+(?:\.\d+)?)\s*(?:m|meter|metres?)\b',  # Meters
            r'(\d+(?:\.\d+)?)\s*(?:m)\s*(?:long|length|overall)',  # "45m long"
        ]
        
        for pattern in length_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    length = float(match.group(1))
                    
                    # Convert feet to meters if needed
                    if any(unit in match.group(0).lower() for unit in ['ft', 'feet', 'foot']):
                        length = length * 0.3048
                    
                    # Sanity check - reasonable yacht length
                    if 5 <= length <= 300:  # 5m to 300m is reasonable range
                        return length
                except ValueError:
                    continue
        
        return None
    
    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """Extract year from text"""
        if not text:
            return None
        
        # Look for 4-digit years
        year_patterns = [
            r'\b(19\d{2}|20\d{2})\b',  # 1900-2099
            r'(?:built|delivered|launched)(?:\s+in)?\s+(19\d{2}|20\d{2})',  # "built 2015"
            r'(19\d{2}|20\d{2})(?:\s+(?:built|delivered|launched))',  # "2015 built"
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    year = int(match if isinstance(match, str) else match[0])
                    # Reasonable year range for vessels
                    if 1800 <= year <= datetime.now().year + 5:
                        return year
                except (ValueError, IndexError):
                    continue
        
        return None