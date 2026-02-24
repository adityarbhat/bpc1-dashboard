"""
Wins, Challenges & Action Items Admin Page
Allows administrators to upload W&C data via Excel template
"""

import streamlit as st
import pandas as pd
import os
from shared.airtable_connection import get_airtable_connection, get_companies_cached
from shared.css_styles import apply_all_styles
from shared.page_components import create_page_header
from shared.auth_utils import require_auth
from pages.data_input.wc_excel_parser import parse_wc_excel, validate_wc_data
from pages.data_input.wc_uploader import upload_wc_to_airtable, get_draft_counts_for_period


def create_wins_challenges_admin_page():
    """Main admin page for managing wins, challenges, and action items via Excel upload"""
    # Require authentication - CRITICAL ADMIN PAGE
    require_auth()

    # Import auth utils for role checking
    from shared.auth_utils import is_super_admin

    # SUPER ADMIN ONLY - Restrict access to this page
    if not is_super_admin():
        st.error("⛔ Access Denied")
        st.warning("This page is only accessible to Super Administrators.")
        st.info("Company users can only upload their Income Statement and Balance Sheet data using the Upload Data page.")

        # Show a button to go back to dashboard
        if st.button("🏠 Return to Dashboard", type="primary"):
            st.session_state.current_page = "overview"
            st.rerun()

        st.stop()  # Stop execution of the rest of the page

    # 1. Minimal CSS for selectbox styling (matching working pages)
    st.markdown("""
    <style>
    div[data-testid="stSelectbox"] > div > div {
        border-color: #e2e8f0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 2. Page header FIRST (creates banner at top)
    create_page_header(
        banner_text="Manage Wins & Challenges",
        show_period_selector=False
    )

    # 3. Create sidebar AFTER header
    create_admin_sidebar()

    # 4. Apply global styles LAST
    apply_all_styles()

    # Instructions
    st.markdown("""
    <div style="background: #f7fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #025a9a; margin-bottom: 1.5rem;">
        <p style="margin: 0; font-size: 1rem; color: #4a5568; line-height: 1.6;">
            <strong>Instructions:</strong> Select a company and period below, then upload the W&C Excel template.
            Data will be saved as <strong>DRAFT</strong> (not visible on dashboard until published).
            Re-uploading will <strong>overwrite</strong> existing drafts for the same company/period.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Company and period selection
    col1, col2 = st.columns(2)

    with col1:
        # Get companies
        companies = get_companies_cached()
        company_names = [c['name'] for c in companies]

        if 'selected_company_admin' not in st.session_state:
            st.session_state.selected_company_admin = company_names[0] if company_names else None

        selected_company = st.selectbox(
            "**Select Company**",
            options=company_names,
            index=company_names.index(st.session_state.selected_company_admin) if st.session_state.selected_company_admin in company_names else 0,
            key="company_selector_admin"
        )
        st.session_state.selected_company_admin = selected_company

    with col2:
        # Period selection - simplified to Annual and H1
        period_options = {
            "2024 Year End": "2024 Annual",
            "2024 Mid Year": "2024 H1",
            "2025 Year End": "2025 Annual",
            "2025 Mid Year": "2025 H1"
        }

        if 'selected_period_admin' not in st.session_state:
            st.session_state.selected_period_admin = "2024 Year End"

        selected_period_display = st.selectbox(
            "**Select Period**",
            options=list(period_options.keys()),
            index=list(period_options.keys()).index(st.session_state.selected_period_admin) if st.session_state.selected_period_admin in period_options.keys() else 0,
            key="period_selector_admin"
        )
        st.session_state.selected_period_admin = selected_period_display
        period_name = period_options[selected_period_display]

    # Display selected combination
    st.markdown(f"""
    <div style="background: #e6f7ff; padding: 0.75rem; border-radius: 6px; text-align: center; margin-bottom: 1.5rem;">
        <strong style="color: #025a9a;">Managing: {selected_company} - {period_name}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Show existing draft counts if any
    show_existing_drafts(selected_company, period_name)

    # File uploader section
    st.markdown("### Upload Excel File with Wins, Challenges & Action Items")

    uploaded_file = st.file_uploader(
        "Choose your filled Excel template",
        type=['xlsx', 'xls'],
        help="Upload the BPC2 W&C Upload Template with your Wins, Challenges, and Action Items filled in.",
        key="wc_file_uploader"
    )

    if uploaded_file is not None:
        handle_file_upload(uploaded_file, selected_company, period_name)


def create_admin_sidebar():
    """Create sidebar navigation for admin page"""
    with st.sidebar:
        st.markdown("### 🏆 Wins & Challenges Admin")

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Navigation back to dashboard
        if st.button("🏠 Back to Dashboard", key="back_to_dashboard_admin", use_container_width=True):
            st.session_state.current_page = "overview"
            st.session_state.nav_tab = "group"
            st.rerun()

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Download template button
        template_path = "bpc_upload_template/BPC2_WC_Upload_Template.xlsx"
        if os.path.exists(template_path):
            with open(template_path, "rb") as f:
                st.download_button(
                    label="📥 Download W&C Template",
                    data=f,
                    file_name="BPC2_WC_Upload_Template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Download the Excel template for uploading Wins, Challenges, and Action Items"
                )
        else:
            st.warning("Template file not found")


def show_existing_drafts(company_name: str, period_name: str):
    """Show warning if drafts already exist for this company/period"""
    existing_counts = get_draft_counts_for_period(company_name, period_name)
    total_existing = existing_counts['wins'] + existing_counts['challenges'] + existing_counts['action_items']

    if total_existing > 0:
        st.markdown(f"""
        <div style="background: #fef3c7; padding: 1rem; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 1rem;">
            <p style="margin: 0; font-size: 0.95rem; color: #92400e;">
                <strong>⚠️ Existing Drafts Found:</strong> {existing_counts['wins']} wins, {existing_counts['challenges']} challenges, {existing_counts['action_items']} action items
                <br><span style="font-size: 0.85rem;">Re-uploading will <strong>replace</strong> these drafts.</span>
            </p>
        </div>
        """, unsafe_allow_html=True)


def handle_file_upload(uploaded_file, company_name: str, period_name: str):
    """Handle the uploaded Excel file - parse and show preview"""

    # Parse the file
    with st.spinner("Parsing Excel file..."):
        results, warnings = parse_wc_excel(uploaded_file)

    # Show any warnings from parsing
    if warnings:
        with st.expander("⚠️ Parsing Warnings", expanded=True):
            for warning in warnings:
                st.warning(warning)

    # Validate data
    is_valid, errors = validate_wc_data(results)
    if not is_valid:
        for error in errors:
            st.error(error)
        return

    # Show preview in tabs
    st.markdown("### Preview Parsed Data")

    tab1, tab2, tab3 = st.tabs([
        f"✓ Wins ({results['wins_count']})",
        f"⚠ Challenges ({results['challenges_count']})",
        f"→ Action Items ({results['action_items_count']})"
    ])

    with tab1:
        if results['wins']:
            df_wins = pd.DataFrame(results['wins'])
            df_wins.columns = ['Win Description', 'Display Order']
            st.dataframe(df_wins, hide_index=True, use_container_width=True)
        else:
            st.info("No wins found in uploaded file")

    with tab2:
        if results['challenges']:
            df_challenges = pd.DataFrame(results['challenges'])
            df_challenges.columns = ['Challenge Description', 'Display Order']
            st.dataframe(df_challenges, hide_index=True, use_container_width=True)
        else:
            st.info("No challenges found in uploaded file")

    with tab3:
        if results['action_items']:
            df_action_items = pd.DataFrame(results['action_items'])
            df_action_items.columns = ['Action Item Description', 'Display Order']
            st.dataframe(df_action_items, hide_index=True, use_container_width=True)
        else:
            st.info("No action items found in uploaded file")

    # Summary
    total_items = results['wins_count'] + results['challenges_count'] + results['action_items_count']
    st.markdown(f"""
    <div style="background: #e6f7ff; padding: 0.75rem; border-radius: 6px; margin: 1rem 0;">
        <strong style="color: #025a9a;">Total Items to Upload:</strong> {total_items}
        ({results['wins_count']} wins, {results['challenges_count']} challenges, {results['action_items_count']} action items)
    </div>
    """, unsafe_allow_html=True)

    # Check for existing drafts warning
    existing_counts = get_draft_counts_for_period(company_name, period_name)
    total_existing = existing_counts['wins'] + existing_counts['challenges'] + existing_counts['action_items']

    if total_existing > 0:
        st.warning(f"⚠️ {total_existing} existing draft(s) will be **overwritten** by this upload.")

    # Initialize session state for upload
    if 'uploading_wc' not in st.session_state:
        st.session_state.uploading_wc = False
    if 'wc_upload_result' not in st.session_state:
        st.session_state.wc_upload_result = None

    # Show previous upload result if exists
    if st.session_state.wc_upload_result:
        result = st.session_state.wc_upload_result
        if result['success']:
            st.success(f"✅ {result['message']}")
            st.markdown(f"""
            <div style="background: #d1fae5; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <p style="margin: 0; color: #065f46;">
                    <strong>Upload Complete:</strong><br>
                    • {result['counts']['wins']} win(s) saved as draft<br>
                    • {result['counts']['challenges']} challenge(s) saved as draft<br>
                    • {result['counts']['action_items']} action item(s) saved as draft<br>
                    <br>
                    <em>Go to User Management → Publish W&C to publish these drafts.</em>
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"❌ {result['message']}")
        # Clear result after displaying
        st.session_state.wc_upload_result = None

    # Upload button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("📤 Upload as Draft", type="primary", use_container_width=True, key="upload_wc_draft"):
            with st.spinner("Uploading to Airtable..."):
                success, message, counts = upload_wc_to_airtable(
                    company_name=company_name,
                    period_name=period_name,
                    wins=results['wins'],
                    challenges=results['challenges'],
                    action_items=results['action_items']
                )
                # Store result in session state
                st.session_state.wc_upload_result = {
                    'success': success,
                    'message': message,
                    'counts': counts
                }
                # Clear caches
                st.cache_data.clear()
                st.rerun()


def perform_upload(results: dict, company_name: str, period_name: str):
    """Perform the actual upload to Airtable"""

    with st.spinner("Uploading to Airtable..."):
        success, message, counts = upload_wc_to_airtable(
            company_name=company_name,
            period_name=period_name,
            wins=results['wins'],
            challenges=results['challenges'],
            action_items=results['action_items']
        )

    if success:
        st.success(f"✅ {message}")
        st.markdown(f"""
        <div style="background: #d1fae5; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <p style="margin: 0; color: #065f46;">
                <strong>Upload Complete:</strong><br>
                • {counts['wins']} win(s) saved as draft<br>
                • {counts['challenges']} challenge(s) saved as draft<br>
                • {counts['action_items']} action item(s) saved as draft<br>
                <br>
                <em>Go to User Management → Publish Data to publish these drafts.</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Clear the file uploader by forcing a rerun
        st.cache_data.clear()

    else:
        st.error(f"❌ {message}")
        if counts['wins'] > 0 or counts['challenges'] > 0 or counts['action_items'] > 0:
            st.warning(f"Partial upload: {counts['wins']} wins, {counts['challenges']} challenges, {counts['action_items']} action items were saved.")


if __name__ == "__main__":
    create_wins_challenges_admin_page()
