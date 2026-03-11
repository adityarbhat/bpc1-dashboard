"""
BPC Dashboard - Login Page
===========================
User authentication page with email/password login.

This page provides:
- Login form with email and password
- Link to password reset page
- Professional Atlas Van Lines branding
- Error handling and user feedback
"""

import streamlit as st
import base64
import os
from shared.auth_utils import login_user, init_session_state


@st.cache_data
def get_logo_base64():
    """Load and encode IM AI Consultants logo as base64 (cached for performance)"""
    try:
        logo_path = os.path.join(os.path.dirname(__file__), '../../assets/imai_logo.png')
        with open(logo_path, 'rb') as f:
            logo_bytes = f.read()
        return base64.b64encode(logo_bytes).decode()
    except:
        return None


def show_login_page():
    """
    Display the login page.

    This function can be called from any page that requires authentication.
    """
    # Apply custom CSS FIRST - before any rendering to prevent sidebar flash
    st.markdown("""
        <style>
            /* Hide default Streamlit elements on login page */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            /* Hide sidebar navigation */
            [data-testid="stSidebarNav"] {display: none !important;}
            section[data-testid="stSidebar"] {display: none !important;}

            /* Login page specific styling */
            .login-container {
                max-width: 450px;
                margin: 50px auto;
                padding: 40px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .login-header {
                text-align: center;
                margin-bottom: 30px;
            }

            .login-title {
                color: #025a9a;
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 10px;
            }

            .login-subtitle {
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

            /* Login button and form submit button */
            .stButton > button,
            button[data-testid="baseButton-primary"],
            button[data-testid="baseButton-primaryFormSubmit"],
            div[data-testid="stForm"] button[type="submit"],
            form button[type="submit"] {
                width: 100%;
                background-color: #025a9a !important;
                background: #025a9a !important;
                color: white !important;
                border: 2px solid #025a9a !important;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: background-color 0.3s;
            }

            .stButton > button:hover,
            button[data-testid="baseButton-primary"]:hover,
            button[data-testid="baseButton-primaryFormSubmit"]:hover,
            div[data-testid="stForm"] button[type="submit"]:hover,
            form button[type="submit"]:hover {
                background-color: #034f87 !important;
                background: #034f87 !important;
                border-color: #034f87 !important;
            }

            /* Links */
            .forgot-password-link {
                text-align: center;
                margin-top: 20px;
            }

            .forgot-password-link a {
                color: #025a9a;
                text-decoration: none;
                font-size: 14px;
            }

            .forgot-password-link a:hover {
                text-decoration: underline;
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    init_session_state()

    # Check for tokens in URL - route to appropriate page
    try:
        query_params = st.query_params
        token = query_params.get('token', None)
        token_hash = query_params.get('token_hash', None)
        type_param = query_params.get('type', None)
        access_token = query_params.get('access_token', None)

        # Also check for error parameters (password reset link clicked)
        error = query_params.get('error', None)
        error_description = query_params.get('error_description', None)

        # If there's a password reset token (email link or alternative format)
        if (access_token and type_param == 'recovery') or \
           (type_param == 'recovery') or \
           (error and 'recovery' in str(error_description).lower()):
            from pages.auth.reset_password import show_reset_password_page
            show_reset_password_page()
            st.stop()

        # If there's an invitation token, redirect to set password page
        if (token or token_hash) and type_param == 'invite':
            from pages.auth.set_password import show_set_password_page
            show_set_password_page()
            st.stop()
    except Exception as e:
        pass  # Continue to normal login if query params fail

    # Add JavaScript to handle hash-based URL parameters from Supabase
    st.markdown("""
        <script>
        // Check if there are hash parameters (Supabase sometimes uses # instead of ?)
        if (window.location.hash) {
            const hashParams = new URLSearchParams(window.location.hash.substring(1));
            const access_token = hashParams.get('access_token');
            const type = hashParams.get('type');

            // If we have password reset tokens in the hash, convert to query params
            if (access_token && type === 'recovery') {
                const newUrl = window.location.pathname + '?' + window.location.hash.substring(1);
                window.location.href = newUrl;
            }
        }
        </script>
    """, unsafe_allow_html=True)

    # Center container
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Logo and header
        logo_b64 = get_logo_base64()

        if logo_b64:
            # With IM AI logo
            st.markdown(f"""
                <div class="login-header">
                    <div class="login-title">🔐 BPC1 Dashboard</div>
                    <a href="https://www.imaiconsultants.com" target="_blank" style="text-decoration: none; display: block; margin-top: 15px;">
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px;">
                            <img src="data:image/png;base64,{logo_b64}" style="height: 60px; width: auto;" alt="IM AI" />
                            <span style="color: #666; font-size: 13px; font-weight: 500;">Powered by IM AI</span>
                        </div>
                    </a>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback without logo
            st.markdown("""
                <div class="login-header">
                    <div class="login-title">🔐 BPC1 Dashboard</div>
                    <div style="margin-top: 8px;">
                        <a href="https://www.imaiconsultants.com" target="_blank" style="text-decoration: none; color: #666; font-size: 12px; font-weight: 500;">
                            Powered by IM AI
                        </a>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Login form (no key to avoid duplicate form error)
        with st.form(key="login_form_unique", clear_on_submit=False):
            st.markdown("### Sign In")

            email = st.text_input(
                "Email Address",
                placeholder="john@company.com"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            submit_button = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        # Handle form submission OUTSIDE the form to avoid widget conflicts
        if submit_button:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                # Attempt login (no spinner to avoid widget conflict)
                result = login_user(email, password)

                if result['success']:
                    # Immediately redirect to dashboard without delays
                    st.rerun()
                else:
                    # Display error messages
                    if result['message'] == "WIDGET_CONFLICT_ERROR":
                        # This should no longer happen, but keep as fallback
                        st.info("👆 Please click the Sign In button above to log in.")
                    else:
                        st.error(result['message'])

        # Forgot password link
        st.markdown("<br>", unsafe_allow_html=True)

        # Use columns to center the forgot password text
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            if st.button("Forgot Password?", use_container_width=True, type="secondary"):
                st.session_state.show_forgot_password = True
                st.rerun()

        # Help text
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="text-align: center; margin-top: 20px; padding: 12px; background: #e6f7ff; border-radius: 8px; border-left: 4px solid #025a9a;">
                <p style="margin: 0; color: #4a5568; font-size: 14px;">
                    📧 For support, email <a href="mailto:adi@imaiconsultants.com" style="color: #025a9a; text-decoration: none; font-weight: 600;">adi@imaiconsultants.com</a>
                </p>
            </div>
        """, unsafe_allow_html=True)


# Standalone page version (for direct navigation only when run as main script)
if __name__ == "__main__":
    show_login_page()
