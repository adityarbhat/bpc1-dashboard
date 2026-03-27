"""
Group Export Page - Centralized Export Feature

Dedicated page for exporting all 7 group comparison pages to Excel.
Uses lazy loading to avoid performance impact on other pages.
"""

import streamlit as st
from shared.page_components import create_page_header, get_period_display_text
from shared.auth_utils import require_auth
from shared.year_config import CURRENT_YEAR


def create_group_export_page():
    """
    Dedicated export page with lazy loading.
    Only imports export_utils when this page is accessed.
    """

    # Require authentication
    require_auth()

    # Remove any custom selectbox styling to match other pages
    st.markdown("""
    <style>
    /* Remove blue border from Analysis Type selector in sidebar */
    div[data-testid="stSelectbox"] > div > div {
        border-color: #e2e8f0 !important;
    }
    div[data-testid="stSelectbox"] > div > div:focus,
    div[data-testid="stSelectbox"] > div > div:focus-within {
        border-color: #cbd5e0 !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Get current period from session state
    current_period = st.session_state.get('period', 'year_end')
    period_display = get_period_display_text()

    # Page header
    create_page_header(
        page_title=f"Export Group Analysis Data - {period_display}",
        subtitle=None,
        show_period_selector=True
    )

    # Add some spacing
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Info box
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                border-left: 4px solid #025a9a;
                padding: 1.5rem;
                margin: 1rem 0 2rem 0;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
        <h3 style="color: #025a9a; font-family: 'Montserrat', sans-serif; margin: 0 0 0.75rem 0; font-size: 1.3rem;">
            📊 Export Options
        </h3>
        <p style="color: #4a5568; font-family: 'Montserrat', sans-serif; margin: 0 0 0.5rem 0; font-size: 0.95rem;">
            • <strong>7 Sheets Included</strong>: Ratios, Balance Sheet, Income Statement, Labor Cost, Business Mix, Value, Cash Flow
        </p>
        <p style="color: #4a5568; font-family: 'Montserrat', sans-serif; margin: 0 0 0.5rem 0; font-size: 0.95rem;">
            • <strong>Current Period</strong>: {period_display}
        </p>
        <p style="color: #4a5568; font-family: 'Montserrat', sans-serif; margin: 0; font-size: 0.95rem;">
            • <strong>Export Time</strong>: Typically 5-15 seconds depending on data size
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Year selection section
    st.markdown("""
    <h3 style="color: #1a202c; font-family: 'Montserrat', sans-serif; font-weight: 600; margin: 1rem 0 1rem 0;">
        Select Year to Export
    </h3>
    """, unsafe_allow_html=True)

    available_years = list(range(CURRENT_YEAR, CURRENT_YEAR - 5, -1))

    # Create 5 columns for year buttons
    cols = st.columns(5)

    for idx, year in enumerate(available_years):
        with cols[idx]:
            export_key = f"export_{year}_{current_period}"

            # Button styling based on whether it's the current year
            button_type = "primary" if year == CURRENT_YEAR else "secondary"

            if st.button(
                f"📅 {year}",
                key=export_key,
                use_container_width=True,
                type=button_type
            ):
                # Lazy import - only loads when export button is clicked
                from shared.export_utils import create_multi_sheet_export, generate_filename

                with st.spinner(f"Generating {period_display} {year} export... Please wait."):
                    try:
                        excel_data = create_multi_sheet_export(current_period, year)
                        filename = generate_filename(current_period, year)

                        # Store in session state
                        st.session_state['export_data'] = excel_data
                        st.session_state['export_filename'] = filename
                        st.session_state['export_ready'] = True
                        st.session_state['export_year'] = year

                        st.success(f"✅ {year} {period_display} export ready!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Export failed: {str(e)}")
                        st.exception(e)  # Show full error for debugging

    # Download section (appears after successful generation)
    if st.session_state.get('export_ready', False):
        st.markdown("---")
        st.markdown("""
        <h3 style="color: #1a202c; font-family: 'Montserrat', sans-serif; font-weight: 600; margin: 1rem 0;">
            Download Your Export
        </h3>
        """, unsafe_allow_html=True)

        export_year = st.session_state.get('export_year', CURRENT_YEAR)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.download_button(
                label=f"💾 Download {export_year} {period_display} Excel File",
                data=st.session_state['export_data'],
                file_name=st.session_state['export_filename'],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_export",
                use_container_width=True,
                type="primary"
            )

            # Clear button to reset state
            if st.button("Clear", key="clear_export", use_container_width=True):
                st.session_state['export_ready'] = False
                st.session_state.pop('export_data', None)
                st.session_state.pop('export_filename', None)
                st.session_state.pop('export_year', None)
                st.rerun()


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="Export Group Data - BPC Dashboard",
        page_icon="📊",
        layout="wide"
    )
    create_group_export_page()
