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


def create_income_statement_comparison_table(company_data, period):
    """Create and display the income statement comparison table with companies as columns showing % of Total Revenue"""

    # Income statement line items matching the Income Statement Trend Table structure
    # Format: (Display Name, field_name, is_total, is_major_total)
    income_statement_items = [
        ('Revenue', 'total_revenue', True, True),
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
        ('Total Revenue', 'total_revenue', True, True),
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
        ('Advertising & Marketing', 'advertising_marketing', False, False),
        ('Bad Debts', 'bad_debts', False, False),
        ('Sales Compensation', 'sales_commissions', False, False),
        ('Contributions', 'contributions', False, False),
        ('Computer Support', 'computer_support', False, False),
        ('Dues & Subscriptions', 'dues_sub', False, False),
        ('Payroll Taxes & Benefits', 'pr_taxes_benefits', False, False),
        ('Lease Expense - Office Equipment', 'equipment_leases_office_equip', False, False),
        ("Workers' Comp. Insurance", 'workmans_comp_insurance', False, False),
        ('Insurance', 'insurance', False, False),
        ('Legal & Accounting', 'legal_accounting', False, False),
        ('Office Expense', 'office_expense', False, False),
        ('Other Administrative', 'other_admin', False, False),
        ('Pension, profit sharing, 401K', 'pension_profit_sharing_401k', False, False),
        ('Professional Fees', 'prof_fees', False, False),
        ('Repairs & Maintenance', 'repairs_maint', False, False),
        ('Salaries - Administrative', 'salaries_admin', False, False),
        ('Taxes & Licenses', 'taxes_licenses', False, False),
        ('Telephone/Fax/Utilities/Internet', 'tel_fax_utilities_internet', False, False),
        ('Travel & Entertainment', 'travel_ent', False, False),
        ('Vehicle Expense - Administrative', 'vehicle_expense_admin', False, False),
        ('Total Operating Expenses', 'total_operating_expenses', True, False),
        ('Operating Profit Margin', 'operating_profit', True, False),
        ('PPP Funds Received (forgiven)', 'ppp_forgiven', False, False),
        ('Other Income', 'other_income', False, False),
        ('CEO Comp/Perks (-)', 'ceo_comp', False, False),
        ('Other Expense (-)', 'other_expense', False, False),
        ('Interest Expense (-)', 'interest_expense', False, False),
        ('Total Other Income / Expense', 'total_nonoperating_income', True, False),
        ('Net Profit Margin', 'net_profit', True, False)
    ]

    # Get sorted list of companies (excluding companies with no data)
    companies_with_data = []
    for company_name, data in company_data.items():
        # Check if company has at least one non-zero field
        has_data = False
        for item_name, field_name, is_total, is_major_total in income_statement_items:
            value = data.get(field_name, 0) or 0
            if value != 0:
                has_data = True
                break
        if has_data:
            companies_with_data.append(company_name)

    # Sort by rank (rank 1 on the right)
    companies_with_data = sort_companies_by_rank(companies_with_data, period)

    if not companies_with_data:
        st.warning("⚠️ No companies have income statement data for the selected period.")
        return

    # Calculate total revenue for each company
    company_total_revenue = {}
    for company_name in companies_with_data:
        data = company_data[company_name]
        total_revenue = data.get('total_revenue', 0) or 0
        company_total_revenue[company_name] = total_revenue

    # Calculate group averages for each line item
    group_averages = {}

    for item_name, field_name, is_total, is_major_total in income_statement_items:
        if item_name == 'Revenue':
            # For Revenue header, calculate average dollar amount
            values = [company_data[comp].get('total_revenue', 0) or 0
                     for comp in companies_with_data]
            valid_values = [v for v in values if v != 0]
            group_averages[item_name] = sum(valid_values) / len(valid_values) if valid_values else 0

        elif item_name == 'Total Revenue':
            # Always 100%
            group_averages[item_name] = 100

        else:
            # For percentages, calculate average percentage
            percentages = []
            for comp in companies_with_data:
                value = company_data[comp].get(field_name, 0) or 0
                total_revenue = company_total_revenue[comp]
                if total_revenue > 0 and value != 0:
                    pct = (value / total_revenue) * 100
                    percentages.append(pct)
            group_averages[item_name] = sum(percentages) / len(percentages) if percentages else 0

    # Helper function to format values based on type
    def format_value(value, item_name, field_name, total_revenue):
        if value is None:
            return '-'

        if item_name == 'Revenue':
            # Show dollar amount for Revenue header row
            if value == 0:
                return '$0'
            return f'${value:,.0f}'
        elif item_name == 'Total Revenue':
            # Show 100% for Total Revenue
            return '100%' if total_revenue > 0 else '-'
        else:
            # Calculate percentage of total revenue
            if total_revenue > 0 and value != 0:
                percentage = (value / total_revenue) * 100
                return f'{percentage:.1f}%'
            else:
                return '-'

    # Helper function to format average values
    def format_average(avg_value, item_name):
        if avg_value == 0:
            return '-'

        if item_name == 'Revenue':
            return f'${avg_value:,.0f}'
        elif item_name == 'Total Revenue':
            return '100%'
        else:
            return f'{avg_value:.1f}%'

    # Display color coding
    st.markdown("""
    <div style="background-color: #f7fafc; border-left: 4px solid #025a9a; padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px;">
        <div style="display: grid; grid-template-columns: auto 1fr; gap: 0.5rem; align-items: center;">
            <div style="background-color: #c6f6d5; padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; text-align: center;">
                Green
            </div>
            <div style="color: #1a202c; font-family: 'Montserrat', sans-serif;">
                <strong>Leading Agent</strong> - Highest percentage for revenue and other income items (e.g., Intra State HHG, Other Income)
            </div>
            <div style="background-color: #ffe082; padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; text-align: center;">
                Yellow
            </div>
            <div style="color: #1a202c; font-family: 'Montserrat', sans-serif;">
                <strong>Above Group Average</strong> - Expense percentage exceeds group average for all cost and expense items
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CSS styling
    st.markdown("""
    <style>
    .income-statement-table-container {
        max-height: 800px;
        overflow-x: auto;
        overflow-y: auto;
        position: relative;
        margin: 1rem 0;
    }
    .income-statement-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.0rem;
        border: 1px solid white;
    }
    .income-statement-table thead {
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .income-statement-table th {
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
    .income-statement-table th:first-child {
        text-align: left;
        min-width: 200px;
        max-width: 200px;
        position: sticky;
        left: 0;
        z-index: 30;
        background-color: #025a9a;
    }
    .income-statement-table th.average-header {
        text-align: center;
    }
    .income-statement-table td {
        padding: 10px 8px;
        border: 1px solid white;
        text-align: center;
        background-color: white;
        font-size: 1.0rem;
    }
    .income-statement-table td:first-child {
        text-align: left;
        font-weight: 500;
        background-color: white;
        position: sticky;
        left: 0;
        z-index: 20;
        padding-left: 15px;
        font-size: 1.0rem;
    }
    .income-statement-table td.average-cell {
        background-color: #e6f7ff;
        font-weight: 600;
        text-align: center;
    }
    .income-statement-table tr.header-row td {
        background-color: #4a5568 !important;
        color: white;
        font-weight: 700;
        text-align: left;
    }
    .income-statement-table tr.header-row td:first-child {
        background-color: #4a5568 !important;
    }
    .income-statement-table tr.total-row td {
        background-color: #e2e8f0;
        font-weight: 600;
    }
    .income-statement-table tr.total-row td:first-child {
        background-color: #e2e8f0;
    }
    .income-statement-table tr.total-row td.average-cell {
        background-color: #b8e6ff;
        font-weight: 700;
    }
    .income-statement-table tr.major-total-row td {
        background-color: #cbd5e0;
        font-weight: 700;
    }
    .income-statement-table tr.major-total-row td:first-child {
        background-color: #cbd5e0;
    }
    .income-statement-table tr.major-total-row td.average-cell {
        background-color: #9cd9ff;
        font-weight: 700;
    }
    .income-statement-table .overall-rank-row {
        background-color: #025a9a;
        font-weight: 700;
        font-size: 1.05rem;
        box-shadow: 0 2px 4px rgba(2, 90, 154, 0.3);
        border-bottom: 3px solid white;
    }
    .income-statement-table .overall-rank-row td {
        background-color: #025a9a !important;
        color: white;
        font-weight: 700;
        font-size: 1.05rem;
        text-align: center;
    }
    .income-statement-table .overall-rank-row td:first-child {
        background-color: #025a9a !important;
        text-align: left;
    }
    .income-statement-table tr:hover:not(.header-row) td {
        background-color: #edf2f7;
    }
    .income-statement-table tr:hover:not(.header-row) td.average-cell {
        background-color: #d0efff;
    }
    .income-statement-table td.winner-cell {
        background-color: #c6f6d5 !important;
        font-weight: 700 !important;
    }
    .income-statement-table td.above-average-cell {
        background-color: #ffe082 !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Build table HTML with container for scrolling
    table_html = '<div class="income-statement-table-container"><table class="income-statement-table"><thead>'

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
    table_html += '<th>Income Statement Items</th>'
    table_html += '<th class="average-header" style="color: #ffe082;">Group Average</th>'
    for company_name in companies_with_data:
        table_html += f'<th>{company_name}</th>'
    table_html += '</tr></thead><tbody>'

    # Define revenue line items that should have winners highlighted
    revenue_line_items = [
        'Intra State HHG', 'Local HHG', 'Inter State HHG', 'Office & Industrial',
        'Warehouse (Non-commercial)', 'Warehouse handling (Non-commercial)', 'International',
        'Packing & Unpacking', 'Booking & Royalties', 'Special Products', 'Records Storage',
        'Military DPM Contracts', 'Distribution', 'Hotel Deliveries', 'Other Revenue'
    ]

    # Define expense line items (cost of revenue items - after Total Revenue until Gross Profit Margin)
    # PLUS operating expenses (after Gross Profit Margin until Operating Profit Margin)
    expense_line_items = [
        # Cost of Revenue items
        'Direct Wages', 'Vehicle Operating Expense', 'Packing & Warehouse Supplies',
        'Owner Operator - Intra State', 'Owner Operator - Inter State',
        'Owner Operator - Office & Industrial', 'Owner Operator - Packing',
        'Owner Operator - General & Other', 'Claims', 'Other Transportation Expense',
        'Lease Expense - Revenue Equipment', 'Other Direct Expenses',
        'Rent and/or Building Expense', 'Depreciation/Amortization', 'Total Cost Of Revenue',
        # Operating Expense items
        'Advertising & Marketing', 'Bad Debts', 'Sales Compensation', 'Contributions',
        'Computer Support', 'Dues & Subscriptions', 'Payroll Taxes & Benefits',
        'Lease Expense - Office Equipment', "Workers' Comp. Insurance", 'Insurance',
        'Legal & Accounting', 'Office Expense', 'Other Administrative',
        'Pension, profit sharing, 401K', 'Professional Fees', 'Repairs & Maintenance',
        'Salaries - Administrative', 'Taxes & Licenses', 'Telephone/Fax/Utilities/Internet',
        'Travel & Entertainment', 'Vehicle Expense - Administrative', 'Total Operating Expenses',
        # Other Expense items (shown as negative values in the table)
        'CEO Comp/Perks (-)', 'Other Expense (-)', 'Interest Expense (-)'
    ]

    # Define other income line items (higher percentage is better, like revenue)
    other_income_line_items = [
        'PPP Funds Received (forgiven)', 'Other Income'
    ]

    # Data rows
    for item_name, field_name, is_total, is_major_total in income_statement_items:
        # Determine row class based on item type
        if is_major_total:
            row_class = 'major-total-row'
        elif is_total:
            row_class = 'total-row'
        else:
            row_class = ''

        table_html += f'<tr class="{row_class}">'
        table_html += f'<td>{item_name}</td>'

        # Add Group Average column
        avg_value = group_averages[item_name]
        formatted_avg = format_average(avg_value, item_name)
        table_html += f'<td class="average-cell">{formatted_avg}</td>'

        # For revenue line items, find the winner (highest percentage value)
        winner_company = None
        if item_name in revenue_line_items:
            max_percentage = 0
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0
                total_revenue = company_total_revenue[company_name]
                if total_revenue > 0 and value != 0:
                    percentage = (value / total_revenue) * 100
                    if percentage > max_percentage:
                        max_percentage = percentage
                        winner_company = company_name

        # For other income line items, also find the winner (highest percentage value)
        other_income_winner = None
        if item_name in other_income_line_items:
            max_percentage = 0
            for company_name in companies_with_data:
                value = company_data[company_name].get(field_name, 0) or 0
                total_revenue = company_total_revenue[company_name]
                if total_revenue > 0 and value != 0:
                    percentage = (value / total_revenue) * 100
                    if percentage > max_percentage:
                        max_percentage = percentage
                        other_income_winner = company_name

        # Add data for each company
        for company_name in companies_with_data:
            value = company_data[company_name].get(field_name, 0) or 0
            total_revenue = company_total_revenue[company_name]
            formatted_value = format_value(value, item_name, field_name, total_revenue)

            # Determine cell class
            cell_class = ''

            # Apply winner-cell class if this is the winner for a revenue line item
            if item_name in revenue_line_items and company_name == winner_company:
                cell_class = 'winner-cell'

            # Apply winner-cell class if this is the winner for an other income line item
            elif item_name in other_income_line_items and company_name == other_income_winner:
                cell_class = 'winner-cell'

            # Apply above-average-cell class if this is an expense item and value is above group average
            elif item_name in expense_line_items:
                # Calculate this company's percentage
                if total_revenue > 0 and value != 0:
                    company_percentage = (value / total_revenue) * 100
                    group_avg = group_averages.get(item_name, 0)

                    # For expense items shown as negative (CEO Comp, Other Expense, Interest Expense),
                    # "worse" means more negative (i.e., company_percentage < group_avg)
                    # For regular expense items, "worse" means higher positive value (i.e., company_percentage > group_avg)
                    if item_name in ['CEO Comp/Perks (-)', 'Other Expense (-)', 'Interest Expense (-)']:
                        # Highlight if more negative than average (worse for negative expenses)
                        if company_percentage < group_avg:
                            cell_class = 'above-average-cell'
                    else:
                        # Highlight if above average (worse for regular expenses)
                        if company_percentage > group_avg:
                            cell_class = 'above-average-cell'

            table_html += f'<td class="{cell_class}">{formatted_value}</td>'

        table_html += '</tr>'

    table_html += '</tbody></table></div>'

    # Display table
    st.markdown(table_html, unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def fetch_all_companies_income_statement(period):
    """Fetch income statement data for all companies for a specific period"""
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

        # Fetch income statement data for this company
        income_data = airtable.get_income_statement_data_by_period(company_name, period)

        if income_data and len(income_data) > 0:
            company_data[company_name] = income_data[0]

    return company_data


def extract_income_statement_data_for_export(period):
    """
    Extract income statement data as a pandas DataFrame for Excel export.
    Shows line items as rows and companies as columns with % of Total Revenue.

    Returns:
        pandas.DataFrame with income statement line items as rows, companies as columns
    """
    # Reuse cached data
    company_data = fetch_all_companies_income_statement(period)

    if not company_data:
        return None

    # Income statement line items (same structure as table)
    income_statement_items = [
        ('Revenue', 'total_revenue', True, True),
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
        ('Total Revenue', 'total_revenue', True, True),
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
        ('Advertising & Marketing', 'advertising_marketing', False, False),
        ('Bad Debts', 'bad_debts', False, False),
        ('Sales Compensation', 'sales_commissions', False, False),
        ('Contributions', 'contributions', False, False),
        ('Computer Support', 'computer_support', False, False),
        ('Dues & Subscriptions', 'dues_sub', False, False),
        ('Payroll Taxes & Benefits', 'pr_taxes_benefits', False, False),
        ('Lease Expense - Office Equipment', 'equipment_leases_office_equip', False, False),
        ("Workers' Comp. Insurance", 'workmans_comp_insurance', False, False),
        ('Insurance', 'insurance', False, False),
        ('Legal & Accounting', 'legal_accounting', False, False),
        ('Office Expense', 'office_expense', False, False),
        ('Other Administrative', 'other_admin', False, False),
        ('Pension, profit sharing, 401K', 'pension_profit_sharing_401k', False, False),
        ('Professional Fees', 'prof_fees', False, False),
        ('Repairs & Maintenance', 'repairs_maint', False, False),
        ('Salaries - Administrative', 'salaries_admin', False, False),
        ('Taxes & Licenses', 'taxes_licenses', False, False),
        ('Telephone/Fax/Utilities/Internet', 'tel_fax_utilities_internet', False, False),
        ('Travel & Entertainment', 'travel_ent', False, False),
        ('Vehicle Expense - Administrative', 'vehicle_expense_admin', False, False),
        ('Total Operating Expenses', 'total_operating_expenses', True, False),
        ('Operating Profit Margin', 'operating_profit', True, False),
        ('PPP Funds Received (forgiven)', 'ppp_forgiven', False, False),
        ('Other Income', 'other_income', False, False),
        ('CEO Comp/Perks (-)', 'ceo_comp', False, False),
        ('Other Expense (-)', 'other_expense', False, False),
        ('Interest Expense (-)', 'interest_expense', False, False),
        ('Total Other Income / Expense', 'total_nonoperating_income', True, False),
        ('Net Profit Margin', 'net_profit', True, False)
    ]

    # Filter companies with data
    companies_with_data = []
    for company_name, data in company_data.items():
        has_data = False
        for item_name, field_name, is_total, is_major_total in income_statement_items:
            value = data.get(field_name, 0) or 0
            if value != 0:
                has_data = True
                break
        if has_data:
            companies_with_data.append(company_name)

    if not companies_with_data:
        return None

    # Calculate total revenue for each company
    company_total_revenue = {}
    for company_name in companies_with_data:
        data = company_data[company_name]
        total_revenue = data.get('total_revenue', 0) or 0
        company_total_revenue[company_name] = total_revenue

    # Build DataFrame
    data_dict = {}

    for company in sorted(companies_with_data):
        company_values = []
        total_revenue = company_total_revenue[company]

        for item_name, field_name, is_total, is_major_total in income_statement_items:
            value = company_data[company].get(field_name, 0) or 0

            # Format value based on item type
            if item_name == 'Revenue':
                formatted = f'${value:,.0f}' if value != 0 else '$0'
            elif item_name == 'Total Revenue':
                formatted = '100%' if total_revenue > 0 else '-'
            else:
                if total_revenue > 0 and value != 0:
                    percentage = (value / total_revenue) * 100
                    formatted = f'{percentage:.1f}%'
                else:
                    formatted = '-'

            company_values.append(formatted)

        data_dict[company] = company_values

    # Create DataFrame
    line_item_names = [item[0] for item in income_statement_items]
    df = pd.DataFrame(data_dict, index=line_item_names)
    df.index.name = 'Income Statement Item'

    return df


def create_group_income_statement_page():
    """Create group income statement comparison page with header and period selector"""

    # Require authentication
    require_auth()

    # Initialize year selection in session state (default to most recent year)
    if 'group_income_statement_selected_year' not in st.session_state:
        st.session_state.group_income_statement_selected_year = 2024

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
        page_title=f"Group Income Statement Comparison - {period_display}",
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
                {st.session_state.group_income_statement_selected_year} Income Statement
            </h2>
        </div>
        """, unsafe_allow_html=True)

    with col_filter:
        # Year filter - same default size as homepage selectboxes
        year_options = [2024, 2023, 2022, 2021, 2020]
        selected_year = st.selectbox(
            "**Select Year**",
            options=year_options,
            index=year_options.index(st.session_state.group_income_statement_selected_year) if st.session_state.group_income_statement_selected_year in year_options else 0,
            key="group_income_statement_year_selector"
        )

        # Update session state if year changed
        if selected_year != st.session_state.group_income_statement_selected_year:
            st.session_state.group_income_statement_selected_year = selected_year
            st.rerun()

    # Add some spacing
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Get Airtable connection
    conn = get_airtable_connection()

    if not conn:
        st.error("❌ Unable to connect to Airtable. Please check your credentials.")
        return

    # Get selected year from session state
    selected_year = st.session_state.group_income_statement_selected_year

    # Determine period filter based on selection and year
    if current_period == 'year_end':
        period_filter = f"{selected_year} Annual"
    else:
        period_filter = f"June {selected_year}"

    # Fetch income statement data for all companies
    with st.spinner("Loading income statement data..."):
        company_data = fetch_all_companies_income_statement(period_filter)

    if not company_data:
        st.warning(f"⚠️ No income statement data available for {selected_year} - {period_display}.")
        st.info("💡 Try selecting a different year or period.")
        return

    # Display the income statement comparison table
    create_income_statement_comparison_table(company_data, period_filter)


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="Group Income Statement - BPC Dashboard",
        page_icon="📊",
        layout="wide"
    )
    create_group_income_statement_page()
