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
from shared.year_config import get_selected_years

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def get_all_balance_sheet_data_cached(company_name, years_tuple=None):
    """Fetch all balance sheet and income statement data with caching"""
    from shared.year_config import get_default_years
    airtable = get_airtable_connection()

    # Fetch historical data for all years at once
    years = list(years_tuple) if years_tuple else get_default_years()
    balance_historical_data = {}
    income_historical_data = {}

    for year in years:
        period_filter = f"{year} Annual"
        try:
            # Get balance sheet data
            balance_data = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if balance_data and len(balance_data) > 0:
                balance_historical_data[year] = balance_data[0]  # Take first record
            else:
                balance_historical_data[year] = None

            # Get income statement data (needed for some balance sheet ratios)
            income_data = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if income_data and len(income_data) > 0:
                income_historical_data[year] = income_data[0]  # Take first record
            else:
                income_historical_data[year] = None
        except Exception:
            balance_historical_data[year] = None
            income_historical_data[year] = None

    return balance_historical_data, income_historical_data


def create_company_sidebar():
    """Create company-specific sidebar navigation"""
    with st.sidebar:
        # Get current page for active state detection
        current_page = st.session_state.get('current_page', 'company_balance_sheet')

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
                key="balance_sheet_company_selector",
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


def create_company_balance_sheet_page():
    # Require authentication
    require_auth()

    # CSS is already applied by main function - no need to duplicate

    # Initialize session state
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'balance_sheet_overview'
    if 'selected_company_name' not in st.session_state:
        st.session_state.selected_company_name = None
    
    # Create company balance sheet specific sidebar with proper error handling
    try:
        # Clear the entire sidebar first
        st.sidebar.empty()
        
        # Create company balance sheet specific sidebar
        create_company_sidebar()
    except Exception as e:
        st.sidebar.error(f"Error creating sidebar: {str(e)}")
    
    # Handle page routing to other company pages
    if st.session_state.get('current_page') == 'company_ratios':
        from company_ratios import create_company_ratios_page
        create_company_ratios_page()
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
        page_title = f"{st.session_state.selected_company_name} Balance Sheet - {period_text}"
    else:
        page_title = f"Company Balance Sheet Analysis - {period_text}"
    
    # Use centralized page header with consistent spacing
    create_page_header(
        page_title=page_title,
        show_period_selector=True
    )
    
    # Main content
    if st.session_state.selected_company_name:

        # Get cached historical data for selected years - OPTIMIZED!
        years = get_selected_years()
        with st.spinner(f"Loading {st.session_state.selected_company_name} balance sheet..."):
            balance_historical_data, income_historical_data = get_all_balance_sheet_data_cached(st.session_state.selected_company_name, tuple(years))

        # Get current year data for compatibility (2024 Annual)
        airtable = get_airtable_connection()
        balance_data = airtable.get_balance_sheet_data(st.session_state.selected_company_name)

        # Check if we have any data to display
        has_historical_data = any(balance_historical_data.values()) or any(income_historical_data.values())
        has_current_data = balance_data is not None

        if not has_historical_data and not has_current_data:
            st.info(f"⚠️ No balance sheet data found for {st.session_state.selected_company_name}.")
            st.info("💡 This might be because the data hasn't been uploaded yet or the company name doesn't match exactly.")

        # Display key numbers and balance sheet sections with historical data
        if has_current_data or has_historical_data:
            display_key_numbers_section(balance_data)
            display_balance_sheet_sections(balance_data, balance_historical_data, income_historical_data)
        else:
            # Show clear message when no real data is available
            st.info(f"📊 No balance sheet data available for {st.session_state.selected_company_name}.")
            st.info("💡 Data may not have been uploaded yet for this company.")
    
    else:
        st.info("Please select a company from the sidebar to view balance sheet analysis.")


def display_key_numbers_section(balance_data):
    """Display the key numbers section with balance sheet ratio gauges"""
    
    if balance_data:
        latest_balance = balance_data[0]  # Get most recent data
        
        # Get period text for section header
        period_text = get_period_display_text()
        
        # Key Numbers Section header
        st.markdown(f"""
        <div class="key-numbers-section">
            <h2 class="key-numbers-title">Key Numbers - {period_text}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Create four columns for the gauge charts
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Current Ratio Gauge
            current_ratio = latest_balance.get('current_ratio', 0)
            fig1 = create_gauge_chart(
                value=current_ratio,
                title="Current Ratio<br>(Liquidity)",
                min_val=0,
                max_val=8,
                threshold_red=1.5,
                threshold_yellow=2.2,
                format_type="ratio"
            )
            render_gauge_with_formula(fig1, "current_ratio")
        
        with col2:
            # Debt to Equity Gauge
            debt_to_equity = latest_balance.get('debt_to_equity', 0)
            fig2 = create_gauge_chart(
                value=debt_to_equity,
                title="Debt-to-Equity<br>(Safety)",
                min_val=0,
                max_val=3,
                threshold_red=1.1,
                threshold_yellow=1.7,
                format_type="ratio",
                reverse_colors=True
            )
            render_gauge_with_formula(fig2, "debt_to_equity")
        
        with col3:
            # Working Capital as % of Total Assets Gauge (matches ratios page)
            working_capital_pct = latest_balance.get('working_capital_pct_asset', 0)
            fig3 = create_gauge_chart(
                value=working_capital_pct * 100,
                title="Working Capital<br>% of Assets",
                min_val=0,
                max_val=50,
                threshold_red=20,
                threshold_yellow=35,
                format_type="percent"
            )
            render_gauge_with_formula(fig3, "working_capital_pct")
        
        with col4:
            # Survival Score Gauge
            survival_score = latest_balance.get('survival_score', 0)
            fig4 = create_gauge_chart(
                value=survival_score,
                title="Current<br>Survival Score",
                min_val=0,
                max_val=5,
                threshold_red=2.0,
                threshold_yellow=3.0,
                format_type="ratio"
            )
            render_gauge_with_formula(fig4, "survival_score")
        
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


def display_balance_sheet_sections(balance_data, balance_historical_data, income_historical_data):
    """Display the balance sheet graphs with tabbed interface"""
    
    # Get period text for section header
    period_text = get_period_display_text()
    
    # Balance Sheet Graphs Section
    st.markdown(f"""
    <div class="balance-sheet-graphs-section">
        <h2 class="section-title">Balance Sheet Graphs - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different graph types
    tab1, tab2, tab3 = st.tabs(["Current Assets and Liabilities", "Debt to Equity", "Survival Score"])
    
    with tab1:
        display_current_assets_liabilities_chart(st.session_state.selected_company_name)
        # Add Current Ratio trend chart below the bar chart
        if st.session_state.selected_company_name:
            from shared.airtable_connection import get_airtable_connection
            airtable = get_airtable_connection()
            years = get_selected_years()
            display_current_ratio_trend_chart(st.session_state.selected_company_name, years, airtable)
    
    with tab2:
        display_liabilities_equity_chart(st.session_state.selected_company_name)
        # Add Debt to Equity trend chart below the bar chart
        if st.session_state.selected_company_name:
            from shared.airtable_connection import get_airtable_connection
            airtable = get_airtable_connection()
            years = get_selected_years()
            display_debt_to_equity_trend_chart(st.session_state.selected_company_name, years, airtable)
    
    with tab3:
        display_survival_score_chart(st.session_state.selected_company_name)
    
    # Add CSS for the graphs section
    st.markdown("""
    <style>
    .balance-sheet-graphs-section {
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
    
    # Add Balance Sheet Trend Graphs section (always visible regardless of tab selection)
    if st.session_state.selected_company_name:
        from shared.airtable_connection import get_airtable_connection
        airtable = get_airtable_connection()
        years = get_selected_years()
        display_ratio_trend_graphs(st.session_state.selected_company_name, years, airtable)
        
        # Add Balance Sheet Trend Table at the bottom
        display_balance_sheet_trend_table(st.session_state.selected_company_name)


def display_current_assets_liabilities_chart(company_name):
    """Display Current Assets and Liabilities bar chart over time"""
    
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
        'Current Assets': [],
        'Current Liabilities': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if balance_historical and len(balance_historical) > 0:
                record = balance_historical[0]
                
                # Get current assets and liabilities data
                current_assets = record.get('total_current_assets', 0) or 0
                current_liabilities = record.get('total_current_liabilities', 0) or 0
                
                # Only add data if we have real values
                if any([current_assets, current_liabilities]):
                    chart_data['Year'].append(year)
                    chart_data['Current Assets'].append(current_assets)
                    chart_data['Current Liabilities'].append(current_liabilities)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not chart_data['Year']:
        st.info(f"📊 No current assets and liabilities data available for {company_name} for the years 2020-2024.")
        return
    
    # Create the bar chart using Plotly
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    fig = go.Figure()
    
    # Create custom hover data that shows all metrics for each year
    hover_data = []
    for i, year in enumerate(chart_data['Year']):
        hover_info = (
            f"<b>Year {year} - Balance Sheet Overview</b><br>" +
            f"Current Assets: <b>${chart_data['Current Assets'][i]:,.0f}</b><br>" +
            f"Current Liabilities: <b>${chart_data['Current Liabilities'][i]:,.0f}</b>"
        )
        hover_data.append(hover_info)
    
    # Add Current Assets bars
    fig.add_trace(go.Bar(
        name='Current Assets',
        x=chart_data['Year'],
        y=chart_data['Current Assets'],
        marker_color='#025a9a',  # Darker Atlas blue for current assets
        text=[f'${val:,.0f}' for val in chart_data['Current Assets']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Current Liabilities bars
    fig.add_trace(go.Bar(
        name='Current Liabilities', 
        x=chart_data['Year'],
        y=chart_data['Current Liabilities'],
        marker_color='#0e9cd5',  # Lighter Atlas blue for current liabilities
        text=[f'${val:,.0f}' for val in chart_data['Current Liabilities']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Current Assets and Liabilities',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Amount ($)',
        barmode='group',
        height=500,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,
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
            b=80
        )
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def display_liabilities_equity_chart(company_name):
    """Display Total Liabilities and Owner's Equity bar chart over time"""
    
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
        'Total Liabilities': [],
        'Owner\'s Equity': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if balance_historical and len(balance_historical) > 0:
                record = balance_historical[0]
                
                # Get total liabilities and owner's equity data
                total_liabilities = record.get('total_liabilities', 0) or 0
                owners_equity = record.get('owners_equity', 0) or 0
                
                # Only add data if we have real values
                if any([total_liabilities, owners_equity]):
                    chart_data['Year'].append(year)
                    chart_data['Total Liabilities'].append(total_liabilities)
                    chart_data['Owner\'s Equity'].append(owners_equity)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not chart_data['Year']:
        st.info(f"📊 No liabilities and equity data available for {company_name} for the years 2020-2024.")
        return
    
    # Create the bar chart using Plotly
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Create custom hover data that shows all metrics for each year
    hover_data = []
    owners_equity_key = "Owner's Equity"
    for i, year in enumerate(chart_data['Year']):
        hover_info = (
            f"<b>Year {year} - Debt & Equity Overview</b><br>" +
            f"Total Liabilities: <b>${chart_data['Total Liabilities'][i]:,.0f}</b><br>" +
            f"Owner's Equity: <b>${chart_data[owners_equity_key][i]:,.0f}</b>"
        )
        hover_data.append(hover_info)
    
    # Add Total Liabilities bars
    fig.add_trace(go.Bar(
        name='Total Liabilities',
        x=chart_data['Year'],
        y=chart_data['Total Liabilities'],
        marker_color='#025a9a',  # Darker Atlas blue for liabilities
        text=[f'${val:,.0f}' for val in chart_data['Total Liabilities']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Add Owner's Equity bars
    fig.add_trace(go.Bar(
        name='Owner\'s Equity', 
        x=chart_data['Year'],
        y=chart_data['Owner\'s Equity'],
        marker_color='#0e9cd5',  # Lighter Atlas blue for equity
        text=[f'${val:,.0f}' for val in chart_data['Owner\'s Equity']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Total Liabilities and Owner\'s Equity',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Amount ($)',
        barmode='group',
        height=500,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,
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
            b=80
        )
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def display_current_ratio_trend_chart(company_name, years, airtable):
    """Display Current Ratio trend line chart"""
    
    # Add some spacing before the trend chart
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Fetch current ratio data for each year
    ratio_data = {
        'Year': [],
        'Current Ratio': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if balance_historical and len(balance_historical) > 0:
                record = balance_historical[0]
                current_ratio = record.get('current_ratio', 0) or 0
                
                # Only add data if we have real values
                if current_ratio:
                    ratio_data['Year'].append(int(year))
                    ratio_data['Current Ratio'].append(current_ratio)
            # Skip years with no real data - don't add sample data
        except Exception:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not ratio_data['Year']:
        st.info(f"📉 No current ratio data available for {company_name}.")
        return
    
    # Create the line chart using Plotly
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Add the line trace
    fig.add_trace(go.Scatter(
        x=ratio_data['Year'],
        y=ratio_data['Current Ratio'],
        mode='lines+markers',
        name='Ratio',
        line=dict(color='#025a9a', width=3),
        marker=dict(
            color='#025a9a',
            size=8,
            line=dict(color='white', width=2)
        ),
        showlegend=False
    ))
    
    # Update layout to match the screenshot
    fig.update_layout(
        title={
            'text': 'Current Ratio Trend',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='',
        yaxis_title='',
        height=300,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickfont=dict(size=12, color='#666'),
            type='linear',
            tickmode='array',
            tickvals=ratio_data['Year'],
            ticktext=[str(year) for year in ratio_data['Year']]
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickfont=dict(size=12, color='#666'),
            range=[min(ratio_data['Current Ratio']) * 0.8, max(ratio_data['Current Ratio']) * 1.1] if ratio_data['Current Ratio'] else [0, 4]
        ),
        margin=dict(
            l=50,
            r=50,
            t=60,
            b=40
        )
    )
    
    # Add annotations for data point values
    for i, (year, ratio) in enumerate(zip(ratio_data['Year'], ratio_data['Current Ratio'])):
        fig.add_annotation(
            x=year,
            y=ratio,
            text=f"{ratio:.2f}",
            showarrow=False,
            font=dict(color='white', size=16, family='Montserrat'),
            bgcolor='#025a9a',
            bordercolor='#025a9a',
            borderwidth=1,
            xanchor='center',
            yanchor='middle',
            yshift=15
        )
    
    # Display the trend chart
    st.plotly_chart(fig, use_container_width=True)


def display_debt_to_equity_trend_chart(company_name, years, airtable):
    """Display Debt to Equity trend line chart"""
    
    # Add some spacing before the trend chart
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Fetch debt to equity data for each year
    ratio_data = {
        'Year': [],
        'Debt to Equity': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if balance_historical and len(balance_historical) > 0:
                record = balance_historical[0]
                debt_to_equity = record.get('debt_to_equity', 0) or 0
                
                # Only add data if we have real values
                if debt_to_equity:
                    ratio_data['Year'].append(int(year))
                    ratio_data['Debt to Equity'].append(debt_to_equity)
            # Skip years with no real data - don't add sample data
        except Exception:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not ratio_data['Year']:
        st.info(f"📉 No debt to equity ratio data available for {company_name}.")
        return
    
    # Create the line chart using Plotly
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Add the line trace
    fig.add_trace(go.Scatter(
        x=ratio_data['Year'],
        y=ratio_data['Debt to Equity'],
        mode='lines+markers',
        name='Ratio',
        line=dict(color='#025a9a', width=3),
        marker=dict(
            color='#025a9a',
            size=8,
            line=dict(color='white', width=2)
        ),
        showlegend=False
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Debt to Equity Ratio Trend',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Debt to Equity Ratio',
        height=350,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickvals=ratio_data['Year'],
            ticktext=[str(year) for year in ratio_data['Year']],
            gridcolor='#f0f0f0'
        ),
        yaxis=dict(
            tickformat='.2f',
            gridcolor='#f0f0f0'
        ),
        margin=dict(
            l=60,
            r=60,
            t=60,
            b=60
        )
    )
    
    # Add value annotations on data points
    for i, (year, ratio) in enumerate(zip(ratio_data['Year'], ratio_data['Debt to Equity'])):
        fig.add_annotation(
            x=year,
            y=ratio,
            text=f"{ratio:.2f}",
            showarrow=False,
            font=dict(color='white', size=16, family='Montserrat'),
            bgcolor='#025a9a',
            bordercolor='#025a9a',
            borderwidth=1,
            xanchor='center',
            yanchor='middle',
            yshift=15
        )
    
    # Display the trend chart
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data
def create_survival_score_figure(chart_data):
    """Create and cache the survival score Plotly figure for better performance"""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Create custom hover data that shows company survival score and industry average
    hover_data = []
    for i, year in enumerate(chart_data['Year']):
        hover_info = (
            f"<b>Year {year} - Survival Analysis</b><br>" +
            f"Company Survival Score: <b>{chart_data['Survival Score'][i]:.1f}</b><br>" +
            f"Group Average: <b>{chart_data['Group Average'][i]:.1f}</b>"
        )
        hover_data.append(hover_info)
    
    # Add Survival Score bars only (company's actual scores)
    fig.add_trace(go.Bar(
        name='Company Survival Score', 
        x=chart_data['Year'],
        y=chart_data['Survival Score'],
        marker_color='#025a9a',  # Atlas blue for survival scores
        text=[f'{val:.1f}' for val in chart_data['Survival Score']],
        textposition='inside',
        textfont=dict(color='white', size=16, family='Montserrat'),
        customdata=hover_data,
        hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>',
        showlegend=True,
        width=0.25  # Make bars even slimmer for better appearance
    ))
    
    # Add Group Average line overlay
    fig.add_trace(go.Scatter(
        name='Group Average',
        x=chart_data['Year'],
        y=chart_data['Group Average'],
        mode='lines+markers',
        line=dict(color='#4ca3e5', width=3),  # Light blue Atlas themed color
        marker=dict(
            color='#4ca3e5',
            size=8,
            line=dict(color='white', width=2)
        ),
        showlegend=True,
        hoverinfo='skip'  # Use bar chart hover for all data
    ))
    
    # Add invisible trace for baseline legend
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color='#1e7e34', width=3),
        name='Good Performance (5.0)',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Survival Score Analysis',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Survival Score',
        barmode='group',
        height=500,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,
            xanchor='center',
            x=0.5
        ),
        xaxis=dict(
            type='category',  # Force categorical to show only whole years
            tickmode='array',
            tickvals=chart_data['Year'],
            ticktext=[str(year) for year in chart_data['Year']]
        ),
        yaxis=dict(
            tickformat='.1f',
            gridcolor='#f0f0f0',
            range=[0, max(max(chart_data['Survival Score']), max(chart_data['Group Average'])) * 1.1]  # Smart range considering both company and group data
        ),
        margin=dict(
            l=60,
            r=60, 
            t=60,
            b=80
        ),
        dragmode=False,  # Disable dragging for performance
        hovermode='closest'
    )
    
    # Add baseline at 5 to indicate good performance threshold
    fig.add_hline(
        y=5,
        line_color="#1e7e34",  # Darker green for better visibility
        line_width=3
    )
    
    return fig

def display_survival_score_chart(company_name):
    """Display Survival Score and Standard Survival Score bar chart over time"""
    
    if not company_name:
        st.info("Please select a company to view the chart.")
        return
    
    # Get historical data from Airtable
    from shared.airtable_connection import get_airtable_connection
    airtable = get_airtable_connection()
    
    # Fetch data for multiple years
    selected_years = get_selected_years()
    years = selected_years
    chart_data = {
        'Year': [],
        'Survival Score': [],
        'Standard Survival Score': [],
        'Group Average': []
    }
    
    # Standard survival score values provided
    standard_scores = {'2021': 7.65, '2022': 8.07, '2023': 6.60, '2024': 4.29}
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if balance_historical and len(balance_historical) > 0:
                record = balance_historical[0]
                
                # Get survival score data
                survival_score = record.get('survival_score', 0) or 0
                
                # Only add data if we have real survival score values
                if survival_score:
                    # Calculate industry average for this year
                    all_companies_data = airtable.get_all_companies_balance_sheet_by_period(period_filter, is_admin=is_super_admin())
                    valid_scores = [company['survival_score'] for company in all_companies_data if company.get('survival_score', 0) > 0]
                    industry_avg = sum(valid_scores) / len(valid_scores) if valid_scores else 0
                    
                    chart_data['Year'].append(year)
                    chart_data['Survival Score'].append(survival_score)
                    chart_data['Standard Survival Score'].append(standard_scores.get(year, 0))
                    chart_data['Group Average'].append(industry_avg)
            # Skip years with no real data - don't add sample data
        except Exception as e:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not chart_data['Year']:
        st.info(f"📊 No survival score data available for {company_name} for the years 2021-2024.")
        return
    
    # Create cached chart figure for better performance
    fig = create_survival_score_figure(chart_data)
    
    
    # Display the chart with optimized config for better performance
    st.plotly_chart(fig, 
        use_container_width=True,
        config={'displayModeBar': False, 'staticPlot': False}
    )


def display_survival_score_trend_chart(company_name, years, airtable):
    """Display Survival Score and Standard Survival Score trend line chart"""
    
    # Add some spacing before the trend chart
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Standard survival score values provided (only for 2021-2024)
    standard_scores = {'2021': 7.65, '2022': 8.07, '2023': 6.60, '2024': 4.29}
    
    # Fetch survival score data for each year
    ratio_data = {
        'Year': [],
        'Survival Score': [],
        'Standard Survival Score': []
    }
    
    # Use all selected years
    selected_years = get_selected_years()

    for year in selected_years:
        period_filter = f"{year} Annual"
        try:
            balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if balance_historical and len(balance_historical) > 0:
                record = balance_historical[0]
                survival_score = record.get('survival_score', 0) or 0
                
                # Only add data if we have real survival score values
                if survival_score:
                    ratio_data['Year'].append(int(year))
                    ratio_data['Survival Score'].append(survival_score)
                    ratio_data['Standard Survival Score'].append(standard_scores.get(year, 0))
            # Skip years with no real data - don't add sample data
        except Exception:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not ratio_data['Year']:
        st.info(f"📉 No survival score trend data available for {company_name}.")
        return
    
    # Create the line chart using Plotly
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Add Survival Score line only (company's actual scores)
    fig.add_trace(go.Scatter(
        x=ratio_data['Year'],
        y=ratio_data['Survival Score'],
        mode='lines+markers',
        name='Survival Score',
        line=dict(color='#025a9a', width=3),  # Atlas blue for survival scores
        marker=dict(
            color='#025a9a',
            size=8,
            line=dict(color='white', width=2)
        ),
        showlegend=False
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Survival Score Trend',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='Year',
        yaxis_title='Survival Score',
        height=350,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickvals=ratio_data['Year'],
            ticktext=[str(year) for year in ratio_data['Year']],
            gridcolor='#f0f0f0'
        ),
        yaxis=dict(
            tickformat='.1f',
            gridcolor='#f0f0f0'
            # Removed fixed range to allow dynamic scaling based on actual data values
        ),
        margin=dict(
            l=60,
            r=60,
            t=60,
            b=60
        )
    )
    
    # Add value annotations for Survival Score only
    for i, (year, score) in enumerate(zip(ratio_data['Year'], ratio_data['Survival Score'])):
        fig.add_annotation(
            x=year,
            y=score,
            text=f"{score:.1f}",
            showarrow=False,
            font=dict(color='white', size=16, family='Montserrat'),
            bgcolor='#025a9a',  # Atlas blue for survival scores
            bordercolor='#025a9a',
            borderwidth=1,
            xanchor='center',
            yanchor='middle',
            yshift=15
        )
    
    # Display the trend chart
    st.plotly_chart(fig, use_container_width=True)


def display_ratio_trend_graphs(company_name, years, airtable):
    """Display Revenue per Admin Employee and Working Capital trend charts side by side"""
    
    # Get period text for section header
    period_text = get_period_display_text()
    
    # Add section heading with same styling as other sections
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ratio-trends-section">
        <h2 class="section-title">Balance Sheet Trend Graphs - {period_text}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for side-by-side charts
    col1, col2 = st.columns(2)
    
    with col1:
        display_revenue_per_admin_trend(company_name, years, airtable)
    
    with col2:
        display_working_capital_trend(company_name, years, airtable)
    
    # Add CSS for section styling
    st.markdown("""
    <style>
    .ratio-trends-section {
        margin: 1rem 0;
    }
    .section-subtitle {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 1rem;
        font-family: 'Montserrat', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)


def display_revenue_per_admin_trend(company_name, years, airtable):
    """Display Revenue per Admin Employee trend chart"""
    
    # Fetch revenue per admin employee data from income statement
    from shared.airtable_connection import get_airtable_connection
    airtable = get_airtable_connection()
    
    revenue_data = {
        'Year': [],
        'Revenue': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            income_historical = airtable.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if income_historical and len(income_historical) > 0:
                record = income_historical[0]
                revenue = record.get('rev_admin_employee', 0)
                
                # If revenue is in thousands (like 710), multiply by 1000 to get full amount
                if revenue > 0 and revenue < 10000:
                    revenue = revenue * 1000
                
                # Only add data if we have real revenue values
                if revenue:
                    revenue_data['Year'].append(int(year))
                    revenue_data['Revenue'].append(revenue)
            # Skip years with no real data - don't add sample data
        except Exception:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not revenue_data['Year']:
        st.info(f"📈 No revenue per admin data available for {company_name}.")
        return
    
    # Create the line chart
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Create custom hover data
    hover_data = []
    for i, year in enumerate(revenue_data['Year']):
        hover_info = (
            f"<b>Year {year} - Revenue Performance</b><br>" +
            f"Revenue Per Admin Employee: <b>${revenue_data['Revenue'][i]:,.0f}</b>"
        )
        hover_data.append(hover_info)
    
    fig.add_trace(go.Bar(
        x=revenue_data['Year'],
        y=revenue_data['Revenue'],
        name='Revenue per Admin Employee',
        marker_color='#025a9a',
        text=[f'${val:,.0f}' for val in revenue_data['Revenue']],
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
        name='Good Performance ($650K)',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Revenue Per Admin Employee',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        height=300,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickfont=dict(size=10, color='#666'),
            tickmode='array',
            tickvals=revenue_data['Year'],
            ticktext=[str(year) for year in revenue_data['Year']]
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickfont=dict(size=10, color='#666'),
            tickformat='$,.0f'
        ),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.2,
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=40, r=40, t=50, b=80)
    )
    
    # Add baseline at $650,000 to indicate good performance threshold
    fig.add_hline(
        y=650000,
        line_color="#1e7e34",  # Darker green for better visibility
        line_width=3
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_working_capital_trend(company_name, years, airtable):
    """Display Working Capital (% of Total Assets) trend chart"""
    
    capital_data = {
        'Year': [],
        'Working Capital %': []
    }
    
    for year in years:
        period_filter = f"{year} Annual"
        try:
            balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if balance_historical and len(balance_historical) > 0:
                record = balance_historical[0]
                working_capital_pct = record.get('working_capital_pct_asset', 0)
                
                # Convert to percentage if value is decimal (e.g., 0.43 -> 43%)
                if working_capital_pct <= 1:
                    working_capital_pct = working_capital_pct * 100
                
                # Only add data if we have real working capital percentage
                if working_capital_pct:
                    capital_data['Year'].append(int(year))
                    capital_data['Working Capital %'].append(working_capital_pct)
            # Skip years with no real data - don't add sample data
        except Exception:
            # Skip years with errors - don't add sample data
            pass
    
    # Check if we have any data to display
    if not capital_data['Year']:
        st.info(f"📉 No working capital percentage data available for {company_name}.")
        return
    
    # Create the line chart
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Create custom hover data
    hover_data = []
    for i, year in enumerate(capital_data['Year']):
        hover_info = (
            f"<b>Year {year} - Working Capital Analysis</b><br>" +
            f"Working Capital (% of Total Assets): <b>{capital_data['Working Capital %'][i]:.1f}%</b>"
        )
        hover_data.append(hover_info)
    
    fig.add_trace(go.Bar(
        x=capital_data['Year'],
        y=capital_data['Working Capital %'],
        name='Working Capital (% of Total Assets)',
        marker_color='#025a9a',
        text=[f'{val:.0f}%' for val in capital_data['Working Capital %']],
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
        name='Good Performance (45.0%)',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Working Capital (% of Total Assets)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        height=300,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickfont=dict(size=10, color='#666'),
            tickmode='array',
            tickvals=capital_data['Year'],
            ticktext=[str(year) for year in capital_data['Year']]
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickfont=dict(size=10, color='#666'),
            tickformat='.0f',
            ticksuffix='%'
        ),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.2,
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=40, r=40, t=50, b=80)
    )
    
    # Add baseline at 45% to indicate good performance threshold
    fig.add_hline(
        y=45,
        line_color="#1e7e34",  # Darker green for better visibility
        line_width=3
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_balance_sheet_trend_table(company_name):
    """Display the Balance Sheet Trend Table with percentage calculations"""
    
    if not company_name:
        st.info("Please select a company to view the balance sheet trend table.")
        return
    
    # Get period display text for dynamic heading
    period_text = get_period_display_text()
    
    # Get historical data from Airtable
    from shared.airtable_connection import get_airtable_connection
    airtable = get_airtable_connection()
    
    # Fetch data for available years (2020-2024)
    years = get_selected_years()
    table_data = {}
    
    # Initialize data structure - start with fields we know exist
    # We'll calculate total_assets from current_assets + owners_equity + total_liabilities if total_assets is missing
    balance_sheet_items = { 
        'Owner\'s Equity': {'field': 'owners_equity', 'type': 'currency'},
        'Cash and Cash Equivalents': {'field': 'cash_and_cash_equivalents', 'type': 'percent'},
        'Trade Accounts Receivable': {'field': 'trade_accounts_receivable', 'type': 'percent'},
        'Receivables': {'field': 'receivables', 'type': 'percent'},
        'Other Receivables': {'field': 'other_receivables', 'type': 'percent'},
        'Prepaid Expenses': {'field': 'prepaid_expenses', 'type': 'percent'},
        'Related Company Receivables': {'field': 'related_company_receivables', 'type': 'percent'},
        'Owner Receivables': {'field': 'owner_receivables', 'type': 'percent'},
        'Other Current Assets': {'field': 'other_current_assets', 'type': 'percent'},
        'Total Current Assets': {'field': 'total_current_assets', 'type': 'percent'},
        'Gross Fixed Assets': {'field': 'gross_fixed_assets', 'type': 'percent'},
        'Accumulated Depreciation (-)': {'field': 'accumulated_depreciation', 'type': 'percent_negative'},
        'Net Fixed Assets': {'field': 'net_fixed_assets', 'type': 'percent'},
        'Inter Company Receivables': {'field': 'inter_company_receivable', 'type': 'percent'},
        'Other Assets': {'field': 'other_assets', 'type': 'percent'},
        'TOTAL ASSETS': {'field': 'total_assets_calculated', 'type': 'currency_total'},
        'Notes Payable - Bank': {'field': 'notes_payable_bank', 'type': 'percent'},
        'Notes Payable to Owners - Current Portion': {'field': 'notes_payable_owners', 'type': 'percent'},
        'Trade Accounts Payable': {'field': 'trade_accounts_payable', 'type': 'percent'},
        'Accrued Expenses': {'field': 'accrued_expenses', 'type': 'percent'},
        'Current Portion LTD': {'field': 'current_portion_ltd', 'type': 'percent'},
        'Inter Company Payable': {'field': 'inter_company_payable', 'type': 'percent'},
        'Other Current Liabilities': {'field': 'other_current_liabilities', 'type': 'percent'},
        'Total Current Liabilities': {'field': 'total_current_liabilities', 'type': 'percent'},
        'Long-Term Debt': {'field': 'long_term_debt', 'type': 'percent'},
        'Notes Payable to Owners - LT': {'field': 'notes_payable_owners_lt', 'type': 'percent'},
        'Inter Company Debt': {'field': 'inter_company_debt', 'type': 'percent'},
        'Other LT Liabilities': {'field': 'other_lt_liabilities', 'type': 'percent'},
        'Long Term Liabilities': {'field': 'total_long_term_liabilities', 'type': 'percent'},
        'Total Liabilities': {'field': 'total_liabilities', 'type': 'percent'},
        'Owners\' Equity': {'field': 'owners_equity', 'type': 'percent'},
        'TOTAL LIABILITIES & EQUITY': {'field': 'total_assets_calculated', 'type': 'currency_total'}
    }
    
    # Initialize data storage
    for item_name in balance_sheet_items:
        table_data[item_name] = {}
    
    # Fetch data for each year
    for year in years:
        period_filter = f"{year} Annual"
        try:
            balance_historical = airtable.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_super_admin())
            if balance_historical and len(balance_historical) > 0:
                record = balance_historical[0]
                
                # Calculate total assets if not available - use balance sheet equation
                total_assets_raw = record.get('total_assets', 0) or 0
                total_liabilities = record.get('total_liabilities', 0) or 0  
                owners_equity = record.get('owners_equity', 0) or 0
                
                # Use balance sheet equation: Assets = Liabilities + Equity
                if total_assets_raw == 0 and (total_liabilities > 0 or owners_equity > 0):
                    calculated_total_assets = total_liabilities + owners_equity
                else:
                    calculated_total_assets = total_assets_raw
                
                # Store calculated total assets
                record['total_assets_calculated'] = calculated_total_assets
                
                # Store data for each line item
                for item_name, item_info in balance_sheet_items.items():
                    field_name = item_info['field']
                    value = record.get(field_name, 0) or 0
                    table_data[item_name][year] = value
            else:
                # No data for this year - store None
                for item_name in balance_sheet_items:
                    table_data[item_name][year] = None
        except Exception:
            # Error fetching data for this year - store None
            for item_name in balance_sheet_items:
                table_data[item_name][year] = None
    
    # Check if we have any real data
    has_data = False
    for item_data in table_data.values():
        for year_data in item_data.values():
            if year_data and year_data > 0:
                has_data = True
                break
        if has_data:
            break

    if not has_data:
        st.info(f"📊 No balance sheet trend data available for {company_name} for the years 2020-2024.")
        return

    # Calculate averages across all years for the company
    averages_data = {}
    valid_years = [year for year in years if any(
        table_data[item_name].get(year) and table_data[item_name][year] > 0
        for item_name in balance_sheet_items
    )]

    if valid_years:
        for item_name, item_info in balance_sheet_items.items():
            field_values = [table_data[item_name].get(year, 0) or 0 for year in valid_years]
            averages_data[item_name] = sum(field_values) / len(valid_years)

    # Calculate average percentages (as % of average total assets) for variance comparison
    avg_percentages = {}
    if averages_data:
        avg_total_assets = averages_data.get('TOTAL ASSETS', 0)
        if avg_total_assets > 0:
            for item_name, item_info in balance_sheet_items.items():
                item_type = item_info['type']
                if item_type in ['currency', 'currency_total']:
                    continue
                avg_value = averages_data.get(item_name, 0)
                if item_type == 'percent_negative':
                    avg_percentages[item_name] = (abs(avg_value) / avg_total_assets) * 100
                else:
                    avg_percentages[item_name] = (avg_value / avg_total_assets) * 100

    # Create the HTML table
    create_balance_sheet_trend_html_table(table_data, years, balance_sheet_items, period_text, averages_data, avg_percentages)


def create_balance_sheet_trend_html_table(table_data, years, balance_sheet_items, period_text, averages_data=None, avg_percentages=None):
    """Create and display the HTML table for balance sheet trend"""

    if averages_data is None:
        averages_data = {}
    if avg_percentages is None:
        avg_percentages = {}

    # Table title with dynamic period text
    st.markdown(f"""
    <div style="margin: 2rem 0 1rem 0;">
        <h3 style="color: #1a202c; font-family: 'Montserrat', sans-serif; font-weight: 600; margin-bottom: 1rem;">Balance Sheet Trend Table - {period_text}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Add color coding legend
    st.markdown("""
    <div style="margin-bottom: 15px; padding: 8px; background-color: #f8f9fa; border-radius: 5px; font-size: 0.9rem; color: #495057;">
        <strong>Color Legend:</strong>
        <span style="background-color: #d4edda; padding: 2px 6px; border-radius: 3px; margin: 0 5px;">■</span> >10% better than average
        <span style="background-color: #f8d7da; padding: 2px 6px; border-radius: 3px; margin: 0 5px;">■</span> >10% worse than average
        <span style="background-color: #e6f7ff; padding: 2px 6px; border-radius: 3px; margin: 0 5px;">■</span> within ±10% variance
    </div>
    """, unsafe_allow_html=True)

    def get_cell_color(current_pct, avg_pct, item_name):
        """Determine cell background color based on variance from average"""
        if not avg_pct or current_pct == 0 or avg_pct == 0:
            return ""
        variance = ((current_pct - avg_pct) / abs(avg_pct)) * 100

        # Liability items: lower is better
        liability_items = [
            'Notes Payable - Bank', 'Notes Payable to Owners - Current Portion',
            'Trade Accounts Payable', 'Accrued Expenses', 'Current Portion LTD',
            'Inter Company Payable', 'Other Current Liabilities', 'Total Current Liabilities',
            'Long-Term Debt', 'Notes Payable to Owners - LT', 'Inter Company Debt',
            'Other LT Liabilities', 'Long Term Liabilities', 'Total Liabilities'
        ]
        is_liability = item_name in liability_items

        if is_liability:
            if variance < -10:
                return "background-color: #d4edda;"  # Green - lower liabilities is good
            elif variance > 10:
                return "background-color: #f8d7da;"  # Red - higher liabilities is bad
        else:
            if variance > 10:
                return "background-color: #d4edda;"  # Green - higher assets/equity is good
            elif variance < -10:
                return "background-color: #f8d7da;"  # Red - lower assets/equity is bad
        return ""
    
    # Create table HTML with Atlas blue styling
    table_html = """
    <style>
    .balance-sheet-trend-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-family: 'Montserrat', sans-serif;
        border: 1px solid #025a9a;
    }
    .balance-sheet-trend-table th {
        background-color: #025a9a;
        color: white;
        padding: 10px 8px;
        text-align: center;
        font-weight: 600;
        border: 1px solid #025a9a;
    }
    .balance-sheet-trend-table td {
        padding: 8px;
        border: 1px solid #025a9a;
        text-align: center;
        background-color: white;
    }
    .balance-sheet-trend-table .row-label {
        background-color: white;
        color: #1a202c;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid #025a9a;
    }
    .balance-sheet-trend-table .total-row {
        background-color: #025a9a !important;
        color: white !important;
        font-weight: 700;
    }
    .balance-sheet-trend-table .total-row-label {
        background-color: #025a9a !important;
        color: white !important;
        font-weight: 700;
        text-align: left;
        padding-left: 15px;
        border: 1px solid #025a9a;
    }
    .balance-sheet-trend-table .subtotal-row {
        background-color: #f0f0f0 !important;
        font-weight: 600;
    }
    .balance-sheet-trend-table .subtotal-row-label {
        background-color: #f0f0f0 !important;
        color: #1a202c;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid #025a9a;
    }
    .balance-sheet-trend-table .accumulated-depreciation {
        color: #c2002f !important;
    }
    </style>
    
    <table class="balance-sheet-trend-table">
        <thead>
            <tr>
                <th style="text-align: left; padding-left: 15px;">Balance Sheet</th>
                <th style="text-align: center; color: #ffe082;">Averages</th>"""

    # Add year headers for available data only
    available_years = []
    for year in years:
        # Check if any item has data for this year
        year_has_data = False
        for item_name, year_data in table_data.items():
            if year_data.get(year) and year_data[year] > 0:
                year_has_data = True
                break
        
        if year_has_data:
            available_years.append(year)
            table_html += f"<th>{year}</th>"
    
    table_html += "</tr></thead><tbody>"
    
    # Add table rows
    for item_name, item_info in balance_sheet_items.items():
        item_type = item_info['type']
        
        # Determine row styling
        is_total = item_type == 'currency_total'
        is_subtotal = item_name in ['Total Current Assets', 'Net Fixed Assets', 'Total Current Liabilities', 'Total Liabilities', 'Owner\'s Equity']
        is_accumulated_depreciation = item_name == 'Accumulated Depreciation (-)'
        
        if is_total:
            row_class = 'total-row'
            label_class = 'total-row-label'
        elif is_subtotal:
            row_class = 'subtotal-row'
            label_class = 'subtotal-row-label'
        else:
            row_class = ''
            label_class = 'row-label'
            if is_accumulated_depreciation:
                label_class += ' accumulated-depreciation'
        
        table_html += f'<tr><td class="{label_class}">{item_name}</td>'

        # Add averages column
        avg_value = averages_data.get(item_name, 0)
        avg_total_assets = averages_data.get('TOTAL ASSETS', 0)
        if item_type == 'currency':
            formatted_avg = f"${avg_value:,.0f}" if avg_value else "-"
        elif item_type == 'currency_total':
            formatted_avg = "100%" if avg_total_assets > 0 else "-"
        elif not avg_value or avg_total_assets == 0:
            formatted_avg = "0.0%"
        elif item_type == 'percent_negative':
            percentage = (abs(avg_value) / avg_total_assets) * 100
            formatted_avg = f"({percentage:.1f}%)"
        else:
            percentage = (avg_value / avg_total_assets) * 100
            formatted_avg = f"{percentage:.1f}%"

        if is_total:
            avg_style = "background-color: #025a9a; color: white; font-weight: 700;"
        elif is_subtotal:
            avg_style = "background-color: #e6f7ff; font-weight: 600;"
        else:
            avg_style = "background-color: #e6f7ff; font-weight: 600;"
        table_html += f'<td style="padding: 8px; border: 1px solid #025a9a; text-align: center; {avg_style}">{formatted_avg}</td>'

        # Add data for each available year
        for year in available_years:
            value = table_data[item_name].get(year, 0)

            if not value or value == 0:
                formatted_value = "0.0%"
                cell_color = ""
            else:
                # Get calculated total assets for percentage calculation
                total_assets = table_data['TOTAL ASSETS'].get(year, 0)

                if item_type == 'currency':
                    formatted_value = f"${value:,.0f}"
                    cell_color = ""
                elif item_type == 'currency_total':
                    formatted_value = "100%"
                    cell_color = ""
                elif item_type == 'percent_negative':
                    if total_assets > 0:
                        percentage = (abs(value) / total_assets) * 100
                        formatted_value = f"({percentage:.1f}%)"
                        cell_color = ""  # Skip color for depreciation
                    else:
                        formatted_value = "(0.0%)"
                        cell_color = ""
                else:
                    if total_assets > 0:
                        percentage = (value / total_assets) * 100
                        formatted_value = f"{percentage:.1f}%"
                        avg_pct = avg_percentages.get(item_name, 0)
                        cell_color = get_cell_color(percentage, avg_pct, item_name)
                    else:
                        formatted_value = "0.0%"
                        cell_color = ""

            table_html += f'<td class="{row_class}" style="{cell_color}">{formatted_value}</td>'

        table_html += '</tr>'
        
        # Add spacing after certain sections
        if item_name == 'TOTAL ASSETS':
            col_count = len(available_years) + 2  # +2 for label column and averages column
            table_html += f'<tr><td colspan="{col_count}" style="border: none; padding: 5px;"></td></tr>'
    
    table_html += "</tbody></table>"
    
    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)


if __name__ == "__main__":
    create_company_balance_sheet_page()