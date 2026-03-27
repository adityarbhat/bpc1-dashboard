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


def create_cash_flow_comparison_table(company_data, period):
    """Create and display the cash flow comparison table with companies as columns"""

    # Cash flow line items including Cash Flow Proof section
    # Format: (Display Name, field_name, value_type, is_total, is_header)
    # value_type: 'currency' = dollar amount, 'percent' = percentage/ratio
    cash_flow_items = [
        ('Operating Cash Flow (OCF)', 'operating_cash_flow', 'currency', True, False),
        ('OCF/Revenue', 'ocf_revenue_ratio', 'percent', True, False),
        ('Financing Cash Flow (FCF)', 'financing_cash_flow', 'currency', True, False),
        ('FCF/Revenue', 'fcf_revenue_ratio', 'percent', True, False),
        ('Net Cash Flow (NCF)', 'net_cash_flow', 'currency', True, False),
        ('NCF/Revenue', 'ncf_revenue_ratio', 'percent', True, False),
        ('Cash Flow Proof:', None, None, False, True),  # Section header
        ('Prior Period Cash', 'prior_period_cash', 'currency', False, False),
        ('Net Cash Flow', 'net_cash_flow_proof', 'currency', False, False),
        ('Current Period Cash', 'current_period_cash', 'currency', False, False),
        ('Actual Current Period Cash', 'actual_current_period_cash', 'currency', False, False)
    ]

    # Get sorted list of companies (excluding companies with no data)
    companies_with_data = []
    for company_name, data in company_data.items():
        # Check if company has at least one non-zero field
        has_data = False
        for item_name, field_name, value_type, is_total, is_header in cash_flow_items:
            if field_name and not is_header:
                value = data.get(field_name, 0) or 0
                if value != 0:
                    has_data = True
                    break
        if has_data:
            companies_with_data.append(company_name)

    # Sort by rank (rank 1 on the right)
    companies_with_data = sort_companies_by_rank(companies_with_data, period)

    if not companies_with_data:
        st.warning("⚠️ No companies have cash flow data for the selected period.")
        return

    # Calculate group averages for each line item
    group_averages = {}

    for item_name, field_name, value_type, is_total, is_header in cash_flow_items:
        if not field_name or is_header:
            group_averages[item_name] = None
            continue

        if value_type == 'percent':
            # For percentages/ratios, calculate average percentage
            percentages = []
            for comp in companies_with_data:
                value = company_data[comp].get(field_name, 0) or 0
                if value != 0:
                    # Handle both decimal (0.15) and percentage (15) formats
                    pct = value * 100 if abs(value) < 1 else value
                    percentages.append(pct)
            group_averages[item_name] = sum(percentages) / len(percentages) if percentages else 0

        else:  # value_type == 'currency'
            # For dollar amounts, calculate average dollar amount
            values = [company_data[comp].get(field_name, 0) or 0
                     for comp in companies_with_data]
            valid_values = [v for v in values if v != 0]
            group_averages[item_name] = sum(valid_values) / len(valid_values) if valid_values else 0

    # Helper function to format values based on type
    def format_value(value, value_type):
        if value is None or value == 0:
            return '-'

        if value_type == 'currency':
            # Format with parentheses for negative values
            if value < 0:
                return f'$({abs(value):,.0f})'
            else:
                return f'${value:,.0f}'
        elif value_type == 'percent':
            # Handle both decimal (0.15) and percentage (15) formats
            pct = value * 100 if abs(value) < 1 else value
            return f'{pct:.1f}%'
        return '-'

    # Helper function to format average values
    def format_average(avg_value, value_type):
        if avg_value is None or avg_value == 0:
            return '-'

        if value_type == 'currency':
            if avg_value < 0:
                return f'$({abs(avg_value):,.0f})'
            else:
                return f'${avg_value:,.0f}'
        elif value_type == 'percent':
            return f'{avg_value:.1f}%'
        return '-'

    # Display color coding
    st.markdown("""
    <div style="background-color: #f7fafc; border-left: 4px solid #025a9a; padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px;">
        <div style="display: grid; grid-template-columns: auto 1fr; gap: 0.5rem; align-items: center;">
            <div style="background-color: #c6f6d5; padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; text-align: center;">
                Green
            </div>
            <div style="color: #1a202c; font-family: 'Montserrat', sans-serif;">
                <strong>Leading Agent</strong> - Highest cash flow values and ratios (stronger cash generation)
            </div>
            <div style="background-color: #ffe082; padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; text-align: center;">
                Yellow
            </div>
            <div style="color: #1a202c; font-family: 'Montserrat', sans-serif;">
                <strong>Above Group Average</strong> - Cash flow exceeds group average
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CSS styling
    st.markdown("""
    <style>
    .cash-flow-table-container {
        max-height: 800px;
        overflow-x: auto;
        overflow-y: auto;
        position: relative;
        margin: 1rem 0;
    }
    .cash-flow-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.0rem;
        border: 1px solid white;
    }
    .cash-flow-table thead {
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .cash-flow-table th {
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
    .cash-flow-table th:first-child {
        text-align: left;
        min-width: 200px;
        max-width: 200px;
        position: sticky;
        left: 0;
        z-index: 30;
        background-color: #025a9a;
    }
    .cash-flow-table th.average-header {
        text-align: center;
    }
    .cash-flow-table td {
        padding: 10px 8px;
        border: 1px solid white;
        text-align: center;
        background-color: white;
        font-size: 1.0rem;
    }
    .cash-flow-table td:first-child {
        text-align: left;
        font-weight: 500;
        background-color: white;
        position: sticky;
        left: 0;
        z-index: 20;
        padding-left: 15px;
        font-size: 1.0rem;
    }
    .cash-flow-table td.average-cell {
        background-color: #e6f7ff;
        font-weight: 600;
        text-align: center;
    }
    .cash-flow-table tr.section-header-row td {
        background-color: #e0e0e0;
        font-weight: 700;
        text-align: left;
    }
    .cash-flow-table tr.section-header-row td:first-child {
        background-color: #e0e0e0;
    }
    .cash-flow-table tr.section-header-row td.average-cell {
        background-color: #e0e0e0;
    }
    .cash-flow-table .overall-rank-row {
        background-color: #025a9a;
        font-weight: 700;
        font-size: 1.05rem;
        box-shadow: 0 2px 4px rgba(2, 90, 154, 0.3);
        border-bottom: 3px solid white;
    }
    .cash-flow-table .overall-rank-row td {
        background-color: #025a9a !important;
        color: white;
        font-weight: 700;
        font-size: 1.05rem;
        text-align: center;
    }
    .cash-flow-table .overall-rank-row td:first-child {
        background-color: #025a9a !important;
        text-align: left;
    }
    .cash-flow-table tr:hover:not(.section-header-row) td {
        background-color: #f7fafc;
    }
    .cash-flow-table tr:hover:not(.section-header-row) td.average-cell {
        background-color: #e0f2ff;
    }
    .cash-flow-table td.winner-cell {
        background-color: #c6f6d5 !important;
        font-weight: 700 !important;
    }
    .cash-flow-table td.above-average-cell {
        background-color: #ffe082 !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Build table HTML with container for scrolling
    table_html = '<div class="cash-flow-table-container"><table class="cash-flow-table"><thead>'

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
    table_html += '<th>Cash Flow</th>'
    table_html += '<th class="average-header" style="color: #ffe082;">Group Average</th>'
    for company_name in companies_with_data:
        table_html += f'<th>{company_name}</th>'
    table_html += '</tr></thead><tbody>'

    # Define items where higher is better (positive cash flow is good)
    high_is_good_items = [
        'Operating Cash Flow (OCF)',
        'OCF/Revenue',
        'Net Cash Flow (NCF)',
        'NCF/Revenue',
        'Current Period Cash',
        'Actual Current Period Cash'
    ]

    # Data rows
    for item_name, field_name, value_type, is_total, is_header in cash_flow_items:
        # Determine row class
        if is_header:
            row_class = 'section-header-row'
        else:
            row_class = ''

        table_html += f'<tr class="{row_class}">'
        table_html += f'<td>{item_name}</td>'

        # Add Group Average column
        if is_header:
            table_html += '<td class="average-cell"></td>'
        else:
            avg_value = group_averages.get(item_name, 0)
            formatted_avg = format_average(avg_value, value_type)
            table_html += f'<td class="average-cell">{formatted_avg}</td>'

        # Find winner for this row (only for non-header, colorable items)
        winner = None
        if not is_header and item_name in high_is_good_items:
            # Higher is better - find max
            max_value = -999999999
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0 if field_name else 0
                if value > max_value:
                    max_value = value
                    winner = company_name

        # Add data for each company
        for company_name in companies_with_data:
            if is_header:
                table_html += '<td></td>'
            else:
                value = company_data[company_name].get(field_name, 0) or 0 if field_name else 0
                formatted_value = format_value(value, value_type)

                # Determine cell class for color coding
                cell_class = ''

                # Apply color coding only to items in high_is_good_items
                if item_name in high_is_good_items:
                    # Green for highest (winner)
                    if company_name == winner:
                        cell_class = 'winner-cell'
                    # Yellow for above group average
                    elif value != 0 and value > group_averages.get(item_name, 0):
                        cell_class = 'above-average-cell'

                table_html += f'<td class="{cell_class}">{formatted_value}</td>'

        table_html += '</tr>'

    table_html += '</table></div>'

    # Display table
    st.markdown(table_html, unsafe_allow_html=True)


def calculate_cash_flow_changes(balance_data, income_data, company_name=None):
    """Calculate year-over-year changes for cash flow items - copied from company_cash_flow.py"""
    from shared.year_config import get_default_years
    years = get_default_years()
    calculated_data = {}

    # Special handling for Bisson and Hopkins - hardcoded 2024 values
    bisson_2024_values = {
        'operating_cash_flow': -1651552,
        'ocf_revenue_ratio': -16.7,
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
        'operating_cash_flow': -1338086,
        'ocf_revenue_ratio': -27.4,
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
        current_net_profit = current_income.get('profit_before_tax_with_ppp', None)

        # Calculate Operating Cash Flow (OCF) components
        if current_net_profit is not None and i > 0 and prior_balance and current_balance:
            # Change in Current Assets
            prior_total_ca = prior_balance.get('total_current_assets', 0) or 0
            prior_cash = prior_balance.get('cash_and_cash_equivalents', 0) or 0
            current_total_ca = current_balance.get('total_current_assets', 0) or 0
            current_cash = current_balance.get('cash_and_cash_equivalents', 0) or 0
            current_notes_payable = current_balance.get('notes_payable_owners', 0) or 0
            change_current_assets = (prior_total_ca - prior_cash) - (current_total_ca - current_cash - current_notes_payable)

            # Change in Current Liabilities
            current_cl = current_balance.get('total_current_liabilities', 0) or 0
            current_cpltd = current_balance.get('current_portion_ltd', 0) or 0
            current_npb = current_balance.get('notes_payable_bank', 0) or 0
            prior_cl = prior_balance.get('total_current_liabilities', 0) or 0
            prior_cpltd = prior_balance.get('current_portion_ltd', 0) or 0
            prior_npb = prior_balance.get('notes_payable_bank', 0) or 0
            prior_npo = prior_balance.get('notes_payable_owners', 0) or 0
            change_current_liabilities = (current_cl - current_cpltd - current_npb) - (prior_cl - prior_cpltd - prior_npb - prior_npo)

            # Change in Net Fixed Assets
            prior_nfa = prior_balance.get('net_fixed_assets', 0) or 0
            current_nfa = current_balance.get('net_fixed_assets', 0) or 0
            change_net_fixed_assets = prior_nfa - current_nfa

            # Change in Non-Current Assets
            prior_other = prior_balance.get('other_assets', 0) or 0
            prior_inter = prior_balance.get('inter_company_receivable', 0) or 0
            current_other = current_balance.get('other_assets', 0) or 0
            current_inter = current_balance.get('inter_company_receivable', 0) or 0
            change_non_current_assets = (prior_other + prior_inter) - (current_other + current_inter)

            # Calculate OCF
            ocf = current_net_profit + change_current_assets + change_current_liabilities + change_net_fixed_assets + change_non_current_assets
            calculated_data[year]['operating_cash_flow'] = ocf

            # Calculate OCF/Revenue ratio
            revenue = current_income.get('total_revenue', 0)
            if revenue and revenue != 0:
                calculated_data[year]['ocf_revenue_ratio'] = (ocf / revenue) * 100
            else:
                calculated_data[year]['ocf_revenue_ratio'] = None

            # Calculate Financing Cash Flow (FCF) components
            # Change in Bank Debt
            current_npb = current_balance.get('notes_payable_bank', 0) or 0
            current_cpltd = current_balance.get('current_portion_ltd', 0) or 0
            current_ltd = current_balance.get('long_term_debt', 0) or 0
            prior_npb = prior_balance.get('notes_payable_bank', 0) or 0
            prior_cpltd = prior_balance.get('current_portion_ltd', 0) or 0
            prior_ltd = prior_balance.get('long_term_debt', 0) or 0
            change_bank_debt = (current_npb + current_cpltd + current_ltd) - (prior_npb + prior_cpltd + prior_ltd)

            # Change in Owner Debt
            prior_owner_debt = (prior_balance.get('notes_payable_owners', 0) or 0) + (prior_balance.get('notes_payable_owners_lt', 0) or 0)
            current_owner_debt = (current_balance.get('notes_payable_owners', 0) or 0) + (current_balance.get('notes_payable_owners_lt', 0) or 0)
            change_owner_debt = current_owner_debt - prior_owner_debt

            # Change in Non-Current Liabilities
            current_icd = current_balance.get('inter_company_debt', 0) or 0
            current_other_lt = current_balance.get('other_lt_liabilities', 0) or 0
            prior_icd = prior_balance.get('inter_company_debt', 0) or 0
            prior_other_lt = prior_balance.get('other_lt_liabilities', 0) or 0
            change_non_current_liabilities = (current_icd + current_other_lt) - (prior_icd + prior_other_lt)

            # Equity Adjustment
            prior_equity = prior_balance.get('owners_equity', 0) or 0
            current_equity = current_balance.get('owners_equity', 0) or 0
            equity_adjustment = (current_equity - prior_equity) - current_net_profit

            # Calculate FCF
            fcf = change_bank_debt + change_owner_debt + change_non_current_liabilities + equity_adjustment
            calculated_data[year]['financing_cash_flow'] = fcf

            # Calculate FCF/Revenue ratio
            if revenue and revenue != 0:
                calculated_data[year]['fcf_revenue_ratio'] = (fcf / revenue) * 100
            else:
                calculated_data[year]['fcf_revenue_ratio'] = None

            # Calculate Net Cash Flow (NCF) = OCF + FCF
            ncf = ocf + fcf
            calculated_data[year]['net_cash_flow'] = ncf

            # Calculate NCF/Revenue ratio
            if revenue and revenue != 0:
                calculated_data[year]['ncf_revenue_ratio'] = (ncf / revenue) * 100
            else:
                calculated_data[year]['ncf_revenue_ratio'] = None

            # Cash Flow Proof calculations
            # Prior Period Cash
            calculated_data[year]['prior_period_cash'] = prior_balance.get('cash_and_cash_equivalents', None)

            # Net Cash Flow for proof (same as NCF)
            calculated_data[year]['net_cash_flow_proof'] = ncf

            # Current Period Cash (calculated: Prior + NCF)
            if calculated_data[year]['prior_period_cash'] is not None:
                calculated_data[year]['current_period_cash'] = calculated_data[year]['prior_period_cash'] + ncf
            else:
                calculated_data[year]['current_period_cash'] = None

            # Actual Current Period Cash (from balance sheet)
            calculated_data[year]['actual_current_period_cash'] = current_balance.get('cash_and_cash_equivalents', None)
        else:
            calculated_data[year]['operating_cash_flow'] = None
            calculated_data[year]['ocf_revenue_ratio'] = None
            calculated_data[year]['financing_cash_flow'] = None
            calculated_data[year]['fcf_revenue_ratio'] = None
            calculated_data[year]['net_cash_flow'] = None
            calculated_data[year]['ncf_revenue_ratio'] = None
            calculated_data[year]['prior_period_cash'] = None
            calculated_data[year]['net_cash_flow_proof'] = None
            calculated_data[year]['current_period_cash'] = None
            calculated_data[year]['actual_current_period_cash'] = None

    return calculated_data


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def fetch_all_companies_cash_flow(period):
    """Fetch cash flow data for all companies for a specific period"""
    airtable = get_airtable_connection()

    # Get all companies
    from shared.airtable_connection import get_companies_cached
    companies = get_companies_cached()

    if not companies:
        return None

    # Extract year from period (e.g., "2024 Annual" -> "2024")
    year = period.split()[0]

    # Determine prior year for calculations
    try:
        prior_year = str(int(year) - 1)
    except:
        return None

    company_data = {}

    for company in companies:
        company_name = company.get('name')
        if not company_name:
            continue

        # Fetch balance sheet data for current year and prior year
        balance_data = {}
        income_data = {}

        # Current year
        balance_current = airtable.get_balance_sheet_data_by_period(company_name, period, is_admin=is_super_admin())
        if balance_current and len(balance_current) > 0:
            balance_data[year] = balance_current[0]

        income_current = airtable.get_income_statement_data_by_period(company_name, period, is_admin=is_super_admin())
        if income_current and len(income_current) > 0:
            income_data[year] = income_current[0]

        # Prior year
        prior_period = f"{prior_year} Annual" if "Annual" in period else f"June {prior_year}"
        balance_prior = airtable.get_balance_sheet_data_by_period(company_name, prior_period, is_admin=is_super_admin())
        if balance_prior and len(balance_prior) > 0:
            balance_data[prior_year] = balance_prior[0]

        income_prior = airtable.get_income_statement_data_by_period(company_name, prior_period, is_admin=is_super_admin())
        if income_prior and len(income_prior) > 0:
            income_data[prior_year] = income_prior[0]

        # Calculate cash flow using the same logic as company page
        calculated_data = calculate_cash_flow_changes(balance_data, income_data, company_name)

        # Extract data for the selected year
        if year in calculated_data:
            company_data[company_name] = calculated_data[year]

    return company_data


def extract_cash_flow_data_for_export(period):
    """
    Extract cash flow data as a pandas DataFrame for Excel export.

    Returns:
        pandas.DataFrame with cash flow items as rows, companies as columns
    """
    # Reuse cached data
    company_data = fetch_all_companies_cash_flow(period)

    if not company_data:
        return None

    # Cash flow line items
    cash_flow_items = [
        ('Operating Cash Flow (OCF)', 'operating_cash_flow', 'currency'),
        ('OCF/Revenue', 'ocf_revenue_ratio', 'percent'),
        ('Financing Cash Flow (FCF)', 'financing_cash_flow', 'currency'),
        ('FCF/Revenue', 'fcf_revenue_ratio', 'percent'),
        ('Net Cash Flow (NCF)', 'net_cash_flow', 'currency'),
        ('NCF/Revenue', 'ncf_revenue_ratio', 'percent'),
        ('Prior Period Cash', 'prior_period_cash', 'currency'),
        ('Net Cash Flow', 'net_cash_flow_proof', 'currency'),
        ('Current Period Cash', 'current_period_cash', 'currency'),
        ('Actual Current Period Cash', 'actual_current_period_cash', 'currency')
    ]

    # Filter companies with data
    companies_with_data = []
    for company_name, data in company_data.items():
        has_data = False
        for item_name, field_name, value_type in cash_flow_items:
            if field_name:
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

        for item_name, field_name, value_type in cash_flow_items:
            if not field_name:
                formatted = '-'
            else:
                value = company_data[company].get(field_name, 0) or 0

                # Format value
                if value == 0:
                    formatted = '-'
                elif value_type == 'currency':
                    if value < 0:
                        formatted = f'$({abs(value):,.0f})'
                    else:
                        formatted = f'${value:,.0f}'
                else:  # percent
                    pct = value * 100 if abs(value) < 1 else value
                    formatted = f'{pct:.1f}%'

                company_values.append(formatted)

        data_dict[company] = company_values

    # Create DataFrame
    line_item_names = [item[0] for item in cash_flow_items]
    df = pd.DataFrame(data_dict, index=line_item_names)
    df.index.name = 'Cash Flow Item'

    return df


def create_group_cash_flow_page():
    """Create group cash flow comparison page with header and period selector"""

    # Require authentication
    require_auth()

    # Initialize year selection in session state (default to most recent year)
    if 'group_cash_flow_selected_year' not in st.session_state:
        st.session_state.group_cash_flow_selected_year = CURRENT_YEAR

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
        page_title=f"Group Cash Flow Comparison - {period_display}",
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
                {st.session_state.group_cash_flow_selected_year} Cash Flow
            </h2>
        </div>
        """, unsafe_allow_html=True)

    with col_filter:
        # Year filter - same default size as homepage selectboxes
        year_options = list(range(CURRENT_YEAR, CURRENT_YEAR - 5, -1))
        selected_year = st.selectbox(
            "**Select Year**",
            options=year_options,
            index=year_options.index(st.session_state.group_cash_flow_selected_year) if st.session_state.group_cash_flow_selected_year in year_options else 0,
            key="group_cash_flow_year_selector"
        )

        # Update session state if year changed
        if selected_year != st.session_state.group_cash_flow_selected_year:
            st.session_state.group_cash_flow_selected_year = selected_year
            st.rerun()

    # Add some spacing
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Get Airtable connection
    conn = get_airtable_connection()

    if not conn:
        st.error("❌ Unable to connect to Airtable. Please check your credentials.")
        return

    # Get selected year from session state
    selected_year = st.session_state.group_cash_flow_selected_year

    # Determine period filter based on selection and year
    if current_period == 'year_end':
        period_filter = f"{selected_year} Annual"
    else:
        period_filter = f"June {selected_year}"

    # Fetch cash flow data for all companies
    with st.spinner("Loading cash flow data..."):
        company_data = fetch_all_companies_cash_flow(period_filter)

    if not company_data:
        st.warning(f"⚠️ No cash flow data available for {selected_year} - {period_display}.")
        st.info("💡 Try selecting a different year or period.")
        return

    # Display the cash flow comparison table
    create_cash_flow_comparison_table(company_data, period_filter)


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="Group Cash Flow - BPC Dashboard",
        page_icon="📊",
        layout="wide"
    )
    create_group_cash_flow_page()
