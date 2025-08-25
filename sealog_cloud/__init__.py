"""
SeaLog Cloud Shared - Maritime logging and vessel management system
"""

__version__ = "0.1.3"
__author__ = "SeaLog"
__email__ = "admin@sealog.com"

# Lazy imports to avoid dependency issues during package installation
def get_core_utils():
    """Get core utilities with lazy import."""
    try:
        from .core.utils import init_database, init_session_state
        return init_database, init_session_state
    except ImportError as e:
        raise ImportError(f"Failed to import core utils. Install with all dependencies: pip install 'sealog-cloud-shared[postgresql]'. Error: {e}")

def get_db_manager():
    """Get database manager with lazy import."""
    try:
        from .database_manager import db_manager
        return db_manager
    except ImportError as e:
        raise ImportError(f"Failed to import database manager. Install with all dependencies: pip install 'sealog-cloud-shared[postgresql]'. Error: {e}")

def get_auth_functions():
    """Get authentication functions with lazy import."""
    try:
        from .authentication import check_persistent_login, login_page, check_payment_status
        return check_persistent_login, login_page, check_payment_status
    except ImportError as e:
        raise ImportError(f"Failed to import authentication functions. Install with all dependencies: pip install 'sealog-cloud-shared[postgresql]'. Error: {e}")

# Always use lazy loading to avoid import errors
__all__ = [
    "get_core_utils",
    "get_db_manager",
    "get_auth_functions",
]