#!/usr/bin/env python3
"""
Company Value Analysis Page
Atlas BPC 1 Financial Dashboard - Value focused analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import re

# Import from shared modules
from shared.airtable_connection import get_airtable_connection
from shared.page_components import get_period_display_text
from shared.auth_utils import require_auth, logout_user, get_current_user_name, get_current_user_email, is_super_admin
from shared.year_config import get_selected_years

@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes for better performance
def get_group_averages_for_debt(years_with_data):
    """Calculate group averages for Interest Bearing Debt with caching using bulk fetch"""
    airtable = get_airtable_connection()

    group_averages = []
    for year in years_with_data:
        period_filter = f"{year} Annual"

        # Use bulk fetch instead of individual company calls
        all_balance_data = airtable.get_all_companies_balance_sheet_by_period(period_filter, is_admin=is_super_admin())

        year_debt_values = []
        for company_data in all_balance_data:
            debt_value = company_data.get('interest_bearing_debt', 0)
            if debt_value is not None and debt_value != 0:
                year_debt_values.append(float(debt_value))

        # Calculate average for this year
        if year_debt_values:
            group_avg = sum(year_debt_values) / len(year_debt_values)
            group_averages.append(group_avg)
        else:
            group_averages.append(0)

    return group_averages

@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes for better performance
def get_group_averages_for_ebitda(years_with_data):
    """Calculate group averages for EBITDA with caching using bulk fetch"""
    airtable = get_airtable_connection()

    group_averages = []
    for year in years_with_data:
        period_filter = f"{year} Annual"

        # Use bulk fetch instead of individual company calls
        all_income_data = airtable.get_all_companies_income_statement_by_period(period_filter, is_admin=is_super_admin())

        year_ebitda_values = []
        for income_item in all_income_data:
            ebitda_value = income_item.get('ebitda_000', 0)

            # Add EBITDA value to the list
            if ebitda_value is not None and ebitda_value != 0:
                year_ebitda_values.append(float(ebitda_value))

        # Calculate average for this year
        if year_ebitda_values:
            group_avg = sum(year_ebitda_values) / len(year_ebitda_values)
            group_averages.append(group_avg)
        else:
            group_averages.append(0)

    return group_averages


@st.cache_data(ttl=900, show_spinner=False)
def get_group_value_averages(year=None):
    """Calculate group averages for all value metrics.
    Uses the same proven pattern as company_ratios.py - imports from group page.
    Defaults to CURRENT_YEAR from year_config for automatic yearly rollover."""
    from shared.year_config import CURRENT_YEAR
    from pages.group_pages.group_value import fetch_all_companies_value_trends
    if year is None:
        year = CURRENT_YEAR
    period_filter = f"{year} Annual"

    # Fetch per-company data using the same function the group page uses
    company_data = fetch_all_companies_value_trends(period_filter)
    if not company_data:
        return {}

    # Calculate derived fields per company (same logic as group_value.py lines 62-84)
    for comp_name, data in company_data.items():
        ebitda = data.get('ebitda_000', 0) or 0
        debt = data.get('interest_bearing_debt', 0) or 0
        equity_dollars = data.get('owners_equity', 0) or 0
        equity_000 = equity_dollars / 1000 if equity_dollars != 0 else 0

        three_x_ebitda = ebitda * 3
        company_value = three_x_ebitda - debt
        value_to_equity = company_value / equity_000 if equity_000 != 0 else 0

        data['_ebitda'] = ebitda
        data['_3x_ebitda'] = three_x_ebitda
        data['_debt'] = debt
        data['_company_value'] = company_value
        data['_equity_000'] = equity_000
        data['_value_to_equity'] = value_to_equity

    # Average across companies (excluding zeros)
    def avg_metric(field):
        vals = [company_data[c][field] for c in company_data if company_data[c].get(field, 0) != 0]
        return sum(vals) / len(vals) if vals else 0

    return {
        'EBITDA (000)': avg_metric('_ebitda'),
        '3 x EBITDA (000)': avg_metric('_3x_ebitda'),
        'Interest Bearing Debt (000)': avg_metric('_debt'),
        'Company Value (000)': avg_metric('_company_value'),
        'Equity (000)': avg_metric('_equity_000'),
        'Value to Equity': avg_metric('_value_to_equity')
    }


# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


def create_company_sidebar():
    """Create company-specific sidebar navigation"""
    with st.sidebar:        
        # Get current page for active state detection
        current_page = st.session_state.get('current_page', 'company_value')

        # CSS for consistent button styling with active state highlighting
        st.markdown("""
        <style>
            /* Remove default borders from all sidebar buttons first */
            section[data-testid="stSidebar"] .stButton > button {
                border: 1px solid #e2e8f0 !important;
            }

            /* Active button styling */
            section[data-testid="stSidebar"] .stButton > button.active-nav-button {
                border: 3px solid #1a202c !important;
                background-color: #edf2f7 !important;
                font-weight: 700 !important;
                box-shadow: inset 0 0 0 1px #1a202c, 0 2px 4px rgba(26, 32, 44, 0.2) !important;
            }
        </style>
        <script>
            // Add active-nav-button class to buttons with ▶ symbol
            function highlightActiveButtons() {
                const buttons = document.querySelectorAll('section[data-testid="stSidebar"] .stButton > button');
                buttons.forEach(button => {
                    if (button.textContent.includes('▶')) {
                        button.classList.add('active-nav-button');
                    } else {
                        button.classList.remove('active-nav-button');
                    }
                });
            }

            // Run on load and periodically to catch Streamlit rerenders
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', highlightActiveButtons);
            } else {
                highlightActiveButtons();
            }

            // Use MutationObserver to detect sidebar changes
            const observer = new MutationObserver(highlightActiveButtons);
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            if (sidebar) {
                observer.observe(sidebar, { childList: true, subtree: true });
            }

            // Also run after a short delay to catch late renders
            setTimeout(highlightActiveButtons, 100);
            setTimeout(highlightActiveButtons, 500);
        </script>
        """, unsafe_allow_html=True)

        # Helper function to create buttons with visual active indicator
        def button_wrapper(label, key, page_id, **kwargs):
            is_active = current_page == page_id
            # Add visual marker to active button label
            if is_active:
                display_label = f"▶ {label}"
            else:
                display_label = f"   {label}"  # Add spacing to align with active marker

            return st.button(display_label, key=key, **kwargs)


        # Overview button at the top
        # Overview button at the top
        if button_wrapper("🏠 Overview", key="value_nav_overview", page_id="overview", use_container_width=True):
            st.session_state.current_page = "overview"
            st.session_state.nav_tab = "group"
            st.rerun()
        
        # Analysis Type filter
        if 'nav_tab' not in st.session_state:
            st.session_state.nav_tab = 'company'
            
        analysis_options = ["Group", "Company"]
        current_selection = "Group" if st.session_state.nav_tab == 'group' else "Company"
        
        selected_analysis = st.selectbox(
            "**Analysis Type**",
            options=analysis_options,
            index=analysis_options.index(current_selection),
            key="value_analysis_type_selector"
        )
        
        # Handle analysis type changes
        if selected_analysis == "Group" and st.session_state.nav_tab != 'group':
            st.session_state.nav_tab = 'group'
            st.session_state.current_page = 'overview'
            st.rerun()
        elif selected_analysis == "Company" and st.session_state.nav_tab != 'company':
            st.session_state.nav_tab = 'company'
            st.session_state.current_page = 'company_ratios'
            st.rerun()
        
        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
        
        # Get companies for dropdown using shared connection
        airtable = get_airtable_connection()
        companies = airtable.get_companies()
        
        if companies:
            company_options = {comp['name']: comp['name'] for comp in sorted(companies, key=lambda x: x['name'])}
            
            # Get current selection or default to first company
            current_company = st.session_state.get('selected_company_name', list(company_options.keys())[0])
            if current_company not in company_options:
                current_company = list(company_options.keys())[0]
            
            # Company selector with unique key and preserved state
            selected_company_name = st.selectbox(
                "**Select Company Below**",
                options=list(company_options.keys()),
                key="company_value_selector",
                index=list(company_options.keys()).index(current_company)
            )
            st.session_state.selected_company_name = selected_company_name
        else:
            st.error("No companies found")
            return

        from shared.year_config import render_year_selector
        render_year_selector()

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Navigation buttons (matches other company pages)
        if button_wrapper("% Ratios", key="value_nav_ratios", page_id="company_ratios", use_container_width=True):
            st.session_state.current_page = "company_ratios"
            st.rerun()
        
        if button_wrapper("📊 Balance Sheet", key="value_nav_balance", page_id="company_balance_sheet", use_container_width=True):
            st.session_state.current_page = "company_balance_sheet"
            st.rerun()
        if button_wrapper("📈 Income Statement", key="value_nav_income", page_id="company_income_statement", use_container_width=True):
            st.session_state.current_page = "company_income_statement"
            st.rerun()
        if button_wrapper("💸 Cash Flow", key="value_nav_cash_flow", page_id="company_cash_flow", use_container_width=True):
            st.session_state.current_page = "company_cash_flow"
            st.rerun()
        if button_wrapper("👥 Labor Cost", key="value_nav_labor", page_id="company_labor_cost", use_container_width=True):
            st.session_state.current_page = "company_labor_cost"
            st.rerun()
        if button_wrapper("💎 Value", key="value_nav_value", page_id="company_value", use_container_width=True):
            st.session_state.current_page = "company_value"
            st.rerun()
        if button_wrapper("📋 Actuals", key="value_nav_actuals", page_id="company_actuals", use_container_width=True):
            st.session_state.current_page = "company_actuals"
            st.rerun()
        if button_wrapper("🏆 Wins & Challenges", key="value_nav_wins", page_id="company_wins_challenges", use_container_width=True):
            st.session_state.current_page = "company_wins_challenges"
            st.rerun()

        # ====================================================================
        # USER INFO & LOGOUT SECTION
        # ====================================================================
        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 1rem 0;"></div>', unsafe_allow_html=True)

        # User info display
        # Get user display info with validation
        user_name = get_current_user_name()
        user_email = get_current_user_email()

        # Validate consistency: if we have profile but no user, or vice versa, clear session
        if (user_name and not user_email) or (user_email and not user_name):
            from shared.auth_utils import clear_session, clear_cookies
            clear_session()
            clear_cookies()
            st.rerun()

        # If we have both, verify user_id matches between session.user and session.user_profile
        if user_name and user_email and st.session_state.user and st.session_state.user_profile:
            session_user_id = st.session_state.user.id
            profile_user_id = st.session_state.user_profile.get('id')

            if session_user_id != profile_user_id:
                from shared.auth_utils import clear_session, clear_cookies
                clear_session()
                clear_cookies()
                st.rerun()

        if user_name:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                    padding: 0.75rem;
                    border-radius: 8px;
                    margin-bottom: 0.5rem;
                    border-left: 3px solid #025a9a;
                ">
                    <div style="font-size: 0.7rem; color: #718096; margin-bottom: 0.2rem;">
                        Logged in as
                    </div>
                    <div style="font-weight: 600; color: #2d3748; font-size: 0.85rem; margin-bottom: 0.1rem;">
                        {user_name}
                    </div>
                    <div style="font-size: 0.7rem; color: #a0aec0;">
                        {user_email}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Admin badge if user is super admin
            if is_super_admin():
                st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #9f7aea 0%, #805ad5 100%);
                        color: white;
                        padding: 0.3rem 0.6rem;
                        border-radius: 6px;
                        text-align: center;
                        font-size: 0.75rem;
                        font-weight: 600;
                        margin-bottom: 0.5rem;
                    ">
                        🔑 Super Admin
                    </div>
                """, unsafe_allow_html=True)

        # Logout button
        st.markdown("""
            <style>
                /* Logout button styling */
                div[data-testid="column"] button[key="logout_button"] {
                    background: linear-gradient(135deg, #fc8181 0%, #f56565 100%) !important;
                    color: white !important;
                    border: none !important;
                    font-weight: 600 !important;
                    border-radius: 8px !important;
                    padding: 0.5rem !important;
                    box-shadow: 0 2px 4px rgba(245, 101, 101, 0.3) !important;
                }

                div[data-testid="column"] button[key="logout_button"]:hover {
                    background: linear-gradient(135deg, #f56565 0%, #fc8181 100%) !important;
                    transform: translateY(-1px) !important;
                }
            </style>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", key="logout_button", use_container_width=True):
            logout_user()  # This will clear session and reload the page


def create_company_value_page():
    # Require authentication
    require_auth()

    # CSS is already applied by main function - no need to duplicate
    
    # Initialize session state
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'value_overview'
    if 'selected_company_name' not in st.session_state:
        st.session_state.selected_company_name = None
    
    # Create company value specific sidebar with proper error handling (BEFORE page routing)
    try:
        # Clear the entire sidebar first
        st.sidebar.empty()
        
        # Create company value specific sidebar
        create_company_sidebar()
    except Exception as e:
        st.sidebar.error(f"Error creating sidebar: {str(e)}")
    
    # Handle page routing to other company pages
    if st.session_state.get('current_page') == 'company_ratios':
        from company_ratios import create_company_ratios_page
        create_company_ratios_page()
        return
    
    if st.session_state.get('current_page') == 'company_balance_sheet':
        from company_balance_sheet import create_company_balance_sheet_page
        create_company_balance_sheet_page()
        return
    
    if st.session_state.get('current_page') == 'company_income_statement':
        from company_income_statement import create_company_income_statement_page
        create_company_income_statement_page()
        return
    
    if st.session_state.get('current_page') == 'company_labor_cost':
        from company_labor_cost import create_company_labor_cost_page
        create_company_labor_cost_page()
        return
    
    if st.session_state.get('current_page') == 'company_actuals':
        from company_actuals import create_company_actuals_page
        create_company_actuals_page()
        return
    
    if st.session_state.get('current_page') == 'company_cash_flow':
        from company_cash_flow import create_company_cash_flow_page
        create_company_cash_flow_page()
        return
    
    if st.session_state.get('current_page') == 'company_wins_challenges':
        from company_wins_challenges import create_company_wins_challenges_page
        create_company_wins_challenges_page()
        return

    # Import centralized page components
    from shared.page_components import create_page_header

    # Get period display text
    period_text = get_period_display_text()
    
    # Determine page title based on selected company
    if st.session_state.selected_company_name:
        page_title = f"{st.session_state.selected_company_name} Value - {period_text}"
    else:
        page_title = f"Company Value Analysis - {period_text}"
    
    # Use centralized page header with consistent spacing
    create_page_header(
        page_title=page_title,
        show_period_selector=True
    )
    
    # Main content
    if st.session_state.selected_company_name:
        
        # Initialize Airtable connection using shared connection
        airtable = get_airtable_connection()

        # Get data for selected company
        with st.spinner(f"Loading {st.session_state.selected_company_name} value trends..."):
            balance_data = airtable.get_balance_sheet_data(st.session_state.selected_company_name, is_admin=is_super_admin())
            income_data = airtable.get_income_statement_data(st.session_state.selected_company_name, is_admin=is_super_admin())
        
        # Check if we have any data to display
        if not balance_data and not income_data:
            st.info(f"⚠️ No financial data found for {st.session_state.selected_company_name} for the 2024 Annual period.")
            st.info("💡 This might be because the data hasn't been uploaded yet or the company name doesn't match exactly.")
        
        # Display value sections
        if balance_data or income_data:
            display_value_sections(balance_data, income_data)
        else:
            # Show clear message when no real data is available
            st.info(f"📊 No financial data available for {st.session_state.selected_company_name}.")
            st.info("💡 Data may not have been uploaded yet for this company.")
    
    else:
        st.info("Please select a company from the sidebar to view value analysis.")


def display_value_sections(balance_data, income_data):
    """Display the value analysis sections"""

    # Get period text for section header
    period_text = get_period_display_text()

    # Display Value Trend Table
    table_data, years_with_data = display_value_trend_table(st.session_state.selected_company_name)

    # Display Value Trend Graphs
    if years_with_data:
        display_value_trend_graphs(st.session_state.selected_company_name, table_data, years_with_data)


def display_value_trend_table(company_name):
    """Display Value Trend Table with data from 2020-2024"""

    if not company_name:
        st.info("Please select a company to view value data.")
        return

    # Get Airtable connection
    airtable = get_airtable_connection()

    # Define years (dynamically from year config)
    years = get_selected_years()

    # Initialize table data with blank values
    table_data = {
        'EBITDA (000)': ['', '', '', '', ''],
        '3 x EBITDA (000)': ['', '', '', '', ''],
        'Interest Bearing Debt (000)': ['', '', '', '', ''],
        'Company Value (000)': ['', '', '', '', ''],
        'Equity (000)': ['', '', '', '', ''],
        'Value to Equity': ['', '', '', '', '']
    }

    # Fetch EBITDA and Interest Bearing Debt data for each year
    for i, year in enumerate(years):
        try:
            # Create period filter for the specific year
            period_filter = f"{year} Annual"

            # Get income statement data for EBITDA
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())

            if income_historical and len(income_historical) > 0:
                record = income_historical[0]  # Get the first record for this period

                # Look for EBITDA field (try different possible field names)
                ebitda_value = None
                for field_name in ['ebitda_000', 'ebitda', 'total_ebitda']:
                    if field_name in record and record[field_name] is not None and record[field_name] != '':
                        ebitda_value = record[field_name]
                        break

                if ebitda_value is not None and ebitda_value != '':
                    try:
                        # Convert to float and format as currency
                        ebitda_float = float(ebitda_value)

                        # Format EBITDA with parentheses for negative values
                        if ebitda_float < 0:
                            table_data['EBITDA (000)'][i] = f"$({abs(ebitda_float):,.0f})"
                        else:
                            table_data['EBITDA (000)'][i] = f"${ebitda_float:,.0f}"

                        # Calculate 3 x EBITDA
                        three_x_ebitda = ebitda_float * 3
                        if three_x_ebitda < 0:
                            table_data['3 x EBITDA (000)'][i] = f"$({abs(three_x_ebitda):,.0f})"
                        else:
                            table_data['3 x EBITDA (000)'][i] = f"${three_x_ebitda:,.0f}"

                        # Store 3x EBITDA value for company value calculation
                        table_data['_three_x_ebitda_raw'] = table_data.get('_three_x_ebitda_raw', ['', '', '', '', ''])
                        table_data['_three_x_ebitda_raw'][i] = three_x_ebitda
                    except (ValueError, TypeError):
                        # If conversion fails, leave blank
                        continue

            # Get balance sheet data for Interest Bearing Debt and Equity
            balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())

            if balance_historical and len(balance_historical) > 0:
                balance_record = balance_historical[0]  # Get the first record for this period

                # Look for Interest Bearing Debt field
                debt_value = balance_record.get('interest_bearing_debt', '')
                if debt_value is not None and debt_value != '':
                    try:
                        # Convert to float and format as currency with parentheses for negative values
                        debt_float = float(debt_value)
                        if debt_float < 0:
                            table_data['Interest Bearing Debt (000)'][i] = f'<span class="negative-value">$({abs(debt_float):,.0f})</span>'
                        else:
                            table_data['Interest Bearing Debt (000)'][i] = f"${debt_float:,.0f}"

                        # Store debt value for company value calculation
                        table_data['_debt_raw'] = table_data.get('_debt_raw', ['', '', '', '', ''])
                        table_data['_debt_raw'][i] = debt_float
                    except (ValueError, TypeError):
                        # If conversion fails, leave blank
                        continue

                # Look for Equity field
                equity_value = balance_record.get('equity_000', '')
                if equity_value is not None and equity_value != '':
                    try:
                        # Convert to float and format as currency with parentheses for negative values
                        equity_float = float(equity_value)
                        if equity_float < 0:
                            table_data['Equity (000)'][i] = f'<span class="negative-value">$({abs(equity_float):,.0f})</span>'
                        else:
                            table_data['Equity (000)'][i] = f"${equity_float:,.0f}"

                        # Store equity value for Value to Equity calculation
                        table_data['_equity_raw'] = table_data.get('_equity_raw', ['', '', '', '', ''])
                        table_data['_equity_raw'][i] = equity_float
                    except (ValueError, TypeError):
                        # If conversion fails, leave blank
                        continue

        except Exception as e:
            # Continue with blank values if data fetch fails
            continue

    # Calculate Company Value (000) = 3 x EBITDA (000) - Interest Bearing Debt (000)
    if '_three_x_ebitda_raw' in table_data and '_debt_raw' in table_data:
        for i in range(len(years)):
            try:
                three_x_ebitda = table_data['_three_x_ebitda_raw'][i]
                debt = table_data['_debt_raw'][i]

                # Only calculate if both values are available and numeric
                if (three_x_ebitda != '' and debt != '' and
                    three_x_ebitda is not None and debt is not None):
                    company_value = three_x_ebitda - debt
                    if company_value < 0:
                        table_data['Company Value (000)'][i] = f'<span class="negative-value">$({abs(company_value):,.0f})</span>'
                    else:
                        table_data['Company Value (000)'][i] = f"${company_value:,.0f}"

                    # Store company value for Value to Equity calculation
                    table_data['_company_value_raw'] = table_data.get('_company_value_raw', ['', '', '', '', ''])
                    table_data['_company_value_raw'][i] = company_value
            except (ValueError, TypeError, IndexError):
                # If calculation fails, leave blank
                continue

    # Calculate Value to Equity = Company Value (000) / Equity (000)
    if '_company_value_raw' in table_data and '_equity_raw' in table_data:
        for i in range(len(years)):
            try:
                company_value = table_data['_company_value_raw'][i]
                equity = table_data['_equity_raw'][i]

                # Only calculate if both values are available and numeric
                if (company_value != '' and equity != '' and
                    company_value is not None and equity is not None and equity != 0):
                    value_to_equity = company_value / equity
                    if value_to_equity < 0:
                        table_data['Value to Equity'][i] = f'<span class="negative-value">{value_to_equity:.2f}</span>'
                    else:
                        table_data['Value to Equity'][i] = f"{value_to_equity:.2f}"
            except (ValueError, TypeError, IndexError, ZeroDivisionError):
                # If calculation fails, leave blank
                continue

    # Remove the temporary raw value arrays before displaying the table
    table_data.pop('_three_x_ebitda_raw', None)
    table_data.pop('_debt_raw', None)
    table_data.pop('_company_value_raw', None)
    table_data.pop('_equity_raw', None)

    # Get group averages for current year (dynamic via CURRENT_YEAR)
    from shared.year_config import CURRENT_YEAR
    group_averages = get_group_value_averages()

    # Create and display the table
    create_value_trend_table(table_data, years, group_averages, CURRENT_YEAR)

    # Return the data and years with data for reuse in trend graphs
    years_with_data = []
    for i, year in enumerate(years):
        # Check if we have any meaningful data for this year
        has_data = False
        for key in ['EBITDA (000)', 'Interest Bearing Debt (000)', 'Company Value (000)', 'Equity (000)']:
            if key in table_data and i < len(table_data[key]) and table_data[key][i] != '':
                has_data = True
                break
        if has_data:
            years_with_data.append(year)

    return table_data, years_with_data


def create_value_trend_table(table_data, years, group_averages=None, avg_year=None):
    """Create and display the Value Trend Table with proper styling"""

    # Get period display text for dynamic heading
    period_text = get_period_display_text()

    # Table title with dynamic period text
    st.markdown(f"""
    <div style="margin: 1.5rem 0;">
        <h3 style="color: #1a202c; font-family: 'Montserrat', sans-serif; font-weight: 600; margin-bottom: 1rem;">Value Trend Table - {period_text}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Create table HTML with clean Atlas blue styling (matching labor cost table)
    table_html = """
    <style>
    .value-trend-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-family: 'Montserrat', sans-serif;
        border: 1px solid #025a9a;
    }
    .value-trend-table th {
        background-color: #025a9a;
        color: white;
        padding: 12px;
        text-align: center;
        font-weight: 600;
        border: 1px solid #025a9a;
    }
    .value-trend-table td {
        padding: 10px;
        border: 1px solid #025a9a;
        text-align: center;
        background-color: white;
    }
    .value-trend-table .row-label {
        background-color: white;
        color: #1a202c;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid #025a9a;
    }
    .value-trend-table .header-label {
        background-color: #025a9a;
        color: white;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid #025a9a;
    }
    .value-trend-table .category-header {
        background-color: #025a9a;
        color: white;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid #025a9a;
    }
    .value-trend-table .overall-rank {
        background-color: #f0f0f0;
        color: #1a202c;
        font-weight: 600;
        text-align: center;
        border: 1px solid #025a9a;
    }
    .value-trend-table .overall-rank-label {
        background-color: #f0f0f0;
        color: #1a202c;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid #025a9a;
    }
    .value-trend-table .subheading-label {
        background-color: #e0e0e0;
        color: #1a202c;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: none;
    }
    .value-trend-table .subheading-cell {
        background-color: #e0e0e0;
        border: none;
        text-align: center;
    }
    .negative-value {
        color: #c2002f !important;
        font-weight: 600;
    }
    </style>

    <table class="value-trend-table">
        <thead>
            <tr>
                <th class="header-label">Company Value</th>"""

    # Add year headers
    for year in years:
        table_html += f"<th>{year}</th>"
    # Add Group Avg header (dynamic year)
    if group_averages:
        avg_label = avg_year if avg_year else ""
        table_html += f'<th style="background-color: #025a9a; color: #ffe082; font-weight: 600;">Group Avg<br>({avg_label})</th>'
    table_html += "</tr></thead><tbody>"

    # Add category header for "Value based on current EBITDA" with light grey background
    table_html += f'<tr><td class="subheading-label">Value based on current EBITDA</td>'
    for year in years:
        table_html += '<td class="subheading-cell"></td>'
    if group_averages:
        table_html += '<td class="subheading-cell"></td>'
    table_html += '</tr>'

    # Add EBITDA-based value rows
    ebitda_rows = ['EBITDA (000)', '3 x EBITDA (000)', 'Interest Bearing Debt (000)', 'Company Value (000)']

    for row_name in ebitda_rows:
        table_html += f'<tr><td class="row-label">{row_name}</td>'

        for i, year in enumerate(years):
            if row_name in table_data:
                value = table_data[row_name][i]
                table_html += f'<td>{value}</td>'
            else:
                table_html += '<td></td>'
        # Add group average cell
        if group_averages:
            avg_val = group_averages.get(row_name, 0)
            if avg_val != 0:
                if avg_val < 0:
                    cell_content = f'<span class="negative-value">$({abs(avg_val):,.0f})</span>'
                else:
                    cell_content = f'${avg_val:,.0f}'
            else:
                cell_content = '-'
            table_html += f'<td style="background-color: #e3f2fd; font-weight: 600;">{cell_content}</td>'
        table_html += '</tr>'

    # Add category header for "Value based on book value and/or Goodwill*" with light grey background
    table_html += f'<tr><td class="subheading-label">Value based on book value and/or Goodwill*</td>'
    for year in years:
        table_html += '<td class="subheading-cell"></td>'
    if group_averages:
        table_html += '<td class="subheading-cell"></td>'
    table_html += '</tr>'

    # Add book value-based rows
    book_value_rows = ['Equity (000)', 'Value to Equity']

    for row_name in book_value_rows:
        table_html += f'<tr><td class="row-label">{row_name}</td>'
        for i, year in enumerate(years):
            if row_name in table_data:
                value = table_data[row_name][i]
                table_html += f'<td>{value}</td>'
            else:
                table_html += '<td></td>'
        # Add group average cell
        if group_averages:
            avg_val = group_averages.get(row_name, 0)
            if row_name == 'Value to Equity':
                # Format as ratio
                if avg_val != 0:
                    if avg_val < 0:
                        cell_content = f'<span class="negative-value">{avg_val:.2f}</span>'
                    else:
                        cell_content = f'{avg_val:.2f}'
                else:
                    cell_content = '-'
            else:
                # Format as currency
                if avg_val != 0:
                    if avg_val < 0:
                        cell_content = f'<span class="negative-value">$({abs(avg_val):,.0f})</span>'
                    else:
                        cell_content = f'${avg_val:,.0f}'
                else:
                    cell_content = '-'
            table_html += f'<td style="background-color: #e3f2fd; font-weight: 600;">{cell_content}</td>'
        table_html += '</tr>'

    table_html += "</tbody></table>"

    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)


def display_value_trend_graphs(company_name, table_data, years_with_data):
    """Display Value trend charts side by side below the table"""

    # Get period text for section header
    period_text = get_period_display_text()

    # Add section heading with same styling as labor cost trends
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="value-trends-section">
        <h2 class="section-title">Value Trend Graphs - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)

    # Add group average toggle control
    st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

    include_group_average = st.checkbox(
        "**Show Group Average Comparison**",
        value=False,  # Default to unchecked for faster loading
        help="Show group average bars for comparison (uncheck for faster loading)",
        key="company_value_show_group_average"
    )

    st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

    # Create two columns for side-by-side charts
    col1, col2 = st.columns(2)

    with col1:
        display_ebitda_trend(company_name, table_data, years_with_data, include_group_average)

    with col2:
        display_interest_bearing_debt_trend(company_name, table_data, years_with_data, include_group_average)


def display_interest_bearing_debt_trend(company_name, table_data, years_with_data, show_group_average=True):
    """Display Interest Bearing Debt (000) trend chart with optional group average comparison

    Args:
        company_name: Name of the company
        table_data: Table data containing debt values
        years_with_data: List of years with available data
        show_group_average: Boolean to show/hide group average bars (default: True)
    """

    # Prepare data for the chart - extract numerical values for selected company
    debt_values = []
    for year in years_with_data:
        year_index = get_selected_years().index(year)
        debt_str = table_data['Interest Bearing Debt (000)'][year_index]

        # Extract numerical value from formatted string
        if debt_str and debt_str != '':
            # Check if it's an HTML formatted negative value
            if '<span class="negative-value">' in debt_str:
                # Extract the value from within the span tags
                match = re.search(r'\$\(([0-9,]+)\)', debt_str)
                if match:
                    debt_value = -float(match.group(1).replace(',', ''))
                else:
                    debt_value = 0
            elif debt_str.startswith('$(') and debt_str.endswith(')'):
                # Negative value in parentheses (non-HTML)
                debt_value = -float(debt_str[2:-1].replace(',', ''))
            else:
                # Positive value
                debt_value = float(debt_str.replace('$', '').replace(',', ''))
            debt_values.append(debt_value)
        else:
            debt_values.append(0)

    # Get cached group averages only if needed
    if show_group_average:
        group_averages = get_group_averages_for_debt(years_with_data)
    else:
        group_averages = []

    debt_data = {
        'Year': [int(year) for year in years_with_data],
        'Company Debt': debt_values
    }

    if show_group_average:
        debt_data['Group Average'] = group_averages

    # Create the bar chart using Plotly (matching labor cost style)
    fig = go.Figure()

    # Create custom hover data for company debt
    company_hover_data = []
    for i, year in enumerate(debt_data['Year']):
        debt_val = debt_data['Company Debt'][i]

        if debt_val < 0:
            formatted_debt = f"$({abs(debt_val):,.0f})"
        else:
            formatted_debt = f"${debt_val:,.0f}"

        if show_group_average:
            group_val = debt_data['Group Average'][i]
            if group_val < 0:
                formatted_group = f"$({abs(group_val):,.0f})"
            else:
                formatted_group = f"${group_val:,.0f}"

            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"Interest Bearing Debt (000): <b>{formatted_debt}</b><br>" +
                f"Group Average: <b>{formatted_group}</b>"
            )
        else:
            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"Interest Bearing Debt (000): <b>{formatted_debt}</b>"
            )
        company_hover_data.append(hover_info)

    # Create custom hover data for group average (only if showing)
    group_hover_data = []
    if show_group_average:
        for i, year in enumerate(debt_data['Year']):
            avg_val = debt_data['Group Average'][i]
            company_val = debt_data['Company Debt'][i]

            if avg_val < 0:
                formatted_avg = f"$({abs(avg_val):,.0f})"
            else:
                formatted_avg = f"${avg_val:,.0f}"

            if company_val < 0:
                formatted_company = f"$({abs(company_val):,.0f})"
            else:
                formatted_company = f"${company_val:,.0f}"

            hover_info = (
                f"<b>Year {year} - Group Average</b><br>" +
                f"Interest Bearing Debt (000): <b>{formatted_avg}</b><br>" +
                f"{company_name}: <b>{formatted_company}</b>"
            )
            group_hover_data.append(hover_info)

    # Format bar text for company
    company_bar_text = []
    for val in debt_data['Company Debt']:
        if val < 0:
            company_bar_text.append(f'$({abs(val):,.0f})')
        else:
            company_bar_text.append(f'${val:,.0f}')

    # Format bar text for group average (only if showing)
    if show_group_average:
        group_bar_text = []
        for val in debt_data['Group Average']:
            if val < 0:
                group_bar_text.append(f'$({abs(val):,.0f})')
            else:
                group_bar_text.append(f'${val:,.0f}')

    # Add company debt bars
    fig.add_trace(go.Bar(
        x=debt_data['Year'],
        y=debt_data['Company Debt'],
        name=company_name,
        marker_color='#025a9a',  # Atlas blue
        text=company_bar_text,
        textposition='inside',
        textfont=dict(color='white', size=12, family='Montserrat'),
        customdata=company_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        offsetgroup=1
    ))

    # Add group average bars (only if showing)
    if show_group_average:
        fig.add_trace(go.Bar(
            x=debt_data['Year'],
            y=debt_data['Group Average'],
            name='Group Average',
            marker_color='#0e9cd5',  # Lighter Atlas blue for contrast
            text=group_bar_text,
            textposition='inside',
            textfont=dict(color='white', size=12, family='Montserrat'),
            customdata=group_hover_data,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
            offsetgroup=2
        ))

    fig.update_layout(
        title=dict(
            text="Interest Bearing Debt",
            font=dict(size=16, family='Montserrat', color='#1a202c'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Year",
            title_font={'size': 12}
        ),
        yaxis=dict(
            title="Amount ($000)",
            title_font={'size': 12}
        ),
        barmode='group',  # Display bars side by side
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat', size=12),
        margin=dict(l=50, r=50, t=50, b=50),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def display_ebitda_trend(company_name, table_data, years_with_data, show_group_average=True):
    """Display EBITDA (000) trend chart with optional group average comparison

    Args:
        company_name: Name of the company
        table_data: Table data containing EBITDA values
        years_with_data: List of years with available data
        show_group_average: Boolean to show/hide group average bars (default: True)
    """

    # Prepare data for the chart - extract numerical values for selected company
    ebitda_values = []
    for year in years_with_data:
        year_index = get_selected_years().index(year)
        ebitda_str = table_data['EBITDA (000)'][year_index]

        # Extract numerical value from formatted string
        if ebitda_str and ebitda_str != '':
            # Check if it's an HTML formatted negative value
            if '<span class="negative-value">' in ebitda_str:
                # Extract the value from within the span tags
                match = re.search(r'\$\(([0-9,]+)\)', ebitda_str)
                if match:
                    ebitda_value = -float(match.group(1).replace(',', ''))
                else:
                    ebitda_value = 0
            elif ebitda_str.startswith('$(') and ebitda_str.endswith(')'):
                # Negative value in parentheses (non-HTML)
                ebitda_value = -float(ebitda_str[2:-1].replace(',', ''))
            else:
                # Positive value
                ebitda_value = float(ebitda_str.replace('$', '').replace(',', ''))
            ebitda_values.append(ebitda_value)
        else:
            ebitda_values.append(0)

    # Get cached group averages only if needed
    if show_group_average:
        group_averages = get_group_averages_for_ebitda(years_with_data)
    else:
        group_averages = []

    ebitda_data = {
        'Year': [int(year) for year in years_with_data],
        'Company EBITDA': ebitda_values
    }

    if show_group_average:
        ebitda_data['Group Average'] = group_averages

    # Create the bar chart using Plotly (matching labor cost style)
    fig = go.Figure()

    # Create custom hover data for company EBITDA
    company_hover_data = []
    for i, year in enumerate(ebitda_data['Year']):
        ebitda_val = ebitda_data['Company EBITDA'][i]

        if ebitda_val < 0:
            formatted_ebitda = f"$({abs(ebitda_val):,.0f})"
        else:
            formatted_ebitda = f"${ebitda_val:,.0f}"

        if show_group_average:
            group_val = ebitda_data['Group Average'][i]
            if group_val < 0:
                formatted_group = f"$({abs(group_val):,.0f})"
            else:
                formatted_group = f"${group_val:,.0f}"

            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"EBITDA (000): <b>{formatted_ebitda}</b><br>" +
                f"Group Average: <b>{formatted_group}</b>"
            )
        else:
            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"EBITDA (000): <b>{formatted_ebitda}</b>"
            )
        company_hover_data.append(hover_info)

    # Create custom hover data for group average (only if showing)
    group_hover_data = []
    if show_group_average:
        for i, year in enumerate(ebitda_data['Year']):
            avg_val = ebitda_data['Group Average'][i]
            company_val = ebitda_data['Company EBITDA'][i]

            if avg_val < 0:
                formatted_avg = f"$({abs(avg_val):,.0f})"
            else:
                formatted_avg = f"${avg_val:,.0f}"

            if company_val < 0:
                formatted_company = f"$({abs(company_val):,.0f})"
            else:
                formatted_company = f"${company_val:,.0f}"

            hover_info = (
                f"<b>Year {year} - Group Average</b><br>" +
                f"EBITDA (000): <b>{formatted_avg}</b><br>" +
                f"{company_name}: <b>{formatted_company}</b>"
            )
            group_hover_data.append(hover_info)

    # Format bar text for company
    company_bar_text = []
    for val in ebitda_data['Company EBITDA']:
        if val < 0:
            company_bar_text.append(f'$({abs(val):,.0f})')
        else:
            company_bar_text.append(f'${val:,.0f}')

    # Format bar text for group average (only if showing)
    if show_group_average:
        group_bar_text = []
        for val in ebitda_data['Group Average']:
            if val < 0:
                group_bar_text.append(f'$({abs(val):,.0f})')
            else:
                group_bar_text.append(f'${val:,.0f}')

    # Add company EBITDA bars
    fig.add_trace(go.Bar(
        x=ebitda_data['Year'],
        y=ebitda_data['Company EBITDA'],
        name=company_name,
        marker_color='#025a9a',  # Atlas blue
        text=company_bar_text,
        textposition='inside',
        textfont=dict(color='white', size=12, family='Montserrat'),
        customdata=company_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        offsetgroup=1
    ))

    # Add group average bars (only if showing)
    if show_group_average:
        fig.add_trace(go.Bar(
            x=ebitda_data['Year'],
            y=ebitda_data['Group Average'],
            name='Group Average',
            marker_color='#0e9cd5',  # Lighter Atlas blue for contrast
            text=group_bar_text,
            textposition='inside',
            textfont=dict(color='white', size=12, family='Montserrat'),
            customdata=group_hover_data,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
            offsetgroup=2
        ))

    fig.update_layout(
        title=dict(
            text="EBITDA",
            font=dict(size=16, family='Montserrat', color='#1a202c'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Year",
            title_font={'size': 12}
        ),
        yaxis=dict(
            title="Amount ($000)",
            title_font={'size': 12}
        ),
        barmode='group',  # Display bars side by side
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat', size=12),
        margin=dict(l=50, r=50, t=50, b=50),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    create_company_value_page()