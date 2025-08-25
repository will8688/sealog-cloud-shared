import streamlit as st
import json
import os

# Color schemes and constants
class Colors:
    """Color constants for consistent theming"""
    # Maritime theme colors (unified)
    PRIMARY = "#1e3a8a"  # Deep maritime blue
    SECONDARY = "#3b82f6"  # Medium blue
    ACCENT = "#17a2b8"  # Teal accent
    
    # Entry type colors
    SEA_GOING_BG = "#E3F2FD"  # Light blue
    SEA_GOING_BORDER = "#2196F3"  # Blue
    IN_PORT_BG = "#E8F5E8"  # Light green
    IN_PORT_BORDER = "#4CAF50"  # Green
    
    # Status colors
    SUCCESS = "#10b981"  # Green
    WARNING = "#f59e0b"  # Orange
    ERROR = "#ef4444"  # Red
    VERIFIED_BG = "#4CAF50"  # Green
    PENDING_BG = "#FFC107"  # Yellow/Orange
    
    # Text colors
    TEXT_PRIMARY = "#1f2937"
    TEXT_SECONDARY = "#6b7280"
    TEXT_WHITE = "white"
    TEXT_BLACK = "black"
    
    # Background colors
    BACKGROUND_LIGHT = "#f8fafc"
    SURFACE_LIGHT = "#ffffff"
    BACKGROUND_DARK = "#1f2937"
    SURFACE_DARK = "#374151"
    
    # Authentication specific
    AUTH_GRADIENT = "linear-gradient(90deg, #1e3a8a, #17a2b8)"
    TOOL_CARD_GRADIENT = "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)"
    CTA_GRADIENT = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"

    """Color constants for consistent theming"""
    # Your existing colors...
    PRIMARY = "#1e3a8a"
    SECONDARY = "#3b82f6"
    # ... etc ...
    
    # NEW: Naval Night Mode colors
    NAVAL_DARK_BG = "#0A0A0A"
    NAVAL_DARK_SURFACE = "#1A0000"
    NAVAL_RED_PRIMARY = "#FF3333"
    NAVAL_RED_SECONDARY = "#CC0000"
    NAVAL_RED_ACCENT = "#660000"
    NAVAL_RED_DARK = "#330000"

AVAILABLE_THEMES = {
    "maritime": {
        "name": "Maritime Blue",
        "primary": "#1e3a8a",
        "secondary": "#3b82f6",
        "accent": "#17a2b8",
        "background": "#ffffff",
        "surface": "#f8fafc",
        "text": "#1f2937"
    },
    "naval_night": {
        "name": "Night Mode",
        "primary": "#FF3333",
        "secondary": "#CC0000",
        "accent": "#660000",
        "background": "#0A0A0A",
        "surface": "#1A0000",
        "text": "#CC0000"
    },
    "dark": {
        "name": "Dark Mode",
        "primary": "#3b82f6",
        "secondary": "#6b7280",
        "accent": "#10b981",
        "background": "#1f2937",
        "surface": "#374151",
        "text": "#f9fafb"
    }
}

def section_header(text):
    st.markdown(f"###  {text}", unsafe_allow_html=True)

def form_style():
    st.markdown(
        """
        <style>
        .stForm {
            background-color: #f9f9f9;
            padding: 1.5rem;
            border: 1px solid #ddd;
            border-radius: 12px;
            box-shadow: 1px 1px 6px rgba(0,0,0,0.05);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
def get_entry_colors(entry_type):
    """Get background and border colors for entry type"""
    if entry_type == 'Sea Going':
        return Colors.SEA_GOING_BG, Colors.SEA_GOING_BORDER
    else:
        return Colors.IN_PORT_BG, Colors.IN_PORT_BORDER

def render_entry_card_html(ship_name, ship_number, place_joining, date_joining, 
                          place_leaving, date_leaving, capacity, entry_type, 
                          sea_days, sea_miles, description, bg_color, border_color):
    """Generate HTML for entry card"""
    return f"""
    <div style='
        background-color: {bg_color}; 
        border-left: 4px solid {border_color}; 
        padding: 15px; 
        margin: 10px 0; 
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    '>
        <h4 style='margin: 0 0 10px 0; color: {Colors.TEXT_PRIMARY};'>{ship_name} {f"({ship_number})" if ship_number else ""}</h4>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 10px;'>
            <div><strong>Route:</strong> {place_joining} → {place_leaving}</div>
            <div><strong>Dates:</strong> {date_joining} → {date_leaving}</div>
            <div><strong>Capacity:</strong> {capacity}</div>
            <div><strong>Type:</strong> {entry_type}</div>
            <div><strong>Sea Days:</strong> {sea_days}</div>
            <div><strong>Sea Miles:</strong> {sea_miles:.1f} nm</div>
        </div>
        {f"<div style='margin-bottom: 10px;'><strong>Description:</strong> {description}</div>" if description else ""}
    </div>
    """

def render_status_badge(verified):
    """Render verification status badge"""
    if verified:
        return """
        <span style='display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; background-color: #4CAF50; color: white; margin-left: 15px;'>
             Verified
        </span>
        """
    else:
        return """
        <span style='display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; background-color: #FFC107; color: black; margin-left: 15px;'>
            ⏳ Pending Verification
        </span>
        """

def render_pricing_card():
    """Render the premium pricing card with gradient"""
    return f"""
    <div style='
        background: {Colors.CTA_GRADIENT};
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    '>
        <h2 style='margin: 0; color: white;'>$29.99</h2>
        <p style='margin: 5px 0; color: white;'>One-time payment</p>
        <p style='margin: 0; color: white;'><strong>365 days full access</strong></p>
    </div>
    """

def render_security_badges():
    """Render security trust badges"""
    return """
    <div style='text-align: center; opacity: 0.7;'>
         <strong>Secure Payment</strong> |  <strong>Money Back Guarantee</strong> |  <strong>SSL Encrypted</strong>
    </div>
    """

def render_delete_confirmation_box():
    """Render delete confirmation warning box"""
    return """
    <div style='background-color: #ffebee; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #f44336;'>
    """

def render_feature_highlight(icon, title, description):
    """Render a feature highlight box"""
    return f"""
    <div style='
        background-color: #f8f9fa;
        border-left: 4px solid {Colors.PRIMARY};
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    '>
        <h4 style='margin: 0 0 5px 0; color: {Colors.PRIMARY};'>{icon} {title}</h4>
        <p style='margin: 0; color: {Colors.TEXT_SECONDARY};'>{description}</p>
    </div>
    """

def render_auth_header():
    """Render the main authentication header"""
    return f"""
    <div style="
        text-align: center; 
        padding: 1.5rem 0; 
        background: {Colors.AUTH_GRADIENT}; 
        color: white; 
        border-radius: 12px; 
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
    ">
        <h1 style="margin: 0 0 0.5rem 0; font-size: 2.5rem; font-weight: 700;"> The SeaLog Cloud</h1>
        <h3 style="margin: 0 0 0.5rem 0; font-size: 1.3rem; font-weight: 400; opacity: 0.95;">Digital Maritime Tools for Efficiency and Documentation</h3>
        <p style="margin: 0; font-size: 1rem; font-weight: 500; opacity: 0.9;">
            <strong>Crew Logbook (miles and Days) Country Log (for Tax) Ship, Engine and Radio Logbook, Hours of Rest, Watch Schedular, Risk Assessment and much more...</strong>
        </p>
    </div>
    """

def render_auth_value_props():
    """Render authentication value propositions"""
    return f"""
    <div style="
        background: {Colors.SURFACE_LIGHT};
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    ">
        <h4 style="color: {Colors.PRIMARY}; margin: 0 0 0.5rem 0; text-align: center;"> Why Maritime Professionals Choose Us</h4>
        <div style="font-size: 0.9rem; line-height: 1.6; color: {Colors.TEXT_SECONDARY};">
             <strong>Start Free</strong> - No credit card required<br/>
             <strong>Works Anywhere</strong> - Cloud-based platform<br/>
             <strong>Professional PDFs</strong> - MCA compliant exports<br/>
             <strong>Secure & Private</strong> - Your data, protected<br/>
             <strong>Always Improving</strong> - Regular feature updates
        </div>
    </div>
    """

def render_auth_cta_section():
    """Render call-to-action section"""
    return f"""
    <div style="
        text-align: center; 
        padding: 1.5rem; 
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); 
        border-radius: 12px; 
        margin-top: 2rem;
        border: 1px solid #a7f3d0;
    ">
        <h3 style="margin: 0 0 0.5rem 0; color: {Colors.PRIMARY};"> Ready to Go Digital?</h3>
        <p style="margin: 0 0 0.5rem 0; font-weight: 600; color: {Colors.TEXT_PRIMARY};">
            Join maritime professionals worldwide using digital logbooks
        </p>
        <p style="margin: 0; color: {Colors.TEXT_SECONDARY}; font-size: 0.9rem;">
            Start with our free tier - upgrade only when you need more features
        </p>
    </div>
    """

def apply_custom_css():
    """Apply custom CSS styles to the Streamlit app with dark mode support"""
    st.markdown(f"""
    <style>
    /* CSS Variables for theming */
    :root {{
        --primary-color: {Colors.PRIMARY};
        --secondary-color: {Colors.SECONDARY};
        --accent-color: {Colors.ACCENT};
        --success-color: {Colors.SUCCESS};
        --warning-color: {Colors.WARNING};
        --error-color: {Colors.ERROR};
        --text-primary: {Colors.TEXT_PRIMARY};
        --text-secondary: {Colors.TEXT_SECONDARY};
        --background-light: {Colors.BACKGROUND_LIGHT};
        --surface-light: {Colors.SURFACE_LIGHT};
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* ===== AUTHENTICATION STYLES ===== */
    
    /* Tool showcase category headers */
    .category-header {{
        background: {Colors.AUTH_GRADIENT};
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 1.5rem 0 0.5rem 0;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 2px 8px rgba(30, 58, 138, 0.2);
    }}
    
    /* Tool expander styling */
    .streamlit-expanderHeader {{
        background-color: {Colors.TOOL_CARD_GRADIENT} !important;
        border-radius: 8px !important;
        border: 1px solid rgba(30, 58, 138, 0.2) !important;
        margin-bottom: 0.5rem !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        box-shadow: 0 2px 8px rgba(30, 58, 138, 0.1) !important;
        transform: translateY(-1px);
        transition: all 0.3s ease;
    }}
    
    /* Tool expander content */
    .streamlit-expanderContent {{
        background-color: {Colors.SURFACE_LIGHT};
        border: 1px solid #e5e7eb;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 1rem !important;
    }}
    
    /* Authentication form styling */
    .auth-form-container {{
        background: {Colors.SURFACE_LIGHT};
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }}
    
    /* Tool showcase grid */
    .tool-showcase {{
        background: {Colors.SURFACE_LIGHT};
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        max-height: 70vh;
        overflow-y: auto;
    }}
    
    /* Custom scrollbar for tool showcase */
    .tool-showcase::-webkit-scrollbar {{
        width: 6px;
    }}
    
    .tool-showcase::-webkit-scrollbar-track {{
        background: #f1f5f9;
        border-radius: 3px;
    }}
    
    .tool-showcase::-webkit-scrollbar-thumb {{
        background: {Colors.SECONDARY};
        border-radius: 3px;
    }}
    
    .tool-showcase::-webkit-scrollbar-thumb:hover {{
        background: {Colors.PRIMARY};
    }}
    
    /* ===== GENERAL UI IMPROVEMENTS ===== */
    
    /* Button styling with maritime theme */
    .stButton > button {{
        border-radius: 8px;
        border: 1px solid #e0e0e0 !important;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        transition: all 0.3s ease;
        font-size: 0.95rem;
    }}
    
    /* Primary buttons */
    .stButton > button[kind="primary"] {{
        background: {Colors.PRIMARY} !important;
        border: 1px solid {Colors.PRIMARY} !important;
        color: white !important;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background: #1e40af !important;
        border-color: #1e40af !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
    }}
    
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {{
        border: 1px solid {Colors.SECONDARY} !important;
        color: {Colors.SECONDARY} !important;
    }}
    
    .stButton > button[kind="secondary"]:hover {{
        background: {Colors.SECONDARY} !important;
        color: white !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
    }}
    
    /* ===== DARK MODE SUPPORT ===== */
    
    @media (prefers-color-scheme: dark) {{
        :root {{
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --background-light: #1f2937;
            --surface-light: #374151;
        }}
        
        .auth-form-container,
        .tool-showcase,
        .streamlit-expanderContent {{
            background-color: #374151 !important;
            border-color: #4b5563 !important;
            color: #f9fafb !important;
        }}
        
        .category-header {{
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }}
        
        .stButton > button {{
            border: 1px solid #4a4a4a !important;
            color: #f9fafb !important;
        }}
        
        .stButton > button[kind="secondary"] {{
            border: 1px solid #666666 !important;
        }}
        
        .tool-showcase::-webkit-scrollbar-track {{
            background: #4b5563;
        }}
    }}
    
    /* Streamlit dark mode detection */
    [data-testid="stAppViewContainer"][data-theme="dark"] .auth-form-container,
    [data-testid="stAppViewContainer"][data-theme="dark"] .tool-showcase,
    [data-testid="stAppViewContainer"][data-theme="dark"] .streamlit-expanderContent {{
        background-color: #374151 !important;
        border-color: #4b5563 !important;
        color: #f9fafb !important;
    }}
    
    [data-testid="stAppViewContainer"][data-theme="dark"] .stButton > button {{
        border: 1px solid #4a4a4a !important;
        color: #f9fafb !important;
    }}
    
    [data-testid="stAppViewContainer"][data-theme="dark"] .stButton > button[kind="secondary"] {{
        border: 1px solid #666666 !important;
    }}
    
    /* ===== FORM STYLING ===== */
    
    /* Form labels - enhanced visibility */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stDateInput > label,
    .stSlider > label,
    .stRadio > label,
    .stCheckbox > label,
    .stMultiSelect > label,
    .stNumberInput > label {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
        font-size: 0.95rem !important;
    }}
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {{
        border-radius: 6px !important;
        border: 1.5px solid #d1d5db !important;
        padding: 0.6rem !important;
        font-size: 0.95rem !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: {Colors.PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1) !important;
        outline: none !important;
    }}
    
    /* Dark mode form fields */
    @media (prefers-color-scheme: dark) {{
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {{
            background-color: #374151 !important;
            border-color: #4b5563 !important;
            color: #f9fafb !important;
        }}
        
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder,
        .stNumberInput > div > div > input::placeholder {{
            color: #9ca3af !important;
        }}
        
        .stTextInput > label,
        .stTextArea > label,
        .stSelectbox > label,
        .stDateInput > label,
        .stSlider > label,
        .stRadio > label,
        .stCheckbox > label,
        .stMultiSelect > label,
        .stNumberInput > label {{
            color: #f9fafb !important;
        }}
    }}
    
    [data-testid="stAppViewContainer"][data-theme="dark"] .stTextInput > div > div > input,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stTextArea > div > div > textarea,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stNumberInput > div > div > input {{
        background-color: #374151 !important;
        border-color: #4b5563 !important;
        color: #f9fafb !important;
    }}
    
    [data-testid="stAppViewContainer"][data-theme="dark"] .stTextInput > label,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stTextArea > label,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stSelectbox > label,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stDateInput > label,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stSlider > label,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stRadio > label,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stCheckbox > label,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stMultiSelect > label,
    [data-testid="stAppViewContainer"][data-theme="dark"] .stNumberInput > label {{
        color: #f9fafb !important;
    }}
    
    /* ===== LEGACY STYLES (preserved) ===== */
    
    /* Form styling */
    .stForm {{
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        background-color: {Colors.SURFACE_LIGHT};
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }}
    
    @media (prefers-color-scheme: dark) {{
        .stForm {{
            background-color: #374151;
            border-color: #4b5563;
        }}
    }}
    
    /* Form section headers - let themes override */
    .stForm h3,
    .stForm h4 {{
        border-bottom: 2px solid currentColor !important;
        padding-bottom: 0.5rem !important;
        margin-bottom: 1rem !important;
        /* Remove the color override to let themes control it */
    }}
    
    @media (prefers-color-scheme: dark) {{
        .stForm h3,
        .stForm h4 {{
            color: {Colors.SECONDARY} !important;
            border-bottom-color: {Colors.SECONDARY} !important;
        }}
    }}
    
    /* Metric cards */
    .metric-card {{
        background-color: {Colors.SURFACE_LIGHT};
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid {Colors.PRIMARY};
    }}
    
    /* Entry cards hover effect */
    .entry-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }}
    
    /* Status badges */
    .status-verified {{
        background-color: {Colors.SUCCESS};
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        display: inline-block;
    }}
    
    .status-pending {{
        background-color: {Colors.WARNING};
        color: black;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        display: inline-block;
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        background-color: {Colors.BACKGROUND_LIGHT};
    }}
    
    /* Success/Warning/Error message styling */
    .stSuccess {{
        background-color: #d1fae5;
        border-color: #a7f3d0;
        color: #065f46;
    }}
    
    .stWarning {{
        background-color: #fef3c7;
        border-color: #fde68a;
        color: #92400e;
    }}
    
    .stError {{
        background-color: #fee2e2;
        border-color: #fecaca;
        color: #991b1b;
    }}
    
    /* Table styling */
    .dataframe {{
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        min-width: 400px;
        border-radius: 8px 8px 0 0;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }}
    
    .dataframe thead tr {{
        background-color: {Colors.PRIMARY};
        color: #ffffff;
        text-align: left;
    }}
    
    .dataframe th,
    .dataframe td {{
        padding: 12px 15px;
    }}
    
    .dataframe tbody tr {{
        border-bottom: 1px solid #e5e7eb;
    }}
    
    .dataframe tbody tr:nth-of-type(even) {{
        background-color: #f9fafb;
    }}
    
    /* Navigation pills */
    .nav-pills {{
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }}
    
    .nav-pill {{
        padding: 8px 16px;
        border-radius: 20px;
        background-color: #f1f5f9;
        color: {Colors.TEXT_SECONDARY};
        text-decoration: none;
        transition: all 0.3s ease;
    }}
    
    .nav-pill.active {{
        background-color: {Colors.PRIMARY};
        color: white;
    }}
    
    .nav-pill:hover {{
        background-color: #e2e8f0;
        transform: translateY(-1px);
    }}
    
    /* Risk assessment specific styling */
    .risk-matrix-cell {{
        text-align: center;
        font-weight: bold;
        color: white;
        padding: 8px;
        border: 1px solid #d1d5db;
    }}
    
    /* Responsive design */
    @media (max-width: 768px) {{
        .auth-form-container,
        .tool-showcase {{
            margin: 0.5rem 0;
            padding: 1rem;
        }}
        
        .category-header {{
            padding: 0.5rem;
            font-size: 0.9rem;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

def render_premium_features_list():
    """Render the premium features list with icons"""
    return """
     **Unlimited Entries** - Add as many passage entries as you need  
     **Advanced Reports** - Generate custom date range reports  
     **Print & Download** - Export your logbook in professional PDF format  
     **Priority Support** - Get help when you need it most  
     **Auto-calculations** - Enhanced geographic distance calculations  
     **Secure Storage** - Your data is safely stored and backed up  
    """

def render_upgrade_benefits():
    """Render the upgrade benefits section"""
    return """
    ###  What You Get:
    -  Unlimited entries
    -  PDF exports
    -  Custom reports
    -  1 year access
    -  Priority support
    """

def render_payment_success_message(payment_date, expiry_date):
    """Render payment success message with balloons effect"""
    return f"""
    **Premium Access Activated!**
    
     Payment Date: {payment_date.strftime('%Y-%m-%d %H:%M:%S')}  
     Access Until: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}  
     Premium Features: Unlocked  
    
    You now have full access to all premium features!
    """

def render_bank_transfer_details():
    """Render bank transfer information"""
    return """
    **Bank Transfer Details:**
    
    Account: Sea Miles Calculator Ltd  
    IBAN: GB29 NWBK 6016 1331 9268 19  
    BIC: NWBKGB2L  
    Reference: Your username
    
    Please email proof of payment to: payments@seamiles.com
    """

def render_main_header(title, subtitle=None):
    """Render a styled main header"""
    subtitle_html = f"<p style='margin: 0; opacity: 0.9;'>{subtitle}</p>" if subtitle else ""
    
    return f"""
    <div style="
        background: {Colors.AUTH_GRADIENT};
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
    ">
        <h1 style='margin: 0;'>{title}</h1>
        {subtitle_html}
    </div>
    """

def render_info_box(message, box_type="info"):
    """Render an informational box with different types"""
    colors = {
        "info": {"bg": "#dbeafe", "border": "#93c5fd", "text": "#1e40af"},
        "success": {"bg": "#d1fae5", "border": "#a7f3d0", "text": "#065f46"},
        "warning": {"bg": "#fef3c7", "border": "#fde68a", "text": "#92400e"},
        "error": {"bg": "#fee2e2", "border": "#fecaca", "text": "#991b1b"}
    }
    
    color = colors.get(box_type, colors["info"])
    
    return f"""
    <div style='
        background-color: {color["bg"]};
        border: 1px solid {color["border"]};
        color: {color["text"]};
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    '>
        {message}
    </div>
    """

def render_loading_spinner(message="Loading..."):
    """Render a loading spinner with message"""
    return f"""
    <div style='text-align: center; padding: 20px;'>
        <div style='
            border: 4px solid #f3f3f3;
            border-top: 4px solid {Colors.PRIMARY};
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
            margin: 0 auto 10px;
        '></div>
        <p>{message}</p>
    </div>
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """

def render_stats_card(title, value, icon="", color=None):
    """Render a statistics card"""
    if color is None:
        color = Colors.PRIMARY
        
    return f"""
    <div style='
        background-color: {Colors.SURFACE_LIGHT};
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid {color};
        text-align: center;
        margin: 10px 0;
    '>
        <div style='font-size: 24px; margin-bottom: 10px;'>{icon}</div>
        <h3 style='margin: 0; color: {color};'>{value}</h3>
        <p style='margin: 5px 0 0 0; color: {Colors.TEXT_SECONDARY};'>{title}</p>
    </div>
    """

def render_navigation_pills(current_page, pages):
    """Render navigation pills"""
    pills_html = "<div class='nav-pills'>"
    for page_key, page_name in pages.items():
        active_class = " active" if current_page == page_key else ""
        pills_html += f"<div class='nav-pill{active_class}'>{page_name}</div>"
    pills_html += "</div>"
    
    return pills_html

def load_user_theme():
    """Load user's theme preference"""
    if 'user_theme' not in st.session_state:
        # Try to load from file
        try:
            with open('user_theme.json', 'r') as f:
                config = json.load(f)
                st.session_state.user_theme = config.get('theme', 'maritime')
        except FileNotFoundError:
            st.session_state.user_theme = 'maritime'
    return st.session_state.user_theme

def save_user_theme(theme_name):
    """Save user's theme preference"""
    st.session_state.user_theme = theme_name
    config = {'theme': theme_name}
    with open('user_theme.json', 'w') as f:
        json.dump(config, f)

def apply_naval_night_theme():
    """Apply the naval night mode theme"""
    st.markdown("""
    <style>
    /* Naval Night Mode Theme */
    .stApp {
        background-color: #0A0A0A !important;
        color: #CC0000 !important;
    }
    
    /* Sidebar */
    .stSidebar {
        background-color: #1A0000 !important;
    }
    .stSidebar .stButton > button {
        background-color: #330000 !important;
        color: #CC0000 !important;
        border: 1px solid #660000 !important;
    }
    .stSidebar .stButton > button:hover {
        background-color: #660000 !important;
        color: #FF3333 !important;
        box-shadow: 0 0 10px rgba(255, 51, 51, 0.3) !important;
    }
    .stSidebar .stButton > button[kind="primary"] {
        background-color: #660000 !important;
        color: #FF3333 !important;
        border: 1px solid #FF3333 !important;
    }
    .stSidebar .stButton > button[kind="primary"]:hover {
        background-color: #FF3333 !important;
        color: #000000 !important;
        box-shadow: 0 0 15px rgba(255, 51, 51, 0.5) !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #FF3333 !important;
        text-shadow: 0 0 5px rgba(255, 51, 51, 0.3);
    }
    
    /* Main content text */
    .stMarkdown, .stText, p, span, div, li {
        color: #CC0000 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #330000 !important;
        color: #FF3333 !important;
        border: 1px solid #660000 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #660000 !important;
        color: #FF6666 !important;
        box-shadow: 0 0 10px rgba(255, 51, 51, 0.3) !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #660000 !important;
        color: #FF3333 !important;
        border: 1px solid #FF3333 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #FF3333 !important;
        color: #000000 !important;
        box-shadow: 0 0 15px rgba(255, 51, 51, 0.5) !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        background-color: #1A0000 !important;
        color: #CC0000 !important;
        border: 1px solid #660000 !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #FF3333 !important;
        box-shadow: 0 0 0 2px rgba(255, 51, 51, 0.2) !important;
    }
    
    /* Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stNumberInput > label,
    .stDateInput > label,
    .stRadio > label,
    .stCheckbox > label {
        color: #CC0000 !important;
    }
    
    /* Metrics */
    .stMetric {
        background-color: #1A0000 !important;
        border: 1px solid #330000 !important;
        border-radius: 4px !important;
        padding: 10px !important;
    }
    .stMetric .metric-label {
        color: #CC0000 !important;
    }
    .stMetric .metric-value {
        color: #FF3333 !important;
        text-shadow: 0 0 5px rgba(255, 51, 51, 0.3) !important;
    }
    
    /* Data frames and tables */
    .stDataFrame {
        background-color: #1A0000 !important;
        border: 1px solid #330000 !important;
    }
    .stDataFrame table {
        background-color: #1A0000 !important;
        color: #CC0000 !important;
    }
    .stDataFrame th {
        background-color: #330000 !important;
        color: #FF3333 !important;
    }
    .stDataFrame td {
        border-color: #330000 !important;
    }
    
    /* Forms */
    .stForm {
        background-color: #1A0000 !important;
        border: 1px solid #330000 !important;
    }
    
    /* Columns */
    .stColumn {
        background-color: transparent !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1A0000 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #CC0000 !important;
        background-color: #330000 !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #660000 !important;
        color: #FF3333 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #660000 !important;
        color: #FF3333 !important;
    }
    
    /* Expander */
    .stExpander {
        background-color: #1A0000 !important;
        border: 1px solid #330000 !important;
    }
    .stExpander .streamlit-expanderHeader {
        color: #FF3333 !important;
        background-color: #330000 !important;
    }
    .stExpander .streamlit-expanderContent {
        background-color: #1A0000 !important;
        color: #CC0000 !important;
    }
    
    /* Alert boxes */
    .stAlert {
        background-color: #330000 !important;
        border: 1px solid #660000 !important;
        color: #CC0000 !important;
    }
    .stSuccess {
        background-color: #1A0000 !important;
        border: 1px solid #FF3333 !important;
        color: #FF3333 !important;
    }
    .stWarning {
        background-color: #330000 !important;
        border: 1px solid #FF3333 !important;
        color: #FF3333 !important;
    }
    .stError {
        background-color: #660000 !important;
        border: 1px solid #FF3333 !important;
        color: #FF3333 !important;
    }
    
    /* Progress bars */
    .stProgress .stProgress-bar {
        background-color: #FF3333 !important;
    }
    
    /* Selectbox dropdown */
    .stSelectbox > div > div > div {
        background-color: #1A0000 !important;
        color: #CC0000 !important;
    }
    
    /* Multiselect */
    .stMultiSelect > div > div > div {
        background-color: #1A0000 !important;
        color: #CC0000 !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: #1A0000 !important;
        border: 1px solid #330000 !important;
    }
    
    /* Charts */
    .stPlotlyChart {
        background-color: #1A0000 !important;
        border: 1px solid #330000 !important;
    }
    
    /* Naval-specific elements */
    .naval-panel {
        background-color: #1A0000 !important;
        border: 2px solid #660000 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
        box-shadow: inset 0 0 10px rgba(255, 51, 51, 0.1) !important;
    }
    
    .naval-warning {
        background-color: #330000 !important;
        border: 2px solid #FF3333 !important;
        border-radius: 4px !important;
        padding: 10px !important;
        color: #FF3333 !important;
        text-shadow: 0 0 5px rgba(255, 51, 51, 0.5) !important;
        animation: naval-pulse 2s infinite !important;
    }
    
    @keyframes naval-pulse {
        0% { box-shadow: 0 0 5px rgba(255, 51, 51, 0.3); }
        50% { box-shadow: 0 0 15px rgba(255, 51, 51, 0.6); }
        100% { box-shadow: 0 0 5px rgba(255, 51, 51, 0.3); }
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px !important;
        background-color: #1A0000 !important;
    }
    ::-webkit-scrollbar-thumb {
        background-color: #660000 !important;
        border-radius: 4px !important;
    }
    ::-webkit-scrollbar-thumb:hover {
        background-color: #FF3333 !important;
    }
    
    /* Special maritime elements */
    .maritime-status {
        background-color: #330000 !important;
        border: 1px solid #FF3333 !important;
        padding: 8px 12px !important;
        border-radius: 4px !important;
        color: #FF3333 !important;
        font-weight: bold !important;
        text-shadow: 0 0 3px rgba(255, 51, 51, 0.5) !important;
    }
    
    .bridge-watch {
        background-color: #1A0000 !important;
        border: 2px solid #FF3333 !important;
        padding: 10px !important;
        border-radius: 6px !important;
        text-align: center !important;
        color: #FF3333 !important;
        font-weight: bold !important;
        animation: naval-pulse 3s infinite !important;
    }
    </style>
    """, unsafe_allow_html=True)

def apply_user_theme():
    """Apply the user's selected theme"""
    current_theme = load_user_theme()
    
    if current_theme == 'naval_night':
        apply_naval_night_theme()
    elif current_theme == 'dark':
        apply_dark_theme()
    # maritime theme is handled by your existing apply_custom_css()

def apply_dark_theme():
    """Apply a standard dark theme with targeted fixes"""
    st.markdown("""
    <style>
    /* Base dark theme */
    .stApp {
        background-color: #1f2937 !important;
        color: #f9fafb !important;
    }
    
    .stSidebar {
        background-color: #374151 !important;
    }
    
    /* Fix main text visibility issues */
    .stMarkdown, .stText, p, span, div, li {
        color: #f9fafb !important;
    }
    
    /* Fix headers */
    h1, h2, h3, h4, h5, h6 {
        color: #60a5fa !important;
    }
    
    /* Fix buttons */
    .stButton > button {
        background-color: #4b5563 !important;
        color: #f9fafb !important;
        border: 1px solid #6b7280 !important;
    }
    
    /* Fix input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        background-color: #374151 !important;
        color: #f9fafb !important;
        border: 1px solid #4b5563 !important;
    }
    
    /* Fix labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stNumberInput > label,
    .stDateInput > label,
    .stRadio > label,
    .stCheckbox > label {
        color: #f9fafb !important;
    }
    
    /* Fix dropdown options */
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    
    /* Fix tabs */
    .stTabs [data-baseweb="tab"] {
        color: #f9fafb !important;
    }
    
    /* Fix forms */
    .stForm {
        background-color: #374151 !important;
        border-color: #4b5563 !important;
    }
    
    /* Force dropdown visibility with higher specificity */
    [data-baseweb="menu"] {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    
    [data-baseweb="menu"] * {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    
    [data-baseweb="list"] {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    
    [data-baseweb="list"] * {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    
    [data-baseweb="listitem"] {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    
    [data-baseweb="popover"] {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    
    [data-baseweb="popover"] * {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    /* Force time input display field */
    .stTimeInput > div > div > div > div {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }

    /* More specific time input targeting */
    .stTimeInput [data-baseweb="select"] {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }

    .stTimeInput [data-baseweb="select"] > div {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }

    .stTimeInput [data-baseweb="select"] > div > div {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }

    /* Fix multiselect display field too */
    .stMultiSelect > div > div > div {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }

    .stMultiSelect [data-baseweb="select"] {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }

    .stMultiSelect [data-baseweb="select"] > div {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    /* Fix secondary buttons specifically */
    .stButton > button[kind="secondary"] {
        background-color: #4b5563 !important;
        color: #f9fafb !important;
        border: 1px solid #6b7280 !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background-color: #6b7280 !important;
        color: #f9fafb !important;
    }

    /* Also fix any button that might be getting missed */
    .stButton > button:not([kind="primary"]) {
        background-color: #4b5563 !important;
        color: #f9fafb !important;
        border: 1px solid #6b7280 !important;
    }
    /* Fix download button specifically */
    .stDownloadButton > button {
        background-color: #4b5563 !important;
        color: #f9fafb !important;
        border: 1px solid #6b7280 !important;
    }

    .stDownloadButton > button:hover {
        background-color: #6b7280 !important;
        color: #f9fafb !important;
    }

    /* More specific download button targeting */
    [data-testid="stDownloadButton"] button {
        background-color: #4b5563 !important;
        color: #f9fafb !important;
        border: 1px solid #6b7280 !important;
    }

    [data-testid="stDownloadButton"] button:hover {
        background-color: #6b7280 !important;
        color: #f9fafb !important;
    }
    /* Fix form submit button */
    .stFormSubmitButton > button {
        background-color: #4b5563 !important;
        color: #f9fafb !important;
        border: 1px solid #6b7280 !important;
    }

    .stFormSubmitButton > button:hover {
        background-color: #6b7280 !important;
        color: #f9fafb !important;
    }

    /* More specific form submit button targeting */
    [data-testid="stFormSubmitButton"] button {
        background-color: #4b5563 !important;
        color: #f9fafb !important;
        border: 1px solid #6b7280 !important;
    }

    [data-testid="stFormSubmitButton"] button:hover {
        background-color: #6b7280 !important;
        color: #f9fafb !important;
    }
    /* Hours of Rest cards - dark mode fix */
    .rest-period-card {
        background-color: #374151 !important;
        color: #f9fafb !important;
    }
    
    .rest-period-card * {
        color: #f9fafb !important;
    }
    
    /* Watch Schedule table - dark mode fix */
    .watch-schedule-table tr {
        background-color: #4b5563 !important;
        color: #f9fafb !important;
    }
    
    .watch-schedule-table td {
        color: #f9fafb !important;
    }
    </style>
    
    <script>
    // JavaScript to force dropdown styling
    function fixDropdowns() {
        // Find all dropdown elements
        const dropdowns = document.querySelectorAll('[data-baseweb="menu"], [data-baseweb="list"], [data-baseweb="listitem"], [data-baseweb="popover"]');
        
        dropdowns.forEach(dropdown => {
            dropdown.style.backgroundColor = '#374151';
            dropdown.style.color = '#f9fafb';
            
            // Fix all children too
            const children = dropdown.querySelectorAll('*');
            children.forEach(child => {
                child.style.backgroundColor = '#374151';
                child.style.color = '#f9fafb';
            // Fix download buttons specifically
            const downloadButtons = document.querySelectorAll('.stDownloadButton button, [data-testid="stDownloadButton"] button');
            downloadButtons.forEach(button => {
                button.style.backgroundColor = '#4b5563';
                button.style.color = '#f9fafb';
                button.style.border = '1px solid #6b7280';
            // Fix form submit buttons specifically
            const formSubmitButtons = document.querySelectorAll('.stFormSubmitButton button, [data-testid="stFormSubmitButton"] button');
            formSubmitButtons.forEach(button => {
                button.style.backgroundColor = '#4b5563';
                button.style.color = '#f9fafb';
                button.style.border = '1px solid #6b7280';
            });
        });
        
        // Fix time input display fields
        const timeInputs = document.querySelectorAll('.stTimeInput [data-baseweb="select"]');
        timeInputs.forEach(input => {
            input.style.backgroundColor = '#374151';
            input.style.color = '#f9fafb';
            
            const children = input.querySelectorAll('*');
            children.forEach(child => {
                child.style.backgroundColor = '#374151';
                child.style.color = '#f9fafb';
            });
        });
        
        // Fix multiselect display fields
        const multiInputs = document.querySelectorAll('.stMultiSelect [data-baseweb="select"]');
        multiInputs.forEach(input => {
            input.style.backgroundColor = '#374151';
            input.style.color = '#f9fafb';
            
            const children = input.querySelectorAll('*');
            children.forEach(child => {
                child.style.backgroundColor = '#374151';
                child.style.color = '#f9fafb';
            });
        });
    }
    
    // Run on page load
    setTimeout(fixDropdowns, 100);
    
    // Run periodically to catch dynamic elements
    setInterval(fixDropdowns, 1000);
    
    // Also run when elements are clicked
    document.addEventListener('click', () => {
        setTimeout(fixDropdowns, 100);
    });
    </script>
    """, unsafe_allow_html=True)

def get_period_status_bar_styles(theme: str = "default") -> str:
    """Get CSS styles for log period status bar"""
    
    if theme == "dark":
        return """
        <style>
        .period-status-container {
            background-color: #2d2d2d !important;
            border: 1px solid #404040 !important;
            border-radius: 8px !important;
            padding: 16px !important;
            margin: 12px 0 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
        }
        </style>
        """
    else:  # default/light theme
        return """
        <style>
        .period-status-container {
            background-color: #f8f9fa !important;
            border: 1px solid #dee2e6 !important;
            border-radius: 8px !important;
            padding: 16px !important;
            margin: 12px 0 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
        </style>
        """
        
def render_naval_status_panel():
    """Render a naval-style status panel"""
    return """
    <div class="naval-panel">
        <h4 style="color: #FF3333; margin-bottom: 10px;"> Navigation Status</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
            <div class="maritime-status">GPS: ACTIVE</div>
            <div class="maritime-status">RADAR: ONLINE</div>
            <div class="maritime-status">ENGINE: NORMAL</div>
            <div class="maritime-status">WATCH: ACTIVE</div>
        </div>
    </div>
    """

def render_bridge_watch_warning():
    """Render a bridge watch warning in naval style"""
    return """
    <div class="bridge-watch">
         BRIDGE WATCH ACTIVE 
    </div>
    """

# Theme presets
class Themes:
    """Predefined theme configurations"""
    
    @staticmethod
    def maritime():
        """Maritime blue theme"""
        return {
            "primary": Colors.PRIMARY,
            "secondary": Colors.SECONDARY,
            "accent": Colors.ACCENT,
            "success": Colors.SUCCESS,
            "warning": Colors.WARNING,
            "error": Colors.ERROR,
            "background": Colors.BACKGROUND_LIGHT,
            "surface": Colors.SURFACE_LIGHT
        }
    
    @staticmethod
    def professional():
        """Professional gray theme"""
        return {
            "primary": "#374151",
            "secondary": "#6b7280",
            "success": "#059669",
            "warning": "#d97706",
            "error": "#dc2626",
            "background": "#f9fafb",
            "surface": "#ffffff"
        }

def apply_theme(theme_dict):
    """Apply a theme configuration"""
    css_vars = ""
    for key, value in theme_dict.items():
        css_vars += f"--color-{key}: {value};\n"
    
    st.markdown(f"""
    <style>
    :root {{
        {css_vars}
    }}
    </style>
    """, unsafe_allow_html=True)