"""Centralized year range configuration for company pages.

Provides a single source of truth for available years, default year ranges,
and the sidebar year selector widget. Group pages are not affected.
"""

CURRENT_YEAR = 2025
EARLIEST_YEAR = 2011


def get_default_years():
    """Returns last 5 years as strings: ['2021','2022','2023','2024','2025']"""
    return [str(CURRENT_YEAR - i) for i in range(4, -1, -1)]


def get_selected_years():
    """Read user's year selection from session_state, fallback to default."""
    import streamlit as st
    start = st.session_state.get('start_year', CURRENT_YEAR - 4)
    end = st.session_state.get('end_year', CURRENT_YEAR)
    return [str(y) for y in range(start, end + 1)]


def render_year_selector():
    """Render Start Year / End Year selectboxes side-by-side in sidebar.
    Enforces max 5-year span. Stores selection in session_state."""
    import streamlit as st

    # Initialize defaults
    if 'start_year' not in st.session_state:
        st.session_state.start_year = CURRENT_YEAR - 4
    if 'end_year' not in st.session_state:
        st.session_state.end_year = CURRENT_YEAR

    all_years = list(range(EARLIEST_YEAR, CURRENT_YEAR + 1))

    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox(
            "Start Year", options=all_years,
            index=all_years.index(st.session_state.start_year),
            key="start_year_selector"
        )

    # End year options: from start_year to min(start_year+4, CURRENT_YEAR)
    max_end = min(start_year + 4, CURRENT_YEAR)
    end_options = list(range(start_year, max_end + 1))

    # Clamp current end_year to valid range
    current_end = st.session_state.end_year
    if current_end not in end_options:
        current_end = end_options[-1]

    with col2:
        end_year = st.selectbox(
            "End Year", options=end_options,
            index=end_options.index(current_end),
            key="end_year_selector"
        )

    st.session_state.start_year = start_year
    st.session_state.end_year = end_year
