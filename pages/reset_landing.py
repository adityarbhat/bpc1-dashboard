"""
BPC1 Dashboard - Password Reset Landing Page
=============================================
Dedicated page for handling Supabase password reset redirects using PKCE flow.

This page:
1. Receives Supabase redirect with query parameter tokens (?token_hash=...&type=recovery)
2. Verifies the token hash using Supabase verify_otp() method
3. Displays password reset form
4. Updates password via Supabase
5. Auto-logs in user and redirects to main dashboard

IMPORTANT: Requires Supabase email template to use PKCE flow:
  <a href="{{ .SiteURL }}/reset_landing?token_hash={{ .TokenHash }}&type=recovery">
"""

import streamlit as st
import base64
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.supabase_connection import get_supabase_client
from shared.auth_utils import load_user_profile, log_audit_event


def get_logo_base64():
    """Load and encode IM AI Consultants logo as base64"""
    try:
        logo_path = os.path.join(os.path.dirname(__file__), '../assets/imai_logo.png')
        with open(logo_path, 'rb') as f:
            logo_bytes = f.read()
        return base64.b64encode(logo_bytes).decode()
    except:
        return None


# Page configuration
st.set_page_config(
    page_title="Reset Password - BPC1 Dashboard",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide default Streamlit elements
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Hide sidebar navigation */
        [data-testid="stSidebarNav"] {display: none;}
        section[data-testid="stSidebar"] {display: none;}

        /* Input fields */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            padding: 12px;
            font-size: 16px;
        }

        .stTextInput > div > div > input:focus {
            border-color: #025a9a;
            box-shadow: 0 0 0 2px rgba(2, 90, 154, 0.1);
        }

        /* Button */
        .stButton > button {
            width: 100%;
            background-color: #025a9a;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 16px;
            font-weight: bold;
        }

        .stButton > button:hover {
            background-color: #034f87;
        }

        /* Password requirements */
        .password-requirements {
            background: #f7fafc;
            border-left: 4px solid #025a9a;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            font-size: 14px;
        }
    </style>
""", unsafe_allow_html=True)

# Center container
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Logo and header
    logo_b64 = get_logo_base64()

    if logo_b64:
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #025a9a; font-size: 28px; font-weight: bold; margin-bottom: 10px;">
                    🔐 Reset Your Password
                </h1>
                <a href="https://www.imaiconsultants.com" target="_blank" style="text-decoration: none; display: block; margin-top: 15px;">
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px;">
                        <img src="data:image/png;base64,{logo_b64}" style="height: 60px; width: auto;" alt="IM AI" />
                        <span style="color: #666; font-size: 13px; font-weight: 500;">Powered by IM AI</span>
                    </div>
                </a>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #025a9a; font-size: 28px; font-weight: bold;">🔐 Reset Your Password</h1>
                <a href="https://www.imaiconsultants.com" target="_blank" style="text-decoration: none; color: #666; font-size: 12px;">
                    Powered by IM AI
                </a>
            </div>
        """, unsafe_allow_html=True)

    # Check for tokens in query parameters (PKCE flow)
    try:
        query_params = st.query_params
        token_hash = query_params.get('token_hash')
        type_param = query_params.get('type')

        # Check for error parameters (expired/invalid tokens)
        error = query_params.get('error')
        error_description = query_params.get('error_description')
    except Exception as e:
        st.error(f"Error reading query params: {e}")
        token_hash = None
        type_param = None
        error = None
        error_description = None

    # Check for expired or invalid token errors
    if error == 'access_denied' or 'expired' in str(error_description).lower():
        st.error("❌ This password reset link has expired.")
        st.warning("⏰ Password reset links are only valid for a few minutes and can only be used once.")
        st.info("💡 Please request a new password reset link from the login page and use it immediately.")
        st.markdown("<br>", unsafe_allow_html=True)

        # Use link instead of button for redirect
        st.markdown("""
            <a href="/" style="display: inline-block; width: 100%; text-align: center;
               background-color: #025a9a; color: white; padding: 12px 24px;
               border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px;">
                ← Go to Login Page
            </a>
        """, unsafe_allow_html=True)
        st.stop()

    # If no tokens found, show error
    if not token_hash or type_param != 'recovery':
        st.error("❌ Invalid or missing password reset link.")
        st.info("Please request a new password reset link from the login page.")
        st.markdown("<br>", unsafe_allow_html=True)

        # Use link instead of button for redirect
        st.markdown("""
            <a href="/" style="display: inline-block; width: 100%; text-align: center;
               background-color: #025a9a; color: white; padding: 12px 24px;
               border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px;">
                ← Go to Login Page
            </a>
        """, unsafe_allow_html=True)
        st.stop()

    # Show password requirements
    st.markdown("""
        <div class="password-requirements">
            <h4 style="margin-top: 0; color: #025a9a;">Password Requirements:</h4>
            <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                <li style="margin: 5px 0; color: #666;">At least 8 characters long</li>
                <li style="margin: 5px 0; color: #666;">Mix of uppercase and lowercase letters recommended</li>
                <li style="margin: 5px 0; color: #666;">Include numbers and special characters for security</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    # Password reset form
    with st.form(key="reset_password_form", clear_on_submit=False):
        st.markdown("### Enter Your New Password")

        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Enter your new password",
            key="new_password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            placeholder="Re-enter your new password",
            key="confirm_password"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        submit_button = st.form_submit_button("Reset Password & Sign In", use_container_width=True)

        if submit_button:
            # Validate inputs
            if not new_password or not confirm_password:
                st.error("Please fill in all fields.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif new_password != confirm_password:
                st.error("Passwords do not match. Please try again.")
            else:
                # Update password using Supabase
                try:
                    supabase = get_supabase_client()

                    with st.spinner("Updating your password..."):
                        # Verify the OTP token hash and establish session (PKCE flow)
                        verify_response = supabase.auth.verify_otp({
                            'token_hash': token_hash,
                            'type': 'recovery'
                        })

                        if not verify_response.session:
                            st.error("❌ Failed to verify password reset token.")
                            st.info("Please request a new password reset link from the login page.")
                            st.stop()

                        # Extract session tokens
                        access_token = verify_response.session.access_token
                        refresh_token = verify_response.session.refresh_token

                        # Set the session
                        supabase.auth.set_session(access_token, refresh_token)

                        # Update the password
                        response = supabase.auth.update_user({
                            'password': new_password
                        })

                        if response.user:
                            # Try to load user profile (may not exist for new users)
                            # Pass show_error=False to prevent error display
                            try:
                                load_user_profile(response.user.id, show_error=False)
                            except Exception:
                                pass

                            # Try to log successful password reset
                            try:
                                company_id = st.session_state.user_profile.get('company_id') if st.session_state.get('user_profile') else None
                                log_audit_event(
                                    user_id=response.user.id,
                                    action="password_reset_completed",
                                    resource="auth",
                                    company_id=company_id
                                )
                            except Exception:
                                pass

                            st.success("✅ Password updated successfully!")
                            st.balloons()

                            st.info("🔄 Redirecting to login page in 3 seconds...")

                            # Multiple redirect methods for reliability
                            st.markdown("""
                                <meta http-equiv="refresh" content="3;url=/" />
                                <script>
                                setTimeout(function() {
                                    window.location.href = '/';
                                }, 3000);
                                </script>
                            """, unsafe_allow_html=True)

                            # Manual redirect button as backup
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("""
                                <a href="/" style="display: inline-block; width: 100%; text-align: center;
                                   background-color: #025a9a; color: white; padding: 12px 24px;
                                   border-radius: 8px; text-decoration: none; font-weight: bold;">
                                    ← Go to Login Page Now
                                </a>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("Failed to update password. Please try again.")

                except Exception as e:
                    error_msg = str(e)

                    if "Invalid" in error_msg or "expired" in error_msg.lower():
                        st.error("❌ This password reset link has expired or is invalid.")
                        st.info("Please request a new password reset link from the login page.")
                    else:
                        st.error(f"Error resetting password: {error_msg}")
                        st.info("Please try again or contact your administrator.")

    # Help text
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 After resetting your password, you'll be automatically logged in and redirected to the dashboard.")
