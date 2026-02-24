"""
BPC Dashboard - Forgot Password Page
====================================
Password reset request page.

This page allows users to request a password reset link
via email.
"""

import streamlit as st
import base64
import os
from shared.auth_utils import send_password_reset_email, init_session_state


def get_logo_base64():
    """Load and encode IM AI Consultants logo as base64"""
    try:
        logo_path = os.path.join(os.path.dirname(__file__), '../../assets/imai_logo.png')
        with open(logo_path, 'rb') as f:
            logo_bytes = f.read()
        return base64.b64encode(logo_bytes).decode()
    except:
        return None


def show_forgot_password_page():
    """
    Display the forgot password page.
    """
    # Initialize session state
    init_session_state()

    # Apply custom CSS (similar to login page)
    st.markdown("""
        <style>
            /* Hide default Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            /* Page specific styling */
            .reset-container {
                max-width: 450px;
                margin: 50px auto;
                padding: 40px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .reset-header {
                text-align: center;
                margin-bottom: 30px;
            }

            .reset-title {
                color: #025a9a;
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 10px;
            }

            .reset-subtitle {
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

            /* Buttons */
            .stButton > button {
                width: 100%;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }

            /* Primary button */
            div[data-testid="column"]:nth-child(1) .stButton > button {
                background-color: #025a9a;
                color: white;
                border: none;
            }

            div[data-testid="column"]:nth-child(1) .stButton > button:hover {
                background-color: #034f87;
            }
        </style>
    """, unsafe_allow_html=True)

    # Center container
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Header with IM AI Consultants branding
        logo_b64 = get_logo_base64()

        if logo_b64:
            # With IM AI logo
            st.markdown(f"""
                <div class="reset-header">
                    <div class="reset-title">🔑 Reset Password</div>
                    <a href="https://www.imaiconsultants.com" target="_blank" style="text-decoration: none; display: block; margin-top: 15px;">
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px;">
                            <img src="data:image/png;base64,{logo_b64}" style="height: 60px; width: auto;" alt="IM AI" />
                            <span style="color: #666; font-size: 13px; font-weight: 500;">Powered by IM AI</span>
                        </div>
                    </a>
                    <div class="reset-subtitle" style="margin-top: 12px;">Enter your email to receive a reset link</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback without logo
            st.markdown("""
                <div class="reset-header">
                    <div class="reset-title">🔑 Reset Password</div>
                    <div style="margin-top: 8px;">
                        <a href="https://www.imaiconsultants.com" target="_blank" style="text-decoration: none; color: #666; font-size: 12px; font-weight: 500;">
                            Powered by IM AI
                        </a>
                    </div>
                    <div class="reset-subtitle" style="margin-top: 12px;">Enter your email to receive a reset link</div>
                </div>
            """, unsafe_allow_html=True)

        # Reset form
        with st.form("reset_form", clear_on_submit=False):
            st.markdown("### Request Password Reset")

            st.markdown("""
                Enter your email address and we'll send you a link to reset your password.
                The link will be valid for 1 hour.
            """)

            st.markdown("<br>", unsafe_allow_html=True)

            email = st.text_input(
                "Email Address",
                placeholder="john@company.com",
                key="reset_email"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            col_submit, col_back = st.columns(2)

            with col_submit:
                submit_button = st.form_submit_button("Send Reset Link", use_container_width=True)

            with col_back:
                back_button = st.form_submit_button("Back to Login", use_container_width=True, type="secondary")

            if submit_button:
                if not email:
                    st.error("Please enter your email address.")
                elif '@' not in email:
                    st.error("Please enter a valid email address.")
                else:
                    # Send password reset email
                    with st.spinner("Sending reset link..."):
                        result = send_password_reset_email(email)

                    if result['success']:
                        st.success(result['message'])
                        st.info("💡 **Tip:** Check your spam folder if you don't see the email within a few minutes.")
                    else:
                        st.error(result['message'])

            if back_button:
                st.session_state.show_forgot_password = False
                st.rerun()

        # Help text
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("📧 Still having trouble? Contact your administrator for assistance.")


# Standalone page version
if __name__ == "__main__":
    show_forgot_password_page()
