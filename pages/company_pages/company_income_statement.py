#!/usr/bin/env python3
"""
Company Income Statement Analysis Page
Atlas BPC 1 Financial Dashboard - Income Statement focused analysis
"""

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Import from shared modules
from shared.airtable_connection import get_airtable_connection
from shared.chart_utils import create_gauge_chart, render_gauge_with_formula
from shared.page_components import get_period_display_text
from shared.auth_utils import require_auth, logout_user, get_current_user_name, get_current_user_email, is_super_admin
from shared.year_config import get_selected_years

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def get_all_income_statement_data_cached(company_name, years_tuple=None):
    """Fetch all income statement data with caching to improve performance"""
    from shared.year_config import get_default_years
    airtable = get_airtable_connection()

    # Fetch historical data for all years at once
    years = list(years_tuple) if years_tuple else get_default_years()
    historical_data = {}

    for year in years:
        period_filter = f"{year} Annual"
        try:
            data = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if data and len(data) > 0:
                historical_data[year] = data[0]  # Take first record
            else:
                historical_data[year] = None
        except Exception:
            historical_data[year] = None

    return historical_data


def create_company_sidebar():
    """Create company-specific sidebar navigation"""
    with st.sidebar:        
        # Get current page for active state detection
        current_page = st.session_state.get('current_page', 'company_income_statement')

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
        if button_wrapper("🏠 Overview", key="income_nav_overview", page_id="overview", use_container_width=True):
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
            key="income_analysis_type_selector"
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
                key="income_statement_company_selector",
                index=list(company_options.keys()).index(current_company)
            )
            st.session_state.selected_company_name = selected_company_name
        else:
            st.error("No companies found")
            return

        from shared.year_config import render_year_selector
        render_year_selector()

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Navigation buttons (matches second screenshot)
        if button_wrapper("% Ratios", key="income_nav_ratios", page_id="company_ratios", use_container_width=True):
            st.session_state.current_page = "company_ratios"
            st.rerun()
        
        if button_wrapper("📊 Balance Sheet", key="income_nav_balance", page_id="company_balance_sheet", use_container_width=True):
            st.session_state.current_page = "company_balance_sheet"
            st.rerun()
        if button_wrapper("📈 Income Statement", key="income_nav_income", page_id="company_income_statement", use_container_width=True):
            st.session_state.current_page = "company_income_statement"
            st.rerun()
        if button_wrapper("💸 Cash Flow", key="income_nav_cash_flow", page_id="company_cash_flow", use_container_width=True):
            st.session_state.current_page = "company_cash_flow"
            st.rerun()
        if button_wrapper("👥 Labor Cost", key="income_nav_labor", page_id="company_labor_cost", use_container_width=True):
            st.session_state.current_page = "company_labor_cost"
            st.rerun()
        if button_wrapper("💎 Value", key="income_nav_value", page_id="company_value", use_container_width=True):
            st.session_state.current_page = "company_value"
            st.rerun()
        if button_wrapper("📋 Actuals", key="income_nav_actuals", page_id="company_actuals", use_container_width=True):
            st.session_state.current_page = "company_actuals"
            st.rerun()
        if button_wrapper("🏆 Wins & Challenges", key="income_nav_wins", page_id="company_wins_challenges", use_container_width=True):
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


def create_company_income_statement_page():
    # Require authentication
    require_auth()

    # CSS is already applied by main function - no need to duplicate
    
    # Initialize session state
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'income_statement_overview'
    if 'selected_company_name' not in st.session_state:
        st.session_state.selected_company_name = None
    
    # Handle page routing to other company pages FIRST (before creating sidebar)
    if st.session_state.get('current_page') == 'company_ratios':
        from company_ratios import create_company_ratios_page
        create_company_ratios_page()
        return
    
    if st.session_state.get('current_page') == 'company_balance_sheet':
        from company_balance_sheet import create_company_balance_sheet_page
        create_company_balance_sheet_page()
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
    
    if st.session_state.get('current_page') == 'company_cash_flow':
        from company_cash_flow import create_company_cash_flow_page
        create_company_cash_flow_page()
        return
    
    if st.session_state.get('current_page') == 'company_wins_challenges':
        from company_wins_challenges import create_company_wins_challenges_page
        create_company_wins_challenges_page()
        return
    
    # Create company income statement specific sidebar with proper error handling
    try:
        # Clear the entire sidebar first
        st.sidebar.empty()
        
        # Create company income statement specific sidebar
        create_company_sidebar()
    except Exception as e:
        st.sidebar.error(f"Error creating sidebar: {str(e)}")
    
    # Import centralized page components
    from shared.page_components import create_page_header
    
    # Get period display text
    period_text = get_period_display_text()
    
    # Determine page title based on selected company
    if st.session_state.selected_company_name:
        page_title = f"{st.session_state.selected_company_name} Income Statement - {period_text}"
    else:
        page_title = f"Company Income Statement Analysis - {period_text}"
    
    # Use centralized page header with consistent spacing
    create_page_header(
        page_title=page_title,
        show_period_selector=True
    )
    
    # Main content
    if st.session_state.selected_company_name:

        # Get cached historical data for selected years - OPTIMIZED!
        years = get_selected_years()
        with st.spinner(f"Loading {st.session_state.selected_company_name} income data..."):
            income_historical_data = get_all_income_statement_data_cached(st.session_state.selected_company_name, tuple(years))

        # Get current year data for compatibility
        airtable = get_airtable_connection()
        income_data = airtable.get_income_statement_data(st.session_state.selected_company_name, is_admin=is_super_admin())

        # Check if we have any data to display
        has_historical_data = any(income_historical_data.values())
        has_current_data = income_data is not None

        if not has_historical_data and not has_current_data:
            st.info(f"⚠️ No income statement data found for {st.session_state.selected_company_name}.")
            st.info("💡 This might be because the data hasn't been uploaded yet or the company name doesn't match exactly.")

        # Display key numbers and income statement sections with historical data
        if has_current_data or has_historical_data:
            display_key_numbers_section(income_data)
            display_income_statement_sections(income_data, income_historical_data)
        else:
            # Show clear message when no real data is available
            st.info(f"📊 No income statement data available for {st.session_state.selected_company_name}.")
            st.info("💡 Data may not have been uploaded yet for this company.")
    
    else:
        st.info("Please select a company from the sidebar to view income statement analysis.")


def display_key_numbers_section(income_data):
    """Display the key numbers section with income statement ratio gauges"""
    
    if income_data:
        latest_income = income_data[0]  # Get most recent data
        
        # Get period text for section header
        period_text = get_period_display_text()
        
        # Key Numbers Section header
        st.markdown(f"""
        <div class="key-numbers-section">
            <h2 class="key-numbers-title">Key Numbers - {period_text}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Create four columns for the income statement gauge charts
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Gross Profit Margin Gauge (computed from gross_profit / total_revenue for accuracy)
            _gpm_gross_profit = latest_income.get('gross_profit', 0) or 0
            _gpm_revenue = latest_income.get('total_revenue', 0) or 0
            gpm_value = (_gpm_gross_profit / _gpm_revenue * 100) if _gpm_revenue > 0 else 0
            fig1 = create_gauge_chart(
                value=gpm_value,
                title="Gross Profit<br>Margin",
                min_val=0,
                max_val=50,
                threshold_red=20,
                threshold_yellow=25,
                format_type="percent"
            )
            render_gauge_with_formula(fig1, "gpm")
        
        with col2:
            # Operating Profit Margin Gauge (computed from operating_profit / total_revenue for accuracy)
            _opm_op_profit = latest_income.get('operating_profit', 0) or 0
            _opm_revenue = latest_income.get('total_revenue', 0) or 0
            opm_value = (_opm_op_profit / _opm_revenue * 100) if _opm_revenue > 0 else 0
            fig2 = create_gauge_chart(
                value=opm_value,
                title="Operating Profit<br>Margin",
                min_val=0,
                max_val=15,
                threshold_red=3,
                threshold_yellow=5.5,
                format_type="percent"
            )
            render_gauge_with_formula(fig2, "opm")
        
        with col3:
            # Net Profit Margin Gauge (profit_before_tax_with_ppp / total_revenue — matches Excel definition)
            _npm_net_profit = latest_income.get('profit_before_tax_with_ppp', 0) or 0
            _npm_revenue = latest_income.get('total_revenue', 0) or 0
            npm_value = (_npm_net_profit / _npm_revenue * 100) if _npm_revenue > 0 else 0
            fig3 = create_gauge_chart(
                value=npm_value,
                title="Net Profit<br>Margin",
                min_val=0,
                max_val=15,
                threshold_red=4,
                threshold_yellow=6.5,
                format_type="percent"
            )
            render_gauge_with_formula(fig3, "npm")

        with col4:
            # Revenue Per Admin Employee Gauge (matches ratios page)
            rev_per_employee = latest_income.get('rev_admin_employee', 0)
            fig4 = create_gauge_chart(
                value=rev_per_employee,
                title="Revenue Per<br>Admin Employee",
                min_val=0,
                max_val=800,
                threshold_red=325,
                threshold_yellow=550,
                format_type="currency_k"
            )
            render_gauge_with_formula(fig4, "rev_admin_employee")
        
        # Add CSS for key numbers section
        st.markdown("""
        <style>
        .key-numbers-section {
            margin: 1.5rem 0 1rem 0;
        }
        .key-numbers-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 1.5rem;
            font-family: 'Montserrat', sans-serif;
            text-align: left;
        }
        </style>
        """, unsafe_allow_html=True)


def display_income_statement_sections(income_data, income_historical_data):
    """Display the income statement analysis sections"""
    
    # Get period text for section header
    period_text = get_period_display_text()
    
    # Income Statement Analysis Section
    st.markdown(f"""
    <div class="income-statement-analysis-section">
        <h2 class="section-title">Income Statement Analysis - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different analysis types
    tab1, tab2, tab3, tab4 = st.tabs(["Revenue & Profitability", "Revenue Diversification", "Income Statement ($)", "Income Statement (% of Rev)"])
    
    with tab1:
        # Revenue & Profitability tab - display combined margin trends and revenue chart
        display_revenue_profitability_chart(st.session_state.selected_company_name, income_historical_data)
        # Add income statement trend graphs
        display_income_statement_trend_graphs(st.session_state.selected_company_name, income_historical_data)

    with tab2:
        # Revenue Diversification tab - display revenue segment percentages chart
        display_revenue_diversification_chart(st.session_state.selected_company_name, income_historical_data)

    with tab3:
        # Income Statement ($) tab - display dollar amounts chart
        display_income_statement_dollars_chart(st.session_state.selected_company_name, income_historical_data)

    with tab4:
        # Income Statement (% of Rev) tab - display percentage charts
        display_income_statement_percentage_chart(st.session_state.selected_company_name, income_historical_data)
    
    # Add CSS for the analysis section
    st.markdown("""
    <style>
    .income-statement-analysis-section {
        margin: 2rem 0 1rem 0;
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


def display_revenue_profitability_chart(company_name, income_historical_data):
    """Display Revenue & Profitability bar chart with GPM, OPM, NPM and Revenue line overlay from 2020-2024"""
    
    if not company_name:
        st.info("Please select a company to view the chart.")
        return
    
    
    # Use cached historical data instead of making API calls
    years = get_selected_years()
    chart_data = {
        'Year': [],
        'Gross Profit Margin': [],
        'Operating Profit Margin': [],
        'Net Profit Margin': [],
        'Total Revenue': []
    }

    for year in years:
        if year in income_historical_data and income_historical_data[year]:
            record = income_historical_data[year]

            # Get total revenue data - be flexible with field names
            total_revenue = record.get('total_revenue', 0) or record.get('Total_Revenue', 0) or record.get('totalrevenue', 0)
            if not total_revenue:
                # Check alternative field names
                total_revenue = record.get('revenue', 0) or record.get('Revenue', 0) or record.get('total_rev', 0) or record.get('sales', 0)

            # Compute margins from dollar fields for accuracy
            _gpm_gross = record.get('gross_profit', 0) or 0
            _opm_op = record.get('operating_profit', 0) or 0
            gpm = (_gpm_gross / total_revenue * 100) if total_revenue > 0 else 0
            opm = (_opm_op / total_revenue * 100) if total_revenue > 0 else 0

            # Compute NPM from profit_before_tax_with_ppp / total_revenue (matches Excel definition)
            _npm_net_profit = record.get('profit_before_tax_with_ppp', 0) or 0
            npm = (_npm_net_profit / total_revenue * 100) if total_revenue > 0 else 0

            # Only add data if we have valid values
            if total_revenue and total_revenue != 0:
                chart_data['Year'].append(year)
                chart_data['Gross Profit Margin'].append(gpm)
                chart_data['Operating Profit Margin'].append(opm)
                chart_data['Net Profit Margin'].append(npm)
                chart_data['Total Revenue'].append(total_revenue)
    
    # Check if we have any data to display
    if not chart_data['Year']:
        st.info(f"📊 No income statement data available for {company_name} for the years 2020-2024.")
        return
    
    # Create the combined chart using Plotly with dual y-axes
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Create custom hover data that shows all values for each year
    combined_hover_data = []
    for i, year in enumerate(chart_data['Year']):
        # Format revenue value for display
        revenue = chart_data['Total Revenue'][i]
        if revenue >= 1000000:
            formatted_revenue = f"${revenue/1000000:.1f}M"
        elif revenue >= 1000:
            formatted_revenue = f"${revenue/1000:.0f}K"
        else:
            formatted_revenue = f"${revenue:,.0f}"
        
        hover_info = (
            f"<b>Year {year} - All Metrics</b><br>" +
            f"Total Revenue: <b>{formatted_revenue}</b><br>" +
            f"Gross Profit Margin: <b>{chart_data['Gross Profit Margin'][i]:.1f}%</b><br>" +
            f"Operating Profit Margin: <b>{chart_data['Operating Profit Margin'][i]:.1f}%</b><br>" +
            f"Net Profit Margin: <b>{chart_data['Net Profit Margin'][i]:.1f}%</b>"
        )
        combined_hover_data.append(hover_info)
    
    # Add Gross Profit Margin bars (darker Atlas blue) - primary y-axis
    fig.add_trace(go.Bar(
        name='Gross Profit Margin',
        x=chart_data['Year'],
        y=chart_data['Gross Profit Margin'],
        marker_color='#025a9a',  # Darker Atlas blue
        text=[f'{val:.1f}%' for val in chart_data['Gross Profit Margin']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=combined_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ), secondary_y=False)
    
    # Add Operating Profit Margin bars (medium Atlas blue) - primary y-axis
    fig.add_trace(go.Bar(
        name='Operating Profit Margin', 
        x=chart_data['Year'],
        y=chart_data['Operating Profit Margin'],
        marker_color='#0e9cd5',  # Medium Atlas blue
        text=[f'{val:.1f}%' for val in chart_data['Operating Profit Margin']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=combined_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ), secondary_y=False)
    
    # Add Net Profit Margin bars (much lighter blue for clear distinction) - primary y-axis
    fig.add_trace(go.Bar(
        name='Net Profit Margin', 
        x=chart_data['Year'],
        y=chart_data['Net Profit Margin'],
        marker_color='#87ceeb',  # Light sky blue - clearly distinguishable
        text=[f'{val:.1f}%' for val in chart_data['Net Profit Margin']],
        textposition='inside',
        textfont=dict(color='#1a202c', size=14, family='Montserrat'),  # Dark text for better contrast on light background
        customdata=combined_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ), secondary_y=False)
    
    # Add Revenue line trace - secondary y-axis
    fig.add_trace(go.Scatter(
        x=chart_data['Year'],
        y=chart_data['Total Revenue'],
        mode='lines+markers',
        name='Total Revenue',
        line=dict(color='#c2002f', width=4),  # Atlas red for contrast against blue bars
        marker=dict(
            color='#c2002f',
            size=10,
            line=dict(color='white', width=2)
        ),
        customdata=combined_hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        showlegend=True
    ), secondary_y=True)
    
    # Add revenue value annotations on data points
    for i, (year, revenue) in enumerate(zip(chart_data['Year'], chart_data['Total Revenue'])):
        # Format revenue value for display
        if revenue >= 1000000:
            formatted_value = f"${revenue/1000000:.1f}M"
        elif revenue >= 1000:
            formatted_value = f"${revenue/1000:.0f}K"
        else:
            formatted_value = f"${revenue:,.0f}"
        
        fig.add_annotation(
            x=year,
            y=revenue,
            text=formatted_value,
            showarrow=False,
            yshift=15,
            font=dict(color='#c2002f', size=12, family='Montserrat'),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#c2002f',
            borderwidth=1,
            xref='x',
            yref='y2'  # Reference secondary y-axis
        )
    
    # Update layout for dual y-axis chart
    fig.update_layout(
        title={
            'text': 'Revenue & Profitability Trends',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        barmode='group',
        height=550,  # Slightly taller to accommodate dual y-axis
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.12,
            xanchor='center',
            x=0.5
        ),
        margin=dict(
            l=80,  # More left margin for primary y-axis
            r=80,  # More right margin for secondary y-axis
            t=60,
            b=90   # More bottom margin for legend
        )
    )
    
    # Set x-axis properties
    fig.update_xaxes(
        tickvals=chart_data['Year'],
        ticktext=[str(year) for year in chart_data['Year']],
        gridcolor='#f0f0f0'
    )
    
    # Set y-axes titles and properties
    fig.update_yaxes(
        title_text="Percentage (%)",
        tickformat='.1f',
        ticksuffix='%',
        gridcolor='#f0f0f0',
        secondary_y=False
    )
    
    fig.update_yaxes(
        title_text="Revenue ($)",
        tickformat='$,.0f',
        secondary_y=True,
        showgrid=False  # Don't show grid for secondary y-axis to avoid confusion
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def display_revenue_diversification_chart(company_name, income_historical_data):
    """Display Revenue Diversification percentage of revenue bar chart with 4 key segments from 2020-2024"""
    
    if not company_name:
        st.info("Please select a company to view the chart.")
        return
    
    # Get historical data from Airtable
    from shared.airtable_connection import get_airtable_connection
    airtable = get_airtable_connection()
    
    # Fetch data for multiple years
    years = get_selected_years()
    chart_data = {
        'Year': [],
        'Local HHG': [],
        'Inter State HHG': [],
        'Office & Industrial': [],
        'Distribution': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                
                # Get revenue diversification data
                total_revenue = record.get('total_revenue', 0) or 0
                local_hhg = record.get('local_hhg', 0) or 0
                inter_state_hhg = record.get('inter_state_hhg', 0) or 0
                office_industrial = record.get('office_industrial', 0) or 0
                distribution = record.get('distribution', 0) or 0
                
                # Only add data if we have real values and can calculate percentages
                if any([local_hhg, inter_state_hhg, office_industrial, distribution]) and total_revenue > 0:
                    local_hhg_pct = (local_hhg / total_revenue) * 100
                    inter_state_hhg_pct = (inter_state_hhg / total_revenue) * 100
                    office_industrial_pct = (office_industrial / total_revenue) * 100
                    distribution_pct = (distribution / total_revenue) * 100
                    
                    chart_data['Year'].append(year)
                    chart_data['Local HHG'].append(local_hhg_pct)
                    chart_data['Inter State HHG'].append(inter_state_hhg_pct)
                    chart_data['Office & Industrial'].append(office_industrial_pct)
                    chart_data['Distribution'].append(distribution_pct)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not chart_data['Year']:
        st.info(f"📊 No revenue diversification data available for {company_name} for the years 2020-2024.")
        return
    
    # Create the bar chart using Plotly (matching income statement percentage chart style)
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Define 4 shades of blue for revenue segments (matching income statement style)
    colors = {
        'Local HHG': '#025a9a',        # Darkest Atlas blue
        'Inter State HHG': '#0e70b8',   # Dark blue
        'Office & Industrial': '#1a85d6', # Medium blue  
        'Distribution': '#4ca3e5'       # Light blue
    }
    
    # Create custom hover data that shows all revenue percentages for each year
    hover_data = []
    for i, year in enumerate(chart_data['Year']):
        hover_info = (
            f"<b>Year {year} - Revenue Diversification (% of Revenue)</b><br>" +
            f"Local HHG: <b>{chart_data['Local HHG'][i]:.1f}%</b><br>" +
            f"Inter State HHG: <b>{chart_data['Inter State HHG'][i]:.1f}%</b><br>" +
            f"Office & Industrial: <b>{chart_data['Office & Industrial'][i]:.1f}%</b><br>" +
            f"Distribution: <b>{chart_data['Distribution'][i]:.1f}%</b>"
        )
        hover_data.append(hover_info)

    # Add Local HHG bars (darkest blue)
    fig.add_trace(go.Bar(
        name='Local HHG',
        x=chart_data['Year'],
        y=chart_data['Local HHG'],
        marker_color=colors['Local HHG'],
        text=[f'{val:.1f}%' for val in chart_data['Local HHG']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Inter State HHG bars (dark blue)
    fig.add_trace(go.Bar(
        name='Inter State HHG',
        x=chart_data['Year'],
        y=chart_data['Inter State HHG'],
        marker_color=colors['Inter State HHG'],
        text=[f'{val:.1f}%' for val in chart_data['Inter State HHG']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Office & Industrial bars (medium blue)
    fig.add_trace(go.Bar(
        name='Office & Industrial',
        x=chart_data['Year'],
        y=chart_data['Office & Industrial'],
        marker_color=colors['Office & Industrial'],
        text=[f'{val:.1f}%' for val in chart_data['Office & Industrial']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Distribution bars (light blue)
    fig.add_trace(go.Bar(
        name='Distribution',
        x=chart_data['Year'],
        y=chart_data['Distribution'],
        marker_color=colors['Distribution'],
        text=[f'{val:.1f}%' for val in chart_data['Distribution']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Update layout (matching income statement percentage chart style)
    fig.update_layout(
        title={
            'text': 'Revenue Diversification - Business Segments (% of Revenue)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Percentage of Revenue (%)',
        barmode='group',
        height=500,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.20,  # Move legend further down to make room for X-axis title
            xanchor='center',
            x=0.5
        ),
        yaxis=dict(
            tickformat='.1f',
            ticksuffix='%',
            gridcolor='#f0f0f0'
        ),
        margin=dict(
            l=60,
            r=60, 
            t=60,
            b=120  # Increase bottom margin more for both X-axis title and legend
        )
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def display_income_statement_dollars_chart(company_name, income_historical_data):
    """Display Income Statement dollar amounts bar chart with 5 key metrics from 2020-2024"""
    
    if not company_name:
        st.info("Please select a company to view the chart.")
        return
    
    # Get historical data from Airtable
    from shared.airtable_connection import get_airtable_connection
    airtable = get_airtable_connection()
    
    # Fetch data for multiple years
    years = get_selected_years()
    chart_data = {
        'Year': [],
        'Total Revenue': [],
        'Total COGS': [],
        'Operating Expense': [],
        'Operating Profit': [],
        'Profit Before Tax': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                
                # Get financial metrics data
                total_revenue = record.get('total_revenue', 0) or 0
                total_cogs = record.get('total_cost_of_revenue', 0) or 0
                operating_expense = record.get('total_operating_expenses', 0) or 0
                operating_profit = record.get('operating_profit', 0) or 0
                profit_before_tax = record.get('profit_before_tax_with_ppp', 0) or 0
                
                # Only add data if we have real values
                if any([total_revenue, total_cogs, operating_expense, operating_profit, profit_before_tax]):
                    chart_data['Year'].append(year)
                    chart_data['Total Revenue'].append(total_revenue)
                    chart_data['Total COGS'].append(total_cogs)
                    chart_data['Operating Expense'].append(operating_expense)
                    chart_data['Operating Profit'].append(operating_profit)
                    chart_data['Profit Before Tax'].append(profit_before_tax)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not chart_data['Year']:
        st.info(f"📊 No financial data available for {company_name} for the years 2020-2024.")
        return
    
    # Create the bar chart using Plotly (matching revenue profitability chart style)
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Define 5 shades of blue from darkest to lightest
    colors = {
        'Total Revenue': '#025a9a',      # Darkest Atlas blue
        'Total COGS': '#0e70b8',        # Dark blue
        'Operating Expense': '#1a85d6',  # Medium blue  
        'Operating Profit': '#4ca3e5',   # Light blue
        'Profit Before Tax': '#87ceeb'   # Lightest blue (light sky blue)
    }
    
    # Create custom hover data that shows all metrics for each year
    hover_data = []
    for i, year in enumerate(chart_data['Year']):
        hover_info = (
            f"<b>Year {year} - All Metrics</b><br>" +
            f"Total Revenue: <b>{format_currency_value(chart_data['Total Revenue'][i])}</b><br>" +
            f"Total COGS: <b>{format_currency_value(chart_data['Total COGS'][i])}</b><br>" +
            f"Operating Expense: <b>{format_currency_value(chart_data['Operating Expense'][i])}</b><br>" +
            f"Operating Profit: <b>{format_currency_value(chart_data['Operating Profit'][i])}</b><br>" +
            f"Profit Before Tax: <b>{format_currency_value(chart_data['Profit Before Tax'][i])}</b>"
        )
        hover_data.append(hover_info)

    # Add Total Revenue bars (darkest blue)
    fig.add_trace(go.Bar(
        name='Total Revenue',
        x=chart_data['Year'],
        y=chart_data['Total Revenue'],
        marker_color=colors['Total Revenue'],
        text=[format_currency_value(val) for val in chart_data['Total Revenue']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Total COGS bars
    fig.add_trace(go.Bar(
        name='Total COGS',
        x=chart_data['Year'],
        y=chart_data['Total COGS'],
        marker_color=colors['Total COGS'],
        text=[format_currency_value(val) for val in chart_data['Total COGS']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Operating Expense bars
    fig.add_trace(go.Bar(
        name='Operating Expense',
        x=chart_data['Year'],
        y=chart_data['Operating Expense'],
        marker_color=colors['Operating Expense'],
        text=[format_currency_value(val) for val in chart_data['Operating Expense']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Operating Profit bars
    fig.add_trace(go.Bar(
        name='Operating Profit',
        x=chart_data['Year'],
        y=chart_data['Operating Profit'],
        marker_color=colors['Operating Profit'],
        text=[format_currency_value(val) for val in chart_data['Operating Profit']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Profit Before Tax bars (lightest blue)
    fig.add_trace(go.Bar(
        name='Profit Before Tax',
        x=chart_data['Year'],
        y=chart_data['Profit Before Tax'],
        marker_color=colors['Profit Before Tax'],
        text=[format_currency_value(val) for val in chart_data['Profit Before Tax']],
        textposition='inside',
        textfont=dict(color='#1a202c', size=14, family='Montserrat'),  # Dark text for light background
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Update layout (matching revenue profitability chart style)
    fig.update_layout(
        title={
            'text': 'Income Statement - Key Financial Metrics ($)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Amount (USD)',
        barmode='group',
        height=500,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.20,  # Move legend further down to make room for X-axis title
            xanchor='center',
            x=0.5
        ),
        yaxis=dict(
            tickformat='$,.0f',
            gridcolor='#f0f0f0'
        ),
        margin=dict(
            l=60,
            r=60, 
            t=60,
            b=120  # Increase bottom margin more for both X-axis title and legend
        )
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def display_income_statement_percentage_chart(company_name, income_historical_data):
    """Display Income Statement percentage of revenue bar chart with 4 key metrics from 2020-2024"""
    
    if not company_name:
        st.info("Please select a company to view the chart.")
        return
    
    # Get historical data from Airtable
    from shared.airtable_connection import get_airtable_connection
    airtable = get_airtable_connection()
    
    # Fetch data for multiple years
    years = get_selected_years()
    chart_data = {
        'Year': [],
        'Total Revenue': [],
        'Total COGS': [],
        'Operating Expense': [],
        'Operating Profit': [],
        'Profit Before Tax': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                
                # Get financial metrics data
                total_revenue = record.get('total_revenue', 0) or 0
                total_cogs = record.get('total_cost_of_revenue', 0) or 0
                operating_expense = record.get('total_operating_expenses', 0) or 0
                operating_profit = record.get('operating_profit', 0) or 0
                profit_before_tax = record.get('profit_before_tax_with_ppp', 0) or 0
                
                # Only add data if we have real values and can calculate percentages
                if any([total_revenue, total_cogs, operating_expense, operating_profit, profit_before_tax]) and total_revenue > 0:
                    revenue_pct = 100  # Total Revenue is always 100%
                    cogs_pct = (total_cogs / total_revenue) * 100
                    opex_pct = (operating_expense / total_revenue) * 100
                    op_profit_pct = (operating_profit / total_revenue) * 100
                    pbt_pct = (profit_before_tax / total_revenue) * 100
                    
                    chart_data['Year'].append(year)
                    chart_data['Total Revenue'].append(revenue_pct)
                    chart_data['Total COGS'].append(cogs_pct)
                    chart_data['Operating Expense'].append(opex_pct)
                    chart_data['Operating Profit'].append(op_profit_pct)
                    chart_data['Profit Before Tax'].append(pbt_pct)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not chart_data['Year']:
        st.info(f"📊 No financial data available for {company_name} for the years 2020-2024.")
        return
    
    # Create the bar chart using Plotly (matching dollar chart style)
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Define 5 shades of blue (same as dollar chart but for percentages)
    colors = {
        'Total Revenue': '#025a9a',      # Darkest Atlas blue (100%)
        'Total COGS': '#0e70b8',         # Dark blue
        'Operating Expense': '#1a85d6',   # Medium blue  
        'Operating Profit': '#4ca3e5',    # Light blue
        'Profit Before Tax': '#87ceeb'    # Lightest blue (light sky blue)
    }
    
    # Create custom hover data that shows all percentage metrics for each year
    hover_data = []
    for i, year in enumerate(chart_data['Year']):
        hover_info = (
            f"<b>Year {year} - All Metrics (% of Revenue)</b><br>" +
            f"Total Revenue: <b>{chart_data['Total Revenue'][i]:.1f}%</b><br>" +
            f"Total COGS: <b>{chart_data['Total COGS'][i]:.1f}%</b><br>" +
            f"Operating Expense: <b>{chart_data['Operating Expense'][i]:.1f}%</b><br>" +
            f"Operating Profit: <b>{chart_data['Operating Profit'][i]:.1f}%</b><br>" +
            f"Profit Before Tax: <b>{chart_data['Profit Before Tax'][i]:.1f}%</b>"
        )
        hover_data.append(hover_info)

    # Add Total Revenue bars (darkest blue - always 100%)
    fig.add_trace(go.Bar(
        name='Total Revenue',
        x=chart_data['Year'],
        y=chart_data['Total Revenue'],
        marker_color=colors['Total Revenue'],
        text=[f'{val:.1f}%' for val in chart_data['Total Revenue']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Total COGS bars (dark blue)
    fig.add_trace(go.Bar(
        name='Total COGS',
        x=chart_data['Year'],
        y=chart_data['Total COGS'],
        marker_color=colors['Total COGS'],
        text=[f'{val:.1f}%' for val in chart_data['Total COGS']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Operating Expense bars
    fig.add_trace(go.Bar(
        name='Operating Expense',
        x=chart_data['Year'],
        y=chart_data['Operating Expense'],
        marker_color=colors['Operating Expense'],
        text=[f'{val:.1f}%' for val in chart_data['Operating Expense']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Operating Profit bars
    fig.add_trace(go.Bar(
        name='Operating Profit',
        x=chart_data['Year'],
        y=chart_data['Operating Profit'],
        marker_color=colors['Operating Profit'],
        text=[f'{val:.1f}%' for val in chart_data['Operating Profit']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Profit Before Tax bars (lightest blue)
    fig.add_trace(go.Bar(
        name='Profit Before Tax',
        x=chart_data['Year'],
        y=chart_data['Profit Before Tax'],
        marker_color=colors['Profit Before Tax'],
        text=[f'{val:.1f}%' for val in chart_data['Profit Before Tax']],
        textposition='inside',
        textfont=dict(color='#1a202c', size=14, family='Montserrat'),  # Dark text for light background
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Update layout (matching dollar chart style)
    fig.update_layout(
        title={
            'text': 'Income Statement - Key Financial Metrics (% of Revenue)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Percentage of Revenue (%)',
        barmode='group',
        height=500,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.20,  # Move legend further down to make room for X-axis title
            xanchor='center',
            x=0.5
        ),
        yaxis=dict(
            tickformat='.1f',
            ticksuffix='%',
            gridcolor='#f0f0f0'
        ),
        margin=dict(
            l=60,
            r=60, 
            t=60,
            b=120  # Increase bottom margin more for both X-axis title and legend
        )
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Add Income Statement trend table below the chart
    display_income_statement_trend_table(company_name)


def display_income_statement_trend_table(company_name):
    """Display Income Statement trend table as percentage of revenue from 2020-2024"""
    
    if not company_name:
        st.info("Please select a company to view the trend table.")
        return
    
    # Get historical data from Airtable
    airtable = get_airtable_connection()
    
    # Fetch data for available years (2020-2024) 
    years = get_selected_years()
    table_data = {}
    
    # Income statement line items matching the screenshot format (excluding rank rows as specified)
    income_statement_items = [
        # Revenue Section - show actual dollar amounts first
        ('Revenue', 'total_revenue', True, True),  # Header with actual values
        ('Intra State HHG', 'intra_state_hhg', False, False),
        ('Local HHG', 'local_hhg', False, False),
        ('Inter State HHG', 'inter_state_hhg', False, False),
        ('Office & Industrial', 'office_industrial', False, False),
        ('Warehouse (Non-commercial)', 'warehouse', False, False),
        ('Warehouse handling (Non-commercial)', 'warehouse_handling', False, False),
        ('International', 'international', False, False),
        ('Packing & Unpacking', 'packing_unpacking', False, False),
        ('Booking & Royalties', 'booking_royalties', False, False),
        ('Special Products', 'special_products', False, False),
        ('Records Storage', 'records_storage', False, False),
        ('Military DPM Contracts', 'military_dpm_contracts', False, False),
        ('Distribution', 'distribution', False, False),
        ('Hotel Deliveries', 'hotel_deliveries', False, False),
        ('Other Revenue', 'other_revenue', False, False),
        ('Total Revenue', 'total_revenue', True, True),  # Major total showing dollar amounts
        
        # Direct Expenses Section - show as percentages
        ('Direct Wages', 'direct_wages', False, False),
        ('Vehicle Operating Expense', 'vehicle_operating_expenses', False, False),
        ('Packing & Warehouse Supplies', 'packing_warehouse_supplies', False, False),
        ('Owner Operator - Intra State', 'oo_exp_intra_state', False, False),
        ('Owner Operator - Inter State', 'oo_inter_state', False, False),
        ('Owner Operator - Office & Industrial', 'oo_oi', False, False),
        ('Owner Operator - Packing', 'oo_packing', False, False),
        ('Owner Operator - General & Other', 'oo_other', False, False),
        ('Claims', 'claims', False, False),
        ('Other Transportation Expense', 'other_trans_exp', False, False),
        ('Lease Expense - Revenue Equipment', 'lease_expense_rev_equip', False, False),
        ('Other Direct Expenses', 'other_direct_expenses', False, False),
        ('Rent and/or Building Expense', 'rent', False, False),
        ('Depreciation/Amortization', 'depreciation', False, False),
        ('Total Cost Of Revenue', 'total_cost_of_revenue', True, False),
        ('Gross Profit Margin', 'gross_profit', True, False),
        
        # Operating Expenses Section - show as percentages
        ('Advertising & Marketing', 'advertising_marketing', False, False),
        ('Bad Debts', 'bad_debts', False, False),
        ('Sales Compensation', 'sales_commissions', False, False),
        ('Contributions', 'contributions', False, False),
        ('Computer Support', 'computer_support', False, False),
        ('Dues & Subscriptions', 'dues_sub', False, False),
        ('Payroll Taxes & Benefits', 'pr_taxes_benefits', False, False),
        ('Lease Expense - Office Equipment', 'equipment_leases_office_equip', False, False),
        ('Workers\' Comp. Insurance', 'workmans_comp_insurance', False, False),
        ('Insurance', 'insurance', False, False),
        ('Legal & Accounting', 'legal_accounting', False, False),
        ('Office Expense', 'office_expense', False, False),
        ('Other Administrative', 'other_admin', False, False),
        ('Pension, profit sharing, 401K', 'pension_profit_sharing_401k', False, False),
        ('Professional Fees', 'prof_fees', False, False),
        ('Repairs & Maintenance', 'repairs_maint', False, False),
        ('Salaries - Administrative', 'salaries_admin', False, False),
        ('Rent and/or Building Expense', 'rent', False, False),  # Same field as direct expenses
        ('Depreciation/Amortization', 'depreciation', False, False),  # Same field as direct expenses
        ('Taxes & Licenses', 'taxes_licenses', False, False),
        ('Telephone/Fax/Utilities/Internet', 'tel_fax_utilities_internet', False, False),
        ('Travel & Entertainment', 'travel_ent', False, False),
        ('Vehicle Expense - Administrative', 'vehicle_expense_admin', False, False),
        ('Total Operating Expenses (% of Revenue)', 'total_operating_expenses', True, False),
        ('Operating Profit Margin', 'operating_profit', True, False),
        
        # Other Income/Expense Section - show as percentages
        ('PPP Funds Received (forgiven)', 'ppp_forgiven', False, False),
        ('Other Income', 'other_income', False, False),
        ('CEO Comp/Perks (-)', 'ceo_comp', False, False),
        ('Other Expense (-)', 'other_expense', False, False),
        ('Interest Expense (-)', 'interest_expense', False, False),
        ('Total Other Income / Expense (% of Revenue)', 'total_nonoperating_income', True, False),
        ('Net Profit Margin', 'profit_before_tax_with_ppp', True, False)
    ]
    
    # Collect data for all years
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                table_data[year] = record
        except Exception as e:
            table_data[year] = {}
    
    # Calculate averages across all years for the company
    averages_data = {}
    valid_years = [year for year in years if year in table_data and table_data[year]]
    
    if valid_years:
        # Calculate average total revenue first
        total_revenues = [table_data[year].get('total_revenue', 0) or 0 for year in valid_years]
        avg_total_revenue = sum(total_revenues) / len(valid_years) if valid_years else 0
        averages_data['total_revenue'] = avg_total_revenue
        
        # Calculate average for each field across all line items
        for item_name, field_name, is_total, is_major_total in income_statement_items:
            field_values = [table_data[year].get(field_name, 0) or 0 for year in valid_years]
            averages_data[field_name] = sum(field_values) / len(valid_years) if valid_years else 0
    
    # Store average percentages for variance comparison
    avg_percentages = {}
    if averages_data:
        avg_total_revenue = averages_data.get('total_revenue', 0)
        for item_name, field_name, is_total, is_major_total in income_statement_items:
            if avg_total_revenue > 0 and field_name != 'total_revenue':
                avg_field_value = averages_data.get(field_name, 0)
                if field_name in ['total_cost_of_revenue', 'total_operating_expenses', 'total_nonoperating_income', 'gross_profit', 'operating_profit', 'net_profit', 'profit_before_tax_with_ppp']:
                    # These are aggregate dollar amounts that need to be calculated as percentage of revenue
                    avg_percentages[field_name] = (avg_field_value / avg_total_revenue) * 100
                else:
                    # Other items are calculated the same way
                    avg_percentages[field_name] = (avg_field_value / avg_total_revenue) * 100
    
    def get_cell_color(current_pct, avg_pct, field_name, item_name):
        """Determine cell background color based on variance from average"""
        # Skip if no valid comparison data
        if not avg_pct or current_pct == 0 or avg_pct == 0:
            return ""
        
        # Calculate variance percentage
        variance = ((current_pct - avg_pct) / abs(avg_pct)) * 100
        
        # Define expense items (lower is better)
        expense_items = [
            'total_cost_of_revenue', 'total_operating_expenses', 'direct_wages',
            'vehicle_operating_expenses', 'packing_warehouse_supplies', 'oo_exp_intra_state',
            'oo_inter_state', 'oo_oi', 'oo_packing', 'oo_other', 'claims', 'other_trans_exp',
            'lease_expense_rev_equip', 'other_direct_expenses', 'rent', 'depreciation',
            'advertising_marketing', 'bad_debts', 'sales_commissions', 'contributions',
            'computer_support', 'dues_sub', 'pr_taxes_benefits', 'equipment_leases_office_equip',
            'workmans_comp_insurance', 'insurance', 'legal_accounting', 'office_expense',
            'other_admin', 'pension_profit_sharing_401k', 'prof_fees', 'repairs_maint',
            'salaries_admin', 'taxes_licenses', 'tel_fax_utilities_internet', 'travel_ent',
            'vehicle_expense_admin', 'ceo_comp', 'other_expense', 'interest_expense'
        ]
        
        # Define profit/revenue items (higher is better)
        profit_items = ['gross_profit', 'operating_profit', 'net_profit', 'profit_before_tax_with_ppp']
        
        # Check if this is an expense item
        is_expense = (field_name in expense_items or 
                     'expense' in item_name.lower() or 
                     'cost' in item_name.lower() or
                     'wages' in item_name.lower() or
                     'operator' in item_name.lower() or
                     'claims' in item_name.lower() or
                     'depreciation' in item_name.lower())
        
        # For expense items, lower is better (inverse coloring)
        if is_expense:
            if variance < -10:  # More than 10% below average (good for expenses)
                return "background-color: #d4edda;"  # Light green
            elif variance > 10:  # More than 10% above average (bad for expenses)
                return "background-color: #f8d7da;"  # Light red
        # For profit/revenue items, higher is better
        else:
            if variance > 10:  # More than 10% above average (good)
                return "background-color: #d4edda;"  # Light green
            elif variance < -10:  # More than 10% below average (bad)
                return "background-color: #f8d7da;"  # Light red
        
        return ""  # No color for normal variance (within ±10%)
    
    # Generate HTML table
    st.markdown("### Income Statement Trend Table")
    
    # Add color coding legend
    st.markdown("""
    <div style="margin-bottom: 15px; padding: 8px; background-color: #f8f9fa; border-radius: 5px; font-size: 0.9rem; color: #495057;">
        <strong>Color Legend:</strong>
        <span style="background-color: #d4edda; padding: 2px 6px; border-radius: 3px; margin: 0 5px;">■</span> >10% better than average
        <span style="background-color: #f8d7da; padding: 2px 6px; border-radius: 3px; margin: 0 5px;">■</span> >10% worse than average
        <span style="background-color: #e6f7ff; padding: 2px 6px; border-radius: 3px; margin: 0 5px;">■</span> within ±10% variance
    </div>
    """, unsafe_allow_html=True)
    
    # Add CSS for sticky header and scrollable container
    st.markdown("""
    <style>
    .income-statement-trend-container {
        max-height: 800px;
        overflow-y: auto;
        position: relative;
        margin: 1rem 0;
    }
    .income-statement-trend-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', sans-serif;
    }
    .income-statement-trend-table thead {
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .income-statement-trend-table th {
        background-color: #025a9a;
        color: white;
        padding: 8px;
        border: 1px solid #ddd;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .income-statement-trend-table tbody tr:hover td {
        box-shadow: inset 0 2px 0 #025a9a, inset 0 -2px 0 #025a9a;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create table header
    header_html = "<div class='income-statement-trend-container'><table class='income-statement-trend-table'>"
    header_html += "<thead><tr>"
    header_html += "<th style='text-align: left;'>Income Statement</th>"

    # Add Averages column header first (before years) with yellow/gold text color matching group page
    header_html += f"<th style='text-align: center; color: #ffe082;'>Averages</th>"

    # Add year columns (2020-2024)
    display_years = get_selected_years()
    for year in display_years:
        header_html += f"<th style='text-align: center;'>{year}</th>"

    header_html += "</tr></thead><tbody>"
    
    # Add table rows
    table_html = header_html
    
    for item_name, field_name, is_total, is_major_total in income_statement_items:
        # Skip if this is a header row or major section separator
        if is_major_total and item_name in ['Revenue', 'Total Revenue']:
            # Add revenue row with actual dollar values first
            if item_name == 'Revenue':
                row_style = "background-color: #f8f9fa; font-weight: bold;"
                table_html += f"<tr style='{row_style}'>"
                table_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{item_name}</td>"

                # Add averages column for Revenue row FIRST
                if averages_data and 'total_revenue' in averages_data:
                    avg_revenue = averages_data.get('total_revenue', 0)
                    if avg_revenue > 0:
                        formatted_avg = f"${avg_revenue:,.0f}"
                    else:
                        formatted_avg = "-"
                else:
                    formatted_avg = "-"
                table_html += f"<td style='padding: 6px; border: 1px solid #ddd; text-align: center; background-color: #e6f7ff; font-weight: 600;'>{formatted_avg}</td>"

                # Then add year columns
                for year in display_years:
                    if year in table_data:
                        total_revenue = table_data[year].get('total_revenue', 0) or 0
                        if total_revenue > 0:
                            formatted_value = f"${total_revenue:,.0f}"
                        else:
                            formatted_value = "-"
                    else:
                        formatted_value = "-"
                    table_html += f"<td style='padding: 6px; border: 1px solid #ddd; text-align: center;'>{formatted_value}</td>"

                table_html += "</tr>"
                continue
        
        # Determine row styling
        if is_major_total:
            row_style = "background-color: #6c757d; color: white; font-weight: bold;"  # Dark grey for major totals
        elif is_total:
            row_style = "background-color: #e9ecef; font-weight: bold;"  # Light grey for subtotals
        else:
            row_style = ""
        
        table_html += f"<tr style='{row_style}'>"
        table_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{item_name}</td>"

        # Add averages column FIRST (before year columns)
        if averages_data:
            avg_total_revenue = averages_data.get('total_revenue', 0)

            if field_name == 'total_revenue' and item_name == 'Revenue':
                # Revenue header row - already handled above, skip
                formatted_avg = ""
            elif field_name == 'total_revenue' and item_name == 'Total Revenue':
                # Total Revenue row shows 100% (always 100% of itself)
                formatted_avg = "100%"
            elif field_name in ['total_cost_of_revenue', 'total_operating_expenses', 'total_nonoperating_income', 'gross_profit', 'operating_profit', 'net_profit', 'profit_before_tax_with_ppp']:
                # These are aggregate dollar amounts that need to be calculated as percentage of average revenue
                avg_field_value = averages_data.get(field_name, 0)
                if avg_total_revenue > 0:
                    percentage = (avg_field_value / avg_total_revenue) * 100
                    formatted_avg = f"{percentage:.1f}%"
                else:
                    formatted_avg = "-"
            else:
                # All other items show as percentage of average revenue
                avg_field_value = averages_data.get(field_name, 0)
                if avg_total_revenue > 0 and avg_field_value != 0:
                    percentage = (avg_field_value / avg_total_revenue) * 100
                    formatted_avg = f"{percentage:.1f}%"
                else:
                    formatted_avg = "0.0%" if avg_total_revenue > 0 else "-"
        else:
            formatted_avg = "-"

        # Output averages column (skip only the Revenue header row as it's already handled above)
        if item_name != 'Revenue':
            # Use dark grey background for Total Revenue row, light blue for all others
            if item_name == 'Total Revenue':
                table_html += f"<td style='padding: 6px; border: 1px solid #ddd; text-align: center; background-color: #6c757d; color: white; font-weight: bold;'>{formatted_avg}</td>"
            else:
                table_html += f"<td style='padding: 6px; border: 1px solid #ddd; text-align: center; background-color: #e6f7ff; font-weight: 600;'>{formatted_avg}</td>"

        # Add data for each year
        for year in display_years:
            if year in table_data:
                record = table_data[year]
                total_revenue = record.get('total_revenue', 0) or 0
                
                if field_name == 'total_revenue' and item_name == 'Revenue':
                    # Revenue header row shows actual dollar amounts
                    if total_revenue > 0:
                        formatted_value = f"${total_revenue:,.0f}"
                    else:
                        formatted_value = "-"
                elif field_name == 'total_revenue' and item_name == 'Total Revenue':
                    # Total Revenue row shows 100% (since it's always 100% of itself)
                    formatted_value = "100%" if total_revenue > 0 else "-"
                elif field_name == 'overall_rank':
                    # Overall Rank shows rank numbers, not percentages
                    rank_value = record.get(field_name, 0) or 0
                    if rank_value > 0:
                        formatted_value = str(int(rank_value))
                    else:
                        formatted_value = "-"
                elif field_name in ['total_cost_of_revenue', 'total_operating_expenses', 'total_nonoperating_income', 'gross_profit', 'operating_profit', 'net_profit', 'profit_before_tax_with_ppp']:
                    # These are aggregate dollar amounts that need to be calculated as percentage of revenue
                    field_value = record.get(field_name, 0) or 0
                    if total_revenue > 0:
                        percentage = (field_value / total_revenue) * 100
                        formatted_value = f"{percentage:.1f}%"
                    else:
                        formatted_value = "-"
                else:
                    # All other items show as percentage of revenue
                    field_value = record.get(field_name, 0) or 0
                    if total_revenue > 0 and field_value != 0:
                        percentage = (field_value / total_revenue) * 100
                        formatted_value = f"{percentage:.1f}%"
                    else:
                        formatted_value = "0.0%" if total_revenue > 0 else "-"
            else:
                formatted_value = "-"
            
            # Calculate color for this cell based on variance from average
            cell_color = ""
            if (field_name not in ['total_revenue', 'overall_rank'] and 
                item_name not in ['Revenue', 'Total Revenue'] and 
                avg_percentages and 
                field_name in avg_percentages and 
                year in table_data and 
                formatted_value != "-"):
                
                avg_pct = avg_percentages[field_name]
                
                # Get current percentage (recalculate to match the logic above)
                record = table_data[year]
                total_revenue = record.get('total_revenue', 0) or 0
                
                if total_revenue > 0:
                    field_value = record.get(field_name, 0) or 0
                    
                    if field_name in ['total_cost_of_revenue', 'total_operating_expenses', 'total_nonoperating_income', 'gross_profit', 'operating_profit', 'net_profit', 'profit_before_tax_with_ppp']:
                        # These are aggregate dollar amounts
                        current_pct = (field_value / total_revenue) * 100
                    else:
                        # Other items
                        current_pct = (field_value / total_revenue) * 100
                    
                    cell_color = get_cell_color(current_pct, avg_pct, field_name, item_name)
            
            table_html += f"<td style='padding: 6px; border: 1px solid #ddd; text-align: center; {cell_color}'>{formatted_value}</td>"

        table_html += "</tr>"

    table_html += "</tbody></table></div>"

    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)


def format_currency_value(value):
    """Format currency value with K/M suffixes for readability"""
    if value >= 1000000:
        return f"${value/1000000:.1f}M"
    elif value >= 1000:
        return f"${value/1000:.0f}K"
    else:
        return f"${value:,.0f}"


def display_revenue_trends_section(company_name):
    """Display Revenue Trends section with line chart from 2020-2024"""
    
    if not company_name:
        st.info("Please select a company to view revenue trends.")
        return
    
    # Removed debug message - chart is working properly
    
    # Get period text for section header (matches other sections)
    period_text = get_period_display_text()
    
    # Revenue Trends Section header
    st.markdown(f"""
    <div class="revenue-trends-section">
        <h2 class="section-title">Revenue Trends - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Get historical revenue data from Airtable
    from shared.airtable_connection import get_airtable_connection
    airtable = get_airtable_connection()
    
    # Fetch data for multiple years
    years = get_selected_years()
    revenue_data = {
        'Year': [],
        'Total Revenue': []
    }
    
    # Track data source for better debugging
    real_data_years = []
    sample_data_years = []
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                
                # Get total revenue data - be more flexible with field names
                total_revenue = record.get('total_revenue', 0) or record.get('Total_Revenue', 0) or record.get('totalrevenue', 0)
                
                if total_revenue and total_revenue != 0:
                    revenue_data['Year'].append(int(year))
                    revenue_data['Total Revenue'].append(total_revenue)
                    real_data_years.append(year)
                else:
                    # Check if field exists but with different name or format
                    alt_revenue = record.get('revenue', 0) or record.get('Revenue', 0) or record.get('total_rev', 0) or record.get('sales', 0)
                    if alt_revenue and alt_revenue != 0:
                        revenue_data['Year'].append(int(year))
                        revenue_data['Total Revenue'].append(alt_revenue)
                        real_data_years.append(year)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not revenue_data['Year']:
        st.info(f"📈 No revenue data available for {company_name} for the years 2020-2024.")
        return
    
    # Create the line chart using Plotly (matching screenshot style)
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Add revenue line trace (using Atlas blue)
    fig.add_trace(go.Scatter(
        x=revenue_data['Year'],
        y=revenue_data['Total Revenue'],
        mode='lines+markers',
        name='Total Revenue',
        line=dict(color='#025a9a', width=3),  # Atlas blue
        marker=dict(
            color='#025a9a',
            size=8,
            line=dict(color='white', width=2)
        ),
        showlegend=False
    ))
    
    # Update layout to match screenshot
    fig.update_layout(
        title={
            'text': 'Revenue Trend',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Revenue ($)',
        height=400,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickvals=revenue_data['Year'],
            ticktext=[str(year) for year in revenue_data['Year']],
            gridcolor='#f0f0f0'
        ),
        yaxis=dict(
            tickformat='$,.0f',
            gridcolor='#f0f0f0'
        ),
        margin=dict(
            l=80,
            r=60,
            t=60,
            b=60
        )
    )
    
    # Add value annotations on data points (matching screenshot style)
    for year, revenue in zip(revenue_data['Year'], revenue_data['Total Revenue']):
        # Format revenue value for display
        if revenue >= 1000000:
            formatted_value = f"${revenue/1000000:.1f}M"
        elif revenue >= 1000:
            formatted_value = f"${revenue/1000:.0f}K"
        else:
            formatted_value = f"${revenue:,.0f}"
        
        fig.add_annotation(
            x=year,
            y=revenue,
            text=formatted_value,
            showarrow=False,
            font=dict(color='white', size=16, family='Montserrat'),
            bgcolor='#025a9a',
            bordercolor='#025a9a',
            borderwidth=1,
            xanchor='center',
            yanchor='middle',
            yshift=20
        )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def display_income_statement_trend_graphs(company_name, income_historical_data):
    """Display Gross Profit Margin, Operating Profit Margin, and Net Profit Margin trend charts"""
    
    if not company_name:
        st.info("Please select a company to view income statement trends.")
        return
    
    # Get period text for section header (matches other sections)
    period_text = get_period_display_text()
    
    # Add section heading with same styling as other sections
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="income-statement-trends-section">
        <h2 class="section-title">Profitability Trend Graphs - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Get historical data from Airtable
    from shared.airtable_connection import get_airtable_connection
    airtable = get_airtable_connection()
    
    # Create three columns for side-by-side charts
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_gross_profit_margin_trend(company_name, airtable)
    
    with col2:
        display_operating_profit_margin_trend(company_name, airtable)
    
    with col3:
        display_net_profit_margin_trend(company_name, airtable)


def display_operating_profit_margin_trend(company_name, airtable):
    """Display Operating Profit Margin trend chart"""
    
    # Fetch operating profit margin data from income statement
    years = get_selected_years()
    opm_data = {
        'Year': [],
        'Operating Profit Margin': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                
                # Compute OPM from operating_profit / total_revenue for accuracy
                _opm_op = record.get('operating_profit', 0) or 0
                _opm_rev = record.get('total_revenue', 0) or 0
                opm = (_opm_op / _opm_rev * 100) if _opm_rev > 0 else 0
                
                opm_data['Year'].append(int(year))
                opm_data['Operating Profit Margin'].append(opm)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not opm_data['Year']:
        st.info(f"📉 No operating profit margin data available for {company_name}.")
        return
    
    # Create the line chart using Plotly (matching balance sheet trend chart style)
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Create custom hover data
    hover_data = []
    for i, year in enumerate(opm_data['Year']):
        hover_info = (
            f"<b>Year {year} - Operating Performance</b><br>" +
            f"Operating Profit Margin: <b>{opm_data['Operating Profit Margin'][i]:.1f}%</b>"
        )
        hover_data.append(hover_info)
    
    # Add the bar trace
    fig.add_trace(go.Bar(
        x=opm_data['Year'],
        y=opm_data['Operating Profit Margin'],
        name='Operating Profit Margin',
        marker_color='#025a9a',  # Atlas blue
        text=[f'{val:.0f}%' for val in opm_data['Operating Profit Margin']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        showlegend=True
    ))
    
    # Add invisible trace for baseline legend
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color='#1e7e34', width=3),
        name='Good Performance (8.0%)',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    # Update layout (matching balance sheet trend chart style)
    fig.update_layout(
        title={
            'text': 'Operating Profit Margin (%)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Operating Profit Margin (%)',
        height=350,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickvals=opm_data['Year'],
            ticktext=[str(year) for year in opm_data['Year']],
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
        margin=dict(
            l=60,
            r=60,
            t=60,
            b=100
        )
    )
    
    # Add baseline at 8% to indicate good performance threshold
    fig.add_hline(
        y=8,
        line_color="#1e7e34",  # Darker green for better visibility
        line_width=3
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def display_gross_profit_margin_trend(company_name, airtable):
    """Display Gross Profit Margin trend chart"""
    
    # Fetch gross profit margin data from income statement
    years = get_selected_years()
    gpm_data = {
        'Year': [],
        'Gross Profit Margin': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                
                # Compute GPM from gross_profit / total_revenue for accuracy
                _gpm_gross = record.get('gross_profit', 0) or 0
                _gpm_rev = record.get('total_revenue', 0) or 0
                gpm = (_gpm_gross / _gpm_rev * 100) if _gpm_rev > 0 else 0
                
                gpm_data['Year'].append(int(year))
                gpm_data['Gross Profit Margin'].append(gpm)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not gpm_data['Year']:
        st.info(f"📉 No gross profit margin data available for {company_name}.")
        return
    
    # Create the line chart using Plotly (matching balance sheet trend chart style)
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Create custom hover data
    hover_data = []
    for i, year in enumerate(gpm_data['Year']):
        hover_info = (
            f"<b>Year {year} - Profitability Analysis</b><br>" +
            f"Gross Profit Margin: <b>{gpm_data['Gross Profit Margin'][i]:.1f}%</b>"
        )
        hover_data.append(hover_info)
    
    # Add the bar trace
    fig.add_trace(go.Bar(
        x=gpm_data['Year'],
        y=gpm_data['Gross Profit Margin'],
        name='Gross Profit Margin',
        marker_color='#025a9a',  # Same Atlas blue as Operating Profit Margin
        text=[f'{val:.0f}%' for val in gpm_data['Gross Profit Margin']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        showlegend=True
    ))
    
    # Add invisible trace for baseline legend
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color='#1e7e34', width=3),
        name='Good Performance (25.0%)',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    # Update layout (matching balance sheet trend chart style)
    fig.update_layout(
        title={
            'text': 'Gross Profit Margin (%)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Gross Profit Margin (%)',
        height=350,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickvals=gpm_data['Year'],
            ticktext=[str(year) for year in gpm_data['Year']],
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
        margin=dict(
            l=60,
            r=60,
            t=60,
            b=100
        )
    )
    
    # Add baseline at 25% to indicate good performance threshold
    fig.add_hline(
        y=25,
        line_color="#1e7e34",  # Darker green for better visibility
        line_width=3
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def display_net_profit_margin_trend(company_name, airtable):
    """Display Net Profit Margin trend chart"""
    
    # Fetch net profit margin data from income statement
    years = get_selected_years()
    npm_data = {
        'Year': [],
        'Net Profit Margin': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                
                # Compute NPM from profit_before_tax_with_ppp / total_revenue (matches Excel definition)
                _npm_net_profit = record.get('profit_before_tax_with_ppp', 0) or 0
                _npm_revenue = record.get('total_revenue', 0) or 0
                npm = (_npm_net_profit / _npm_revenue * 100) if _npm_revenue > 0 else 0
                
                npm_data['Year'].append(int(year))
                npm_data['Net Profit Margin'].append(npm)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not npm_data['Year']:
        st.info(f"📉 No net profit margin data available for {company_name}.")
        return
    
    # Create the line chart using Plotly (matching balance sheet trend chart style)
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Create custom hover data
    hover_data = []
    for i, year in enumerate(npm_data['Year']):
        hover_info = (
            f"<b>Year {year} - Net Profitability</b><br>" +
            f"Net Profit Margin: <b>{npm_data['Net Profit Margin'][i]:.1f}%</b>"
        )
        hover_data.append(hover_info)
    
    # Add the bar trace
    fig.add_trace(go.Bar(
        x=npm_data['Year'],
        y=npm_data['Net Profit Margin'],
        name='Net Profit Margin',
        marker_color='#025a9a',  # Same Atlas blue as other charts
        text=[f'{val:.0f}%' for val in npm_data['Net Profit Margin']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        showlegend=True
    ))
    
    # Add invisible trace for baseline legend
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color='#1e7e34', width=3),
        name='Good Performance (6.0%)',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    # Update layout (matching balance sheet trend chart style)
    fig.update_layout(
        title={
            'text': 'Net Profit Margin (%)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Net Profit Margin (%)',
        height=350,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickvals=npm_data['Year'],
            ticktext=[str(year) for year in npm_data['Year']],
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
        margin=dict(
            l=60,
            r=60,
            t=60,
            b=100
        )
    )
    
    # Add baseline at 6% to indicate good performance threshold
    fig.add_hline(
        y=6,
        line_color="#1e7e34",  # Darker green for better visibility
        line_width=3
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    create_company_income_statement_page()
