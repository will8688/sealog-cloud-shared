"""
Global Mobile CSS - Conservative Approach
=========================================
Fixes major mobile issues without breaking existing functionality
Add this to your main app file - safe and non-disruptive
"""

import streamlit as st

def inject_global_mobile_css():
    """
    Inject conservative mobile CSS fixes
    Focuses on whitespace, headers, and obvious mobile issues only
    """
    mobile_css = """
    <style>
    /* ===== MOBILE-ONLY FIXES (max-width: 768px) ===== */
    @media (max-width: 768px) {
        
        /* 1. FIX MAJOR WHITESPACE ISSUES */
        .main .block-container {
            padding-top: 1rem !important;        /* Reduce from ~3rem */
            padding-left: 1rem !important;       /* Reduce side padding */
            padding-right: 1rem !important;      /* Reduce side padding */
            padding-bottom: 1rem !important;     /* Reduce bottom padding */
        }
        
        /* Remove excessive top margin from first element */
        .main .block-container > div:first-child {
            margin-top: 0 !important;
        }
        
        /* Compress Streamlit's header bar */
        header[data-testid="stHeader"] {
            height: 2.5rem !important;           /* Reduce header height */
        }
        
        /* 2. FIX HEADER SIZE ISSUES */
        /* Main headers (st.header) */
        .main h1 {
            font-size: 1.5rem !important;        /* Reduce from ~2.5rem */
            margin-top: 0.5rem !important;       /* Reduce top margin */
            margin-bottom: 0.75rem !important;   /* Reduce bottom margin */
            line-height: 1.2 !important;         /* Tighter line height */
        }
        
        /* Subheaders (st.subheader) */
        .main h2 {
            font-size: 1.25rem !important;       /* Reduce from ~2rem */
            margin-top: 0.4rem !important;       /* Reduce top margin */
            margin-bottom: 0.6rem !important;    /* Reduce bottom margin */
            line-height: 1.2 !important;         /* Tighter line height */
        }
        
        /* Smaller headers */
        .main h3 {
            font-size: 1.1rem !important;        /* Reduce size */
            margin-top: 0.3rem !important;       /* Reduce margin */
            margin-bottom: 0.5rem !important;    /* Reduce margin */
        }
        
        /* 3. SAFE CONTENT SPACING FIXES */
        /* Reduce excessive paragraph spacing */
        .main p {
            margin-bottom: 0.75rem !important;   /* Reduce from ~1rem */
        }
        
        /* Compress info boxes, warnings, etc. */
        .main .element-container {
            margin-bottom: 0.75rem !important;   /* Reduce spacing between elements */
        }
        
        /* Tighter divider spacing */
        .main hr {
            margin: 1rem 0 !important;           /* Reduce from ~1.5rem */
        }
        
        /* 4. SAFE BUTTON IMPROVEMENTS */
        /* Make buttons touch-friendly (44px minimum) */
        .main button {
            min-height: 2.75rem !important;      /* 44px touch target */
            font-size: 0.9rem !important;        /* Slightly smaller text */
        }
        
        /* 5. SAFE TABLE IMPROVEMENTS */
        /* Allow tables to scroll horizontally instead of breaking layout */
        .main .dataframe {
            overflow-x: auto !important;
            font-size: 0.85rem !important;       /* Smaller text for better fit */
        }
        
        /* 6. SAFE SIDEBAR HANDLING */
        /* Start with sidebar collapsed on mobile */
        .css-1d391kg {
            width: 0 !important;                 /* Hide sidebar initially */
        }
        
        /* 7. SAFE FORM IMPROVEMENTS */
        /* Better spacing for form elements */
        .main .stTextInput > div > div > input,
        .main .stSelectbox > div > div > div,
        .main .stDateInput > div > div > input,
        .main .stNumberInput > div > div > input {
            font-size: 1rem !important;          /* Prevent zoom on iOS */
        }
        
        /* 8. SAFE METRIC IMPROVEMENTS */
        /* Compress metrics slightly */
        .main [data-testid="metric-container"] {
            padding: 0.5rem !important;          /* Reduce padding */
        }
        
        .main [data-testid="metric-container"] [data-testid="metric-value"] {
            font-size: 1.5rem !important;        /* Reduce metric value size */
        }
        
        .main [data-testid="metric-container"] [data-testid="metric-label"] {
            font-size: 0.8rem !important;        /* Reduce metric label size */
        }
    }
    
    /* ===== SMALL MOBILE FIXES (max-width: 480px) ===== */
    @media (max-width: 480px) {
        
        /* Even more aggressive spacing for very small screens */
        .main .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* Smaller headers on tiny screens */
        .main h1 {
            font-size: 1.3rem !important;
        }
        
        .main h2 {
            font-size: 1.1rem !important;
        }
        
        /* Stack columns on very small screens */
        .main .row-widget.stHorizontal {
            flex-direction: column !important;
        }
        
        .main .row-widget.stHorizontal > div {
            width: 100% !important;
            margin-bottom: 0.5rem !important;
        }
    }
    
    /* ===== ACCESSIBILITY IMPROVEMENTS (ALL SCREENS) ===== */
    /* Better touch targets - safe for all screen sizes */
    .main button,
    .main .stSelectbox,
    .main .stTextInput input {
        min-height: 2.75rem !important;          /* 44px minimum touch target */
    }
    
    /* Prevent zoom on iOS form inputs - safe improvement */
    .main input,
    .main select,
    .main textarea {
        font-size: 1rem !important;              /* Prevents iOS zoom */
    }
    
    /* Better focus states for keyboard navigation - safe improvement */
    .main button:focus,
    .main input:focus,
    .main select:focus {
        outline: 2px solid #ff6b35 !important;   /* Streamlit orange */
        outline-offset: 2px !important;
    }
    
    </style>
    """
    
    st.markdown(mobile_css, unsafe_allow_html=True)


def apply_global_mobile_fixes():
    """
    Apply global mobile fixes to your Streamlit app
    Call this once in your main app file
    
    Usage:
        # At the top of main.py or your main app function
        from mobile_css import apply_global_mobile_fixes
        apply_global_mobile_fixes()
    """
    inject_global_mobile_css()


# Example integration
if __name__ == "__main__":
    # Example of how to integrate into your main app
    st.set_page_config(
        page_title="SeaLog",
        page_icon="",
        layout="wide",
        initial_sidebar_state="collapsed"  # Start collapsed on mobile
    )
    
    # Apply global mobile fixes
    apply_global_mobile_fixes()
    
    # Your existing app content
    st.header(" Crew List")
    st.write("This content will now be mobile-optimized automatically!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Crew", "12")
    with col2:
        st.metric("Officers", "4") 
    with col3:
        st.metric("Active", "12")
    
    st.button("Add New Crew Member", use_container_width=True)