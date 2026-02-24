"""
Bisson Historical Data Migration Script
Imports Balance Sheet and Income Statement data for years 2021-2024 from Bisson's Excel file.

Usage:
    DRY_RUN=True: Shows what would be uploaded without making changes
    DRY_RUN=False: Actually uploads to Airtable
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============ CONFIGURATION ============
DRY_RUN = False  # Set to False to actually upload

EXCEL_FILE_PATH = '/Users/adi/Documents/imai_codebases/bisson_historical_data/FY24 BPC - Financial Data Worksheet Year End 24.xlsx'
BISSON_COMPANY_ID = 'recFtJTFbWVHVW5Ut'
YEARS_TO_IMPORT = [2021, 2022, 2023, 2024]

# Airtable credentials from .env
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_PAT = os.getenv('AIRTABLE_PAT')

# ============ FIELD MAPPINGS ============
# Maps Excel labels (human-readable) to Airtable field names

BALANCE_SHEET_LABEL_MAP = {
    # Current Assets
    'Cash and cash equivalents': 'cash_and_cash_equivalents',
    'Trade Accounts Receivable': 'trade_accounts_receivable',
    'Receivables - Van Lines': 'receivables',
    'Other Receivables': 'other_receivables',
    'Prepaid Expenses': 'prepaid_expenses',
    'Related Company Receivables': 'related_company_receivables',
    'Owner Receivables': 'owner_receivables',
    'Other Current Assets': 'other_current_assets',
    'Total Current Assets': 'total_current_assets',

    # Fixed Assets
    'Gross Fixed Assets': 'gross_fixed_assets',
    'Accumulated Depreciation (-)': 'accumulated_depreciation',
    'Net Fixed Assets': 'net_fixed_assets',

    # Other Assets
    'Inter Company Receivable': 'inter_company_receivable',
    'Other Assets': 'other_assets',
    'TOTAL ASSETS': 'total_assets',

    # Current Liabilities
    'Notes Payable-Bank': 'notes_payable_bank',
    'Notes Payable-Owners': 'notes_payable_owners',
    'Trade Accounts Payable': 'trade_accounts_payable',
    'Accrued Expenses': 'accrued_expenses',
    'Current Portion LTD': 'current_portion_ltd',
    'Inter Company payable': 'inter_company_payable',
    'Other Current Liabilities': 'other_current_liabilities',
    'Total Current Liabilities': 'total_current_liabilities',

    # Long-term Liabilities
    'Long-Term Debt': 'long_term_debt',
    'Notes Payable Owners': 'notes_payable_owners_lt',
    'Inter Company Debt': 'inter_company_debt',
    'Other LT Liabilities': 'other_lt_liabilities',
    'Total Long Term Liabilities': 'total_long_term_liabilities',
    'Total Liabilities': 'total_liabilities',

    # Equity
    "Owners' Equity": 'owners_equity',
    'TOTAL LIABILITIES & EQUITY': 'total_liabilities_equity',
}

INCOME_STATEMENT_LABEL_MAP = {
    # Revenue
    'Intra State HHG': 'intra_state_hhg',
    'Local HHG': 'local_hhg',
    'Inter State Hauling': 'inter_state_hhg',
    'Office & Industrial': 'office_industrial',
    'HHG Warehouse': 'warehouse',
    'HHG Warehouse handling': 'warehouse_handling',
    'International': 'international',
    'Packing/Unpacking': 'packing_unpacking',
    'Booking & Royalties': 'booking_royalties',
    'Special Products': 'special_products',
    'Records Storage': 'records_storage',
    'Military DPM Contracts': 'military_dpm_contracts',
    'Distribution': 'distribution',
    'Hotel Deliveries': 'hotel_deliveries',
    'Other Revenue': 'other_revenue',
    'Total Revenue': 'total_revenue',

    # Direct Expenses (Cost of Revenue)
    'Direct Wages': 'direct_wages',
    'Vehicle Operating Expense': 'vehicle_operating_expenses',
    'Packing/Warehouse Supplies': 'packing_warehouse_supplies',
    'Owner Operator Exp/Intra State': 'oo_exp_intra_state',
    'Owner Operator Inter State': 'oo_inter_state',
    'Owner Operator O/I': 'oo_oi',
    'Owner Operator Packing': 'oo_packing',
    'Owner Operator Other': 'oo_other',
    'Claims': 'claims',
    'Other Transportation Expense                       (Powertrack Fee should be here)': 'other_trans_exp',
    'Depreciation/amortization': 'depreciation',
    'Lease Expense - Revenue Equip': 'lease_expense_rev_equip',
    'Rent/building expense': 'rent',
    'Other Direct Costs & CC Fees': 'other_direct_expenses',
    'Total Cost of Revenue': 'total_cost_of_revenue',
    'Total Gross Profit': 'gross_profit',

    # Operating Expenses
    'Advertising/marketing': 'advertising_marketing',
    'Bad Debts': 'bad_debts',
    'Sales Compensation': 'sales_commissions',
    'Contributions': 'contributions',
    'Computer Support': 'computer_support',
    'Dues & Subscriptions': 'dues_sub',
    'Payroll Taxes and Benefits': 'pr_taxes_benefits',
    'Lease Expense - office equp.': 'equipment_leases_office_equip',
    "Workmen's Comp. Insurance": 'workmans_comp_insurance',
    'Insurance': 'insurance',
    'Legal & Accounting': 'legal_accounting',
    'Office Expense': 'office_expense',
    'Other Administrative': 'other_admin',
    'Pension/profit sharing/401K': 'pension_profit_sharing_401k',
    'Professional Fees': 'prof_fees',
    'Repairs & Maintenance': 'repairs_maint',
    'Salaries - Admin': 'salaries_admin',
    'Taxes & Licenses': 'taxes_licenses',
    'Telephone/Fax/Utilities/Internet': 'tel_fax_utilities_internet',
    'Travel & Entertainment': 'travel_ent',
    'Vehicle - Admin': 'vehicle_expense_admin',
    'Total Operating Expenses': 'total_operating_expenses',
    'Total Operating Income/(Loss)': 'operating_profit',

    # Non-Operating
    'Other Income': 'other_income',
    'CEO Comp/Perks (-)': 'ceo_comp',
    'Other Expense (-)': 'other_expense',
    'Interest Expense (-)': 'interest_expense',
    'Total Non-Operating Income & (Expense)': 'total_nonoperating_income',
    'Profit Before Tax': 'profit_before_tax_with_ppp',

    # Other
    'Number of Admin Employees': 'administrative_employees',
}


def convert_value(val):
    """Convert numpy/pandas types to native Python types."""
    if pd.isna(val):
        return None
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val)
    return val


def parse_balance_sheet(excel_path):
    """Parse Balance Sheet data from Bisson's Excel file."""
    print("\n📊 Parsing Balance Sheet...")

    df = pd.read_excel(excel_path, sheet_name='Balance Sheet', header=None)

    # Data structure:
    # Row 0: Header "BEST PRACTICE COUNCIL - BALANCE SHEET"
    # Row 1: "Company Name:"
    # Row 2: Headers - col 0 empty, cols 1-4 are dates (2021-12-31, etc.)
    # Row 3: "Chart of accounts" label row
    # Row 4+: Data rows

    # Extract year columns (columns 1-4 contain years 2021-2024)
    year_columns = {
        2021: 1,
        2022: 2,
        2023: 3,
        2024: 4,
    }

    results = {year: {} for year in YEARS_TO_IMPORT}
    matched_count = 0
    unmatched_labels = []

    # Process each row starting from row 4
    for idx in range(4, len(df)):
        label = df.iloc[idx, 0]
        if pd.isna(label):
            continue

        label = str(label).strip()

        # Check if this label maps to an Airtable field
        if label in BALANCE_SHEET_LABEL_MAP:
            airtable_field = BALANCE_SHEET_LABEL_MAP[label]

            for year in YEARS_TO_IMPORT:
                col_idx = year_columns[year]
                value = convert_value(df.iloc[idx, col_idx])

                if value is not None:
                    # Handle accumulated depreciation - should be positive in Airtable
                    if airtable_field == 'accumulated_depreciation' and value < 0:
                        value = abs(value)

                    results[year][airtable_field] = value
                    matched_count += 1
        else:
            # Track unmatched labels for debugging
            if label and not label.startswith('NaN') and label not in ['Chart of accounts', 'Company Name:']:
                unmatched_labels.append(label)

    # Remove duplicates from unmatched
    unmatched_labels = list(set(unmatched_labels))

    print(f"  ✓ Matched {matched_count} values across {len(YEARS_TO_IMPORT)} years")
    if unmatched_labels:
        print(f"  ⚠ Unmatched labels: {unmatched_labels[:5]}{'...' if len(unmatched_labels) > 5 else ''}")

    return results


def parse_income_statement(excel_path):
    """Parse Income Statement data from Bisson's Excel file."""
    print("\n📈 Parsing Income Statement...")

    df = pd.read_excel(excel_path, sheet_name='Income Statement', header=None)

    # Similar structure to Balance Sheet
    year_columns = {
        2021: 1,
        2022: 2,
        2023: 3,
        2024: 4,
    }

    results = {year: {} for year in YEARS_TO_IMPORT}
    matched_count = 0
    unmatched_labels = []

    # Process each row starting from row 4
    for idx in range(4, len(df)):
        label = df.iloc[idx, 0]
        if pd.isna(label):
            continue

        label = str(label).strip()

        # Check if this label maps to an Airtable field
        if label in INCOME_STATEMENT_LABEL_MAP:
            airtable_field = INCOME_STATEMENT_LABEL_MAP[label]

            for year in YEARS_TO_IMPORT:
                col_idx = year_columns[year]
                value = convert_value(df.iloc[idx, col_idx])

                if value is not None:
                    # Handle negative entries (CEO comp, interest expense, other expense)
                    # These are entered as negatives in Excel but stored as positives in Airtable
                    if airtable_field in ['ceo_comp', 'interest_expense', 'other_expense'] and value < 0:
                        value = abs(value)

                    results[year][airtable_field] = value
                    matched_count += 1
        else:
            if label and not label.startswith('NaN') and label not in ['Chart of accounts', 'Company Name:']:
                unmatched_labels.append(label)

    unmatched_labels = list(set(unmatched_labels))

    print(f"  ✓ Matched {matched_count} values across {len(YEARS_TO_IMPORT)} years")
    if unmatched_labels:
        print(f"  ⚠ Unmatched labels: {unmatched_labels[:5]}{'...' if len(unmatched_labels) > 5 else ''}")

    return results


def display_dry_run_results(bs_data, is_data):
    """Display what would be uploaded in dry run mode."""
    print("\n" + "="*60)
    print("🔍 DRY RUN RESULTS - No data will be uploaded")
    print("="*60)

    for year in YEARS_TO_IMPORT:
        print(f"\n📅 {year} Annual")
        print("-" * 40)

        # Balance Sheet summary
        bs = bs_data.get(year, {})
        print(f"\n  Balance Sheet ({len(bs)} fields):")
        if bs:
            total_assets = bs.get('total_assets', 'N/A')
            total_liab_equity = bs.get('total_liabilities_equity', 'N/A')
            print(f"    Total Assets: ${total_assets:,.2f}" if isinstance(total_assets, (int, float)) else f"    Total Assets: {total_assets}")
            print(f"    Total Liab+Equity: ${total_liab_equity:,.2f}" if isinstance(total_liab_equity, (int, float)) else f"    Total Liab+Equity: {total_liab_equity}")

            # Check if balanced
            if isinstance(total_assets, (int, float)) and isinstance(total_liab_equity, (int, float)):
                diff = abs(total_assets - total_liab_equity)
                if diff < 1:
                    print(f"    ✅ Balanced!")
                else:
                    print(f"    ⚠️ Difference: ${diff:,.2f}")

        # Income Statement summary
        is_year = is_data.get(year, {})
        print(f"\n  Income Statement ({len(is_year)} fields):")
        if is_year:
            total_rev = is_year.get('total_revenue', 'N/A')
            gross_profit = is_year.get('gross_profit', 'N/A')
            op_profit = is_year.get('operating_profit', 'N/A')
            pbt = is_year.get('profit_before_tax_with_ppp', 'N/A')

            print(f"    Total Revenue: ${total_rev:,.2f}" if isinstance(total_rev, (int, float)) else f"    Total Revenue: {total_rev}")
            print(f"    Gross Profit: ${gross_profit:,.2f}" if isinstance(gross_profit, (int, float)) else f"    Gross Profit: {gross_profit}")
            print(f"    Operating Profit: ${op_profit:,.2f}" if isinstance(op_profit, (int, float)) else f"    Operating Profit: {op_profit}")
            print(f"    Profit Before Tax: ${pbt:,.2f}" if isinstance(pbt, (int, float)) else f"    Profit Before Tax: {pbt}")

    print("\n" + "="*60)
    print("To actually upload, set DRY_RUN = False in the script")
    print("="*60)


def upload_to_airtable(bs_data, is_data):
    """Upload data to Airtable."""
    from data_transformation_bs import AirtableBalanceSheetUploader
    from data_transformation_is import AirtableIncomeStatementUploader

    print("\n" + "="*60)
    print("📤 UPLOADING TO AIRTABLE")
    print("="*60)

    bs_uploader = AirtableBalanceSheetUploader(AIRTABLE_BASE_ID, AIRTABLE_PAT)
    is_uploader = AirtableIncomeStatementUploader(AIRTABLE_BASE_ID, AIRTABLE_PAT)

    results = {'bs': [], 'is': []}

    for year in YEARS_TO_IMPORT:
        period_name = f"{year} Annual"
        print(f"\n📅 Processing {period_name}...")

        # Period info for creating/finding periods
        period_info = {
            'period_name': period_name,
            'period_type': 'Annual',
            'half_year': None,
            'start_date': f'{year}-01-01',
            'end_date': f'{year}-12-31',
            'year': year
        }

        # Upload Balance Sheet
        bs = bs_data.get(year, {})
        if bs:
            period_id = bs_uploader.create_period_if_not_exists(period_info, BISSON_COMPANY_ID)
            if period_id:
                result = bs_uploader.upload_balance_sheet(
                    period_id,
                    bs,
                    f'Bisson_Historical_Import_{datetime.now().strftime("%Y%m%d")}',
                    BISSON_COMPANY_ID,
                    'migration_script',
                    publication_status='published'  # Admin migration - immediately visible
                )
                results['bs'].append({'year': year, 'result': result})
                if result.get('success'):
                    print(f"  ✅ Balance Sheet: {result.get('action', 'done')}")
                else:
                    print(f"  ❌ Balance Sheet: {result.get('message', 'failed')}")

        # Upload Income Statement
        is_year = is_data.get(year, {})
        if is_year:
            period_id = is_uploader.create_period_if_not_exists(period_info, BISSON_COMPANY_ID)
            if period_id:
                result = is_uploader.upload_income_statement(
                    period_id,
                    is_year,
                    f'Bisson_Historical_Import_{datetime.now().strftime("%Y%m%d")}',
                    BISSON_COMPANY_ID,
                    'migration_script',
                    publication_status='published'  # Admin migration - immediately visible
                )
                results['is'].append({'year': year, 'result': result})
                if result.get('success'):
                    print(f"  ✅ Income Statement: {result.get('action', 'done')}")
                else:
                    print(f"  ❌ Income Statement: {result.get('message', 'failed')}")

    # Summary
    print("\n" + "="*60)
    print("📊 UPLOAD SUMMARY")
    print("="*60)
    bs_success = sum(1 for r in results['bs'] if r['result'].get('success'))
    is_success = sum(1 for r in results['is'] if r['result'].get('success'))
    print(f"Balance Sheets: {bs_success}/{len(YEARS_TO_IMPORT)} uploaded")
    print(f"Income Statements: {is_success}/{len(YEARS_TO_IMPORT)} uploaded")

    # Link BS to IS records (required for DSO and other formula calculations)
    if bs_success > 0 and is_success > 0:
        print("\n" + "="*60)
        print("🔗 LINKING BS TO IS RECORDS")
        print("="*60)
        link_bs_to_is_records(BISSON_COMPANY_ID)

    return results


def link_bs_to_is_records(company_id):
    """
    Link Balance Sheet records to corresponding Income Statement records.

    This is required for Airtable formula fields that need data from both tables,
    such as DSO (Days Sales Outstanding) which needs Total Revenue from IS.

    Matches records by period name (year).
    """
    import requests

    headers = {
        'Authorization': f'Bearer {AIRTABLE_PAT}',
        'Content-Type': 'application/json'
    }
    base_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}"

    # Get all periods for this company (map period ID to name)
    periods = {}
    response = requests.get(f'{base_url}/financial_periods', headers=headers, params={'maxRecords': 200})
    if response.status_code == 200:
        for r in response.json().get('records', []):
            fields = r.get('fields', {})
            if company_id in fields.get('company', []):
                periods[r['id']] = fields.get('period_name', 'Unknown')

    # Get IS records indexed by period name
    is_by_period_name = {}
    response = requests.get(f'{base_url}/income_statement_data', headers=headers, params={'maxRecords': 100})
    if response.status_code == 200:
        for r in response.json().get('records', []):
            fields = r.get('fields', {})
            if company_id in fields.get('company', []):
                period_link = fields.get('period', [])
                period_id = period_link[0] if period_link else None
                period_name = periods.get(period_id, 'Unknown')
                is_by_period_name[period_name] = r['id']

    # Get BS records and link to corresponding IS
    response = requests.get(f'{base_url}/balance_sheet_data', headers=headers, params={'maxRecords': 100})
    if response.status_code == 200:
        for r in response.json().get('records', []):
            fields = r.get('fields', {})
            if company_id in fields.get('company', []):
                # Skip if already linked
                if fields.get('related_income_stmt'):
                    continue

                period_link = fields.get('period', [])
                period_id = period_link[0] if period_link else None
                period_name = periods.get(period_id, 'Unknown')

                # Find matching IS by period name
                matching_is = is_by_period_name.get(period_name)

                if matching_is:
                    # Update BS record to link to IS
                    update_url = f'{base_url}/balance_sheet_data/{r["id"]}'
                    payload = {'fields': {'related_income_stmt': [matching_is]}}

                    update_response = requests.patch(update_url, headers=headers, json=payload)
                    if update_response.status_code == 200:
                        print(f"  ✅ {period_name}: Linked BS to IS")
                    else:
                        print(f"  ❌ {period_name}: Failed to link - {update_response.text[:50]}")
                else:
                    print(f"  ⚠️ {period_name}: No matching IS record found")


def main():
    """Main entry point."""
    print("="*60)
    print("🏢 BISSON HISTORICAL DATA MIGRATION")
    print(f"   Company ID: {BISSON_COMPANY_ID}")
    print(f"   Years: {YEARS_TO_IMPORT}")
    print(f"   Mode: {'DRY RUN' if DRY_RUN else '⚠️  LIVE UPLOAD'}")
    print("="*60)

    # Validate
    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"❌ Excel file not found: {EXCEL_FILE_PATH}")
        return

    if not DRY_RUN and (not AIRTABLE_BASE_ID or not AIRTABLE_PAT):
        print("❌ Missing AIRTABLE_BASE_ID or AIRTABLE_PAT in .env")
        return

    # Parse data
    bs_data = parse_balance_sheet(EXCEL_FILE_PATH)
    is_data = parse_income_statement(EXCEL_FILE_PATH)

    if DRY_RUN:
        display_dry_run_results(bs_data, is_data)
    else:
        upload_to_airtable(bs_data, is_data)


if __name__ == "__main__":
    main()
