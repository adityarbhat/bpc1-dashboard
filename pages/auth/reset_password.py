"""
BPC Dashboard - Reset Password Page
====================================
Handles password reset flow after user clicks email link.

This page:
- Detects password reset tokens in URL parameters
- Allows users to enter a new password
- Updates password in Supabase
- Automatically logs them in
"""

import streamlit as st
import base64
import os
from shared.supabase_connection import get_supabase_client
from shared.auth_utils import init_session_state, load_user_profile, log_audit_event


def get_logo_base64():
    """Load and encode IM AI Consultants logo as base64"""
    try:
        logo_path = os.path.join(os.path.dirname(__file__), '../../assets/imai_logo.png')
        with open(logo_path, 'rb') as f:
            logo_bytes = f.read()
        return base64.b64encode(logo_bytes).decode()
    except:
        return None


def show_reset_password_page():
    """
    Display the reset password page for users who clicked the reset link.
    """
    # Initialize session state
    init_session_state()

    # Apply custom CSS
    st.markdown("""
        <style>
            /* Hide default Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

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
                    <h1 style="color: #025a9a; font-size: 28px; font-weight: bold;">🔐 Reset Your Password</h1>
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
                    <h1 style="color: #025a9a;">🔐 Reset Your Password</h1>
                    <a href="https://www.imaiconsultants.com" target="_blank" style="text-decoration: none; color: #666; font-size: 12px;">
                        Powered by IM AI
                    </a>
                </div>
            """, unsafe_allow_html=True)

        # Check for access_token in URL (this is what Supabase sends after email click)
        try:
            query_params = st.query_params
            access_token = query_params.get('access_token', None)
            type_param = query_params.get('type', None)
        except:
            access_token = None
            type_param = None

        if not access_token:
            st.error("❌ Invalid or missing password reset link.")
            st.info("Please request a new password reset link from the login page.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Back to Login", use_container_width=True):
                st.query_params.clear()
                st.rerun()
            return

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
                placeholder="Enter your new password"
            )

            confirm_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter your new password"
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
                            # Set the session with the access token from URL
                            supabase.auth.set_session(access_token, st.query_params.get('refresh_token', ''))

                            # Update the password
                            response = supabase.auth.update_user({
                                'password': new_password
                            })

                            if response.user:
                                # Store user info in session
                                st.session_state.user = response.user
                                st.session_state.access_token = access_token
                                st.session_state.authenticated = True

                                # Load user profile
                                load_user_profile(response.user.id)

                                # Log successful password reset
                                company_id = st.session_state.user_profile.get('company_id') if st.session_state.get('user_profile') else None
                                log_audit_event(
                                    user_id=response.user.id,
                                    action="password_reset_completed",
                                    resource="auth",
                                    company_id=company_id
                                )

                                st.success("✅ Password updated successfully! Redirecting to dashboard...")
                                st.balloons()

                                # Clear URL parameters and redirect
                                st.query_params.clear()
                                st.rerun()
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
        st.info("💡 After resetting your password, you'll be automatically logged in.")


# Standalone page version
if __name__ == "__main__":
    show_reset_password_page()
