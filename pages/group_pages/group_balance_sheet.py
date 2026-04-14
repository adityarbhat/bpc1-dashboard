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


def create_balance_sheet_comparison_table(company_data, period):
    """Create and display the balance sheet comparison table with companies as columns showing % of Total Assets"""

    # Balance sheet line items matching the Balance Sheet Trend Table structure
    # Format: (Display Name, field_name, value_type)
    # value_type: 'currency' = dollar amount (Owner's Equity), 'percent' = % of assets,
    #             'percent_negative' = negative % (Accumulated Depreciation), 'currency_total' = 100%
    balance_sheet_items = [
        ("Owner's Equity", 'owners_equity', 'currency'),  # First row shows dollar amount
        ('Cash and Cash Equivalents', 'cash_and_cash_equivalents', 'percent'),
        ('Trade Accounts Receivable', 'trade_accounts_receivable', 'percent'),
        ('Receivables', 'receivables', 'percent'),
        ('Other Receivables', 'other_receivables', 'percent'),
        ('Prepaid Expenses', 'prepaid_expenses', 'percent'),
        ('Related Company Receivables', 'related_company_receivables', 'percent'),
        ('Owner Receivables', 'owner_receivables', 'percent'),
        ('Other Current Assets', 'other_current_assets', 'percent'),
        ('Total Current Assets', 'total_current_assets', 'percent'),
        ('Gross Fixed Assets', 'gross_fixed_assets', 'percent'),
        ('Accumulated Depreciation (-)', 'accumulated_depreciation', 'percent_negative'),
        ('Net Fixed Assets', 'net_fixed_assets', 'percent'),
        ('Inter Company Receivables', 'inter_company_receivable', 'percent'),
        ('Other Assets', 'other_assets', 'percent'),
        ('TOTAL ASSETS', 'total_assets_calculated', 'currency_total'),  # Shows 100%
        ('Notes Payable - Bank', 'notes_payable_bank', 'percent'),
        ('Notes Payable to Owners - Current Portion', 'notes_payable_owners', 'percent'),
        ('Trade Accounts Payable', 'trade_accounts_payable', 'percent'),
        ('Accrued Expenses', 'accrued_expenses', 'percent'),
        ('Current Portion LTD', 'current_portion_ltd', 'percent'),
        ('Inter Company Payable', 'inter_company_payable', 'percent'),
        ('Other Current Liabilities', 'other_current_liabilities', 'percent'),
        ('Total Current Liabilities', 'total_current_liabilities', 'percent'),
        ('Long-Term Debt', 'long_term_debt', 'percent'),
        ('Notes Payable to Owners - LT', 'notes_payable_owners_lt', 'percent'),
        ('Inter Company Debt', 'inter_company_debt', 'percent'),
        ('Other LT Liabilities', 'other_lt_liabilities', 'percent'),
        ('Long Term Liabilities', 'total_long_term_liabilities', 'percent'),
        ('Total Liabilities', 'total_liabilities', 'percent'),
        ("Owners' Equity", 'owners_equity', 'percent'),
        ('TOTAL LIABILITIES & EQUITY', 'total_assets_calculated', 'currency_total')  # Shows 100%
    ]

    # Get sorted list of companies (excluding companies with no data)
    companies_with_data = []
    for company_name, data in company_data.items():
        # Check if company has at least one non-zero field
        has_data = False
        for item_name, field_name, value_type in balance_sheet_items:
            value = data.get(field_name, 0) or 0
            if value != 0:
                has_data = True
                break
        if has_data:
            companies_with_data.append(company_name)

    # Sort by rank (rank 1 on the right)
    companies_with_data = sort_companies_by_rank(companies_with_data, period)

    if not companies_with_data:
        st.warning("⚠️ No companies have balance sheet data for the selected period.")
        return

    # Calculate total assets for each company (Assets = Liabilities + Equity)
    company_total_assets = {}
    for company_name in companies_with_data:
        data = company_data[company_name]
        total_assets_raw = data.get('total_assets', 0) or 0
        total_liabilities = data.get('total_liabilities', 0) or 0
        owners_equity = data.get('owners_equity', 0) or 0

        # Use balance sheet equation if total_assets not available
        if total_assets_raw == 0 and (total_liabilities > 0 or owners_equity > 0):
            calculated_total_assets = total_liabilities + owners_equity
        else:
            calculated_total_assets = total_assets_raw

        company_total_assets[company_name] = calculated_total_assets
        # Store in company data for later reference
        company_data[company_name]['total_assets_calculated'] = calculated_total_assets

    # Calculate group averages for each line item
    group_averages = {}

    for item_name, field_name, value_type in balance_sheet_items:
        if value_type == 'currency':
            # For Owner's Equity, calculate average dollar amount
            values = [company_data[comp].get(field_name, 0) or 0
                     for comp in companies_with_data]
            valid_values = [v for v in values if v != 0]
            group_averages[item_name] = sum(valid_values) / len(valid_values) if valid_values else 0

        elif value_type == 'currency_total':
            # Always 100%
            group_averages[item_name] = 100

        elif value_type == 'percent_negative':
            # For accumulated depreciation, calculate average negative percentage
            percentages = []
            for comp in companies_with_data:
                value = company_data[comp].get(field_name, 0) or 0
                total_assets = company_total_assets[comp]
                if total_assets > 0 and value != 0:
                    pct = (abs(value) / total_assets) * 100
                    percentages.append(pct)
            group_averages[item_name] = -(sum(percentages) / len(percentages)) if percentages else 0

        else:  # value_type == 'percent'
            # For percentages, calculate average percentage
            percentages = []
            for comp in companies_with_data:
                value = company_data[comp].get(field_name, 0) or 0
                total_assets = company_total_assets[comp]
                if total_assets > 0 and value != 0:
                    pct = (value / total_assets) * 100
                    percentages.append(pct)
            group_averages[item_name] = sum(percentages) / len(percentages) if percentages else 0

    # Helper function to format values based on type
    def format_value(value, value_type, total_assets):
        if value is None:
            return '-'

        if value_type == 'currency':
            # Show dollar amount for Owner's Equity
            if value == 0:
                return '$0'
            return f'${value:,.0f}'
        elif value_type == 'currency_total':
            # Show 100% for TOTAL ASSETS and TOTAL LIABILITIES & EQUITY
            return '100%'
        elif value_type == 'percent_negative':
            # Handle negative percentages (accumulated depreciation)
            if total_assets > 0 and value != 0:
                percentage = (abs(value) / total_assets) * 100
                return f'({percentage:.1f}%)'
            else:
                return '-'
        else:  # value_type == 'percent'
            # Calculate percentage of total assets
            if total_assets > 0 and value != 0:
                percentage = (value / total_assets) * 100
                return f'{percentage:.1f}%'
            else:
                return '-'

    # Helper function to format average values
    def format_average(avg_value, value_type):
        if avg_value == 0:
            return '-'

        if value_type == 'currency':
            return f'${avg_value:,.0f}'
        elif value_type == 'currency_total':
            return '100%'
        elif value_type == 'percent_negative':
            return f'({abs(avg_value):.1f}%)'
        else:  # percent
            return f'{avg_value:.1f}%'

    # Display color coding
    st.markdown("""
    <div style="background-color: #f7fafc; border-left: 4px solid #025a9a; padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px;">
        <div style="display: grid; grid-template-columns: auto 1fr; gap: 0.75rem; align-items: start;">
            <div style="background-color: #c6f6d5; padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; text-align: center;">
                Green
            </div>
            <div style="color: #1a202c; font-family: 'Montserrat', sans-serif;">
                <strong>Strong Financial Position (Leading Agent)</strong><br>
                <span style="font-size: 0.9rem;">
                • <strong>Highest %</strong> for key assets: Cash & Cash Equivalents, Total Current Assets, Gross/Net Fixed Assets, Owners' Equity<br>
                • <strong>Highest %</strong> for informational items: All receivables (Trade AR, Receivables, Owner Receivables, Related Co. Receivables, etc.), Prepaid Expenses, Other Current/Long-term Assets (shows which company has most)<br>
                • <strong>Lowest %</strong> for Accumulated Depreciation: Lower depreciation indicates newer/better-maintained equipment<br>
                • <strong>Lowest %</strong> for all liability items: Notes Payable, Accounts Payable, Long-Term Debt, Total Liabilities, etc. (lower debt is better)
                </span>
            </div>
            <div style="background-color: #ffe082; padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; text-align: center;">
                Yellow
            </div>
            <div style="color: #1a202c; font-family: 'Montserrat', sans-serif;">
                <strong>Above Group Average</strong><br>
                <span style="font-size: 0.9rem;">
                • Any liability item where company's % exceeds group average (indicates higher debt burden)
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CSS styling
    st.markdown("""
    <style>
    .balance-sheet-table-container {
        max-height: 800px;
        overflow-x: auto;
        overflow-y: auto;
        position: relative;
        margin: 1rem 0;
    }
    .balance-sheet-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.0rem;
        border: 1px solid white;
    }
    .balance-sheet-table thead {
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .balance-sheet-table th {
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
    .balance-sheet-table th:first-child {
        text-align: left;
        min-width: 200px;
        max-width: 200px;
        position: sticky;
        left: 0;
        z-index: 30;
        background-color: #025a9a;
    }
    .balance-sheet-table th.average-header {
        text-align: center;
    }
    .balance-sheet-table td {
        padding: 10px 8px;
        border: 1px solid white;
        text-align: center;
        background-color: white;
        font-size: 1.0rem;
    }
    .balance-sheet-table td:first-child {
        text-align: left;
        font-weight: 500;
        background-color: white;
        position: sticky;
        left: 0;
        z-index: 20;
        padding-left: 15px;
        font-size: 1.0rem;
    }
    .balance-sheet-table td.average-cell {
        background-color: #e6f7ff;
        font-weight: 600;
        text-align: center;
    }
    .balance-sheet-table tr.header-row td {
        background-color: #4a5568 !important;
        color: white;
        font-weight: 700;
        text-align: left;
    }
    .balance-sheet-table tr.header-row td:first-child {
        background-color: #4a5568 !important;
    }
    .balance-sheet-table tr.total-row td {
        background-color: #e2e8f0;
        font-weight: 600;
    }
    .balance-sheet-table tr.total-row td:first-child {
        background-color: #e2e8f0;
    }
    .balance-sheet-table tr.total-row td.average-cell {
        background-color: #b8e6ff;
        font-weight: 700;
    }
    .balance-sheet-table tr.major-total-row td {
        background-color: #cbd5e0;
        font-weight: 700;
    }
    .balance-sheet-table tr.major-total-row td:first-child {
        background-color: #cbd5e0;
    }
    .balance-sheet-table tr.major-total-row td.average-cell {
        background-color: #9cd9ff;
        font-weight: 700;
    }
    .balance-sheet-table .overall-rank-row {
        background-color: #025a9a;
        font-weight: 700;
        font-size: 1.05rem;
        box-shadow: 0 2px 4px rgba(2, 90, 154, 0.3);
    }
    .balance-sheet-table .overall-rank-row td {
        background-color: #025a9a !important;
        color: white;
        font-weight: 700;
        font-size: 1.05rem;
        text-align: center;
    }
    .balance-sheet-table .overall-rank-row td:first-child {
        background-color: #025a9a !important;
        text-align: left;
    }
    .balance-sheet-table tr:hover:not(.header-row) td {
        box-shadow: inset 0 2px 0 #025a9a, inset 0 -2px 0 #025a9a;
    }
    .balance-sheet-table td.winner-cell {
        background-color: #c6f6d5 !important;
        font-weight: 700 !important;
    }
    .balance-sheet-table td.above-average-cell {
        background-color: #ffe082 !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Define items where HIGHER percentage is better (highlight highest in green)
    high_is_good_items = [
        'Cash and Cash Equivalents',  # Higher liquidity is better
        'Total Current Assets',  # Higher current assets shows stronger liquidity position
        'Gross Fixed Assets',  # Higher productive capacity
        'Net Fixed Assets',  # Higher productive capacity (after depreciation)
        "Owners' Equity"  # Higher equity is better (appears twice in balance sheet)
    ]

    # Define items where LOWER percentage is better (like liabilities, but these are assets)
    # Highlight lowest (closest to zero) in green - these are contra-asset accounts
    low_is_good_asset_items = [
        'Accumulated Depreciation (-)',  # Lower accumulated depreciation = newer/better equipment
    ]

    # Define items where it's informational - highlight highest for visibility (not necessarily good/bad)
    # These will get green for highest but it's just to show who has the most
    informational_items = [
        'Trade Accounts Receivable',  # Shows who has most receivables
        'Receivables',  # General receivables
        'Other Receivables',  # Other receivables
        'Prepaid Expenses',  # Prepaid items
        'Related Company Receivables',  # Inter-company receivables
        'Owner Receivables',  # Amounts owed by owners
        'Other Current Assets',  # Other current asset items
        'Inter Company Receivables',  # Inter-company amounts
        'Other Assets',  # Other long-term assets
    ]

    # Define liability items where LOWER percentage is better
    # Highlight lowest in green AND above-average in yellow
    liability_items = [
        'Notes Payable - Bank',
        'Notes Payable to Owners - Current Portion',
        'Trade Accounts Payable',
        'Accrued Expenses',
        'Current Portion LTD',
        'Inter Company Payable',
        'Other Current Liabilities',
        'Total Current Liabilities',
        'Long-Term Debt',
        'Notes Payable to Owners - LT',
        'Inter Company Debt',
        'Other LT Liabilities',
        'Long Term Liabilities',
        'Total Liabilities'
    ]

    # Build table HTML with container for scrolling
    table_html = '<div class="balance-sheet-table-container"><table class="balance-sheet-table"><thead>'

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
    table_html += '<th>Balance Sheet Items</th>'
    table_html += '<th class="average-header" style="color: #ffe082;">Group Average</th>'
    for company_name in companies_with_data:
        table_html += f'<th>{company_name}</th>'
    table_html += '</tr></thead><tbody>'

    # Data rows
    for item_name, field_name, value_type in balance_sheet_items:
        # Determine row class based on item name
        if 'TOTAL' in item_name.upper():
            row_class = 'major-total-row'
        elif item_name in ["Owner's Equity", 'Total Current Assets', 'Net Fixed Assets', 'Total Current Liabilities',
                           'Long Term Liabilities', 'Total Liabilities', "Owners' Equity"]:
            row_class = 'total-row'
        else:
            row_class = ''

        table_html += f'<tr class="{row_class}">'
        table_html += f'<td>{item_name}</td>'

        # Add Group Average column
        avg_value = group_averages[item_name]
        formatted_avg = format_average(avg_value, value_type)
        table_html += f'<td class="average-cell">{formatted_avg}</td>'

        # For "high is good" items, find the winner (highest percentage)
        high_winner = None
        if item_name in high_is_good_items or item_name in informational_items:
            max_percentage = -999999
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0
                total_assets = company_total_assets[company_name]
                if total_assets > 0 and value != 0:
                    percentage = (value / total_assets) * 100
                    if percentage > max_percentage:
                        max_percentage = percentage
                        high_winner = company_name

        # For liability items, find the winner (lowest percentage)
        low_winner = None
        if item_name in liability_items:
            min_percentage = 999999
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0
                total_assets = company_total_assets[company_name]
                if total_assets > 0 and value != 0:
                    percentage = (value / total_assets) * 100
                    if percentage < min_percentage:
                        min_percentage = percentage
                        low_winner = company_name

        # For "low is good" asset items (like Accumulated Depreciation), find the winner (lowest absolute percentage)
        low_asset_winner = None
        if item_name in low_is_good_asset_items:
            min_abs_percentage = 999999
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0
                total_assets = company_total_assets[company_name]
                if total_assets > 0 and value != 0:
                    # Use absolute value since Accumulated Depreciation is negative
                    abs_percentage = (abs(value) / total_assets) * 100
                    if abs_percentage < min_abs_percentage:
                        min_abs_percentage = abs_percentage
                        low_asset_winner = company_name

        # Add data for each company
        for company_name in companies_with_data:
            value = company_data[company_name].get(field_name, 0) or 0
            total_assets = company_total_assets[company_name]
            formatted_value = format_value(value, value_type, total_assets)

            # Determine cell class
            cell_class = ''

            # Apply winner-cell class if this is the highest for a "high is good" or informational item
            if (item_name in high_is_good_items or item_name in informational_items) and company_name == high_winner:
                cell_class = 'winner-cell'

            # Apply winner-cell class if this is the lowest for a liability item
            elif item_name in liability_items and company_name == low_winner:
                cell_class = 'winner-cell'

            # Apply winner-cell class if this is the lowest for a "low is good" asset item (Accumulated Depreciation)
            elif item_name in low_is_good_asset_items and company_name == low_asset_winner:
                cell_class = 'winner-cell'

            # Apply above-average-cell class if this is a liability item and above group average
            elif item_name in liability_items:
                if total_assets > 0 and value != 0:
                    company_percentage = (value / total_assets) * 100
                    group_avg = group_averages.get(item_name, 0)
                    # Highlight if above average (worse for liabilities)
                    if company_percentage > group_avg:
                        cell_class = 'above-average-cell'

            table_html += f'<td class="{cell_class}">{formatted_value}</td>'

        table_html += '</tr>'

    table_html += '</tbody></table></div>'

    # Display table
    st.markdown(table_html, unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def fetch_all_companies_balance_sheet(period):
    """Fetch balance sheet data for all companies for a specific period"""
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

        # Fetch balance sheet data for this company
        balance_data = airtable.get_balance_sheet_data_by_period(company_name, period, is_admin=is_super_admin())

        if balance_data and len(balance_data) > 0:
            company_data[company_name] = balance_data[0]

    return company_data


def extract_balance_sheet_data_for_export(period):
    """
    Extract balance sheet data as a pandas DataFrame for Excel export.
    Shows line items as rows and companies as columns with % of Total Assets.

    Returns:
        pandas.DataFrame with balance sheet line items as rows, companies as columns
    """
    # Reuse cached data
    company_data = fetch_all_companies_balance_sheet(period)

    if not company_data:
        return None

    # Balance sheet line items (same as in create_balance_sheet_comparison_table)
    balance_sheet_items = [
        ("Owner's Equity", 'owners_equity', 'currency'),
        ('Cash and Cash Equivalents', 'cash_and_cash_equivalents', 'percent'),
        ('Trade Accounts Receivable', 'trade_accounts_receivable', 'percent'),
        ('Receivables', 'receivables', 'percent'),
        ('Other Receivables', 'other_receivables', 'percent'),
        ('Prepaid Expenses', 'prepaid_expenses', 'percent'),
        ('Related Company Receivables', 'related_company_receivables', 'percent'),
        ('Owner Receivables', 'owner_receivables', 'percent'),
        ('Other Current Assets', 'other_current_assets', 'percent'),
        ('Total Current Assets', 'total_current_assets', 'percent'),
        ('Gross Fixed Assets', 'gross_fixed_assets', 'percent'),
        ('Accumulated Depreciation (-)', 'accumulated_depreciation', 'percent_negative'),
        ('Net Fixed Assets', 'net_fixed_assets', 'percent'),
        ('Inter Company Receivables', 'inter_company_receivable', 'percent'),
        ('Other Assets', 'other_assets', 'percent'),
        ('TOTAL ASSETS', 'total_assets_calculated', 'currency_total'),
        ('Notes Payable - Bank', 'notes_payable_bank', 'percent'),
        ('Notes Payable to Owners - Current Portion', 'notes_payable_owners', 'percent'),
        ('Trade Accounts Payable', 'trade_accounts_payable', 'percent'),
        ('Accrued Expenses', 'accrued_expenses', 'percent'),
        ('Current Portion LTD', 'current_portion_ltd', 'percent'),
        ('Inter Company Payable', 'inter_company_payable', 'percent'),
        ('Other Current Liabilities', 'other_current_liabilities', 'percent'),
        ('Total Current Liabilities', 'total_current_liabilities', 'percent'),
        ('Long-Term Debt', 'long_term_debt', 'percent'),
        ('Notes Payable to Owners - LT', 'notes_payable_owners_lt', 'percent'),
        ('Inter Company Debt', 'inter_company_debt', 'percent'),
        ('Other LT Liabilities', 'other_lt_liabilities', 'percent'),
        ('Long Term Liabilities', 'total_long_term_liabilities', 'percent'),
        ('Total Liabilities', 'total_liabilities', 'percent'),
        ("Owners' Equity", 'owners_equity', 'percent'),
        ('TOTAL LIABILITIES & EQUITY', 'total_assets_calculated', 'currency_total')
    ]

    # Filter companies with data
    companies_with_data = []
    for company_name, data in company_data.items():
        has_data = False
        for item_name, field_name, value_type in balance_sheet_items:
            value = data.get(field_name, 0) or 0
            if value != 0:
                has_data = True
                break
        if has_data:
            companies_with_data.append(company_name)

    if not companies_with_data:
        return None

    # Calculate total assets for each company
    company_total_assets = {}
    for company_name in companies_with_data:
        data = company_data[company_name]
        total_assets_raw = data.get('total_assets', 0) or 0
        total_liabilities = data.get('total_liabilities', 0) or 0
        owners_equity = data.get('owners_equity', 0) or 0

        if total_assets_raw == 0 and (total_liabilities > 0 or owners_equity > 0):
            calculated_total_assets = total_liabilities + owners_equity
        else:
            calculated_total_assets = total_assets_raw

        company_total_assets[company_name] = calculated_total_assets
        company_data[company_name]['total_assets_calculated'] = calculated_total_assets

    # Build DataFrame
    data_dict = {}

    for company in sorted(companies_with_data):
        company_values = []
        total_assets = company_total_assets[company]

        for item_name, field_name, value_type in balance_sheet_items:
            value = company_data[company].get(field_name, 0) or 0

            # Format value based on type
            if value_type == 'currency':
                formatted = f'${value:,.0f}' if value != 0 else '$0'
            elif value_type == 'currency_total':
                formatted = '100%'
            elif value_type == 'percent_negative':
                if total_assets > 0 and value != 0:
                    percentage = (abs(value) / total_assets) * 100
                    formatted = f'({percentage:.1f}%)'
                else:
                    formatted = '-'
            else:  # percent
                if total_assets > 0 and value != 0:
                    percentage = (value / total_assets) * 100
                    formatted = f'{percentage:.1f}%'
                else:
                    formatted = '-'

            company_values.append(formatted)

        data_dict[company] = company_values

    # Create DataFrame
    line_item_names = [item[0] for item in balance_sheet_items]
    df = pd.DataFrame(data_dict, index=line_item_names)
    df.index.name = 'Balance Sheet Item'

    return df


def create_group_balance_sheet_page():
    """Create group balance sheet comparison page with header and period selector"""

    # Require authentication
    require_auth()

    # Initialize year selection in session state (default to most recent year)
    if 'group_balance_sheet_selected_year' not in st.session_state:
        st.session_state.group_balance_sheet_selected_year = CURRENT_YEAR

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
        page_title=f"Group Balance Sheet Comparison - {period_display}",
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
                {st.session_state.group_balance_sheet_selected_year} Balance Sheet
            </h2>
        </div>
        """, unsafe_allow_html=True)

    with col_filter:
        # Year filter - same default size as homepage selectboxes
        year_options = list(range(CURRENT_YEAR, CURRENT_YEAR - 5, -1))
        selected_year = st.selectbox(
            "**Select Year**",
            options=year_options,
            index=year_options.index(st.session_state.group_balance_sheet_selected_year) if st.session_state.group_balance_sheet_selected_year in year_options else 0,
            key="group_balance_sheet_year_selector"
        )

        # Update session state if year changed
        if selected_year != st.session_state.group_balance_sheet_selected_year:
            st.session_state.group_balance_sheet_selected_year = selected_year
            st.rerun()

    # Add some spacing
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Get Airtable connection
    conn = get_airtable_connection()

    if not conn:
        st.error("❌ Unable to connect to Airtable. Please check your credentials.")
        return

    # Get selected year from session state
    selected_year = st.session_state.group_balance_sheet_selected_year

    # Determine period filter based on selection and year
    if current_period == 'year_end':
        period_filter = f"{selected_year} Annual"
    else:
        period_filter = f"June {selected_year}"

    # Fetch balance sheet data for all companies
    with st.spinner("Loading balance sheet data..."):
        company_data = fetch_all_companies_balance_sheet(period_filter)

    if not company_data:
        st.warning(f"⚠️ No balance sheet data available for {selected_year} - {period_display}.")
        st.info("💡 Try selecting a different year or period.")
        return

    # Display the balance sheet comparison table
    create_balance_sheet_comparison_table(company_data, period_filter)


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="Group Balance Sheet - BPC Dashboard",
        page_icon="📊",
        layout="wide"
    )
    create_group_balance_sheet_page()
