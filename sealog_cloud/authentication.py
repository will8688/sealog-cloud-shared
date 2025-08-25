import hashlib
import secrets
import re
import json
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from database_manager import db_manager

def check_for_invitation_token():
    """Check if user arrived via invitation link and display invitation info"""
    try:
        # Check for invitation token in URL
        invitation_token = st.query_params.get('invitation_token')
        
        if not invitation_token:
            return False
        
        # Store in session state so it persists through login/registration
        st.session_state['pending_invitation_token'] = invitation_token
        
        # Import invitation service
        from tools.crew_management.services.invitation_service import InvitationService
        invitation_service = InvitationService()
        
        # Validate and get preview
        is_valid, invitation = invitation_service.validate_invitation_token(invitation_token)
        
        if is_valid:
            preview = invitation_service.get_invitation_preview(invitation_token)
            if preview:
                # Store preview for use after login
                st.session_state['invitation_preview'] = preview
                
                # Show invitation banner
                st.success(f"""
                🚢 **You've been invited to join {preview['vessel_name']}!**
                
                {f"**Position:** {preview['crew_member']['rank']}" if preview.get('crew_member') else ""}
                {f"**Invited by:** {preview.get('invited_by', 'Your Captain')}" if preview.get('invited_by') else ""}
                
                Please sign in or create an account to accept this invitation.
                """)
                
                # Show expiry warning if close
                if preview.get('days_until_expiry', 7) <= 2:
                    st.warning(f"⚠️ This invitation expires in {preview['days_until_expiry']} days!")
                
                return True
        else:
            st.error("❌ This invitation link is invalid or has expired.")
            # Clear the invalid token
            if 'pending_invitation_token' in st.session_state:
                del st.session_state['pending_invitation_token']
            # Remove from URL
            try:
                del st.query_params['invitation_token']
            except:
                pass
                
    except Exception as e:
        # Don't break the login flow if invitation check fails
        st.warning(f"Could not validate invitation: {str(e)}")
        
    return False


def handle_post_login_invitation():
    """Handle invitation acceptance after successful login"""
    try:
        # Check if we have a pending invitation
        if 'pending_invitation_token' not in st.session_state:
            return
        
        if 'user_id' not in st.session_state:
            return
        
        invitation_token = st.session_state['pending_invitation_token']
        user_id = st.session_state['user_id']
        
        # Show processing message
        with st.spinner("Processing your invitation..."):
            # Import services
            from tools.crew_management.services.invitation_service import InvitationService
            from tools.crew_management.services.crew_service import CrewService
            
            invitation_service = InvitationService()
            crew_service = CrewService()
            
            # Accept the invitation
            success, message, invitation_data = invitation_service.accept_invitation(
                invitation_token, 
                user_id
            )
            
            if success:
                st.success(f"✅ {message}")
                
                # Create assignment if needed
                if invitation_data and invitation_data.get('needs_assignment'):
                    assignment_id = crew_service.create_assignment_from_invitation(invitation_data)
                    
                    if assignment_id:
                        vessel_name = invitation_data.get('vessel_name', 'the vessel')
                        st.success(f"""
                        🚢 **Welcome aboard {vessel_name}!**
                        
                        You now have access to:
                        - Ship's Logbook entries
                        - View crew lists and schedules
                        - Make basic log entries
                        
                        Navigate to the **Crew List** to see your assignment and permissions.
                        """)
                        st.balloons()
                        
                        # Set a flag to redirect to crew list
                        st.session_state['redirect_to_crew'] = True
                
                # Clear invitation data
                del st.session_state['pending_invitation_token']
                if 'invitation_preview' in st.session_state:
                    del st.session_state['invitation_preview']
                
                # Clean up URL
                try:
                    del st.query_params['invitation_token']
                except:
                    pass
                    
            else:
                st.error(f"❌ {message}")
                # Clear the failed token
                if 'pending_invitation_token' in st.session_state:
                    del st.session_state['pending_invitation_token']
                    
    except Exception as e:
        st.error(f"Error processing invitation: {str(e)}")
        # Clear invitation data on error
        if 'pending_invitation_token' in st.session_state:
            del st.session_state['pending_invitation_token']
            
# Keep all your existing authentication functions but update database calls
def hash_password(password):
    """Hash password using SHA-256 (keeping existing method for compatibility)"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    # Check for common passwords (basic check)
    common_passwords = ['password', '123456', 'qwerty', 'abc123', 'password123']
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password"
    
    return True, "Password strength is good"

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def check_existing_user(username: str, email: str) -> tuple[bool, str]:
    """Check if username or email already exists"""
    try:
        result = db_manager.execute_query(
            'SELECT username, email FROM users WHERE username = ? OR email = ?', 
            (username, email), 
            fetch='one'
        )
        
        if result:
            if result['username'] == username:
                return False, "Username already exists"
            else:
                return False, "Email already exists"
        return True, "Available"
    except Exception as e:
        return False, f"Database error: {str(e)}"

def create_user(username, email, password):
    """Create new user account with enhanced validation"""
    # Validate inputs
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if not validate_email(email):
        return False, "Please enter a valid email address"
    
    is_strong, message = validate_password_strength(password)
    if not is_strong:
        return False, message
    
    # Check for existing users
    available, availability_message = check_existing_user(username, email)
    if not available:
        return False, availability_message
    
    try:
        password_hash = hash_password(password)
        db_manager.execute_query(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        return True, "Account created successfully"
    except Exception as e:
        if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e).lower():
            return False, "Username or email already exists"
        else:
            return False, f"Database error: {str(e)}"

def authenticate_user(username, password):
    """Authenticate user credentials"""
    try:
        password_hash = hash_password(password)
        user = db_manager.execute_query(
            'SELECT id, username, payment_expiry FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash),
            fetch='one'
        )
        
        if user:
            return {
                'id': user['id'],
                'username': user['username'],
                'payment_expiry': user['payment_expiry']
            }
        return None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

def check_payment_status(user_id):
    """Check if user has valid payment"""
    try:
        result = db_manager.execute_query(
            'SELECT subscription_status, subscription_end FROM users WHERE id = ?',
            (user_id,),
            fetch='one'
        )
        
        if result:
            # Check new Stripe subscription status first
            if result.get('subscription_status') == 'active':
                # Check if subscription hasn't expired
                if result.get('subscription_end'):
                    try:
                        if isinstance(result['subscription_end'], str):
                            end_date = datetime.fromisoformat(result['subscription_end'])
                        else:
                            end_date = result['subscription_end']
                        
                        if end_date > datetime.now():
                            return True
                    except:
                        # If there's an issue parsing the date, assume active
                        return True
                else:
                    # If no end date but status is active, assume active
                    return True
            
            # Fall back to old payment_expiry system for backward compatibility
            if result.get('payment_expiry'):
                payment_expiry = result['payment_expiry']
                
                # Handle both string dates (SQLite) and datetime objects (PostgreSQL)
                if isinstance(payment_expiry, str):
                    # SQLite returns strings - parse them
                    try:
                        # Try with microseconds first
                        expiry_date = datetime.strptime(payment_expiry, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        # Fall back to without microseconds
                        expiry_date = datetime.strptime(payment_expiry, '%Y-%m-%d %H:%M:%S')
                else:
                    # PostgreSQL returns datetime objects - use directly
                    expiry_date = payment_expiry
                
                return expiry_date > datetime.now()
        
        return False
    except Exception as e:
        st.error(f"Payment status check error: {e}")
        return False

def ensure_user_sessions_table():
    """Ensure user_sessions table exists with proper structure"""
    try:
        if db_manager.db_type == 'postgresql':
            # PostgreSQL version
            create_sql = """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    session_token TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    expires_date TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """
        else:
            # SQLite version
            create_sql = """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_token TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    expires_date TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """
        
        db_manager.execute_query(create_sql)
        return True
    except Exception as e:
        st.error(f"Could not create user_sessions table: {e}")
        return False

def check_persistent_login():
    """Check for session token in URL/cookies and auto-login"""
    try:
        # First try cookie-based authentication (preferred method)
        if load_cookie_session():
            return True
        
        # Fall back to URL parameter method (backward compatibility)
        query_params = st.query_params
        
        if 'st' in query_params:  # 'st' = session token
            session_token = query_params['st']
            
            # Ensure user_sessions table exists
            if not ensure_user_sessions_table():
                return False
            
            # Check if session token is valid and not expired
            # Handle different datetime formats for different databases
            if db_manager.db_type == 'postgresql':
                datetime_check = "us.expires_date > NOW()"
                query = f'''
                    SELECT us.user_id, u.username, us.expires_date 
                    FROM user_sessions us 
                    JOIN users u ON us.user_id = u.id 
                    WHERE us.session_token = %s AND {datetime_check}
                '''
                params = (session_token,)
            else:
                datetime_check = "us.expires_date > datetime('now')"
                query = f'''
                    SELECT us.user_id, u.username, us.expires_date 
                    FROM user_sessions us 
                    JOIN users u ON us.user_id = u.id 
                    WHERE us.session_token = ? AND {datetime_check}
                '''
                params = (session_token,)
            
            result = db_manager.execute_query(query, params, fetch='one')
            
            if result:
                user_id, username, expires_date = result['user_id'], result['username'], result['expires_date']
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_id = str(user_id)
                
                # Migrate to cookie-based session
                save_cookie_session(user_id, username)
                
                return True
            else:
                # Invalid or expired token, remove it from URL
                try:
                    del st.query_params['st']
                except:
                    pass
                
    except Exception as e:
        # Silent fail for session check, but log for debugging
        # st.error(f"Session check error: {e}")  # Uncomment for debugging
        pass
    
    return False

def create_session_token(user_id):
    """Create a new session token for the user"""
    session_token = secrets.token_urlsafe(32)
    expires_date = datetime.now() + timedelta(days=7)  # 7 days
    
    try:
        # Ensure user_sessions table exists
        if not ensure_user_sessions_table():
            return None
        
        # Clean up old sessions for this user
        if db_manager.db_type == 'postgresql':
            cleanup_query = 'DELETE FROM user_sessions WHERE user_id = %s OR expires_date < NOW()'
            params = (user_id,)
        else:
            cleanup_query = 'DELETE FROM user_sessions WHERE user_id = ? OR expires_date < datetime("now")'
            params = (user_id,)
        
        db_manager.execute_query(cleanup_query, params)
        
        # Insert new session with proper parameter binding
        if db_manager.db_type == 'postgresql':
            insert_query = '''
                INSERT INTO user_sessions (session_token, user_id, expires_date)
                VALUES (%s, %s, %s)
            '''
            insert_params = (session_token, user_id, expires_date)
        else:
            insert_query = '''
                INSERT INTO user_sessions (session_token, user_id, expires_date)
                VALUES (?, ?, ?)
            '''
            insert_params = (session_token, user_id, expires_date)
        
        db_manager.execute_query(insert_query, insert_params)
        
        return session_token
    except Exception as e:
        st.error(f"Session creation error: {e}")
        return None

def save_persistent_login(username, user_id):
    """Save login state using cookies (preferred) and session token (fallback)"""
    # Save cookie-based session (primary method)
    cookie_success = save_cookie_session(user_id, username)
    
    if not cookie_success:
        # Fall back to URL parameter method if cookies fail
        session_token = create_session_token(user_id)
        if session_token:
            # Add token to URL for persistence
            st.query_params['st'] = session_token

def clear_persistent_login():
    """Clear persistent login"""
    try:
        # Get current session token from URL (backward compatibility)
        if 'st' in st.query_params:
            session_token = st.query_params['st']
            
            # Remove from database with proper parameter binding
            if db_manager.db_type == 'postgresql':
                delete_query = 'DELETE FROM user_sessions WHERE session_token = %s'
                params = (session_token,)
            else:
                delete_query = 'DELETE FROM user_sessions WHERE session_token = ?'
                params = (session_token,)
            
            db_manager.execute_query(delete_query, params)
            
            # Remove from URL
            del st.query_params['st']
        
        # Also clear cookie-based session
        clear_cookie_session()
    except:
        pass

# NEW: Cookie-based session management functions
def set_cookie(name: str, value: str, expires_days: int = 7):
    """Set a cookie using improved cookie manager"""
    try:
        from cookie_manager import set_cookie_component
        set_cookie_component(name, value, expires_days)
        
        # Also store in session state for immediate access
        st.session_state[f"cookie_{name}"] = value
    except ImportError:
        # Fallback to basic JavaScript method
        expires_date = datetime.now() + timedelta(days=expires_days)
        expires_str = expires_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        cookie_script = f"""
        <script>
        document.cookie = "{name}={value}; expires={expires_str}; path=/; SameSite=Lax";
        console.log("Cookie set: {name}");
        </script>
        """
        st.markdown(cookie_script, unsafe_allow_html=True)
        st.session_state[f"cookie_{name}"] = value

def get_cookie(name: str) -> str:
    """Get cookie value using improved cookie manager"""
    try:
        # Check session state first (immediate access)
        cookie_key = f"cookie_{name}"
        if cookie_key in st.session_state:
            return st.session_state[cookie_key]
        
        # Try to get from cookie manager
        try:
            from cookie_manager import get_cookies_from_browser
            cookies = get_cookies_from_browser()
            if name in cookies:
                # Store in session state for next time
                st.session_state[cookie_key] = cookies[name]
                return cookies[name]
        except ImportError:
            pass
        
        # Check query params as fallback
        if f"cookie_{name}" in st.query_params:
            value = st.query_params[f"cookie_{name}"]
            st.session_state[cookie_key] = value
            return value
        
        return ""
    except:
        return ""

def delete_cookie(name: str):
    """Delete a cookie using improved cookie manager"""
    try:
        from cookie_manager import delete_cookie_component
        delete_cookie_component(name)
    except ImportError:
        # Fallback to basic JavaScript method
        cookie_script = f"""
        <script>
        document.cookie = "{name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax";
        console.log("Cookie deleted: {name}");
        </script>
        """
        st.markdown(cookie_script, unsafe_allow_html=True)
    
    # Remove from session state
    cookie_key = f"cookie_{name}"
    if cookie_key in st.session_state:
        del st.session_state[cookie_key]

def create_secure_session_data(user_id: int, username: str) -> str:
    """Create secure session data with encryption"""
    session_data = {
        'user_id': user_id,
        'username': username,
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(days=7)).isoformat()
    }
    
    # Convert to JSON and encode
    json_data = json.dumps(session_data)
    encoded_data = base64.b64encode(json_data.encode()).decode()
    
    # Add a simple checksum for integrity
    checksum = hashlib.md5(f"{encoded_data}:{user_id}".encode()).hexdigest()[:8]
    
    return f"{encoded_data}.{checksum}"

def validate_session_data(session_token: str) -> Optional[Dict[str, Any]]:
    """Validate and decode session data"""
    try:
        if '.' not in session_token:
            return None
        
        encoded_data, checksum = session_token.rsplit('.', 1)
        
        # Decode the data
        json_data = base64.b64decode(encoded_data.encode()).decode()
        session_data = json.loads(json_data)
        
        # Validate checksum
        expected_checksum = hashlib.md5(f"{encoded_data}:{session_data['user_id']}".encode()).hexdigest()[:8]
        if checksum != expected_checksum:
            return None
        
        # Check expiration
        expires = datetime.fromisoformat(session_data['expires'])
        if expires < datetime.now():
            return None
        
        return session_data
    except:
        return None

def save_cookie_session(user_id: int, username: str):
    """Save session using secure file-based persistence"""
    try:
        # Create database session token for additional security
        db_session_token = create_session_token(user_id)
        if not db_session_token:
            return False
        
        # Use the secure session manager (no URL parameters, no browser storage exposure)
        try:
            from secure_sessions import save_secure_session
            return save_secure_session(user_id, username, db_session_token)
        except ImportError:
            # Fallback to session state only (still secure, just not persistent)
            st.session_state["persistent_user_id"] = user_id
            st.session_state["persistent_username"] = username
            st.session_state["persistent_auth_token"] = db_session_token
            st.session_state["persistent_expires"] = (datetime.now() + timedelta(days=7)).isoformat()
            return True
        
    except Exception as e:
        st.error(f"Error saving session: {e}")
        return False

def load_cookie_session() -> bool:
    """Load session securely (no URL parameters, no browser storage exposure)"""
    try:
        # Load from secure session manager
        try:
            from secure_sessions import load_secure_session
            session_data = load_secure_session()
        except ImportError:
            # Fallback to session state check
            if "persistent_user_id" in st.session_state and "persistent_auth_token" in st.session_state:
                session_data = {
                    'user_id': st.session_state["persistent_user_id"],
                    'username': st.session_state["persistent_username"],
                    'auth_token': st.session_state["persistent_auth_token"],
                    'expires': st.session_state.get("persistent_expires")
                }
            else:
                return False
        
        if not session_data:
            return False
        
        # Validate session hasn't expired
        if 'expires' in session_data:
            try:
                expires = datetime.fromisoformat(session_data['expires'])
                if expires < datetime.now():
                    # Session expired, clear it
                    clear_cookie_session()
                    return False
            except (ValueError, TypeError):
                # Invalid expiration format, clear session
                clear_cookie_session()
                return False
        
        # Verify database token is still valid
        auth_token = session_data['auth_token']
        
        if db_manager.db_type == 'postgresql':
            query = '''
                SELECT user_id FROM user_sessions 
                WHERE session_token = %s AND expires_date > NOW()
            '''
            params = (auth_token,)
        else:
            query = '''
                SELECT user_id FROM user_sessions 
                WHERE session_token = ? AND expires_date > datetime('now')
            '''
            params = (auth_token,)
        
        result = db_manager.execute_query(query, params, fetch='one')
        
        if result and result['user_id'] == session_data['user_id']:
            # Valid session found - restore authentication
            st.session_state.authenticated = True
            st.session_state.username = session_data['username']
            st.session_state.user_id = str(session_data['user_id'])
            return True
        else:
            # Invalid database token, clear session
            clear_cookie_session()
            return False
        
    except Exception:
        # Silent fail for session check
        return False

def clear_cookie_session():
    """Clear all session data securely"""
    try:
        # Get current token to remove from database
        auth_token = None
        
        # Try secure session manager first
        try:
            from secure_sessions import load_secure_session, clear_secure_session
            session_data = load_secure_session()
            if session_data:
                auth_token = session_data.get('auth_token')
            clear_secure_session()
        except ImportError:
            # Fallback to session state
            auth_token = st.session_state.get("persistent_auth_token")
            
            # Clear session state
            keys_to_remove = [
                "persistent_user_id", "persistent_username",
                "persistent_auth_token", "persistent_expires"
            ]
            for key in keys_to_remove:
                if key in st.session_state:
                    del st.session_state[key]
        
        # Remove token from database if we have one
        if auth_token:
            if db_manager.db_type == 'postgresql':
                delete_query = 'DELETE FROM user_sessions WHERE session_token = %s'
                params = (auth_token,)
            else:
                delete_query = 'DELETE FROM user_sessions WHERE session_token = ?'
                params = (auth_token,)
            
            db_manager.execute_query(delete_query, params)
                
    except:
        pass

def render_tool_showcase():
    """Render the tool showcase panel"""
    # Import styling functions
    from styling import render_auth_header
    
    # Use CSS classes instead of inline styles
    st.markdown('<div class="category-header"> Essential Logbooks - Core Maritime Documentation</div>', unsafe_allow_html=True)
    
    # Profile
    with st.expander(" **Profile** - Employment Ready", expanded=False):
        st.markdown("""
        **Paper seamans book → Digital professional profile.**

        Your profile is a digital version of your Seamans book. Record your information and output a professional pdf to hand to employers.
        
         Digital seamans book with professional PDF export  
         Medical records tracking (ENG1, vaccinations, eyesight)  
         Expiry alerts and compliance warnings  
         Multiple export formats for employers
        """)
    
    # Crew Logbook
    with st.expander(" **Crew Logbook** - Auto Sea Miles", expanded=False):
        st.markdown("""
        **Manual sea time tracking → Automated calculations**

        You crew logbook provides tools for you to track you miles and sea days in just a few input fields.
        
         Smart distance calculation between ports  
         Sea time and sea miles tracking  
         Professional employment records  
         Manual override for accuracy
        """)
    
    # Ships Logbook
    with st.expander(" **Ships Logbook** - 3-in-1 Platform", expanded=False):
        st.markdown("""
        **Multiple paper logs → Unified digital system**

        Your Logbook online with professional PDF output for keeping records onboard. Assign your crew members and track trends digitally to see your voyage from a new perspective.
        
         Navigation, Engine & Radio logs combined  
         Crew assignment and collaboration  
         Trend analysis and voyage insights  
         MCA compliant PDF exports
        
        *Professional PDF exports with premium*
        """)
    
    # Hours of Rest
    with st.expander("**Hours of Rest** - STCW Compliant", expanded=False):
        st.markdown("""
        **Compliance stress → Automated validation**

        Track your hours of rest and get flags for non compliance. Export the data and give it to the captain to be kept on record alongside the other crew.
        
         Real-time compliance checking  
         Violation alerts and prevention  
         Professional certification exports  
         Crew management for masters
        """)
    
    st.markdown('<div class="category-header"> Operations & Safety - Professional Maritime Tools</div>', unsafe_allow_html=True)
    
    # Risk Assessment
    with st.expander(" **Risk Assessment** - MCA Compliant", expanded=False):
        st.markdown("""
        **Paper risk forms → Professional digital assessments**

        Finally a tool that outputs a professional MCA compliant pdf for your records or for the insurance company.
        
         5x5 risk matrix methodology  
         Professional PDF suitable for inspections  
         Environmental conditions tracking  
         Review and update workflow
        
        *Professional PDFs available with premium*
        """)
    
    # Watch Scheduler
    with st.expander(" **Watch Scheduler** - STCW Ready", expanded=False):
        st.markdown("""
        **Manual roster planning → Automated scheduling**

        In just a few simple entries you can output the watch schedule for the entire trip. Send as a pdf or print to display on the wall.
        
         Solo and dual watch patterns  
         Crew workload distribution  
         Rest period compliance built-in  
         PDF schedules for bridge display
        
        *Create unlimited schedules - Export PDFs with premium*
        """)
    
    # Engine Room Log
    with st.expander(" **Engine Room Log** - MCA 13-Section", expanded=False):
        st.markdown("""
        **Paper engine logs → Digital 13-section system**

        The 13 step engine room log is MCA compliant and allows for dashboard, analytics and notifications to simply monitor and be alerted of any abnormalities.
        
         Complete MCA compliant structure  
         Performance charts and analytics  
         Maintenance tracking integration  
         MARPOL environmental compliance
        
        *Advanced analytics and PDF exports with premium*
        """)
    
    # Radio Log
    with st.expander(" **Radio Log** - GMDSS Ready", expanded=False):
        st.markdown("""
        **Manual radio records → GMDSS compliant system**

        Record your radio communications digitally and output in an MCA compliant pdf format.
        
         Equipment testing scheduler  
         International station database  
         Incident reporting workflow  
         Compliance monitoring dashboard
        
        *Full compliance reporting with premium*
        """)
    
    st.markdown('<div class="category-header"> Business Tools - Efficiency & Compliance</div>', unsafe_allow_html=True)
    
    # Crew List (moved first)
    with st.expander(" **Crew List** - Team Ready", expanded=False):
        st.markdown("""
        **Paper crew management → Digital collaboration**

        The digital crew list not only serves to produce a professional pdf output but also assigns your crew permissions to fill out the logbooks for the vessel.
        
         Professional crew list PDFs  
         Logbook access permissions  
         Vessel assignment management  
         Crew qualification tracking
        
        *Manage your crew digitally - Professional outputs with premium*
        """)
    
    # Country Log
    with st.expander(" **Country Log (Tax)** - Tax Ready", expanded=False):
        st.markdown("""
        **Tax time nightmare → Automated residency tracking**

        This tool will save you hours, maybe even days when it comes to tax time. Record your movements with 3 easy form fields or import from your calendar to receive a detailed breakdown of the countries and days you've been there, with tax implications for each.
        
         Movement tracking with smart calculations  
         183-day rule and substantial presence alerts  
         Multi-country compliance checking  
         Accountant-ready reports
        
        *Free tier: 5 movements - Save hours at tax time*
        """)
    
    # Fuel Burn Calculator
    with st.expander(" **Fuel Burn Calculator** - Passage Planner", expanded=False):
        st.markdown("""
        **Passage planning guesswork → Accurate fuel planning**

        A simple tool to do some key passage planning.
        
         Multi-engine and generator calculations  
         Distance auto-calculation between ports  
         Cost estimation and reserves  
         Multiple unit support (L, UK gal, US gal)
        
        *Free calculations - Advanced planning tools available*
        """)
    
    # Conversion Tools
    with st.expander(" **Conversion Tools** - Galley + Engine", expanded=False):
        st.markdown("""
        **Mixed metric/imperial confusion → Instant conversions**
        
        Take away the pain of mixed Metric and Imperial onboard with our simple conversion tools (Galley and Deck).

         Galley conversions (recipes, temperatures)  
         Engine room conversions (pressure, power, fuel)  
         Automatic logging for compliance  
         Professional calculation history
        
        *Unlimited conversions - Logging and reports with premium*
        """)

# Update the enhanced_login_page function to include invitation checking
def enhanced_login_page():
    """Enhanced login page with tool showcase and invitation handling"""
    # Import styling functions
    from styling import render_auth_header, render_auth_value_props, render_auth_cta_section
    
    # CHECK FOR INVITATION TOKEN FIRST
    has_invitation = check_for_invitation_token()
    
    # Page header using styled function
    st.markdown(render_auth_header(), unsafe_allow_html=True)
    
    # Create two columns: Login (left) and Tool showcase (right)
    # If has invitation, make login column slightly wider
    if has_invitation:
        col1, col2 = st.columns([2.5, 2.5])
    else:
        col1, col2 = st.columns([2, 3])
    
    with col1:
        # Use CSS class for form container
        
        
        st.markdown("## Get Started")
        
        # Add tabs for login/register
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            st.markdown("### Welcome Back")
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                remember_me = st.checkbox("Keep me logged in", value=True)
                
                submit_button = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                
                if submit_button:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        user = authenticate_user(username, password)
                        
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.username = user['username']
                            st.session_state.user_id = str(user['id'])
                            
                            if remember_me:
                                save_persistent_login(user['username'], user['id'])
                            
                            st.success("Login successful!")
                            
                            # HANDLE PENDING INVITATION
                            handle_post_login_invitation()
                            
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
            
            # Help text
            st.markdown("---")
            st.markdown("**Need help?** Contact support for assistance.")
            
        with tab2:
            st.markdown("### Join Maritime Professionals")
            
            # If has invitation, show special message
            if has_invitation and 'invitation_preview' in st.session_state:
                preview = st.session_state['invitation_preview']
                if preview.get('crew_member'):
                    st.info(f"📝 Creating an account for **{preview['crew_member'].get('name', 'your position')}**")
            
            with st.form("register_form"):
                new_username = st.text_input("Username", placeholder="Choose a username (min 3 characters)")
                new_email = st.text_input("Email", placeholder="Enter your email address")
                new_password = st.text_input("Password", type="password", placeholder="Create a strong password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                # Password requirements
                st.markdown("""
                **Password Requirements:**
                - At least 8 characters long
                - Include uppercase and lowercase letters
                - Include at least one number
                - Avoid common passwords
                """)
                
                submit_button = st.form_submit_button("Create Free Account", use_container_width=True, type="primary")
                
                if submit_button:
                    if new_password != confirm_password:
                        st.error("Passwords don't match")
                    else:
                        success, message = create_user(new_username, new_email, new_password)
                        
                        if success:
                            # Automatically log in the new user
                            user = authenticate_user(new_username, new_password)
                            if user:
                                st.session_state.authenticated = True
                                st.session_state.username = user['username']
                                st.session_state.user_id = str(user['id'])
                                
                                # Save persistent login
                                save_persistent_login(user['username'], user['id'])
                                
                                st.success("Account created successfully! Welcome to Sea Log!")
                                
                                # HANDLE PENDING INVITATION
                                handle_post_login_invitation()
                                
                                st.balloons()
                                st.rerun()
                            else:
                                st.success("Account created successfully! Please sign in with your new credentials.")
                        else:
                            st.error(message)
        
        # Value proposition using styled function
        st.markdown(render_auth_value_props(), unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close auth-form-container
    
    with col2:
        # If has invitation, show vessel info instead of full tool showcase
        if has_invitation and 'invitation_preview' in st.session_state:
            st.markdown('<div class="tool-showcase">', unsafe_allow_html=True)
            
            preview = st.session_state['invitation_preview']
            
            st.markdown(f"## 🚢 Join {preview['vessel_name']}")
            st.markdown("*Accept your invitation to start collaborating*")
            
            st.info(f"""
            **What happens next:**
            
            1. **Sign in or create account** - Use your existing account or create a new one
            2. **Automatic assignment** - You'll be linked to your crew position
            3. **Access granted** - Start making log entries immediately
            4. **Collaborate** - Work with your crew on vessel documentation
            
            **Your access will include:**
            - View and make entries in ship's logs
            - Access crew lists and schedules  
            - Collaborate on vessel documentation
            - Receive important vessel notifications
            """)
            
            # Show some key features
            st.markdown("### 🌟 Key Platform Features")
            st.markdown("""
            - **Digital Logbooks** - Navigation, Engine & Radio logs
            - **Crew Management** - Assignments and permissions
            - **Compliance Tools** - MCA compliant documentation
            - **Professional PDFs** - Export for inspections
            """)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Normal tool showcase
            st.markdown('<div class="tool-showcase">', unsafe_allow_html=True)
            
            st.markdown("## What's Included")
            st.markdown("*Discover the complete maritime documentation suite*")
            
            # Render tool showcase
            render_tool_showcase()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Call to action using styled function
        st.markdown(render_auth_cta_section(), unsafe_allow_html=True)

# Keep the old function name for compatibility
def login_page():
    """Wrapper for backward compatibility"""
    enhanced_login_page()