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
from shared.page_components import create_page_header, get_period_display_text, sort_companies_by_rank
from shared.auth_utils import require_auth

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


def create_labor_cost_comparison_table(company_data, period):
    """Create and display the labor cost comparison table with companies as columns"""

    # Labor cost line items matching the Labor Cost Trend Table structure
    # Format: (Display Name, field_name, value_type)
    # value_type: 'currency' = dollar amount, 'percent' = percentage
    labor_cost_items = [
        ('Admin Labor and Expenses', 'admin_labor_cost', 'currency'),
        ('Admin Labor and Expenses (% of Revenue)', 'admin_labor_cost_pct_rev', 'percent'),
        ('Revenue Producing Labor and Expenses', 'rev_producing_labor_expenses', 'currency'),
        ('Revenue Producing Labor and Expenses (% of Revenue)', 'rev_producing_labor_expenses_pct_rev', 'percent'),
        ('Labor Ratio: Labor costs as a percentage of revenue', 'labor_ratio', 'percent'),
        ('Total Labor and Expenses', 'tot_labor_expenses', 'currency'),
        ('Total Labor and Expenses (% of Revenue)', 'tot_labor_expenses_pct_rev', 'percent')
    ]

    # Get sorted list of companies (excluding companies with no data)
    companies_with_data = []
    for company_name, data in company_data.items():
        # Check if company has at least one non-zero field
        has_data = False
        for item_name, field_name, value_type in labor_cost_items:
            value = data.get(field_name, 0) or 0
            if value != 0:
                has_data = True
                break
        if has_data:
            companies_with_data.append(company_name)

    # Sort by rank (rank 1 on the right)
    companies_with_data = sort_companies_by_rank(companies_with_data, period)

    if not companies_with_data:
        st.warning("⚠️ No companies have labor cost data for the selected period.")
        return

    # Calculate group averages for each line item
    group_averages = {}

    for item_name, field_name, value_type in labor_cost_items:
        if value_type == 'currency':
            # For dollar amounts, calculate average dollar amount
            values = [company_data[comp].get(field_name, 0) or 0
                     for comp in companies_with_data]
            valid_values = [v for v in values if v != 0]
            group_averages[item_name] = sum(valid_values) / len(valid_values) if valid_values else 0

        else:  # value_type == 'percent'
            # For percentages, calculate average percentage
            percentages = []
            for comp in companies_with_data:
                value = company_data[comp].get(field_name, 0) or 0
                if value != 0:
                    # Handle both decimal (0.15) and percentage (15) formats
                    pct = value * 100 if value < 1 else value
                    percentages.append(pct)
            group_averages[item_name] = sum(percentages) / len(percentages) if percentages else 0

    # Helper function to format values based on type
    def format_value(value, value_type):
        if value is None or value == 0:
            return '-'

        if value_type == 'currency':
            return f'${value:,.0f}'
        else:  # percent
            # Handle both decimal (0.15) and percentage (15) formats
            pct = value * 100 if value < 1 else value
            return f'{pct:.1f}%'

    # Helper function to format average values
    def format_average(avg_value, value_type):
        if avg_value == 0:
            return '-'

        if value_type == 'currency':
            return f'${avg_value:,.0f}'
        else:  # percent
            return f'{avg_value:.1f}%'

    # Display color coding
    st.markdown("""
    <div style="background-color: #f7fafc; border-left: 4px solid #025a9a; padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px;">
        <div style="display: grid; grid-template-columns: auto 1fr; gap: 0.5rem; align-items: center;">
            <div style="background-color: #c6f6d5; padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; text-align: center;">
                Green
            </div>
            <div style="color: #1a202c; font-family: 'Montserrat', sans-serif;">
                <strong>Leading Agent</strong> - Lowest percentage for labor cost metrics (lower costs are better)
            </div>
            <div style="background-color: #ffe082; padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; text-align: center;">
                Yellow
            </div>
            <div style="color: #1a202c; font-family: 'Montserrat', sans-serif;">
                <strong>Above Group Average</strong> - Labor cost percentage exceeds group average
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CSS styling
    st.markdown("""
    <style>
    .labor-cost-table-container {
        max-height: 800px;
        overflow-x: auto;
        overflow-y: auto;
        position: relative;
        margin: 1rem 0;
    }
    .labor-cost-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.0rem;
        border: 1px solid white;
    }
    .labor-cost-table thead {
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .labor-cost-table th {
        background-color: #025a9a;
        color: white;
        padding: 12px 10px;
        text-align: center;
        font-weight: 600;
        font-size: 1.1rem;
        border: 1px solid white;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .labor-cost-table th:first-child {
        text-align: left;
        min-width: 200px;
        max-width: 200px;
        position: sticky;
        left: 0;
        z-index: 30;
        background-color: #025a9a;
    }
    .labor-cost-table th.average-header {
        text-align: center;
    }
    .labor-cost-table td {
        padding: 10px 8px;
        border: 1px solid white;
        text-align: center;
        background-color: white;
        font-size: 1.0rem;
    }
    .labor-cost-table td:first-child {
        text-align: left;
        font-weight: 500;
        background-color: white;
        position: sticky;
        left: 0;
        z-index: 20;
        padding-left: 15px;
        font-size: 1.0rem;
    }
    .labor-cost-table td.average-cell {
        background-color: #e6f7ff;
        font-weight: 600;
        text-align: center;
    }
    .labor-cost-table tr.percent-row td:first-child {
        background-color: #f0f0f0;
        font-style: italic;
        padding-left: 1.5rem;
        position: sticky;
        left: 0;
        z-index: 20;
    }
    .labor-cost-table .overall-rank-row {
        background-color: #025a9a;
        font-weight: 700;
        font-size: 1.05rem;
        box-shadow: 0 2px 4px rgba(2, 90, 154, 0.3);
        border-bottom: 3px solid white;
    }
    .labor-cost-table .overall-rank-row td {
        background-color: #025a9a !important;
        color: white;
        font-weight: 700;
        font-size: 1.05rem;
        text-align: center;
    }
    .labor-cost-table .overall-rank-row td:first-child {
        background-color: #025a9a !important;
        text-align: left;
    }
    .labor-cost-table tr:hover td {
        background-color: #edf2f7;
    }
    .labor-cost-table tr:hover td.average-cell {
        background-color: #d0efff;
    }
    .labor-cost-table td.winner-cell {
        background-color: #c6f6d5 !important;
        font-weight: 700 !important;
    }
    .labor-cost-table td.above-average-cell {
        background-color: #ffe082 !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Build table HTML with container for scrolling
    table_html = '<div class="labor-cost-table-container"><table class="labor-cost-table"><thead>'

    # Add Overall Rank row at the very top (before header)
    from pages.group_pages.group_ratios import calculate_group_rankings
    rankings_data = calculate_group_rankings(period)
    overall_rankings = rankings_data.get('rankings', {}) if rankings_data else {}

    table_html += '<tr class="overall-rank-row"><td>🏆 Overall Rank</td>'
    table_html += '<td></td>'  # Empty cell for Group Average column
    for company_name in companies_with_data:
        rank = overall_rankings.get(company_name, '')
        table_html += f'<td>{rank}</td>'
    table_html += '</tr>'

    # Header row with company names
    table_html += '<tr>'
    table_html += '<th>Labor Cost Items</th>'
    table_html += '<th class="average-header" style="color: #ffe082;">Group Average</th>'
    for company_name in companies_with_data:
        table_html += f'<th>{company_name}</th>'
    table_html += '</tr></thead><tbody>'

    # Data rows
    for item_name, field_name, value_type in labor_cost_items:
        # Determine row class - percentage rows get special styling
        row_class = 'percent-row' if '(% of Revenue)' in item_name or 'percentage' in item_name.lower() else ''

        table_html += f'<tr class="{row_class}">'
        table_html += f'<td>{item_name}</td>'

        # Add Group Average column
        avg_value = group_averages[item_name]
        formatted_avg = format_average(avg_value, value_type)
        table_html += f'<td class="average-cell">{formatted_avg}</td>'

        # Define which items should be color coded (both percentage and specific currency items)
        # For labor costs, lower values are better for both currency and percentages
        colorable_currency_items = [
            'Revenue Producing Labor and Expenses',
            'Total Labor and Expenses'
        ]

        # Find the winner (lowest value = best)
        winner = None
        if value_type == 'percent':
            # For percentage items
            min_percentage = 999999
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0
                if value != 0:
                    # Handle both decimal (0.15) and percentage (15) formats
                    pct = value * 100 if value < 1 else value
                    if pct < min_percentage:
                        min_percentage = pct
                        winner = company_name
        elif value_type == 'currency' and item_name in colorable_currency_items:
            # For specific currency items (lower dollar amount = better)
            min_value = 999999999
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0
                if value != 0 and value < min_value:
                    min_value = value
                    winner = company_name

        # Add data for each company
        for company_name in companies_with_data:
            value = company_data[company_name].get(field_name, 0) or 0
            formatted_value = format_value(value, value_type)

            # Determine cell class
            cell_class = ''

            # Apply color coding to percentage items
            if value_type == 'percent' and value != 0:
                # Convert to percentage for comparison
                company_pct = value * 100 if value < 1 else value
                group_avg = group_averages.get(item_name, 0)

                # Apply winner-cell class if this is the lowest percentage (best)
                if company_name == winner:
                    cell_class = 'winner-cell'
                # Apply above-average-cell class if above group average (worse)
                elif company_pct > group_avg:
                    cell_class = 'above-average-cell'

            # Apply color coding to specific currency items
            elif value_type == 'currency' and item_name in colorable_currency_items and value != 0:
                group_avg = group_averages.get(item_name, 0)

                # Apply winner-cell class if this is the lowest dollar amount (best)
                if company_name == winner:
                    cell_class = 'winner-cell'
                # Apply above-average-cell class if above group average (worse)
                elif value > group_avg:
                    cell_class = 'above-average-cell'

            table_html += f'<td class="{cell_class}">{formatted_value}</td>'

        table_html += '</tr>'

    table_html += '</table></div>'

    # Display table
    st.markdown(table_html, unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def fetch_all_companies_labor_cost(period):
    """Fetch labor cost data for all companies for a specific period"""
    airtable = get_airtable_connection()

    # Get all companies
    from shared.airtable_connection import get_companies_cached
    companies = get_companies_cached()

    if not companies:
        return None

    company_data = {}

    for company in companies:
        company_name = company.get('name')
        if not company_name:
            continue

        # Fetch income statement data for labor cost fields
        income_data = airtable.get_income_statement_data_by_period(company_name, period)

        if income_data and len(income_data) > 0:
            company_data[company_name] = income_data[0]

    return company_data


def extract_labor_cost_data_for_export(period):
    """
    Extract labor cost data as a pandas DataFrame for Excel export.

    Returns:
        pandas.DataFrame with labor cost items as rows, companies as columns
    """
    # Reuse cached data
    company_data = fetch_all_companies_labor_cost(period)

    if not company_data:
        return None

    # Labor cost line items
    labor_cost_items = [
        ('Admin Labor and Expenses', 'admin_labor_cost', 'currency'),
        ('Admin Labor and Expenses (% of Revenue)', 'admin_labor_cost_pct_rev', 'percent'),
        ('Revenue Producing Labor and Expenses', 'rev_producing_labor_expenses', 'currency'),
        ('Revenue Producing Labor and Expenses (% of Revenue)', 'rev_producing_labor_expenses_pct_rev', 'percent'),
        ('Labor Ratio: Labor costs as a percentage of revenue', 'labor_ratio', 'percent'),
        ('Total Labor and Expenses', 'tot_labor_expenses', 'currency'),
        ('Total Labor and Expenses (% of Revenue)', 'tot_labor_expenses_pct_rev', 'percent')
    ]

    # Filter companies with data
    companies_with_data = []
    for company_name, data in company_data.items():
        has_data = False
        for item_name, field_name, value_type in labor_cost_items:
            value = data.get(field_name, 0) or 0
            if value != 0:
                has_data = True
                break
        if has_data:
            companies_with_data.append(company_name)

    if not companies_with_data:
        return None

    # Build DataFrame
    data_dict = {}

    for company in sorted(companies_with_data):
        company_values = []

        for item_name, field_name, value_type in labor_cost_items:
            value = company_data[company].get(field_name, 0) or 0

            # Format value
            if value == 0:
                formatted = '-'
            elif value_type == 'currency':
                formatted = f'${value:,.0f}'
            else:  # percent
                pct = value * 100 if value < 1 else value
                formatted = f'{pct:.1f}%'

            company_values.append(formatted)

        data_dict[company] = company_values

    # Create DataFrame
    line_item_names = [item[0] for item in labor_cost_items]
    df = pd.DataFrame(data_dict, index=line_item_names)
    df.index.name = 'Labor Cost Item'

    return df


def create_group_labor_cost_page():
    """Create group labor cost comparison page with header and period selector"""

    # Require authentication
    require_auth()

    # Initialize year selection in session state (default to most recent year)
    if 'group_labor_cost_selected_year' not in st.session_state:
        st.session_state.group_labor_cost_selected_year = 2024

    # Get current period for data fetching
    current_period = st.session_state.get('period', 'year_end')
    period_display = get_period_display_text()

    # Remove any custom selectbox styling to match homepage
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

    # Apply page header with period selector and dynamic title
    create_page_header(
        page_title=f"Group Labor Cost Comparison - {period_display}",
        subtitle=None,
        show_period_selector=True
    )

    # Add some spacing before filter section
    st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

    # Create layout: Title on left, large spacer, compact year filter aligned with table
    col_title, col_spacer, col_filter = st.columns([3, 6, 1])

    with col_title:
        # Show selected year prominently - reduced font size to fit on one line
        st.markdown(f"""
        <div style="margin: 1rem 0;">
            <h2 style="color: #1a202c; font-family: 'Montserrat', sans-serif; font-weight: 600; margin: 0; font-size: 1.5rem; white-space: nowrap;">
                {st.session_state.group_labor_cost_selected_year} Labor Cost
            </h2>
        </div>
        """, unsafe_allow_html=True)

    with col_filter:
        # Year filter - same default size as homepage selectboxes
        year_options = [2024, 2023, 2022, 2021, 2020]
        selected_year = st.selectbox(
            "**Select Year**",
            options=year_options,
            index=year_options.index(st.session_state.group_labor_cost_selected_year) if st.session_state.group_labor_cost_selected_year in year_options else 0,
            key="group_labor_cost_year_selector"
        )

        # Update session state if year changed
        if selected_year != st.session_state.group_labor_cost_selected_year:
            st.session_state.group_labor_cost_selected_year = selected_year
            st.rerun()

    # Add some spacing
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Get Airtable connection
    conn = get_airtable_connection()

    if not conn:
        st.error("❌ Unable to connect to Airtable. Please check your credentials.")
        return

    # Get selected year from session state
    selected_year = st.session_state.group_labor_cost_selected_year

    # Determine period filter based on selection and year
    if current_period == 'year_end':
        period_filter = f"{selected_year} Annual"
    else:
        period_filter = f"June {selected_year}"

    # Fetch labor cost data for all companies
    with st.spinner("Loading labor cost data..."):
        company_data = fetch_all_companies_labor_cost(period_filter)

    if not company_data:
        st.warning(f"⚠️ No labor cost data available for {selected_year} - {period_display}.")
        st.info("💡 Try selecting a different year or period.")
        return

    # Display the labor cost comparison table
    create_labor_cost_comparison_table(company_data, period_filter)


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="Group Labor Cost - BPC Dashboard",
        page_icon="📊",
        layout="wide"
    )
    create_group_labor_cost_page()
