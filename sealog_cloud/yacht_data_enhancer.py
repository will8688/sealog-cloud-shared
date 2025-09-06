# yacht_data_enhancer.py
"""
Yacht Data Enhancement Engine
A modular system to search and aggregate yacht data from multiple public sources.
Simply drop this file into your project and use enhance_yacht_data() function.
"""

import asyncio
import aiohttp
import requests
from typing import Dict, List, Optional, Any
import time
import json
import re
from urllib.parse import quote_plus, urljoin
from dataclasses import dataclass, asdict
import logging
from concurrent.futures import ThreadPoolExecutor
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class YachtData:
    """Standardized yacht data structure"""
    name: Optional[str] = None
    imo: Optional[str] = None
    mmsi: Optional[str] = None
    length: Optional[float] = None
    beam: Optional[float] = None
    year_built: Optional[int] = None
    builder: Optional[str] = None
    designer: Optional[str] = None
    owner: Optional[str] = None
    flag: Optional[str] = None
    gross_tonnage: Optional[float] = None
    max_speed: Optional[float] = None
    cruise_speed: Optional[float] = None
    guests: Optional[int] = None
    crew: Optional[int] = None
    price: Optional[str] = None
    location: Optional[str] = None
    yacht_type: Optional[str] = None
    sources: List[str] = None
    confidence_score: float = 0.0
    last_updated: Optional[str] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []

class DataSourceAdapter:
    """Base class for data source adapters"""
    
    def __init__(self, name: str, base_url: str, rate_limit: float = 1.0):
        self.name = name
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.last_request = 0
        self.session = None
    
    async def _rate_limit(self):
        """Enforce rate limiting"""
        now = time.time()
        time_since_last = now - self.last_request
        if time_since_last < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last)
        self.last_request = time.time()
    
    async def search(self, yacht_name: str) -> Optional[YachtData]:
        """Override in subclasses"""
        raise NotImplementedError

class MarineTrafficAdapter(DataSourceAdapter):
    """MarineTraffic API adapter"""
    
    def __init__(self):
        super().__init__("MarineTraffic", "https://www.marinetraffic.com", 2.0)
    
    async def search(self, yacht_name: str) -> Optional[YachtData]:
        await self._rate_limit()
        
        try:
            # Using their search endpoint (this is a simplified example)
            search_url = f"{self.base_url}/en/ais/details/ships/search"
            params = {'query': yacht_name}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        # Parse response (implementation depends on actual API)
                        data = await response.text()
                        return self._parse_marinetraffic_data(data, yacht_name)
        except Exception as e:
            logger.warning(f"MarineTraffic search failed for {yacht_name}: {e}")
        
        return None
    
    def _parse_marinetraffic_data(self, html_data: str, yacht_name: str) -> Optional[YachtData]:
        """Parse MarineTraffic response"""
        # This would contain actual parsing logic
        # For demo purposes, returning mock data
        if "yacht" in html_data.lower():
            return YachtData(
                name=yacht_name,
                sources=[self.name],
                confidence_score=0.7
            )
        return None

class VesselFinderAdapter(DataSourceAdapter):
    """VesselFinder adapter"""
    
    def __init__(self):
        super().__init__("VesselFinder", "https://www.vesselfinder.com", 1.5)
    
    async def search(self, yacht_name: str) -> Optional[YachtData]:
        await self._rate_limit()
        
        try:
            search_url = f"{self.base_url}/vessels?name={quote_plus(yacht_name)}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.text()
                        return self._parse_vesselfinder_data(data, yacht_name)
        except Exception as e:
            logger.warning(f"VesselFinder search failed for {yacht_name}: {e}")
        
        return None
    
    def _parse_vesselfinder_data(self, html_data: str, yacht_name: str) -> Optional[YachtData]:
        """Parse VesselFinder response"""
        # Mock implementation - replace with actual parsing
        if yacht_name.lower() in html_data.lower():
            return YachtData(
                name=yacht_name,
                sources=[self.name],
                confidence_score=0.6
            )
        return None

class SuperYachtTimesAdapter(DataSourceAdapter):
    """SuperYacht Times adapter"""
    
    def __init__(self):
        super().__init__("SuperYacht Times", "https://www.superyachttimes.com", 2.0)
    
    async def search(self, yacht_name: str) -> Optional[YachtData]:
        await self._rate_limit()
        
        try:
            # Their search endpoint
            search_url = f"{self.base_url}/yachts"
            params = {'search': yacht_name}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.text()
                        return self._parse_syt_data(data, yacht_name)
        except Exception as e:
            logger.warning(f"SuperYacht Times search failed for {yacht_name}: {e}")
        
        return None
    
    def _parse_syt_data(self, html_data: str, yacht_name: str) -> Optional[YachtData]:
        """Parse SuperYacht Times response"""
        # Mock implementation with more detailed data
        if yacht_name.lower() in html_data.lower():
            return YachtData(
                name=yacht_name,
                length=85.0,  # Mock data
                year_built=2020,
                builder="Mock Builder",
                sources=[self.name],
                confidence_score=0.8
            )
        return None

class YachtDataEnhancer:
    """Main yacht data enhancement engine"""
    
    def __init__(self):
        self.adapters = [
            MarineTrafficAdapter(),
            VesselFinderAdapter(),
            SuperYachtTimesAdapter(),
        ]
        self.cache = {}
    
    async def search_all_sources(self, yacht_name: str) -> List[YachtData]:
        """Search all data sources concurrently"""
        
        # Check cache first
        cache_key = yacht_name.lower().strip()
        if cache_key in self.cache:
            logger.info(f"Cache hit for {yacht_name}")
            return self.cache[cache_key]
        
        # Search all sources concurrently
        tasks = [adapter.search(yacht_name) for adapter in self.adapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_results = [
            result for result in results 
            if isinstance(result, YachtData) and result is not None
        ]
        
        # Cache results
        self.cache[cache_key] = valid_results
        
        return valid_results
    
    def merge_yacht_data(self, data_list: List[YachtData]) -> YachtData:
        """Merge data from multiple sources into a single record"""
        if not data_list:
            return YachtData()
        
        # Start with the highest confidence result
        merged = YachtData()
        all_sources = []
        total_confidence = 0
        
        for data in data_list:
            all_sources.extend(data.sources)
            total_confidence += data.confidence_score
            
            # Merge fields, preferring non-None values
            for field, value in asdict(data).items():
                if field in ['sources', 'confidence_score']:
                    continue
                if value is not None and getattr(merged, field) is None:
                    setattr(merged, field, value)
        
        merged.sources = list(set(all_sources))
        merged.confidence_score = total_confidence / len(data_list) if data_list else 0
        merged.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")
        
        return merged
    
    def normalize_yacht_name(self, name: str) -> List[str]:
        """Generate variations of yacht name for better matching"""
        variations = [name.strip()]
        
        # Remove common prefixes/suffixes
        cleaned = re.sub(r'^(M/Y|S/Y|MY|SY)\s+', '', name, flags=re.IGNORECASE)
        if cleaned != name:
            variations.append(cleaned)
        
        # Add quoted version
        variations.append(f'"{name}"')
        
        return list(set(variations))

# Global enhancer instance
_enhancer = None

def get_enhancer():
    """Get or create the global enhancer instance"""
    global _enhancer
    if _enhancer is None:
        _enhancer = YachtDataEnhancer()
    return _enhancer

async def enhance_yacht_data_async(yacht_name: str) -> Dict[str, Any]:
    """
    Async function to enhance yacht data from multiple sources
    
    Args:
        yacht_name: Name of the yacht to search for
        
    Returns:
        Dictionary containing enhanced yacht data
    """
    enhancer = get_enhancer()
    
    # Get name variations for better search results
    name_variations = enhancer.normalize_yacht_name(yacht_name)
    
    all_results = []
    for name_var in name_variations:
        results = await enhancer.search_all_sources(name_var)
        all_results.extend(results)
    
    # Merge all results
    merged_data = enhancer.merge_yacht_data(all_results)
    
    return asdict(merged_data)

def enhance_yacht_data(yacht_name: str) -> Dict[str, Any]:
    """
    Main function to enhance yacht data - USE THIS IN YOUR STREAMLIT APP
    
    Args:
        yacht_name: Name of the yacht to search for
        
    Returns:
        Dictionary containing enhanced yacht data with fields:
        - name, imo, mmsi, length, beam, year_built, builder, designer, etc.
        - sources: List of sources that provided data
        - confidence_score: Overall confidence in the data (0-1)
        - last_updated: Timestamp of when data was retrieved
    
    Example usage in your Streamlit app:
        enhanced_data = enhance_yacht_data("Eclipse")
        st.write(f"Length: {enhanced_data['length']}m")
        st.write(f"Built: {enhanced_data['year_built']}")
        st.write(f"Sources: {', '.join(enhanced_data['sources'])}")
    """
    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(enhance_yacht_data_async(yacht_name))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error enhancing data for {yacht_name}: {e}")
        return asdict(YachtData(name=yacht_name, sources=["error"], confidence_score=0.0))

def enhance_yacht_data_batch(yacht_names: List[str], progress_callback=None) -> List[Dict[str, Any]]:
    """
    Enhance data for multiple yachts efficiently
    
    Args:
        yacht_names: List of yacht names to enhance
        progress_callback: Optional callback function for progress updates
        
    Returns:
        List of enhanced yacht data dictionaries
    """
    results = []
    total = len(yacht_names)
    
    for i, yacht_name in enumerate(yacht_names):
        if progress_callback:
            progress_callback(i + 1, total, yacht_name)
        
        enhanced_data = enhance_yacht_data(yacht_name)
        results.append(enhanced_data)
        
        # Small delay to be respectful to servers
        time.sleep(0.5)
    
    return results

# Streamlit demo component (optional - for testing)
def demo_streamlit_integration():
    """Demo function showing how to integrate with Streamlit"""
    st.title("Yacht Data Enhancement Demo")
    
    yacht_name = st.text_input("Enter yacht name:", "Eclipse")
    
    if st.button("Enhance Data"):
        with st.spinner(f"Searching for {yacht_name}..."):
            enhanced_data = enhance_yacht_data(yacht_name)
        
        st.subheader("Enhanced Data")
        
        # Display key information
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Name", enhanced_data.get('name', 'N/A'))
            st.metric("Length (m)", enhanced_data.get('length', 'N/A'))
            st.metric("Year Built", enhanced_data.get('year_built', 'N/A'))
            st.metric("Builder", enhanced_data.get('builder', 'N/A'))
        
        with col2:
            st.metric("IMO", enhanced_data.get('imo', 'N/A'))
            st.metric("MMSI", enhanced_data.get('mmsi', 'N/A'))
            st.metric("Beam (m)", enhanced_data.get('beam', 'N/A'))
            st.metric("Confidence", f"{enhanced_data.get('confidence_score', 0):.2f}")
        
        # Show sources
        if enhanced_data.get('sources'):
            st.subheader("Data Sources")
            for source in enhanced_data['sources']:
                st.badge(source)
        
        # Show raw data
        with st.expander("Raw Data"):
            st.json(enhanced_data)

if __name__ == "__main__":
    # Run demo if executed directly
    demo_streamlit_integration()
