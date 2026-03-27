"""
Centralized Cash Flow Ratio Calculations

This module provides cached functions to calculate ocf_rev, fcf_rev, ncf_rev
from Balance Sheet and Income Statement data.

These calculations replace the manually-entered Airtable values, ensuring:
- Consistent calculations across all dashboard pages
- Auto-calculation for new data uploads
- No manual data entry required for these 3 metrics
"""

import streamlit as st
from shared.airtable_connection import get_airtable_connection


def _calculate_cash_flow_for_year(current_balance, prior_balance, current_income, company_name=None, year=None):
    """
    Calculate OCF, FCF, NCF and their revenue ratios for a single year.

    Args:
        current_balance: Balance sheet data for current year
        prior_balance: Balance sheet data for prior year (needed for YoY changes)
        current_income: Income statement data for current year
        company_name: Optional company name for special handling
        year: Optional year string for special handling

    Returns:
        dict with 'ocf_rev', 'fcf_rev', 'ncf_rev' as decimals (e.g., 0.072 for 7.2%)
        Returns None values if calculation not possible (e.g., no prior year data)
    """
    result = {
        'ocf_rev': None,
        'fcf_rev': None,
        'ncf_rev': None
    }

    # Special hardcoded values for Hopkins 2024 (no prior year data available)
    if company_name == 'Hopkins' and year == '2024':
        return {
            'ocf_rev': -0.274,  # -27.4%
            'fcf_rev': 0.449,   # 44.9%
            'ncf_rev': 0.176    # 17.6%
        }

    # Need prior year data to calculate YoY changes
    if not prior_balance or not current_balance or not current_income:
        return result

    # Get total revenue for ratio calculations
    revenue = current_income.get('total_revenue', 0)
    if not revenue or revenue == 0:
        return result

    # --- Calculate Operating Cash Flow (OCF) ---
    # OCF = Net Profit + Δ Current Assets + Δ Current Liabilities + Δ Net Fixed Assets + Δ Non-Current Assets

    # Current Net Profit
    net_profit = current_income.get('profit_before_tax_with_ppp', 0) or 0

    # Change in Current Assets (excluding cash)
    prior_ca = (prior_balance.get('total_current_assets', 0) or 0) - (prior_balance.get('cash_and_cash_equivalents', 0) or 0)
    current_ca = (current_balance.get('total_current_assets', 0) or 0) - (current_balance.get('cash_and_cash_equivalents', 0) or 0) - (current_balance.get('notes_payable_owners', 0) or 0)
    change_current_assets = prior_ca - current_ca

    # Change in Current Liabilities (excluding debt items)
    current_cl = (current_balance.get('total_current_liabilities', 0) or 0) - (current_balance.get('current_portion_ltd', 0) or 0) - (current_balance.get('notes_payable_bank', 0) or 0)
    prior_cl = (prior_balance.get('total_current_liabilities', 0) or 0) - (prior_balance.get('current_portion_ltd', 0) or 0) - (prior_balance.get('notes_payable_bank', 0) or 0) - (prior_balance.get('notes_payable_owners', 0) or 0)
    change_current_liabilities = current_cl - prior_cl

    # Change in Net Fixed Assets
    prior_nfa = prior_balance.get('net_fixed_assets', 0) or 0
    current_nfa = current_balance.get('net_fixed_assets', 0) or 0
    change_net_fixed_assets = prior_nfa - current_nfa

    # Change in Non-Current Assets
    prior_nca = (prior_balance.get('other_assets', 0) or 0) + (prior_balance.get('inter_company_receivable', 0) or 0)
    current_nca = (current_balance.get('other_assets', 0) or 0) + (current_balance.get('inter_company_receivable', 0) or 0)
    change_non_current_assets = prior_nca - current_nca

    # Calculate OCF
    ocf = net_profit + change_current_assets + change_current_liabilities + change_net_fixed_assets + change_non_current_assets
    result['ocf_rev'] = ocf / revenue

    # --- Calculate Financing Cash Flow (FCF) ---
    # FCF = Δ Bank Debt + Δ Owner Debt + Δ Non-Current Liabilities + Equity Adjustment

    # Change in Bank Debt
    current_bank_debt = (current_balance.get('notes_payable_bank', 0) or 0) + (current_balance.get('current_portion_ltd', 0) or 0) + (current_balance.get('long_term_debt', 0) or 0)
    prior_bank_debt = (prior_balance.get('notes_payable_bank', 0) or 0) + (prior_balance.get('current_portion_ltd', 0) or 0) + (prior_balance.get('long_term_debt', 0) or 0)
    change_bank_debt = current_bank_debt - prior_bank_debt

    # Change in Owner Debt
    current_owner_debt = (current_balance.get('notes_payable_owners', 0) or 0) + (current_balance.get('notes_payable_owners_lt', 0) or 0)
    prior_owner_debt = (prior_balance.get('notes_payable_owners', 0) or 0) + (prior_balance.get('notes_payable_owners_lt', 0) or 0)
    change_owner_debt = current_owner_debt - prior_owner_debt

    # Change in Non-Current Liabilities
    current_ncl = (current_balance.get('inter_company_debt', 0) or 0) + (current_balance.get('other_lt_liabilities', 0) or 0)
    prior_ncl = (prior_balance.get('inter_company_debt', 0) or 0) + (prior_balance.get('other_lt_liabilities', 0) or 0)
    change_non_current_liabilities = current_ncl - prior_ncl

    # Equity Adjustment
    prior_equity = prior_balance.get('owners_equity', 0) or 0
    current_equity = current_balance.get('owners_equity', 0) or 0
    equity_adjustment = (current_equity - prior_equity) - net_profit

    # Calculate FCF
    fcf = change_bank_debt + change_owner_debt + change_non_current_liabilities + equity_adjustment
    result['fcf_rev'] = fcf / revenue

    # --- Calculate Net Cash Flow (NCF) ---
    ncf = ocf + fcf
    result['ncf_rev'] = ncf / revenue

    return result


@st.cache_data(ttl=1800, show_spinner=False)
def get_cash_flow_ratios(_airtable, company_name: str, year: str, is_admin: bool = False) -> dict:
    """
    Calculate ocf_rev, fcf_rev, ncf_rev for a specific company and year.

    Cached for 30 minutes to match Airtable data TTL.

    Args:
        _airtable: AirtableConnection instance (underscore prefix for cache compatibility)
        company_name: Company name
        year: Year string (e.g., '2024')

    Returns:
        dict with 'ocf_rev', 'fcf_rev', 'ncf_rev' as decimals
    """
    period = f"{year} Annual"
    prior_year = str(int(year) - 1)
    prior_period = f"{prior_year} Annual"

    # Fetch current year data
    current_bs_list = _airtable.get_balance_sheet_data_by_period(company_name, period, is_admin=is_admin)
    current_is_list = _airtable.get_income_statement_data_by_period(company_name, period, is_admin=is_admin)

    # Fetch prior year data
    prior_bs_list = _airtable.get_balance_sheet_data_by_period(company_name, prior_period, is_admin=is_admin)

    # Extract first record from each list
    current_balance = current_bs_list[0] if current_bs_list else {}
    current_income = current_is_list[0] if current_is_list else {}
    prior_balance = prior_bs_list[0] if prior_bs_list else {}

    return _calculate_cash_flow_for_year(
        current_balance,
        prior_balance,
        current_income,
        company_name=company_name,
        year=year
    )


@st.cache_data(ttl=1800, show_spinner=False)
def get_all_companies_cash_flow_ratios(_airtable, year: str, companies: list, is_admin: bool = False) -> dict:
    """
    Bulk calculate cash flow ratios for all companies for a given year.

    Optimized for group pages - calculates all companies in one pass.
    Cached for 30 minutes.

    Args:
        _airtable: AirtableConnection instance
        year: Year string (e.g., '2024')
        companies: List of company dicts with 'name' key

    Returns:
        dict mapping company_name to {'ocf_rev', 'fcf_rev', 'ncf_rev'}
    """
    period = f"{year} Annual"
    prior_year = str(int(year) - 1)
    prior_period = f"{prior_year} Annual"

    result = {}

    # Fetch bulk data for all companies
    all_current_bs = _airtable.get_all_companies_balance_sheet_by_period(period, is_admin=is_admin)
    all_prior_bs = _airtable.get_all_companies_balance_sheet_by_period(prior_period, is_admin=is_admin)
    all_current_is = _airtable.get_all_companies_income_statement_by_period(period, is_admin=is_admin)

    # Index by company name for quick lookup
    current_bs_by_company = {r.get('company_name'): r for r in all_current_bs}
    prior_bs_by_company = {r.get('company_name'): r for r in all_prior_bs}
    current_is_by_company = {r.get('company_name'): r for r in all_current_is}

    for company in companies:
        company_name = company['name']
        current_balance = current_bs_by_company.get(company_name, {})
        prior_balance = prior_bs_by_company.get(company_name, {})
        current_income = current_is_by_company.get(company_name, {})

        result[company_name] = _calculate_cash_flow_for_year(
            current_balance,
            prior_balance,
            current_income,
            company_name=company_name,
            year=year
        )

    return result


def get_cash_flow_ratios_for_trends(_airtable, company_name: str, years: list = None, is_admin: bool = False) -> dict:
    """
    Get cash flow ratios for multiple years (for trend tables).

    Args:
        _airtable: AirtableConnection instance
        company_name: Company name
        years: List of year strings, defaults to last 5 years from year_config
        is_admin: Whether the current user is an admin (sees submitted records too)

    Returns:
        dict mapping year to {'ocf_rev', 'fcf_rev', 'ncf_rev'}
    """
    if years is None:
        from shared.year_config import get_default_years
        years = get_default_years()

    result = {}
    for year in years:
        result[year] = get_cash_flow_ratios(_airtable, company_name, year, is_admin=is_admin)

    return result
