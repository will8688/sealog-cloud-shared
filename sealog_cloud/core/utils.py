import streamlit as st
from datetime import datetime

# Import database manager
from ..database_manager import db_manager

# Optional imports with fallbacks
try:
    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

# ============================================================================
# DATABASE INITIALIZATION (SHARED)
# ============================================================================

def init_database():
    """Initialize database with required tables using database manager"""
    try:
        # Users table
        users_schema = '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                payment_date DATETIME,
                payment_expiry DATETIME
            )
        '''
        db_manager.create_table_from_schema('users', users_schema)
        
        # Entries table (for crew logbook)
        entries_schema = '''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ship_name TEXT NOT NULL,
                ship_number TEXT,
                port_registry TEXT,
                gross_tonnage REAL,
                place_joining TEXT NOT NULL,
                date_joining DATE NOT NULL,
                place_leaving TEXT NOT NULL,
                date_leaving DATE NOT NULL,
                capacity TEXT NOT NULL,
                description TEXT,
                entry_type TEXT NOT NULL,
                sea_days INTEGER,
                sea_miles REAL,
                senior_email TEXT,
                verification_token TEXT,
                verified BOOLEAN DEFAULT FALSE,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        '''
        db_manager.create_table_from_schema('entries', entries_schema)
        
        # User sessions table for persistent login
        sessions_schema = '''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_token TEXT PRIMARY KEY,
                user_id INTEGER,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_date DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        '''
        db_manager.create_table_from_schema('user_sessions', sessions_schema)
        
        # Ships logbook table (placeholder for future)
        ship_logs_schema = '''
            CREATE TABLE IF NOT EXISTS ship_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ship_name TEXT NOT NULL,
                log_date DATE NOT NULL,
                log_type TEXT NOT NULL,
                entry_content TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        '''
        db_manager.create_table_from_schema('ship_logs', ship_logs_schema)
        
        # User profiles table (for profile tool)
        profiles_schema = '''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                first_name TEXT,
                discharge_book_number TEXT,
                date_of_issue DATE,
                place_of_issue TEXT,
                other_names TEXT,
                date_of_birth DATE,
                place_of_birth TEXT,
                nationality TEXT,
                tax_number TEXT,
                height TEXT,
                eye_colour TEXT,
                distinguishing_marks TEXT,
                profile_photo_url TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        '''
        db_manager.create_table_from_schema('user_profiles', profiles_schema)
        
        # Country entries table (for country log)
        country_entries_schema = '''
            CREATE TABLE IF NOT EXISTS country_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                entry_date DATE NOT NULL,
                departure_country TEXT NOT NULL,
                arrival_country TEXT NOT NULL,
                entry_type TEXT NOT NULL,
                description TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        '''
        db_manager.create_table_from_schema('country_entries', country_entries_schema)
        
        # Country periods table (calculated periods in each country)
        country_periods_schema = '''
            CREATE TABLE IF NOT EXISTS country_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                country TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                days INTEGER,
                period_type TEXT NOT NULL,
                entry_id INTEGER,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (entry_id) REFERENCES country_entries (id)
            )
        '''
        db_manager.create_table_from_schema('country_periods', country_periods_schema)
        
    except Exception as e:
        print(f"Error initializing database: {e}")

# ============================================================================
# SESSION STATE MANAGEMENT (SHARED)
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'entries' not in st.session_state:
        st.session_state.entries = []
    if 'editing_entry' not in st.session_state:
        st.session_state.editing_entry = None
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False

def clear_form_state():
    """Clear form input states"""
    # Crew logbook form keys
    crew_form_keys = [
        'ship_name', 'ship_number', 'port_registry', 'gross_tonnage',
        'place_joining', 'date_joining', 'place_leaving', 'date_leaving',
        'capacity', 'description', 'entry_type', 'sea_miles', 'senior_email'
    ]
    
    # Country log form keys
    country_log_keys = [
        'custom_departure', 'custom_arrival'
    ]
    
    # Clear all form keys
    all_keys = crew_form_keys + country_log_keys
    
    for key in all_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    st.session_state.editing_entry = None

# ============================================================================
# DATE AND TIME UTILITIES (SHARED)
# ============================================================================

def format_utc_datetime(date_obj):
    """Format date as UTC datetime string"""
    if isinstance(date_obj, str):
        # If it's already a string, try to parse it first
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
        except:
            return date_obj
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%Y-%m-%d %H:%M:%S UTC')
    return str(date_obj)

def calculate_sea_days(start_date, end_date):
    """Calculate sea days between two dates"""
    if start_date and end_date:
        delta = end_date - start_date
        return delta.days
    return 0

# ============================================================================
# GEOGRAPHIC CALCULATION FUNCTIONS (SHARED)
# ============================================================================

def get_coordinates(location):
    """Get coordinates for a location"""
    if not GEOPY_AVAILABLE:
        return None
    
    try:
        geolocator = Nominatim(user_agent="sea_miles_calculator")
        location_data = geolocator.geocode(location, timeout=10)
        if location_data:
            return (location_data.latitude, location_data.longitude)
    except:
        pass
    return None

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates in nautical miles"""
    if not GEOPY_AVAILABLE or not coord1 or not coord2:
        return None
    
    try:
        distance_km = geodesic(coord1, coord2).kilometers
        # Convert to nautical miles (1 nautical mile = 1.852 km)
        return distance_km / 1.852
    except:
        return None

# ============================================================================
# SHARED UTILITY FUNCTIONS
# ============================================================================

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_currency(amount):
    """Format currency for display"""
    return f"${amount:,.2f}"

def format_distance(distance_nm):
    """Format distance in nautical miles"""
    return f"{distance_nm:.1f} nm"

def format_duration(days):
    """Format duration in days"""
    if days == 1:
        return "1 day"
    return f"{days} days"

# ============================================================================
# SHARED VALIDATION FUNCTIONS
# ============================================================================

def validate_coordinates(lat, lon):
    """Validate latitude and longitude"""
    try:
        lat = float(lat)
        lon = float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False

def validate_date_range(start_date, end_date):
    """Validate that start_date is before or equal to end_date"""
    if not start_date or not end_date:
        return False
    return start_date <= end_date

def sanitize_string(text):
    """Basic string sanitization"""
    if not text:
        return ""
    return str(text).strip()