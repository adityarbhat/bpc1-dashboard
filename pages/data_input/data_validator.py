"""
Data Validation Module
Validates financial data before uploading to Airtable.
Focuses on data cleanliness (numeric types, no stray text) and structural
integrity (balance sheet equation, IS calculation checks).
Negative values are allowed — data quality is the user's responsibility.
"""


def clean_numeric_value(value):
    """
    Clean and convert a value to float.
    Strips commas, whitespace, dollar signs, and converts to float.
    Returns: (cleaned_float, error_string_or_None)
    """
    if value is None:
        return 0.0, None
    if isinstance(value, (int, float)):
        return float(value), None
    if isinstance(value, str):
        cleaned = value.strip().replace(',', '').replace('$', '').replace(' ', '')
        if cleaned == '' or cleaned == '-':
            return 0.0, None
        try:
            return float(cleaned), None
        except ValueError:
            return None, f"Not a valid number: '{value}'"
    return None, f"Unexpected type {type(value).__name__} for value: '{value}'"


def clean_financial_data(data):
    """
    Clean all numeric fields in a financial data dict.
    Strips commas, whitespace, dollar signs and converts to floats.
    Returns: (cleaned_data, errors_list)
    """
    cleaned = {}
    errors = []
    for field, value in data.items():
        clean_val, error = clean_numeric_value(value)
        if error:
            errors.append(f"{field}: {error}")
        else:
            cleaned[field] = clean_val
    return cleaned, errors


def validate_balance_sheet(data):
    """
    Validate balance sheet data.
    Cleans inputs, checks required fields exist and are numeric,
    and verifies the balance sheet equation.
    Returns: (is_valid, errors_list)
    """
    errors = []

    # Clean all values — strip commas, whitespace, enforce floats
    cleaned, clean_errors = clean_financial_data(data)
    if clean_errors:
        return False, clean_errors

    # Check if required fields are present
    required_fields = ['total_assets', 'total_liabilities', 'owners_equity', 'total_liabilities_equity']
    for field in required_fields:
        if field not in cleaned:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate balance sheet equation: Assets = Liabilities + Equity
    total_assets = cleaned.get('total_assets', 0)
    total_liab_equity = cleaned.get('total_liabilities_equity', 0)

    if abs(total_assets - total_liab_equity) > 0.01:
        errors.append(f"Balance sheet not balanced: Assets (${total_assets:,.2f}) ≠ Liabilities + Equity (${total_liab_equity:,.2f})")

    if errors:
        return False, errors

    # Update original data with cleaned values
    data.update(cleaned)
    return True, []


def validate_income_statement(data):
    """
    Validate income statement data.
    Cleans inputs, checks required fields exist and are numeric,
    and verifies key calculations.
    Returns: (is_valid, errors_list)
    """
    errors = []

    # Clean all values — strip commas, whitespace, enforce floats
    cleaned, clean_errors = clean_financial_data(data)
    if clean_errors:
        return False, clean_errors

    # Check if required fields are present
    required_fields = ['total_revenue', 'total_cost_of_revenue', 'gross_profit', 'total_operating_expenses', 'operating_profit']
    for field in required_fields:
        if field not in cleaned:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate calculations
    total_revenue = cleaned.get('total_revenue', 0)
    total_cost = cleaned.get('total_cost_of_revenue', 0)
    gross_profit = cleaned.get('gross_profit', 0)

    # Check: Gross Profit = Revenue - Cost of Revenue
    expected_gross_profit = total_revenue - total_cost
    if abs(gross_profit - expected_gross_profit) > 0.01:
        errors.append(f"Gross Profit calculation incorrect: Expected ${expected_gross_profit:,.2f}, got ${gross_profit:,.2f}")

    # Check: Operating Profit = Gross Profit - Operating Expenses
    total_operating = cleaned.get('total_operating_expenses', 0)
    operating_profit = cleaned.get('operating_profit', 0)
    expected_operating_profit = gross_profit - total_operating
    if abs(operating_profit - expected_operating_profit) > 0.01:
        errors.append(f"Operating Profit calculation incorrect: Expected ${expected_operating_profit:,.2f}, got ${operating_profit:,.2f}")

    if errors:
        return False, errors

    # Update original data with cleaned values
    data.update(cleaned)
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
