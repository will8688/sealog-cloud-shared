"""
Ships Logbook Schema Definitions
Based on IMO, IHO S-421, IALA, and international maritime standards

This module defines standardized schemas for various ship logbook types
to ensure compliance and data portability between systems.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json

class LogbookType(Enum):
    """Standard logbook types as per IMO requirements"""
    NAVIGATION = "navigation"      # Free - Bridge/Deck logbook
    ENGINE = "engine"             # Premium - Engine room logbook  
    RADIO = "radio"               # Premium - Radio communications logbook
    CARGO = "cargo"               # Future - Cargo operations
    SECURITY = "security"         # Future - Ship security logbook

class WeatherCondition(Enum):
    """Standard weather condition codes (WMO)"""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    MIST = "mist"
    RAIN = "rain"
    DRIZZLE = "drizzle"
    SNOW = "snow"
    STORM = "storm"
    SQUALL = "squall"

class SeaState(Enum):
    """Douglas Sea State Scale (0-9)"""
    CALM = 0          # Calm (glassy)
    CALM_RIPPLES = 1  # Calm (rippled)
    SMOOTH = 2        # Smooth (wavelets)
    SLIGHT = 3        # Slight
    MODERATE = 4      # Moderate
    ROUGH = 5         # Rough
    VERY_ROUGH = 6    # Very rough
    HIGH = 7          # High
    VERY_HIGH = 8     # Very high
    PHENOMENAL = 9    # Phenomenal

class VisibilityScale(Enum):
    """Standard visibility scale (nautical miles)"""
    EXCELLENT = "10+"     # >10nm
    GOOD = "5-10"        # 5-10nm
    MODERATE = "2-5"     # 2-5nm
    POOR = "0.5-2"       # 0.5-2nm
    FOG = "<0.5"         # <0.5nm

class WindScale(Enum):
    """Beaufort Wind Scale"""
    CALM = 0           # <1 knot
    LIGHT_AIR = 1      # 1-3 knots
    LIGHT_BREEZE = 2   # 4-6 knots
    GENTLE_BREEZE = 3  # 7-10 knots
    MODERATE_BREEZE = 4 # 11-16 knots
    FRESH_BREEZE = 5   # 17-21 knots
    STRONG_BREEZE = 6  # 22-27 knots
    NEAR_GALE = 7      # 28-33 knots
    GALE = 8           # 34-40 knots
    STRONG_GALE = 9    # 41-47 knots
    STORM = 10         # 48-55 knots
    VIOLENT_STORM = 11 # 56-63 knots
    HURRICANE = 12     # 64+ knots

# ============================================================================
# RADIO AND COMMUNICATION CONSTANTS
# ============================================================================

# Radio operator certificates and licenses
RADIO_CERTIFICATES = [
    "GOC",                                    # General Operator's Certificate (UK)
    "LRC",                                    # Long Range Certificate (UK)
    "SRC",                                    # Short Range Certificate (UK)
    "VHF DSC",                               # VHF DSC Certificate
    "GMDSS GOC",                             # GMDSS General Operator's Certificate
    "GMDSS ROC",                             # GMDSS Restricted Operator's Certificate
    "Marine Radio Operator Permit",          # US license
    "Restricted Radiotelephone Operator Permit", # US basic license
    "STCW Radio",                            # STCW radio requirements
    "Commercial Radio Operator License",      # Various countries
    "Amateur Radio License",                  # Ham radio
    "Aeronautical Radio Operator License",   # Aviation radio
    "Ship Radio Station License",            # Station license
    "Coastal Radio Station License",         # Shore station
    "Radio Electronics Certificate",         # Technical certificate
    "Radar Observer Certificate",            # Radar endorsement
    "ARPA Certificate",                      # Automatic Radar Plotting Aid
    "Electronic Chart Display Certificate",  # ECDIS
    "Satellite Communication Certificate",   # SATCOM
    "Digital Selective Calling Certificate", # DSC
    "Search and Rescue Transponder",        # SART
    "Emergency Position Indicating Beacon",  # EPIRB
    "Other"
]

# Communication methods for radio log
COMMUNICATION_METHODS = [
    "VHF",                    # VHF Radio (156-174 MHz)
    "UHF",                    # UHF Radio (300-3000 MHz)
    "HF",                     # High Frequency (3-30 MHz)
    "MF",                     # Medium Frequency (300-3000 kHz)
    "LF",                     # Low Frequency (30-300 kHz)
    "SSB",                    # Single Sideband
    "DSC",                    # Digital Selective Calling
    "Satellite",              # Satellite communication
    "Inmarsat",              # Inmarsat satellite
    "Iridium",               # Iridium satellite
    "VSAT",                  # Very Small Aperture Terminal
    "Cellular",              # Cellular/mobile phone
    "Internet",              # Internet-based communication
    "Email",                 # Email
    "Telex",                 # Telex (legacy)
    "Fax",                   # Facsimile
    "NAVTEX",                # Navigational telex
    "Weather Fax",           # Weather facsimile
    "AIS",                   # Automatic Identification System
    "SART",                  # Search and Rescue Transponder
    "EPIRB",                 # Emergency Position Indicating Beacon
    "PLB",                   # Personal Locator Beacon
    "Flare",                 # Pyrotechnic signals
    "Flag",                  # Flag signals
    "Light",                 # Light signals
    "Sound",                 # Sound signals (horn, whistle)
    "Other"
]

# Message types for radio communications
MESSAGE_TYPES = [
    "Routine",               # Normal operational messages
    "Safety",                # Safety-related messages
    "Urgency",               # Urgent but not distress
    "Distress",              # Emergency/distress calls
    "Position Report",       # Position reporting
    "Weather Report",        # Weather information
    "Traffic List",          # Message traffic list
    "Medical",               # Medical advice/assistance
    "Navigation Warning",    # Navigation warnings
    "Weather Warning",       # Weather warnings
    "Port Operations",       # Port/harbor operations
    "Pilot Service",         # Pilot boat communications
    "Customs/Immigration",   # Customs and immigration
    "Ship Business",         # Commercial ship business
    "Crew Welfare",          # Crew personal communications
    "Technical",             # Technical/engineering
    "Administrative",        # Administrative messages
    "Training",              # Training exercises
    "Test",                  # Equipment testing
    "Other"
]

# Common radio frequencies
COMMON_RADIO_FREQUENCIES = [
    # VHF Marine frequencies
    "156.800",    # Channel 16 (Distress/Safety/Calling)
    "156.650",    # Channel 13 (Navigation safety)
    "156.300",    # Channel 06
    "156.400",    # Channel 08
    "156.450",    # Channel 09
    "156.500",    # Channel 10
    "156.600",    # Channel 12
    "156.700",    # Channel 14
    "157.100",    # Channel 22
    
    # HF Marine frequencies
    "4125.0",     # HF Distress
    "6215.0",     # HF Distress
    "8291.0",     # HF Distress
    "12290.0",    # HF Distress
    "16420.0",    # HF Distress
    
    # Common working frequencies
    "2182.0",     # MF Distress
    "121.5",      # Aeronautical emergency
    "406.0",      # EPIRB/COSPAS-SARSAT
    
    "Custom"      # For manual entry
]

# Equipment status options
EQUIPMENT_STATUS_OPTIONS = [
    "Operational",
    "Testing",
    "Maintenance",
    "Defective", 
    "Not Available",
    "Backup in Use",
    "Calibration Required",
    "Service Due",
    "Out of Service"
]

# Navigation equipment types
NAVIGATION_EQUIPMENT = [
    "GPS/GNSS",
    "DGPS",
    "Radar",
    "ARPA",
    "AIS Transponder",
    "AIS Receiver",
    "ECDIS",
    "Chart Plotter",
    "Magnetic Compass",
    "Gyro Compass",
    "Fluxgate Compass",
    "Autopilot",
    "Wind Instruments",
    "Speed Log",
    "Depth Sounder",
    "Fish Finder",
    "Weather Router",
    "Barometer",
    "Thermometer",
    "Anemometer",
    "Weather Station",
    "Satellite Weather",
    "NAVTEX",
    "Weather Fax",
    "Electronic Bearing Line",
    "Pelorus",
    "Sextant",
    "Chronometer",
    "Rate Gyro",
    "Doppler Log",
    "Other"
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_radio_certificates():
    """Get list of radio certificates"""
    return RADIO_CERTIFICATES

def get_communication_methods():
    """Get list of communication methods"""
    return COMMUNICATION_METHODS

def get_message_types():
    """Get list of message types"""
    return MESSAGE_TYPES

def get_common_frequencies():
    """Get list of common radio frequencies"""
    return COMMON_RADIO_FREQUENCIES

def get_equipment_status_options():
    """Get list of equipment status options"""
    return EQUIPMENT_STATUS_OPTIONS

def get_navigation_equipment():
    """Get list of navigation equipment"""
    return NAVIGATION_EQUIPMENT

def format_frequency(frequency, band_type="VHF"):
    """Format frequency display with band information"""
    if band_type == "VHF":
        return f"{frequency} MHz (VHF Ch {get_vhf_channel(frequency)})"
    elif band_type == "HF":
        return f"{frequency} kHz (HF)"
    elif band_type == "MF":
        return f"{frequency} kHz (MF)"
    else:
        return f"{frequency} MHz"

def get_vhf_channel(frequency):
    """Get VHF channel number from frequency"""
    freq_to_channel = {
        "156.050": "01", "156.100": "02", "156.150": "03", "156.200": "04",
        "156.250": "05", "156.300": "06", "156.350": "07", "156.400": "08",
        "156.450": "09", "156.500": "10", "156.550": "11", "156.600": "12",
        "156.650": "13", "156.700": "14", "156.750": "15", "156.800": "16",
        "156.850": "17", "156.900": "18", "156.950": "19", "157.000": "20",
        "157.050": "21", "157.100": "22", "157.150": "23", "157.200": "24",
        "157.250": "25", "157.300": "26", "157.350": "27", "157.400": "28"
    }
    return freq_to_channel.get(frequency, "")

def is_distress_frequency(frequency):
    """Check if frequency is a distress/emergency frequency"""
    distress_frequencies = {
        "156.800",  # VHF Ch 16
        "2182.0",   # MF Distress
        "4125.0",   # HF Distress
        "6215.0",   # HF Distress
        "8291.0",   # HF Distress
        "12290.0",  # HF Distress
        "16420.0",  # HF Distress
        "121.5",    # Aeronautical emergency
        "243.0",    # Military emergency
        "406.0"     # EPIRB
    }
    return frequency in distress_frequencies

# ============================================================================
# BASE LOGBOOK ENTRY SCHEMA
# ============================================================================

class BaseLogbookEntry:
    """Base schema for all logbook entries (IMO compliance)"""
    
    def __init__(self):
        # Mandatory fields (IMO requirement)
        self.entry_id = None
        self.logbook_type = LogbookType.NAVIGATION
        self.date_time_utc = None
        self.vessel_name = None
        self.vessel_imo_number = None
        self.watch_officer = None
        self.entry_text = None
        
        # Optional metadata
        self.created_by = None
        self.created_date = None
        self.modified_date = None
        self.signed_by = None
        self.signature_date = None

    def to_dict(self):
        """Convert to dictionary for JSON export"""
        return {
            'entry_id': self.entry_id,
            'logbook_type': self.logbook_type.value if self.logbook_type else None,
            'date_time_utc': self.date_time_utc.isoformat() if self.date_time_utc else None,
            'vessel_name': self.vessel_name,
            'vessel_imo_number': self.vessel_imo_number,
            'watch_officer': self.watch_officer,
            'entry_text': self.entry_text,
            'created_by': self.created_by,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'signed_by': self.signed_by,
            'signature_date': self.signature_date.isoformat() if self.signature_date else None
        }

# ============================================================================
# NAVIGATION LOGBOOK SCHEMA (FREE)
# ============================================================================

class NavigationLogbookEntry(BaseLogbookEntry):
    """Navigation/Bridge logbook entry schema (IMO Official Logbook)"""
    
    def __init__(self):
        super().__init__()
        self.logbook_type = LogbookType.NAVIGATION
        
        # Position and navigation (IMO mandatory)
        self.latitude = None
        self.longitude = None
        self.course_over_ground = None  # degrees (0-360)
        self.speed_over_ground = None   # knots
        self.course_through_water = None
        self.speed_through_water = None
        
        # Weather conditions (IMO required)
        self.wind_direction = None        # degrees (0-360)
        self.wind_force = None      # Beaufort scale
        self.weather_condition = None
        self.visibility = None
        self.sea_state = None
        self.barometric_pressure = None # millibars
        self.air_temperature = None     # Celsius
        self.water_temperature = None   # Celsius
        
        # Navigation equipment status
        self.gps_status = None
        self.radar_status = None
        self.autopilot_status = None
        self.compass_variation = None   # degrees
        
        # Port operations
        self.port_name = None
        self.berth_number = None
        self.pilot_aboard = None
        self.tug_assistance = None
        
        # Cargo/passenger information
        self.cargo_operations = None
        self.passengers_embarked = None
        self.passengers_disembarked = None
        
        # Safety and incidents
        self.safety_equipment_checks = None
        self.incidents_accidents = None
        self.pollution_incidents = None

    def to_dict(self):
        base_dict = super().to_dict()
        navigation_dict = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'course_over_ground': self.course_over_ground,
            'speed_over_ground': self.speed_over_ground,
            'course_through_water': self.course_through_water,
            'speed_through_water': self.speed_through_water,
            'wind_direction': self.wind_direction,
            'wind_force': self.wind_force.value if self.wind_force else None,
            'weather_condition': self.weather_condition.value if self.weather_condition else None,
            'visibility': self.visibility.value if self.visibility else None,
            'sea_state': self.sea_state.value if self.sea_state else None,
            'barometric_pressure': self.barometric_pressure,
            'air_temperature': self.air_temperature,
            'water_temperature': self.water_temperature,
            'gps_status': self.gps_status,
            'radar_status': self.radar_status,
            'autopilot_status': self.autopilot_status,
            'compass_variation': self.compass_variation,
            'port_name': self.port_name,
            'berth_number': self.berth_number,
            'pilot_aboard': self.pilot_aboard,
            'tug_assistance': self.tug_assistance,
            'cargo_operations': self.cargo_operations,
            'passengers_embarked': self.passengers_embarked,
            'passengers_disembarked': self.passengers_disembarked,
            'safety_equipment_checks': self.safety_equipment_checks,
            'incidents_accidents': self.incidents_accidents,
            'pollution_incidents': self.pollution_incidents
        }
        return {**base_dict, **navigation_dict}

# ============================================================================
# ENGINE ROOM LOGBOOK SCHEMA (PREMIUM)
# ============================================================================

class EngineLogbookEntry(BaseLogbookEntry):
    """Engine room logbook entry schema"""
    
    def __init__(self):
        super().__init__()
        self.logbook_type = LogbookType.ENGINE
        
        # Main engine data
        self.main_engine_hours = None
        self.main_engine_rpm = None
        self.main_engine_load = None      # percentage
        self.fuel_consumption_rate = None # liters/hour
        self.fuel_remaining = None        # liters
        
        # Engine temperatures and pressures
        self.coolant_temperature = None   # Celsius
        self.oil_pressure = None          # bar
        self.oil_temperature = None       # Celsius
        self.exhaust_temperature = None   # Celsius
        self.turbo_pressure = None        # bar
        
        # Generator information
        self.generator_1_hours = None
        self.generator_2_hours = None
        self.generator_load = None        # kW
        self.shore_power = None
        
        # Fuel and fluids
        self.fuel_transferred = None      # liters
        self.water_produced = None        # liters
        self.waste_oil_transferred = None # liters
        self.bilge_pumped = None          # liters
        
        # Maintenance and inspections
        self.maintenance_performed = None
        self.parts_replaced = None
        self.next_service_due = None
        self.equipment_defects = None
        
        # Environmental compliance
        self.oily_water_separator_operation = None
        self.marpol_compliance = None

    def to_dict(self):
        base_dict = super().to_dict()
        engine_dict = {
            'main_engine_hours': self.main_engine_hours,
            'main_engine_rpm': self.main_engine_rpm,
            'main_engine_load': self.main_engine_load,
            'fuel_consumption_rate': self.fuel_consumption_rate,
            'fuel_remaining': self.fuel_remaining,
            'coolant_temperature': self.coolant_temperature,
            'oil_pressure': self.oil_pressure,
            'oil_temperature': self.oil_temperature,
            'exhaust_temperature': self.exhaust_temperature,
            'turbo_pressure': self.turbo_pressure,
            'generator_1_hours': self.generator_1_hours,
            'generator_2_hours': self.generator_2_hours,
            'generator_load': self.generator_load,
            'shore_power': self.shore_power,
            'fuel_transferred': self.fuel_transferred,
            'water_produced': self.water_produced,
            'waste_oil_transferred': self.waste_oil_transferred,
            'bilge_pumped': self.bilge_pumped,
            'maintenance_performed': self.maintenance_performed,
            'parts_replaced': self.parts_replaced,
            'next_service_due': self.next_service_due,
            'equipment_defects': self.equipment_defects,
            'oily_water_separator_operation': self.oily_water_separator_operation,
            'marpol_compliance': self.marpol_compliance
        }
        return {**base_dict, **engine_dict}

# ============================================================================
# RADIO LOGBOOK SCHEMA (PREMIUM)
# ============================================================================

class RadioLogbookEntry(BaseLogbookEntry):
    """Radio communications logbook entry schema"""
    
    def __init__(self):
        super().__init__()
        self.logbook_type = LogbookType.RADIO
        
        # Communication details
        self.frequency = None               # MHz/kHz
        self.call_sign_from = None
        self.call_sign_to = None
        self.message_type = None            # Routine, Urgency, Safety, Distress
        self.communication_method = None    # VHF, HF, MF, Satellite
        
        # Message content
        self.message_content = None
        self.acknowledgment_received = None
        self.transmission_quality = None    # Excellent, Good, Fair, Poor
        
        # Position reports
        self.position_report_sent = None
        self.position_latitude = None
        self.position_longitude = None
        
        # Safety and distress
        self.distress_call = None
        self.safety_message = None
        self.urgency_message = None
        self.medical_advice = None
        
        # Equipment status
        self.radio_equipment_status = None
        self.antenna_status = None
        self.battery_status = None
        self.gmdss_equipment_check = None
        
        # Regulatory compliance
        self.watch_schedule = None
        self.license_verification = None

    def to_dict(self):
        base_dict = super().to_dict()
        radio_dict = {
            'frequency': self.frequency,
            'call_sign_from': self.call_sign_from,
            'call_sign_to': self.call_sign_to,
            'message_type': self.message_type,
            'communication_method': self.communication_method,
            'message_content': self.message_content,
            'acknowledgment_received': self.acknowledgment_received,
            'transmission_quality': self.transmission_quality,
            'position_report_sent': self.position_report_sent,
            'position_latitude': self.position_latitude,
            'position_longitude': self.position_longitude,
            'distress_call': self.distress_call,
            'safety_message': self.safety_message,
            'urgency_message': self.urgency_message,
            'medical_advice': self.medical_advice,
            'radio_equipment_status': self.radio_equipment_status,
            'antenna_status': self.antenna_status,
            'battery_status': self.battery_status,
            'gmdss_equipment_check': self.gmdss_equipment_check,
            'watch_schedule': self.watch_schedule,
            'license_verification': self.license_verification
        }
        return {**base_dict, **radio_dict}

# ============================================================================
# SCHEMA VALIDATION AND EXPORT FUNCTIONS
# ============================================================================

def validate_entry(entry):
    """Validate logbook entry against schema requirements"""
    errors = []
    
    # Check mandatory fields
    if not entry.date_time_utc:
        errors.append("Date/Time UTC is required")
    if not entry.vessel_name:
        errors.append("Vessel name is required")
    if not entry.watch_officer:
        errors.append("Watch officer is required")
    if not entry.entry_text:
        errors.append("Entry text is required")
    
    # Type-specific validation
    if isinstance(entry, NavigationLogbookEntry):
        if entry.latitude is not None and not (-90 <= entry.latitude <= 90):
            errors.append("Latitude must be between -90 and 90 degrees")
        if entry.longitude is not None and not (-180 <= entry.longitude <= 180):
            errors.append("Longitude must be between -180 and 180 degrees")
        if entry.course_over_ground is not None and not (0 <= entry.course_over_ground <= 360):
            errors.append("Course must be between 0 and 360 degrees")
    
    return len(errors) == 0, errors

def export_to_json(entries, include_metadata=True):
    """Export logbook entries to JSON format"""
    export_data = {
        'format': 'Ships_Logbook_Export_v1.0',
        'export_date': datetime.now().isoformat(),
        'standards_compliance': [
            'IMO_Official_Logbook',
            'IHO_S421',
            'IALA_Guidelines',
            'ISO_8601_DateTime'
        ],
        'entries': [entry.to_dict() for entry in entries]
    }
    
    if include_metadata:
        export_data['metadata'] = {
            'total_entries': len(entries),
            'logbook_types': list(set(entry.logbook_type.value for entry in entries)),
            'date_range': {
                'start': min(entry.date_time_utc for entry in entries if entry.date_time_utc).isoformat() if entries else None,
                'end': max(entry.date_time_utc for entry in entries if entry.date_time_utc).isoformat() if entries else None
            }
        }
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def export_to_csv(entries, logbook_type):
    """Export logbook entries to CSV format for specific logbook type"""
    import csv
    import io
    
    output = io.StringIO()
    
    if logbook_type == LogbookType.NAVIGATION:
        fieldnames = [
            'date_time_utc', 'vessel_name', 'watch_officer', 'latitude', 'longitude',
            'course_over_ground', 'speed_over_ground', 'wind_direction', 'wind_force',
            'weather_condition', 'visibility', 'sea_state', 'entry_text'
        ]
    elif logbook_type == LogbookType.ENGINE:
        fieldnames = [
            'date_time_utc', 'vessel_name', 'watch_officer', 'main_engine_hours',
            'fuel_consumption_rate', 'fuel_remaining', 'oil_pressure', 'oil_temperature',
            'maintenance_performed', 'entry_text'
        ]
    elif logbook_type == LogbookType.RADIO:
        fieldnames = [
            'date_time_utc', 'vessel_name', 'watch_officer', 'frequency', 'call_sign_from',
            'call_sign_to', 'message_type', 'message_content', 'entry_text'
        ]
    else:
        fieldnames = ['date_time_utc', 'vessel_name', 'watch_officer', 'entry_text']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for entry in entries:
        if entry.logbook_type == logbook_type:
            entry_dict = entry.to_dict()
            # Only include fields that are in fieldnames
            filtered_dict = {k: v for k, v in entry_dict.items() if k in fieldnames}
            writer.writerow(filtered_dict)
    
    return output.getvalue()

# ============================================================================
# SCHEMA FACTORY
# ============================================================================

def create_logbook_entry(logbook_type):
    """Factory function to create appropriate logbook entry"""
    if logbook_type == LogbookType.NAVIGATION:
        return NavigationLogbookEntry()
    elif logbook_type == LogbookType.ENGINE:
        return EngineLogbookEntry()
    elif logbook_type == LogbookType.RADIO:
        return RadioLogbookEntry()
    else:
        return BaseLogbookEntry()

# Schema version for compatibility tracking
SCHEMA_VERSION = "1.0.0"
SUPPORTED_STANDARDS = [
    "IMO Official Logbook Requirements",
    "IHO S-421 Digital Logbook Standard", 
    "IALA Digital Navigation Guidelines",
    "ISO 8601 Date/Time Format",
    "WMO Weather Codes",
    "Douglas Sea State Scale",
    "Beaufort Wind Scale"
]