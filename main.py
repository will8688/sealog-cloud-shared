import streamlit as st
from datetime import datetime
import json
import os
import warnings
from urllib.parse import parse_qs


warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")

# Import database manager at the top
from sealog_cloud.database_manager import db_manager
from sealog_cloud.mobile_css import apply_global_mobile_fixes

# SAFE ROUTER IMPLEMENTATION

# Import modules - RESTORED TO MATCH ORIGINAL
from sealog_cloud.authentication import (
    check_persistent_login, 
    clear_persistent_login, 
    login_page,
    check_payment_status,
    handle_post_login_invitation
)
from sealog_cloud.core.utils import (
    init_database,
    init_session_state
)
from sealog_cloud.ui.styling import (
    apply_custom_css,
    Themes,
    apply_theme,
    apply_user_theme
)

from sealog_cloud.components.settings import render_settings
# Import tools

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_cached_user_info(user_id):
    """Cache user basic info"""
    try:
        result = db_manager.execute_query(
            'SELECT username, email FROM users WHERE id = ?',
            (user_id,),
            fetch='one'
        )
        return result
    except ImportError:
        return None

# QUICK WIN 1: Add caching to expensive operations  
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_payment_status(user_id):
    """Cache payment status to avoid repeated DB calls"""
    return check_payment_status(user_id)

def import_tool_module(tool_name):
    """Get tool modules (simplified since we import directly now)"""
    tool_map = {
        "settings": render_settings,
    }
    
    return tool_map.get(tool_name)


# ADD THIS SECTION RIGHT HERE - Simple credentials setup (UNCHANGED)
if not os.path.exists('credentials.json'):
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if credentials_json:
        try:
            with open('credentials.json', 'w') as f:
                json.dump(json.loads(credentials_json), f, indent=2)
            print(" Created credentials.json from environment variable")
        except Exception as e:
            print(f" Error creating credentials.json: {e}")
    else:
        print(" GOOGLE_CREDENTIALS_JSON environment variable not found")

# QUICK WIN 3: Initialize database connections once
@st.cache_resource
def initialize_app_resources():
    """Initialize heavy resources once and cache them"""
    try:
        
        return {
            'db_status': db_manager.test_connection()
        }
    except Exception as e:
        return {
            'radiolog_available': False,
            'engine_db_available': False,
            'db_status': (False, str(e))
        }

def main():
    """Main application function"""
    # Only set page config if it hasn't been set already
    try:
        st.set_page_config(
            page_title="SeaLog Cloud",
            page_icon="",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except st.errors.StreamlitAPIException:
        # Page config already set, continue
        pass
    
    # Hide Streamlit header/toolbar
    st.markdown("""
        <style>
        header[data-testid="stHeader"] {
            display: none;
        }
        .block-container {
            padding-top: 0 !important;
        }
                
        .stApp [data-testid="stToolbar"]{
            display:none;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }

        
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize secure session persistence system early
    try:
        from sealog_cloud.components.secure_sessions import initialize_secure_sessions
        initialize_secure_sessions()
    except ImportError:
        # Secure sessions not available, continue with fallback methods
        pass
    
    # ROUTER: Initialize routing from URL
    router.initialize_routing()
    
    # Initialize core components - RESTORED TO MATCH ORIGINAL
    init_session_state()
    init_database()

    # Now load heavy resources only for authenticated users
    apply_global_mobile_fixes()
    
    # Initialize database and resources for authenticated users - RESTORED
    app_resources = initialize_app_resources()
    
    # Initialize current tool state
    if 'current_tool' not in st.session_state:
        st.session_state.current_tool = "crewlog"
    
    # Add backward compatibility for modules still using st.session_state.db
    if 'db' not in st.session_state:
        try:
            st.session_state.db = db_manager
            st.session_state.db_connected = app_resources['db_status'][0]
        except Exception as e:
            st.error(f"Database backward compatibility setup error: {e}")
            st.session_state.db_connected = False
    
    # Display database status
    success, message = app_resources['db_status']
    if not success:
        st.error(f" Database connection failed: {message}")
        st.info("Please check your database configuration and try again.")
        return
    
    st.session_state.db_connected = True
    
    # Apply full styling for authenticated users
    apply_custom_css()
    apply_user_theme()
    apply_theme(Themes.maritime())

    # Sidebar navigation
    # render_sidebar()
    
    # Main content
    # render_main_content();

    render_admin()

# ROUTER-ENABLED SIDEBAR: Uses router but maintains backward compatibility
def render_sidebar():
    with st.sidebar:
        
        
        # Use cached user info
        user_info = get_cached_user_info(st.session_state.user_id)
        username = user_info['username'] if user_info else st.session_state.get('username', 'User')
        st.markdown(f"Welcome, **{username}**")

        # Database mode switch button
        # current_offline = st.session_state.get('use_offline_mode', False)
        # if st.button(f"Switch to {'Online' if current_offline else 'Offline'}", 
        #             use_container_width=True, 
        #             type="secondary"):
        #     db_manager.switch_database_mode(use_offline=not current_offline)
        #     st.rerun()

        # Show database mode for development
        if st.session_state.get('show_db_status', False):
            db_mode = " Online" if db_manager.db_type == 'postgresql' else " Local"
            st.caption(f"Database: {db_mode}")
            
            
        
        # ROUTER: Show current page in URL bar (development helper)
        if st.session_state.get('show_current_route', False):
            st.caption(f" Route: {router.get_current_tool()}")
        
        # ROUTER-ENABLED: Group related buttons to reduce redraws
        render_navigation_buttons()
        render_account_section()

def render_navigation_buttons():
    """Render navigation buttons with router integration"""
    current_tool = router.get_current_tool()
    
    # Profile button - ROUTER ENABLED
    if st.button(" Profile", 
                use_container_width=True,
                type="primary" if current_tool == "profile" else "secondary"):
        router.navigate_to("profile")  # Uses router instead of direct session_state
    
    # Accounting Tools section
    st.markdown("###  Accounting Tools")
    if st.button(" Country Log (Tax)", 
                use_container_width=True,
                type="primary" if current_tool == "countrylog" else "secondary"):
        router.navigate_to("countrylog")  # Uses router

    # Main Tools section
    st.subheader(" Tools")
    
    # Group tool buttons for better performance - ALL ROUTER ENABLED
    tool_buttons = [
        (" Crew Logbook", "crewlog"),
        (" Crew List", "crew_list"),
        (" Ships Logbook", "shipslog"),
        (" Engine Logbook", "enginelog"),
        (" Radio Logbook", "radiolog"),
        (" Hours of Rest", "hoursofrest"),
        (" Watch Scheduler", "watch_scheduler"),
        (" Fuel Burn Calculator", "fuelburn"),
        (" Conversion Tools", "conversions"),
        (" Risk Assessment", "risk_assessment")
    ]
    
    for label, tool_key in tool_buttons:
        if st.button(label, 
                    use_container_width=True,
                    type="primary" if current_tool == tool_key else "secondary"):
            router.navigate_to(tool_key)  # All use router now
    
    # Show Ships Logbook contents
    if current_tool == "shipslog":
        st.markdown("-  *Navigation,  Engine,  Radio*")

def render_account_section():
    """Render account section with router integration"""
    st.markdown("---")
    st.subheader(" Account")
    
    # QUICK WIN 9: Cache payment status
    has_payment = get_cached_payment_status(st.session_state.user_id)
    if has_payment:
        st.success(" Premium Active")
    else:
        st.warning(" Free Version")
        if st.button(" Upgrade", use_container_width=True):
            router.navigate_to("payment")  # Uses router
    
    # Settings and logout - ROUTER ENABLED
    if st.button(" Settings", 
                use_container_width=True,
                type="primary" if router.get_current_tool() == "settings" else "secondary"):
        router.navigate_to("settings")  # Uses router
    
    if st.button(" Logout", use_container_width=True):
        # Clear cached data on logout
        st.cache_data.clear()
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
        # ROUTER: Clear routing state on logout
        st.session_state.current_tool = "crewlog"
        st.session_state.current_route = "crewlog"
        st.query_params.clear()  # Clear URL parameters
        from sealog_cloud.authentication import clear_persistent_login
        clear_persistent_login()
        st.rerun()
    
    # Feature Request / Bug Report - ROUTER ENABLED
    st.markdown("---")
    if st.button(" Feature Request / Bug Report", 
                use_container_width=True,
                type="secondary"):
        router.navigate_to("contact")  # Uses router
    
    # ROUTER: Show routing info for development
    if st.session_state.get('show_routing_debug', False):
        st.markdown("---")
        st.caption(" Router Debug")
        st.caption(f"Tool: {router.get_current_tool()}")
        st.caption(f"Route: {router.get_url_param('route', 'none')}")

# Tool functions
def render_risk_assessment():
    """Risk assessment tool - now implemented"""
    risk_assessment_main()

def render_main_content():
    """Render the main content area based on selected tool - ROUTER COMPATIBLE"""
    current_tool = router.get_current_tool()
    tool_function = import_tool_module(current_tool)
    
    if tool_function:
        tool_function()
    else:
        # Show main app title for unhandled tools
        st.title("SeaLog Cloud")
        st.markdown("*Digital maritime documentation and tools for professional mariners*")
        st.info(f"Tool '{current_tool}' is not yet implemented.")
        
        # Dashboard overview
        st.title(" Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Tools", "6")
        with col2:
            st.metric("Total Entries", "12")
        with col3:
            st.metric("Sea Miles", "2,450")
        with col4:
            st.metric("Days at Sea", "89")
        
        st.markdown("---")
        
        st.subheader(" Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(" Add Logbook Entry", use_container_width=True):
                router.navigate_to("crewlog")
        
        with col2:
            if st.button(" Ships Log", use_container_width=True):
                router.navigate_to("shipslog")
        
        with col3:
            if st.button(" Radio Log", use_container_width=True):
                router.navigate_to("radiolog")

def handle_oauth_redirect():
    """Handle OAuth redirect and navigate to correct page - ROUTER ENHANCED"""
    # Check if we have a pending Google Calendar redirect
    if st.session_state.get('google_calendar_redirect_pending'):
        # ROUTER: Navigate to countrylog with parameters
        router.navigate_to("countrylog", params={'show_calendar': 'true'})
        
        # Set a flag to show the calendar import tab
        st.session_state.show_calendar_import = True

# ROUTER: Helper functions for tools to use
def get_current_route():
    """Helper function for tools to get current route"""
    return router.get_current_tool()

def get_route_param(key, default=None):
    """Helper function for tools to get URL parameters"""
    return router.get_url_param(key, default)

def navigate_to_tool(tool_name, **params):
    """Helper function for tools to navigate"""
    router.navigate_to(tool_name, params=params)

if __name__ == "__main__":
    main()