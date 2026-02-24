# Feature Deep Dive: Authentication & Security System

## Overview

This deep dive covers the comprehensive authentication and security system implemented in the BPC Dashboard. You'll learn about session management, cookie-based persistence, security hardening, and audit logging patterns.

**What You'll Learn:**
- Session isolation and cookie management
- Authentication flow with Supabase
- Token refresh and validation
- Security hardening patterns
- Audit logging implementation
- Email notification system

**Difficulty:** Advanced
**Time:** 60-90 minutes

---

## The Security Challenge

### Requirements

Build an authentication system that:
1. Prevents session bleeding between users (CRITICAL)
2. Persists sessions across page refreshes
3. Validates sessions on every request
4. Logs security events for auditing
5. Notifies users of login activity
6. Handles token expiration gracefully

### The Problem: Global State in Streamlit

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT SERVER                      │
│                                                          │
│    User A logs in                                        │
│         ↓                                                │
│    Global cookie_manager = CookieManager()  ← SHARED!   │
│         ↓                                                │
│    User B loads page                                     │
│         ↓                                                │
│    cookie_manager.get('session') → Returns User A's!    │
│                                                          │
│    ⚠️ SESSION BLEEDING - User B sees User A's data!     │
└─────────────────────────────────────────────────────────┘
```

**This was a critical security vulnerability** that was fixed by moving to per-session cookie managers.

---

## Core Architecture

### File Structure

```
shared/
├── auth_utils.py              # Main authentication logic (1,081 lines)
├── supabase_connection.py     # Supabase client management
└── email_notifications.py     # Login notification emails (130 lines)

pages/auth/
├── login.py                   # Login page UI
├── forgot_password.py         # Password reset request
├── reset_password.py          # Password reset completion
└── set_password.py            # Initial password setup
```

### Session State Structure

```python
# Authentication state stored in st.session_state
st.session_state = {
    # Core auth
    'user': {...},              # Supabase user object
    'user_profile': {...},      # Profile from user_profiles table
    'authenticated': True,

    # Tokens
    'access_token': 'eyJ...',   # JWT access token (1 hour)
    'refresh_token': 'abc...',  # Refresh token (24 hours)

    # Per-user cookie manager (CRITICAL for security)
    'cookie_manager': CookieManager(),

    # Tracking
    'ip_address': '123.45.67.89',
    'login_notification_sent': True,
}
```

---

## Authentication Flow

### Complete Login Flow

```
User enters credentials
        ↓
login_user(email, password)
        ↓
┌───────────────────────────────────────────────────────────┐
│ 1. Sign in with Supabase Auth                             │
│    supabase.auth.sign_in_with_password(...)               │
│                                                           │
│ 2. Save tokens to cookies (per-session cookie manager)    │
│    cookie_manager.set('access_token', token, max_age=3600)│
│                                                           │
│ 3. Load user profile from database                        │
│    SELECT * FROM user_profiles WHERE id = user_id         │
│    ↓                                                      │
│    ⚠️ VALIDATE: profile.id == authenticated user.id      │
│                                                           │
│ 4. Send login notification email                          │
│    send_login_notification(email, ip_address)             │
│                                                           │
│ 5. Log audit event                                        │
│    log_audit_event('login', user_id, company_id, ip)      │
│                                                           │
│ 6. Update session state                                   │
│    st.session_state.authenticated = True                  │
└───────────────────────────────────────────────────────────┘
        ↓
    Page reload → Dashboard
```

### Implementation

```python
# File: shared/auth_utils.py

def login_user(email: str, password: str) -> tuple[bool, str]:
    """
    Authenticate user and establish session.

    Returns:
        (success: bool, message: str)
    """
    try:
        # Get fresh Supabase client (never cached globally!)
        supabase = get_supabase_client()

        # Attempt authentication
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        user = response.user
        session = response.session

        if not user or not session:
            return False, "Invalid credentials"

        # Store tokens in session state
        st.session_state.user = user
        st.session_state.access_token = session.access_token
        st.session_state.refresh_token = session.refresh_token

        # Get per-session cookie manager (CRITICAL!)
        cookie_manager = get_cookie_manager()

        # Save to cookies for persistence
        cookie_manager.set('access_token', session.access_token, max_age=3600)
        cookie_manager.set('refresh_token', session.refresh_token, max_age=86400)

        # Load and validate user profile
        profile_loaded = load_user_profile(user.id, show_error=True)

        if not profile_loaded:
            return False, "Failed to load user profile"

        # SECURITY: Validate profile belongs to this user
        if st.session_state.user_profile.get('id') != user.id:
            clear_session()
            return False, "Profile mismatch detected"

        # Send email notification (non-blocking)
        try:
            send_login_notification(email, get_client_ip())
        except Exception:
            pass  # Don't fail login if email fails

        # Log audit event
        log_audit_event(
            action='login',
            user_id=user.id,
            resource='auth',
            company_id=get_user_company_id(),
            metadata={'ip_address': get_client_ip()}
        )

        st.session_state.authenticated = True
        return True, "Login successful"

    except Exception as e:
        # Handle Streamlit widget conflicts separately
        if 'widget' in str(e).lower():
            return False, "Please try again"

        log_audit_event(
            action='failed_login',
            metadata={'email': email, 'error': str(e)}
        )
        return False, "Authentication failed"
```

---

## Session Persistence & Recovery

### The Challenge

Streamlit pages reload on every interaction. Without persistence:

```
User logs in → Page reloads → User logged out!
```

### Solution: Cookie-Based Persistence

```
┌────────────────────────────────────────────────────────┐
│                   Page Load Sequence                    │
├────────────────────────────────────────────────────────┤
│                                                         │
│  1. require_auth() called at page start                 │
│           ↓                                             │
│  2. Check session state: authenticated?                 │
│           ↓ No                                          │
│  3. attempt_session_recovery()                          │
│           ↓                                             │
│  4. Read cookies (access_token, refresh_token)          │
│           ↓                                             │
│  5. Validate tokens with Supabase                       │
│           ↓                                             │
│  6. Restore session state                               │
│           ↓                                             │
│  7. Continue to protected content                       │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### Implementation

```python
def attempt_session_recovery() -> bool:
    """
    Attempt to restore session from cookies.
    Called on every page load when not authenticated.

    Returns:
        True if session restored, False otherwise
    """
    cookie_manager = get_cookie_manager()

    # Read tokens from cookies
    access_token = cookie_manager.get('access_token')
    refresh_token = cookie_manager.get('refresh_token')

    if not access_token or not refresh_token:
        return False

    # Check if access token is expired
    if is_token_expired(access_token, buffer_minutes=5):
        # Try to refresh
        new_token = refresh_access_token(refresh_token)
        if not new_token:
            clear_cookies()
            return False
        access_token = new_token

    # Validate with Supabase
    try:
        supabase = get_supabase_client()
        supabase.auth.set_session(access_token, refresh_token)
        user = supabase.auth.get_user()

        if not user:
            clear_session()
            return False

        # Restore session state
        st.session_state.user = user.user
        st.session_state.access_token = access_token
        st.session_state.refresh_token = refresh_token

        # Load profile
        load_user_profile(user.user.id)

        # SECURITY: Validate cookie/session consistency
        if not validate_session_consistency():
            clear_session()
            return False

        st.session_state.authenticated = True

        # Send recovery notification (first time only)
        if not st.session_state.get('recovery_notification_sent'):
            send_login_notification(user.user.email, get_client_ip())
            st.session_state.recovery_notification_sent = True

        return True

    except Exception:
        clear_session()
        return False
```

---

## Security Hardening: Cookie Validation

### The Critical Security Fix

```python
def validate_session_consistency() -> bool:
    """
    CRITICAL: Validate that cookies match session state.
    Runs on EVERY request to detect session hijacking.

    Scenarios:
    1. Cookie exists but session doesn't match → CLEAR BOTH
    2. Cookie exists but no session user → CLEAR BOTH
    3. Session exists but no cookie → CLEAR BOTH
    """
    cookie_manager = get_cookie_manager()

    cookie_token = cookie_manager.get('access_token')
    session_token = st.session_state.get('access_token')
    session_user = st.session_state.get('user')

    # Case 1: Cookie exists but session token doesn't match
    if cookie_token and session_token and cookie_token != session_token:
        logger.warning("Session mismatch detected - clearing session")
        return False

    # Case 2: Cookie exists but no session user
    if cookie_token and not session_user:
        logger.warning("Cookie without session user - clearing")
        return False

    # Case 3: Session exists but no cookie (cookie was cleared/expired)
    if session_user and not cookie_token:
        logger.warning("Session without cookie - clearing")
        return False

    return True
```

### Per-Session Cookie Manager

```python
def get_cookie_manager():
    """
    Get per-session cookie manager.
    CRITICAL: Never use global cookie manager!

    Each user session gets its own cookie manager instance
    stored in st.session_state, ensuring isolation.
    """
    if 'cookie_manager' not in st.session_state:
        # Create new instance for this session
        from extra_streamlit_components import CookieManager
        st.session_state.cookie_manager = CookieManager()

    return st.session_state.cookie_manager
```

**Why This Matters:**

```
❌ WRONG (Vulnerable):
cookie_manager = CookieManager()  # Global - shared between users!

✅ CORRECT (Secure):
cookie_manager = st.session_state.get('cookie_manager')  # Per-session
```

---

## Token Management

### JWT Token Validation

```python
def is_token_expired(token: str, buffer_minutes: int = 5) -> bool:
    """
    Check if JWT token is expired or will expire soon.

    Args:
        token: JWT access token
        buffer_minutes: Minutes before expiry to consider "expired"

    Returns:
        True if expired or expiring soon
    """
    try:
        import jwt

        # Decode without verification (just reading claims)
        payload = jwt.decode(token, options={"verify_signature": False})

        exp_timestamp = payload.get('exp')
        if not exp_timestamp:
            return True

        # Check with buffer
        from datetime import datetime, timedelta
        expiry = datetime.fromtimestamp(exp_timestamp)
        buffer = timedelta(minutes=buffer_minutes)

        return datetime.now() >= (expiry - buffer)

    except Exception:
        return True  # Assume expired if can't parse
```

### Token Refresh

```python
def refresh_access_token(refresh_token: str) -> str | None:
    """
    Refresh expired access token using refresh token.

    Returns:
        New access token or None if refresh failed
    """
    try:
        supabase = get_supabase_client()
        response = supabase.auth.refresh_session(refresh_token)

        if response.session:
            new_access_token = response.session.access_token
            new_refresh_token = response.session.refresh_token

            # Update cookies
            cookie_manager = get_cookie_manager()
            cookie_manager.set('access_token', new_access_token, max_age=3600)
            cookie_manager.set('refresh_token', new_refresh_token, max_age=86400)

            # Update session state
            st.session_state.access_token = new_access_token
            st.session_state.refresh_token = new_refresh_token

            return new_access_token

    except Exception as e:
        logger.error(f"Token refresh failed: {e}")

    return None
```

---

## Role-Based Access Control

### Authorization Decorators

```python
def require_auth():
    """
    Page-level authentication gatekeeper.
    Call at the start of every protected page.

    Usage:
        def company_page():
            require_auth()  # Must be first!
            # ... rest of page
    """
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Validate existing session
    if st.session_state.authenticated:
        if not validate_session_consistency():
            clear_session()

    # Try to recover from cookies if not authenticated
    if not st.session_state.authenticated:
        if not attempt_session_recovery():
            show_login_page()
            st.stop()  # Halt execution


def require_role(required_role: str):
    """
    Require specific role for page access.

    Args:
        required_role: 'super_admin' or 'company_user'
    """
    require_auth()  # First ensure authenticated

    user_role = st.session_state.get('user_profile', {}).get('role')

    if user_role != required_role:
        st.error("You don't have permission to access this page.")
        st.stop()
```

### Helper Functions

```python
def is_super_admin() -> bool:
    """Check if current user is super admin."""
    profile = st.session_state.get('user_profile', {})
    return profile.get('role') == 'super_admin'


def can_upload_data() -> bool:
    """Check if current user can upload data."""
    profile = st.session_state.get('user_profile', {})
    return profile.get('can_upload_data', False) or is_super_admin()


def get_user_company_id() -> str | None:
    """Get current user's company ID."""
    profile = st.session_state.get('user_profile', {})
    return profile.get('company_id')


def get_user_company_name() -> str | None:
    """Get current user's company name."""
    profile = st.session_state.get('user_profile', {})
    return profile.get('company_name')
```

---

## Audit Logging

### Implementation

```python
def log_audit_event(
    action: str,
    user_id: str = None,
    resource: str = None,
    company_id: str = None,
    metadata: dict = None
):
    """
    Log security event to audit table.

    Args:
        action: Event type ('login', 'logout', 'failed_login',
                'upload_data', 'create_user', 'edit_permissions')
        user_id: User who performed action
        resource: Resource affected
        company_id: Company context
        metadata: Additional JSON metadata
    """
    try:
        # Use admin client to bypass RLS
        from shared.supabase_connection import get_admin_client
        admin = get_admin_client()

        # Get IP address
        ip_address = get_client_ip()

        # Insert audit record
        admin.table('audit_logs').insert({
            'user_id': user_id or st.session_state.get('user', {}).get('id'),
            'action': action,
            'resource': resource,
            'company_id': company_id or get_user_company_id(),
            'ip_address': ip_address,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }).execute()

    except Exception as e:
        # Non-fatal - log but don't fail the operation
        logger.error(f"Failed to log audit event: {e}")
```

### IP Address Capture

```python
def get_client_ip() -> str:
    """
    Get client's public IP address.
    Uses ipify.org API (cached in session).
    """
    # Return cached IP if available
    if 'ip_address' in st.session_state:
        return st.session_state.ip_address

    try:
        import requests
        response = requests.get('https://api.ipify.org', timeout=5)
        ip = response.text
        st.session_state.ip_address = ip
        return ip
    except Exception:
        return 'unknown'
```

---

## Email Notifications

### Login Notification

```python
# File: shared/email_notifications.py

def send_login_notification(email: str, ip_address: str):
    """
    Send email notification on successful login.
    Alerts user to potentially unauthorized access.
    """
    from datetime import datetime
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    company_name = get_user_company_name() or 'Unknown'
    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto;">
            <h2 style="color: #025a9a;">BPC Dashboard Login Alert</h2>

            <p>A new login was detected on your account:</p>

            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Email:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{email}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Company:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{company_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Time:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{timestamp}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>IP Address:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{ip_address}</td>
                </tr>
            </table>

            <p style="margin-top: 20px;">
                If this wasn't you, please contact support immediately.
            </p>

            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                This is an automated security notification from the BPC Dashboard.
            </p>
        </div>
    </body>
    </html>
    """

    # Send via configured SMTP
    # ... (implementation details)
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Global Cookie Manager

```python
# ❌ WRONG - Causes session bleeding
cookie_manager = CookieManager()  # At module level

def login():
    cookie_manager.set('token', token)  # Shared between users!

# ✅ CORRECT - Per-session isolation
def login():
    cookie_manager = st.session_state.get('cookie_manager')
    if not cookie_manager:
        cookie_manager = CookieManager()
        st.session_state.cookie_manager = cookie_manager
    cookie_manager.set('token', token)
```

### Pitfall 2: Not Validating Profile Ownership

```python
# ❌ WRONG - Profile might belong to different user
profile = get_profile(user_id)
st.session_state.user_profile = profile

# ✅ CORRECT - Validate ownership
profile = get_profile(user_id)
if profile.get('id') != authenticated_user.id:
    clear_session()
    raise SecurityError("Profile mismatch")
st.session_state.user_profile = profile
```

### Pitfall 3: Caching Auth Functions

```python
# ❌ WRONG - Auth state can change
@st.cache_data
def get_current_user():
    return st.session_state.get('user')

# ✅ CORRECT - Never cache auth-related data
def get_current_user():
    return st.session_state.get('user')  # No caching!
```

---

## Key Takeaways

- **Per-session cookie managers** prevent authentication bleeding between users
- **Cookie validation on every request** detects session hijacking
- **Profile ID verification** ensures auth context integrity
- **Token refresh with buffer** prevents expired token issues
- **Audit logging** provides security event trail
- **Email notifications** alert users to login activity
- **Non-fatal error handling** for ancillary operations (logging, email)

---

## Practice Exercise

**Challenge:** Implement a session timeout feature

**Requirements:**
- Auto-logout after 30 minutes of inactivity
- Show warning 5 minutes before timeout
- Allow user to extend session
- Log timeout events to audit table

<details>
<summary>Show Solution Approach</summary>

```python
def check_session_timeout():
    """Check and handle session timeout."""
    TIMEOUT_MINUTES = 30
    WARNING_MINUTES = 25

    last_activity = st.session_state.get('last_activity')

    if not last_activity:
        st.session_state.last_activity = datetime.now()
        return

    inactive_minutes = (datetime.now() - last_activity).seconds / 60

    if inactive_minutes >= TIMEOUT_MINUTES:
        log_audit_event('session_timeout')
        logout_user()
        st.warning("Your session has expired. Please log in again.")
        st.stop()

    elif inactive_minutes >= WARNING_MINUTES:
        if st.button("Extend Session"):
            st.session_state.last_activity = datetime.now()
            st.rerun()
        else:
            remaining = TIMEOUT_MINUTES - inactive_minutes
            st.warning(f"Session expires in {remaining:.0f} minutes")

    # Update last activity on any interaction
    st.session_state.last_activity = datetime.now()
```

</details>

---

## Related Topics

- **[03-session-state-navigation.md](../03-session-state-navigation.md)** - Session state fundamentals
- **[publication-control.md](publication-control.md)** - Role-based data access

---

*You now understand the complete authentication and security system!*
