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
from shared.auth_utils import require_auth, is_super_admin
from shared.year_config import CURRENT_YEAR

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


def create_value_trends_comparison_table(company_data, period):
    """Create and display the value trends comparison table with companies as columns"""

    # Value trends line items matching the Value Trend Table structure
    # Format: (Display Name, field_name, value_type, is_calculated)
    # value_type: 'currency' = dollar amount, 'ratio' = decimal ratio, 'rank' = rank number
    # is_calculated: True if field needs to be calculated from other fields
    value_items = [
        ('EBITDA (000)', 'ebitda', 'currency', False),
        ('3 x EBITDA (000)', '3x_ebitda', 'currency', True),  # Calculated: EBITDA * 3
        ('Interest Bearing Debt (000)', 'interest_bearing_debt', 'currency', False),
        ('Company Value (000)', 'company_value', 'currency', True),  # Calculated: 3x EBITDA - Debt
        ('Company Value Rank', 'company_value_rank', 'rank', True),  # Calculated: Rank based on Company Value
        ('Equity (000)', 'owners_equity', 'currency', False),
        ('Value to Equity', 'value_to_equity', 'ratio', True)  # Calculated: Company Value / Equity
    ]

    # Get sorted list of companies (excluding companies with no data)
    companies_with_data = []
    for company_name, data in company_data.items():
        # Check if company has at least one non-zero field
        has_data = False
        for item_name, field_name, value_type, is_calculated in value_items:
            if not is_calculated:
                value = data.get(field_name, 0) or 0
                if value != 0:
                    has_data = True
                    break
        if has_data:
            companies_with_data.append(company_name)

    # Sort by rank (rank 1 on the right)
    companies_with_data = sort_companies_by_rank(companies_with_data, period)

    if not companies_with_data:
        st.warning("⚠️ No companies have value data for the selected period.")
        return

    # Calculate derived fields for each company
    for company_name in companies_with_data:
        data = company_data[company_name]

        # Convert equity from dollars to thousands to match other (000) fields
        equity = data.get('owners_equity', 0) or 0
        data['owners_equity'] = equity / 1000 if equity != 0 else 0

        # Calculate 3 x EBITDA
        ebitda = data.get('ebitda', 0) or 0
        data['3x_ebitda'] = ebitda * 3

        # Calculate Company Value (3 x EBITDA - Interest Bearing Debt)
        interest_bearing_debt = data.get('interest_bearing_debt', 0) or 0
        data['company_value'] = data['3x_ebitda'] - interest_bearing_debt

        # Calculate Value to Equity ratio
        # Now both company_value and owners_equity are in thousands (000) notation
        equity_in_thousands = data['owners_equity']
        if equity_in_thousands != 0:
            data['value_to_equity'] = data['company_value'] / equity_in_thousands
        else:
            data['value_to_equity'] = 0

    # Calculate Company Value Rankings (higher value = lower rank number)
    # Create list of (company_name, company_value) tuples
    company_values = [(comp, company_data[comp].get('company_value', 0) or 0)
                      for comp in companies_with_data]

    # Sort by company value in descending order (highest first)
    company_values.sort(key=lambda x: x[1], reverse=True)

    # Assign ranks (1 = highest value)
    for rank, (company_name, _) in enumerate(company_values, start=1):
        company_data[company_name]['company_value_rank'] = rank

    # Calculate group averages for each line item
    group_averages = {}

    for item_name, field_name, value_type, is_calculated in value_items:
        if value_type == 'rank':
            # For Company Value Rank, don't show average (not meaningful)
            if item_name == 'Company Value Rank':
                group_averages[item_name] = 0  # Will display as '-'
            else:
                # For other ranks, calculate average rank
                ranks = [company_data[comp].get(field_name, 0) or 0
                        for comp in companies_with_data]
                valid_ranks = [r for r in ranks if r != 0]
                group_averages[item_name] = sum(valid_ranks) / len(valid_ranks) if valid_ranks else 0

        elif value_type == 'ratio':
            # For ratios, calculate average ratio
            ratios = [company_data[comp].get(field_name, 0) or 0
                     for comp in companies_with_data]
            valid_ratios = [r for r in ratios if r != 0]
            group_averages[item_name] = sum(valid_ratios) / len(valid_ratios) if valid_ratios else 0

        else:  # value_type == 'currency'
            # For dollar amounts, calculate average dollar amount
            values = [company_data[comp].get(field_name, 0) or 0
                     for comp in companies_with_data]
            valid_values = [v for v in values if v != 0]
            group_averages[item_name] = sum(valid_values) / len(valid_values) if valid_values else 0

    # Helper function to format values based on type
    def format_value(value, value_type, item_name=''):
        if value is None or value == 0:
            return '-'

        if value_type == 'currency':
            # Format with parentheses for negative values
            if value < 0:
                return f'$({abs(value):,.0f})'
            else:
                return f'${value:,.0f}'
        elif value_type == 'ratio':
            # Format as decimal ratio (e.g., 1.5)
            return f'{value:.1f}'
        else:  # rank
            if value == 0:
                return '-'
            return str(int(value))

    # Helper function to format average values
    def format_average(avg_value, value_type, item_name=''):
        if avg_value == 0:
            return '-'

        if value_type == 'currency':
            if avg_value < 0:
                return f'$({abs(avg_value):,.0f})'
            else:
                return f'${avg_value:,.0f}'
        elif value_type == 'ratio':
            return f'{avg_value:.1f}'
        else:  # rank
            return f'{avg_value:.1f}'

    # Display color coding
    st.markdown("""
    <div style="background-color: #f7fafc; border-left: 4px solid #025a9a; padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px;">
        <div style="display: grid; grid-template-columns: auto 1fr; gap: 0.5rem; align-items: center;">
            <div style="background-color: #c6f6d5; padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; text-align: center;">
                Green
            </div>
            <div style="color: #1a202c; font-family: 'Montserrat', sans-serif;">
                <strong>Leading Agent</strong> - Highest value for EBITDA, Company Value, Equity, Value to Equity; Lowest for Interest Bearing Debt and Rank
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CSS styling
    st.markdown("""
    <style>
    .value-trends-table-container {
        max-height: 800px;
        overflow-x: auto;
        overflow-y: auto;
        position: relative;
        margin: 1rem 0;
    }
    .value-trends-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.0rem;
        border: 1px solid white;
    }
    .value-trends-table thead {
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .value-trends-table th {
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
    .value-trends-table th:first-child {
        text-align: left;
        min-width: 200px;
        max-width: 200px;
        position: sticky;
        left: 0;
        z-index: 30;
        background-color: #025a9a;
    }
    .value-trends-table th.average-header {
        text-align: center;
    }
    .value-trends-table td {
        padding: 10px 8px;
        border: 1px solid white;
        text-align: center;
        background-color: white;
        font-size: 1.0rem;
    }
    .value-trends-table td:first-child {
        text-align: left;
        font-weight: 500;
        background-color: white;
        position: sticky;
        left: 0;
        z-index: 20;
        padding-left: 15px;
        font-size: 1.0rem;
    }
    .value-trends-table td.average-cell {
        background-color: #e6f7ff;
        font-weight: 600;
        text-align: center;
    }
    .value-trends-table tr.rank-row td {
        background-color: #f0f0f0;
        font-weight: 600;
    }
    .value-trends-table tr.rank-row td:first-child {
        background-color: #f0f0f0;
    }
    .value-trends-table tr.rank-row td.average-cell {
        background-color: #d0e8f5;
        font-weight: 700;
    }
    .value-trends-table .overall-rank-row {
        background-color: #025a9a;
        font-weight: 700;
        font-size: 1.05rem;
        box-shadow: 0 2px 4px rgba(2, 90, 154, 0.3);
    }
    .value-trends-table .overall-rank-row td {
        background-color: #025a9a !important;
        color: white;
        font-weight: 700;
        font-size: 1.05rem;
        text-align: center;
    }
    .value-trends-table .overall-rank-row td:first-child {
        background-color: #025a9a !important;
        text-align: left;
    }
    .value-trends-table tr:hover td {
        box-shadow: inset 0 2px 0 #025a9a, inset 0 -2px 0 #025a9a;
    }
    .value-trends-table td.winner-cell {
        background-color: #c6f6d5 !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Build table HTML with container for scrolling
    table_html = '<div class="value-trends-table-container"><table class="value-trends-table"><thead>'

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
    table_html += '<th>Value Trends Items</th>'
    table_html += '<th class="average-header" style="color: #ffe082;">Group Average</th>'
    for company_name in companies_with_data:
        table_html += f'<th>{company_name}</th>'
    table_html += '</tr></thead><tbody>'

    # Define items where higher is better
    high_is_good_items = ['EBITDA (000)', '3 x EBITDA (000)', 'Company Value (000)', 'Equity (000)', 'Value to Equity']

    # Define items where lower is better
    low_is_good_items = ['Interest Bearing Debt (000)']

    # Data rows
    for item_name, field_name, value_type, is_calculated in value_items:
        # Determine row class - rank rows get special styling
        row_class = 'rank-row' if value_type == 'rank' else ''

        table_html += f'<tr class="{row_class}">'
        table_html += f'<td>{item_name}</td>'

        # Add Group Average column
        avg_value = group_averages[item_name]
        formatted_avg = format_average(avg_value, value_type, item_name)
        table_html += f'<td class="average-cell">{formatted_avg}</td>'

        # Find winner for this row
        winner = None
        if item_name in high_is_good_items:
            # Higher is better - find max
            max_value = -999999
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0
                if value > max_value:
                    max_value = value
                    winner = company_name
        elif item_name in low_is_good_items:
            # Lower is better - find min
            min_value = 999999
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0
                if value != 0 and value < min_value:
                    min_value = value
                    winner = company_name

        # Add data for each company
        for company_name in companies_with_data:
            value = company_data[company_name].get(field_name, 0) or 0
            formatted_value = format_value(value, value_type, item_name)

            # Determine cell class
            cell_class = ''

            # Apply color coding
            if item_name in high_is_good_items:
                # Green for highest
                if company_name == winner:
                    cell_class = 'winner-cell'

            elif item_name in low_is_good_items:
                # Green for lowest
                if company_name == winner and value != 0:
                    cell_class = 'winner-cell'

            table_html += f'<td class="{cell_class}">{formatted_value}</td>'

        table_html += '</tr>'

    table_html += '</table></div>'

    # Display table
    st.markdown(table_html, unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def fetch_all_companies_value_trends(period):
    """Fetch value trends data for all companies for a specific period"""
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

        # Fetch income statement data for EBITDA and ranks
        income_data = airtable.get_income_statement_data_by_period(company_name, period, is_admin=is_super_admin())

        # Fetch balance sheet data for Interest Bearing Debt and Equity
        balance_data = airtable.get_balance_sheet_data_by_period(company_name, period, is_admin=is_super_admin())

        # Combine data from both sources
        combined_data = {}

        if income_data and len(income_data) > 0:
            combined_data.update(income_data[0])

        if balance_data and len(balance_data) > 0:
            combined_data.update(balance_data[0])

        if combined_data:
            company_data[company_name] = combined_data

    return company_data


def extract_value_data_for_export(period):
    """
    Extract value trends data as a pandas DataFrame for Excel export.
    Reuses the cached fetch_all_companies_value_trends function.

    Returns:
        pandas.DataFrame with value line items as rows and companies as columns
    """
    # Reuse cached data
    company_data = fetch_all_companies_value_trends(period)

    if not company_data:
        return None

    # Value trends line items (same as in create_value_trends_comparison_table)
    value_items = [
        ('EBITDA (000)', 'ebitda', 'currency', False),
        ('3 x EBITDA (000)', '3x_ebitda', 'currency', True),
        ('Interest Bearing Debt (000)', 'interest_bearing_debt', 'currency', False),
        ('Company Value (000)', 'company_value', 'currency', True),
        ('Company Value Rank', 'company_value_rank', 'rank', True),
        ('Equity (000)', 'owners_equity', 'currency', False),
        ('Value to Equity', 'value_to_equity', 'ratio', True)
    ]

    # Filter companies with data
    companies_with_data = []
    for company_name, data in company_data.items():
        has_data = False
        for item_name, field_name, value_type, is_calculated in value_items:
            if not is_calculated:
                value = data.get(field_name, 0) or 0
                if value != 0:
                    has_data = True
                    break
        if has_data:
            companies_with_data.append(company_name)

    if not companies_with_data:
        return None

    # Perform calculations (same logic as create_value_trends_comparison_table)
    for company_name in companies_with_data:
        data = company_data[company_name]

        # Convert equity from dollars to thousands
        equity = data.get('owners_equity', 0) or 0
        data['owners_equity'] = equity / 1000 if equity != 0 else 0

        # Calculate 3 x EBITDA
        ebitda = data.get('ebitda', 0) or 0
        data['3x_ebitda'] = ebitda * 3

        # Calculate Company Value
        interest_bearing_debt = data.get('interest_bearing_debt', 0) or 0
        data['company_value'] = data['3x_ebitda'] - interest_bearing_debt

        # Calculate Value to Equity ratio
        equity_in_thousands = data['owners_equity']
        if equity_in_thousands != 0:
            data['value_to_equity'] = data['company_value'] / equity_in_thousands
        else:
            data['value_to_equity'] = 0

    # Calculate rankings
    company_values = [(comp, company_data[comp].get('company_value', 0) or 0)
                      for comp in companies_with_data]
    company_values.sort(key=lambda x: x[1], reverse=True)

    for rank, (company_name, _) in enumerate(company_values, start=1):
        company_data[company_name]['company_value_rank'] = rank

    # Build DataFrame
    data_dict = {}

    for company in sorted(companies_with_data):
        company_values = []

        for item_name, field_name, value_type, is_calculated in value_items:
            value = company_data[company].get(field_name, 0) or 0

            # Format value based on type
            if value is None or value == 0:
                formatted = '-'
            elif value_type == 'currency':
                if value < 0:
                    formatted = f'$({abs(value):,.0f})'
                else:
                    formatted = f'${value:,.0f}'
            elif value_type == 'ratio':
                formatted = f'{value:.1f}'
            else:  # rank
                formatted = str(int(value)) if value != 0 else '-'

            company_values.append(formatted)

        data_dict[company] = company_values

    # Create DataFrame
    line_item_names = [item[0] for item in value_items]
    df = pd.DataFrame(data_dict, index=line_item_names)
    df.index.name = 'Value Trends'

    return df


def create_group_value_page():
    """Create group value comparison page with header and period selector"""

    # Require authentication
    require_auth()

    # Initialize year selection in session state (default to most recent year)
    if 'group_value_selected_year' not in st.session_state:
        st.session_state.group_value_selected_year = CURRENT_YEAR

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
        page_title=f"Group Value Comparison - {period_display}",
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
                {st.session_state.group_value_selected_year} Value Trends
            </h2>
        </div>
        """, unsafe_allow_html=True)

    with col_filter:
        # Year filter - same default size as homepage selectboxes
        year_options = list(range(CURRENT_YEAR, CURRENT_YEAR - 5, -1))
        selected_year = st.selectbox(
            "**Select Year**",
            options=year_options,
            index=year_options.index(st.session_state.group_value_selected_year) if st.session_state.group_value_selected_year in year_options else 0,
            key="group_value_year_selector"
        )

        # Update session state if year changed
        if selected_year != st.session_state.group_value_selected_year:
            st.session_state.group_value_selected_year = selected_year
            st.rerun()

    # Add some spacing
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Get Airtable connection
    conn = get_airtable_connection()

    if not conn:
        st.error("❌ Unable to connect to Airtable. Please check your credentials.")
        return

    # Get selected year from session state
    selected_year = st.session_state.group_value_selected_year

    # Determine period filter based on selection and year
    if current_period == 'year_end':
        period_filter = f"{selected_year} Annual"
    else:
        period_filter = f"June {selected_year}"

    # Fetch value trends data for all companies
    with st.spinner("Loading value analysis data..."):
        company_data = fetch_all_companies_value_trends(period_filter)

    if not company_data:
        st.warning(f"⚠️ No value trends data available for {selected_year} - {period_display}.")
        st.info("💡 Try selecting a different year or period.")
        return

    # Display the value trends comparison table
    create_value_trends_comparison_table(company_data, period_filter)


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="Group Value - BPC Dashboard",
        page_icon="📊",
        layout="wide"
    )
    create_group_value_page()
