#!/usr/bin/env python3
"""
Company Actuals Analysis Page
Atlas BPC 1 Financial Dashboard - Actuals focused analysis
"""

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Import from shared modules
from shared.airtable_connection import get_airtable_connection
from shared.page_components import get_period_display_text
from shared.auth_utils import require_auth, logout_user, get_current_user_name, get_current_user_email, is_super_admin
from shared.year_config import get_selected_years

# Load environment variables from .env file for local development
load_dotenv()

@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes for better performance
def get_all_actuals_data_cached(company_name, years_tuple=None):
    """Fetch all actuals data (balance sheet and income statement) with caching"""
    from shared.year_config import get_default_years
    airtable = get_airtable_connection()
    years = list(years_tuple) if years_tuple else get_default_years()

    # Initialize data storage
    balance_data = {}
    income_data = {}

    for year in years:
        period_filter = f"{year} Annual"

        # Fetch balance sheet data for this year
        balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
        if balance_historical and len(balance_historical) > 0:
            balance_data[year] = balance_historical[0]
        else:
            balance_data[year] = {}

        # Fetch income statement data for this year
        income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
        if income_historical and len(income_historical) > 0:
            income_data[year] = income_historical[0]
        else:
            income_data[year] = {}

    return balance_data, income_data

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


def create_company_sidebar():
    """Create company-specific sidebar navigation"""
    with st.sidebar:        
        # Get current page for active state detection
        current_page = st.session_state.get('current_page', 'company_actuals')

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
        if button_wrapper("🏠 Overview", key="actuals_nav_overview", page_id="overview", use_container_width=True):
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
            key="actuals_analysis_type_selector"
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
                key="company_actuals_selector",
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
        if button_wrapper("% Ratios", key="actuals_nav_ratios", page_id="company_ratios", use_container_width=True):
            st.session_state.current_page = "company_ratios"
            st.rerun()
        
        if button_wrapper("📊 Balance Sheet", key="actuals_nav_balance", page_id="company_balance_sheet", use_container_width=True):
            st.session_state.current_page = "company_balance_sheet"
            st.rerun()
        if button_wrapper("📈 Income Statement", key="actuals_nav_income", page_id="company_income_statement", use_container_width=True):
            st.session_state.current_page = "company_income_statement"
            st.rerun()
        if button_wrapper("💸 Cash Flow", key="actuals_nav_cash_flow", page_id="company_cash_flow", use_container_width=True):
            st.session_state.current_page = "company_cash_flow"
            st.rerun()
        if button_wrapper("👥 Labor Cost", key="actuals_nav_labor", page_id="company_labor_cost", use_container_width=True):
            st.session_state.current_page = "company_labor_cost"
            st.rerun()
        if button_wrapper("💎 Value", key="actuals_nav_value", page_id="company_value", use_container_width=True):
            st.session_state.current_page = "company_value"
            st.rerun()
        if button_wrapper("📋 Actuals", key="actuals_nav_actuals", page_id="company_actuals", use_container_width=True):
            st.session_state.current_page = "company_actuals"
            st.rerun()
        if button_wrapper("🏆 Wins & Challenges", key="actuals_nav_wins", page_id="company_wins_challenges", use_container_width=True):
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


def create_company_actuals_page():
    # Require authentication
    require_auth()

    # CSS is already applied by main function - no need to duplicate
    
    # Initialize session state
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'actuals_overview'
    if 'selected_company_name' not in st.session_state:
        st.session_state.selected_company_name = None
    
    # Create company actuals specific sidebar with proper error handling (BEFORE page routing)
    try:
        # Clear the entire sidebar first
        st.sidebar.empty()
        
        # Create company actuals specific sidebar
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
    
    if st.session_state.get('current_page') == 'company_value':
        from company_value import create_company_value_page
        create_company_value_page()
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
        page_title = f"{st.session_state.selected_company_name} Actuals - {period_text}"
    else:
        page_title = f"Company Actuals Analysis - {period_text}"
    
    # Use centralized page header with consistent spacing
    create_page_header(
        page_title=page_title,
        show_period_selector=True
    )
    
    # Main content
    if st.session_state.selected_company_name:

        # Get cached historical data for selected years - OPTIMIZED!
        years = get_selected_years()
        with st.spinner(f"Loading {st.session_state.selected_company_name} financial data..."):
            balance_historical_data, income_historical_data = get_all_actuals_data_cached(st.session_state.selected_company_name, tuple(years))

        # Get current year data for compatibility (some functions may still need it)
        airtable = get_airtable_connection()
        balance_data = airtable.get_balance_sheet_data(st.session_state.selected_company_name, is_admin=is_super_admin())
        income_data = airtable.get_income_statement_data(st.session_state.selected_company_name, is_admin=is_super_admin())

        # Check if we have any data to display
        has_historical_data = any(balance_historical_data.values()) or any(income_historical_data.values())
        has_current_data = balance_data or income_data

        if not has_historical_data and not has_current_data:
            st.info(f"⚠️ No financial data found for {st.session_state.selected_company_name}.")
            st.info("💡 This might be because the data hasn't been uploaded yet or the company name doesn't match exactly.")

        # Display actuals sections with historical data
        if has_historical_data or has_current_data:
            display_actuals_sections(balance_data, income_data, balance_historical_data, income_historical_data)
        else:
            # Show clear message when no real data is available
            st.info(f"📊 No financial data available for {st.session_state.selected_company_name}.")
            st.info("💡 Data may not have been uploaded yet for this company.")
    
    else:
        st.info("Please select a company from the sidebar to view actuals analysis.")


def display_actuals_sections(balance_data, income_data, balance_historical_data, income_historical_data):
    """Display the actuals analysis sections with Balance Sheet and Income Statement tabs"""

    # Get period text for section header
    period_text = get_period_display_text()

    # Actuals Analysis Section
    st.markdown(f"""
    <div class="actuals-analysis-section">
        <h2 class="section-title">Actuals Analysis - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)

    # Create tabs for Balance Sheet and Income Statement
    balance_tab, income_tab = st.tabs(["Balance Sheet", "Income Statement"])

    with balance_tab:
        display_balance_sheet_actuals_table(st.session_state.selected_company_name, balance_historical_data)
    
    with income_tab:
        display_income_statement_actuals_table(st.session_state.selected_company_name, income_historical_data)
    
    # Add CSS for the analysis section and tables
    st.markdown("""
    <style>
    .actuals-analysis-section {
        margin: 2rem 0 1rem 0;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 1rem;
        font-family: 'Montserrat', sans-serif;
    }
    
    /* Atlas-themed table styling */
    .actuals-table-container {
        max-height: 800px;
        overflow-y: auto;
        position: relative;
        margin: 1rem 0;
    }

    .actuals-table {
        border-collapse: collapse;
        width: 100%;
        font-family: 'Montserrat', sans-serif;
    }

    .actuals-table thead {
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .actuals-table th {
        background-color: #025a9a;
        color: white;
        padding: 12px 8px;
        text-align: center;
        font-weight: 600;
        border: 1px solid #ddd;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    .actuals-table th:first-child {
        text-align: left;
        background-color: #025a9a;
    }
    
    .actuals-table td {
        padding: 8px;
        text-align: right;
        border: 1px solid #ddd;
        background-color: white;
    }
    
    .actuals-table td:first-child {
        text-align: left;
        font-weight: 500;
        background-color: #f8f9fa;
    }

    .actuals-table .total-row {
        background-color: #f0f0f0 !important;
        font-weight: 600;
    }

    .actuals-table .total-row td {
        background-color: #f0f0f0 !important;
    }

    .actuals-table .total-row td:first-child {
        font-weight: 600;
    }

    .actuals-table .major-total-row {
        background-color: #e0e0e0 !important;
        font-weight: 700;
        font-size: 1.05em;
    }

    .actuals-table .major-total-row td {
        background-color: #e0e0e0 !important;
        font-weight: 700;
        border-top: 2px solid #025a9a !important;
        border-bottom: 2px solid #025a9a !important;
    }

    .actuals-table .major-total-row td:first-child {
        font-weight: 700;
    }
    
    .negative-value {
        color: #c2002f;
    }
    
    .atlas-red-text {
        color: #c2002f !important;
        font-weight: 600;
    }
    
    .no-data {
        color: #6c757d;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)


def display_balance_sheet_actuals_table(company_name, balance_historical_data):
    """Display the Balance Sheet Actuals Table with historical data from 2020-2024"""

    if not company_name:
        st.info("Please select a company to view the balance sheet actuals table.")
        return

    # Use cached historical data instead of making API calls
    years = get_selected_years()
    table_data = {}

    # Balance sheet line items based on data_transformation_bs.py BALANCE_SHEET_MAPPING
    # Format: ('Display Name', 'airtable_field_name', is_total_row, is_major_total)
    balance_sheet_items = [
        # Current Assets Section Header
        ('Current Assets', 'header_current_assets', True, True),  # Header row with dark grey highlighting
        ('Cash And Cash Equivalents', 'cash_and_cash_equivalents', False, False),
        ('Trade Accounts Receivable', 'trade_accounts_receivable', False, False),
        ('Receivables', 'receivables', False, False),
        ('Other Receivables', 'other_receivables', False, False),
        ('Prepaid Expenses', 'prepaid_expenses', False, False),
        ('Related Company Receivables', 'related_company_receivables', False, False),
        ('Owner Receivables', 'owner_receivables', False, False),
        ('Other Current Assets', 'other_current_assets', False, False),
        ('Total Current Assets', 'total_current_assets', True, False),

        # Fixed Assets Section
        ('Gross Fixed Assets', 'gross_fixed_assets', False, False),
        ('Accumulated Depreciation (-)', 'accumulated_depreciation', False, False),
        ('Net Fixed Assets', 'net_fixed_assets', True, False),  # Green background like totals

        # Other Assets
        ('Inter Company Receivable', 'inter_company_receivable', False, False),
        ('Other Assets', 'other_assets', False, False),
        ('TOTAL ASSETS', 'total_assets', True, True),  # MAJOR TOTAL - darker green

        # Current Liabilities
        ('Notes Payable Bank', 'notes_payable_bank', False, False),
        ('Notes Payable Owners', 'notes_payable_owners', False, False),
        ('Trade Accounts Payable', 'trade_accounts_payable', False, False),
        ('Accrued Expenses', 'accrued_expenses', False, False),
        ('Current Portion LTD', 'current_portion_ltd', False, False),
        ('Inter Company Payable', 'inter_company_payable', False, False),
        ('Other Current Liabilities', 'other_current_liabilities', False, False),
        ('Total Current Liabilities', 'total_current_liabilities', True, False),

        # Long-term Liabilities
        ('EID Loan', 'eid_loan', False, False),
        ('Long Term Debt', 'long_term_debt', False, False),
        ('Notes Payable Owners LT', 'notes_payable_owners_lt', False, False),
        ('Inter Company Debt', 'inter_company_debt', False, False),
        ('Other LT Liabilities', 'other_lt_liabilities', False, False),
        ('Total Long Term Liabilities', 'total_long_term_liabilities', True, False),
        ('Total Liabilities', 'total_liabilities', True, False),

        # Equity
        ('Owners Equity', 'owners_equity', True, False),  # Light grey background like other totals
        ('TOTAL LIABILITIES & EQUITY', 'total_liabilities_equity', True, True)  # MAJOR TOTAL - darker grey
    ]

    # Initialize data storage
    for item_name, field_name, is_total, is_major_total in balance_sheet_items:
        table_data[item_name] = {}

    # Use cached data instead of making API calls
    available_fields = set()
    has_data = False

    for year in years:
        if year in balance_historical_data and balance_historical_data[year]:
            record = balance_historical_data[year]

            # Store data for each line item
            for item_name, field_name, is_total, is_major_total in balance_sheet_items:
                value = record.get(field_name, 0) or 0
                table_data[item_name][year] = value

            # Track what fields actually have data
            for key, value in record.items():
                if value and value != 0:
                    available_fields.add(key)
                    has_data = True
        else:
            # No data for this year - store None
            for item_name, field_name, is_total, is_major_total in balance_sheet_items:
                table_data[item_name][year] = None
    
    if not has_data:
        st.info(f"📊 No balance sheet data available for {company_name} for the years 2020-2024.")
        return
    
    
    # Create the table HTML
    def format_currency(value, field_name=None):
        # Always show empty for header fields
        if field_name and field_name.startswith('header_'):
            return ''
        elif value is None or value == 0:
            return '<span class="no-data">-</span>'
        elif value < 0:
            return f'<span class="negative-value">(${abs(value):,.0f})</span>'
        else:
            return f'${value:,.0f}'

    table_html = '<div class="actuals-table-container"><table class="actuals-table"><thead>'

    # Header row
    table_html += '<tr>'
    table_html += '<th>Data Type</th>'
    for year in years:
        table_html += f'<th>{year}</th>'
    table_html += '</tr></thead><tbody>'

    # Data rows - only show rows where we have the field available
    for item_name, field_name, is_total, is_major_total in balance_sheet_items:
        # Only show this row if the field exists in our available data
        if field_name in available_fields or is_total:  # Always show total rows
            # Determine row class based on total type
            if is_major_total:
                row_class = 'major-total-row'
            elif is_total:
                row_class = 'total-row'
            else:
                row_class = ''
            
            table_html += f'<tr class="{row_class}">'
            
            # Apply special styling to Accumulated Depreciation
            if item_name == 'Accumulated Depreciation (-)':
                table_html += f'<td><span class="atlas-red-text">{item_name}</span></td>'
            else:
                table_html += f'<td>{item_name}</td>'
            
            for year in years:
                value = table_data[item_name].get(year)
                table_html += f'<td>{format_currency(value, field_name)}</td>'

            table_html += '</tr>'

    table_html += '</tbody></table></div>'

    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)


def display_income_statement_actuals_table(company_name, income_historical_data):
    """Display the Income Statement Actuals Table with historical data from 2020-2024"""
    
    if not company_name:
        st.info("Please select a company to view the income statement actuals table.")
        return
    
    # Use cached historical data instead of making API calls
    years = get_selected_years()
    table_data = {}

    # Income statement line items based on data_transformation_is.py INCOME_STATEMENT_MAPPING
    # Format: ('Display Name', 'airtable_field_name', is_total_row, is_major_total)
    income_statement_items = [
        # Administrative Employees header section
        ('Useful Data Points', 'header_admin_employees', True, True),  # Header row with dark grey
        ('# Administrative Employees', 'administrative_employees', False, False),
        ('# of Branches', 'number_of_branches', False, False),

        # Revenue Section
        ('Revenue', 'header_revenue', True, True),  # Header row with dark grey
        ('Intra State HHG', 'intra_state_hhg', False, False),
        ('Local HHG', 'local_hhg', False, False),
        ('Inter State HHG', 'inter_state_hhg', False, False),
        ('Office Industrial', 'office_industrial', False, False),
        ('Warehouse', 'warehouse', False, False),
        ('Warehouse Handling', 'warehouse_handling', False, False),
        ('International', 'international', False, False),
        ('Packing Unpacking', 'packing_unpacking', False, False),
        ('Booking Royalties', 'booking_royalties', False, False),
        ('Special Products', 'special_products', False, False),
        ('Records Storage', 'records_storage', False, False),
        ('Military DPM Contracts', 'military_dpm_contracts', False, False),
        ('Distribution', 'distribution', False, False),
        ('Hotel Deliveries', 'hotel_deliveries', False, False),
        ('Other Revenue', 'other_revenue', False, False),
        ('Total Revenue', 'total_revenue', True, True),  # Major total - dark grey like TOTAL ASSETS
        
        # Cost of Revenue Section
        ('Direct Expenses', 'header_direct_expenses', True, True),  # Header row with dark grey
        ('Direct Wages', 'direct_wages', False, False),
        ('Vehicle Operating Expenses', 'vehicle_operating_expenses', False, False),
        ('Packing & Warehouse Supplies', 'packing_warehouse_supplies', False, False),
        ('Owner Operator - Intra State', 'oo_exp_intra_state', False, False),
        ('Owner Operator - Inter State', 'oo_inter_state', False, False),
        ('Owner Operator - Office & Industrial', 'oo_oi', False, False),
        ('Owner Operator - Packing', 'oo_packing', False, False),
        ('Owner Operator - General & Other', 'oo_other', False, False),
        ('Claims', 'claims', False, False),
        ('Other Transportation Expenses', 'other_trans_exp', False, False),
        ('Depreciation/Amortization', 'depreciation', False, False),
        ('Total Direct Expenses', 'calculated_total_direct_expenses', True, False),  # Calculated total with light grey
        ('Gross Profit $', 'gross_profit', True, False),  # From income statement table - light grey
        ('Gross Profit Margin %', 'gpm', True, False),  # From income statement table, percentage - light grey
        ('Operating Expenses', 'header_operating_expenses', True, True),  # Header row with dark grey
        ('Lease Expense Rev Equip', 'lease_expense_rev_equip', False, False),
        ('Rent', 'rent', False, False),
        ('Other Direct Expenses', 'other_direct_expenses', False, False),
        
        # Operating Expenses Section
        ('Advertising Marketing', 'advertising_marketing', False, False),
        ('Bad Debts', 'bad_debts', False, False),
        ('Sales Commissions', 'sales_commissions', False, False),
        ('Contributions', 'contributions', False, False),
        ('Computer Support', 'computer_support', False, False),
        ('Dues & Subscriptions', 'dues_sub', False, False),
        ('Payroll Taxes & Benefits', 'pr_taxes_benefits', False, False),
        ('Equipment Leases Office Equip', 'equipment_leases_office_equip', False, False),
        ('Workmans Comp Insurance', 'workmans_comp_insurance', False, False),
        ('Insurance', 'insurance', False, False),
        ('Legal Accounting', 'legal_accounting', False, False),
        ('Office Expense', 'office_expense', False, False),
        ('Other Administrative', 'other_admin', False, False),
        ('Pension, profit sharing, 401K', 'pension_profit_sharing_401k', False, False),
        ('Professional Fees', 'prof_fees', False, False),
        ('Repairs & Maintenance', 'repairs_maint', False, False),
        ('Salaries - Administrative', 'salaries_admin', False, False),
        ('Taxes & Licenses', 'taxes_licenses', False, False),
        ('Telephone/Fax/Utilities/Internet', 'tel_fax_utilities_internet', False, False),
        ('Travel & Entertainment', 'travel_ent', False, False),
        ('Vehicle Expense - Administrative', 'vehicle_expense_admin', False, False),
        ('Total Operating Expenses', 'total_operating_expenses', True, False),
        ('Operating Profit $', 'operating_profit', True, False),
        ('Operating Profit Margin %', 'opm', True, False),  # Light grey background like rows above
        ('Other Income & Expense', 'header_other_income_expense', True, True),  # Header row with dark grey
        
        # Non-Operating Section
        ('Other Income', 'other_income', False, False),
        ('CEO Compensation (-)', 'ceo_comp', False, False),
        ('Other Expense (-)', 'other_expense', False, False),
        ('Interest Expense (-)', 'interest_expense', False, False),
        ('Total Other Income & Expense', 'total_nonoperating_income', True, False),
        ('Profit Before Tax With PPP', 'profit_before_tax_with_ppp', True, False),
        ('Net Profit $', 'net_profit', True, False),  # From income statement table - light grey
        ('Net Profit Margin %', 'npm', True, False),  # From income statement table, percentage - light grey
        ('EBITDA', 'ebitda', True, False)  # From income statement table - light grey
    ]
    
    # Initialize data storage
    for item_name, field_name, is_total, is_major_total in income_statement_items:
        table_data[item_name] = {}
    
    # Use cached data instead of making API calls
    available_fields = set()
    has_data = False

    for year in years:
        if year in income_historical_data and income_historical_data[year]:
            income_record = income_historical_data[year]

            # Store data for each line item
            for item_name, field_name, is_total, is_major_total in income_statement_items:
                if field_name == 'calculated_total_direct_expenses':
                    # Calculate sum of Direct Expenses (from Direct Wages to Depreciation/Amortization)
                    direct_expense_fields = [
                        'direct_wages', 'vehicle_operating_expenses', 'packing_warehouse_supplies',
                        'oo_exp_intra_state', 'oo_inter_state', 'oo_oi', 'oo_packing', 'oo_other',
                        'claims', 'other_trans_exp', 'depreciation'
                    ]
                    total_direct = sum(income_record.get(field, 0) or 0 for field in direct_expense_fields)
                    table_data[item_name][year] = total_direct
                elif field_name == 'gpm':
                    _rev = income_record.get('total_revenue', 0) or 0
                    _gp = income_record.get('gross_profit', 0) or 0
                    value = (_gp / _rev) if _rev > 0 else (income_record.get('gpm', 0) or 0)
                    table_data[item_name][year] = value
                elif field_name == 'opm':
                    _rev = income_record.get('total_revenue', 0) or 0
                    _op = income_record.get('operating_profit', 0) or 0
                    value = (_op / _rev) if _rev > 0 else (income_record.get('opm', 0) or 0)
                    table_data[item_name][year] = value
                elif field_name == 'npm':
                    _rev = income_record.get('total_revenue', 0) or 0
                    _np = income_record.get('net_profit', 0) or 0
                    value = (_np / _rev) if _rev > 0 else (income_record.get('npm', 0) or 0)
                    table_data[item_name][year] = value
                elif field_name in ['gross_profit', 'ebitda', 'net_profit']:
                    # Get from income statement data
                    value = income_record.get(field_name, 0) or 0
                    # EBITDA is stored in thousands in Airtable — convert to full dollars
                    if field_name == 'ebitda' and value != 0:
                        value = value * 1000
                    table_data[item_name][year] = value
                else:
                    value = income_record.get(field_name, 0) or 0
                    table_data[item_name][year] = value

            # Track what fields actually have data
            for key, value in income_record.items():
                if value and value != 0:
                    available_fields.add(key)
                    has_data = True
        else:
            # No data for this year - store None
            for item_name, field_name, is_total, is_major_total in income_statement_items:
                if field_name == 'calculated_total_direct_expenses':
                    table_data[item_name][year] = 0  # Default to 0 for calculated fields
                else:
                    table_data[item_name][year] = None
    
    if not has_data:
        st.info(f"📊 No income statement data available for {company_name} for the years 2020-2024.")
        return
    
    
    # Create the table HTML
    def format_currency(value):
        if value is None or value == 0:
            return '<span class="no-data">-</span>'
        elif value < 0:
            return f'<span class="negative-value">(${abs(value):,.0f})</span>'
        else:
            return f'${value:,.0f}'
    
    def format_employees(value):
        """Special formatting for employee count"""
        if value is None or value == 0:
            return '<span class="no-data">-</span>'
        else:
            return f'{int(value)}'
    
    def format_percentage(value):
        """Special formatting for percentage values - round to nearest whole number"""
        if value is None or value == 0:
            return '<span class="no-data">-</span>'
        else:
            # Handle both percentage format (e.g., 95) and decimal format (e.g., 0.95)
            if value < 1:
                # Assume decimal format, convert to percentage
                return f'{round(value * 100)}%'
            else:
                # Assume already in percentage format
                return f'{round(value)}%'

    table_html = '<div class="actuals-table-container"><table class="actuals-table"><thead>'

    # Header row
    table_html += '<tr>'
    table_html += '<th>Data Type</th>'
    for year in years:
        table_html += f'<th>{year}</th>'
    table_html += '</tr></thead><tbody>'

    # Data rows - only show rows where we have the field available
    for item_name, field_name, is_total, is_major_total in income_statement_items:
        # Only show this row if the field exists in our available data
        if field_name in available_fields or is_total or field_name.startswith('header_') or field_name.startswith('calculated_'):  # Always show total, header, and calculated rows
            # Determine row class based on total type
            if is_major_total:
                row_class = 'major-total-row'
            elif is_total:
                row_class = 'total-row'
            else:
                row_class = ''
            
            table_html += f'<tr class="{row_class}">'
            
            # Apply special styling to expense items
            if item_name in ['CEO Compensation (-)', 'Other Expense (-)', 'Interest Expense (-)']:
                # Split the text to make the (-) part red
                base_text = item_name.replace(' (-)', '')
                table_html += f'<td><span class="atlas-red-text">{base_text} <span class="atlas-red-text">(-)</span></span></td>'
            else:
                table_html += f'<td>{item_name}</td>'
            
            for year in years:
                value = table_data[item_name].get(year)
                # Always show empty for header fields
                if field_name.startswith('header_'):
                    table_html += '<td></td>'
                # Special formatting for Administrative Employees (number field)
                elif field_name in ['administrative_employees', 'number_of_branches']:
                    table_html += f'<td>{format_employees(value)}</td>'
                # Special formatting for percentage fields (round to nearest whole number)
                elif field_name in ['gpm', 'opm', 'npm']:
                    table_html += f'<td>{format_percentage(value)}</td>'
                else:
                    table_html += f'<td>{format_currency(value)}</td>'

            table_html += '</tr>'

    table_html += '</tbody></table></div>'

    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)


if __name__ == "__main__":
    create_company_actuals_page()