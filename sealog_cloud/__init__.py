"""
SeaLog Cloud Shared - Maritime logging and vessel management system
"""

__version__ = "0.1.2"
__author__ = "SeaLog"
__email__ = "admin@sealog.com"

# Lazy imports to avoid dependency issues during package installation
def get_core_utils():
    """Get core utilities with lazy import."""
    from .core.utils import init_database, init_session_state
    return init_database, init_session_state

def get_db_manager():
    """Get database manager with lazy import."""
    from .database_manager import db_manager
    return db_manager

def get_auth_functions():
    """Get authentication functions with lazy import."""
    from .authentication import check_persistent_login, login_page, check_payment_status
    return check_persistent_login, login_page, check_payment_status

# Always use lazy loading to avoid import errors
__all__ = [
    "get_core_utils",
    "get_db_manager",
    "get_auth_functions",
]