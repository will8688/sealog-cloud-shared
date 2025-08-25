"""
Secure session persistence using temporary files
SECURITY: No data exposed in URLs or browser storage - uses secure server-side files
"""

import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
import tempfile

class SecureSessionManager:
    """Manages persistent sessions using secure temporary files"""
    
    def __init__(self):
        self.session_dir = os.path.join(tempfile.gettempdir(), "sealog_sessions")
        self.ensure_session_directory()
    
    def ensure_session_directory(self):
        """Ensure session directory exists with proper permissions"""
        try:
            if not os.path.exists(self.session_dir):
                os.makedirs(self.session_dir, mode=0o700)  # Only owner can access
        except OSError:
            # If we can't create the directory, fall back to session state only
            self.session_dir = None
    
    def get_browser_fingerprint(self) -> str:
        """Create a unique browser fingerprint for session identification"""
        # Use Streamlit's session info to create a consistent browser fingerprint
        session_id = getattr(st, '_get_session_id', lambda: 'default')()
        user_agent = st.context.headers.get('user-agent', 'unknown')
        
        # Create a hash of browser characteristics
        fingerprint_data = f"{session_id}:{user_agent}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def get_session_file_path(self, browser_fingerprint: str) -> str:
        """Get the file path for a specific browser's session"""
        if not self.session_dir:
            return None
        
        session_filename = f"session_{browser_fingerprint}.json"
        return os.path.join(self.session_dir, session_filename)
    
    def save_session(self, user_id: int, username: str, auth_token: str) -> bool:
        """Save session securely to file system"""
        try:
            if not self.session_dir:
                # Fall back to session state only
                st.session_state["persistent_user_id"] = user_id
                st.session_state["persistent_username"] = username
                st.session_state["persistent_auth_token"] = auth_token
                st.session_state["persistent_expires"] = (datetime.now() + timedelta(days=7)).isoformat()
                return True
            
            browser_fingerprint = self.get_browser_fingerprint()
            session_file = self.get_session_file_path(browser_fingerprint)
            
            if not session_file:
                return False
            
            session_data = {
                'user_id': user_id,
                'username': username,
                'auth_token': auth_token,
                'created': datetime.now().isoformat(),
                'expires': (datetime.now() + timedelta(days=7)).isoformat(),
                'browser_fingerprint': browser_fingerprint
            }
            
            # Write to temporary file first, then rename (atomic operation)
            temp_file = session_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Set restrictive permissions (owner only)
            os.chmod(temp_file, 0o600)
            
            # Atomic rename
            os.rename(temp_file, session_file)
            
            # Also store in session state for immediate access
            st.session_state["persistent_user_id"] = user_id
            st.session_state["persistent_username"] = username
            st.session_state["persistent_auth_token"] = auth_token
            
            return True
            
        except Exception as e:
            # Fall back to session state only
            st.session_state["persistent_user_id"] = user_id
            st.session_state["persistent_username"] = username
            st.session_state["persistent_auth_token"] = auth_token
            st.session_state["persistent_expires"] = (datetime.now() + timedelta(days=7)).isoformat()
            return True
    
    def load_session(self) -> Optional[Dict]:
        """Load session securely from file system"""
        try:
            # First check session state (fastest)
            if all(key in st.session_state for key in ["persistent_user_id", "persistent_username", "persistent_auth_token"]):
                return {
                    'user_id': st.session_state["persistent_user_id"],
                    'username': st.session_state["persistent_username"],
                    'auth_token': st.session_state["persistent_auth_token"],
                    'expires': st.session_state.get("persistent_expires", (datetime.now() + timedelta(days=7)).isoformat())
                }
            
            # Try to load from file if session state is empty
            if not self.session_dir:
                return None
            
            browser_fingerprint = self.get_browser_fingerprint()
            session_file = self.get_session_file_path(browser_fingerprint)
            
            if not session_file or not os.path.exists(session_file):
                return None
            
            # Check file age (delete if too old)
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(session_file))
            if file_age > timedelta(days=7):
                self.clear_session()
                return None
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Validate session hasn't expired
            if 'expires' in session_data:
                expires = datetime.fromisoformat(session_data['expires'])
                if expires < datetime.now():
                    self.clear_session()
                    return None
            
            # Validate browser fingerprint matches
            if session_data.get('browser_fingerprint') != browser_fingerprint:
                self.clear_session()
                return None
            
            # Store in session state for faster access next time
            st.session_state["persistent_user_id"] = session_data['user_id']
            st.session_state["persistent_username"] = session_data['username']
            st.session_state["persistent_auth_token"] = session_data['auth_token']
            st.session_state["persistent_expires"] = session_data['expires']
            
            return session_data
            
        except Exception:
            return None
    
    def clear_session(self):
        """Clear session from both file system and session state"""
        try:
            # Clear from session state
            keys_to_remove = [
                "persistent_user_id", "persistent_username", 
                "persistent_auth_token", "persistent_expires"
            ]
            for key in keys_to_remove:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Clear from file system
            if self.session_dir:
                browser_fingerprint = self.get_browser_fingerprint()
                session_file = self.get_session_file_path(browser_fingerprint)
                
                if session_file and os.path.exists(session_file):
                    os.remove(session_file)
            
        except Exception:
            pass
    
    def cleanup_expired_sessions(self):
        """Clean up expired session files (run periodically)"""
        try:
            if not self.session_dir or not os.path.exists(self.session_dir):
                return
            
            current_time = datetime.now()
            
            for filename in os.listdir(self.session_dir):
                if filename.startswith('session_') and filename.endswith('.json'):
                    file_path = os.path.join(self.session_dir, filename)
                    
                    try:
                        # Check file age
                        file_age = current_time - datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_age > timedelta(days=7):
                            os.remove(file_path)
                            continue
                        
                        # Check session expiration
                        with open(file_path, 'r') as f:
                            session_data = json.load(f)
                        
                        if 'expires' in session_data:
                            expires = datetime.fromisoformat(session_data['expires'])
                            if expires < current_time:
                                os.remove(file_path)
                    
                    except (OSError, json.JSONDecodeError, KeyError, ValueError):
                        # Remove corrupted files
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass
            
        except Exception:
            pass

# Global session manager instance
_session_manager = None

def get_session_manager() -> SecureSessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SecureSessionManager()
    return _session_manager

def save_secure_session(user_id: int, username: str, auth_token: str) -> bool:
    """Save session using the secure session manager"""
    manager = get_session_manager()
    return manager.save_session(user_id, username, auth_token)

def load_secure_session() -> Optional[Dict]:
    """Load session using the secure session manager"""
    manager = get_session_manager()
    return manager.load_session()

def clear_secure_session():
    """Clear session using the secure session manager"""
    manager = get_session_manager()
    manager.clear_session()

def initialize_secure_sessions():
    """Initialize the secure session system"""
    if 'secure_sessions_initialized' not in st.session_state:
        manager = get_session_manager()
        
        # Clean up expired sessions on initialization
        manager.cleanup_expired_sessions()
        
        st.session_state.secure_sessions_initialized = True