"""
SeaLog Cloud Shared - Maritime logging and vessel management system
"""

__version__ = "0.1.1"
__author__ = "SeaLog"
__email__ = "admin@sealog.com"

from .core.utils import init_database, init_session_state
from .database_manager import db_manager
from .authentication import check_persistent_login, login_page, check_payment_status

__all__ = [
    "init_database",
    "init_session_state", 
    "db_manager",
    "check_persistent_login",
    "login_page",
    "check_payment_status",
]