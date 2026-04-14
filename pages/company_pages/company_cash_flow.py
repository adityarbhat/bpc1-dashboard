#!/usr/bin/env python3
"""
Company Cash Flow Analysis Page
Atlas BPC 1 Financial Dashboard - Cash Flow focused analysis
"""

import streamlit as st
from dotenv import load_dotenv
import plotly.graph_objects as go

# Import from shared modules
from shared.airtable_connection import get_airtable_connection
from shared.page_components import get_period_display_text
from shared.auth_utils import require_auth, logout_user, get_current_user_name, get_current_user_email, is_super_admin
from shared.year_config import get_selected_years

# Load environment variables from .env file for local development
load_dotenv()

# Global cache for group averages (persists across all users/sessions)
_GLOBAL_GROUP_AVERAGES_CACHE = None


@st.cache_data(ttl=900, show_spinner=False)
def get_group_cash_flow_averages(year=None):
    """Calculate group averages for all cash flow metrics.
    Uses the same proven pattern as company_ratios.py - imports from group page.
    Defaults to CURRENT_YEAR from year_config for automatic yearly rollover."""
    from shared.year_config import CURRENT_YEAR
    from pages.group_pages.group_cash_flow import fetch_all_companies_cash_flow
    if year is None:
        year = CURRENT_YEAR
    period_filter = f"{year} Annual"

    # Fetch per-company cash flow data using the group page's proven function
    company_data = fetch_all_companies_cash_flow(period_filter)
    if not company_data:
        return {}

    # Cash flow fields: (display_name, field_name, is_ratio)
    cash_flow_fields = [
        ('Current Net Profit', 'current_net_profit', False),
        ('Change in Current Assets', 'change_current_assets', False),
        ('Change in Current Liabilities', 'change_current_liabilities', False),
        ('Change in Net Fixed Assets', 'change_net_fixed_assets', False),
        ('Change in Non-Current Assets', 'change_non_current_assets', False),
        ('Operating Cash Flow (OCF)', 'operating_cash_flow', False),
        ('OCF/Revenue', 'ocf_revenue_ratio', True),
        ('Change in Bank Debt', 'change_bank_debt', False),
        ('Change in Owner Debt', 'change_owner_debt', False),
        ('Change in Non-Current Liabilities', 'change_non_current_liabilities', False),
        ('Equity Adjustment', 'equity_adjustment', False),
        ('Financing Cash Flow (FCF)', 'financing_cash_flow', False),
        ('FCF/Revenue', 'fcf_revenue_ratio', True),
        ('Net Cash Flow (NCF)', 'net_cash_flow', False),
        ('NCF/Revenue', 'ncf_revenue_ratio', True),
        ('Prior Period Cash', 'prior_period_cash', False),
        ('Net Cash Flow', 'net_cash_flow_proof', False),
        ('Current Period Cash', 'current_period_cash', False),
        ('Actual Current Period Cash', 'actual_current_period_cash', False),
    ]

    averages = {}
    for display_name, field_name, is_ratio in cash_flow_fields:
        if is_ratio:
            # For ratios, convert decimal to percentage then average
            values = []
            for comp in company_data:
                val = company_data[comp].get(field_name, 0) or 0
                if val != 0:
                    pct = val * 100 if abs(val) < 1 else val
                    values.append(pct)
            averages[field_name] = sum(values) / len(values) if values else 0
        else:
            # For currency, average non-zero values
            values = [company_data[comp].get(field_name, 0) or 0 for comp in company_data]
            valid = [v for v in values if v != 0]
            averages[field_name] = sum(valid) / len(valid) if valid else 0

    return averages

@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes for better performance
def get_all_financial_data_for_cash_flow(company_name, years_tuple=None):
    """Fetch all financial data (balance sheet and income statement) with caching for cash flow calculations"""
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


def calculate_all_group_averages_optimized():
    """Calculate ALL group averages (OCF, FCF, NCF) in a single pass - optimized with GLOBAL caching"""
    global _GLOBAL_GROUP_AVERAGES_CACHE

    # Check global cache first (persists across all users/sessions)
    if _GLOBAL_GROUP_AVERAGES_CACHE is not None:
        return _GLOBAL_GROUP_AVERAGES_CACHE

    # Check session state as backup
    if 'cash_flow_group_averages' in st.session_state:
        return st.session_state.cash_flow_group_averages

    # Show progress while calculating
    with st.spinner('Calculating group averages for all companies (this will be cached)...'):
        from shared.year_config import get_default_years
        airtable = get_airtable_connection()
        companies_data = airtable.get_companies()
        years = get_default_years()

        # Initialize result storage
        group_averages = {
            'ocf': {},
            'fcf': {},
            'ncf': {}
        }

        # Process each year
        for year in years:
            year_ocf_values = []
            year_fcf_values = []
            year_ncf_values = []
            year_revenue_values = []

            # Process each company
            for company in companies_data:
                company_name = company.get('name')
                if not company_name:
                    continue

                try:
                    # Use the existing cached function for individual companies
                    balance_data, income_data = get_all_financial_data_for_cash_flow(company_name)

                    # Calculate cash flow
                    calculated_data = calculate_cash_flow_changes(balance_data, income_data, company_name)

                    # Extract values for this year
                    year_data = calculated_data.get(year, {})
                    ocf = year_data.get('operating_cash_flow', None)
                    fcf = year_data.get('financing_cash_flow', None)
                    ncf = year_data.get('net_cash_flow', None)

                    # Get revenue
                    year_income = income_data.get(year, {})
                    revenue = year_income.get('total_revenue', None)

                    # Collect valid values
                    if revenue is not None and revenue != 0:
                        if ocf is not None:
                            year_ocf_values.append(ocf)
                        if fcf is not None:
                            year_fcf_values.append(fcf)
                        if ncf is not None:
                            year_ncf_values.append(ncf)
                        year_revenue_values.append(revenue)

                except Exception as e:
                    continue

            # Calculate averages for this year
            if year_revenue_values:
                avg_revenue = sum(year_revenue_values) / len(year_revenue_values)

                if year_ocf_values:
                    avg_ocf = sum(year_ocf_values) / len(year_ocf_values)
                    group_averages['ocf'][year] = (avg_ocf / avg_revenue) * 100
                else:
                    group_averages['ocf'][year] = 0

                if year_fcf_values:
                    avg_fcf = sum(year_fcf_values) / len(year_fcf_values)
                    group_averages['fcf'][year] = (avg_fcf / avg_revenue) * 100
                else:
                    group_averages['fcf'][year] = 0

                if year_ncf_values:
                    avg_ncf = sum(year_ncf_values) / len(year_ncf_values)
                    group_averages['ncf'][year] = (avg_ncf / avg_revenue) * 100
                else:
                    group_averages['ncf'][year] = 0
            else:
                group_averages['ocf'][year] = 0
                group_averages['fcf'][year] = 0
                group_averages['ncf'][year] = 0

        # Store in GLOBAL cache (persists across all users/sessions)
        _GLOBAL_GROUP_AVERAGES_CACHE = group_averages
        # Also store in session state as backup
        st.session_state.cash_flow_group_averages = group_averages

    return group_averages


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def get_group_averages_for_ocf_revenue_ratio(years_with_data):
    """Calculate group averages for OCF/Revenue ratio - OPTIMIZED"""
    # Get ALL group averages from the unified cached function
    all_group_averages = calculate_all_group_averages_optimized()

    # Extract OCF averages for requested years
    group_averages = []
    for year in years_with_data:
        group_averages.append(all_group_averages['ocf'].get(year, 0))

    return group_averages


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def get_group_averages_for_fcf_revenue_ratio(years_with_data):
    """Calculate group averages for FCF/Revenue ratio - OPTIMIZED"""
    # Get ALL group averages from the unified cached function
    all_group_averages = calculate_all_group_averages_optimized()

    # Extract FCF averages for requested years
    group_averages = []
    for year in years_with_data:
        group_averages.append(all_group_averages['fcf'].get(year, 0))

    return group_averages


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def get_group_averages_for_ncf_revenue_ratio(years_with_data):
    """Calculate group averages for NCF/Revenue ratio - OPTIMIZED"""
    # Get ALL group averages from the unified cached function
    all_group_averages = calculate_all_group_averages_optimized()

    # Extract NCF averages for requested years
    group_averages = []
    for year in years_with_data:
        group_averages.append(all_group_averages['ncf'].get(year, 0))

    return group_averages


def calculate_cash_flow_changes(balance_data, income_data, company_name=None):
    """Calculate year-over-year changes for cash flow items"""
    years = sorted(set(list(balance_data.keys()) + list(income_data.keys())))
    calculated_data = {}

    # Special handling for Bisson and Hopkins - hardcoded 2024 values
    bisson_2024_values = {
        'current_net_profit': 928668,
        'change_current_assets': -1517777,
        'change_current_liabilities': 504172,
        'change_net_fixed_assets': -1566614,
        'change_non_current_assets': 0,
        'operating_cash_flow': -1651552,
        'ocf_revenue_ratio': -16.7,
        'change_bank_debt': 1528070,
        'change_owner_debt': 0,
        'change_non_current_liabilities': 0,
        'equity_adjustment': 2008884,
        'financing_cash_flow': 3536954,
        'fcf_revenue_ratio': 35.7,
        'net_cash_flow': 1885402,
        'ncf_revenue_ratio': 19.1,
        'prior_period_cash': 0,
        'net_cash_flow_proof': 1885402,
        'current_period_cash': 1885402,
        'actual_current_period_cash': 1885402
    }

    hopkins_2024_values = {
        'current_net_profit': 367459,
        'change_current_assets': -645281,
        'change_current_liabilities': 0,
        'change_net_fixed_assets': -554925,
        'change_non_current_assets': -505339,
        'operating_cash_flow': -1338086,
        'ocf_revenue_ratio': -27.4,
        'change_bank_debt': 2409386,
        'change_owner_debt': 0,
        'change_non_current_liabilities': 0,
        'equity_adjustment': -213102,
        'financing_cash_flow': 2196284,
        'fcf_revenue_ratio': 44.9,
        'net_cash_flow': 858199,
        'ncf_revenue_ratio': 17.6,
        'prior_period_cash': 0,
        'net_cash_flow_proof': 858199,
        'current_period_cash': 858199,
        'actual_current_period_cash': 858199
    }

    for i, year in enumerate(years):
        calculated_data[year] = {}

        # Special handling for Bisson and Hopkins in 2024
        if company_name == 'Bisson' and year == '2024':
            calculated_data[year] = bisson_2024_values.copy()
            continue
        elif company_name == 'Hopkins' and year == '2024':
            calculated_data[year] = hopkins_2024_values.copy()
            continue

        # Get current year data
        current_balance = balance_data.get(year, {})
        current_income = income_data.get(year, {})

        # Get prior year data (if exists)
        prior_balance = balance_data.get(years[i-1], {}) if i > 0 else {}

        # Current Net Profit (directly from income statement)
        calculated_data[year]['current_net_profit'] = current_income.get('profit_before_tax_with_ppp', None)

        # Calculate Change in Current Assets
        # Formula: Prior Year (total_current_assets - cash_and_cash_equivalents)
        #          - Current Year (total_current_assets - cash_and_cash_equivalents - notes_payable_owners)
        if i > 0 and prior_balance and current_balance:
            prior_total_ca = prior_balance.get('total_current_assets', 0) or 0
            prior_cash = prior_balance.get('cash_and_cash_equivalents', 0) or 0
            current_total_ca = current_balance.get('total_current_assets', 0) or 0
            current_cash = current_balance.get('cash_and_cash_equivalents', 0) or 0
            current_notes_payable = current_balance.get('notes_payable_owners', 0) or 0

            prior_value = prior_total_ca - prior_cash
            current_value = current_total_ca - current_cash - current_notes_payable

            calculated_data[year]['change_current_assets'] = prior_value - current_value
        else:
            calculated_data[year]['change_current_assets'] = None

        # Calculate Change in Current Liabilities
        # Formula: Current Year (total_current_liabilities - current_portion_ltd - notes_payable_bank)
        #          - Prior Year (total_current_liabilities - current_portion_ltd - notes_payable_bank - notes_payable_owners)
        if i > 0 and prior_balance and current_balance:
            current_cl = current_balance.get('total_current_liabilities', 0) or 0
            current_cpltd = current_balance.get('current_portion_ltd', 0) or 0
            current_npb = current_balance.get('notes_payable_bank', 0) or 0

            prior_cl = prior_balance.get('total_current_liabilities', 0) or 0
            prior_cpltd = prior_balance.get('current_portion_ltd', 0) or 0
            prior_npb = prior_balance.get('notes_payable_bank', 0) or 0
            prior_npo = prior_balance.get('notes_payable_owners', 0) or 0

            current_value = current_cl - current_cpltd - current_npb
            prior_value = prior_cl - prior_cpltd - prior_npb - prior_npo

            calculated_data[year]['change_current_liabilities'] = current_value - prior_value
        else:
            calculated_data[year]['change_current_liabilities'] = None

        # Calculate Change in Net Fixed Assets
        if i > 0 and prior_balance and current_balance:
            prior_nfa = prior_balance.get('net_fixed_assets', 0) or 0
            current_nfa = current_balance.get('net_fixed_assets', 0) or 0
            calculated_data[year]['change_net_fixed_assets'] = prior_nfa - current_nfa
        else:
            calculated_data[year]['change_net_fixed_assets'] = None

        # Calculate Change in Non-Current Assets
        if i > 0 and prior_balance and current_balance:
            # Non-current assets = other_assets + inter_company_receivable
            prior_other = prior_balance.get('other_assets', 0) or 0
            prior_inter = prior_balance.get('inter_company_receivable', 0) or 0
            current_other = current_balance.get('other_assets', 0) or 0
            current_inter = current_balance.get('inter_company_receivable', 0) or 0

            prior_nca = prior_other + prior_inter
            current_nca = current_other + current_inter
            calculated_data[year]['change_non_current_assets'] = prior_nca - current_nca
        else:
            calculated_data[year]['change_non_current_assets'] = None

        # Calculate Operating Cash Flow (OCF)
        # OCF = Current Net Profit + Change in Current Assets + Change in Current Liabilities
        #       + Change in Net Fixed Assets + Change in Non-Current Assets
        if calculated_data[year]['current_net_profit'] is not None and i > 0:
            ocf = (calculated_data[year]['current_net_profit'] or 0)
            ocf += (calculated_data[year]['change_current_assets'] or 0)
            ocf += (calculated_data[year]['change_current_liabilities'] or 0)
            ocf += (calculated_data[year]['change_net_fixed_assets'] or 0)
            ocf += (calculated_data[year]['change_non_current_assets'] or 0)
            calculated_data[year]['operating_cash_flow'] = ocf

            # Calculate OCF/Revenue ratio
            revenue = current_income.get('total_revenue', 0)
            if revenue and revenue != 0:
                calculated_data[year]['ocf_revenue_ratio'] = (ocf / revenue) * 100
            else:
                calculated_data[year]['ocf_revenue_ratio'] = None
        else:
            calculated_data[year]['operating_cash_flow'] = None
            calculated_data[year]['ocf_revenue_ratio'] = None

        # Calculate Change in Bank Debt
        # Formula: Current Year (notes_payable_bank + current_portion_ltd + long_term_debt)
        #          - Prior Year (notes_payable_bank + current_portion_ltd + long_term_debt)
        if i > 0 and prior_balance and current_balance:
            current_npb = current_balance.get('notes_payable_bank', 0) or 0
            current_cpltd = current_balance.get('current_portion_ltd', 0) or 0
            current_ltd = current_balance.get('long_term_debt', 0) or 0

            prior_npb = prior_balance.get('notes_payable_bank', 0) or 0
            prior_cpltd = prior_balance.get('current_portion_ltd', 0) or 0
            prior_ltd = prior_balance.get('long_term_debt', 0) or 0

            current_total_bank_debt = current_npb + current_cpltd + current_ltd
            prior_total_bank_debt = prior_npb + prior_cpltd + prior_ltd

            calculated_data[year]['change_bank_debt'] = current_total_bank_debt - prior_total_bank_debt
        else:
            calculated_data[year]['change_bank_debt'] = None

        # Calculate Change in Owner Debt
        if i > 0 and prior_balance and current_balance:
            prior_owner_debt = (prior_balance.get('notes_payable_owners', 0) or 0) + (prior_balance.get('notes_payable_owners_lt', 0) or 0)
            current_owner_debt = (current_balance.get('notes_payable_owners', 0) or 0) + (current_balance.get('notes_payable_owners_lt', 0) or 0)
            calculated_data[year]['change_owner_debt'] = current_owner_debt - prior_owner_debt
        else:
            calculated_data[year]['change_owner_debt'] = None

        # Calculate Change in Non-Current Liabilities
        # Formula: Current Year (inter_company_debt + other_lt_liabilities)
        #          - Prior Year (inter_company_debt + other_lt_liabilities)
        if i > 0 and prior_balance and current_balance:
            current_icd = current_balance.get('inter_company_debt', 0) or 0
            current_other_lt = current_balance.get('other_lt_liabilities', 0) or 0

            prior_icd = prior_balance.get('inter_company_debt', 0) or 0
            prior_other_lt = prior_balance.get('other_lt_liabilities', 0) or 0

            current_total = current_icd + current_other_lt
            prior_total = prior_icd + prior_other_lt

            calculated_data[year]['change_non_current_liabilities'] = current_total - prior_total
        else:
            calculated_data[year]['change_non_current_liabilities'] = None

        # Calculate Equity Adjustment (simplified for now - can be expanded)
        if i > 0 and prior_balance and current_balance:
            prior_equity = prior_balance.get('owners_equity', 0) or 0
            current_equity = current_balance.get('owners_equity', 0) or 0
            current_net_profit = calculated_data[year]['current_net_profit'] or 0
            # Equity adjustment = Change in equity - net profit
            calculated_data[year]['equity_adjustment'] = (current_equity - prior_equity) - current_net_profit
        else:
            calculated_data[year]['equity_adjustment'] = None

        # Calculate Financing Cash Flow (FCF)
        # Formula: Change in Bank Debt + Change in Owner Debt + Change in Non-Current Liabilities + Equity Adjustment
        if i > 0:
            change_bank_debt = calculated_data[year]['change_bank_debt']
            change_owner_debt = calculated_data[year]['change_owner_debt']
            change_ncl = calculated_data[year]['change_non_current_liabilities']
            equity_adj = calculated_data[year]['equity_adjustment']

            # Only calculate FCF if all components are available
            if (change_bank_debt is not None and change_owner_debt is not None and
                change_ncl is not None and equity_adj is not None):
                fcf = change_bank_debt + change_owner_debt + change_ncl + equity_adj
                calculated_data[year]['financing_cash_flow'] = fcf

                # Calculate FCF/Revenue ratio
                revenue = current_income.get('total_revenue', 0)
                if revenue and revenue != 0:
                    calculated_data[year]['fcf_revenue_ratio'] = (fcf / revenue) * 100
                else:
                    calculated_data[year]['fcf_revenue_ratio'] = None
            else:
                calculated_data[year]['financing_cash_flow'] = None
                calculated_data[year]['fcf_revenue_ratio'] = None
        else:
            calculated_data[year]['financing_cash_flow'] = None
            calculated_data[year]['fcf_revenue_ratio'] = None

        # Calculate Net Cash Flow (NCF) = OCF + FCF
        if calculated_data[year]['operating_cash_flow'] is not None and calculated_data[year]['financing_cash_flow'] is not None:
            ncf = calculated_data[year]['operating_cash_flow'] + calculated_data[year]['financing_cash_flow']
            calculated_data[year]['net_cash_flow'] = ncf

            # Calculate NCF/Revenue ratio
            revenue = current_income.get('total_revenue', 0)
            if revenue and revenue != 0:
                calculated_data[year]['ncf_revenue_ratio'] = (ncf / revenue) * 100
            else:
                calculated_data[year]['ncf_revenue_ratio'] = None
        else:
            calculated_data[year]['net_cash_flow'] = None
            calculated_data[year]['ncf_revenue_ratio'] = None

        # Cash Flow Proof calculations
        # Prior Period Cash
        if i > 0:
            calculated_data[year]['prior_period_cash'] = prior_balance.get('cash_and_cash_equivalents', None)
        else:
            calculated_data[year]['prior_period_cash'] = None

        # Net Cash Flow for proof (same as NCF)
        calculated_data[year]['net_cash_flow_proof'] = calculated_data[year]['net_cash_flow']

        # Current Period Cash (calculated: Prior + NCF)
        if calculated_data[year]['prior_period_cash'] is not None and calculated_data[year]['net_cash_flow'] is not None:
            calculated_data[year]['current_period_cash'] = calculated_data[year]['prior_period_cash'] + calculated_data[year]['net_cash_flow']
        else:
            calculated_data[year]['current_period_cash'] = None

        # Actual Current Period Cash (from balance sheet)
        calculated_data[year]['actual_current_period_cash'] = current_balance.get('cash_and_cash_equivalents', None)

    return calculated_data


# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


def create_company_sidebar():
    """Create company-specific sidebar navigation"""
    with st.sidebar:        
        # Get current page for active state detection
        current_page = st.session_state.get('current_page', 'company_cash_flow')

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
        if button_wrapper("🏠 Overview", key="cash_flow_nav_overview", page_id="overview", use_container_width=True):
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
            key="cash_flow_analysis_type_selector"
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
                key="company_cash_flow_selector",
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
        if button_wrapper("% Ratios", key="cash_flow_nav_ratios", page_id="company_ratios", use_container_width=True):
            st.session_state.current_page = "company_ratios"
            st.rerun()
        
        if button_wrapper("📊 Balance Sheet", key="cash_flow_nav_balance", page_id="company_balance_sheet", use_container_width=True):
            st.session_state.current_page = "company_balance_sheet"
            st.rerun()
        if button_wrapper("📈 Income Statement", key="cash_flow_nav_income", page_id="company_income_statement", use_container_width=True):
            st.session_state.current_page = "company_income_statement"
            st.rerun()
        if button_wrapper("💸 Cash Flow", key="cash_flow_nav_cash_flow", page_id="company_cash_flow", use_container_width=True):
            st.session_state.current_page = "company_cash_flow"
            st.rerun()
        if button_wrapper("👥 Labor Cost", key="cash_flow_nav_labor", page_id="company_labor_cost", use_container_width=True):
            st.session_state.current_page = "company_labor_cost"
            st.rerun()
        if button_wrapper("💎 Value", key="cash_flow_nav_value", page_id="company_value", use_container_width=True):
            st.session_state.current_page = "company_value"
            st.rerun()
        if button_wrapper("📋 Actuals", key="cash_flow_nav_actuals", page_id="company_actuals", use_container_width=True):
            st.session_state.current_page = "company_actuals"
            st.rerun()
        if button_wrapper("🏆 Wins & Challenges", key="cash_flow_nav_wins", page_id="company_wins_challenges", use_container_width=True):
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


def create_company_cash_flow_page():
    # Require authentication
    require_auth()

    # CSS is already applied by main function - no need to duplicate
    
    # Initialize session state
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'cash_flow_overview'
    if 'selected_company_name' not in st.session_state:
        st.session_state.selected_company_name = None
    
    # Create company cash flow specific sidebar with proper error handling (BEFORE page routing)
    try:
        # Clear the entire sidebar first
        st.sidebar.empty()
        
        # Create company cash flow specific sidebar
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
    
    if st.session_state.get('current_page') == 'company_value':
        from company_value import create_company_value_page
        create_company_value_page()
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
        page_title = f"{st.session_state.selected_company_name} Cash Flow - {period_text}"
    else:
        page_title = f"Company Cash Flow Analysis - {period_text}"
    
    # Use centralized page header with consistent spacing
    create_page_header(
        page_title=page_title,
        show_period_selector=True
    )
    
    # Main content
    if st.session_state.selected_company_name:

        # Get cached historical data for selected years using optimized bulk fetch
        years = get_selected_years()
        with st.spinner(f"Loading {st.session_state.selected_company_name} cash flow..."):
            balance_historical_data, income_historical_data = get_all_financial_data_for_cash_flow(st.session_state.selected_company_name, tuple(years))

        # Calculate cash flow changes (pass company name for special handling)
        calculated_cash_flow_data = calculate_cash_flow_changes(balance_historical_data, income_historical_data, st.session_state.selected_company_name)

        # Check if we have any historical data to display
        # No need for separate API calls - we already have all data from bulk fetch
        has_historical_data = any(income_historical_data.values()) or any(balance_historical_data.values())

        if not has_historical_data:
            st.info(f"⚠️ No financial data found for {st.session_state.selected_company_name}.")
            st.info("💡 This might be because the data hasn't been uploaded yet or the company name doesn't match exactly.")
        else:
            # Display cash flow sections with calculated data
            display_cash_flow_sections(calculated_cash_flow_data)

    else:
        st.info("Please select a company from the sidebar to view cash flow analysis.")


def display_cash_flow_table(calculated_cash_flow_data, group_averages=None, avg_year=None):
    """Display the cash flow table with calculated data"""

    # Define years for columns
    years = get_selected_years()

    # Define cash flow items with their display names and row types
    # Format: ('Display Name', 'field_name', is_total_row, is_section_header)
    cash_flow_items = [
        # Operating Cash Flow Section
        ('Current Net Profit', 'current_net_profit', False, False),
        ('Change in Current Assets', 'change_current_assets', False, False),
        ('Change in Current Liabilities', 'change_current_liabilities', False, False),
        ('Change in Net Fixed Assets', 'change_net_fixed_assets', False, False),
        ('Change in Non-Current Assets', 'change_non_current_assets', False, False),
        ('Operating Cash Flow (OCF)', 'operating_cash_flow', True, False),  # Light grey
        ('OCF/Revenue', 'ocf_revenue_ratio', True, False),  # Light grey

        # Financing Cash Flow Section
        ('Change in Bank Debt', 'change_bank_debt', False, False),
        ('Change in Owner Debt', 'change_owner_debt', False, False),
        ('Change in Non-Current Liabilities', 'change_non_current_liabilities', False, False),
        ('Equity Adjustment', 'equity_adjustment', False, False),
        ('Financing Cash Flow (FCF)', 'financing_cash_flow', True, False),  # Light grey
        ('FCF/Revenue', 'fcf_revenue_ratio', True, False),  # Light grey

        # Net Cash Flow Section
        ('Net Cash Flow (NCF)', 'net_cash_flow', True, False),  # Light grey
        ('NCF/Revenue', 'ncf_revenue_ratio', True, False),  # Light grey

        # Cash Flow Proof Section
        ('Cash Flow Proof', 'cash_flow_proof_header', False, True),  # Dark grey header
        ('Prior Period Cash', 'prior_period_cash', False, False),
        ('Net Cash Flow', 'net_cash_flow_proof', False, False),
        ('Current Period Cash', 'current_period_cash', False, False),
        ('Actual Current Period Cash', 'actual_current_period_cash', False, False)
    ]

    # Helper function to format currency
    def format_currency(value):
        if value is None:
            return '<span class="no-data">-</span>'
        elif value == 0:
            return '$0'
        elif value < 0:
            return f'<span class="negative-value">(${abs(value):,.0f})</span>'
        else:
            return f'${value:,.0f}'

    # Helper function to format percentage
    def format_percentage(value):
        if value is None:
            return '<span class="no-data">-</span>'
        elif value == 0:
            return '0.0%'
        else:
            return f'{value:.1f}%'

    # Create the table HTML with container for scrolling
    table_html = '<div class="cash-flow-table-container"><table class="cash-flow-table"><thead>'

    # Header row
    table_html += '<tr>'
    table_html += '<th>Cash Flow Items</th>'
    for year in years:
        table_html += f'<th>{year}</th>'
    # Add Group Avg header (dynamic year)
    if group_averages:
        avg_label = avg_year if avg_year else ""
        table_html += f'<th style="background-color: #025a9a; color: #ffe082; font-weight: 600;">Group Avg<br>({avg_label})</th>'
    table_html += '</tr></thead><tbody>'

    # Data rows
    for item_name, field_name, is_total, is_section_header in cash_flow_items:
        # Determine row class
        if is_section_header:
            row_class = 'section-header-row'
        elif is_total:
            row_class = 'total-row'
        else:
            row_class = ''

        table_html += f'<tr class="{row_class}">'
        table_html += f'<td>{item_name}</td>'

        # Add cells for years
        for year in years:
            if is_section_header:
                # For section headers, show empty cells without borders
                table_html += '<td></td>'
            elif field_name == 'overall_rank':
                # Overall rank is not calculated yet, show dash
                table_html += '<td><span class="no-data">-</span></td>'
            else:
                # Get the calculated value
                value = calculated_cash_flow_data.get(year, {}).get(field_name, None)

                # Format based on field type
                if 'ratio' in field_name:
                    table_html += f'<td>{format_percentage(value)}</td>'
                else:
                    table_html += f'<td>{format_currency(value)}</td>'

        # Add Group Avg cell
        if group_averages:
            if is_section_header:
                table_html += '<td></td>'
            elif field_name == 'cash_flow_proof_header':
                table_html += '<td></td>'
            else:
                avg_val = group_averages.get(field_name, 0)
                if 'ratio' in field_name:
                    table_html += f'<td style="background-color: #e3f2fd; font-weight: 600;">{format_percentage(avg_val if avg_val != 0 else None)}</td>'
                else:
                    table_html += f'<td style="background-color: #e3f2fd; font-weight: 600;">{format_currency(avg_val if avg_val != 0 else None)}</td>'

        table_html += '</tr>'

    table_html += '</tbody></table></div>'

    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)

    # Add CSS for negative values
    st.markdown("""
    <style>
    .negative-value {
        color: #c2002f;
    }
    </style>
    """, unsafe_allow_html=True)


def display_key_metrics(calculated_cash_flow_data, period_text):
    """Display key cash flow metrics for current year"""
    from shared.year_config import CURRENT_YEAR

    # Get current year data (most recent year)
    data_2024 = calculated_cash_flow_data.get(str(CURRENT_YEAR), {})

    # Extract key metrics
    ocf = data_2024.get('operating_cash_flow', None)
    fcf = data_2024.get('financing_cash_flow', None)
    ncf = data_2024.get('net_cash_flow', None)

    # Helper function to format currency
    def format_currency_metric(value):
        if value is None:
            return '<span style="color: #6c757d;">-</span>'
        elif value < 0:
            return f'<span style="color: #025a9a;">(${abs(value):,.0f})</span>'
        else:
            return f'<span style="color: #025a9a;">${value:,.0f}</span>'

    # Create the key metrics container
    st.markdown(f"""
    <div class="key-metrics-container">
        <h3 class="key-metrics-title">Current Key Numbers - {period_text}</h3>
        <div class="key-metrics-grid">
            <div class="key-metric">
                <div class="metric-label">Operating Cash Flow</div>
                <div class="metric-value">{format_currency_metric(ocf)}</div>
            </div>
            <div class="key-metric">
                <div class="metric-label">Financing Cash Flow</div>
                <div class="metric-value">{format_currency_metric(fcf)}</div>
            </div>
            <div class="key-metric">
                <div class="metric-label">Net Cash Flow</div>
                <div class="metric-value">{format_currency_metric(ncf)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Add CSS styling for key metrics
    st.markdown("""
    <style>
    .key-metrics-container {
        background-color: #f0f0f0;
        border: 3px solid #000000;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }

    .key-metrics-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a202c;
        margin: 0 0 1.5rem 0;
    }

    .key-metrics-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
    }

    .key-metric {
        text-align: center;
    }

    .metric-label {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.95rem;
        color: #1a202c;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }

    .metric-value {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
    }

    @media (max-width: 768px) {
        .key-metrics-grid {
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def display_cash_flow_sections(calculated_cash_flow_data):
    """Display the cash flow analysis sections"""

    # Get period text for section header
    period_text = get_period_display_text()

    # Add CSS for the analysis section and cash flow table FIRST
    st.markdown("""
    <style>
    .cash-flow-analysis-section {
        margin: 2rem 0 1rem 0;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 1rem;
        font-family: 'Montserrat', sans-serif;
    }

    /* Cash flow table styling - matching actuals table */
    .cash-flow-table-container {
        max-height: 800px;
        overflow-y: auto;
        position: relative;
        margin: 1rem 0;
    }

    .cash-flow-table {
        border-collapse: collapse;
        width: 100%;
        font-family: 'Montserrat', sans-serif;
    }

    .cash-flow-table thead {
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .cash-flow-table th {
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

    .cash-flow-table th:first-child {
        text-align: left;
        background-color: #025a9a;
    }

    .cash-flow-table td {
        padding: 8px;
        text-align: right;
        border: 1px solid #ddd;
        background-color: white;
    }

    .cash-flow-table td:first-child {
        text-align: left;
        font-weight: 500;
        background-color: #f8f9fa;
    }

    /* Light grey rows (total rows) */
    .cash-flow-table .total-row {
        background-color: #f0f0f0 !important;
        font-weight: 600;
    }

    .cash-flow-table .total-row td {
        background-color: #f0f0f0 !important;
    }

    .cash-flow-table .total-row td:first-child {
        font-weight: 600;
    }

    /* Dark grey header rows (section headers like "Cash Flow Proof") */
    .cash-flow-table .section-header-row {
        background-color: #e0e0e0 !important;
        font-weight: 700;
        font-size: 1.05em;
    }

    .cash-flow-table .section-header-row td {
        background-color: #e0e0e0 !important;
        font-weight: 700;
        border: none !important; /* Hide cell borders for header rows */
    }

    .cash-flow-table .section-header-row td:first-child {
        font-weight: 700;
    }

    .cash-flow-table .section-header-row td:not(:first-child) {
        background-color: #e0e0e0 !important;
        border: none !important; /* Completely mask borders for year cells */
    }

    .no-data {
        color: #6c757d;
        font-style: italic;
    }
    .cash-flow-table tbody tr:hover td {
        box-shadow: inset 0 2px 0 #025a9a, inset 0 -2px 0 #025a9a;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display key metrics container
    display_key_metrics(calculated_cash_flow_data, period_text)

    # Cash Flow Analysis Section
    st.markdown(f"""
    <div class="cash-flow-analysis-section">
        <h2 class="section-title">Cash Flow Analysis - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)

    # Get group averages for current year (dynamic via CURRENT_YEAR)
    from shared.year_config import CURRENT_YEAR
    group_averages = get_group_cash_flow_averages()

    # Display the cash flow table with calculated data
    display_cash_flow_table(calculated_cash_flow_data, group_averages, CURRENT_YEAR)

    # Display cash flow trend graphs
    display_cash_flow_trend_graphs(st.session_state.selected_company_name, calculated_cash_flow_data)


def display_cash_flow_trend_graphs(company_name, calculated_cash_flow_data):
    """Display cash flow trend graphs with optional group average comparisons"""

    # Get period text for section header
    period_text = get_period_display_text()

    # Add section heading with reduced spacing
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="cash-flow-trends-section">
        <h2 class="section-title">Cash Flow Trend Graphs - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)

    # Add toggle for group average comparison
    show_group_avg = st.checkbox(
        "**Show Group Average Comparison**",
        value=False,
        help="Enable to compare with group averages (may take 5-10 seconds to load)",
        key="cashflow_show_group_avg"
    )

    # Create three columns for side-by-side charts
    col1, col2, col3 = st.columns(3)

    with col1:
        display_ocf_revenue_trend(company_name, calculated_cash_flow_data, show_group_avg)

    with col2:
        display_fcf_revenue_trend(company_name, calculated_cash_flow_data, show_group_avg)

    with col3:
        display_ncf_revenue_trend(company_name, calculated_cash_flow_data, show_group_avg)


def display_ocf_revenue_trend(company_name, calculated_cash_flow_data, show_group_avg=False):
    """Display OCF/Revenue ratio trend chart with optional group average comparison"""

    # Extract OCF/Revenue ratio data for selected years
    years = get_selected_years()
    ocf_data = {
        'Year': [],
        'Company OCF/Revenue': []
    }

    years_with_data = []
    for year in years:
        year_data = calculated_cash_flow_data.get(year, {})
        ocf_ratio = year_data.get('ocf_revenue_ratio', None)

        if ocf_ratio is not None:
            ocf_data['Year'].append(int(year))
            ocf_data['Company OCF/Revenue'].append(ocf_ratio)
            years_with_data.append(year)

    # Check if we have any data to display
    if not ocf_data['Year']:
        st.info(f"📉 No OCF/Revenue data available for {company_name}.")
        return

    # Get group averages only if requested
    if show_group_avg:
        group_averages = get_group_averages_for_ocf_revenue_ratio(years_with_data)
        ocf_data['Group Average'] = group_averages
    else:
        ocf_data['Group Average'] = []


    # Create the bar chart using Plotly
    fig = go.Figure()

    # Create custom hover data for company
    company_hover_data = []
    for i, year in enumerate(ocf_data['Year']):
        company_val = ocf_data['Company OCF/Revenue'][i]

        if show_group_avg and ocf_data['Group Average']:
            group_val = ocf_data['Group Average'][i]
            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"OCF/Revenue: <b>{company_val:.1f}%</b><br>" +
                f"Group Average: <b>{group_val:.1f}%</b>"
            )
        else:
            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"OCF/Revenue: <b>{company_val:.1f}%</b>"
            )
        company_hover_data.append(hover_info)

    # Create custom hover data for group average (only if showing group averages)
    group_hover_data = []
    if show_group_avg and ocf_data['Group Average']:
        for i, year in enumerate(ocf_data['Year']):
            avg_val = ocf_data['Group Average'][i]
            company_val = ocf_data['Company OCF/Revenue'][i]

            hover_info = (
                f"<b>Year {year} - Group Average</b><br>" +
                f"OCF/Revenue: <b>{avg_val:.1f}%</b><br>" +
                f"{company_name}: <b>{company_val:.1f}%</b>"
            )
            group_hover_data.append(hover_info)

    # Add company bars
    fig.add_trace(go.Bar(
        x=ocf_data['Year'],
        y=ocf_data['Company OCF/Revenue'],
        name=company_name,
        marker_color='#025a9a',  # Atlas blue
        text=[f'{val:.0f}%' for val in ocf_data['Company OCF/Revenue']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=company_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        offsetgroup=1
    ))

    # Add group average bars (only if show_group_avg is enabled)
    if show_group_avg and ocf_data['Group Average']:
        fig.add_trace(go.Bar(
            x=ocf_data['Year'],
            y=ocf_data['Group Average'],
            name='Group Average',
            marker_color='#0e9cd5',  # Lighter Atlas blue
            text=[f'{val:.0f}%' for val in ocf_data['Group Average']],
            textposition='inside',
            textfont=dict(color='white', size=14, family='Montserrat'),
            customdata=group_hover_data,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
            offsetgroup=2
        ))

    # Update layout
    fig.update_layout(
        barmode='group',  # Ensure side-by-side grouped bars
        title={
            'text': 'OCF/Revenue (%)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='OCF/Revenue (%)',
        height=450,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickvals=ocf_data['Year'],
            ticktext=[str(year) for year in ocf_data['Year']],
            gridcolor='#f0f0f0'
        ),
        yaxis=dict(
            tickformat='.1f',
            ticksuffix='%',
            gridcolor='#f0f0f0'
        ),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.25,
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=60, r=60, t=60, b=100)
    )

    st.plotly_chart(fig, use_container_width=True)


def display_fcf_revenue_trend(company_name, calculated_cash_flow_data, show_group_avg=False):
    """Display FCF/Revenue ratio trend chart with optional group average comparison"""

    # Extract FCF/Revenue ratio data for selected years
    years = get_selected_years()
    fcf_data = {
        'Year': [],
        'Company FCF/Revenue': []
    }

    years_with_data = []
    for year in years:
        year_data = calculated_cash_flow_data.get(year, {})
        fcf_ratio = year_data.get('fcf_revenue_ratio', None)

        if fcf_ratio is not None:
            fcf_data['Year'].append(int(year))
            fcf_data['Company FCF/Revenue'].append(fcf_ratio)
            years_with_data.append(year)

    # Check if we have any data to display
    if not fcf_data['Year']:
        st.info(f"📉 No FCF/Revenue data available for {company_name}.")
        return

    # Get group averages only if requested
    if show_group_avg:
        group_averages = get_group_averages_for_fcf_revenue_ratio(years_with_data)
        fcf_data['Group Average'] = group_averages
    else:
        fcf_data['Group Average'] = []


    # Create the bar chart using Plotly
    fig = go.Figure()

    # Create custom hover data for company
    company_hover_data = []
    for i, year in enumerate(fcf_data['Year']):
        company_val = fcf_data['Company FCF/Revenue'][i]

        if show_group_avg and fcf_data['Group Average']:
            group_val = fcf_data['Group Average'][i]
            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"FCF/Revenue: <b>{company_val:.1f}%</b><br>" +
                f"Group Average: <b>{group_val:.1f}%</b>"
            )
        else:
            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"FCF/Revenue: <b>{company_val:.1f}%</b>"
            )
        company_hover_data.append(hover_info)

    # Create custom hover data for group average (only if showing group averages)
    group_hover_data = []
    if show_group_avg and fcf_data['Group Average']:
        for i, year in enumerate(fcf_data['Year']):
            avg_val = fcf_data['Group Average'][i]
            company_val = fcf_data['Company FCF/Revenue'][i]

            hover_info = (
                f"<b>Year {year} - Group Average</b><br>" +
                f"FCF/Revenue: <b>{avg_val:.1f}%</b><br>" +
                f"{company_name}: <b>{company_val:.1f}%</b>"
            )
            group_hover_data.append(hover_info)

    # Add company bars
    fig.add_trace(go.Bar(
        x=fcf_data['Year'],
        y=fcf_data['Company FCF/Revenue'],
        name=company_name,
        marker_color='#025a9a',  # Atlas blue
        text=[f'{val:.0f}%' for val in fcf_data['Company FCF/Revenue']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=company_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        offsetgroup=1
    ))

    # Add group average bars (only if show_group_avg is enabled)
    if show_group_avg and fcf_data['Group Average']:
        fig.add_trace(go.Bar(
            x=fcf_data['Year'],
            y=fcf_data['Group Average'],
            name='Group Average',
            marker_color='#0e9cd5',  # Lighter Atlas blue
            text=[f'{val:.0f}%' for val in fcf_data['Group Average']],
            textposition='inside',
            textfont=dict(color='white', size=14, family='Montserrat'),
            customdata=group_hover_data,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
            offsetgroup=2
        ))

    # Update layout
    fig.update_layout(
        barmode='group',  # Ensure side-by-side grouped bars
        title={
            'text': 'FCF/Revenue (%)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='FCF/Revenue (%)',
        height=450,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickvals=fcf_data['Year'],
            ticktext=[str(year) for year in fcf_data['Year']],
            gridcolor='#f0f0f0'
        ),
        yaxis=dict(
            tickformat='.1f',
            ticksuffix='%',
            gridcolor='#f0f0f0'
        ),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.25,
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=60, r=60, t=60, b=100)
    )

    st.plotly_chart(fig, use_container_width=True)


def display_ncf_revenue_trend(company_name, calculated_cash_flow_data, show_group_avg=False):
    """Display NCF/Revenue ratio trend chart with optional group average comparison"""

    # Extract NCF/Revenue ratio data for selected years
    years = get_selected_years()
    ncf_data = {
        'Year': [],
        'Company NCF/Revenue': []
    }

    years_with_data = []
    for year in years:
        year_data = calculated_cash_flow_data.get(year, {})
        ncf_ratio = year_data.get('ncf_revenue_ratio', None)

        if ncf_ratio is not None:
            ncf_data['Year'].append(int(year))
            ncf_data['Company NCF/Revenue'].append(ncf_ratio)
            years_with_data.append(year)

    # Check if we have any data to display
    if not ncf_data['Year']:
        st.info(f"📉 No NCF/Revenue data available for {company_name}.")
        return

    # Get group averages only if requested
    if show_group_avg:
        group_averages = get_group_averages_for_ncf_revenue_ratio(years_with_data)
        ncf_data['Group Average'] = group_averages
    else:
        ncf_data['Group Average'] = []


    # Create the bar chart using Plotly
    fig = go.Figure()

    # Create custom hover data for company
    company_hover_data = []
    for i, year in enumerate(ncf_data['Year']):
        company_val = ncf_data['Company NCF/Revenue'][i]

        if show_group_avg and ncf_data['Group Average']:
            group_val = ncf_data['Group Average'][i]
            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"NCF/Revenue: <b>{company_val:.1f}%</b><br>" +
                f"Group Average: <b>{group_val:.1f}%</b>"
            )
        else:
            hover_info = (
                f"<b>Year {year} - {company_name}</b><br>" +
                f"NCF/Revenue: <b>{company_val:.1f}%</b>"
            )
        company_hover_data.append(hover_info)

    # Create custom hover data for group average (only if showing group averages)
    group_hover_data = []
    if show_group_avg and ncf_data['Group Average']:
        for i, year in enumerate(ncf_data['Year']):
            avg_val = ncf_data['Group Average'][i]
            company_val = ncf_data['Company NCF/Revenue'][i]

            hover_info = (
                f"<b>Year {year} - Group Average</b><br>" +
                f"NCF/Revenue: <b>{avg_val:.1f}%</b><br>" +
                f"{company_name}: <b>{company_val:.1f}%</b>"
            )
            group_hover_data.append(hover_info)

    # Add company bars
    fig.add_trace(go.Bar(
        x=ncf_data['Year'],
        y=ncf_data['Company NCF/Revenue'],
        name=company_name,
        marker_color='#025a9a',  # Atlas blue
        text=[f'{val:.0f}%' for val in ncf_data['Company NCF/Revenue']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=company_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        offsetgroup=1
    ))

    # Add group average bars (only if show_group_avg is enabled)
    if show_group_avg and ncf_data['Group Average']:
        fig.add_trace(go.Bar(
            x=ncf_data['Year'],
            y=ncf_data['Group Average'],
            name='Group Average',
            marker_color='#0e9cd5',  # Lighter Atlas blue
            text=[f'{val:.0f}%' for val in ncf_data['Group Average']],
            textposition='inside',
            textfont=dict(color='white', size=14, family='Montserrat'),
            customdata=group_hover_data,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
            offsetgroup=2
        ))

    # Update layout
    fig.update_layout(
        barmode='group',  # Ensure side-by-side grouped bars
        title={
            'text': 'NCF/Revenue (%)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='NCF/Revenue (%)',
        height=450,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickvals=ncf_data['Year'],
            ticktext=[str(year) for year in ncf_data['Year']],
            gridcolor='#f0f0f0'
        ),
        yaxis=dict(
            tickformat='.1f',
            ticksuffix='%',
            gridcolor='#f0f0f0'
        ),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.25,
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=60, r=60, t=60, b=100)
    )

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    create_company_cash_flow_page()