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
from shared.page_components import create_page_header, get_period_display_text
from shared.auth_utils import require_auth
from shared.cash_flow_utils import get_cash_flow_ratios

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def fetch_group_ratio_data(period):
    """Fetch all companies' ratio data for 2024"""
    airtable = get_airtable_connection()

    # Get all companies from shared cache
    from shared.airtable_connection import get_companies_cached
    companies = get_companies_cached()

    if not companies:
        st.warning("⚠️ Could not fetch companies list from Airtable")
        return None

    # Build dictionary with company names as keys
    ratio_data = {}

    # Fetch data for each company individually
    for company in companies:
        company_name = company.get('name')
        if not company_name:
            continue

        # Get balance sheet and income statement data for this company
        balance_data = airtable.get_balance_sheet_data_by_period(company_name, period)
        income_data = airtable.get_income_statement_data_by_period(company_name, period)

        # Initialize company entry
        if company_name not in ratio_data:
            ratio_data[company_name] = {}

        # Extract balance sheet ratios
        if balance_data and len(balance_data) > 0:
            balance_record = balance_data[0]
            ratio_data[company_name].update({
                'current_ratio': balance_record.get('current_ratio', 0),
                'debt_to_equity': balance_record.get('debt_to_equity', 0),
                'working_capital_pct': balance_record.get('working_capital_pct_asset', 0),
                'survival_score': balance_record.get('survival_score', 0),
                'dso': balance_record.get('dso', 0)
            })

            # Calculate cash flow ratios using centralized function (replaces Airtable values)
            year = period.split()[0]  # Extract year from "2024 Annual"
            cf_ratios = get_cash_flow_ratios(airtable, company_name, year)
            ratio_data[company_name].update({
                'ocf_rev': cf_ratios.get('ocf_rev') or 0,
                'fcf_rev': cf_ratios.get('fcf_rev') or 0,
                'ncf_rev': cf_ratios.get('ncf_rev') or 0
            })

        # Extract income statement ratios
        if income_data and len(income_data) > 0:
            income_record = income_data[0]
            ratio_data[company_name].update({
                'gpm': income_record.get('gpm', 0),
                'opm': income_record.get('opm', 0),
                'npm': income_record.get('npm', 0),
                'rev_per_employee': income_record.get('rev_admin_employee', 0),
                'ebitda_margin': income_record.get('ebitda_margin', 0),
                'sales_assets': income_record.get('sales_assets', 0) or 0
            })

    if not ratio_data:
        st.warning(f"⚠️ No ratio data found for period: {period}")
        return None

    return ratio_data


def extract_ratios_data_for_export(period):
    """
    Extract ratio data as a pandas DataFrame for Excel export.
    Reuses the cached fetch_group_ratio_data function.

    Returns:
        pandas.DataFrame with ratios as rows and companies as columns
        Includes formatted values (e.g., "2.5", "15.3%", "$580K")
    """
    # Reuse cached data
    ratio_data = fetch_group_ratio_data(period)

    if not ratio_data:
        return None

    # Define all metrics in the order they appear on the page
    metrics = [
        # Asset & Liability Mgmt
        {'name': 'Current Ratio', 'key': 'current_ratio', 'format': 'ratio'},
        {'name': 'Debt to Equity', 'key': 'debt_to_equity', 'format': 'ratio'},
        {'name': 'Working Capital %', 'key': 'working_capital_pct', 'format': 'percent'},
        {'name': 'Survival Score', 'key': 'survival_score', 'format': 'ratio'},
        {'name': 'Sales/Assets', 'key': 'sales_assets', 'format': 'ratio'},
        # Profitability Mgmt
        {'name': 'Gross Profit Margin', 'key': 'gpm', 'format': 'percent'},
        {'name': 'Operating Profit Margin', 'key': 'opm', 'format': 'percent'},
        {'name': 'Net Profit Margin', 'key': 'npm', 'format': 'percent'},
        {'name': 'Revenue Per Employee', 'key': 'rev_per_employee', 'format': 'currency_k'},
        {'name': 'EBITDA/Revenue', 'key': 'ebitda_margin', 'format': 'percent'},
        # Cash Flow Mgmt
        {'name': 'Days Sales Outstanding (DSO)', 'key': 'dso', 'format': 'days'},
        {'name': 'OCF/Revenue', 'key': 'ocf_rev', 'format': 'percent'},
        {'name': 'FCF/Revenue', 'key': 'fcf_rev', 'format': 'percent'},
        {'name': 'NCF/Revenue', 'key': 'ncf_rev', 'format': 'percent'},
    ]

    # Get list of companies
    companies = sorted(ratio_data.keys())

    # Build data dictionary for DataFrame
    data_dict = {}

    for company in companies:
        company_metrics = ratio_data[company]
        formatted_values = []

        for metric in metrics:
            value = company_metrics.get(metric['key'], 0) or 0
            formatted = format_metric_value(value, metric['key'])
            formatted_values.append(formatted)

        data_dict[company] = formatted_values

    # Create DataFrame with metric names as index
    metric_names = [m['name'] for m in metrics]
    df = pd.DataFrame(data_dict, index=metric_names)
    df.index.name = 'Ratio'

    return df


def calculate_rankings(ratio_data, metric_name, reverse=False):
    """Calculate rankings for a specific metric across all companies"""
    # Extract values for the metric
    company_values = []
    for company, metrics in ratio_data.items():
        value = metrics.get(metric_name, 0)
        if value is not None and value != 0:  # Only include valid values
            company_values.append((company, value))

    # Sort based on reverse parameter
    if reverse:
        # Lower is better (e.g., debt_to_equity)
        # BUT: negative values are worst (indicate negative equity)
        positive_values = [(c, v) for c, v in company_values if v >= 0]
        negative_values = [(c, v) for c, v in company_values if v < 0]

        # Sort positives ascending (lower is better)
        positive_values.sort(key=lambda x: x[1])
        # Sort negatives descending (more negative is worse)
        negative_values.sort(key=lambda x: x[1], reverse=True)

        # Combine: positive values first (best ranks), then negative values (worst ranks)
        company_values = positive_values + negative_values
    else:
        # Higher is better (most metrics)
        company_values.sort(key=lambda x: x[1], reverse=True)

    # Assign ranks
    rankings = {}
    for rank, (company, value) in enumerate(company_values, start=1):
        rankings[company] = rank

    return rankings


def calculate_bpc2_average(ratio_data, metric_name):
    """Calculate BPC2 average for a specific metric"""
    values = []
    for company, metrics in ratio_data.items():
        value = metrics.get(metric_name, 0)
        if value is not None and value != 0:  # Only include valid values
            values.append(value)

    if values:
        return sum(values) / len(values)
    return 0


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def calculate_group_rankings(period):
    """
    Centralized function to calculate group rankings and scores.
    Used by both the group ratios page and home page for consistency.

    Returns dictionary with company rankings, scores, and timestamp.
    """
    # Fetch ratio data
    ratio_data = fetch_group_ratio_data(period)

    if not ratio_data:
        return None

    companies_list = sorted(ratio_data.keys())

    # Define all metrics
    al_metrics = [
        {'key': 'current_ratio', 'reverse': False},
        {'key': 'debt_to_equity', 'reverse': True},
        {'key': 'working_capital_pct', 'reverse': False},
        {'key': 'survival_score', 'reverse': False},
        {'key': 'sales_assets', 'reverse': False},
    ]

    prof_metrics = [
        {'key': 'gpm', 'reverse': False},
        {'key': 'opm', 'reverse': False},
        {'key': 'npm', 'reverse': False},
        {'key': 'rev_per_employee', 'reverse': False},
        {'key': 'ebitda_margin', 'reverse': False},
    ]

    cf_metrics = [
        {'key': 'dso', 'reverse': True},
        {'key': 'ocf_rev', 'reverse': False},
        {'key': 'fcf_rev', 'reverse': False},
        {'key': 'ncf_rev', 'reverse': False},
    ]

    # Calculate Asset & Liability Mgmt Points
    asset_liability_points = {}
    for company in companies_list:
        total_points = 0
        for metric in al_metrics:
            rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
            rank = rankings.get(company, 0)
            if rank and rank != '-':
                total_points += rank
        asset_liability_points[company] = total_points

    # Calculate Profitability Mgmt Points
    profitability_points = {}
    for company in companies_list:
        total_points = 0
        for metric in prof_metrics:
            rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
            rank = rankings.get(company, 0)
            if rank and rank != '-':
                total_points += rank
        profitability_points[company] = total_points

    # Calculate Cash Flow Mgmt Points and Weighted Points
    cash_flow_points = {}
    for company in companies_list:
        total_points = 0
        for metric in cf_metrics:
            rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
            rank = rankings.get(company, 0)
            if rank and rank != '-':
                total_points += rank
        cash_flow_points[company] = total_points

    weighted_values = {}
    for company in companies_list:
        points = cash_flow_points.get(company, 0)
        weighted_values[company] = points / 2 if points > 0 else 0

    # Calculate Total Score
    total_scores = {}
    for company in companies_list:
        al_points = asset_liability_points.get(company, 0)
        prof_points = profitability_points.get(company, 0)
        cf_weighted = weighted_values.get(company, 0)
        total_scores[company] = al_points + prof_points + cf_weighted

    # Calculate overall rankings (lowest score = rank 1)
    sorted_total_scores = sorted(total_scores.items(), key=lambda x: x[1])
    overall_rankings = {}
    for rank, (company, score) in enumerate(sorted_total_scores, start=1):
        if score > 0:
            overall_rankings[company] = rank

    return {
        'rankings': overall_rankings,
        'scores': total_scores,
        'asset_liability_points': asset_liability_points,
        'profitability_points': profitability_points,
        'cash_flow_points': cash_flow_points,
        'weighted_values': weighted_values,
        'timestamp': datetime.now()
    }


def get_cell_color(value, metric_name):
    """Get background color for table cell based on metric value and thresholds"""
    if value is None or value == '' or value == 0:
        return '#f8f9fa'  # Light gray for missing data

    # Define thresholds for each metric
    # Note: Percentage metrics (gpm, opm, ebitda_margin) use decimal values (0.25 = 25%)
    thresholds = {
        'current_ratio': {'great': 2.4, 'caution': [1.5, 2.3], 'improve': 1.5},
        'debt_to_equity': {'great': 1.1, 'caution': [1.2, 1.7], 'improve': 1.7, 'reverse': True},
        'working_capital_pct': {'great': 0.35, 'caution': [0.20, 0.35], 'improve': 0.20},  # 35% = 0.35
        'survival_score': {'great': 3.0, 'caution': [2.0, 3.0], 'improve': 2.0},
        'sales_assets': {'great': 3.7, 'caution': [2.0, 3.6], 'improve': 2.0},
        'gpm': {'great': 0.25, 'caution': [0.20, 0.2499], 'improve': 0.20},
        'opm': {'great': 0.065, 'caution': [0.04, 0.0649], 'improve': 0.04},
        'rev_per_employee': {'great': 550, 'caution': [325, 549], 'improve': 325},
        'ebitda_margin': {'great': 0.05, 'caution': [0.03, 0.0499], 'improve': 0.025},
        'dso': {'great': 40, 'caution': [40, 60], 'improve': 60, 'reverse': True},
        'ocf_rev': {'great': 0.005, 'caution': [-0.005, 0.005], 'improve': -0.005},  # 0.5% = 0.005
    }

    if metric_name not in thresholds:
        return '#ffffff'  # White for unknown metrics

    threshold = thresholds[metric_name]
    is_reverse = threshold.get('reverse', False)

    try:
        val = float(value)

        if is_reverse:
            # Lower is better
            if val <= threshold['great']:
                return '#c8e6c9'  # Green
            elif isinstance(threshold['caution'], list) and threshold['caution'][0] <= val <= threshold['caution'][1]:
                return '#fff3c4'  # Yellow
            else:
                return '#ffcdd2'  # Red
        else:
            # Higher is better
            if val >= threshold['great']:
                return '#c8e6c9'  # Green
            elif isinstance(threshold['caution'], list) and threshold['caution'][0] <= val <= threshold['caution'][1]:
                return '#fff3c4'  # Yellow
            else:
                return '#ffcdd2'  # Red
    except (ValueError, TypeError):
        return '#f8f9fa'


def format_metric_value(value, metric_name):
    """Format metric values for display"""
    if value is None or value == '' or value == 0:
        return '-'

    try:
        val = float(value)

        if metric_name in ['current_ratio', 'debt_to_equity', 'survival_score', 'sales_assets']:
            return f"{val:.1f}"
        elif metric_name == 'dso':
            # DSO formatted as whole number (no decimals)
            return f"{int(val)}"
        elif metric_name in ['working_capital_pct', 'gpm', 'opm', 'npm', 'ebitda_margin']:
            # Convert to percentage if needed
            if val <= 1:
                return f"{val * 100:.1f}%"
            else:
                return f"{val:.1f}%"
        elif metric_name == 'rev_per_employee':
            # Format as currency in thousands
            return f"${val / 1000:.0f}K" if val >= 1000 else f"${val:.0f}"
        elif metric_name in ['ocf_rev', 'fcf_rev', 'ncf_rev']:
            # Cash flow as percentage of revenue - values are already percentages (0.1 = 10%)
            # Display with % sign and 1 decimal place
            return f"{val * 100:.1f}%"
        else:
            return f"{val:.2f}"
    except (ValueError, TypeError):
        return '-'


def create_group_ratio_table(ratio_data):
    """Create and display the group ratio comparison table with proper styling"""

    # Filter out companies with no valid data (all metrics are 0 or None)
    # This excludes companies like Bisson and Hopkins when viewing historical years
    filtered_ratio_data = {}
    for company, metrics in ratio_data.items():
        # Check if company has at least one non-zero metric
        has_data = False
        for key, value in metrics.items():
            if value is not None and value != 0:
                has_data = True
                break

        # Only include companies with actual data
        if has_data:
            filtered_ratio_data[company] = metrics

    # If no companies have data, show message and return
    if not filtered_ratio_data:
        st.warning("⚠️ No companies have data for the selected period.")
        return

    # Get sorted list of companies (only those with data)
    companies_list = sorted(filtered_ratio_data.keys())

    # Update ratio_data to use filtered data for all subsequent calculations
    ratio_data = filtered_ratio_data

    # Calculate overall rankings first to sort companies
    # We need to calculate all metrics, points, and total scores to determine final ranking

    # Define all metrics
    al_metrics = [
        {'key': 'current_ratio', 'reverse': False},
        {'key': 'debt_to_equity', 'reverse': True},
        {'key': 'working_capital_pct', 'reverse': False},
        {'key': 'survival_score', 'reverse': False},
        {'key': 'sales_assets', 'reverse': False},
    ]

    prof_metrics = [
        {'key': 'gpm', 'reverse': False},
        {'key': 'opm', 'reverse': False},
        {'key': 'npm', 'reverse': False},
        {'key': 'rev_per_employee', 'reverse': False},
        {'key': 'ebitda_margin', 'reverse': False},
    ]

    cf_metrics = [
        {'key': 'dso', 'reverse': True},
        {'key': 'ocf_rev', 'reverse': False},
        {'key': 'fcf_rev', 'reverse': False},
        {'key': 'ncf_rev', 'reverse': False},
    ]

    # Calculate Asset & Liability Mgmt Points
    asset_liability_points_calc = {}
    for company in companies_list:
        total_points = 0
        for metric in al_metrics:
            rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
            rank = rankings.get(company, 0)
            if rank and rank != '-':
                total_points += rank
        asset_liability_points_calc[company] = total_points

    # Calculate Profitability Mgmt Points
    profitability_points_calc = {}
    for company in companies_list:
        total_points = 0
        for metric in prof_metrics:
            rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
            rank = rankings.get(company, 0)
            if rank and rank != '-':
                total_points += rank
        profitability_points_calc[company] = total_points

    # Calculate Cash Flow Mgmt Points and Weighted Points
    cash_flow_points_calc = {}
    for company in companies_list:
        total_points = 0
        for metric in cf_metrics:
            rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
            rank = rankings.get(company, 0)
            if rank and rank != '-':
                total_points += rank
        cash_flow_points_calc[company] = total_points

    weighted_values_calc = {}
    for company in companies_list:
        points = cash_flow_points_calc.get(company, 0)
        weighted_values_calc[company] = points / 2 if points > 0 else 0

    # Calculate Total Score
    total_scores_calc = {}
    for company in companies_list:
        al_points = asset_liability_points_calc.get(company, 0)
        prof_points = profitability_points_calc.get(company, 0)
        cf_weighted = weighted_values_calc.get(company, 0)
        total_scores_calc[company] = al_points + prof_points + cf_weighted

    # Sort companies by total score (lowest is best) - rank 1 on the left, rank 10 on the right
    sorted_companies_by_rank = sorted(total_scores_calc.items(), key=lambda x: x[1])
    companies = [company for company, score in sorted_companies_by_rank]

    # Define metric definitions
    metrics = [
        {'name': 'Current Ratio', 'key': 'current_ratio', 'standard': '3.0', 'green': '2.4 & above', 'yellow': '1.5 to 2.3', 'red': 'Below 1.3', 'reverse': False},
        {'name': 'Debt to Equity', 'key': 'debt_to_equity', 'standard': '1.0', 'green': '0 to 1.1', 'yellow': '1.2 to 1.7', 'red': 'Above 3.0', 'reverse': True},
        {'name': 'Working Capital as % of Total Assets', 'key': 'working_capital_pct', 'standard': '45%', 'green': '36% & above', 'yellow': '15% to 35%', 'red': 'Below 15%', 'reverse': False},
        {'name': 'Survival Score', 'key': 'survival_score', 'standard': '5.0', 'green': '3.0 & above', 'yellow': '2.0 to 3.0', 'red': 'Below 2.0', 'reverse': False},
        {'name': 'Sales/Assets', 'key': 'sales_assets', 'standard': '10%', 'green': '', 'yellow': '', 'red': '', 'reverse': False},
    ]

    income_metrics = [
        {'name': 'Gross Profit Margin', 'key': 'gpm', 'standard': 'N/A', 'green': '', 'yellow': '', 'red': '', 'reverse': False},
        {'name': 'Operating Profit Margin', 'key': 'opm', 'standard': 'N/A', 'green': '', 'yellow': '', 'red': '', 'reverse': False},
        {'name': 'Net Profit Margin', 'key': 'npm', 'standard': 'N/A', 'green': '', 'yellow': '', 'red': '', 'reverse': False},
        {'name': 'Revenue Per Employee', 'key': 'rev_per_employee', 'standard': 'N/A', 'green': '', 'yellow': '', 'red': '', 'reverse': False},
        {'name': 'EBITDA/Revenue', 'key': 'ebitda_margin', 'standard': 'N/A', 'green': '', 'yellow': '', 'red': '', 'reverse': False},
    ]

    cash_flow_metrics = [
        {'name': 'Days Sales Outstanding (DSO)', 'key': 'dso', 'standard': 'N/A', 'green': '', 'yellow': '', 'red': '', 'reverse': True},
        {'name': 'Operating Cash Flow (OCF)/Revenue', 'key': 'ocf_rev', 'standard': 'N/A', 'green': '', 'yellow': '', 'red': '', 'reverse': False},
        {'name': 'Financing Cash Flow (FCF)/Revenue', 'key': 'fcf_rev', 'standard': 'N/A', 'green': '', 'yellow': '', 'red': '', 'reverse': False},
        {'name': 'Net Cash Flow (NCF)/Revenue', 'key': 'ncf_rev', 'standard': 'N/A', 'green': '', 'yellow': '', 'red': '', 'reverse': False},
    ]

    # Add CSS styling
    st.markdown("""
    <style>
    .group-ratio-table-container {
        max-height: 800px;
        overflow-x: auto;
        overflow-y: auto;
        position: relative;
        margin: 1rem 0;
    }
    .group-ratio-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.0rem;
        border: 1px solid white;
    }
    .group-ratio-table thead {
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .group-ratio-table .overall-rank-row.sticky-rank {
        position: sticky;
        top: 0;
        z-index: 99;
    }
    .group-ratio-table th {
        background-color: #025a9a;
        color: white;
        padding: 12px 10px;
        text-align: center;
        font-weight: 600;
        border: 1px solid white;
        font-size: 1.1rem;
        position: sticky;
        top: 48px;
        z-index: 98;
    }
    .group-ratio-table td {
        padding: 10px 8px;
        border: 1px solid white;
        text-align: center;
        background-color: white;
        font-size: 1.0rem;
    }
    .group-ratio-table .row-label {
        background-color: white;
        color: #1a202c;
        font-weight: 500;
        text-align: left;
        padding-left: 15px;
        border: 1px solid white;
        font-size: 1.0rem;
    }
    .group-ratio-table .section-header {
        background-color: #4a5568;
        color: white;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid white;
        padding: 12px 15px;
        font-size: 1.05rem;
    }
    .group-ratio-table .main-header {
        background-color: #025a9a;
        color: white;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid white;
        font-size: 1.0rem;
    }
    .group-ratio-table .orange-header {
        background-color: #f56500;
        color: white;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        border: 1px solid white;
        font-size: 1.0rem;
    }
    .group-ratio-table .rank-row {
        background-color: #f0f0f0;
        font-style: italic;
        font-size: 0.95rem;
    }
    .group-ratio-table .rank-row td {
        background-color: #f0f0f0 !important;
        font-size: 0.95rem;
    }
    .group-ratio-table .overall-rank-row {
        background-color: #025a9a;
        font-weight: 700;
        font-size: 1.05rem;
        font-style: normal;
        box-shadow: 0 2px 4px rgba(2, 90, 154, 0.3);
    }
    .group-ratio-table .overall-rank-row td {
        background-color: #025a9a !important;
        color: white;
        font-weight: 700;
        font-size: 1.05rem;
        font-style: normal;
        text-align: center;
    }
    .group-ratio-table .overall-rank-row .row-label {
        background-color: #025a9a !important;
        color: white;
        font-weight: 700;
        font-size: 1.05rem;
        font-style: normal;
        text-align: left;
    }
    .group-ratio-table .standard-col {
        background-color: #f0f4f8 !important;
        font-weight: 600;
    }
    .group-ratio-table .average-col {
        background-color: #e3f2fd !important;
        font-weight: 600;
    }
    .group-ratio-table .threshold-col {
        background-color: white;
        font-size: 0.95rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Build table HTML with container for scrolling
    table_html = '<div class="group-ratio-table-container"><table class="group-ratio-table"><thead>'

    # Add Overall Rank row at the very top (before header)
    # First calculate overall rankings to display at top
    sorted_total_scores_preview = sorted(total_scores_calc.items(), key=lambda x: x[1])
    overall_rankings_preview = {}
    for rank, (company, score) in enumerate(sorted_total_scores_preview, start=1):
        if score > 0:
            overall_rankings_preview[company] = rank

    table_html += '<tr class="rank-row overall-rank-row sticky-rank"><td class="row-label">🏆 Overall Rank</td>'
    for company in companies:
        rank = overall_rankings_preview.get(company, '')
        table_html += f'<td>{rank}</td>'
    # Empty cells for standard and average columns
    table_html += '<td></td><td></td>'
    table_html += '</tr>'

    # Now add the main header row with company names
    table_html += '<tr>'
    table_html += '<th class="main-header">RATIO ANALYSIS</th>'

    # Add company columns
    for company in companies:
        table_html += f'<th>{company}</th>'

    # Add extra columns (with light yellow text to distinguish from company names)
    table_html += '<th style="color: #ffe082;">Standard</th>'
    table_html += '<th style="color: #ffe082;">Averages</th>'
    table_html += '</tr></thead><tbody>'

    # Asset & Liability Management section
    table_html += '<tr><td class="section-header" colspan="' + str(len(companies) + 3) + '">Asset & Liability Mgmt</td></tr>'

    for metric in metrics:
        # Calculate rankings and average
        rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
        bpc2_avg = calculate_bpc2_average(ratio_data, metric['key'])

        # Metric row
        table_html += f'<tr><td class="row-label">{metric["name"]}</td>'

        for company in companies:
            value = ratio_data[company].get(metric['key'], 0)
            formatted_value = format_metric_value(value, metric['key'])
            color = get_cell_color(value, metric['key'])
            table_html += f'<td style="background-color: {color};">{formatted_value}</td>'

        # Standard and Average columns
        table_html += f'<td class="standard-col">{metric["standard"]}</td>'
        table_html += f'<td class="average-col">{format_metric_value(bpc2_avg, metric["key"])}</td>'
        table_html += '</tr>'

        # Rank row
        table_html += '<tr class="rank-row"><td class="row-label">rank</td>'
        for company in companies:
            rank = rankings.get(company, '-')
            table_html += f'<td>{rank if rank != "-" else ""}</td>'
        # Empty cells for standard and average columns
        table_html += '<td></td><td></td>'
        table_html += '</tr>'

    # Asset & Liability Mgmt Points row (sum of all ranks in this section)
    asset_liability_points = {}
    for company in companies:
        total_points = 0
        for metric in metrics:
            rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
            rank = rankings.get(company, 0)
            if rank and rank != '-':
                total_points += rank
        asset_liability_points[company] = total_points

    table_html += '<tr><td class="row-label">Asset & Liability Mgmt Points</td>'
    for company in companies:
        points = asset_liability_points.get(company, 0)
        table_html += f'<td>{points if points > 0 else ""}</td>'
    # Empty cells for standard and average columns
    table_html += '<td></td><td></td>'
    table_html += '</tr>'

    # Asset & Liability Mgmt overall rank (rank the points - lowest is best)
    # Rank based on total points (lower total points = better rank)
    sorted_points = sorted(asset_liability_points.items(), key=lambda x: x[1])
    points_rankings = {}
    for rank, (company, points) in enumerate(sorted_points, start=1):
        if points > 0:  # Only rank companies with points
            points_rankings[company] = rank

    table_html += '<tr class="rank-row"><td class="row-label">Asset & Liability Mgmt Rank</td>'
    for company in companies:
        rank = points_rankings.get(company, '')
        table_html += f'<td>{rank}</td>'
    # Empty cells for standard and average columns
    table_html += '<td></td><td></td>'
    table_html += '</tr>'

    # Profitability Mgmt section (dark grey header)
    table_html += '<tr><td class="section-header" colspan="' + str(len(companies) + 3) + '">Profitability Mgmt</td></tr>'

    for metric in income_metrics:
        # Calculate rankings and average
        rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
        bpc2_avg = calculate_bpc2_average(ratio_data, metric['key'])

        # Metric row
        table_html += f'<tr><td class="row-label">{metric["name"]}</td>'

        for company in companies:
            value = ratio_data[company].get(metric['key'], 0)
            formatted_value = format_metric_value(value, metric['key'])
            color = get_cell_color(value, metric['key'])
            table_html += f'<td style="background-color: {color};">{formatted_value}</td>'

        # Standard and Average columns
        table_html += f'<td class="standard-col">{metric["standard"]}</td>'
        table_html += f'<td class="average-col">{format_metric_value(bpc2_avg, metric["key"])}</td>'
        table_html += '</tr>'

        # Rank row
        table_html += '<tr class="rank-row"><td class="row-label">rank</td>'
        for company in companies:
            rank = rankings.get(company, '-')
            table_html += f'<td>{rank if rank != "-" else ""}</td>'
        # Empty cells for standard and average columns
        table_html += '<td></td><td></td>'
        table_html += '</tr>'

    # Profitability Mgmt Points row (sum of all ranks in this section)
    profitability_points = {}
    for company in companies:
        total_points = 0
        for metric in income_metrics:
            rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
            rank = rankings.get(company, 0)
            if rank and rank != '-':
                total_points += rank
        profitability_points[company] = total_points

    table_html += '<tr><td class="row-label">Profitability Mgmt Points</td>'
    for company in companies:
        points = profitability_points.get(company, 0)
        table_html += f'<td>{points if points > 0 else ""}</td>'
    # Empty cells for standard and average columns
    table_html += '<td></td><td></td>'
    table_html += '</tr>'

    # Profitability Mgmt overall rank (rank the points - lowest is best)
    # Rank based on total points (lower total points = better rank)
    sorted_prof_points = sorted(profitability_points.items(), key=lambda x: x[1])
    prof_points_rankings = {}
    for rank, (company, points) in enumerate(sorted_prof_points, start=1):
        if points > 0:  # Only rank companies with points
            prof_points_rankings[company] = rank

    table_html += '<tr class="rank-row"><td class="row-label">Profitability Mgmt Rank</td>'
    for company in companies:
        rank = prof_points_rankings.get(company, '')
        table_html += f'<td>{rank}</td>'
    # Empty cells for standard and average columns
    table_html += '<td></td><td></td>'
    table_html += '</tr>'

    # Cash Flow Mgmt section (dark grey header)
    table_html += '<tr><td class="section-header" colspan="' + str(len(companies) + 3) + '">Cash Flow Mgmt</td></tr>'

    for metric in cash_flow_metrics:
        # Calculate rankings and average
        rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
        bpc2_avg = calculate_bpc2_average(ratio_data, metric['key'])

        # Metric row
        table_html += f'<tr><td class="row-label">{metric["name"]}</td>'

        for company in companies:
            value = ratio_data[company].get(metric['key'], 0)
            formatted_value = format_metric_value(value, metric['key'])
            color = get_cell_color(value, metric['key'])
            table_html += f'<td style="background-color: {color};">{formatted_value}</td>'

        # Standard and Average columns
        table_html += f'<td class="standard-col">{metric["standard"]}</td>'
        table_html += f'<td class="average-col">{format_metric_value(bpc2_avg, metric["key"])}</td>'
        table_html += '</tr>'

        # Rank row
        table_html += '<tr class="rank-row"><td class="row-label">rank</td>'
        for company in companies:
            rank = rankings.get(company, '-')
            table_html += f'<td>{rank if rank != "-" else ""}</td>'
        # Empty cells for standard and average columns
        table_html += '<td></td><td></td>'
        table_html += '</tr>'

    # Cash Flow Mgmt Points row (sum of all ranks in this section)
    cash_flow_points = {}
    for company in companies:
        total_points = 0
        for metric in cash_flow_metrics:
            rankings = calculate_rankings(ratio_data, metric['key'], reverse=metric['reverse'])
            rank = rankings.get(company, 0)
            if rank and rank != '-':
                total_points += rank
        cash_flow_points[company] = total_points

    table_html += '<tr><td class="row-label">Cash Flow Mgmt Points</td>'
    for company in companies:
        points = cash_flow_points.get(company, 0)
        table_html += f'<td>{points if points > 0 else ""}</td>'
    # Empty cells for standard and average columns
    table_html += '<td></td><td></td>'
    table_html += '</tr>'

    # Weighted Points row (Cash Flow Mgmt Points / 2)
    weighted_values = {}
    for company in companies:
        points = cash_flow_points.get(company, 0)
        weighted_values[company] = points / 2 if points > 0 else 0

    table_html += '<tr><td class="row-label">Weighted Points</td>'
    for company in companies:
        weighted = weighted_values.get(company, 0)
        display_value = f"{weighted:.1f}" if weighted > 0 else ""
        table_html += f'<td>{display_value}</td>'
    # Empty cells for standard and average columns
    table_html += '<td></td><td></td>'
    table_html += '</tr>'

    # Cash Flow Mgmt overall rank (rank the weighted values - lowest is best)
    # Rank based on weighted values (lower weighted value = better rank)
    sorted_weighted = sorted(weighted_values.items(), key=lambda x: x[1])
    cf_points_rankings = {}
    for rank, (company, weighted) in enumerate(sorted_weighted, start=1):
        if weighted > 0:  # Only rank companies with weighted values
            cf_points_rankings[company] = rank

    table_html += '<tr class="rank-row"><td class="row-label">Cash Flow Mgmt Rank</td>'
    for company in companies:
        rank = cf_points_rankings.get(company, '')
        table_html += f'<td>{rank}</td>'
    # Empty cells for standard and average columns
    table_html += '<td></td><td></td>'
    table_html += '</tr>'

    # Total Score row (sum of Asset & Liability Mgmt Points, Profitability Mgmt Points, Weighted Points)
    total_scores = {}
    for company in companies:
        al_points = asset_liability_points.get(company, 0)
        prof_points = profitability_points.get(company, 0)
        cf_weighted = weighted_values.get(company, 0)
        total_scores[company] = al_points + prof_points + cf_weighted

    table_html += '<tr><td class="row-label">Total Score</td>'
    for company in companies:
        total = total_scores.get(company, 0)
        display_value = f"{total:.1f}" if total > 0 else ""
        table_html += f'<td>{display_value}</td>'
    # Empty cells for standard and average columns
    table_html += '<td></td><td></td>'
    table_html += '</tr>'

    table_html += '</tbody></table></div>'

    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)

    # Add Range Key table below
    st.markdown("""
    <div style="margin-top: 2rem;">
        <h3 style="font-size: 1.4rem; margin-bottom: 1rem; color: #1a202c; font-family: 'Montserrat', sans-serif;">Range Key</h3>
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
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">2.3</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">1.5 to 2.2</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 1.5</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Debt to Equity (Safety)</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">0 to 1.1</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">1.2 to 1.7</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Above 1.7</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Working Capital as % of Total Assets</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Above 35%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">20% to 35%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 20%</td>
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
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Above 6.5%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">4% to 6.5%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 4%</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Net Profit Margin</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa; font-size: 0.95rem;">No Range</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Revenue Per Admin Employee</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Above $580</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">$325 to $580</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below $325</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">EBITDA/Revenue</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Above 5%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">3% to 5%</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Below 3%</td>
                    </tr>
                    <tr style="background-color: #2c3e50; color: white;">
                        <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600; font-size: 1.0rem;" colspan="4">Cash Flows</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Days Sales Outstanding (DSO)</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Below 40</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">40 to 60</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Above 60</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px; font-size: 0.95rem;">Operating Cash Flow (OCF)/Revenue</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #d4edda; font-size: 0.95rem;">Greater than 0.5</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #fff3cd; font-size: 0.95rem;">Near 0</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8d7da; font-size: 0.95rem;">Less than -0.5</td>
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


def create_group_ratios_page():
    """Create group ratios comparison page with header, period selector, and year filter"""
    # Require authentication
    require_auth()

    # Initialize year selection in session state (default to most recent year)
    if 'group_ratios_selected_year' not in st.session_state:
        st.session_state.group_ratios_selected_year = 2024

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

    # Apply page header with period selector
    create_page_header(
        page_title=f"Group Ratio Comparison - {period_display}",
        subtitle=None,
        show_period_selector=True
    )

    # Add some spacing before filter section
    st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

    # Create layout: Title on left, large spacer, compact year filter aligned with Averages column
    col_title, col_spacer, col_filter = st.columns([3, 6, 1])

    with col_title:
        # Show selected year prominently
        st.markdown(f"""
        <div style="margin: 1rem 0;">
            <h2 style="color: #1a202c; font-family: 'Montserrat', sans-serif; font-weight: 600; margin: 0; font-size: 1.5rem; white-space: nowrap;">
                {st.session_state.group_ratios_selected_year} Rankings
            </h2>
        </div>
        """, unsafe_allow_html=True)

    with col_filter:
        # Year filter - same default size as homepage selectboxes
        year_options = [2024, 2023, 2022, 2021, 2020]
        selected_year = st.selectbox(
            "**Select Year**",
            options=year_options,
            index=year_options.index(st.session_state.group_ratios_selected_year) if st.session_state.group_ratios_selected_year in year_options else 0,
            key="group_ratios_year_selector"
        )

        # Update session state if year changed
        if selected_year != st.session_state.group_ratios_selected_year:
            st.session_state.group_ratios_selected_year = selected_year
            st.rerun()

    # Add some spacing
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Get Airtable connection
    conn = get_airtable_connection()

    if not conn:
        st.error("❌ Unable to connect to Airtable. Please check your credentials.")
        return

    # Get selected year from session state
    selected_year = st.session_state.group_ratios_selected_year

    # Determine period filter based on selection and year
    if current_period == 'year_end':
        period_filter = f"{selected_year} Annual"
    else:
        period_filter = f"June {selected_year}"

    # Fetch ratio data for all companies for the selected year
    with st.spinner("Loading ratio analysis data..."):
        ratio_data = fetch_group_ratio_data(period_filter)

    if not ratio_data:
        st.warning(f"⚠️ No ratio data available for {selected_year} - {period_display}.")
        st.info("💡 Try selecting a different year or period.")
        return

    # Display the group ratio comparison table
    create_group_ratio_table(ratio_data)


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="Group Ratios - BPC Dashboard",
        page_icon="📊",
        layout="wide"
    )
    create_group_ratios_page()
