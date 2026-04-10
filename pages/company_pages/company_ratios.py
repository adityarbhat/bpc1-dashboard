import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import os
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Import from shared modules
from shared.airtable_connection import get_airtable_connection
from shared.chart_utils import create_gauge_chart, render_gauge_with_formula
from shared.page_components import get_period_display_text
from shared.auth_utils import require_auth, logout_user, get_current_user_name, get_current_user_email, is_super_admin
from shared.cash_flow_utils import get_cash_flow_ratios
from shared.year_config import get_selected_years

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


def create_company_sidebar():
    """Create company-specific sidebar navigation"""
    with st.sidebar:
        # Get current page for active state detection
        current_page = st.session_state.get('current_page', 'company_ratios')

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
        if button_wrapper("🏠 Overview", key="nav_overview", page_id="overview", use_container_width=True):
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
            key="company_analysis_type_selector"
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
        
        # Get companies for dropdown using session-level caching for better performance
        from shared.airtable_connection import get_companies_cached
        companies = get_companies_cached()
        
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
                key="company_ratios_selector",
                index=list(company_options.keys()).index(current_company)
            )
            st.session_state.selected_company_name = selected_company_name
        else:
            st.error("No companies found")
            return

        from shared.year_config import render_year_selector
        render_year_selector()

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Single Ratios button for navigation
        if button_wrapper("% Ratios", key="nav_ratios", page_id="company_ratios", use_container_width=True):
            st.session_state.current_page = "company_ratios"
            st.rerun()

        if button_wrapper("📊 Balance Sheet", key="nav_balance", page_id="company_balance_sheet", use_container_width=True):
            st.session_state.current_page = "company_balance_sheet"
            st.rerun()
        if button_wrapper("📈 Income Statement", key="nav_income", page_id="company_income_statement", use_container_width=True):
            st.session_state.current_page = "company_income_statement"
            st.rerun()
        if button_wrapper("💸 Cash Flow", key="nav_cash_flow", page_id="company_cash_flow", use_container_width=True):
            st.session_state.current_page = "company_cash_flow"
            st.rerun()
        if button_wrapper("👥 Labor Cost", key="nav_labor", page_id="company_labor_cost", use_container_width=True):
            st.session_state.current_page = "company_labor_cost"
            st.rerun()
        if button_wrapper("💎 Value", key="nav_value", page_id="company_value", use_container_width=True):
            st.session_state.current_page = "company_value"
            st.rerun()
        if button_wrapper("📋 Actuals", key="nav_actuals", page_id="company_actuals", use_container_width=True):
            st.session_state.current_page = "company_actuals"
            st.rerun()
        if button_wrapper("🏆 Wins & Challenges", key="nav_wins", page_id="company_wins_challenges", use_container_width=True):
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

# Top navigation buttons removed - now handled by Analysis Type filter in sidebar

# Period selector now handled by centralized page components

def create_action_buttons():
    """Create top action buttons"""
    st.markdown("""
    <div class="action-buttons">
       
        <div class="action-btn">Glossary</div>
        <div class="action-btn">Update Data</div>
        <div class="action-btn">Sign Out</div>
    </div>
    """, unsafe_allow_html=True)

def create_company_ratios_page():
    # Require authentication
    require_auth()

    # CSS is already applied by main function - no need to duplicate

    # Initialize session state
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'ratios_overview'
    if 'selected_company_name' not in st.session_state:
        st.session_state.selected_company_name = None
    
    # Create company ratios specific sidebar with proper error handling
    try:
        # Clear the entire sidebar first
        st.sidebar.empty()

        # Create company ratios specific sidebar
        create_company_sidebar()
    except Exception as e:
        st.sidebar.error(f"Error creating sidebar: {str(e)}")
    
    # Import centralized page components
    from shared.page_components import create_page_header
    
    # Get period display text
    period_text = get_period_display_text()
    
    # Determine page title based on selected company
    if st.session_state.selected_company_name:
        page_title = f"{st.session_state.selected_company_name} Ratios - {period_text}"
    else:
        page_title = f"Company Ratios Analysis - {period_text}"
    
    # Use centralized page header with consistent spacing
    create_page_header(
        page_title=page_title,
        show_period_selector=True
    )
    
    # Main content
    if st.session_state.selected_company_name:
        
        # Initialize Airtable connection using shared connection
        airtable = get_airtable_connection()
        
        # Determine which period to use based on user selection
        if 'period' not in st.session_state:
            st.session_state.period = 'year_end'
        
        from shared.year_config import CURRENT_YEAR
        period_filter = f"{CURRENT_YEAR} Annual" if st.session_state.period == 'year_end' else f"June {CURRENT_YEAR}"

        # Get data for selected company for the selected period
        with st.spinner(f"Loading {st.session_state.selected_company_name} ratios..."):
            balance_data = airtable.get_balance_sheet_data_by_period(st.session_state.selected_company_name, period_filter, is_admin=is_super_admin())
            income_data = airtable.get_income_statement_data_by_period(st.session_state.selected_company_name, period_filter, is_admin=is_super_admin())
        
        # Check if we have any data to display
        if not balance_data and not income_data:
            st.info(f"⚠️ No financial data found for {st.session_state.selected_company_name} for the {period_filter} period.")
            st.info("💡 This might be because the data hasn't been uploaded yet or the company name doesn't match exactly.")
        
        # Display ratios sections
        if balance_data or income_data:
            display_ratios_sections(balance_data, income_data)
        else:
            # Show sample data if no real data is available
            st.warning("No financial data found for the selected company. Showing sample data below:")
            
            # Sample balance sheet data
            sample_balance = [{
                'current_ratio': 2.24,
                'debt_to_equity': 2.43,
                'working_capital_pct_asset': 32,
                'survival_score': 3.3
            }]
            
            # Sample income statement data
            sample_income = [{
                'gpm': 45.9,
                'opm': -1.0,
                'rev_admin_employee': 621732,
                'ebitda_margin': 0
            }]
            
            display_ratios_sections(sample_balance, sample_income)
    else:
        st.info("Please select a company from the sidebar to view ratios.")
        
        # Show default content or sample data when no company is selected
        st.markdown("### Welcome to Company Ratios Analysis")
        st.write("Select a company from the sidebar to view detailed financial ratios and analysis.")
        
        # Show sample content to demonstrate functionality
        with st.expander("Preview: Sample Company Ratios"):
            st.write("Here's what you'll see when you select a company:")
            
            # Sample data preview
            sample_balance = [{
                'current_ratio': 2.24,
                'debt_to_equity': 2.43,
                'working_capital_pct_asset': 32,
                'survival_score': 3.3
            }]
            
            sample_income = [{
                'gpm': 45.9,
                'opm': -1.0,
                'rev_admin_employee': 621732,
                'ebitda_margin': 0
            }]
            
            display_ratios_sections(sample_balance, sample_income)

def get_cell_color(value, metric_name):
    """Get background color for table cell based on metric value and thresholds"""
    if value is None or value == '':
        return '#f8f9fa'  # Light gray for missing data
    
    # Define thresholds for each metric
    # NOTE: Percentage metrics (working_capital_pct, gpm, opm, ebitda_margin) use decimal values
    # because Airtable stores them as decimals (e.g., 0.53 for 53%)
    thresholds = {
        'current_ratio': {'great': 2.0, 'caution': [1.2, 2.0], 'improve': 1.3},
        'debt_to_equity': {'great': 1.4, 'caution': [1.5, 2.9], 'improve': 3.0, 'reverse': True},  # Lower is better
        'working_capital_pct': {'great': 0.30, 'caution': [0.15, 0.29], 'improve': 0.15},  # Decimal (0.30 = 30%)
        'survival_score': {'great': 3.0, 'caution': [2.0, 3.0], 'improve': 2.0},
        'gpm': {'great': 0.25, 'caution': [0.20, 0.25], 'improve': 0.20},  # Decimal (0.25 = 25%)
        'opm': {'great': 0.055, 'caution': [0.03, 0.054], 'improve': 0.03},  # Decimal (0.055 = 5.5%)
        'rev_per_employee': {'great': 550, 'caution': [325, 550], 'improve': 325},  # In thousands
        'ebitda_margin': {'great': 0.05, 'caution': [0.025, 0.05], 'improve': 0.025},  # Decimal (0.05 = 5%)
        'dso': {'great': 30, 'caution': [30, 60], 'improve': 60, 'reverse': True},  # Lower is better
        'ocf_rev': {'great': 0.0, 'caution': [-0.03, 0.0], 'improve': -0.03},  # Positive = green, 0 to neg 3% = yellow
    }
    
    if metric_name not in thresholds:
        return '#f8f9fa'  # Default light gray
    
    threshold = thresholds[metric_name]
    is_reverse = threshold.get('reverse', False)  # For metrics where lower is better
    
    try:
        val = float(value)
        
        if is_reverse:
            # For reverse metrics (like debt_to_equity, dso), lower values are better
            if val <= threshold['great']:
                return '#c8e6c9'  # Muted light green
            elif isinstance(threshold['caution'], list) and threshold['caution'][0] <= val <= threshold['caution'][1]:
                return '#fff3c4'  # Muted light yellow
            else:
                return '#ffcdd2'  # Muted light red
        else:
            # For normal metrics, higher values are better
            if val >= threshold['great']:
                return '#c8e6c9'  # Muted light green
            elif isinstance(threshold['caution'], list) and threshold['caution'][0] <= val <= threshold['caution'][1]:
                return '#fff3c4'  # Muted light yellow  
            else:
                return '#ffcdd2'  # Muted light red
    except (ValueError, TypeError):
        return '#f8f9fa'  # Light gray for invalid values

def format_metric_value(value, metric_name):
    """Format metric values for display in the trends table"""
    if value is None or value == '' or value == 0:
        return '-'
    
    try:
        val = float(value)
        
        # Balance Sheet formatting
        if metric_name in ['Current Ratio (Liquidity)', 'current_ratio']:
            return f"{val:.1f}"
        elif metric_name in ['Debt to Equity (Safety)', 'debt_to_equity']:
            return f"{val:.1f}"
        elif metric_name in ['Working Capital as % of Total Assets', 'working_capital_pct']:
            # Convert to percentage if needed (assuming data comes as decimal)
            if val <= 1:
                return f"{val * 100:.1f}%"
            else:
                return f"{val:.1f}%"
        elif metric_name in ['Survival Score', 'survival_score']:
            return f"{val:.1f}"
        elif metric_name in ['Sales/Assets', 'sales_assets']:
            return f"{val:.2f}"

        # Income Statement formatting  
        elif metric_name in ['Gross Profit Margin', 'Gross profit margin', 'gpm']:
            # Convert to percentage
            if val <= 1:
                return f"{val * 100:.1f}%"
            else:
                return f"{val:.1f}%"
        elif metric_name in ['Operating Profit Margin', 'Operating profit margin', 'opm']:
            # Convert to percentage
            if val <= 1:
                return f"{val * 100:.1f}%"
            else:
                return f"{val:.1f}%"
        elif metric_name in ['Net Profit Margin', 'Net profit margin', 'npm']:
            # Convert to percentage
            if val <= 1:
                return f"{val * 100:.1f}%"
            else:
                return f"{val:.1f}%"
        elif metric_name in ['EBITDA/Revenue', 'ebitda_margin']:
            # Convert to percentage
            if val <= 1:
                return f"{val * 100:.1f}%"
            else:
                return f"{val:.1f}%"
        elif metric_name in ['Revenue Per Admin Employee', 'Revenue per admin employee', 'rev_per_employee']:
            # Format as currency in thousands
            return f"${val:.0f}K"
        
        # Cash Flow formatting
        elif metric_name in ['Days Sales Outstanding (DSO)', 'dso']:
            return f"{val:.0f}"
        elif metric_name in ['Operating Cash Flow (OCF)/Revenue', 'ocf_rev']:
            # Convert to percentage
            if val <= 1 and val >= -1:
                return f"{val * 100:.1f}%"
            else:
                return f"{val:.1f}%"
        elif metric_name in ['Financing Cash Flow (FCF)/Revenue', 'fcf_rev']:
            # Convert to percentage
            if val <= 1 and val >= -1:
                return f"{val * 100:.1f}%"
            else:
                return f"{val:.1f}%"
        elif metric_name in ['Net Cash Flow (NCF)/Revenue', 'ncf_rev']:
            # Convert to percentage
            if val <= 1 and val >= -1:
                return f"{val * 100:.1f}%"
            else:
                return f"{val:.1f}%"
        
        # Default formatting
        else:
            return f"{val:.1f}"
            
    except (ValueError, TypeError):
        return '-'

def display_ratio_trends_table(balance_data, income_data):
    """Display the ratio trends table for years 2020-2024 with real historical data"""
    
    # Get period text for header
    period_text = get_period_display_text()
    
    st.markdown(f"""
    <div class="ratios-section" style="margin-top: 2rem;">
        <h2 class="section-title">Ratio Trends Table - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create the trends table
    years = get_selected_years()
    
    # Fetch historical data for all years
    if not st.session_state.selected_company_name:
        st.info("Please select a company to view historical trends.")
        return
    
    # Get Airtable connection
    from shared.airtable_connection import get_airtable_connection
    airtable = get_airtable_connection()
    
    # Initialize trends data structure
    trends_data = {
        'balance_sheet': {
            'Current Ratio (Liquidity)': {},
            'Debt to Equity (Safety)': {},
            'Working Capital as % of Total Assets': {},
            'Survival Score': {},
            'Sales/Assets': {}
        },
        'income_statement': {
            'Gross Profit Margin': {},
            'Operating Profit Margin': {},
            'Net Profit Margin': {},
            'Revenue Per Admin Employee': {},
            'EBITDA/Revenue': {}
        },
        'cash_flow': {
            'Days Sales Outstanding (DSO)': {},
            'Operating Cash Flow (OCF)/Revenue': {},
            'Financing Cash Flow (FCF)/Revenue': {},
            'Net Cash Flow (NCF)/Revenue': {}
        }
    }
    
    # Fetch data for each year
    for year in years:
        period_filter = f"{year} Annual"
        _balance_record_for_year = None

        # Get balance sheet data for this year
        try:
            balance_historical = airtable.get_balance_sheet_data_by_period(st.session_state.selected_company_name, period_filter, is_admin=is_super_admin())
            if balance_historical:
                record = balance_historical[0]  # Get first record for this period
                _balance_record_for_year = record

                # Balance Sheet metrics — computed from dollar fields to avoid stale stored ratios
                _bs_ca = record.get('total_current_assets', 0) or 0
                _bs_cl = record.get('total_current_liabilities', 0) or 0
                _bs_liab = record.get('total_liabilities', 0) or 0
                _bs_eq = record.get('owners_equity', 0) or 0
                trends_data['balance_sheet']['Current Ratio (Liquidity)'][year] = (_bs_ca / _bs_cl) if _bs_cl > 0 else record.get('current_ratio', '')
                trends_data['balance_sheet']['Debt to Equity (Safety)'][year] = (_bs_liab / _bs_eq) if _bs_eq > 0 else record.get('debt_to_equity', '')
                trends_data['balance_sheet']['Working Capital as % of Total Assets'][year] = record.get('working_capital_pct_asset', '')
                trends_data['balance_sheet']['Survival Score'][year] = record.get('survival_score', '')
                
                # Cash Flow metrics
                trends_data['cash_flow']['Days Sales Outstanding (DSO)'][year] = record.get('dso', '')

                # Calculate cash flow ratios using centralized function (replaces Airtable values)
                cf_ratios = get_cash_flow_ratios(airtable, st.session_state.selected_company_name, year)
                trends_data['cash_flow']['Operating Cash Flow (OCF)/Revenue'][year] = cf_ratios.get('ocf_rev', '')
                trends_data['cash_flow']['Financing Cash Flow (FCF)/Revenue'][year] = cf_ratios.get('fcf_rev', '')
                trends_data['cash_flow']['Net Cash Flow (NCF)/Revenue'][year] = cf_ratios.get('ncf_rev', '')
            else:
                # Set empty values if no data found
                for metric in trends_data['balance_sheet']:
                    trends_data['balance_sheet'][metric][year] = ''
                for metric in trends_data['cash_flow']:
                    trends_data['cash_flow'][metric][year] = ''
        except Exception as e:
            st.error(f"Error fetching balance sheet data for {year}: {str(e)}")
            # Set empty values on error
            for metric in trends_data['balance_sheet']:
                trends_data['balance_sheet'][metric][year] = ''
            for metric in trends_data['cash_flow']:
                trends_data['cash_flow'][metric][year] = ''
        
        # Get income statement data for this year
        try:
            income_historical = airtable.get_income_statement_data_by_period(st.session_state.selected_company_name, period_filter, is_admin=is_super_admin())
            if income_historical:
                record = income_historical[0]  # Get first record for this period

                # Income Statement metrics
                _ratio_rev = record.get('total_revenue', 0) or 0
                _gpm_gross = record.get('gross_profit', 0) or 0
                _opm_op = record.get('operating_profit', 0) or 0
                _npm_pbt = record.get('profit_before_tax_with_ppp', 0) or 0
                _ebitda_val = record.get('ebitda', 0) or 0
                trends_data['income_statement']['Gross Profit Margin'][year] = (_gpm_gross / _ratio_rev) if _ratio_rev > 0 else record.get('gpm', '')
                trends_data['income_statement']['Operating Profit Margin'][year] = (_opm_op / _ratio_rev) if _ratio_rev > 0 else record.get('opm', '')
                trends_data['income_statement']['Net Profit Margin'][year] = (_npm_pbt / _ratio_rev) if _ratio_rev > 0 else record.get('npm', '')
                trends_data['income_statement']['Revenue Per Admin Employee'][year] = record.get('rev_admin_employee', '')
                trends_data['income_statement']['EBITDA/Revenue'][year] = (_ebitda_val * 1000 / _ratio_rev) if _ratio_rev > 0 else record.get('ebitda_margin', '')

                # Sales/Assets: Revenue / Total Assets (cross-referenced with balance sheet record)
                _sa_total_assets = (_balance_record_for_year.get('total_assets', 0) or 0) if _balance_record_for_year else 0
                trends_data['balance_sheet']['Sales/Assets'][year] = (_ratio_rev / _sa_total_assets) if _sa_total_assets > 0 else record.get('sales_assets', '')
            else:
                # Set empty values if no data found
                for metric in trends_data['income_statement']:
                    trends_data['income_statement'][metric][year] = ''
        except Exception as e:
            st.error(f"Error fetching income statement data for {year}: {str(e)}")
            # Set empty values on error
            for metric in trends_data['income_statement']:
                trends_data['income_statement'][metric][year] = ''
    
    # Fetch group ratio data for current year to calculate group averages
    from pages.group_pages.group_ratios import fetch_group_ratio_data, calculate_group_average
    from shared.year_config import CURRENT_YEAR
    group_ratio_data = fetch_group_ratio_data(f"{CURRENT_YEAR} Annual")

    # Build the HTML table with enhanced font sizes for senior readability
    table_html = """
    <div style="overflow-x: auto; margin: 1rem 0;">
        <table style="width: 100%; border-collapse: collapse; font-family: 'Montserrat', sans-serif; font-size: 1.0rem;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="border: 1px solid #dee2e6; padding: 10px; text-align: left; font-weight: 600; font-size: 1.0rem;"></th>
    """
    
    # Add year headers with enhanced font size
    for year in years:
        table_html += '<th style="border: 1px solid #dee2e6; padding: 10px; text-align: center; font-weight: 600; font-size: 1.0rem;">' + year + '</th>'

    # Add Group Avg column header (dynamic year)
    table_html += f'<th style="border: 1px solid #dee2e6; padding: 10px; text-align: center; font-weight: 600; font-size: 1.0rem; background-color: #025a9a; color: #ffe082;">Group Avg<br>({CURRENT_YEAR})</th>'

    table_html += """
                </tr>
            </thead>
            <tbody>
    """
    
    # Add Balance Sheet section with enhanced font size
    table_html += '<tr style="background-color: #2c3e50; color: white;"><td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600; font-size: 1.0rem;" colspan="7">Balance Sheet</td></tr>'
    
    for metric, values in trends_data['balance_sheet'].items():
        table_html += '<tr><td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">' + metric + '</td>'
        
        # Map metric names to color coding keys
        metric_key_map = {
            'Current Ratio (Liquidity)': 'current_ratio',
            'Debt to Equity (Safety)': 'debt_to_equity',
            'Working Capital as % of Total Assets': 'working_capital_pct',
            'Survival Score': 'survival_score',
            'Sales/Assets': 'sales_assets'
        }
        
        metric_key = metric_key_map.get(metric, '')
        
        for year in years:
            value = values.get(year, '')
            if value != '':
                bg_color = get_cell_color(value, metric_key)
                formatted_value = format_metric_value(value, metric_key)
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: ' + bg_color + '; font-size: 0.95rem;">' + str(formatted_value) + '</td>'
            else:
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; font-size: 0.95rem;">-</td>'
        # Add Group Avg (2024) cell
        if group_ratio_data and metric_key:
            group_avg = calculate_group_average(group_ratio_data, metric_key)
            if group_avg:
                avg_bg_color = get_cell_color(group_avg, metric_key)
                avg_formatted = format_metric_value(group_avg, metric_key)
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: ' + avg_bg_color + '; font-size: 0.95rem; font-weight: 600;">' + str(avg_formatted) + '</td>'
            else:
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #e3f2fd; font-size: 0.95rem;">-</td>'
        else:
            table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #e3f2fd; font-size: 0.95rem;">-</td>'
        table_html += '</tr>'

    # Add Income Statement section with enhanced font size
    table_html += '<tr style="background-color: #2c3e50; color: white;"><td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600; font-size: 1.0rem;" colspan="7">Income Statement</td></tr>'
    
    for metric, values in trends_data['income_statement'].items():
        table_html += '<tr><td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">' + metric + '</td>'
        
        # Map metric names to color coding keys
        metric_key_map = {
            'Gross Profit Margin': 'gpm',
            'Operating Profit Margin': 'opm',
            'Net Profit Margin': 'npm',
            'Revenue Per Admin Employee': 'rev_per_employee',
            'EBITDA/Revenue': 'ebitda_margin'
        }
        
        metric_key = metric_key_map.get(metric, '')
        
        for year in years:
            value = values.get(year, '')
            if value != '':
                bg_color = get_cell_color(value, metric_key)
                formatted_value = format_metric_value(value, metric_key)
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: ' + bg_color + '; font-size: 0.95rem;">' + str(formatted_value) + '</td>'
            else:
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; font-size: 0.95rem;">-</td>'
        # Add Group Avg (2024) cell
        if group_ratio_data and metric_key:
            group_avg = calculate_group_average(group_ratio_data, metric_key)
            if group_avg:
                avg_bg_color = get_cell_color(group_avg, metric_key)
                avg_formatted = format_metric_value(group_avg, metric_key)
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: ' + avg_bg_color + '; font-size: 0.95rem; font-weight: 600;">' + str(avg_formatted) + '</td>'
            else:
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #e3f2fd; font-size: 0.95rem;">-</td>'
        else:
            table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #e3f2fd; font-size: 0.95rem;">-</td>'
        table_html += '</tr>'

    # Add Cash Flow section with enhanced font size
    table_html += '<tr style="background-color: #2c3e50; color: white;"><td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600; font-size: 1.0rem;" colspan="7">Cash Flow</td></tr>'
    
    for metric, values in trends_data['cash_flow'].items():
        table_html += '<tr><td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">' + metric + '</td>'
        
        # Map metric names to color coding keys
        metric_key_map = {
            'Days Sales Outstanding (DSO)': 'dso',
            'Operating Cash Flow (OCF)/Revenue': 'ocf_rev',
            'Financing Cash Flow (FCF)/Revenue': 'fcf_rev',
            'Net Cash Flow (NCF)/Revenue': 'ncf_rev'
        }
        
        metric_key = metric_key_map.get(metric, '')
        
        for year in years:
            value = values.get(year, '')
            if value != '':
                if metric_key:
                    bg_color = get_cell_color(value, metric_key)
                    formatted_value = format_metric_value(value, metric_key)
                else:
                    bg_color = '#f8f9fa'  # Light gray for no range metrics
                    formatted_value = str(value)
                
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: ' + bg_color + '; font-size: 0.95rem;">' + str(formatted_value) + '</td>'
            else:
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; font-size: 0.95rem;">-</td>'
        # Add Group Avg (2024) cell
        if group_ratio_data and metric_key:
            group_avg = calculate_group_average(group_ratio_data, metric_key)
            if group_avg:
                avg_bg_color = get_cell_color(group_avg, metric_key)
                avg_formatted = format_metric_value(group_avg, metric_key)
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: ' + avg_bg_color + '; font-size: 0.95rem; font-weight: 600;">' + str(avg_formatted) + '</td>'
            else:
                table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #e3f2fd; font-size: 0.95rem;">-</td>'
        else:
            table_html += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #e3f2fd; font-size: 0.95rem;">-</td>'
        table_html += '</tr>'

    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)

def display_ratios_sections(balance_data, income_data):
    """Display the ratios sections with gauges"""
    
    # Get period text for headers
    period_text = get_period_display_text()
    
    # Balance Sheet Ratios Section
    st.markdown(f"""
    <div class="ratios-section">
        <h2 class="section-title">Balance Sheet Ratios - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if balance_data:
        latest_balance = balance_data[0]  # Get most recent data
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            _cr_ca = latest_balance.get('total_current_assets', 0) or 0
            _cr_cl = latest_balance.get('total_current_liabilities', 0) or 0
            _computed_cr = (_cr_ca / _cr_cl) if _cr_cl > 0 else (latest_balance.get('current_ratio', 0) or 0)
            fig1 = create_gauge_chart(
                value=_computed_cr,
                title="Current Ratio<br>(Liquidity)",
                min_val=0,
                max_val=3,
                threshold_red=1.2,
                threshold_yellow=2.0,
                format_type="ratio"
            )
            render_gauge_with_formula(fig1, "current_ratio")

        with col2:
            _de_liab = latest_balance.get('total_liabilities', 0) or 0
            _de_eq = latest_balance.get('owners_equity', 0) or 0
            _computed_de = (_de_liab / _de_eq) if _de_eq > 0 else (latest_balance.get('debt_to_equity', 0) or 0)
            fig2 = create_gauge_chart(
                value=_computed_de,
                title="Debt-to-Equity<br>(Safety)",
                min_val=0,
                max_val=3,
                threshold_red=1.4,
                threshold_yellow=2.9,
                format_type="ratio",
                reverse_colors=True
            )
            render_gauge_with_formula(fig2, "debt_to_equity")
        
        with col3:
            fig3 = create_gauge_chart(
                value=latest_balance['working_capital_pct_asset']*100,
                title="Working Capital<br>% of Total Assets",
                min_val=0,
                max_val=50,
                threshold_red=15,
                threshold_yellow=30,
                format_type="percent"
            )
            render_gauge_with_formula(fig3, "working_capital_pct")
        
        with col4:
            fig4 = create_gauge_chart(
                value=latest_balance['survival_score'],
                title="Current<br>Survival Score",
                min_val=0,
                max_val=5,
                threshold_red=2.0,
                threshold_yellow=3.0,
                format_type="ratio"
            )
            render_gauge_with_formula(fig4, "survival_score")
    
    # Income Statement Ratios Section
    st.markdown(f"""
    <div class="ratios-section">
        <h2 class="section-title">Income Statement Ratios - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if income_data:
        latest_income = income_data[0]  # Get most recent data

        # Compute margins from dollar fields to avoid stale stored ratios
        _gi_rev = latest_income.get('total_revenue', 0) or 0
        _gi_gp = latest_income.get('gross_profit', 0) or 0
        _gi_op = latest_income.get('operating_profit', 0) or 0
        _gi_ebitda = latest_income.get('ebitda', 0) or 0
        _computed_gpm = (_gi_gp / _gi_rev * 100) if _gi_rev > 0 else (latest_income.get('gpm', 0) or 0) * 100
        _computed_opm = (_gi_op / _gi_rev * 100) if _gi_rev > 0 else (latest_income.get('opm', 0) or 0) * 100
        _computed_ebitda_margin = (_gi_ebitda * 1000 / _gi_rev * 100) if _gi_rev > 0 else (latest_income.get('ebitda_margin', 0) or 0) * 100

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            fig5 = create_gauge_chart(
                value=_computed_gpm,
                title="Gross Profit<br>Margin",
                min_val=0,
                max_val=50,
                threshold_red=20,
                threshold_yellow=25,
                format_type="percent"
            )
            render_gauge_with_formula(fig5, "gpm")

        with col2:
            fig6 = create_gauge_chart(
                value=_computed_opm,
                title="Operating Profit<br>Margin",
                min_val=0,
                max_val=15,
                threshold_red=3,
                threshold_yellow=5.5,
                format_type="percent"
            )
            render_gauge_with_formula(fig6, "opm")

        with col3:
            # Convert to hundreds of thousands for display
            rev_per_employee_hundreds = latest_income['rev_admin_employee']  if latest_income['rev_admin_employee'] else 0
            fig7 = create_gauge_chart(
                value=rev_per_employee_hundreds,
                title="Revenue Per<br>Admin Employee",
                min_val=0,
                max_val=800,
                threshold_red=325,
                threshold_yellow=550,
                format_type="currency_k"
            )
            render_gauge_with_formula(fig7, "rev_admin_employee")

        with col4:
            fig8 = create_gauge_chart(
                value=_computed_ebitda_margin,
                title="EBITDA/<br>Revenue",
                min_val=0,
                max_val=10,
                threshold_red=2.5,
                threshold_yellow=5,
                format_type="percent"
            )
            render_gauge_with_formula(fig8, "ebitda_margin")
    
    # Ratio Trends Table
    display_ratio_trends_table(balance_data, income_data)
    
    # Add Range Key table at the bottom with enhanced font sizes for senior readability
    st.markdown("""
    <div class="ratios-section" style="margin-top: 2rem;">
        <h3 class="section-title" style="font-size: 1.4rem; margin-bottom: 1rem;">Range Key</h3>
        <div style="overflow-x: auto; margin: 0.5rem 0;">
            <table style="width: 100%; border-collapse: collapse; font-family: 'Montserrat', sans-serif; font-size: 1.0rem;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="border: 1px solid #dee2e6; padding: 10px; text-align: left; font-weight: 600; font-size: 1.0rem;"></th>
                        <th style="border: 1px solid #dee2e6; padding: 10px; text-align: center; font-weight: 600; background-color: #c8e6c9; color: #2e7d32; font-size: 1.0rem;">Great</th>
                        <th style="border: 1px solid #dee2e6; padding: 10px; text-align: center; font-weight: 600; background-color: #fff3c4; color: #f57c00; font-size: 1.0rem;">Caution</th>
                        <th style="border: 1px solid #dee2e6; padding: 10px; text-align: center; font-weight: 600; background-color: #ffcdd2; color: #d32f2f; font-size: 1.0rem;">Improve</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="background-color: #2c3e50; color: white;">
                        <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600; font-size: 1.0rem;" colspan="4">Balance Sheet</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Current Ratio (Liquidity)</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Above 2.0</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">1.2 to 2.0</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 1.3</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Debt to Equity (Safety)</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">0 to 1.4</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">1.5 to 2.9</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Above 3.0</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Working Capital as % of Total Assets</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">30% & above</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">15% to 29%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 15%</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Survival Score</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Above 3.0</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">2.0 to 3.0</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 2.0</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Sales/Assets</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                    </tr>
                    <tr style="background-color: #2c3e50; color: white;">
                        <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600; font-size: 1.0rem;" colspan="4">Income Statement</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Gross Profit Margin</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Above 25%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">20% to 25%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 20%</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Operating Profit Margin</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">5.5% & above</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">3% to 5.4%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 3%</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Net Profit Margin</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Revenue Per Admin Employee</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Above $550</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">$325 to $550</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below $325</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">EBITDA/Revenue</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">5% & above</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">2.5% to 5%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 2.5%</td>
                    </tr>
                    <tr style="background-color: #2c3e50; color: white;">
                        <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600; font-size: 1.0rem;" colspan="4">Cash Flows</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Days Sales Outstanding (DSO)</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">30 & Below</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">30 to 60</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Above 60</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Operating Cash Flow (OCF)/Revenue</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Positive</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">0 to neg 3%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Negative</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Financing Cash Flow (FCF)/Revenue</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Net Cash Flow (NCF)/Revenue</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)