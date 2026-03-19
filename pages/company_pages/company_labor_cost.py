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
from shared.chart_utils import create_gauge_chart
from shared.page_components import get_period_display_text
from shared.auth_utils import require_auth, logout_user, get_current_user_name, get_current_user_email, is_super_admin
from shared.year_config import get_selected_years

# Load environment variables from .env file for local development
load_dotenv()

@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes for better performance
def get_group_averages_for_admin_labor_pct(years_with_data):
    """Calculate group averages for Admin and Labor expenses (% of Revenue) with caching using bulk fetch"""
    airtable = get_airtable_connection()

    group_averages = []
    for year in years_with_data:
        period_filter = f"{year} Annual"

        # Get all companies' income statement data for this year using bulk fetch
        all_companies_data = airtable.get_all_companies_income_statement_by_period(period_filter)

        # Calculate admin labor percentage for each company in this year
        year_admin_labor_percentages = []
        for company_data in all_companies_data:
            # Get the individual components for admin labor calculation
            pr_taxes_benefits = company_data.get('pr_taxes_benefits', 0) or 0
            pension_profit_sharing_401k = company_data.get('pension_profit_sharing_401k', 0) or 0
            salaries_admin = company_data.get('salaries_admin', 0) or 0
            total_revenue = company_data.get('total_revenue', 0) or 0

            # Calculate admin labor dollar amount
            admin_labor_dollars = pr_taxes_benefits + pension_profit_sharing_401k + salaries_admin

            # Calculate percentage using the Airtable formula logic
            if total_revenue != 0 and admin_labor_dollars > 0:
                admin_labor_pct = (admin_labor_dollars / total_revenue) * 100
                year_admin_labor_percentages.append(admin_labor_pct)

        # Calculate average for this year
        if year_admin_labor_percentages:
            group_avg = sum(year_admin_labor_percentages) / len(year_admin_labor_percentages)
            group_averages.append(group_avg)
        else:
            group_averages.append(0)

    return group_averages

@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes for better performance
def get_group_averages_for_revenue_producing_labor_pct(years_with_data):
    """Calculate group averages for Revenue Producing Labor expenses (% of Revenue) with caching using bulk fetch"""
    airtable = get_airtable_connection()

    group_averages = []
    for year in years_with_data:
        period_filter = f"{year} Annual"

        # Get all companies' income statement data for this year using bulk fetch
        all_companies_data = airtable.get_all_companies_income_statement_by_period(period_filter)

        # Calculate revenue producing labor percentage for each company in this year
        year_revenue_labor_percentages = []
        for company_data in all_companies_data:
            # Get the individual components for revenue producing labor calculation
            direct_wages = company_data.get('direct_wages', 0) or 0
            vehicle_operating_expenses = company_data.get('vehicle_operating_expenses', 0) or 0
            oo_exp_intra_state = company_data.get('oo_exp_intra_state', 0) or 0
            oo_inter_state = company_data.get('oo_inter_state', 0) or 0
            oo_packing = company_data.get('oo_packing', 0) or 0
            oo_oi = company_data.get('oo_oi', 0) or 0
            lease_expense_rev_equip = company_data.get('lease_expense_rev_equip', 0) or 0
            oo_other = company_data.get('oo_other', 0) or 0
            total_revenue = company_data.get('total_revenue', 0) or 0

            # Calculate revenue producing labor dollar amount using the Airtable formula
            revenue_labor_dollars = (direct_wages + vehicle_operating_expenses + oo_exp_intra_state +
                                   oo_inter_state + oo_packing + oo_oi + lease_expense_rev_equip + oo_other)

            # Calculate percentage using the Airtable formula logic
            if total_revenue != 0 and revenue_labor_dollars > 0:
                revenue_labor_pct = (revenue_labor_dollars / total_revenue) * 100
                year_revenue_labor_percentages.append(revenue_labor_pct)

        # Calculate average for this year
        if year_revenue_labor_percentages:
            group_avg = sum(year_revenue_labor_percentages) / len(year_revenue_labor_percentages)
            group_averages.append(group_avg)
        else:
            group_averages.append(0)

    return group_averages

@st.cache_data(ttl=900, show_spinner=False)
def get_group_labor_cost_averages(year=None):
    """Calculate group averages for all labor cost metrics.
    Uses the same proven pattern as company_ratios.py - imports from group page.
    Defaults to CURRENT_YEAR from year_config for automatic yearly rollover."""
    from shared.year_config import CURRENT_YEAR
    from pages.group_pages.group_labor_cost import fetch_all_companies_labor_cost
    if year is None:
        year = CURRENT_YEAR
    period_filter = f"{year} Annual"

    # Fetch per-company data using the same function the group page uses
    company_data = fetch_all_companies_labor_cost(period_filter)
    if not company_data:
        return {}

    # Collect values for each metric across all companies
    metrics = {
        'Admin Labor and Expenses': [],
        'Admin Labor and Expenses (% of Revenue)': [],
        'Revenue Producing Labor and Expenses': [],
        'Revenue Producing Labor and Expenses (% of Revenue)': [],
        'Labor Ratio: Labor costs as a percentage of revenue': [],
        'Total Labor and Expenses': [],
        'Total Labor and Expenses (% of Revenue)': []
    }

    for comp_name, data in company_data.items():
        admin_labor = data.get('admin_labor_cost', 0) or 0
        admin_labor_pct = data.get('admin_labor_cost_pct_rev', 0) or 0
        rev_labor = data.get('rev_producing_labor_expenses', 0) or 0
        rev_labor_pct = data.get('rev_producing_labor_expenses_pct_rev', 0) or 0
        labor_ratio = data.get('labor_ratio', 0) or 0
        total_labor = data.get('tot_labor_expenses', 0) or 0
        total_labor_pct = data.get('tot_labor_expenses_pct_rev', 0) or 0

        if admin_labor != 0:
            metrics['Admin Labor and Expenses'].append(float(admin_labor))
        if admin_labor_pct != 0:
            pct = float(admin_labor_pct)
            metrics['Admin Labor and Expenses (% of Revenue)'].append(pct * 100 if pct < 1 else pct)
        if rev_labor != 0:
            metrics['Revenue Producing Labor and Expenses'].append(float(rev_labor))
        if rev_labor_pct != 0:
            pct = float(rev_labor_pct)
            metrics['Revenue Producing Labor and Expenses (% of Revenue)'].append(pct * 100 if pct < 1 else pct)
        if labor_ratio != 0:
            ratio = float(labor_ratio)
            metrics['Labor Ratio: Labor costs as a percentage of revenue'].append(ratio * 100 if ratio < 1 else ratio)
        if total_labor != 0:
            metrics['Total Labor and Expenses'].append(float(total_labor))
        if total_labor_pct != 0:
            pct = float(total_labor_pct)
            metrics['Total Labor and Expenses (% of Revenue)'].append(pct * 100 if pct < 1 else pct)

    # Compute averages
    averages = {}
    for metric, values in metrics.items():
        averages[metric] = sum(values) / len(values) if values else 0

    return averages


# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app




def create_company_sidebar():
    """Create company-specific sidebar navigation"""
    with st.sidebar:        
        # Get current page for active state detection
        current_page = st.session_state.get('current_page', 'company_labor_cost')

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
                key="labor_cost_company_selector",
                index=list(company_options.keys()).index(current_company)
            )
            st.session_state.selected_company_name = selected_company_name
        else:
            st.error("No companies found")
            return

        from shared.year_config import render_year_selector
        render_year_selector()

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Navigation buttons
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
            
        # Labor Cost button - current page
        if button_wrapper("👥 Labor Cost", key="nav_labor", page_id="company_labor_cost", use_container_width=True):
            st.session_state.current_page = "company_labor_cost"
            
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


def create_company_labor_cost_page():
    """Main function for the Labor Cost page"""
    # Require authentication
    require_auth()

    # Initialize session state
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'labor_cost'
    if 'selected_company_name' not in st.session_state:
        st.session_state.selected_company_name = None
    
    # Create company specific sidebar with proper error handling
    try:
        # Clear the entire sidebar first
        st.sidebar.empty()
        
        # Create company specific sidebar
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
    
    if st.session_state.get('current_page') == 'company_actuals':
        from company_actuals import create_company_actuals_page
        create_company_actuals_page()
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
        page_title = f"{st.session_state.selected_company_name} Labor Cost - {period_text}"
    else:
        page_title = f"Company Labor Cost Analysis - {period_text}"
    
    # Use centralized page header with consistent spacing
    create_page_header(
        page_title=page_title,
        show_period_selector=True
    )
    
    # Main content
    if st.session_state.selected_company_name:
        
        # Initialize Airtable connection using shared connection
        airtable = get_airtable_connection()
        
        # Determine which period to use
        if 'period' not in st.session_state:
            st.session_state.period = 'year_end'
        
        period_filter = "2024 Annual" if st.session_state.period == 'year_end' else "June 2024"

        # Main Labor Cost Content

        # Display Labor Cost Trend Table
        with st.spinner(f"Loading {st.session_state.selected_company_name} labor cost..."):
            table_data, years_with_data = display_labor_cost_trend_table(st.session_state.selected_company_name)
        
        # Display Labor Cost Trend Graphs
        if years_with_data:
            display_labor_cost_trend_graphs(st.session_state.selected_company_name, table_data, years_with_data)
        
    else:
        st.warning("Please select a company from the sidebar to view data.")


def display_labor_cost_trend_table(company_name):
    """Display Labor Cost Trend Table with data from 2020-2024"""
    
    if not company_name:
        st.info("Please select a company to view labor cost data.")
        return
    
    # Get historical data from Airtable
    airtable = get_airtable_connection()
    
    # Define years and initialize table data
    years = get_selected_years()
    years_with_data = []
    table_data = {
        'Admin Labor and Expenses': [],
        'Admin Labor and Expenses (% of Revenue)': [],
        'Revenue Producing Labor and Expenses': [],
        'Revenue Producing Labor and Expenses (% of Revenue)': [],
        'Labor Ratio: Labor costs as a percentage of revenue': [],
        'Total Labor and Expenses': [],
        'Total Labor and Expenses (% of Revenue)': []
    }
    
    # Fetch data for each year
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter)
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                
                # Get real data from Airtable fields
                admin_labor = record.get('admin_labor_cost', 0) or 0
                admin_labor_pct = record.get('admin_labor_cost_pct_rev', 0) or 0
                rev_labor = record.get('rev_producing_labor_expenses', 0) or 0
                rev_labor_pct = record.get('rev_producing_labor_expenses_pct_rev', 0) or 0
                labor_ratio = record.get('labor_ratio', 0) or 0
                total_labor = record.get('tot_labor_expenses', 0) or 0
                total_labor_pct = record.get('tot_labor_expenses_pct_rev', 0) or 0
                
                # Only add data if we have real values
                if any([admin_labor, admin_labor_pct, rev_labor, rev_labor_pct, labor_ratio, total_labor, total_labor_pct]):
                    years_with_data.append(year)
                    table_data['Admin Labor and Expenses'].append(admin_labor)
                    table_data['Admin Labor and Expenses (% of Revenue)'].append(admin_labor_pct * 100 if admin_labor_pct < 1 else admin_labor_pct)
                    table_data['Revenue Producing Labor and Expenses'].append(rev_labor)
                    table_data['Revenue Producing Labor and Expenses (% of Revenue)'].append(rev_labor_pct * 100 if rev_labor_pct < 1 else rev_labor_pct)
                    table_data['Labor Ratio: Labor costs as a percentage of revenue'].append(labor_ratio * 100 if labor_ratio < 1 else labor_ratio)
                    table_data['Total Labor and Expenses'].append(total_labor)
                    table_data['Total Labor and Expenses (% of Revenue)'].append(total_labor_pct * 100 if total_labor_pct < 1 else total_labor_pct)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not years_with_data:
        st.info(f"📊 No labor cost data available for {company_name} for the years 2020-2024.")
        return None, None
    
    # Get group averages for current year (dynamic via CURRENT_YEAR)
    from shared.year_config import CURRENT_YEAR
    group_averages = get_group_labor_cost_averages()

    # Create and display the table with only years that have data
    create_labor_cost_table(table_data, years_with_data, group_averages, CURRENT_YEAR)

    # Return the data for reuse in trend graphs
    return table_data, years_with_data


def create_labor_cost_table(table_data, years, group_averages=None, avg_year=None):
    """Create and display the Labor Cost Trend Table with proper styling"""
    
    # Get period display text for dynamic heading
    period_text = get_period_display_text()
    
    # Table title with dynamic period text
    st.markdown(f"""
    <div style="margin: 1.5rem 0;">
        <h3 style="color: #1a202c; font-family: 'Montserrat', sans-serif; font-weight: 600; margin-bottom: 1rem;">Labor Cost Trend Table - {period_text}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create table HTML with clean Atlas blue styling (matching original screenshot)
    table_html = """
    <style>
    .labor-cost-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-family: 'Montserrat', sans-serif;
        border: 1px solid #025a9a;
    }
    .labor-cost-table th {
        background-color: #025a9a;
        color: white;
        padding: 12px;
        text-align: center;
        font-weight: 600;
        border: 1px solid #025a9a;
    }
    .labor-cost-table td {
        padding: 10px;
        border: 1px solid #025a9a;
        text-align: center;
        background-color: white;
    }
    .labor-cost-table .row-label {
        background-color: white;
        color: #1a202c;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid #025a9a;
    }
    .labor-cost-table .header-label {
        background-color: #025a9a;
        color: white;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid #025a9a;
    }
    .labor-cost-table .sub-label {
        background-color: #f0f0f0;
        color: #1a202c;
        font-style: italic;
        text-align: left;
        padding-left: 20px;
        font-size: 0.85rem;
        border: 1px solid #025a9a;
    }
    .overall-rank {
        background-color: #025a9a;
        color: white;
        font-weight: 600;
        border: 1px solid #025a9a;
    }
    </style>
    
    <table class="labor-cost-table">
        <thead>
            <tr>
                <th class="header-label">Labor Cost</th>"""
    
    # Add year headers
    for year in years:
        table_html += f"<th>{year}</th>"
    # Add Group Avg header (dynamic year)
    if group_averages:
        avg_label = avg_year if avg_year else ""
        table_html += f'<th style="background-color: #025a9a; color: #ffe082; font-weight: 600;">Group Avg<br>({avg_label})</th>'
    table_html += "</tr></thead><tbody>"

    # Calculate total columns for separator colspan
    total_cols = len(years) + 2 if group_averages else len(years) + 1

    # Define percentage and currency columns
    percentage_rows = [
        'Admin Labor and Expenses (% of Revenue)',
        'Revenue Producing Labor and Expenses (% of Revenue)',
        'Labor Ratio: Labor costs as a percentage of revenue',
        'Total Labor and Expenses (% of Revenue)'
    ]

    currency_rows = [
        'Admin Labor and Expenses',
        'Revenue Producing Labor and Expenses',
        'Total Labor and Expenses'
    ]

    # Add table rows
    for row_name, values in table_data.items():
        if row_name in currency_rows:
            # Currency rows
            table_html += f'<tr><td class="row-label">{row_name}</td>'
            for value in values:
                formatted_value = f"${value:,.0f}" if value else "$0"
                table_html += f'<td>{formatted_value}</td>'
            # Add group average cell
            if group_averages:
                avg_val = group_averages.get(row_name, 0)
                if avg_val != 0:
                    cell_content = f'${avg_val:,.0f}'
                else:
                    cell_content = '-'
                table_html += f'<td style="background-color: #e3f2fd; font-weight: 600;">{cell_content}</td>'
            table_html += '</tr>'
        elif row_name in percentage_rows:
            # Percentage rows
            table_html += f'<tr><td class="row-label">{row_name}</td>'
            for value in values:
                formatted_value = f"{value:.1f}%" if value else "0.0%"
                table_html += f'<td>{formatted_value}</td>'
            # Add group average cell
            if group_averages:
                avg_val = group_averages.get(row_name, 0)
                if avg_val != 0:
                    cell_content = f'{avg_val:.1f}%'
                else:
                    cell_content = '-'
                table_html += f'<td style="background-color: #e3f2fd; font-weight: 600;">{cell_content}</td>'
            table_html += '</tr>'

        # Add separator after certain rows
        if row_name == 'Admin Labor and Expenses (% of Revenue)':
            table_html += f'<tr><td colspan="{total_cols}" style="border: none; padding: 0;"></td></tr>'
        elif row_name == 'Revenue Producing Labor and Expenses (% of Revenue)':
            table_html += f'<tr><td colspan="{total_cols}" style="border: none; padding: 0;"></td></tr>'
            # Add explanatory text for Labor Ratio
            table_html += f'<tr><td class="sub-label" colspan="{total_cols}" style="border: none;">(Sum of Direct Wages & all O/O Exp divided by All Revenue Categories except Warehouse, Booking/Royalties, & Other Revenue)</td></tr>'
        elif row_name == 'Labor Ratio: Labor costs as a percentage of revenue':
            table_html += f'<tr><td colspan="{total_cols}" style="border: none; padding: 0;"></td></tr>'

    table_html += "</tbody></table>"
    
    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)


def get_sample_labor_data(company_name, year, data_type):
    """Return sample labor cost data for different companies and years"""
    
    # Sample labor cost data by company and year
    labor_data = {
        'ACE': {
            '2020': {
                'admin_labor': 1907283, 'admin_labor_pct': 14.0,
                'rev_labor': 6635872, 'rev_labor_pct': 47.0,
                'labor_ratio': 51.0, 'total_labor': 8543155, 'total_labor_pct': 61.0
            },
            '2021': {
                'admin_labor': 1229403, 'admin_labor_pct': 16.0,
                'rev_labor': 3135852, 'rev_labor_pct': 42.0,
                'labor_ratio': 45.0, 'total_labor': 4365255, 'total_labor_pct': 58.0
            },
            '2022': {
                'admin_labor': 2650695, 'admin_labor_pct': 14.0,
                'rev_labor': 8589209, 'rev_labor_pct': 46.0,
                'labor_ratio': 49.0, 'total_labor': 11239904, 'total_labor_pct': 61.0
            },
            '2023': {
                'admin_labor': 4292109, 'admin_labor_pct': 16.0,
                'rev_labor': 13270864, 'rev_labor_pct': 50.0,
                'labor_ratio': 53.0, 'total_labor': 17562973, 'total_labor_pct': 66.0
            },
            '2024': {
                'admin_labor': 4612104, 'admin_labor_pct': 16.0,
                'rev_labor': 13798982, 'rev_labor_pct': 49.0,
                'labor_ratio': 56.0, 'total_labor': 18411086, 'total_labor_pct': 66.0
            }
        },
        'Ace': {
            '2020': {
                'admin_labor': 1907283, 'admin_labor_pct': 14.0,
                'rev_labor': 6635872, 'rev_labor_pct': 47.0,
                'labor_ratio': 51.0, 'total_labor': 8543155, 'total_labor_pct': 61.0
            },
            '2021': {
                'admin_labor': 1229403, 'admin_labor_pct': 16.0,
                'rev_labor': 3135852, 'rev_labor_pct': 42.0,
                'labor_ratio': 45.0, 'total_labor': 4365255, 'total_labor_pct': 58.0
            },
            '2022': {
                'admin_labor': 2650695, 'admin_labor_pct': 14.0,
                'rev_labor': 8589209, 'rev_labor_pct': 46.0,
                'labor_ratio': 49.0, 'total_labor': 11239904, 'total_labor_pct': 61.0
            },
            '2023': {
                'admin_labor': 4292109, 'admin_labor_pct': 16.0,
                'rev_labor': 13270864, 'rev_labor_pct': 50.0,
                'labor_ratio': 53.0, 'total_labor': 17562973, 'total_labor_pct': 66.0
            },
            '2024': {
                'admin_labor': 4612104, 'admin_labor_pct': 16.0,
                'rev_labor': 13798982, 'rev_labor_pct': 49.0,
                'labor_ratio': 56.0, 'total_labor': 18411086, 'total_labor_pct': 66.0
            }
        },
        'A1': {
            '2020': {
                'admin_labor': 1500000, 'admin_labor_pct': 15.2,
                'rev_labor': 7200000, 'rev_labor_pct': 48.5,
                'labor_ratio': 52.8, 'total_labor': 8700000, 'total_labor_pct': 63.7
            },
            '2021': {
                'admin_labor': 1650000, 'admin_labor_pct': 16.1,
                'rev_labor': 7800000, 'rev_labor_pct': 49.2,
                'labor_ratio': 54.3, 'total_labor': 9450000, 'total_labor_pct': 65.3
            },
            '2022': {
                'admin_labor': 1780000, 'admin_labor_pct': 15.8,
                'rev_labor': 8500000, 'rev_labor_pct': 47.8,
                'labor_ratio': 53.6, 'total_labor': 10280000, 'total_labor_pct': 63.6
            },
            '2023': {
                'admin_labor': 1920000, 'admin_labor_pct': 16.4,
                'rev_labor': 9100000, 'rev_labor_pct': 50.1,
                'labor_ratio': 55.5, 'total_labor': 11020000, 'total_labor_pct': 66.5
            },
            '2024': {
                'admin_labor': 2050000, 'admin_labor_pct': 15.9,
                'rev_labor': 9800000, 'rev_labor_pct': 48.9,
                'labor_ratio': 54.8, 'total_labor': 11850000, 'total_labor_pct': 64.8
            }
        },
        'A-1': {
            '2020': {
                'admin_labor': 1500000, 'admin_labor_pct': 15.2,
                'rev_labor': 7200000, 'rev_labor_pct': 48.5,
                'labor_ratio': 52.8, 'total_labor': 8700000, 'total_labor_pct': 63.7
            },
            '2021': {
                'admin_labor': 1650000, 'admin_labor_pct': 16.1,
                'rev_labor': 7800000, 'rev_labor_pct': 49.2,
                'labor_ratio': 54.3, 'total_labor': 9450000, 'total_labor_pct': 65.3
            },
            '2022': {
                'admin_labor': 1780000, 'admin_labor_pct': 15.8,
                'rev_labor': 8500000, 'rev_labor_pct': 47.8,
                'labor_ratio': 53.6, 'total_labor': 10280000, 'total_labor_pct': 63.6
            },
            '2023': {
                'admin_labor': 1920000, 'admin_labor_pct': 16.4,
                'rev_labor': 9100000, 'rev_labor_pct': 50.1,
                'labor_ratio': 55.5, 'total_labor': 11020000, 'total_labor_pct': 66.5
            },
            '2024': {
                'admin_labor': 2050000, 'admin_labor_pct': 15.9,
                'rev_labor': 9800000, 'rev_labor_pct': 48.9,
                'labor_ratio': 54.8, 'total_labor': 11850000, 'total_labor_pct': 64.8
            }
        },
        'DEFAULT': {
            '2020': {
                'admin_labor': 1056509, 'admin_labor_pct': 18.0,
                'rev_labor': 2508879, 'rev_labor_pct': 44.0,
                'labor_ratio': 53.0, 'total_labor': 3565388, 'total_labor_pct': 62.0
            },
            '2021': {
                'admin_labor': 1229403, 'admin_labor_pct': 16.0,
                'rev_labor': 3135852, 'rev_labor_pct': 42.0,
                'labor_ratio': 45.0, 'total_labor': 4365255, 'total_labor_pct': 58.0
            },
            '2022': {
                'admin_labor': 2650695, 'admin_labor_pct': 14.0,
                'rev_labor': 8589209, 'rev_labor_pct': 46.0,
                'labor_ratio': 49.0, 'total_labor': 11239904, 'total_labor_pct': 61.0
            },
            '2023': {
                'admin_labor': 4292109, 'admin_labor_pct': 16.0,
                'rev_labor': 13270864, 'rev_labor_pct': 50.0,
                'labor_ratio': 53.0, 'total_labor': 17562973, 'total_labor_pct': 66.0
            },
            '2024': {
                'admin_labor': 4612104, 'admin_labor_pct': 16.0,
                'rev_labor': 13798982, 'rev_labor_pct': 49.0,
                'labor_ratio': 56.0, 'total_labor': 18411086, 'total_labor_pct': 66.0
            }
        }
    }
    
    company_data = labor_data.get(company_name, labor_data['DEFAULT'])
    year_data = company_data.get(year, company_data['2024'])
    return year_data.get(data_type, 0)


def display_labor_cost_trend_graphs(company_name, table_data, years_with_data):
    """Display Labor Cost trend charts side by side below the table"""

    # Get period text for section header
    period_text = get_period_display_text()

    # Add section heading with same styling as balance sheet ratio trends
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="labor-trends-section">
        <h2 class="section-title">Labor Cost Trend Graphs - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)

    # Add toggle for group average comparison
    show_group_avg = st.checkbox(
        "**Show Group Average Comparison**",
        value=False,  # Default to unchecked for faster loading
        help="Show group average bars for comparison (uncheck for faster loading)",
        key="labor_cost_show_group_avg"
    )

    # Create two columns for side-by-side charts
    col1, col2 = st.columns(2)

    with col1:
        display_admin_labor_trend(company_name, table_data, years_with_data, show_group_avg)

    with col2:
        display_revenue_producing_labor_trend(company_name, table_data, years_with_data, show_group_avg)
    
    # Add CSS for section styling (matching balance sheet ratio trends)
    st.markdown("""
    <style>
    .labor-trends-section {
        margin: 1rem 0;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 1rem;
        font-family: 'Montserrat', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)


def display_admin_labor_trend(company_name, table_data, years_with_data, show_group_average=True):
    """Display Admin Labor and Expenses (% of Revenue) trend chart with optional group average comparison"""

    # Prepare data for the chart
    admin_labor_values = table_data['Admin Labor and Expenses (% of Revenue)']

    # Get cached group averages only if requested
    if show_group_average:
        group_averages = get_group_averages_for_admin_labor_pct(years_with_data)
    else:
        group_averages = []

    admin_data = {
        'Year': [int(year) for year in years_with_data],
        'Company Admin Labor %': admin_labor_values
    }
    if show_group_average:
        admin_data['Group Average'] = group_averages

    # Create the bar chart using Plotly (matching company value style)
    import plotly.graph_objects as go

    fig = go.Figure()

    # Create custom hover data for company
    company_hover_data = []
    for i, year in enumerate(admin_data['Year']):
        if show_group_average and admin_data.get('Group Average'):
            hover_info = (
                f"<b>Year {year} - {company_name} Admin Labor Analysis</b><br>" +
                f"Company Admin Labor and Expenses (% of Revenue): <b>{admin_data['Company Admin Labor %'][i]:.1f}%</b><br>" +
                f"Group Average Admin Labor and Expenses (% of Revenue): <b>{admin_data['Group Average'][i]:.1f}%</b>"
            )
        else:
            hover_info = (
                f"<b>Year {year} - {company_name} Admin Labor Analysis</b><br>" +
                f"Company Admin Labor and Expenses (% of Revenue): <b>{admin_data['Company Admin Labor %'][i]:.1f}%</b>"
            )
        company_hover_data.append(hover_info)

    # Create custom hover data for group average (only if showing group averages)
    group_hover_data = []
    if show_group_average and admin_data.get('Group Average'):
        for i, year in enumerate(admin_data['Year']):
            avg_val = admin_data['Group Average'][i]
            hover_info = (
                f"<b>Year {year} - Group Average Admin Labor Analysis</b><br>" +
                f"Group Average Admin Labor and Expenses (% of Revenue): <b>{avg_val:.1f}%</b><br>" +
                f"{company_name} Admin Labor and Expenses (% of Revenue): <b>{admin_data['Company Admin Labor %'][i]:.1f}%</b>"
            )
            group_hover_data.append(hover_info)

    # Format bar text for company
    company_bar_text = []
    for val in admin_data['Company Admin Labor %']:
        company_bar_text.append(f'{val:.1f}%')

    # Format bar text for group average (only if showing group averages)
    group_bar_text = []
    if show_group_average and admin_data.get('Group Average'):
        for val in admin_data['Group Average']:
            group_bar_text.append(f'{val:.1f}%')

    # Add company bars
    fig.add_trace(go.Bar(
        x=admin_data['Year'],
        y=admin_data['Company Admin Labor %'],
        name=f'{company_name}',
        marker_color='#025a9a',  # Atlas blue
        text=company_bar_text,
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=company_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        offsetgroup=1
    ))

    # Add group average bars (only if show_group_average is enabled)
    if show_group_average and admin_data.get('Group Average'):
        fig.add_trace(go.Bar(
            x=admin_data['Year'],
            y=admin_data['Group Average'],
            name='Group Average',
            marker_color='#0e9cd5',  # Lighter Atlas blue
            text=group_bar_text,
            textposition='inside',
            textfont=dict(color='white', size=14, family='Montserrat'),
            customdata=group_hover_data,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
            offsetgroup=2
        ))

    # Update layout (matching company value chart style)
    fig.update_layout(
        title={
            'text': 'Admin Labor and Expenses (% of Revenue)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Percentage (%)',
        height=350,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font={'family': 'Montserrat', 'size': 12}
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'family': 'Montserrat', 'size': 12},
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0',
            title_font={'size': 12}
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0',
            title_font={'size': 12}
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def display_revenue_producing_labor_trend(company_name, table_data, years_with_data, show_group_average=True):
    """Display Revenue Producing Labor and Expenses (% of Revenue) trend chart with optional group average comparison"""

    # Prepare data for the chart
    revenue_labor_values = table_data['Revenue Producing Labor and Expenses (% of Revenue)']

    # Get cached group averages only if requested
    if show_group_average:
        group_averages = get_group_averages_for_revenue_producing_labor_pct(years_with_data)
    else:
        group_averages = []

    revenue_labor_data = {
        'Year': [int(year) for year in years_with_data],
        'Company Revenue Labor %': revenue_labor_values
    }
    if show_group_average:
        revenue_labor_data['Group Average'] = group_averages

    # Create the bar chart using Plotly (matching company value style)
    import plotly.graph_objects as go

    fig = go.Figure()

    # Create custom hover data for company
    company_hover_data = []
    for i, year in enumerate(revenue_labor_data['Year']):
        if show_group_average and revenue_labor_data.get('Group Average'):
            hover_info = (
                f"<b>Year {year} - {company_name} Revenue Labor Analysis</b><br>" +
                f"Company Revenue Producing Labor and Expenses (% of Revenue): <b>{revenue_labor_data['Company Revenue Labor %'][i]:.1f}%</b><br>" +
                f"Group Average Revenue Producing Labor and Expenses (% of Revenue): <b>{revenue_labor_data['Group Average'][i]:.1f}%</b>"
            )
        else:
            hover_info = (
                f"<b>Year {year} - {company_name} Revenue Labor Analysis</b><br>" +
                f"Company Revenue Producing Labor and Expenses (% of Revenue): <b>{revenue_labor_data['Company Revenue Labor %'][i]:.1f}%</b>"
            )
        company_hover_data.append(hover_info)

    # Create custom hover data for group average (only if showing group averages)
    group_hover_data = []
    if show_group_average and revenue_labor_data.get('Group Average'):
        for i, year in enumerate(revenue_labor_data['Year']):
            avg_val = revenue_labor_data['Group Average'][i]
            hover_info = (
                f"<b>Year {year} - Group Average Revenue Labor Analysis</b><br>" +
                f"Group Average Revenue Producing Labor and Expenses (% of Revenue): <b>{avg_val:.1f}%</b><br>" +
                f"{company_name} Revenue Producing Labor and Expenses (% of Revenue): <b>{revenue_labor_data['Company Revenue Labor %'][i]:.1f}%</b>"
            )
            group_hover_data.append(hover_info)

    # Format bar text for company
    company_bar_text = []
    for val in revenue_labor_data['Company Revenue Labor %']:
        company_bar_text.append(f'{val:.1f}%')

    # Format bar text for group average (only if showing group averages)
    group_bar_text = []
    if show_group_average and revenue_labor_data.get('Group Average'):
        for val in revenue_labor_data['Group Average']:
            group_bar_text.append(f'{val:.1f}%')

    # Add company bars
    fig.add_trace(go.Bar(
        x=revenue_labor_data['Year'],
        y=revenue_labor_data['Company Revenue Labor %'],
        name=f'{company_name}',
        marker_color='#025a9a',  # Atlas blue
        text=company_bar_text,
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=company_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        offsetgroup=1
    ))

    # Add group average bars (only if show_group_average is enabled)
    if show_group_average and revenue_labor_data.get('Group Average'):
        fig.add_trace(go.Bar(
            x=revenue_labor_data['Year'],
            y=revenue_labor_data['Group Average'],
            name='Group Average',
            marker_color='#0e9cd5',  # Lighter Atlas blue
            text=group_bar_text,
            textposition='inside',
            textfont=dict(color='white', size=14, family='Montserrat'),
            customdata=group_hover_data,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
            offsetgroup=2
        ))

    # Update layout (matching company value chart style)
    fig.update_layout(
        title={
            'text': 'Revenue Producing Labor and Expenses (% of Revenue)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Percentage (%)',
        height=350,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font={'family': 'Montserrat', 'size': 12}
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'family': 'Montserrat', 'size': 12},
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0',
            title_font={'size': 12}
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0',
            title_font={'size': 12}
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    """Main function called from financial_dashboard.py or other entry points"""
    # Apply global CSS styles first (should already be done by parent)
    from shared.css_styles import apply_global_css
    apply_global_css()
    
    # Then create the page
    create_company_labor_cost_page()


if __name__ == "__main__":
    # This allows the file to be run standalone for testing
    st.set_page_config(
        page_title="Labor Cost Analysis",
        page_icon="👥",
        layout="wide"
    )
    main()