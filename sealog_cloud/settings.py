import streamlit as st

# Import database manager
from database_manager import db_manager

def render_settings():
    

    # Admin access button
    st.subheader(" Administrative Tools")

    if st.button(" Admin Panel", use_container_width=True, type="secondary"):
        # Set both session state and query params before rerun
        st.session_state.current_tool = "admin"
        st.query_params['route'] = "admin"
        # Clear any pending states that might cause extra reruns
        if 'show_admin_login' in st.session_state:
            del st.session_state.show_admin_login
        st.rerun()

def render_theme_settings():
    """Render the theme selection settings"""
    from styling import AVAILABLE_THEMES, load_user_theme, save_user_theme
    
    current_theme = load_user_theme()
    
    # Just the selectbox, no extra titles
    theme_options = {key: config["name"] for key, config in AVAILABLE_THEMES.items()}
    
    selected_theme = st.selectbox(
        "Theme:",
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(current_theme),
    )
    
    # Only show preview if naval_night is selected
    if selected_theme == 'naval_night':
        st.markdown("""
        <div class="naval-panel">
            <div class="naval-warning"> BRIDGE WATCH ACTIVE </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Apply theme change
    if selected_theme != current_theme:
        save_user_theme(selected_theme)
        st.success(f" Theme changed to {theme_options[selected_theme]}")
        st.rerun()