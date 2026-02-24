"""
BPC Dashboard - Set Password Page
==================================
Handles new user invitation flow - allows users to set their password
after clicking the invitation link.

This page:
- Detects invitation tokens in URL parameters
- Allows new users to set their password
- Automatically logs them in after password is set
- Professional Atlas Van Lines branding
"""

import streamlit as st
import base64
import os
from shared.supabase_connection import get_supabase_client


def get_logo_base64():
    """Load and encode IM AI Consultants logo as base64"""
    try:
        logo_path = os.path.join(os.path.dirname(__file__), '../../assets/imai_logo.png')
        with open(logo_path, 'rb') as f:
            logo_bytes = f.read()
        return base64.b64encode(logo_bytes).decode()
    except:
        return None


def show_set_password_page():
    """
    Display the set password page for invited users.

    This page is shown when users click the invitation link in their email.
    """
    # Apply custom CSS for set password page
    st.markdown("""
        <style>
            /* Hide default Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            /* Set password page styling */
            .password-container {
                max-width: 500px;
                margin: 50px auto;
                padding: 40px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .password-header {
                text-align: center;
                margin-bottom: 30px;
            }

            .password-title {
                color: #025a9a;
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 10px;
            }

            .password-subtitle {
                color: #666;
                font-size: 16px;
            }

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
                cursor: pointer;
                transition: background-color 0.3s;
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

            .password-requirements h4 {
                margin-top: 0;
                color: #025a9a;
            }

            .password-requirements ul {
                margin: 10px 0 0 0;
                padding-left: 20px;
            }

            .password-requirements li {
                margin: 5px 0;
                color: #666;
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
                <div class="password-header">
                    <div class="password-title">🔐 Set Your Password</div>
                    <div class="password-subtitle">Welcome to BPC1 Dashboard</div>
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
                <div class="password-header">
                    <div class="password-title">🔐 Set Your Password</div>
                    <div class="password-subtitle">Welcome to BPC1 Dashboard</div>
                    <div style="margin-top: 8px;">
                        <a href="https://www.imaiconsultants.com" target="_blank" style="text-decoration: none; color: #666; font-size: 12px; font-weight: 500;">
                            Powered by IM AI
                        </a>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Check for token in URL (Streamlit's experimental get query params)
        try:
            query_params = st.query_params
            token = query_params.get('token', None)
            token_hash = query_params.get('token_hash', None)
            type_param = query_params.get('type', None)

            # Handle both token formats
            access_token = token or token_hash
        except:
            access_token = None

        if not access_token:
            st.error("❌ Invalid or missing invitation link.")
            st.info("Please check your email and click the invitation link again.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.show_set_password = False
                st.rerun()
            return

        # Show password requirements
        st.markdown("""
            <div class="password-requirements">
                <h4>Password Requirements:</h4>
                <ul>
                    <li>At least 8 characters long</li>
                    <li>Mix of uppercase and lowercase letters recommended</li>
                    <li>Include numbers and special characters for security</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        # Password setup form
        with st.form(key="set_password_form", clear_on_submit=False):
            st.markdown("### Create Your Password")

            password = st.text_input(
                "New Password",
                type="password",
                placeholder="Enter your password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            submit_button = st.form_submit_button("Set Password & Sign In", use_container_width=True)

            if submit_button:
                # Validate inputs
                if not password or not confirm_password:
                    st.error("Please fill in all fields.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters long.")
                elif password != confirm_password:
                    st.error("Passwords do not match. Please try again.")
                else:
                    # Update password using Supabase
                    try:
                        supabase = get_supabase_client()

                        with st.spinner("Setting up your account..."):
                            # Verify the token and update password
                            response = supabase.auth.verify_otp({
                                'token_hash': access_token,
                                'type': 'invite'
                            })

                            if response.user:
                                # Update the password
                                supabase.auth.update_user({
                                    'password': password
                                })

                                # Auto-login the user
                                st.session_state.user = response.user
                                st.session_state.access_token = response.session.access_token
                                st.session_state.refresh_token = response.session.refresh_token
                                st.session_state.authenticated = True

                                # Load user profile
                                from shared.auth_utils import load_user_profile, log_audit_event
                                load_user_profile(response.user.id)

                                # Log successful password setup
                                company_id = st.session_state.user_profile.get('company_id') if st.session_state.get('user_profile') else None
                                log_audit_event(
                                    user_id=response.user.id,
                                    action="password_setup",
                                    resource="auth",
                                    company_id=company_id
                                )

                                st.success("✅ Password set successfully! Redirecting to dashboard...")
                                st.balloons()

                                # Clear the token from URL and redirect
                                st.query_params.clear()
                                st.session_state.show_set_password = False
                                st.rerun()
                            else:
                                st.error("Invalid or expired invitation link. Please contact your administrator.")

                    except Exception as e:
                        error_msg = str(e)

                        if "Invalid token" in error_msg or "expired" in error_msg.lower():
                            st.error("❌ This invitation link has expired or is invalid.")
                            st.info("Please contact your administrator to resend the invitation.")
                        else:
                            st.error(f"Error setting password: {error_msg}")
                            st.info("Please try again or contact your administrator.")

        # Help text
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 After setting your password, you'll be automatically logged in.")


# Standalone page version
if __name__ == "__main__":
    show_set_password_page()
