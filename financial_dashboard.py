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
import logging

# Configure logger for auth debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import from shared modules and pages with error handling
try:
    from shared.airtable_connection import get_airtable_connection
    from shared.css_styles import apply_all_styles
    from shared.auth_utils import require_auth, logout_user, get_current_user_name, get_current_user_email, is_super_admin
    from pages.company_pages.company_ratios import create_company_ratios_page
    from pages.company_pages.company_balance_sheet import create_company_balance_sheet_page
    from pages.company_pages.company_income_statement import create_company_income_statement_page
    from pages.company_pages.company_labor_cost import create_company_labor_cost_page
    from pages.company_pages.company_actuals import create_company_actuals_page
    from pages.company_pages.company_value import create_company_value_page
    from pages.company_pages.company_cash_flow import create_company_cash_flow_page
    from pages.company_pages.company_wins_challenges import create_company_wins_challenges_page
    from pages.group_pages.group_ratios import create_group_ratios_page
    from pages.group_pages.group_balance_sheet import create_group_balance_sheet_page
    from pages.group_pages.group_income_statement import create_group_income_statement_page
    from pages.group_pages.group_cash_flow import create_group_cash_flow_page
    from pages.group_pages.group_labor_cost import create_group_labor_cost_page
    from pages.group_pages.group_value import create_group_value_page
    from pages.group_pages.group_business_mix import create_group_business_mix_page
    from pages.group_pages.group_export import create_group_export_page
    from pages.group_pages.group_custom_analysis import create_group_custom_analysis_page
    from pages.data_input.data_input_page import create_data_input_page
    from pages.data_input.wins_challenges_admin import create_wins_challenges_admin_page
    from pages.admin.user_management import create_user_management_page
    from pages.resources.glossary_page import create_glossary_page
    imports_successful = True
except ImportError as e:
    print(f"Import error: {str(e)}")  # Use print instead of st.error at module level
    imports_successful = False
    
    # Fallback imports and functions
    def get_airtable_connection():
        return None
    
    def apply_all_styles():
        st.markdown("""
        <style>
            .stApp { font-family: 'Montserrat', sans-serif; }
            .stButton > button { background: #025a9a; color: white; }
        </style>
        """, unsafe_allow_html=True)
    
    def create_company_ratios_page():
        st.error("Company ratios page unavailable - import error")
    
    def create_company_balance_sheet_page():
        st.error("Company balance sheet page unavailable - import error")
    
    def create_company_actuals_page():
        st.error("Company actuals page unavailable - import error")
    
    def create_company_value_page():
        st.error("Company value page unavailable - import error")
    
    def create_company_cash_flow_page():
        st.error("Company cash flow page unavailable - import error")
    
    def create_company_wins_challenges_page():
        st.error("Company wins & challenges page unavailable - import error")

    def create_group_ratios_page():
        st.error("Group ratios page unavailable - import error")

    def create_group_balance_sheet_page():
        st.error("Group balance sheet page unavailable - import error")

    def create_group_income_statement_page():
        st.error("Group income statement page unavailable - import error")

    def create_group_cash_flow_page():
        st.error("Group cash flow page unavailable - import error")

    def create_group_labor_cost_page():
        st.error("Group labor cost page unavailable - import error")

    def create_group_value_page():
        st.error("Group value page unavailable - import error")

    def create_group_business_mix_page():
        st.error("Group business mix page unavailable - import error")

    def create_group_export_page():
        st.error("Group export page unavailable - import error")

    def create_group_custom_analysis_page():
        st.error("Group custom analysis page unavailable - import error")

    def create_data_input_page():
        st.error("Data input page unavailable - import error")

    def create_glossary_page():
        st.error("Glossary page unavailable - import error")

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: All Streamlit commands (including st.set_page_config and st.markdown) 
# are moved inside functions to avoid execution during import

def create_sidebar_navigation():
    """Create the sidebar navigation matching the Atlas BPC layout"""
    # Clear any existing sidebar content first
    st.sidebar.empty()

    with st.sidebar:
        # CSS for active button highlighting with dark border
        current_page = st.session_state.get('current_page', 'overview')

        # Map pages to button keys for active state detection
        page_button_map = {
            'overview': 'nav_overview',
            'balance_sheet_ratios': 'ratio_balance_sheet',
            'balance_sheet_comparison': 'comp_balance_sheet',
            'income_statement_comparison': 'comp_income',
            'cash_flow_comparison': 'comp_cash_flow',
            'labor_cost_comparison': 'comp_labor',
            'value_comparison': 'comp_value',
            'business_mix_comparison': 'comp_business_mix',
            'group_export': 'nav_export',
            'custom_analysis': 'comp_custom_analysis',
            'glossary': 'nav_glossary'
        }

        active_button_key = page_button_map.get(current_page, '')

        # CSS for active button highlighting - using custom class approach
        st.markdown("""
        <style>
            /* Remove default borders from all sidebar buttons first */
            section[data-testid="stSidebar"] .stButton > button {
                border: 1px solid #e2e8f0 !important;
            }

            /* Active button will have special background */
            section[data-testid="stSidebar"] .stButton > button.active-nav-btn {
                border: 3px solid #1a202c !important;
                background-color: #edf2f7 !important;
                font-weight: 700 !important;
                box-shadow: inset 0 0 0 1px #1a202c, 0 2px 4px rgba(26, 32, 44, 0.2) !important;
            }
        </style>
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

        # Overview section
        if button_wrapper("🏠 Overview", key="nav_overview", page_id="overview", use_container_width=True):
            st.session_state.current_page = "overview"
            st.session_state.nav_tab = "group"
            st.rerun()

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
        
        # Analysis Type filter
        if 'nav_tab' not in st.session_state:
            st.session_state.nav_tab = 'group'
            
        analysis_options = ["Group", "Company"]
        current_selection = "Group" if st.session_state.nav_tab == 'group' else "Company"
        
        selected_analysis = st.selectbox(
            "**Analysis Type**",
            options=analysis_options,
            index=analysis_options.index(current_selection),
            key="analysis_type_selector"
        )
        
        # Handle analysis type changes
        if selected_analysis == "Group" and st.session_state.nav_tab != 'group':
            st.session_state.nav_tab = 'group'
            st.session_state.current_page = 'overview'
            st.rerun()
        elif selected_analysis == "Company" and st.session_state.nav_tab != 'company':
            st.session_state.nav_tab = 'company'
            # Only reset to company_ratios if we're not already on a company page
            if not st.session_state.current_page.startswith('company_'):
                st.session_state.current_page = 'company_ratios'
            st.rerun()
        
        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
        
        # Ratios section
        st.markdown("**Ratios**")
        if button_wrapper("% Group Ratios", key="ratio_balance_sheet", page_id="balance_sheet_ratios", use_container_width=True):
            st.session_state.current_page = "balance_sheet_ratios"
            st.session_state.nav_tab = "group"
            st.rerun()

        # Comparisons section
        st.markdown("**Comparisons**")

        # Determine button labels based on analysis type
        nav_tab = st.session_state.get('nav_tab', 'group')
        prefix = "Group " if nav_tab == 'group' else ""

        if button_wrapper(f"📊 {prefix}Balance Sheet", key="comp_balance_sheet", page_id="balance_sheet_comparison", use_container_width=True):
            st.session_state.current_page = "balance_sheet_comparison"
            st.session_state.nav_tab = "group"
            st.rerun()
        if button_wrapper(f"💰 {prefix}Income Stmt", key="comp_income", page_id="income_statement_comparison", use_container_width=True):
            st.session_state.current_page = "income_statement_comparison"
            st.session_state.nav_tab = "group"
            st.rerun()
        if button_wrapper(f"💸 {prefix}Cash Flow", key="comp_cash_flow", page_id="cash_flow_comparison", use_container_width=True):
            st.session_state.current_page = "cash_flow_comparison"
            st.session_state.nav_tab = "group"
            st.rerun()
        if button_wrapper(f"👥 {prefix}Labor Cost", key="comp_labor", page_id="labor_cost_comparison", use_container_width=True):
            if nav_tab == 'group':
                st.session_state.current_page = "labor_cost_comparison"
                st.session_state.nav_tab = "group"
            else:
                st.session_state.current_page = "company_labor_cost"
                st.session_state.nav_tab = "company"
            st.rerun()
        if button_wrapper(f"📈 {prefix}Value", key="comp_value", page_id="value_comparison", use_container_width=True):
            st.session_state.current_page = "value_comparison"
            st.session_state.nav_tab = "group"
            st.rerun()
        if button_wrapper(f"🏢 {prefix}Business Mix", key="comp_business_mix", page_id="business_mix_comparison", use_container_width=True):
            st.session_state.current_page = "business_mix_comparison"
            st.session_state.nav_tab = "group"
            st.rerun()
        if button_wrapper(f"📊 Export Data", key="nav_export", page_id="group_export", use_container_width=True):
            st.session_state.current_page = "group_export"
            st.session_state.nav_tab = "group"
            st.rerun()
        if button_wrapper(f"📈 Custom Analysis", key="comp_custom_analysis", page_id="custom_analysis", use_container_width=True):
            st.session_state.current_page = "custom_analysis"
            st.session_state.nav_tab = "group"
            st.rerun()

        # Resources section
        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 1rem 0;"></div>', unsafe_allow_html=True)
        st.markdown("**Resources**")
        if button_wrapper("📚 Glossary", key="nav_glossary", page_id="glossary", use_container_width=True):
            st.session_state.current_page = "glossary"
            st.rerun()

        # Admin section - Compact layout at bottom with purple styling
        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 1rem 0;"></div>', unsafe_allow_html=True)
        st.markdown("**Admin**")

        st.markdown("""
        <style>
            /* Purple admin button styling */
            div[data-testid="column"] button[key="admin_upload_sidebar"],
            div[data-testid="column"] button[key="admin_wins_sidebar"] {
                background: linear-gradient(135deg, #9f7aea 0%, #805ad5 100%) !important;
                color: white !important;
                border: none !important;
                font-weight: 600 !important;
                font-size: 0.8rem !important;
                padding: 0.4rem 0.3rem !important;
                border-radius: 6px !important;
                box-shadow: 0 2px 4px rgba(128, 90, 213, 0.3) !important;
            }

            div[data-testid="column"] button[key="admin_upload_sidebar"]:hover,
            div[data-testid="column"] button[key="admin_wins_sidebar"]:hover {
                background: linear-gradient(135deg, #805ad5 0%, #9f7aea 100%) !important;
                transform: translateY(-1px) !important;
            }
        </style>
        """, unsafe_allow_html=True)

        # Admin buttons - different layout based on role
        if is_super_admin():
            # Super admins see both buttons in 2-column layout
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📤 Upload", key="admin_upload_sidebar", use_container_width=True):
                    st.session_state.current_page = "data_input"
                    st.rerun()
            with col2:
                if st.button("🏆 W&C", key="admin_wins_sidebar", use_container_width=True):
                    st.session_state.current_page = "wins_challenges_admin"
                    st.rerun()
        else:
            # Company users only see Upload button (full width)
            if st.button("📤 Upload Data", key="admin_upload_sidebar", use_container_width=True):
                st.session_state.current_page = "data_input"
                st.rerun()

        # User Management button (only for super admins)
        if is_super_admin():
            st.markdown("""
            <style>
                /* User Management button styling */
                div[data-testid="column"] button[key="admin_user_management"] {
                    background: linear-gradient(135deg, #9f7aea 0%, #805ad5 100%) !important;
                    color: white !important;
                    border: none !important;
                    font-weight: 600 !important;
                    font-size: 0.9rem !important;
                    padding: 0.5rem !important;
                    border-radius: 6px !important;
                    box-shadow: 0 2px 4px rgba(128, 90, 213, 0.3) !important;
                    margin-top: 0.3rem !important;
                }

                div[data-testid="column"] button[key="admin_user_management"]:hover {
                    background: linear-gradient(135deg, #805ad5 0%, #9f7aea 100%) !important;
                    transform: translateY(-1px) !important;
                }
            </style>
            """, unsafe_allow_html=True)

            if st.button("👥 User Management", key="admin_user_management", use_container_width=True):
                st.session_state.current_page = "user_management"
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
            logger.warning(f"User data inconsistency detected - Name: {user_name}, Email: {user_email}")
            from shared.auth_utils import clear_session, clear_cookies
            clear_session()
            clear_cookies()
            st.rerun()

        # If we have both, verify user_id matches between session.user and session.user_profile
        if user_name and user_email and st.session_state.user and st.session_state.user_profile:
            session_user_id = st.session_state.user.id
            profile_user_id = st.session_state.user_profile.get('id')

            if session_user_id != profile_user_id:
                logger.error(f"CRITICAL: User ID mismatch - Session: {session_user_id}, Profile: {profile_user_id}")
                from shared.auth_utils import clear_session, clear_cookies
                clear_session()
                clear_cookies()
                st.rerun()

        # Log sidebar display for debugging
        if user_name and user_email:
            role = st.session_state.user_profile.get('role') if st.session_state.user_profile else None
            logger.debug(f"Sidebar display - Name: {user_name}, Email: {user_email}, Role: {role}")

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

# Navigation functions moved to sidebar - main navigation tabs removed

def create_period_selector():
    """Create period selector for homepage matching company ratios page style"""
    # Initialize period if not exists
    if 'period' not in st.session_state:
        st.session_state.period = 'year_end'
    
    # Debug: Show current period state
    # st.write(f"Current period: {st.session_state.period}")
    
    # Add CSS for period selector matching company ratios page
    st.markdown("""
    <style>
        .period-selector {
            display: flex;
            gap: 0.3rem;
            margin: 0.5rem 0;
            justify-content: flex-start;
        }
        
        .period-btn {
            padding: 0.4rem 0.8rem;
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            font-size: 0.9rem;
            cursor: pointer;
            color: #4a5568;
            font-weight: 500;
            font-family: 'Montserrat', sans-serif;
            transition: all 0.2s ease;
        }
        
        .period-btn.active {
            background: #025a9a;
            color: white;
            border-color: #025a9a;
        }
        
        .period-btn:hover {
            background: #e2e8f0;
            border-color: #cbd5e0;
        }
        
        .period-btn.active:hover {
            background: #025a9a;
            border-color: #025a9a;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Add CSS to completely hide functional buttons  
    st.markdown("""
    <style>
        /* Completely hide functional buttons that follow period selector */
        .period-selector + div[data-testid="element-container"],
        .period-selector ~ div[data-testid="element-container"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create period selector using HTML divs exactly like company ratios page
    active_year = "active" if st.session_state.period == 'year_end' else ""
    active_june = "active" if st.session_state.period == 'june_end' else ""
    
    # Override button styling to match the CSS divs
    st.markdown("""
    <style>
        .period-selector-buttons .stButton > button {
            background: #f7fafc !important;
            color: #4a5568 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 4px !important;
            padding: 0.4rem 0.8rem !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            font-family: 'Montserrat', sans-serif !important;
            transition: all 0.2s ease !important;
            white-space: nowrap !important;
            width: auto !important;
            min-width: auto !important;
            height: auto !important;
            box-shadow: none !important;
            transform: none !important;
        }
        
        /* Ensure non-active buttons stay with default styling */
        .period-selector-buttons div:not(.period-active-btn) .stButton > button {
            background: #f7fafc !important;
            color: #4a5568 !important;
            border: 1px solid #e2e8f0 !important;
        }
        
        .period-selector-buttons .stButton > button:hover {
            background: #e2e8f0 !important;
            border-color: #cbd5e0 !important;
            transform: none !important;
            box-shadow: none !important;
        }
        
        /* Active period button styling - more specific selector */
        .period-selector-buttons .period-active-btn .stButton > button {
            background: #025a9a !important;
            color: white !important;
            border: 1px solid #025a9a !important;
            box-shadow: none !important;
            transform: none !important;
        }
        
        .period-active-btn .stButton > button:hover {
            background: #025a9a !important;
            border-color: #025a9a !important;
            transform: none !important;
            box-shadow: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Set active states for period buttons  
    active_year = "active" if st.session_state.period == 'year_end' else ""
    active_june = "active" if st.session_state.period == 'june_end' else ""
    
    # Create period selector using HTML divs - display only
    st.markdown(f"""
    <div class="period-selector" style="margin-left: 0; text-align: left;">
        <div class="period-btn {active_year}">Year End</div>
        <div class="period-btn {active_june}">Mid Year</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create functional buttons with much simpler approach - using forms
    """with st.form(key="period_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            year_clicked = st.form_submit_button("Year End")
        with col2:
            june_clicked = st.form_submit_button("Mid Year")
        
        if year_clicked:
            st.session_state.period = "year_end"
            st.rerun()
        if june_clicked:
            st.session_state.period = "june_end"
            st.rerun()"""

def create_top_navigation_header():
    """Create red banner with centered title that appears on every page"""
    # Add CSS for the red banner
    st.markdown("""
    <style>
        .header-banner {
            background: linear-gradient(135deg, #c2002f 0%, #a50026 100%);
            color: white;
            text-align: center;
            padding: 1rem 0;
            margin: -1rem -1rem 1rem -1rem;
            width: calc(100% + 2rem);
            position: relative;
            left: -1rem;
            box-shadow: 0 2px 4px rgba(194, 0, 47, 0.3);
        }
        
        .banner-title {
            font-size: 1.8rem;
            font-weight: 700;
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            letter-spacing: 0.5px;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }
        
        @media (max-width: 768px) {
            .banner-title {
                font-size: 1.4rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the red banner
    st.markdown("""
    <div class="header-banner">
        <div class="banner-title">BPC 1 Financial Dashboard</div>
    </div>
    """, unsafe_allow_html=True)


def create_group_overview_page(companies):
    """Create the main Group Overview page"""

    # Import centralized page components
    from shared.page_components import create_page_header
    from pages.group_pages.group_ratios import calculate_group_rankings

    # Use centralized page header with consistent spacing
    create_page_header(
        page_title="Group Overview",
        subtitle="Welcome to the 2025 BPC 1 Financial Analysis!",
        show_period_selector=True
    )

    # Instructions - larger font for seniors readability
    st.markdown("""
    <div class="instructions" style="margin: 0.2rem 0 0.4rem 0; font-size: 1.4rem; line-height: 1.5;">
        <ul>
            <li style="margin-bottom: 0.5rem;"><strong>Use the Analysis Type filter in the sidebar to switch between Group and Company data.</strong></li>
            <li style="margin-bottom: 0.5rem;"><strong>Use the navigation options in the sidebar to explore different data types.</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Group Rankings section
    st.markdown('<div class="rankings-section">', unsafe_allow_html=True)
    st.markdown('<div class="rankings-title">Group Rankings</div>', unsafe_allow_html=True)

    # Add compact table styling for homepage
    st.markdown("""
    <style>
        .homepage-table-container {
            display: flex;
            justify-content: center;
            margin: 1rem auto;
            width: 100%;
        }

        .homepage-table-container .rankings-table {
            width: 100% !important;
            border-collapse: collapse !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: 0.9rem !important;
            background: white !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }

        .homepage-table-container .rankings-table th {
            background: #025a9a !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 0.6rem 0.8rem !important;
            text-align: left !important;
            border: none !important;
        }

        .homepage-table-container .rankings-table td {
            padding: 0.5rem 0.8rem !important;
            border-bottom: 1px solid #e2e8f0 !important;
            color: #4a5568 !important;
        }

        .homepage-table-container .rankings-table tbody tr:nth-child(even) {
            background-color: #f7fafc !important;
        }

        .homepage-table-container .rankings-table tbody tr:hover {
            background-color: #edf2f7 !important;
        }

        .homepage-table-container .rankings-table tbody tr:last-child td {
            border-bottom: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Hardcoded rankings from 2024 Annual data (avoids slow API calls on homepage load)
    hardcoded_rankings = [
        (1, 'Ace Worldwide', 34.0),
        (2, 'Smith Dray', 35.0),
        (3, 'Apex', 48.5),
        (4, 'Guardian', 51.0),
        (5, 'Ace Relo', 56.0),
        (6, "Alexander's", 58.0),
        (7, 'Weleski', 65.5),
        (8, 'InterWest', 72.0),
    ]

    table_html = '<div class="homepage-table-container"><table class="rankings-table"><thead><tr><th style="text-align: center;">Rank</th><th style="text-align: center;">Company</th><th style="text-align: center;">Total Score</th></tr></thead><tbody>'

    for rank, company_name, score in hardcoded_rankings:
        row_bg = "background-color: #f7fafc;" if rank % 2 == 0 else ""
        table_html += f'<tr style="{row_bg}"><td style="text-align: center; font-weight: 600;"><strong>#{rank}</strong></td><td style="text-align: center; font-weight: 600;"><strong>{company_name}</strong></td><td style="text-align: center;">{score:.1f}</td></tr>'

    table_html += '</tbody></table></div>'
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # Close rankings-section

def create_ratios_page(ratio_type):
    """Create ratio analysis pages"""
    # Import centralized page components
    from shared.page_components import create_page_header
    
    # Use centralized page header
    create_page_header(
        page_title=f'Ratios - {ratio_type.replace("_", " ").title()}',
        show_period_selector=True
    )
    
    st.info(f"🚧 {ratio_type.replace('_', ' ').title()} ratios analysis coming soon!")
    
    # Placeholder content
    st.markdown(f"""
    **Planned Features for {ratio_type.replace('_', ' ').title()}:**
    - Ratio calculations and trends
    - Company comparisons
    - Interactive charts and visualizations
    """)

def create_comparison_page(comparison_type):
    """Create comparison pages"""
    # Import centralized page components
    from shared.page_components import create_page_header
    
    # Use centralized page header
    create_page_header(
        page_title=f'Comparisons - {comparison_type.replace("_", " ").title()}',
        show_period_selector=True
    )
    
    st.info(f"🚧 {comparison_type.replace('_', ' ').title()} comparisons coming soon!")
    
    # Placeholder content
    st.markdown(f"""
    **Planned Features for {comparison_type.replace('_', ' ').title()}:**
    - Side-by-side company comparisons
    - Historical trend analysis
    - Performance rankings
    - Export capabilities
    """)

def main():
    # Page configuration - MUST be first Streamlit command
    st.set_page_config(
        page_title="BPC 1 - Financial Dashboard",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Hide default Streamlit page navigation (we use custom routing)
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # ========================================================================
    # AUTHENTICATION GATE - Require user to be logged in
    # ========================================================================
    # This MUST be called after st.set_page_config() but before any other content
    # If user is not logged in, this will show the login page and stop execution
    require_auth()

    # Apply custom CSS styling with error handling
    try:
        apply_all_styles()
    except Exception as e:
        st.error(f"CSS loading error: {str(e)}")
        # Fallback to basic styling
        st.markdown("""
        <style>
            .stApp { font-family: 'Montserrat', sans-serif; }
            .stButton > button {
                background: #025a9a;
                color: white;
                border-radius: 6px;
            }
        </style>
        """, unsafe_allow_html=True)

    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'overview'
    if 'nav_tab' not in st.session_state:
        st.session_state.nav_tab = 'group'
    if 'period' not in st.session_state:
        st.session_state.period = 'year_end'
    
    # Special Pages - Handle these FIRST before any sidebar creation
    # Data Input page handles its own minimal sidebar
    if st.session_state.current_page == 'data_input':
        try:
            create_data_input_page()
            return  # Exit early to prevent sidebar creation
        except Exception as e:
            st.error(f"Data input page error: {str(e)}")
            # Fall back to overview page
            st.session_state.current_page = 'overview'

    # Wins & Challenges Admin page handles its own minimal sidebar
    if st.session_state.current_page == 'wins_challenges_admin':
        try:
            create_wins_challenges_admin_page()
            return  # Exit early to prevent sidebar creation
        except Exception as e:
            st.error(f"Wins & Challenges admin page error: {str(e)}")
            # Fall back to overview page
            st.session_state.current_page = 'overview'

    # User Management Admin page handles its own minimal sidebar
    if st.session_state.current_page == 'user_management':
        try:
            create_user_management_page()
            return  # Exit early to prevent sidebar creation
        except Exception as e:
            st.error(f"User Management page error: {str(e)}")
            # Fall back to overview page
            st.session_state.current_page = 'overview'

    # Company Analysis Pages - Handle these FIRST before any sidebar creation
    if st.session_state.current_page == 'company_ratios':
        try:
            create_company_ratios_page()
            return  # Exit early to prevent sidebar creation
        except Exception as e:
            st.error(f"Company ratios page error: {str(e)}")
            # Fall back to overview page
            st.session_state.current_page = 'overview'

    if st.session_state.current_page == 'company_balance_sheet':
        try:
            create_company_balance_sheet_page()
            return  # Exit early to prevent sidebar creation
        except Exception as e:
            st.error(f"Company balance sheet page error: {str(e)}")
            # Fall back to overview page
            st.session_state.current_page = 'overview'
    
    # Initialize Airtable connection using shared connection with error handling
    try:
        airtable = get_airtable_connection()
    except Exception as e:
        st.error(f"Airtable connection error: {str(e)}")
        # Use a dummy connection for demo purposes
        airtable = None
    
    # Get companies data with session-level caching for better performance
    try:
        from shared.airtable_connection import get_companies_cached
        companies = get_companies_cached() if airtable else []
    except Exception as e:
        st.error(f"Error fetching companies: {str(e)}")
        companies = [{"name": "Demo Company", "id": "demo"}]  # Fallback data
    
    # Determine if we should create main sidebar (for group pages) or let pages handle their own
    company_pages = ['company_ratios', 'company_balance_sheet', 'company_income_statement', 'company_labor_cost', 'company_actuals', 'company_value', 'company_cash_flow', 'company_wins_challenges']
    data_input_pages = ['data_input']  # Pages that handle their own sidebar

    # Create main sidebar navigation for all pages EXCEPT company-specific ones and data input
    if st.session_state.current_page not in company_pages and st.session_state.current_page not in data_input_pages:
        try:
            create_sidebar_navigation()
        except Exception as e:
            st.error(f"Sidebar creation error: {str(e)}")
            # Create a basic fallback sidebar
            with st.sidebar:
                st.markdown("### Navigation")
                if st.button("🏠 Overview"):
                    st.session_state.current_page = "overview"
                    st.rerun()
    
    # Main content area - route to appropriate page
    if st.session_state.current_page == 'overview':
        # If in company mode, redirect to company ratios (no company overview page exists)
        if st.session_state.nav_tab == 'company':
            st.session_state.current_page = 'company_ratios'
            st.rerun()
        else:
            create_group_overview_page(companies)
    
    # Company-specific pages (they handle their own sidebars)
    elif st.session_state.current_page == 'company_ratios':
        create_company_ratios_page()
    elif st.session_state.current_page == 'company_balance_sheet':
        create_company_balance_sheet_page()
    elif st.session_state.current_page == 'company_income_statement':
        create_company_income_statement_page()
    elif st.session_state.current_page == 'company_labor_cost':
        create_company_labor_cost_page()
    
    elif st.session_state.current_page == 'company_actuals':
        create_company_actuals_page()
    
    elif st.session_state.current_page == 'company_value':
        create_company_value_page()
    
    elif st.session_state.current_page == 'company_cash_flow':
        create_company_cash_flow_page()
    
    elif st.session_state.current_page == 'company_wins_challenges':
        create_company_wins_challenges_page()
    
    # Ratios pages
    elif st.session_state.current_page == 'balance_sheet_ratios':
        create_group_ratios_page()
    elif st.session_state.current_page == 'income_statement_ratios':
        create_ratios_page('income_statement')
    elif st.session_state.current_page == 'cash_flow_ratios':
        create_ratios_page('cash_flow')
    
    # Comparison pages
    elif st.session_state.current_page == 'balance_sheet_comparison':
        create_group_balance_sheet_page()
    elif st.session_state.current_page == 'income_statement_comparison':
        create_group_income_statement_page()
    elif st.session_state.current_page == 'cash_flow_comparison':
        create_group_cash_flow_page()
    elif st.session_state.current_page == 'labor_cost_comparison':
        create_group_labor_cost_page()
    elif st.session_state.current_page == 'value_comparison':
        create_group_value_page()
    elif st.session_state.current_page == 'business_mix_comparison':
        create_group_business_mix_page()
    elif st.session_state.current_page == 'group_export':
        create_group_export_page()
    elif st.session_state.current_page == 'custom_analysis':
        create_group_custom_analysis_page()

    # Data Input page
    elif st.session_state.current_page == 'data_input':
        create_data_input_page()

    # Glossary page
    elif st.session_state.current_page == 'glossary':
        create_glossary_page()

if __name__ == "__main__":
    main()