"""
BPC Dashboard - Authentication Utilities
========================================
Core authentication functions for user login, logout, session management,
and permission checking.

This module provides all the authentication-related utilities used across
the BPC Dashboard application.

Usage:
    from shared.auth_utils import require_auth, login_user, logout_user

    # At the top of every protected page:
    require_auth()

    # In login page:
    if login_user(email, password):
        st.success("Login successful!")
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from shared.supabase_connection import get_supabase_client, get_supabase_admin_client
from extra_streamlit_components import CookieManager
import os
import logging
import requests

# Configure logger for auth debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# ============================================================================
# COOKIE MANAGER INITIALIZATION
# ============================================================================

def get_cookies():
    """
    Get cookie manager from session state (per-user isolation).

    CRITICAL SECURITY FIX: Cookie manager MUST be stored in st.session_state,
    NOT as a module-level global variable. Module-level variables are shared
    across ALL users in a Streamlit server deployment, causing authentication
    cookies to leak between users.

    Each user session gets its own isolated cookie manager instance, preventing
    session bleeding where User A's cookies would be visible to User B.

    Returns:
        CookieManager: Session-specific cookie manager instance
    """
    # Store cookie manager in session state (unique per user session)
    if '_cookie_manager' not in st.session_state:
        st.session_state._cookie_manager = CookieManager()

    return st.session_state._cookie_manager


def save_navigation_state():
    """
    Save current navigation state to cookies for persistence across page refreshes.

    This saves:
    - current_page: Which page/view is active
    - nav_tab: Whether in 'group' or 'company' view
    - period: 'year_end' or 'june_end'
    - selected_company_name: Currently selected company (if any)

    Call this whenever navigation state changes.
    """
    try:
        cookies = get_cookies()

        # Save navigation state
        if st.session_state.get('current_page'):
            cookies.set('current_page', st.session_state.current_page,
                       same_site='lax',
                       max_age=604800,
                       key='current_page')

        if st.session_state.get('nav_tab'):
            cookies.set('nav_tab', st.session_state.nav_tab,
                       same_site='lax',
                       max_age=604800,
                       key='nav_tab')

        if st.session_state.get('period'):
            cookies.set('period', st.session_state.period,
                       same_site='lax',
                       max_age=604800,
                       key='period')

        if st.session_state.get('selected_company_name'):
            cookies.set('selected_company_name', st.session_state.selected_company_name,
                       same_site='lax',
                       max_age=604800,
                       key='selected_company_name')

    except Exception:
        # Silent failure - navigation still works without persistence
        pass


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def init_session_state():
    """
    Initialize session state variables if they don't exist.

    This should be called at the start of the main app to ensure
    all required session variables are available.
    """
    if 'user' not in st.session_state:
        st.session_state.user = None

    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = None

    if 'access_token' not in st.session_state:
        st.session_state.access_token = None

    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False


def attempt_session_recovery():
    """
    Attempt to recover user session from cookies after page refresh.

    This function reads authentication tokens from browser cookies and
    restores the user session to Streamlit's session state. This allows
    users to stay logged in across page refreshes.

    Returns:
        bool: True if session was recovered, False otherwise
    """
    try:
        # Get cookie manager first
        cookies = get_cookies()

        # STRICT VALIDATION: Clear session on ANY cookie/session inconsistency
        cookie_user_id = cookies.get('user_id')
        session_user_id = getattr(st.session_state.user, 'id', None) if st.session_state.user else None

        # DEBUG: Log validation check on every request
        logger.debug(f"VALIDATION CHECK - Cookie: {cookie_user_id}, Session: {session_user_id}")

        # Case 1: Cookie exists but session doesn't match (session mismatch)
        if cookie_user_id and session_user_id and cookie_user_id != session_user_id:
            logger.error(f"SECURITY: User ID mismatch - cookie={cookie_user_id}, session={session_user_id}")
            clear_session()
            clear_cookies()
            return False

        # Case 2: Cookie exists but no session user (suspicious - possible session hijacking)
        if cookie_user_id and not session_user_id:
            logger.warning(f"SECURITY: Cookie exists but no session user - cookie={cookie_user_id}")
            clear_session()
            clear_cookies()
            return False

        # Case 3: Session exists but no cookie (session hijacking attempt?)
        if session_user_id and not cookie_user_id:
            logger.warning(f"SECURITY: Session exists but no cookie - session_user={session_user_id}")
            clear_session()
            clear_cookies()
            return False

        # If already authenticated and all validations passed, skip recovery
        if st.session_state.authenticated and st.session_state.user:
            return True  # Skip if already authenticated and user matches

        # Try to read tokens from cookies
        access_token = cookies.get('access_token')
        refresh_token = cookies.get('refresh_token')
        user_id = cookies.get('user_id')

        # Log session recovery attempt
        session_user_id = getattr(st.session_state.user, 'id', None) if st.session_state.user else None
        logger.info(f"Session recovery attempted - Cookie user_id: {user_id}, Session user_id: {session_user_id}")

        # If no tokens in cookies, can't recover
        if not access_token or not refresh_token or not user_id:
            logger.debug("Session recovery failed - No tokens in cookies")
            return False

        # Get Supabase client
        from shared.supabase_connection import get_supabase_client, get_authenticated_client
        supabase = get_supabase_client()

        # Try to restore session with saved tokens
        try:
            response = supabase.auth.set_session(access_token, refresh_token)

            if not response or not response.user:
                # Tokens are invalid, clear cookies
                cookies.delete('access_token', key='clear_access_token_invalid')
                cookies.delete('refresh_token', key='clear_refresh_token_invalid')
                cookies.delete('user_id', key='clear_user_id_invalid')
                return False

            # Store the authenticated client in session state for use by other functions
            st.session_state.supabase_client = supabase

            # Successfully recovered session - populate session state
            st.session_state.user = response.user
            st.session_state.user_id = response.user.id
            st.session_state.access_token = response.session.access_token
            st.session_state.refresh_token = response.session.refresh_token
            st.session_state.authenticated = True

            # Load user profile and permissions - MUST succeed for valid session
            profile_loaded = load_user_profile(response.user.id, show_error=False)

            if not profile_loaded or not st.session_state.user_profile:
                # Profile load failed - invalid session, clear everything
                logger.warning(f"Session recovery failed - could not load profile for user {response.user.id}")
                clear_session()
                clear_cookies()
                return False

            # Log successful session recovery
            profile_name = st.session_state.user_profile.get('full_name', 'Unknown')
            profile_role = st.session_state.user_profile.get('role', 'Unknown')
            logger.info(f"Session recovered successfully - ID: ...{str(response.user.id)[-8:]}, Role: {profile_role}")

            # Send login notification email for FIRST-TIME session recovery only
            # Check if we've already sent email this session
            if not st.session_state.get('session_recovery_email_sent', False):
                try:
                    from shared.email_notifications import send_login_notification_email
                    send_login_notification_email(
                        user_email=response.user.email,
                        user_name=st.session_state.user_profile.get('full_name', 'User'),
                        login_status='success',
                        ip_address=get_client_ip(),
                        timestamp=datetime.now()
                    )
                    # Mark that we've sent the email for this session
                    st.session_state.session_recovery_email_sent = True
                except Exception as email_error:
                    logger.warning(f"Session recovery email failed: {type(email_error).__name__}")

            # Log successful recovery with company context
            try:
                log_audit_event(
                    user_id=response.user.id,
                    action="session_recovered",
                    resource="auth",
                    company_id=st.session_state.user_profile.get('company_id'),
                    ip_address=get_client_ip(),
                    metadata={
                        'recovery_type': 'cookie',
                        'username': st.session_state.user_profile.get('username'),
                        'role': st.session_state.user_profile.get('role')
                    }
                )
            except Exception:
                # Logging failed, but session recovery succeeded
                pass

            return True

        except Exception as e:
            # Token restoration failed, clear invalid cookies
            logger.warning(f"Token restoration failed: {e}")
            cookies.delete('access_token', key='clear_access_token_failed')
            cookies.delete('refresh_token', key='clear_refresh_token_failed')
            cookies.delete('user_id', key='clear_user_id_failed')
            return False

    except Exception as e:
        # Session recovery failed - this is normal for logged-out users
        # Silently fail and let them see the login page
        return False


def clear_session():
    """
    Clear ALL session state to prevent data leakage between users.

    This is called when a user logs out or when a session expires.
    Clears all session variables to ensure no stale data persists.
    """
    # List all keys to clear (create copy to avoid modification during iteration)
    keys_to_clear = list(st.session_state.keys())

    # Clear each key
    for key in keys_to_clear:
        del st.session_state[key]

    # Reinitialize essential state to default values
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.user_profile = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None

    logger.debug("Session state fully cleared")


def clear_cookies():
    """
    Clear all authentication-related cookies.

    This is called when a user logs out or when session validation fails.
    Removes access_token, refresh_token, and user_id cookies.
    """
    try:
        cookies = get_cookies()
        cookies.delete('access_token', key='delete_access_token')
        cookies.delete('refresh_token', key='delete_refresh_token')
        cookies.delete('user_id', key='delete_user_id')
        logger.debug("Cookies cleared")
    except Exception as e:
        # Cookie clearing failed, log but don't raise
        logger.warning(f"Failed to clear cookies: {e}")


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def login_user(email: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a user with email and password.

    Args:
        email: User's email address
        password: User's password

    Returns:
        Dict with keys:
            - success (bool): Whether login was successful
            - message (str): Success or error message
            - user (dict): User object if successful

    Example:
        >>> result = login_user("john@ace.com", "SecurePass123")
        >>> if result['success']:
        ...     st.success(result['message'])
        ... else:
        ...     st.error(result['message'])
    """
    try:
        # CRITICAL: Clear existing session ONLY if there's a different user logged in
        # Don't clear if no one is logged in (prevents infinite loop)
        if st.session_state.get('authenticated') and st.session_state.get('user'):
            existing_email = st.session_state.user.email if st.session_state.user else None
            if existing_email and existing_email != email:
                logger.info("Different user logging in - Clearing session/cookies")
                clear_session()
                clear_cookies()

        supabase = get_supabase_client()

        # Attempt to sign in with Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # Save tokens to cookies for session persistence across page refreshes
        cookies = get_cookies()
        cookies.set('access_token', response.session.access_token,
                   same_site='strict',  # Tighten security to prevent cross-site cookie reuse
                   max_age=3600,        # 1 hour (matches JWT token expiry)
                   key='access_token')
        cookies.set('refresh_token', response.session.refresh_token,
                   same_site='strict',
                   max_age=86400,       # 24 hours (allows session refresh within a day)
                   key='refresh_token')
        cookies.set('user_id', response.user.id,
                   same_site='strict',
                   max_age=3600,        # 1 hour (matches access token expiry)
                   key='user_id')

        # Store the authenticated client in session state for use by other functions
        st.session_state.supabase_client = supabase

        # Store user info in session state (for current session)
        st.session_state.user = response.user
        st.session_state.access_token = response.session.access_token
        st.session_state.refresh_token = response.session.refresh_token
        st.session_state.authenticated = True

        # Fetch user profile and permissions
        profile_loaded = load_user_profile(response.user.id, show_error=False)

        # Validate profile loaded successfully
        if not profile_loaded or not st.session_state.user_profile:
            clear_session()
            clear_cookies()
            return {
                'success': False,
                'message': "Authentication succeeded but failed to load user profile. Please try again."
            }

        # Verify profile belongs to correct user (critical security check)
        if st.session_state.user_profile.get('id') != response.user.id:
            logger.error(f"CRITICAL: Profile ID mismatch - Expected: ...{str(response.user.id)[-8:]}, Got: ...{str(st.session_state.user_profile.get('id', ''))[-8:]}")
            clear_session()
            clear_cookies()
            return {
                'success': False,
                'message': f"Profile mismatch detected. Please clear your browser cache and try again."
            }

        # Log successful authentication and profile load
        logger.info(f"Login successful - ID: ...{str(response.user.id)[-8:]}, Role: {st.session_state.user_profile.get('role')}")

        # Send successful login notification email
        try:
            from shared.email_notifications import send_login_notification_email
            send_login_notification_email(
                user_email=response.user.email,
                user_name=st.session_state.user_profile.get('full_name', 'User'),
                login_status='success',
                ip_address=get_client_ip(),
                timestamp=datetime.now()
            )
        except Exception as email_error:
            logger.warning(f"Login notification email failed: {type(email_error).__name__}")

        # Log successful login with company context
        log_audit_event(
            user_id=response.user.id,
            action="login",
            resource="auth",
            company_id=st.session_state.user_profile.get('company_id'),
            ip_address=get_client_ip(),
            metadata={
                'username': st.session_state.user_profile.get('username'),
                'full_name': st.session_state.user_profile.get('full_name'),
                'role': st.session_state.user_profile.get('role')
            }
        )

        # Final verification: Ensure session state has correct user (paranoid check)
        final_check_user_id = st.session_state.user.id if st.session_state.user else None
        final_check_profile_id = st.session_state.user_profile.get('id') if st.session_state.user_profile else None
        final_check_email = st.session_state.user.email if st.session_state.user else None

        if final_check_user_id != response.user.id or final_check_email != response.user.email:
            logger.error(f"CRITICAL POST-LOGIN: Session state corruption - Expected ID: ...{str(response.user.id)[-8:]}, Got ID: ...{str(final_check_user_id or '')[-8:]}")
            clear_session()
            clear_cookies()
            return {
                'success': False,
                'message': "Session validation failed. Please try logging in again."
            }

        logger.info(f"Final verification passed - Session state correctly set for ID: ...{str(response.user.id)[-8:]}")

        return {
            'success': True,
            'message': f"Welcome back, {st.session_state.user_profile['full_name']}!",
            'user': response.user
        }

    except Exception as e:
        error_message = str(e)

        # Check if this is a widget conflict error (NOT a real login failure)
        is_widget_conflict = "cannot be modified after the widget" in error_message

        # Only send failed login email for ACTUAL authentication failures
        # Skip email for widget conflicts (technical rendering issues)
        if not is_widget_conflict:
            try:
                from shared.email_notifications import send_login_notification_email
                send_login_notification_email(
                    user_email=email,
                    user_name='Unknown User',
                    login_status='failed',
                    ip_address=get_client_ip(),
                    timestamp=datetime.now(),
                    error_reason=error_message
                )
            except Exception:
                pass  # Silent failure

        # Log failed login attempt (or widget conflict)
        # Try to look up company_id from email for better security tracking
        company_id_for_audit = None
        try:
            admin_client = get_supabase_admin_client()
            profile_lookup = admin_client.table('user_profiles') \
                .select('company_id') \
                .eq('email', email) \
                .maybeSingle() \
                .execute()
            if profile_lookup.data:
                company_id_for_audit = profile_lookup.data.get('company_id')
        except Exception:
            pass  # If lookup fails, just log without company_id

        log_audit_event(
            user_id=None,
            action="failed_login" if not is_widget_conflict else "widget_conflict",
            resource="auth",
            company_id=company_id_for_audit,
            metadata={'email': email, 'error': str(e)},
            ip_address=get_client_ip()
        )

        # Provide user-friendly error messages
        if "Invalid login credentials" in error_message:
            return {
                'success': False,
                'message': "Invalid email or password. Please try again."
            }
        elif "Email not confirmed" in error_message:
            return {
                'success': False,
                'message': "Please confirm your email address before logging in."
            }
        elif is_widget_conflict:
            return {
                'success': False,
                'message': "WIDGET_CONFLICT_ERROR"  # Special marker for login page to handle
            }
        else:
            return {
                'success': False,
                'message': f"Login failed: {error_message}"
            }


def logout_user():
    """
    Log out the current user and clear their session.

    This function:
    1. Signs out from Supabase
    2. Logs the logout event
    3. Clears session state
    4. Reloads the page to show login screen

    Example:
        >>> if st.button("Logout"):
        ...     logout_user()
    """
    try:
        supabase = get_supabase_client()

        # Log logout event before clearing session (capture company_id before clearing)
        if st.session_state.user:
            company_id = st.session_state.user_profile.get('company_id') if st.session_state.user_profile else None
            username = st.session_state.user_profile.get('username') if st.session_state.user_profile else None
            role = st.session_state.user_profile.get('role') if st.session_state.user_profile else None

            log_audit_event(
                user_id=st.session_state.user.id,
                action="logout",
                resource="auth",
                company_id=company_id,
                ip_address=get_client_ip(),
                metadata={
                    'username': username,
                    'role': role
                }
            )

        # Clear cookies (auth tokens only)
        clear_cookies()

        # Sign out from Supabase
        supabase.auth.sign_out()

        # Clear any query parameters that might re-authenticate
        try:
            st.query_params.clear()
        except Exception:
            pass

        # Clear session
        clear_session()

        # Force page reload to show login screen
        st.rerun()

    except Exception as e:
        # Even if Supabase logout fails, clear local session and cookies
        clear_cookies()
        st.error(f"Logout error: {e}")
        clear_session()
        st.rerun()


def load_user_profile(user_id: str, show_error: bool = True) -> bool:
    """
    Load user profile and permissions from database.

    Args:
        user_id: The user's UUID
        show_error: Whether to display error messages (default True)

    Returns:
        True if profile loaded successfully, False otherwise

    This fetches the user's profile from the user_profiles table
    and stores it in session state for easy access.
    """
    try:
        # Use the authenticated client from session state
        # This client has the auth context from login/session recovery
        from shared.supabase_connection import get_authenticated_client
        supabase = get_authenticated_client()

        # Fetch user profile
        response = supabase.table('user_profiles') \
            .select('*, companies(*)') \
            .eq('id', user_id) \
            .single() \
            .execute()

        # Validate response has expected data
        if not response.data or 'full_name' not in response.data:
            raise ValueError(f"Invalid profile data returned for user {user_id}")

        # Verify user_id matches (security check to prevent auth context bleeding)
        if response.data.get('id') != user_id:
            raise ValueError(f"Profile ID mismatch: requested {user_id}, got {response.data.get('id')}")

        st.session_state.user_profile = response.data

        # Log successful profile load
        logger.info(f"Profile loaded - ID: ...{str(user_id)[-8:]}, Role: {response.data.get('role')}")

        return True

    except Exception as e:
        if show_error:
            st.error(f"Error loading user profile: {e}")
        st.session_state.user_profile = None
        return False


# ============================================================================
# AUTHORIZATION FUNCTIONS
# ============================================================================

def require_auth():
    """
    Require authentication to access a page.

    This function checks if the user is authenticated. If not, it attempts
    to recover an existing session from cookies before showing the login page.

    Usage:
        Call this at the beginning of any page that requires authentication.
    """
    # Initialize session state
    init_session_state()

    # SECURITY: ALWAYS validate cookie/session consistency on every request
    # This runs whether user is logged in or out to detect session hijacking
    # If validation fails (cookie/session mismatch), it will clear session and force re-login
    attempt_session_recovery()

    # Clear any login transition flags if user is authenticated
    if st.session_state.authenticated and st.session_state.user:
        # Clear the logging_in flag if it was set
        if st.session_state.get('logging_in', False):
            st.session_state.logging_in = False
        return  # User is authenticated, continue to dashboard

    # User is not authenticated - show login page
    if st.session_state.get('show_forgot_password', False):
        from pages.auth.forgot_password import show_forgot_password_page
        show_forgot_password_page()
    else:
        # Show login page
        from pages.auth.login import show_login_page
        show_login_page()
    st.stop()  # Stop execution of the rest of the page

    # Verify token hasn't expired (check every request)
    if is_token_expired():
        try:
            refresh_access_token()
        except Exception as e:
            st.error("Your session has expired. Please log in again.")
            clear_session()
            st.rerun()


def require_role(required_role: str):
    """
    Require a specific role to access a page or feature.

    Args:
        required_role: The role required (e.g., 'super_admin')

    Raises:
        Streamlit error and stops execution if user doesn't have the role

    Example:
        >>> def show_admin_page():
        ...     require_auth()
        ...     require_role('super_admin')  # Only super admins can access
        ...
        ...     st.title("Admin Panel")
        ...     # Rest of admin page...
    """
    if not st.session_state.user_profile:
        st.error("User profile not loaded. Please log in again.")
        clear_session()
        st.rerun()
        st.stop()

    user_role = st.session_state.user_profile.get('role')

    if user_role != required_role:
        st.error(f"Access denied. This page requires '{required_role}' role.")
        st.info(f"Your role: {user_role}")
        st.stop()


def is_super_admin() -> bool:
    """
    Check if the current user is a super admin.

    Returns:
        bool: True if user is super admin, False otherwise

    Example:
        >>> if is_super_admin():
        ...     st.button("Delete All Data")  # Only show for admins
    """
    if not st.session_state.user_profile:
        return False

    return st.session_state.user_profile.get('role') == 'super_admin'


def can_upload_data() -> bool:
    """
    Check if the current user has permission to upload data.

    Returns:
        bool: True if user can upload data, False otherwise

    Example:
        >>> if can_upload_data():
        ...     show_upload_form()
        ... else:
        ...     st.warning("You don't have permission to upload data.")
    """
    if not st.session_state.user_profile:
        return False

    return st.session_state.user_profile.get('can_upload_data', False)


def get_user_company_id() -> Optional[int]:
    """
    Get the company ID assigned to the current user.

    Returns:
        int: Company ID, or None if user is super admin (has access to all)

    Example:
        >>> company_id = get_user_company_id()
        >>> if company_id:
        ...     st.info(f"You are assigned to company ID: {company_id}")
    """
    if not st.session_state.user_profile:
        return None

    return st.session_state.user_profile.get('company_id')


def get_user_company_name() -> Optional[str]:
    """
    Get the company name assigned to the current user.

    Returns:
        str: Company name, or None if user is super admin

    Example:
        >>> company_name = get_user_company_name()
        >>> st.title(f"{company_name} Dashboard")
    """
    if not st.session_state.user_profile:
        return None

    company = st.session_state.user_profile.get('companies')
    if company:
        return company.get('display_name')

    return None


# ============================================================================
# TOKEN MANAGEMENT
# ============================================================================

def is_token_expired(token: str = None, buffer_minutes: int = 5) -> bool:
    """
    Check if a JWT access token has expired or will expire soon.

    Args:
        token: JWT token to check. If None, uses st.session_state.access_token
        buffer_minutes: Consider token expired this many minutes before actual expiry

    Returns:
        bool: True if token is expired or will expire within buffer, False otherwise
    """
    import jwt
    from datetime import datetime, timedelta

    # Use provided token or get from session state
    check_token = token if token else st.session_state.access_token

    # If no token, consider it expired
    if not check_token:
        return True

    try:
        # Decode token without verification (we just need the expiry claim)
        decoded = jwt.decode(check_token, options={"verify_signature": False})

        # Get expiration timestamp
        exp_timestamp = decoded.get('exp')
        if not exp_timestamp:
            # No expiry claim, let Supabase handle it
            return False

        # Convert to datetime
        exp_time = datetime.fromtimestamp(exp_timestamp)

        # Add buffer to current time
        buffer_time = datetime.now() + timedelta(minutes=buffer_minutes)

        # Token is expired if expiry is before (now + buffer)
        return exp_time <= buffer_time

    except Exception:
        # If we can't decode the token, assume it's invalid
        return True


def refresh_access_token():
    """
    Refresh the access token using the refresh token.

    This is called automatically when the token is about to expire.
    """
    try:
        supabase = get_supabase_client()

        # Supabase automatically handles token refresh
        # We just need to call refresh_session
        response = supabase.auth.refresh_session()

        if response.session:
            st.session_state.access_token = response.session.access_token
            st.session_state.refresh_token = response.session.refresh_token

    except Exception as e:
        # If refresh fails, force re-login
        raise Exception(f"Token refresh failed: {e}")


# ============================================================================
# AUDIT LOGGING
# ============================================================================

def log_audit_event(
    user_id: Optional[str],
    action: str,
    resource: str,
    company_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """
    Log an audit event to the database.

    Args:
        user_id: User's UUID (can be None for failed logins)
        action: Action performed (e.g., 'login', 'upload_data', 'create_user')
        resource: Resource affected (e.g., 'auth', 'data_input', 'users')
        company_id: Company ID if action is company-specific
        metadata: Additional JSON data about the event
        ip_address: Client IP address

    Example:
        >>> log_audit_event(
        ...     user_id=user.id,
        ...     action="upload_balance_sheet",
        ...     resource="data_input",
        ...     company_id=1,
        ...     metadata={'filename': 'oct_2025.xlsx', 'rows': 45}
        ... )
    """
    try:
        supabase = get_supabase_admin_client()  # Use admin client to bypass RLS

        supabase.table('audit_logs').insert({
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'company_id': company_id,
            'metadata': metadata,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat()
        }).execute()

    except Exception as e:
        # Don't let audit logging failures break the application
        # But print the error for debugging
        print(f"Audit logging error: {e}")


def get_client_ip() -> Optional[str]:
    """
    Get the client's IP address.

    Returns:
        str: IP address or None if not available

    Note: This is tricky in Streamlit. In production with a reverse proxy,
    you'd need to read from X-Forwarded-For header.

    This implementation uses a free IP detection service (ipify.org) to get
    the public IP address. The IP is cached in session state for performance.
    """
    # Check if IP is already cached in session state
    if 'client_ip' in st.session_state and st.session_state.client_ip:
        return st.session_state.client_ip

    try:
        # Use ipify.org free API to get public IP address
        # Alternative services: api.ipify.org, icanhazip.com, ifconfig.me
        response = requests.get('https://api.ipify.org?format=json', timeout=3)

        if response.status_code == 200:
            ip_address = response.json().get('ip')

            # Cache in session state to avoid repeated API calls
            st.session_state.client_ip = ip_address

            return ip_address
        else:
            logging.warning(f"IP detection service returned status {response.status_code}")
            return None

    except requests.RequestException as e:
        # Don't let IP detection failures break the application
        logging.warning(f"Failed to detect IP address: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in IP detection: {e}")
        return None


# ============================================================================
# PASSWORD RESET
# ============================================================================

def send_password_reset_email(email: str) -> Dict[str, Any]:
    """
    Send a password reset email to the user.

    Args:
        email: User's email address

    Returns:
        Dict with keys:
            - success (bool): Whether email was sent
            - message (str): Success or error message

    Example:
        >>> result = send_password_reset_email("john@ace.com")
        >>> if result['success']:
        ...     st.success(result['message'])
    """
    try:
        supabase = get_supabase_client()

        # Send password reset email via Supabase with redirect URL
        # Redirect to dedicated reset_landing page that handles hash-based tokens
        supabase.auth.reset_password_for_email(
            email,
            options={
                "redirect_to": "https://bpc1-dashboard.onrender.com/reset_landing"
            }
        )

        # Log the password reset request
        log_audit_event(
            user_id=None,
            action="password_reset_requested",
            resource="auth",
            metadata={'email': email},
            ip_address=get_client_ip()
        )

        return {
            'success': True,
            'message': f"Password reset link sent to {email}. Please check your inbox."
        }

    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to send reset email: {str(e)}"
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_user_email() -> Optional[str]:
    """
    Get the current user's email address.

    Returns:
        str: Email address or None if not logged in
    """
    if st.session_state.user:
        return st.session_state.user.email
    return None


def get_current_user_name() -> Optional[str]:
    """
    Get the current user's full name.

    Returns:
        str: Full name or None if not logged in
    """
    if st.session_state.user_profile:
        return st.session_state.user_profile.get('full_name')
    return None


# Quick test function for development
if __name__ == "__main__":
    print("Auth utils module loaded successfully!")
    print("Available functions:")
    print("  - login_user(email, password)")
    print("  - logout_user()")
    print("  - require_auth()")
    print("  - require_role(role)")
    print("  - is_super_admin()")
    print("  - can_upload_data()")
    print("  - log_audit_event(...)")
