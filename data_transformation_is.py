# Updated data_transformation_is.py with cleaned line items and Sheet3 support

import pandas as pd
import numpy as np
from datetime import datetime
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Updated field mapping with cleaned line item names (matching your Excel file)
INCOME_STATEMENT_MAPPING = {
    # === REVENUE FIELDS ===
    'intra_state_hhg': 'intra_state_hhg',
    'local_hhg': 'local_hhg',
    'inter_state_hhg': 'inter_state_hhg',
    'office_industrial': 'office_industrial',
    'warehouse': 'warehouse',
    'warehouse_handling': 'warehouse_handling',
    'international': 'international',
    'packingunpacking': 'packing_unpacking',
    'bookingroyalties': 'booking_royalties',
    'special_products': 'special_products',
    'records_storage': 'records_storage',
    'military_dpm_contracts': 'military_dpm_contracts',
    'distribution': 'distribution',
    'hotel_deliveries': 'hotel_deliveries',
    'other_revenue': 'other_revenue',
    'total_revenue': 'total_revenue',  # Client-provided aggregate
    
    # === COST OF REVENUE FIELDS ===
    'direct_wages': 'direct_wages',
    'vehicle_operating_expenses': 'vehicle_operating_expenses',
    'packingwarehouse_supplies': 'packing_warehouse_supplies',
    'oo_exp_intra_state': 'oo_exp_intra_state',
    'oo_inter_state': 'oo_inter_state',
    'oo_oi': 'oo_oi',
    'oo_packing': 'oo_packing',
    'oo_other': 'oo_other',
    'claims': 'claims',
    'other_trans_exp': 'other_trans_exp',
    'depreciation': 'depreciation',
    'lease_expense_rev_equip': 'lease_expense_rev_equip',
    'rent': 'rent',
    'other_direct_expenses': 'other_direct_expenses',
    'total_cost_of_revenue': 'total_cost_of_revenue',  # Client-provided aggregate
    'gross_profit': 'gross_profit',  # Client-provided aggregate
    
    # === OPERATING EXPENSE FIELDS ===
    'advertisingmarketing': 'advertising_marketing',
    'bad_debts': 'bad_debts',
    'sales_commissions': 'sales_commissions',
    'contributions': 'contributions',
    'computer_support': 'computer_support',
    'dues_sub': 'dues_sub',
    'pr_taxes_benefits': 'pr_taxes_benefits',
    'equipment_leases_office_equip': 'equipment_leases_office_equip',
    'workmans_comp_insurance': 'workmans_comp_insurance',
    'insurance': 'insurance',
    'legal_accounting': 'legal_accounting',
    'office_expense': 'office_expense',
    'other_admin': 'other_admin',
    'pensionprofit_sharing401k': 'pension_profit_sharing_401k',
    'prof_fees': 'prof_fees',
    'repairs_maint': 'repairs_maint',
    'salaries_admin': 'salaries_admin',
    'taxes_licenses': 'taxes_licenses',
    'telfaxutilitiesinternet': 'tel_fax_utilities_internet',
    'travel_ent': 'travel_ent',
    'vehicle_expense_admin': 'vehicle_expense_admin',
    'total_operating_expenses': 'total_operating_expenses',  # Client-provided aggregate
    'operating_profit': 'operating_profit',  # Client-provided aggregate
    
    # === NON-OPERATING FIELDS ===
    'other_income': 'other_income',
    'ceo_comp': 'ceo_comp',
    'other_expense': 'other_expense',
    'interest_expense': 'interest_expense',
    'total_nonoperating_income': 'total_nonoperating_income',  # Client-provided aggregate
    'profit_before_tax_with_ppp': 'profit_before_tax_with_ppp',  # Client-provided aggregate
    
    # === OTHER FIELDS ===
    'administrative_employees': 'administrative_employees',  # Number field, not currency
    'number_of_branches': 'number_of_branches',  # Number field, not currency
}

def convert_to_json_serializable(obj):
    """Convert numpy data types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

def smart_period_detection_is(df_melted):
    """
    Intelligently detect period types based on the actual date patterns in the data.
    Same logic as balance sheet but for income statement.
    """
    # Convert to datetime if not already
    df_melted['period_datetime'] = pd.to_datetime(df_melted['period_date'])
    df_melted['year'] = df_melted['period_datetime'].dt.year
    df_melted['month'] = df_melted['period_datetime'].dt.month
    
    # Group by year to see what months we have
    year_months = df_melted.groupby('year')['month'].unique()
    
    period_info_list = []
    for _, row in df_melted.iterrows():
        year = row['year']
        month = row['month']
        period_datetime = row['period_datetime']
        
        # Get all months available for this year
        available_months = year_months[year]
        
        # Smart detection logic
        if len(available_months) == 1:
            # Only one period for this year
            if month == 12:
                # December only = Annual
                period_info = {
                    'period_type': 'Annual',
                    'period_name': f'{year} Annual',
                    'half_year': None,
                    'start_date': f'{year}-01-01',
                    'end_date': f'{year}-12-31',
                }
            elif month in [6, 7]:
                # June/July only = H1
                period_info = {
                    'period_type': 'Semi-Annual',
                    'period_name': f'{year} H1',
                    'half_year': 'H1',
                    'start_date': f'{year}-01-01',
                    'end_date': f'{year}-06-30',
                }
            else:
                # Other single month = treat as annual
                period_info = {
                    'period_type': 'Annual',
                    'period_name': f'{year} Annual',
                    'half_year': None,
                    'start_date': f'{year}-01-01',
                    'end_date': f'{year}-12-31',
                }
        elif len(available_months) == 2:
            # Two periods for this year = likely semi-annual
            if month in [6, 7]:
                period_info = {
                    'period_type': 'Semi-Annual',
                    'period_name': f'{year} H1',
                    'half_year': 'H1',
                    'start_date': f'{year}-01-01',
                    'end_date': f'{year}-06-30',
                }
            else:  # Assume the other is H2
                period_info = {
                    'period_type': 'Semi-Annual',
                    'period_name': f'{year} H2',
                    'half_year': 'H2',
                    'start_date': f'{year}-07-01',
                    'end_date': f'{year}-12-31',
                }
        else:
            # Multiple periods or fallback
            if month in [6, 7]:
                period_info = {
                    'period_type': 'Semi-Annual',
                    'period_name': f'{year} H1',
                    'half_year': 'H1',
                    'start_date': f'{year}-01-01',
                    'end_date': f'{year}-06-30',
                }
            elif month == 12:
                period_info = {
                    'period_type': 'Annual',
                    'period_name': f'{year} Annual',
                    'half_year': None,
                    'start_date': f'{year}-01-01',
                    'end_date': f'{year}-12-31',
                }
            else:
                # Default to annual for other months
                period_info = {
                    'period_type': 'Annual',
                    'period_name': f'{year} Annual',
                    'half_year': None,
                    'start_date': f'{year}-01-01',
                    'end_date': f'{year}-12-31',
                }
        
        period_info_list.append(period_info)
    
    # Add period info to dataframe
    period_df = pd.DataFrame(period_info_list)
    for col in period_df.columns:
        df_melted[col] = period_df[col]
    
    return df_melted

def transform_income_statement_to_airtable_format(excel_file_path, sheet_name='Sheet3'):
    """
    Transform Excel income statement from wide format (years as columns) 
    to long format suitable for Airtable import with smart period detection.
    """
    print("Reading Income Statement Excel file...")
    
    # Read from the correct sheet (Sheet3)
    try:
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        print(f"Trying to read from default sheet...")
        df = pd.read_excel(excel_file_path)
    
    # Debug: Show what we're reading
    print(f"Initial DataFrame shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Clean up the dataframe
    df = df.dropna(subset=[df.columns[0]])
    df.set_index(df.columns[0], inplace=True)
    
    # Remove the header row if it contains "INCOME STATEMENT"
    if 'INCOME STATEMENT' in str(df.index[0]):
        df = df.drop(df.index[0])
    
    # Debug: Check for any problematic columns
    print(f"Date columns after cleanup: {df.columns.tolist()}")
    for col in df.columns:
        sample_values = df[col].dropna().head(2).tolist()
        print(f"Column '{col}': {type(col)} | Sample values: {sample_values}")
    
    print(f"Found {len(df)} line items and {len(df.columns)} periods")
    
    # Transform from wide to long format
    df_melted = df.reset_index().melt(
        id_vars=[df.index.name or 'line_item'], 
        var_name='period_date', 
        value_name='amount'
    )
    
    # Debug: Check for NaN period_dates
    nan_periods = df_melted[df_melted['period_date'].isna()]
    if not nan_periods.empty:
        print(f"WARNING: Found {len(nan_periods)} records with NaN period_date")
        print("Sample NaN period records:")
        print(nan_periods.head())
    
    # Clean the line item names FIRST (before dropna)
    line_item_col = df.index.name or 'line_item'
    df_melted[line_item_col] = df_melted[line_item_col].str.strip()
    
    # Remove rows with NaN period_date to fix the "nan" period issue
    df_melted = df_melted.dropna(subset=['period_date'])
    
    # Clean the data - but be more careful about nulls
    # First convert to numeric
    df_melted['amount'] = pd.to_numeric(df_melted['amount'], errors='coerce')
    
    # Keep track of original data before dropping nulls
    print(f"Total records before cleaning: {len(df_melted)}")
    
    # Only drop rows where amount is NaN (not zero)
    df_melted = df_melted.dropna(subset=['amount'])
    print(f"Records after removing NaN amounts: {len(df_melted)}")
    
    # Round amounts to 2 decimal places
    df_melted['amount'] = df_melted['amount'].round(2)
    
    # Smart period detection based on actual dates
    print("Detecting period types from date patterns...")
    df_melted = smart_period_detection_is(df_melted)
    
    # Show detected periods
    period_summary = df_melted[['period_name', 'period_type', 'half_year']].drop_duplicates().sort_values('period_name')
    print("Detected periods:")
    for _, period in period_summary.iterrows():
        half_info = f" ({period['half_year']})" if period['half_year'] else ""
        print(f"  - {period['period_name']}: {period['period_type']}{half_info}")
    
    # Map line items to Airtable field names
    df_melted['airtable_field'] = df_melted[line_item_col].map(INCOME_STATEMENT_MAPPING)
    
    # Show mapping results with more detail
    mapped_data = df_melted.dropna(subset=['airtable_field'])
    unmapped_data = df_melted[df_melted['airtable_field'].isna()]
    
    print(f"Mapped {len(mapped_data)} records")
    print(f"Skipped {len(unmapped_data)} calculated/unmapped fields:")
    for item in unmapped_data[line_item_col].unique():
        # Show sample amounts for debugging
        sample_amounts = unmapped_data[unmapped_data[line_item_col] == item]['amount'].head(3).tolist()
        print(f"  - {item} (sample amounts: {sample_amounts})")
    
    # Add debug info for key totals - CHECK FOR EXACT NAMES
    key_terms = ['total_revenue', 'gross_profit', 'operating_profit', 'total_cost_of_revenue']
    for term in key_terms:
        matching_rows = df_melted[df_melted[line_item_col] == term]  # Exact match for cleaned names
        if not matching_rows.empty:
            print(f"\nFound '{term}' data:")
            for _, row in matching_rows.iterrows():
                mapped = "✓ MAPPED" if pd.notna(row['airtable_field']) else "✗ UNMAPPED"
                print(f"  {row['period_name']}: ${row['amount']:,.2f} {mapped}")
    
    return mapped_data

def group_income_statement_data_by_period(transformed_data):
    """
    Group the transformed income statement data by period for batch upload.
    """
    grouped = {}
    for period_name, group in transformed_data.groupby('period_name'):
        period_data = {}
        for _, row in group.iterrows():
            field_name = row['airtable_field']
            amount = row['amount']
            if pd.notna(amount):  # Include all values including zero for income statement
                period_data[field_name] = convert_to_json_serializable(amount)
        
        if period_data:
            # Include period metadata - convert all values to JSON serializable
            period_info = group.iloc[0]  # Get period info from first row
            grouped[period_name] = {
                'financial_data': period_data,
                'period_info': {
                    'period_name': convert_to_json_serializable(period_info['period_name']),
                    'period_type': convert_to_json_serializable(period_info['period_type']),
                    'half_year': convert_to_json_serializable(period_info['half_year']),
                    'start_date': convert_to_json_serializable(period_info['start_date']),
                    'end_date': convert_to_json_serializable(period_info['end_date']),
                    'year': convert_to_json_serializable(period_info['year'])
                }
            }
    
    return grouped

class AirtableIncomeStatementUploader:
    def __init__(self, base_id, personal_access_token):
        self.base_id = base_id
        self.pat = personal_access_token
        self.headers = {
            'Authorization': f'Bearer {personal_access_token}',
            'Content-Type': 'application/json'
        }
        self.base_url = f"https://api.airtable.com/v0/{base_id}"
    
    def get_existing_period(self, period_name, company_id):
        """Check if a period already exists for this company.
        Filters by period_name via Airtable formula, then matches company_id
        in Python (ARRAYJOIN on linked fields returns display names, not record IDs)."""
        url = f"{self.base_url}/financial_periods"
        params = {
            'filterByFormula': f'{{period_name}} = "{period_name}"'
        }

        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            records = response.json().get('records', [])
            for record in records:
                linked_companies = record.get('fields', {}).get('company', [])
                if company_id in linked_companies:
                    return record['id']
        return None
    
    def create_period_if_not_exists(self, period_data, company_id):
        """Create a financial period record if it doesn't exist."""
        period_name = period_data['period_name']
        
        # Check if period already exists
        existing_period_id = self.get_existing_period(period_name, company_id)
        if existing_period_id:
            print(f"  📅 Using existing period: {period_name}")
            return existing_period_id
        
        # Create new period with smart detection data - all values are already JSON serializable
        period_record = {
            'period_name': period_data['period_name'],
            'company': [company_id],
            'period_type': period_data['period_type'],
            'start_date': period_data['start_date'],
            'end_date': period_data['end_date'],
            'year': period_data['year'],
            'half_year': period_data['half_year'],
            'month': None  # Not used for semi-annual
        }
        
        url = f"{self.base_url}/financial_periods"
        payload = {"records": [{"fields": period_record}]}
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            period_type = period_data['period_type']
            half_info = f" ({period_data['half_year']})" if period_data['half_year'] else ""
            print(f"  📅 Created new {period_type} period: {period_name}{half_info}")
            return response.json()['records'][0]['id']
        else:
            print(f"Error creating period: {response.text}")
            return None

    def get_existing_income_statement_record(self, period_id, company_id, company_name=None, period_name=None):
        """Check if income statement record already exists for this company and period.
        Uses display names for Airtable formula filter (linked fields return display names, not IDs).
        Falls back to Python-side matching by record IDs if display names not provided."""
        url = f"{self.base_url}/income_statement_data"

        if company_name and period_name:
            params = {
                'filterByFormula': f'AND({{company}} = "{company_name}", {{period}} = "{period_name}")'
            }
        else:
            params = {}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                records = response.json().get('records', [])
                if company_name and period_name:
                    if records:
                        return records[0]
                else:
                    for record in records:
                        fields = record.get('fields', {})
                        if period_id in fields.get('period', []) and company_id in fields.get('company', []):
                            return record
            return None
        except Exception as e:
            print(f"Error checking for existing record: {str(e)}")
            return None

    def upload_income_statement(self, period_id, financial_data, data_source, company_id, user_email=None, publication_status='submitted', company_name=None, period_name=None):
        """
        Upload or update income statement data for a specific period.

        Checks if record exists for this company+period:
        - If exists: UPDATE (overwrites existing data)
        - If new: CREATE (creates new record)

        Args:
            publication_status: 'submitted' for user uploads (requires admin approval),
                              'published' for admin/migration scripts (immediately visible)
            company_name: display name for Airtable linked field lookup
            period_name: display name for Airtable linked field lookup
        """
        # Check for existing record
        existing_record = self.get_existing_income_statement_record(period_id, company_id, company_name=company_name, period_name=period_name)

        # Prepare record data
        record_data = {
            'company': [company_id],
            'period': [period_id],
            'data_source': data_source,
            'upload_date': datetime.now().strftime('%Y-%m-%d'),
            'publication_status': publication_status,
            'submitted_by': user_email or 'unknown',
            'submitted_date': datetime.now().strftime('%Y-%m-%d')
        }

        # Add financial data (already JSON serializable)
        record_data.update(financial_data)

        if existing_record:
            # UPDATE existing record (overwrite scenario)
            record_id = existing_record['id']
            url = f"{self.base_url}/income_statement_data/{record_id}"
            payload = {"fields": record_data}

            try:
                response = requests.patch(url, headers=self.headers, json=payload)

                if response.status_code == 200:
                    return {
                        'success': True,
                        'action': 'updated',
                        'record_id': record_id,
                        'message': f'Income statement updated for {data_source}'
                    }
                else:
                    return {
                        'success': False,
                        'action': 'error',
                        'record_id': None,
                        'message': f'Failed to update income statement: {response.text}'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'action': 'error',
                    'record_id': None,
                    'message': f'Exception during update: {str(e)}'
                }
        else:
            # CREATE new record (first upload for this period)
            url = f"{self.base_url}/income_statement_data"
            payload = {"records": [{"fields": record_data}]}

            try:
                response = requests.post(url, headers=self.headers, json=payload)

                if response.status_code == 200:
                    created_records = response.json().get('records', [])
                    if created_records:
                        return {
                            'success': True,
                            'action': 'created',
                            'record_id': created_records[0]['id'],
                            'message': f'Income statement created for {data_source}'
                        }
                    else:
                        return {
                            'success': False,
                            'action': 'error',
                            'record_id': None,
                            'message': 'No records returned after creation'
                        }
                else:
                    return {
                        'success': False,
                        'action': 'error',
                        'record_id': None,
                        'message': f'Failed to create income statement: {response.text}'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'action': 'error',
                    'record_id': None,
                    'message': f'Exception during creation: {str(e)}'
                }
    
    def log_import(self, company_id, file_name, records_count, status, error_log="", user_email=None):
        """Log the import activity."""
        log_data = {
            'company': [company_id],
            'import_source': 'Income Statement Python Script',
            'file_name': file_name,
            'records_imported_is': records_count,
            'records_imported_bs': 0,
            'import_status': status,
            'error_log': error_log,
            'imported_by': user_email or 'script_user'
        }
        
        url = f"{self.base_url}/data_import_log"
        payload = {"records": [{"fields": log_data}]}
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json() if response.status_code == 200 else None

def main_income_statement():
    """
    Main function to transform and upload income statement data with smart period detection.
    """
    
    # CONFIGURATION - Loaded from .env file
    EXCEL_FILE_PATH = os.getenv('INCOME_STATEMENT_FILE_PATH', './historical_data/winter_income_statement.xlsx')
    AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
    AIRTABLE_PAT = os.getenv('AIRTABLE_PAT')
    COMPANY_ID = os.getenv('COMPANY_ID')
    DATA_SOURCE = f'IS_Historical_Import_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    # Validation
    if not os.path.exists(EXCEL_FILE_PATH):
        raise FileNotFoundError(f"Income Statement file not found: {EXCEL_FILE_PATH}")
    if not all([AIRTABLE_BASE_ID, AIRTABLE_PAT, COMPANY_ID]):
        raise ValueError("Missing required environment variables")
    
    print(f"Using Income Statement file: {EXCEL_FILE_PATH}")
    print(f"Using Airtable Base: {AIRTABLE_BASE_ID[:8]}...")
    print(f"Data source: {DATA_SOURCE}")
    
    try:
        # Step 1: Transform the Excel data with smart period detection (using Sheet3)
        print("Starting income statement data transformation...")
        transformed_data = transform_income_statement_to_airtable_format(EXCEL_FILE_PATH, sheet_name='Sheet3')
        
        # Step 2: Group data by period (now includes period metadata)
        print("Grouping income statement data by period...")
        grouped_data = group_income_statement_data_by_period(transformed_data)
        
        # Step 3: Initialize Airtable uploader
        uploader = AirtableIncomeStatementUploader(AIRTABLE_BASE_ID, AIRTABLE_PAT)
        
        # Step 4: Create periods and upload data
        uploaded_records = 0
        errors = []
        
        for period_name, period_data in grouped_data.items():
            print(f"Processing {period_data['period_info']['period_type']}: {period_name}...")
            
            # Create period record with smart detection
            period_id = uploader.create_period_if_not_exists(period_data['period_info'], COMPANY_ID)
            
            if period_id:
                # Upload income statement data
                record_id = uploader.upload_income_statement(
                    period_id, period_data['financial_data'], DATA_SOURCE, COMPANY_ID
                )
                
                if record_id:
                    uploaded_records += 1
                    period_type = period_data['period_info']['period_type']
                    print(f"✅ Successfully uploaded {period_type} income statement data for {period_name}")
                else:
                    errors.append(f"Failed to upload income statement for {period_name}")
            else:
                errors.append(f"Failed to create/find period for {period_name}")
        
        # Step 5: Log the import
        status = "Success" if len(errors) == 0 else "Partial" if uploaded_records > 0 else "Failed"
        error_log = "; ".join(errors) if errors else ""
        
        uploader.log_import(COMPANY_ID, EXCEL_FILE_PATH, uploaded_records, status, error_log)
        
        # Summary
        print(f"\n=== INCOME STATEMENT IMPORT SUMMARY ===")
        print(f"Total periods processed: {len(grouped_data)}")
        print(f"Successfully uploaded: {uploaded_records}")
        print(f"Errors: {len(errors)}")
        if errors:
            print("Error details:")
            for error in errors:
                print(f"  - {error}")
        
    except Exception as e:
        print(f"Income statement script failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main_income_statement()