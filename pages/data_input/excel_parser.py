"""
Excel Parser for Financial Data Upload
Parses Income Statement and Balance Sheet data from uploaded Excel files
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Any
from data_transformation_bs import BALANCE_SHEET_MAPPING
from data_transformation_is import INCOME_STATEMENT_MAPPING

# Direct label-to-field mappings for template parsing
IS_LABEL_MAPPING = {
    # Revenue
    'Intra State HHG': 'intra_state_hhg',
    'Local HHG': 'local_hhg',
    'Inter State HHG': 'inter_state_hhg',
    'Office & Industrial': 'office_industrial',
    'Warehouse (Non-commercial)': 'warehouse',
    'Warehouse Handling (Non-commercial)': 'warehouse_handling',
    'International': 'international',
    'Packing & Unpacking': 'packing_unpacking',
    'Booking & Royalties': 'booking_royalties',
    'Special Products': 'special_products',
    'Records Storage': 'records_storage',
    'Military DPM Contracts': 'military_dpm_contracts',
    'Distribution': 'distribution',
    'Hotel Deliveries': 'hotel_deliveries',
    'Other Revenue': 'other_revenue',
    # Direct Expenses
    'Direct Wages': 'direct_wages',
    'Vehicle Operating Expense': 'vehicle_operating_expenses',
    'Packing/Warehouse Supplies': 'packing_warehouse_supplies',
    'OO Exp Intra State': 'oo_exp_intra_state',
    'OO Inter State': 'oo_inter_state',
    'OO O&I': 'oo_oi',
    'OO Packing': 'oo_packing',
    'OO Other': 'oo_other',
    'Claims': 'claims',
    'Other Trans Exp': 'other_trans_exp',
    'Depreciation': 'depreciation',
    'Lease Expense Rev Equip': 'lease_expense_rev_equip',
    'Rent': 'rent',
    'Other Direct Expenses': 'other_direct_expenses',
    # Operating Expenses
    'Advertising/Marketing': 'advertising_marketing',
    'Bad Debts': 'bad_debts',
    'Sales Commissions': 'sales_commissions',
    'Contributions': 'contributions',
    'Computer Support': 'computer_support',
    'Dues & Subscriptions': 'dues_sub',
    'PR Taxes & Benefits': 'pr_taxes_benefits',
    'Equipment Leases Office Equip': 'equipment_leases_office_equip',
    "Workman's Comp Insurance": 'workmans_comp_insurance',
    'Insurance': 'insurance',
    'Legal & Accounting': 'legal_accounting',
    'Office Expense': 'office_expense',
    'Other Admin': 'other_admin',
    'Pension/Profit Sharing/401k': 'pension_profit_sharing_401k',
    'Professional Fees': 'prof_fees',
    'Repairs & Maintenance': 'repairs_maint',
    'Salaries Admin': 'salaries_admin',
    'Taxes & Licenses': 'taxes_licenses',
    'Tel/Fax/Utilities/Internet': 'tel_fax_utilities_internet',
    'Travel & Entertainment': 'travel_ent',
    'Vehicle Expense Admin': 'vehicle_expense_admin',
    # Other Income/Expenses
    'Other Income': 'other_income',
    'CEO Comp': 'ceo_comp',
    'Other Expense': 'other_expense',
    'Interest Expense': 'interest_expense',
    # Labor Analysis
    'Administrative Employees': 'administrative_employees',
    'Admin Employees': 'administrative_employees',
    'Admin employees': 'administrative_employees',
}

BS_LABEL_MAPPING = {
    # Current Assets
    'Cash & Cash Equivalents': 'cash_and_cash_equivalents',
    'Trade Accounts Receivable': 'trade_accounts_receivable',
    'Receivables': 'receivables',
    'Other Receivables': 'other_receivables',
    'Prepaid Expenses': 'prepaid_expenses',
    'Related Company Receivables': 'related_company_receivables',
    'Owner Receivables': 'owner_receivables',
    'Other Current Assets': 'other_current_assets',
    # Fixed Assets
    'Gross Fixed Assets': 'gross_fixed_assets',
    'Accumulated Depreciation': 'accumulated_depreciation',
    # Other Assets
    'Inter Company Receivable': 'inter_company_receivable',
    'Other Assets': 'other_assets',
    # Current Liabilities
    'Notes Payable/Bank': 'notes_payable_bank',
    'Notes Payable/Owners': 'notes_payable_owners',
    'Trade Accounts Payable': 'trade_accounts_payable',
    'Accrued Expenses': 'accrued_expenses',
    'Current Portion LTD': 'current_portion_ltd',
    'Inter Company Payable': 'inter_company_payable',
    'Other Current Liabilities': 'other_current_liabilities',
    # Long-term Liabilities
    'EID Loan': 'eid_loan',
    'Long-term Debt': 'long_term_debt',
    'Notes Payable Owners (LT)': 'notes_payable_owners_lt',
    'Inter Company Debt': 'inter_company_debt',
    'Other LT Liabilities': 'other_lt_liabilities',
    # Equity
    "Owner's Equity": 'owners_equity',
}


def normalize_field_name(name: str) -> str:
    """
    Normalize a field name for matching by removing spaces, special characters, and converting to lowercase.

    Examples:
        "Packing/Unpacking" → "packingunpacking"
        "Notes Payable/Bank" → "notes_payablebank"
        "Long-term Debt" → "longterm_debt"

    Args:
        name: Original field name from Excel

    Returns:
        Normalized field name
    """
    if pd.isna(name) or not isinstance(name, str):
        return ""

    # Convert to lowercase
    normalized = name.lower().strip()

    # Remove common special characters and spaces
    normalized = re.sub(r'[/\-&(),\'\s]+', '', normalized)

    return normalized


def parse_income_statement_excel(uploaded_file) -> Tuple[Dict[str, float], int, List[str], List[str]]:
    """
    Parse Income Statement data from an uploaded Excel file.

    Expected Excel structure:
        - Sheet name: "Income Statement" or "IS"
        - Column A: Line Item names
        - Column B: Amount values
        - Header row expected at row 0

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Tuple of (data_dict, matched_count, unmatched_items, warnings)
        - data_dict: Dictionary mapping field keys to values
        - matched_count: Number of successfully matched line items
        - unmatched_items: List of line items that couldn't be matched
        - warnings: List of warning messages
    """
    warnings = []
    unmatched_items = []
    data_dict = {}
    matched_count = 0

    try:
        # Try to read the Excel file - look for Income Statement sheet
        try:
            df = pd.read_excel(uploaded_file, sheet_name='Income Statement')
        except ValueError:
            # Try alternative sheet name
            try:
                df = pd.read_excel(uploaded_file, sheet_name='IS')
            except ValueError:
                # Try first non-Instructions sheet
                xls = pd.ExcelFile(uploaded_file)
                data_sheets = [s for s in xls.sheet_names if s.lower() != 'instructions']
                if data_sheets:
                    df = pd.read_excel(uploaded_file, sheet_name=data_sheets[0])
                    warnings.append(f"⚠️ Could not find 'Income Statement' sheet, using '{data_sheets[0]}'")
                else:
                    df = pd.read_excel(uploaded_file, sheet_name=0)
                    warnings.append("⚠️ Could not find 'Income Statement' sheet, using first sheet")

        # Assume first column is Line Item, second column is Amount
        if len(df.columns) < 2:
            warnings.append("❌ Excel file must have at least 2 columns (Line Item, Amount)")
            return {}, 0, [], warnings

        # Rename columns for easier access
        df.columns = ['Line_Item', 'Amount'] + list(df.columns[2:])

        # Iterate through rows
        for idx, row in df.iterrows():
            line_item = row['Line_Item']
            amount = row['Amount']

            # Skip empty rows or header rows
            if pd.isna(line_item) or pd.isna(amount):
                continue

            # Skip if line item is just "Line Item" (header row)
            if str(line_item).strip().lower() in ['line item', 'line_item', '']:
                continue

            # Skip total/calculated rows (these are auto-calculated in the app)
            if any(keyword in str(line_item).lower() for keyword in ['total', 'gross profit', 'operating profit', 'profit before tax']):
                continue

            # Normalize the line item name
            normalized_name = normalize_field_name(line_item)

            # Check if this normalized name exists in the mapping
            if normalized_name in INCOME_STATEMENT_MAPPING:
                field_key = INCOME_STATEMENT_MAPPING[normalized_name]

                # Convert amount to float
                try:
                    numeric_amount = float(amount)
                    data_dict[field_key] = numeric_amount
                    matched_count += 1
                except (ValueError, TypeError):
                    warnings.append(f"⚠️ Invalid amount for '{line_item}': {amount}")
            else:
                # Check if the original field name is already a key
                if str(line_item) in INCOME_STATEMENT_MAPPING:
                    field_key = INCOME_STATEMENT_MAPPING[str(line_item)]
                    try:
                        numeric_amount = float(amount)
                        data_dict[field_key] = numeric_amount
                        matched_count += 1
                    except (ValueError, TypeError):
                        warnings.append(f"⚠️ Invalid amount for '{line_item}': {amount}")
                else:
                    unmatched_items.append(str(line_item))

        if matched_count == 0:
            warnings.append("❌ No matching line items found. Please check Excel format.")

        return data_dict, matched_count, unmatched_items, warnings

    except Exception as e:
        warnings.append(f"❌ Error reading Excel file: {str(e)}")
        return {}, 0, [], warnings


def parse_balance_sheet_excel(uploaded_file) -> Tuple[Dict[str, float], int, List[str], List[str]]:
    """
    Parse Balance Sheet data from an uploaded Excel file.

    Expected Excel structure:
        - Sheet name: "Balance Sheet" or "BS"
        - Column A: Line Item names
        - Column B: Amount values
        - Header row expected at row 0

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Tuple of (data_dict, matched_count, unmatched_items, warnings)
        - data_dict: Dictionary mapping field keys to values
        - matched_count: Number of successfully matched line items
        - unmatched_items: List of line items that couldn't be matched
        - warnings: List of warning messages
    """
    warnings = []
    unmatched_items = []
    data_dict = {}
    matched_count = 0

    try:
        # Try to read the Excel file - look for Balance Sheet sheet
        try:
            df = pd.read_excel(uploaded_file, sheet_name='Balance Sheet')
        except ValueError:
            # Try lowercase version
            try:
                df = pd.read_excel(uploaded_file, sheet_name='balance sheet')
            except ValueError:
                # Try alternative sheet name
                try:
                    df = pd.read_excel(uploaded_file, sheet_name='BS')
                except ValueError:
                    # Try second sheet (assuming IS is first)
                    # Try to find a non-Instructions sheet that isn't the first data sheet
                    xls = pd.ExcelFile(uploaded_file)
                    data_sheets = [s for s in xls.sheet_names if s.lower() != 'instructions']
                    if len(data_sheets) >= 2:
                        df = pd.read_excel(uploaded_file, sheet_name=data_sheets[1])
                        warnings.append(f"⚠️ Could not find 'Balance Sheet' sheet, using '{data_sheets[1]}'")
                    elif data_sheets:
                        df = pd.read_excel(uploaded_file, sheet_name=data_sheets[0])
                        warnings.append(f"⚠️ Could not find 'Balance Sheet' sheet, using '{data_sheets[0]}'")
                    else:
                        df = pd.read_excel(uploaded_file, sheet_name=0)
                        warnings.append("⚠️ Could not find 'Balance Sheet' sheet, using first sheet")

        # Assume first column is Line Item, second column is Amount
        if len(df.columns) < 2:
            warnings.append("❌ Excel file must have at least 2 columns (Line Item, Amount)")
            return {}, 0, [], warnings

        # Rename columns for easier access
        df.columns = ['Line_Item', 'Amount'] + list(df.columns[2:])

        # Iterate through rows
        for idx, row in df.iterrows():
            line_item = row['Line_Item']
            amount = row['Amount']

            # Skip empty rows or header rows
            if pd.isna(line_item) or pd.isna(amount):
                continue

            # Skip if line item is just "Line Item" (header row)
            if str(line_item).strip().lower() in ['line item', 'line_item', '']:
                continue

            # Skip total/calculated rows (these are auto-calculated in the app)
            if any(keyword in str(line_item).lower() for keyword in ['total', 'net fixed assets']):
                continue

            # Normalize the line item name
            normalized_name = normalize_field_name(line_item)

            # Check if this normalized name exists in the mapping
            if normalized_name in BALANCE_SHEET_MAPPING:
                field_key = BALANCE_SHEET_MAPPING[normalized_name]

                # Convert amount to float
                try:
                    numeric_amount = float(amount)
                    data_dict[field_key] = numeric_amount
                    matched_count += 1
                except (ValueError, TypeError):
                    warnings.append(f"⚠️ Invalid amount for '{line_item}': {amount}")
            else:
                # Check if the original field name is already a key
                if str(line_item) in BALANCE_SHEET_MAPPING:
                    field_key = BALANCE_SHEET_MAPPING[str(line_item)]
                    try:
                        numeric_amount = float(amount)
                        data_dict[field_key] = numeric_amount
                        matched_count += 1
                    except (ValueError, TypeError):
                        warnings.append(f"⚠️ Invalid amount for '{line_item}': {amount}")
                else:
                    unmatched_items.append(str(line_item))

        if matched_count == 0:
            warnings.append("❌ No matching line items found. Please check Excel format.")

        return data_dict, matched_count, unmatched_items, warnings

    except Exception as e:
        warnings.append(f"❌ Error reading Excel file: {str(e)}")
        return {}, 0, [], warnings


def parse_consolidated_excel(uploaded_file) -> Tuple[Dict[str, Any], List[str]]:
    """
    Parse both Income Statement and Balance Sheet from a single consolidated Excel file.

    Expected Excel structure:
        - Sheet 1: "Income Statement" with columns: Line Item | Description | 12/31/25
        - Sheet 2: "Balance Sheet" with columns: Line Item | Description | 12/31/25

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Tuple of (results_dict, warnings)
        - results_dict: Contains 'is_data', 'bs_data', 'is_matched', 'bs_matched', 'is_unmatched', 'bs_unmatched', 'is_balanced', 'balance_difference'
        - warnings: List of warning messages
    """
    warnings = []
    results = {
        'is_data': {},
        'bs_data': {},
        'is_matched': 0,
        'bs_matched': 0,
        'is_unmatched': [],
        'bs_unmatched': [],
        'is_balanced': False,
        'balance_difference': 0.0
    }

    try:
        # Parse Income Statement sheet
        is_data, is_matched, is_unmatched, is_warnings = parse_sheet_with_description(
            uploaded_file,
            sheet_name='Income Statement',
            mapping=INCOME_STATEMENT_MAPPING,
            statement_type='IS'
        )
        results['is_data'] = is_data
        results['is_matched'] = is_matched
        results['is_unmatched'] = is_unmatched
        warnings.extend(is_warnings)

        # Parse Balance Sheet sheet
        bs_data, bs_matched, bs_unmatched, bs_warnings = parse_sheet_with_description(
            uploaded_file,
            sheet_name='Balance Sheet',
            mapping=BALANCE_SHEET_MAPPING,
            statement_type='BS'
        )
        results['bs_data'] = bs_data
        results['bs_matched'] = bs_matched
        results['bs_unmatched'] = bs_unmatched
        warnings.extend(bs_warnings)

        # Validate balance sheet balance
        if bs_matched > 0:
            is_balanced, difference = validate_balance_sheet_balance(bs_data)
            results['is_balanced'] = is_balanced
            results['balance_difference'] = difference

        return results, warnings

    except Exception as e:
        warnings.append(f"❌ Error parsing consolidated Excel file: {str(e)}")
        return results, warnings


def parse_sheet_with_description(uploaded_file, sheet_name: str, mapping: Dict, statement_type: str) -> Tuple[Dict[str, float], int, List[str], List[str]]:
    """
    Parse a single sheet from Excel file that has the format: Line Item | Description | Amount

    Args:
        uploaded_file: Streamlit uploaded file object
        sheet_name: Name of the sheet to parse
        mapping: Field mapping dictionary (INCOME_STATEMENT_MAPPING or BALANCE_SHEET_MAPPING)
        statement_type: 'IS' or 'BS' for error messages

    Returns:
        Tuple of (data_dict, matched_count, unmatched_items, warnings)
    """
    warnings = []
    unmatched_items = []
    data_dict = {}
    matched_count = 0

    # Select the appropriate label mapping
    label_mapping = IS_LABEL_MAPPING if statement_type == 'IS' else BS_LABEL_MAPPING

    try:
        # Try to read the specified sheet
        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        except ValueError:
            warnings.append(f"⚠️ Could not find '{sheet_name}' sheet")
            return {}, 0, [], warnings

        # Check if we have at least 3 columns (Line Item, Description, Amount)
        if len(df.columns) < 3:
            warnings.append(f"❌ {sheet_name} sheet must have at least 3 columns (Line Item, Description, Amount)")
            return {}, 0, [], warnings

        # The template has: Column A = Line Item, Column B = Description, Column C = Amount (12/31/25)
        # Use the third column as the amount column
        line_item_col = df.columns[0]
        amount_col = df.columns[2]  # Third column (index 2)

        # Iterate through rows
        for idx, row in df.iterrows():
            line_item = row[line_item_col]
            amount = row[amount_col]

            # Skip empty rows
            if pd.isna(line_item) or pd.isna(amount):
                continue

            # Skip header rows
            if str(line_item).strip().lower() in ['line item', 'line_item', '']:
                continue

            # Skip category header rows (all caps rows like "REVENUE", "CURRENT ASSETS")
            if str(line_item).strip().isupper() and len(str(line_item).split()) <= 4:
                continue

            # Skip total/calculated rows
            skip_keywords = ['total', 'gross profit', 'operating profit', 'profit before tax', 'net fixed assets']
            if any(keyword in str(line_item).lower() for keyword in skip_keywords):
                continue

            # Try direct label mapping first (most reliable for template)
            line_item_str = str(line_item).strip()
            if line_item_str in label_mapping:
                field_key = label_mapping[line_item_str]

                # Convert amount to float
                try:
                    numeric_amount = float(amount)
                    data_dict[field_key] = numeric_amount
                    matched_count += 1
                except (ValueError, TypeError):
                    warnings.append(f"⚠️ Invalid amount for '{line_item}': {amount}")
                continue  # Move to next row

            # Fallback to normalized matching
            normalized_name = normalize_field_name(line_item)

            # Check if this normalized name exists in the mapping
            if normalized_name in mapping:
                field_key = mapping[normalized_name]

                # Convert amount to float
                try:
                    numeric_amount = float(amount)
                    data_dict[field_key] = numeric_amount
                    matched_count += 1
                except (ValueError, TypeError):
                    warnings.append(f"⚠️ Invalid amount for '{line_item}': {amount}")
            else:
                # Check if the original field name is already a key
                if str(line_item) in mapping:
                    field_key = mapping[str(line_item)]
                    try:
                        numeric_amount = float(amount)
                        data_dict[field_key] = numeric_amount
                        matched_count += 1
                    except (ValueError, TypeError):
                        warnings.append(f"⚠️ Invalid amount for '{line_item}': {amount}")
                else:
                    # Only add to unmatched if it's not a blank/spacing row
                    if str(line_item).strip():
                        unmatched_items.append(str(line_item))

        if matched_count == 0:
            warnings.append(f"❌ No matching line items found in {sheet_name}. Please check Excel format.")

        return data_dict, matched_count, unmatched_items, warnings

    except Exception as e:
        warnings.append(f"❌ Error reading {sheet_name} sheet: {str(e)}")
        return {}, 0, [], warnings


def validate_balance_sheet_balance(data: Dict[str, float]) -> Tuple[bool, float]:
    """
    Check if Balance Sheet balances (Assets = Liabilities + Equity).

    Args:
        data: Dictionary of balance sheet field values

    Returns:
        Tuple of (is_balanced, difference)
    """
    # Calculate Total Current Assets
    current_assets_fields = [
        'cash_and_cash_equivalents', 'trade_accounts_receivable', 'receivables',
        'other_receivables', 'prepaid_expenses', 'related_company_receivables',
        'owner_receivables', 'other_current_assets'
    ]
    total_current_assets = sum(data.get(field, 0) for field in current_assets_fields)

    # Calculate Net Fixed Assets
    gross_fixed_assets = data.get('gross_fixed_assets', 0)
    accumulated_depreciation = data.get('accumulated_depreciation', 0)
    net_fixed_assets = gross_fixed_assets + accumulated_depreciation  # depreciation entered as negative

    # Calculate Other Assets
    other_assets_fields = ['inter_company_receivable', 'other_assets']
    total_other_assets = sum(data.get(field, 0) for field in other_assets_fields)

    # Total Assets
    total_assets = total_current_assets + net_fixed_assets + total_other_assets

    # Calculate Total Current Liabilities
    current_liab_fields = [
        'notes_payable_bank', 'notes_payable_owners', 'trade_accounts_payable',
        'accrued_expenses', 'current_portion_ltd', 'inter_company_payable',
        'other_current_liabilities'
    ]
    total_current_liabilities = sum(data.get(field, 0) for field in current_liab_fields)

    # Calculate Total Long-term Liabilities
    lt_liab_fields = [
        'eid_loan', 'long_term_debt', 'notes_payable_owners_lt',
        'inter_company_debt', 'other_lt_liabilities'
    ]
    total_lt_liabilities = sum(data.get(field, 0) for field in lt_liab_fields)

    # Calculate Equity
    owners_equity = data.get('owners_equity', 0)

    # Total Liabilities + Equity
    total_liabilities_equity = total_current_liabilities + total_lt_liabilities + owners_equity

    # Check balance
    difference = total_assets - total_liabilities_equity
    is_balanced = abs(difference) < 0.01  # Allow for rounding differences

    return is_balanced, difference
