"""
Data Uploader Module
Handles uploading validated financial data to Airtable
Uses existing upload classes from data_transformation scripts
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st

# Add parent directory to path to import transformation modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from data_transformation_bs import AirtableBalanceSheetUploader
from data_transformation_is import AirtableIncomeStatementUploader
from pages.data_input.data_validator import (
    validate_balance_sheet,
    validate_income_statement,
    validate_period_format,
    get_period_details
)

# Load environment variables
load_dotenv()


def get_company_id(company_name):
    """Get Airtable company ID from company name"""
    from shared.airtable_connection import get_companies_cached

    companies = get_companies_cached()
    for company in companies:
        if company['name'] == company_name:
            return company['id']
    return None


def upload_balance_sheet_to_airtable(company_name, period_name, year, data, user_email):
    """
    Upload Balance Sheet data to Airtable
    Returns: (success: bool, message: str)
    """

    # Validate period format
    valid_period, period_error = validate_period_format(period_name)
    if not valid_period:
        return False, period_error

    # Validate data
    is_valid, errors = validate_balance_sheet(data)
    if not is_valid:
        error_msg = "Validation failed:\n" + "\n".join([f"• {err}" for err in errors])
        return False, error_msg

    # Get company ID
    company_id = get_company_id(company_name)
    if not company_id:
        return False, f"Company '{company_name}' not found in Airtable"

    # Get Airtable credentials
    try:
        airtable_base_id = st.secrets.get("AIRTABLE_BASE_ID") or os.getenv("AIRTABLE_BASE_ID")
        airtable_pat = st.secrets.get("AIRTABLE_PAT") or os.getenv("AIRTABLE_PAT")
    except:
        airtable_base_id = os.getenv("AIRTABLE_BASE_ID")
        airtable_pat = os.getenv("AIRTABLE_PAT")

    if not airtable_base_id or not airtable_pat:
        return False, "Airtable credentials not found"

    # Initialize uploader
    uploader = AirtableBalanceSheetUploader(airtable_base_id, airtable_pat)

    # Get period details
    period_info = get_period_details(period_name)
    if not period_info:
        return False, f"Invalid period name: {period_name}"

    try:
        # Create or get period record
        period_id = uploader.create_period_if_not_exists(period_info, company_id)
        if not period_id:
            return False, "Failed to create/find period record in Airtable"

        # Prepare financial data (remove calculated totals that aren't base fields)
        financial_data = {k: v for k, v in data.items() if v is not None}

        # Create data source identifier
        data_source = f'Dashboard_Upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

        # Upload balance sheet data
        result = uploader.upload_balance_sheet(
            period_id,
            financial_data,
            data_source,
            company_id,
            user_email
        )

        if result['success']:
            # Log the import
            uploader.log_import(
                company_id,
                f"Dashboard Upload - {period_name}",
                1,  # records count
                "Success",
                "",
                user_email
            )

            # Different messages for create vs. update
            if result['action'] == 'updated':
                message = f"Successfully UPDATED Balance Sheet for {company_name} - {period_name}. Previous data was overwritten. Status: 'submitted' - data will appear after admin publishes."
            else:  # created
                message = f"Successfully uploaded Balance Sheet for {company_name} - {period_name}. Status: 'submitted' - data will appear after admin publishes."

            return True, message
        else:
            return False, f"Upload failed: {result['message']}"

    except Exception as e:
        return False, f"Upload error: {str(e)}"


def upload_income_statement_to_airtable(company_name, period_name, year, data, user_email):
    """
    Upload Income Statement data to Airtable
    Returns: (success: bool, message: str)
    """

    # Validate period format
    valid_period, period_error = validate_period_format(period_name)
    if not valid_period:
        return False, period_error

    # Validate data
    is_valid, errors = validate_income_statement(data)
    if not is_valid:
        error_msg = "Validation failed:\n" + "\n".join([f"• {err}" for err in errors])
        return False, error_msg

    # Get company ID
    company_id = get_company_id(company_name)
    if not company_id:
        return False, f"Company '{company_name}' not found in Airtable"

    # Get Airtable credentials
    try:
        airtable_base_id = st.secrets.get("AIRTABLE_BASE_ID") or os.getenv("AIRTABLE_BASE_ID")
        airtable_pat = st.secrets.get("AIRTABLE_PAT") or os.getenv("AIRTABLE_PAT")
    except:
        airtable_base_id = os.getenv("AIRTABLE_BASE_ID")
        airtable_pat = os.getenv("AIRTABLE_PAT")

    if not airtable_base_id or not airtable_pat:
        return False, "Airtable credentials not found"

    # Initialize uploader
    uploader = AirtableIncomeStatementUploader(airtable_base_id, airtable_pat)

    # Get period details
    period_info = get_period_details(period_name)
    if not period_info:
        return False, f"Invalid period name: {period_name}"

    try:
        # Create or get period record
        period_id = uploader.create_period_if_not_exists(period_info, company_id)
        if not period_id:
            return False, "Failed to create/find period record in Airtable"

        # Prepare financial data
        financial_data = {k: v for k, v in data.items() if v is not None}

        # Create data source identifier
        data_source = f'Dashboard_Upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

        # Upload income statement data
        result = uploader.upload_income_statement(
            period_id,
            financial_data,
            data_source,
            company_id,
            user_email
        )

        if result['success']:
            # Log the import
            uploader.log_import(
                company_id,
                f"Dashboard Upload - {period_name}",
                1,  # records count
                "Success",
                "",
                user_email
            )

            # Different messages for create vs. update
            if result['action'] == 'updated':
                message = f"Successfully UPDATED Income Statement for {company_name} - {period_name}. Previous data was overwritten. Status: 'submitted' - data will appear after admin publishes."
            else:  # created
                message = f"Successfully uploaded Income Statement for {company_name} - {period_name}. Status: 'submitted' - data will appear after admin publishes."

            return True, message
        else:
            return False, f"Upload failed: {result['message']}"

    except Exception as e:
        return False, f"Upload error: {str(e)}"
