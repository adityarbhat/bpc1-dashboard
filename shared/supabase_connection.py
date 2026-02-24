"""
BPC Dashboard - Supabase Connection Module
==========================================
Centralized Supabase client connection for authentication and user management.

This module provides per-session Supabase client instances to prevent
authentication context bleeding between users while maintaining auth state
within a single user session.

Usage:
    from shared.supabase_connection import get_supabase_client, get_authenticated_client

    # For login operations (creates fresh client):
    supabase = get_supabase_client()
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})

    # For authenticated operations (reuses session client):
    supabase = get_authenticated_client()
    profile = supabase.table('user_profiles').select('*').eq('id', user_id).execute()

Note:
    Clients are stored per-session (not globally cached) to ensure each user
    gets their own authenticated client while preventing cross-user contamination.
"""

import os
import logging
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """
    Create a new Supabase client instance (not cached).

    IMPORTANT: This function does NOT cache the client to prevent authentication
    context bleeding between users. Each request gets a fresh client instance
    with clean auth state, which is essential for multi-user security.

    The function attempts to read credentials from:
    1. Streamlit secrets (for production deployment)
    2. Environment variables from .env file (for local development)

    Returns:
        Client: Fresh Supabase client instance

    Raises:
        ValueError: If required environment variables are not set

    Example:
        >>> supabase = get_supabase_client()
        >>> user = supabase.auth.get_user()

    Note:
        Creating new client instances is lightweight (just API key setup)
        and essential for preventing user data cross-contamination.
    """

    # Try to get from Streamlit secrets first (production)
    # Fall back to environment variables (local development)
    try:
        supabase_url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
        supabase_anon_key = st.secrets.get("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
    except:
        # If st.secrets fails (running outside Streamlit), use env vars
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")

    # Validate that credentials exist
    if not supabase_url:
        raise ValueError(
            "SUPABASE_URL not found. Please set it in .env file or Streamlit secrets."
        )

    if not supabase_anon_key:
        raise ValueError(
            "SUPABASE_ANON_KEY not found. Please set it in .env file or Streamlit secrets."
        )

    # Create and return Supabase client
    # Note: We use the anon key here, which respects Row-Level Security policies
    # For admin operations, use get_supabase_admin_client() instead
    return create_client(supabase_url, supabase_anon_key)


def get_authenticated_client() -> Client:
    """
    Get the authenticated Supabase client for the current user session.

    This function returns the Supabase client that was authenticated during
    login or session recovery. The client is stored in session state to
    maintain auth context for database operations that require RLS authentication.

    If no authenticated client exists in session state, creates a new one.

    Returns:
        Client: Authenticated Supabase client instance for current session

    Example:
        >>> # After login, use this for authenticated database operations:
        >>> supabase = get_authenticated_client()
        >>> profile = supabase.table('user_profiles').select('*').eq('id', user_id).execute()

    Note:
        This client is stored per-session, not globally cached, preventing
        auth context bleeding between different user sessions.
    """
    # Check if we have a cached client
    if 'supabase_client' in st.session_state and st.session_state.supabase_client:
        cached_client = st.session_state.supabase_client

        # SECURITY: Validate cached client belongs to current user
        if 'user' in st.session_state and st.session_state.user:
            try:
                # Get user from cached client
                cached_user = cached_client.auth.get_user()
                current_user_id = st.session_state.user.id

                # Verify user IDs match
                if cached_user and cached_user.user and cached_user.user.id == current_user_id:
                    return cached_client
                else:
                    logger.warning(f"SECURITY: Cached client user mismatch - clearing")
                    # Clear invalid cached client
                    if 'supabase_client' in st.session_state:
                        del st.session_state.supabase_client
            except Exception as e:
                logger.error(f"Error validating cached client: {e}")
                # Clear on any error
                if 'supabase_client' in st.session_state:
                    del st.session_state.supabase_client

    # Create fresh client
    client = get_supabase_client()
    st.session_state.supabase_client = client
    return client


def get_supabase_admin_client() -> Client:
    """
    Create a new Supabase admin client instance (not cached).

    This function creates a Supabase client with service_role key, which
    bypasses Row-Level Security (RLS) policies. Use this ONLY for admin
    operations like creating users, managing permissions, etc.

    IMPORTANT: Not cached to prevent auth context issues between operations.

    WARNING: This client has full database access. Use with caution!

    Returns:
        Client: Fresh Supabase admin client instance

    Raises:
        ValueError: If required environment variables are not set

    Example:
        >>> supabase_admin = get_supabase_admin_client()
        >>> # Create a new user (admin operation)
        >>> response = supabase_admin.auth.admin.create_user({
        ...     "email": "john@example.com",
        ...     "password": "SecurePass123"
        ... })
    """

    # Try to get from Streamlit secrets first (production)
    # Fall back to environment variables (local development)
    try:
        supabase_url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
        supabase_service_key = st.secrets.get("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    except:
        # If st.secrets fails (running outside Streamlit), use env vars
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

    # Validate that credentials exist
    if not supabase_url:
        raise ValueError(
            "SUPABASE_URL not found. Please set it in .env file or Streamlit secrets."
        )

    if not supabase_service_key:
        raise ValueError(
            "SUPABASE_SERVICE_KEY not found. Please set it in .env file or Streamlit secrets."
        )

    # Create and return Supabase admin client
    # This client bypasses RLS - use only for admin operations!
    return create_client(supabase_url, supabase_service_key)


# Quick test function for development
if __name__ == "__main__":
    """Test the Supabase connection when running this file directly"""
    print("Testing Supabase connection...")

    try:
        # Test regular client
        supabase = get_supabase_client()
        print("✅ Successfully created Supabase client")

        # Test admin client
        supabase_admin = get_supabase_admin_client()
        print("✅ Successfully created Supabase admin client")

        # Try to query companies table
        response = supabase_admin.table('companies').select('*').limit(3).execute()
        print(f"✅ Successfully queried database ({len(response.data)} companies)")

        print("\n🎉 All connection tests passed!")

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
