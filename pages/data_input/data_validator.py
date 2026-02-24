"""
Data Validation Module
Validates financial data before uploading to Airtable
"""


def validate_balance_sheet(data):
    """
    Validate balance sheet data
    Returns: (is_valid, errors_list)
    """
    errors = []

    # Check if required fields are present
    required_fields = ['total_assets', 'total_liabilities', 'owners_equity', 'total_liabilities_equity']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate balance sheet equation: Assets = Liabilities + Equity
    total_assets = data.get('total_assets', 0)
    total_liab_equity = data.get('total_liabilities_equity', 0)

    if abs(total_assets - total_liab_equity) > 0.01:
        errors.append(f"Balance sheet equation not balanced: Assets (${total_assets:,.2f}) ≠ Liabilities + Equity (${total_liab_equity:,.2f})")

    # Check for negative values in key totals (excluding accumulated depreciation which should be negative)
    check_non_negative = ['total_assets', 'total_current_assets', 'total_current_liabilities', 'owners_equity']
    for field in check_non_negative:
        if data.get(field, 0) < 0:
            errors.append(f"{field} should not be negative: ${data.get(field, 0):,.2f}")

    # Validate accumulated depreciation should be negative or zero
    if data.get('accumulated_depreciation', 0) > 0:
        errors.append("Accumulated depreciation should be negative or zero (it reduces assets)")

    if errors:
        return False, errors

    return True, []


def validate_income_statement(data):
    """
    Validate income statement data
    Returns: (is_valid, errors_list)
    """
    errors = []

    # Check if required fields are present
    required_fields = ['total_revenue', 'total_cost_of_revenue', 'gross_profit', 'total_operating_expenses', 'operating_profit']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate calculations
    total_revenue = data.get('total_revenue', 0)
    total_cost = data.get('total_cost_of_revenue', 0)
    gross_profit = data.get('gross_profit', 0)

    # Check: Gross Profit = Revenue - Cost of Revenue
    expected_gross_profit = total_revenue - total_cost
    if abs(gross_profit - expected_gross_profit) > 0.01:
        errors.append(f"Gross Profit calculation incorrect: Expected ${expected_gross_profit:,.2f}, got ${gross_profit:,.2f}")

    # Check: Operating Profit = Gross Profit - Operating Expenses
    total_operating = data.get('total_operating_expenses', 0)
    operating_profit = data.get('operating_profit', 0)
    expected_operating_profit = gross_profit - total_operating
    if abs(operating_profit - expected_operating_profit) > 0.01:
        errors.append(f"Operating Profit calculation incorrect: Expected ${expected_operating_profit:,.2f}, got ${operating_profit:,.2f}")

    # Warn if revenue is zero (might be valid for some periods)
    if total_revenue == 0:
        errors.append("Warning: Total Revenue is zero")

    if errors:
        return False, errors

    return True, []


def validate_period_format(period_name):
    """
    Validate period name format
    Valid formats: "2024 Annual", "2024 H1", "2024 H2"
    """
    import re
    pattern = r'^\d{4} (Annual|H1|H2)$'
    if not re.match(pattern, period_name):
        return False, f"Invalid period format: {period_name}. Expected format: 'YYYY Annual', 'YYYY H1', or 'YYYY H2'"
    return True, ""


def get_period_details(period_name):
    """
    Extract period details from period name
    Returns: dict with year, period_type, half_year, start_date, end_date
    """
    parts = period_name.split()
    year = int(parts[0])
    period_type_str = parts[1]

    if period_type_str == 'Annual':
        return {
            'year': year,
            'period_type': 'Annual',
            'half_year': None,
            'start_date': f'{year}-01-01',
            'end_date': f'{year}-12-31',
            'period_name': period_name
        }
    elif period_type_str == 'H1':
        return {
            'year': year,
            'period_type': 'Semi-Annual',
            'half_year': 'H1',
            'start_date': f'{year}-01-01',
            'end_date': f'{year}-06-30',
            'period_name': period_name
        }
    elif period_type_str == 'H2':
        return {
            'year': year,
            'period_type': 'Semi-Annual',
            'half_year': 'H2',
            'start_date': f'{year}-07-01',
            'end_date': f'{year}-12-31',
            'period_name': period_name
        }
    else:
        return None
