"""
SeaLog Cloud Shared - Maritime logging and vessel management system
"""

__version__ = "0.1.4"
__author__ = "SeaLog"
__email__ = "admin@sealog.com"

# Completely minimal implementation - no imports at package level
def get_core_utils():
    """Get core utilities with lazy import."""
    try:
        from .core.utils import init_database, init_session_state
        return init_database, init_session_state
    except Exception as e:
        raise ImportError(f"Failed to import core utils: {e}")

def get_db_manager():
    """Get database manager with lazy import."""
    try:
        from .database_manager import db_manager
        return db_manager
    except Exception as e:
        raise ImportError(f"Failed to import database manager: {e}")

def get_auth_functions():
    """Get authentication functions with lazy import."""
    try:
        from .authentication import check_persistent_login, login_page, check_payment_status
        return check_persistent_login, login_page, check_payment_status
    except Exception as e:
        raise ImportError(f"Failed to import authentication functions: {e}")

# Direct imports for convenience (when all deps available)
def __getattr__(name):
    """Dynamic attribute access for direct imports."""
    if name == 'db_manager':
        return get_db_manager()
    elif name == 'init_database':
        return get_core_utils()[0]
    elif name == 'init_session_state':
        return get_core_utils()[1]
    elif name == 'check_persistent_login':
        return get_auth_functions()[0]
    elif name == 'login_page':
        return get_auth_functions()[1]
    elif name == 'check_payment_status':
        return get_auth_functions()[2]
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "get_core_utils",
    "get_db_manager",
    "get_auth_functions",
]