"""
Comprehensive Vessel/Yacht Schema
Compliant with IMO, Schema.org, and industry standards

This module defines standardized schemas for vessels including yachts,
commercial vessels, and recreational boats to ensure compliance and
data portability between maritime systems.

Standards Compliance:
- IMO (International Maritime Organization)
- Schema.org Boat/Vehicle types
- BOAT International superyacht standards
- IIMS (International Institute of Marine Surveying)
- Lloyd's Register classifications
- ABS (American Bureau of Shipping)
- DNV GL classifications
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, Dict, Any, List
import json

# ============================================================================
# VESSEL CLASSIFICATION ENUMS (IMO/International Standards)
# ============================================================================

class VesselType(Enum):
    """IMO vessel type classifications"""
    # Commercial vessels
    CARGO_SHIP = "cargo_ship"
    CONTAINER_SHIP = "container_ship"
    BULK_CARRIER = "bulk_carrier"
    TANKER = "tanker"
    CHEMICAL_TANKER = "chemical_tanker"
    LPG_TANKER = "lpg_tanker"
    LNG_TANKER = "lng_tanker"
    PASSENGER_SHIP = "passenger_ship"
    CRUISE_SHIP = "cruise_ship"
    FERRY = "ferry"
    RO_RO_SHIP = "ro_ro_ship"
    
    # Specialized vessels
    FISHING_VESSEL = "fishing_vessel"
    RESEARCH_VESSEL = "research_vessel"
    OFFSHORE_VESSEL = "offshore_vessel"
    SUPPLY_VESSEL = "supply_vessel"
    TUG_BOAT = "tug_boat"
    PILOT_VESSEL = "pilot_vessel"
    
    # Recreational vessels
    YACHT = "yacht"
    MOTOR_YACHT = "motor_yacht"
    SAILING_YACHT = "sailing_yacht"
    SUPERYACHT = "superyacht"
    MEGAYACHT = "megayacht"
    CATAMARAN = "catamaran"
    TRIMARAN = "trimaran"
    
    # Military vessels
    NAVAL_VESSEL = "naval_vessel"
    COAST_GUARD = "coast_guard"
    
    # Other
    OTHER = "other"

class YachtCategory(Enum):
    """Yacht-specific categories (BOAT International standards)"""
    MOTOR_YACHT = "motor_yacht"           # Power-driven yachts
    SAILING_YACHT = "sailing_yacht"       # Wind-powered yachts
    EXPEDITION_YACHT = "expedition_yacht" # Long-range exploration
    CLASSIC_YACHT = "classic_yacht"       # Vintage/heritage yachts
    SPORT_YACHT = "sport_yacht"          # High-performance yachts
    EXPLORER_YACHT = "explorer_yacht"     # Ice-class/extreme conditions
    HYBRID_YACHT = "hybrid_yacht"        # Hybrid propulsion
    ECO_YACHT = "eco_yacht"              # Environmentally focused

class HullMaterial(Enum):
    """Hull construction materials"""
    STEEL = "steel"
    ALUMINUM = "aluminum"
    FIBERGLASS = "fiberglass"
    CARBON_FIBER = "carbon_fiber"
    WOOD = "wood"
    COMPOSITE = "composite"
    CONCRETE = "concrete"
    PLASTIC = "plastic"

class PropulsionType(Enum):
    """Propulsion system types"""
    DIESEL = "diesel"
    PETROL = "petrol"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    SAIL = "sail"
    NUCLEAR = "nuclear"
    GAS_TURBINE = "gas_turbine"
    STEAM = "steam"
    FUEL_CELL = "fuel_cell"

class ClassificationSociety(Enum):
    """Major classification societies"""
    LLOYDS_REGISTER = "lr"               # Lloyd's Register
    ABS = "abs"                          # American Bureau of Shipping
    DNV_GL = "dnv_gl"                   # DNV GL
    BV = "bv"                           # Bureau Veritas
    RINA = "rina"                       # RINA
    CCS = "ccs"                         # China Classification Society
    NK = "nk"                           # Nippon Kaiji Kyokai
    RS = "rs"                           # Russian Maritime Register
    KR = "kr"                           # Korean Register

class BuildStandard(Enum):
    """Construction standards and regulations"""
    MCA_LY3 = "mca_ly3"                # MCA Large Yacht Code LY3
    MCA_LY2 = "mca_ly2"                # MCA Large Yacht Code LY2
    CE_MARKING = "ce_marking"          # European Conformity
    USCG = "uscg"                      # US Coast Guard
    ABYC = "abyc"                      # American Boat & Yacht Council
    ISO_12215 = "iso_12215"            # ISO Hull construction
    SOLAS = "solas"                    # Safety of Life at Sea
    MARPOL = "marpol"                  # Marine pollution prevention

# ============================================================================
# COMPREHENSIVE REFERENCE DATA LISTS
# ============================================================================

# Complete list of flag states (maritime nations and territories)
FLAG_STATES = [
    # Major maritime nations
    "United Kingdom", "United States", "Canada", "Australia", "New Zealand",
    "Ireland", "Netherlands", "Germany", "France", "Spain", "Italy", 
    "Norway", "Denmark", "Sweden", "Finland", "Belgium", "Greece", 
    "Cyprus", "Malta", "Portugal", "Croatia", "Slovenia", "Poland",
    "Estonia", "Latvia", "Lithuania", "Luxembourg", "Austria", "Switzerland",
    "Monaco", "Liechtenstein", "Iceland", "Faroe Islands",
    
    # British territories and dependencies
    "Gibraltar", "Isle of Man", "Jersey", "Guernsey", "Bermuda",
    "Cayman Islands", "British Virgin Islands", "Turks and Caicos",
    "Anguilla", "Montserrat", "Falkland Islands", "South Georgia",
    "British Indian Ocean Territory",
    
    # Caribbean nations
    "Bahamas", "Barbados", "Antigua and Barbuda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Grenada",
    "Trinidad and Tobago", "Jamaica", "Dominican Republic", "Haiti", "Cuba",
    "Puerto Rico", "US Virgin Islands", "Martinique", "Guadeloupe",
    "Saint Martin", "Sint Maarten", "Curacao", "Aruba", "Bonaire",
    
    # Central and South America
    "Belize", "Panama", "Costa Rica", "Nicaragua", "Honduras", "Guatemala",
    "Mexico", "Colombia", "Venezuela", "Guyana", "Suriname", "French Guiana",
    "Brazil", "Uruguay", "Argentina", "Chile", "Peru", "Ecuador", "Bolivia", "Paraguay",
    
    # Major flag of convenience states
    "Liberia", "Marshall Islands", "Vanuatu", "Cook Islands", "Tuvalu",
    "Kiribati", "Nauru", "Palau", "Tonga", "Samoa", "Fiji", "Solomon Islands",
    
    # Asia Pacific
    "Singapore", "Hong Kong", "Macau", "Japan", "South Korea", "North Korea",
    "Taiwan", "China", "Philippines", "Thailand", "Malaysia", "Indonesia",
    "Brunei", "Vietnam", "Cambodia", "Laos", "Myanmar", "Bangladesh",
    "Sri Lanka", "Maldives", "India", "Pakistan",
    
    # Pacific Islands
    "Papua New Guinea", "New Caledonia", "French Polynesia", "American Samoa",
    "Guam", "Northern Mariana Islands", "Federated States of Micronesia",
    "Wake Island", "Christmas Island", "Cocos Islands", "Norfolk Island",
    
    # Indian Ocean
    "Seychelles", "Mauritius", "Comoros", "Madagascar", "Reunion", "Mayotte",
    
    # Africa
    "South Africa", "Namibia", "Angola", "Democratic Republic of Congo",
    "Republic of Congo", "Gabon", "Equatorial Guinea", "Cameroon", "Nigeria",
    "Benin", "Togo", "Ghana", "Cote d'Ivoire", "Sierra Leone", "Guinea",
    "Guinea-Bissau", "Senegal", "Gambia", "Cape Verde", "Mauritania",
    "Morocco", "Western Sahara", "Algeria", "Tunisia", "Libya", "Egypt",
    "Sudan", "South Sudan", "Eritrea", "Ethiopia", "Djibouti", "Somalia",
    "Kenya", "Tanzania", "Mozambique", "Malawi", "Zambia", "Zimbabwe",
    "Botswana", "Swaziland", "Lesotho",
    
    # Middle East
    "Israel", "Palestine", "Jordan", "Syria", "Lebanon", "Turkey",
    "United Arab Emirates", "Qatar", "Bahrain", "Kuwait", "Saudi Arabia",
    "Oman", "Yemen", "Iraq", "Iran",
    
    # Eastern Europe and Former Soviet Union
    "Georgia", "Armenia", "Azerbaijan", "Ukraine", "Belarus", "Moldova",
    "Russia", "Kazakhstan", "Uzbekistan", "Turkmenistan", "Kyrgyzstan", "Tajikistan",
    
    # Balkans
    "Montenegro", "Albania", "North Macedonia", "Serbia", "Bosnia and Herzegovina",
    "Kosovo", "Bulgaria", "Romania",
    
    # Northern Europe/Arctic
    "Svalbard", "Jan Mayen", "Greenland",
    
    # Antarctica (special status)
    "Antarctica",
    
    # Other/Unspecified
    "Other"
]

# Commonly used flag states for quick selection
COMMON_FLAG_STATES = [
    "United Kingdom", "United States", "Canada", "Australia", "New Zealand",
    "Netherlands", "Germany", "France", "Italy", "Spain", "Norway", "Denmark",
    "Panama", "Marshall Islands", "Cayman Islands", "Malta", "Cyprus",
    "Singapore", "Hong Kong", "Other"
]

# Design categories with full descriptions
DESIGN_CATEGORIES = {
    "": "Not specified",
    "A": "Ocean - Winds exceeding Force 8 (Beaufort scale) and significant wave heights exceeding 4m",
    "B": "Offshore - Winds up to and including Force 8 and significant wave heights up to and including 4m", 
    "C": "Inshore - Winds up to and including Force 6 and significant wave heights up to and including 2m",
    "D": "Sheltered waters - Winds up to and including Force 4 and significant wave heights up to and including 0.5m"
}

# Short descriptions for dropdowns
DESIGN_CATEGORIES_SHORT = {
    "": "Not specified",
    "A": "Ocean (>Force 8, >4m seas)",
    "B": "Offshore (≤Force 8, ≤4m seas)", 
    "C": "Inshore (≤Force 6, ≤2m seas)",
    "D": "Sheltered (≤Force 4, ≤0.5m seas)"
}

# Major ports worldwide
MAJOR_PORTS = [
    # UK & Ireland
    "Portsmouth", "Southampton", "Plymouth", "Falmouth", "Cowes", "Brighton",
    "Dover", "Liverpool", "Hull", "Newcastle", "Bristol", "Cardiff", "Belfast",
    "Dublin", "Cork", "Galway",
    
    # Northern Europe  
    "Amsterdam", "Rotterdam", "Hamburg", "Copenhagen", "Stockholm", "Oslo",
    "Bergen", "Helsinki", "Tallinn", "Riga", "Gdansk",
    
    # Mediterranean
    "Barcelona", "Valencia", "Palma de Mallorca", "Monaco", "Nice", "Cannes",
    "Genoa", "Rome", "Naples", "Venice", "Dubrovnik", "Athens", "Istanbul",
    
    # Americas
    "New York", "Miami", "Fort Lauderdale", "Los Angeles", "San Francisco",
    "Seattle", "Vancouver", "Nassau", "George Town",
    
    # Asia Pacific
    "Singapore", "Hong Kong", "Tokyo", "Sydney", "Auckland",
    
    # Other
    "Other"
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_flag_states(use_common=False):
    """Get list of flag states
    
    Args:
        use_common: If True, return shortened list of common flag states
        
    Returns:
        List of flag state names
    """
    return COMMON_FLAG_STATES if use_common else FLAG_STATES

def get_design_categories():
    """Get list of design category codes"""
    return list(DESIGN_CATEGORIES.keys())

def get_design_category_description(category, short=False):
    """Get description for design category
    
    Args:
        category: Design category code (A, B, C, D)
        short: If True, return short description
        
    Returns:
        Category description
    """
    if short:
        return DESIGN_CATEGORIES_SHORT.get(category, "")
    return DESIGN_CATEGORIES.get(category, "")

def get_major_ports():
    """Get list of major world ports"""
    return MAJOR_PORTS

def get_flag_emoji(flag_state):
    """Get flag emoji for country"""
    flag_emojis = {
        "United Kingdom": "", "United States": "", "Canada": "",
        "Australia": "", "New Zealand": "", "Ireland": "",
        "Netherlands": "", "Germany": "", "France": "",
        "Spain": "", "Italy": "", "Norway": "",
        "Denmark": "", "Sweden": "", "Finland": "",
        "Belgium": "", "Greece": "", "Cyprus": "",
        "Malta": "", "Portugal": "", "Croatia": "",
        "Singapore": "", "Hong Kong": "", "Japan": "",
        "Panama": "", "Marshall Islands": "", "Cayman Islands": ""
    }
    return flag_emojis.get(flag_state, "")

def is_eu_flag_state(flag_state):
    """Check if flag state is in EU/EEA (for tax purposes)"""
    eu_eea_states = {
        "Germany", "France", "Italy", "Spain", "Netherlands", "Belgium",
        "Austria", "Portugal", "Greece", "Finland", "Ireland", "Luxembourg",
        "Slovenia", "Slovakia", "Estonia", "Latvia", "Lithuania", "Malta",
        "Cyprus", "Czech Republic", "Hungary", "Poland", "Bulgaria", "Romania",
        "Croatia", "Denmark", "Sweden", "Norway", "Iceland", "Liechtenstein"
    }
    return flag_state in eu_eea_states

def is_flag_of_convenience(flag_state):
    """Check if flag state is considered a flag of convenience"""
    foc_states = {
        "Panama", "Liberia", "Marshall Islands", "Bahamas", "Malta", "Cyprus",
        "Antigua and Barbuda", "Barbados", "Belize", "Bermuda", "Cayman Islands",
        "Cook Islands", "Curacao", "Gibraltar", "Honduras", "Jamaica", "Lebanon",
        "Moldova", "Mongolia", "Saint Kitts and Nevis", "Saint Vincent and the Grenadines",
        "Sierra Leone", "Tonga", "Vanuatu"
    }
    return flag_state in foc_states

# ============================================================================
# BASE VESSEL SCHEMA (IMO Compliant)
# ============================================================================

class BaseVessel:
    """Base vessel schema compliant with IMO and Schema.org standards"""
    
    def __init__(self):
        # IMO Required Identifiers
        self.vessel_name = None
        self.imo_number = None              # IMO unique identifier
        self.mmsi_number = None             # Maritime Mobile Service Identity
        self.call_sign = None               # Radio call sign
        self.official_number = None         # Flag state number
        
        # Basic Classification (IMO)
        self.vessel_type = None
        self.flag_state = None              # Country of registration
        self.port_of_registry = None
        self.classification_society = None
        self.class_notation = None          # Specific class notation
        
        # Physical Dimensions (IMO Required)
        self.length_overall = None        # LOA in meters
        self.length_waterline = None      # LWL in meters
        self.beam = None                  # Maximum width in meters
        self.draft = None                 # Maximum draft in meters
        self.depth = None                 # Depth to main deck
        self.air_draft = None             # Height above waterline
        self.gross_tonnage = None         # GT (IMO calculation)
        self.net_tonnage = None           # NT (IMO calculation)
        self.deadweight = None            # DWT in tonnes
        self.displacement = None          # Full load displacement
        
        # Construction Details
        self.year_built = None
        self.builder = None                 # Shipyard/manufacturer
        self.build_location = None          # Country/city
        self.hull_material = None
        self.hull_number = None             # Builder's hull number
        self.design_category = None         # CE category A,B,C,D
        
        # Standards and Certification
        self.build_standards = []     # Applicable standards
        self.survey_date = None            # Last survey
        self.certificate_expiry = None     # Safety certificate
        
        # Radio Log integration fields
        self.default_operator_name = None
        self.radio_certificate = None
        
        # Schema.org Vehicle properties
        self.manufacturer = None            # Same as builder
        self.model = None                   # Vessel model/series
        self.vehicle_identification_number = None  # Same as hull_number
        
        # Metadata
        self.created_date = None
        self.updated_date = None
        self.data_source = None             # Source of information

    def to_dict(self):
        """Convert to dictionary for JSON export (Schema.org compatible)"""
        return {
            '@type': 'Boat',  # Schema.org type
            'name': self.vessel_name,
            'identifier': [
                {'@type': 'PropertyValue', 'name': 'IMO', 'value': self.imo_number},
                {'@type': 'PropertyValue', 'name': 'MMSI', 'value': self.mmsi_number},
                {'@type': 'PropertyValue', 'name': 'CallSign', 'value': self.call_sign}
            ] if any([self.imo_number, self.mmsi_number, self.call_sign]) else None,
            
            # Basic properties
            'vessel_type': self.vessel_type.value if self.vessel_type else None,
            'flag_state': self.flag_state,
            'port_of_registry': self.port_of_registry,
            'classification_society': self.classification_society.value if self.classification_society else None,
            'class_notation': self.class_notation,
            
            # Dimensions
            'length_overall': self.length_overall,
            'length_waterline': self.length_waterline,
            'beam': self.beam,
            'draft': self.draft,
            'depth': self.depth,
            'air_draft': self.air_draft,
            'gross_tonnage': self.gross_tonnage,
            'net_tonnage': self.net_tonnage,
            'deadweight': self.deadweight,
            'displacement': self.displacement,
            
            # Construction
            'year_built': self.year_built,
            'manufacturer': self.builder,
            'model': self.model,
            'build_location': self.build_location,
            'hull_material': self.hull_material.value if self.hull_material else None,
            'hull_number': self.hull_number,
            'design_category': self.design_category,
            
            # Standards
            'build_standards': [std.value for std in self.build_standards],
            'survey_date': self.survey_date.isoformat() if self.survey_date else None,
            'certificate_expiry': self.certificate_expiry.isoformat() if self.certificate_expiry else None,
            
            # Radio integration
            'default_operator_name': self.default_operator_name,
            'radio_certificate': self.radio_certificate,
            
            # Metadata
            'dateCreated': self.created_date.isoformat() if self.created_date else None,
            'dateModified': self.updated_date.isoformat() if self.updated_date else None,
            'data_source': self.data_source
        }

# ============================================================================
# YACHT-SPECIFIC SCHEMA (Extends Base Vessel)
# ============================================================================

class YachtSchema(BaseVessel):
    """Extended schema for yachts (BOAT International compatible)"""
    
    def __init__(self):
        super().__init__()
        
        # Yacht-specific classification
        self.yacht_category = None
        self.superyacht_status = False               # >24m typically
        self.commercial_operation = False            # Charter operation
        
        # Enhanced dimensions for yachts
        self.length_deck = None           # Deck length
        self.beam_waterline = None        # Waterline beam
        self.freeboard = None             # Deck height above water
        self.bridge_clearance = None      # Bridge/mast height
        
        # Accommodation (yacht-specific)
        self.guest_cabins = None
        self.crew_cabins = None
        self.total_berths = None
        self.guest_capacity = None
        self.crew_capacity = None
        self.number_of_heads = None          # Bathrooms
        
        # Performance specifications
        self.max_speed = None             # Knots
        self.cruise_speed = None          # Knots
        self.range = None                 # Nautical miles (note: 'range' conflicts with Python builtin)
        self.fuel_capacity = None         # Liters
        self.water_capacity = None        # Liters
        
        # Propulsion system
        self.propulsion_type = None
        self.main_engines = None            # Engine make/model
        self.engine_power = None          # Total kW/HP
        self.number_of_engines = None
        self.propeller_type = None          # Fixed/folding/feathering
        self.bow_thruster = False
        self.stern_thruster = False
        
        # Sailing yacht specific
        self.sail_area = None             # Square meters
        self.mast_height = None           # Meters above deck
        self.keel_type = None               # Fin/full/wing/centerboard
        self.ballast_weight = None        # Kg
        
        # Luxury amenities (superyacht features)
        self.helicopter_pad = False
        self.swimming_pool = False
        self.beach_club = False
        self.gym = False
        self.spa = False
        self.wine_cellar = False
        self.elevator = False
        self.air_conditioning = False
        self.stabilizers = False
        
        # Technology and equipment
        self.satellite_communication = False
        self.wifi_coverage = None           # Coverage description
        self.entertainment_systems = None
        self.navigation_equipment = None
        
        # Charter and commercial operation
        self.charter_license = None         # MCA/USCG license
        self.charter_rate_high = None     # Weekly rate high season
        self.charter_rate_low = None      # Weekly rate low season
        self.charter_currency = None        # EUR/USD/GBP
        self.management_company = None
        
        # Ownership and brokerage
        self.owner_name = None              # If public
        self.brokerage_firm = None
        self.asking_price = None
        self.price_currency = None
        self.for_sale = False
        self.for_charter = False
        
        # Awards and recognition
        self.awards = []                        # Yacht awards/recognition
        self.design_awards = []                 # Design awards
        
        # Environmental features
        self.environmental_certification = None
        self.green_technologies = []            # Solar, hybrid, etc.
        
        # Interior and exterior design
        self.interior_designer = None
        self.exterior_designer = None
        self.naval_architect = None
        self.interior_style = None          # Contemporary, classic, etc.
        
        # Operational details
        self.home_port = None
        self.cruising_areas = []                # Preferred regions
        self.winter_location = None
        self.summer_location = None

    def to_dict(self):
        """Extended dictionary export for yacht-specific data"""
        base_dict = super().to_dict()
        
        yacht_dict = {
            '@type': 'Boat/Yacht',  # Extended Schema.org type
            'yacht_category': self.yacht_category.value if self.yacht_category else None,
            'superyacht_status': self.superyacht_status,
            'commercial_operation': self.commercial_operation,
            
            # Enhanced dimensions
            'length_deck': self.length_deck,
            'beam_waterline': self.beam_waterline,
            'freeboard': self.freeboard,
            'bridge_clearance': self.bridge_clearance,
            
            # Accommodation
            'guest_cabins': self.guest_cabins,
            'crew_cabins': self.crew_cabins,
            'total_berths': self.total_berths,
            'guest_capacity': self.guest_capacity,
            'crew_capacity': self.crew_capacity,
            'number_of_heads': self.number_of_heads,
            
            # Performance
            'max_speed': self.max_speed,
            'cruise_speed': self.cruise_speed,
            'range': self.range,
            'fuel_capacity': self.fuel_capacity,
            'water_capacity': self.water_capacity,
            
            # Propulsion
            'propulsion_type': self.propulsion_type.value if self.propulsion_type else None,
            'main_engines': self.main_engines,
            'engine_power': self.engine_power,
            'number_of_engines': self.number_of_engines,
            'propeller_type': self.propeller_type,
            'bow_thruster': self.bow_thruster,
            'stern_thruster': self.stern_thruster,
            
            # Sailing specific
            'sail_area': self.sail_area,
            'mast_height': self.mast_height,
            'keel_type': self.keel_type,
            'ballast_weight': self.ballast_weight,
            
            # Amenities
            'luxury_amenities': {
                'helicopter_pad': self.helicopter_pad,
                'swimming_pool': self.swimming_pool,
                'beach_club': self.beach_club,
                'gym': self.gym,
                'spa': self.spa,
                'wine_cellar': self.wine_cellar,
                'elevator': self.elevator,
                'air_conditioning': self.air_conditioning,
                'stabilizers': self.stabilizers
            },
            
            # Charter information
            'charter_information': {
                'charter_license': self.charter_license,
                'charter_rate_high': self.charter_rate_high,
                'charter_rate_low': self.charter_rate_low,
                'charter_currency': self.charter_currency,
                'for_charter': self.for_charter
            } if any([self.charter_license, self.charter_rate_high, self.for_charter]) else None,
            
            # Design team
            'design_team': {
                'interior_designer': self.interior_designer,
                'exterior_designer': self.exterior_designer,
                'naval_architect': self.naval_architect
            } if any([self.interior_designer, self.exterior_designer, self.naval_architect]) else None,
            
            # Operational
            'home_port': self.home_port,
            'cruising_areas': self.cruising_areas,
            'awards': self.awards,
            'green_technologies': self.green_technologies
        }
        
        return {**base_dict, **yacht_dict}

# ============================================================================
# SCHEMA VALIDATION AND UTILITIES
# ============================================================================

def validate_vessel_data(vessel):
    """Validate vessel data against schema requirements"""
    errors = []
    
    # Required fields validation
    if not vessel.vessel_name:
        errors.append("Vessel name is required")
    
    # IMO number validation (if provided)
    if vessel.imo_number:
        if not vessel.imo_number.isdigit() or len(vessel.imo_number) != 7:
            errors.append("IMO number must be 7 digits")
    
    # MMSI validation (if provided)
    if vessel.mmsi_number:
        if not vessel.mmsi_number.isdigit() or len(vessel.mmsi_number) != 9:
            errors.append("MMSI must be 9 digits")
    
    # Dimension validation
    if vessel.length_overall and vessel.length_overall <= 0:
        errors.append("Length overall must be positive")
    
    if vessel.beam and vessel.beam <= 0:
        errors.append("Beam must be positive")
    
    # Year validation
    if vessel.year_built:
        current_year = datetime.now().year
        if vessel.year_built < 1800 or vessel.year_built > current_year + 5:
            errors.append(f"Year built must be between 1800 and {current_year + 5}")
    
    return len(errors) == 0, errors

def export_vessel_to_json(vessel, include_schema_org=True):
    """Export vessel to JSON with optional Schema.org compliance"""
    vessel_dict = vessel.to_dict()
    
    if include_schema_org:
        vessel_dict['@context'] = 'https://schema.org'
    
    export_data = {
        'format': 'Vessel_Schema_v1.0',
        'export_date': datetime.now().isoformat(),
        'standards_compliance': [
            'IMO_Requirements',
            'Schema.org_Boat',
            'BOAT_International',
            'IIMS_Standards'
        ],
        'vessel': vessel_dict
    }
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def create_vessel_from_type(vessel_type):
    """Factory function to create appropriate vessel schema"""
    if vessel_type in [VesselType.YACHT, VesselType.MOTOR_YACHT, 
                      VesselType.SAILING_YACHT, VesselType.SUPERYACHT, 
                      VesselType.MEGAYACHT]:
        return YachtSchema()
    else:
        return BaseVessel()

# ============================================================================
# INTEGRATION UTILITIES
# ============================================================================

def import_from_boat_international(data):
    """Import yacht data from BOAT International format"""
    yacht = YachtSchema()
    
    # Map common fields (would need actual BOAT International API format)
    yacht.vessel_name = data.get('name')
    yacht.length_overall = data.get('length_m')
    yacht.year_built = data.get('year')
    yacht.builder = data.get('builder')
    
    return yacht

def import_from_schema_org(data):
    """Import vessel data from Schema.org format"""
    vessel = BaseVessel()
    
    vessel.vessel_name = data.get('name')
    vessel.manufacturer = data.get('manufacturer')
    vessel.model = data.get('model')
    
    # Handle identifier array
    if 'identifier' in data:
        for identifier in data['identifier']:
            if identifier.get('name') == 'IMO':
                vessel.imo_number = identifier.get('value')
            elif identifier.get('name') == 'MMSI':
                vessel.mmsi_number = identifier.get('value')
    
    return vessel

# Schema version for compatibility tracking
VESSEL_SCHEMA_VERSION = "1.0.0"
SUPPORTED_STANDARDS = [
    "IMO Ship Identification Requirements",
    "Schema.org Boat/Vehicle Types",
    "BOAT International Superyacht Database",
    "IIMS Marine Surveying Standards",
    "Lloyd's Register Classifications",
    "MCA Large Yacht Code (LY2/LY3)",
    "CE Recreational Craft Directive",
    "ABYC Standards",
    "ISO 12215 Hull Construction"
]