"""
User Management Admin Page
Allows super admins to create, view, and manage user accounts
"""

import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from shared.auth_utils import require_auth, is_super_admin
from shared.supabase_connection import get_supabase_admin_client
from shared.airtable_connection import _escape_airtable_value


# ============================================================================
# FORM STATE MANAGEMENT FUNCTIONS
# ============================================================================

def initialize_create_form_state():
    """Initialize session state for Create User form fields"""
    if 'create_form_email' not in st.session_state:
        st.session_state.create_form_email = ''
    if 'create_form_name' not in st.session_state:
        st.session_state.create_form_name = ''
    if 'create_form_role' not in st.session_state:
        st.session_state.create_form_role = 'company_user'
    if 'create_form_company_id' not in st.session_state:
        st.session_state.create_form_company_id = None
    if 'create_form_can_upload' not in st.session_state:
        st.session_state.create_form_can_upload = False
    if 'create_form_method' not in st.session_state:
        st.session_state.create_form_method = 'manual_password'
    if 'create_form_temp_password' not in st.session_state:
        st.session_state.create_form_temp_password = ''
    if 'create_form_success_msg' not in st.session_state:
        st.session_state.create_form_success_msg = None
    if 'create_form_success_info' not in st.session_state:
        st.session_state.create_form_success_info = None


def clear_create_form_fields():
    """Clear all Create User form fields by resetting session state"""
    # Clear the tracking variables
    st.session_state.create_form_email = ''
    st.session_state.create_form_name = ''
    st.session_state.create_form_role = 'company_user'
    st.session_state.create_form_company_id = None
    st.session_state.create_form_can_upload = False
    st.session_state.create_form_method = 'manual_password'
    st.session_state.create_form_temp_password = ''

    # Also clear the widget keys (these are the actual form values in Streamlit)
    widget_keys = [
        'create_email_input',
        'create_name_input',
        'create_role_selector',
        'create_company_selector',
        'create_upload_checkbox',
        'create_method_radio',
        'create_password_input'
    ]
    for key in widget_keys:
        if key in st.session_state:
            del st.session_state[key]


def initialize_edit_form_state():
    """Initialize session state for Edit Permissions form tracking"""
    if 'edit_form_success_msg' not in st.session_state:
        st.session_state.edit_form_success_msg = None
    if 'edit_form_last_user_id' not in st.session_state:
        st.session_state.edit_form_last_user_id = None
    if 'edit_form_clear_requested' not in st.session_state:
        st.session_state.edit_form_clear_requested = False


def handle_edit_user_selection_change(new_user_id):
    """Clear edit form success message when user selection changes"""
    if st.session_state.edit_form_last_user_id != new_user_id:
        st.session_state.edit_form_success_msg = None
        st.session_state.edit_form_last_user_id = new_user_id


def clear_edit_form():
    """Clear edit form state to allow editing another user"""
    st.session_state.edit_form_success_msg = None
    st.session_state.edit_form_last_user_id = None
    st.session_state.edit_form_clear_requested = True
    # Clear the user selector widget key to reset selection
    if 'edit_user_selector' in st.session_state:
        del st.session_state['edit_user_selector']


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

def create_user_management_sidebar():
    """Create sidebar navigation for user management page"""
    with st.sidebar:
        st.markdown("### 👥 User Management")
        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Navigation back to dashboard at the top
        if st.button("🏠 Back to Dashboard", key="back_to_dashboard_user_mgmt", use_container_width=True):
            st.session_state.current_page = "overview"
            st.session_state.nav_tab = "group"  # Ensure we're on group tab for overview
            st.rerun()


# ============================================================================
# USER FETCHING FUNCTIONS
# ============================================================================

def fetch_all_users():
    """
    Fetch all users from the database with their company information and email addresses.

    Returns:
        list: List of user dictionaries with company data and email joined
    """
    try:
        supabase = get_supabase_admin_client()

        # Fetch all users with their company information from user_profiles
        response = supabase.table('user_profiles') \
            .select('*, companies(*)') \
            .order('created_at', desc=True) \
            .execute()

        users = response.data

        # Fetch email addresses from auth.users for each user
        for user in users:
            try:
                # Get user from auth system to retrieve email
                auth_user = supabase.auth.admin.get_user_by_id(user['id'])
                if auth_user and auth_user.user:
                    user['email'] = auth_user.user.email
                else:
                    user['email'] = 'N/A'
            except Exception as e:
                # If we can't get the email, set to N/A
                user['email'] = 'N/A'

        return users

    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return []


def fetch_all_companies():
    """
    Fetch all companies from the database.

    Returns:
        list: List of company dictionaries
    """
    try:
        supabase = get_supabase_admin_client()

        response = supabase.table('companies') \
            .select('*') \
            .order('display_name') \
            .execute()

        return response.data

    except Exception as e:
        st.error(f"Error fetching companies: {e}")
        return []


def create_new_user(email, full_name, role, company_id, can_upload_data, temporary_password):
    """
    Create a new user in Supabase Auth and user_profiles table with manual password.

    Args:
        email: User's email address
        full_name: User's full name
        role: User's role (company_user or super_admin)
        company_id: Company ID (None for super_admin)
        can_upload_data: Whether user can upload data
        temporary_password: Temporary password for the user

    Returns:
        dict: Result dictionary with success status and message
    """
    try:
        supabase = get_supabase_admin_client()

        # Create user in Supabase Auth
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": temporary_password,
            "email_confirm": True  # Auto-confirm email
        })

        user_id = auth_response.user.id

        # Create user profile in database
        profile_data = {
            "id": user_id,
            "full_name": full_name,
            "role": role,
            "company_id": company_id if role == "company_user" else None,
            "can_upload_data": can_upload_data,
            "is_active": True
        }

        supabase.table('user_profiles').insert(profile_data).execute()

        return {
            "success": True,
            "message": f"User {email} created successfully!",
            "method": "manual"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating user: {str(e)}"
        }


def create_new_user_with_invitation(email, full_name, role, company_id, can_upload_data):
    """
    Create a new user and send them an invitation email to set their own password.

    Args:
        email: User's email address
        full_name: User's full name
        role: User's role (company_user or super_admin)
        company_id: Company ID (None for super_admin)
        can_upload_data: Whether user can upload data

    Returns:
        dict: Result dictionary with success status and message
    """
    try:
        supabase = get_supabase_admin_client()

        # Create user with Supabase invite (NO PASSWORD - user sets it)
        auth_response = supabase.auth.admin.invite_user_by_email(
            email,
            options={
                "data": {
                    "full_name": full_name
                }
            }
        )

        user_id = auth_response.user.id

        # Create user profile in database
        profile_data = {
            "id": user_id,
            "full_name": full_name,
            "role": role,
            "company_id": company_id if role == "company_user" else None,
            "can_upload_data": can_upload_data,
            "is_active": True
        }

        supabase.table('user_profiles').insert(profile_data).execute()

        return {
            "success": True,
            "message": f"Invitation sent to {email}!",
            "method": "invitation"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending invitation: {str(e)}"
        }


def update_user_permissions(user_id, full_name, role, company_id, can_upload_data, is_active):
    """
    Update user permissions and profile information.

    Args:
        user_id: User's UUID
        full_name: User's full name
        role: User's role (company_user or super_admin)
        company_id: Company ID (None for super_admin)
        can_upload_data: Whether user can upload data
        is_active: Whether user is active

    Returns:
        dict: Result dictionary with success status and message
    """
    try:
        supabase = get_supabase_admin_client()

        # Update user profile
        update_data = {
            "full_name": full_name,
            "role": role,
            "company_id": company_id if role == "company_user" else None,
            "can_upload_data": can_upload_data,
            "is_active": is_active
        }

        supabase.table('user_profiles') \
            .update(update_data) \
            .eq('id', user_id) \
            .execute()

        return {
            "success": True,
            "message": "User permissions updated successfully!"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating user: {str(e)}"
        }


def delete_user(user_id):
    """
    Delete a user from Supabase Auth (profile will cascade delete).

    Args:
        user_id: User's UUID

    Returns:
        dict: Result dictionary with success status and message
    """
    try:
        supabase = get_supabase_admin_client()

        # Delete user from Supabase Auth (will cascade to user_profiles)
        response = supabase.auth.admin.delete_user(user_id)

        return {
            "success": True,
            "message": "User deleted successfully!"
        }

    except Exception as e:
        # Print full error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"Delete user error details:\n{error_details}")

        return {
            "success": False,
            "message": f"Error deleting user: {str(e)}"
        }


# ============================================================================
# PUBLICATION CONTROL HELPER FUNCTIONS
# ============================================================================

def get_airtable_credentials():
    """Get Airtable credentials from secrets or environment."""
    try:
        base_id = st.secrets.get("AIRTABLE_BASE_ID") or os.getenv("AIRTABLE_BASE_ID")
        pat = st.secrets.get("AIRTABLE_PAT") or os.getenv("AIRTABLE_PAT")
    except:
        load_dotenv()
        base_id = os.getenv("AIRTABLE_BASE_ID")
        pat = os.getenv("AIRTABLE_PAT")
    return base_id, pat


def get_pending_data_submissions():
    """
    Fetch all pending data submissions (publication_status='submitted').

    Returns:
        {
            'has_pending': bool,
            'by_period': {
                '2025 Annual': [
                    {
                        'company_name': 'A-1',
                        'has_is': True,
                        'has_bs': True,
                        'submitted_by': 'user@example.com',
                        'submitted_date': '2025-01-15',
                        'is_record_id': 'recXXX',
                        'bs_record_id': 'recYYY'
                    }
                ]
            }
        }
    """
    base_id, pat = get_airtable_credentials()
    headers = {'Authorization': f'Bearer {pat}', 'Content-Type': 'application/json'}
    base_url = f"https://api.airtable.com/v0/{base_id}"

    try:
        # Fetch submitted BS records
        bs_response = requests.get(
            f"{base_url}/balance_sheet_data",
            headers=headers,
            params={'filterByFormula': "{publication_status}='submitted'"}
        )
        bs_records = bs_response.json().get('records', []) if bs_response.status_code == 200 else []

        # Fetch submitted IS records
        is_response = requests.get(
            f"{base_url}/income_statement_data",
            headers=headers,
            params={'filterByFormula': "{publication_status}='submitted'"}
        )
        is_records = is_response.json().get('records', []) if is_response.status_code == 200 else []

        # Collect unique period IDs and company IDs to fetch names
        period_ids = set()
        company_ids = set()
        for record in bs_records + is_records:
            period = record['fields'].get('period', [])
            if period and len(period) > 0:
                period_ids.add(period[0])  # period is an array of linked record IDs

            company = record['fields'].get('company', [])
            if company and len(company) > 0:
                company_ids.add(company[0])  # company is an array of linked record IDs

        # Fetch period names from financial_periods table
        period_id_to_name = {}
        for period_id in period_ids:
            try:
                period_response = requests.get(
                    f"{base_url}/financial_periods/{period_id}",
                    headers=headers
                )
                if period_response.status_code == 200:
                    period_data = period_response.json()
                    period_name = period_data['fields'].get('period_name', 'Unknown')
                    period_id_to_name[period_id] = period_name
            except:
                period_id_to_name[period_id] = 'Unknown'

        # Fetch company names from companies table
        company_id_to_name = {}
        for company_id in company_ids:
            try:
                company_response = requests.get(
                    f"{base_url}/companies/{company_id}",
                    headers=headers
                )
                if company_response.status_code == 200:
                    company_data = company_response.json()
                    company_name = company_data['fields'].get('company_name', 'Unknown')
                    company_id_to_name[company_id] = company_name
            except:
                company_id_to_name[company_id] = 'Unknown'

        # Group by period and company
        pending_by_period = {}

        for record in bs_records:
            fields = record['fields']

            # Get period name - try lookup field first, then linked record
            period = fields.get('period_name', None)
            if not period:
                # Get period ID from linked record field and look up the name
                period_ids_list = fields.get('period', [])
                period_id = period_ids_list[0] if period_ids_list else None
                period = period_id_to_name.get(period_id, 'Unknown') if period_id else 'Unknown'

            # Get company name - try lookup field first, then linked record
            company = fields.get('company_name', None)
            if not company:
                company_list = fields.get('company', [])
                company_id = company_list[0] if company_list else None
                company = company_id_to_name.get(company_id, 'Unknown') if company_id else 'Unknown'

            if period not in pending_by_period:
                pending_by_period[period] = {}
            if company not in pending_by_period[period]:
                pending_by_period[period][company] = {
                    'company_name': company, 'has_is': False, 'has_bs': False,
                    'submitted_by': fields.get('submitted_by'), 'submitted_date': fields.get('submitted_date'),
                    'is_record_id': None, 'bs_record_id': None
                }
            pending_by_period[period][company]['has_bs'] = True
            pending_by_period[period][company]['bs_record_id'] = record['id']

        for record in is_records:
            fields = record['fields']

            # Get period name - try lookup field first, then linked record
            period = fields.get('period_name', None)
            if not period:
                # Get period ID from linked record field and look up the name
                period_ids_list = fields.get('period', [])
                period_id = period_ids_list[0] if period_ids_list else None
                period = period_id_to_name.get(period_id, 'Unknown') if period_id else 'Unknown'

            # Get company name - try lookup field first, then linked record
            company = fields.get('company_name', None)
            if not company:
                company_list = fields.get('company', [])
                company_id = company_list[0] if company_list else None
                company = company_id_to_name.get(company_id, 'Unknown') if company_id else 'Unknown'

            if period not in pending_by_period:
                pending_by_period[period] = {}
            if company not in pending_by_period[period]:
                pending_by_period[period][company] = {
                    'company_name': company, 'has_is': False, 'has_bs': False,
                    'submitted_by': fields.get('submitted_by'), 'submitted_date': fields.get('submitted_date'),
                    'is_record_id': None, 'bs_record_id': None
                }
            pending_by_period[period][company]['has_is'] = True
            pending_by_period[period][company]['is_record_id'] = record['id']
            # Update submitted info if IS was submitted more recently
            pending_by_period[period][company]['submitted_by'] = fields.get('submitted_by')
            pending_by_period[period][company]['submitted_date'] = fields.get('submitted_date')

        return {
            'has_pending': len(pending_by_period) > 0,
            'by_period': {p: list(c.values()) for p, c in pending_by_period.items()}
        }
    except Exception as e:
        return {'has_pending': False, 'by_period': {}, 'error': str(e)}


def publish_all_data_for_period(period_name, admin_email):
    """
    Bulk publish all submitted data for a period.
    Uses batch PATCH (max 10 records per request).

    Returns:
        {
            'success': bool,
            'message': str,
            'is_count': int,
            'bs_count': int,
            'errors': list
        }
    """
    base_id, pat = get_airtable_credentials()
    headers = {'Authorization': f'Bearer {pat}', 'Content-Type': 'application/json'}
    base_url = f"https://api.airtable.com/v0/{base_id}"

    errors = []
    is_count = 0
    bs_count = 0

    try:
        # Filter using period display name (Airtable matches linked record primary field)
        # Fetch BS records to publish
        bs_filter = f"AND({{period}}='{period_name}',{{publication_status}}='submitted')"
        bs_response = requests.get(
            f"{base_url}/balance_sheet_data",
            headers=headers,
            params={'filterByFormula': bs_filter}
        )
        bs_records = bs_response.json().get('records', []) if bs_response.status_code == 200 else []

        # Batch update BS (10 per request)
        for i in range(0, len(bs_records), 10):
            batch = bs_records[i:i+10]
            payload = {
                'records': [
                    {
                        'id': r['id'],
                        'fields': {
                            'publication_status': 'published',
                            'published_by': admin_email,
                            'published_date': datetime.now().strftime('%Y-%m-%d')
                        }
                    }
                    for r in batch
                ]
            }
            response = requests.patch(f"{base_url}/balance_sheet_data", headers=headers, json=payload)
            if response.status_code == 200:
                bs_count += len(batch)
            else:
                errors.append(f"BS batch {i//10 + 1} failed: {response.text}")

        # Fetch IS records to publish
        is_filter = f"AND({{period}}='{period_name}',{{publication_status}}='submitted')"
        is_response = requests.get(
            f"{base_url}/income_statement_data",
            headers=headers,
            params={'filterByFormula': is_filter}
        )
        is_records = is_response.json().get('records', []) if is_response.status_code == 200 else []

        # Batch update IS (10 per request)
        for i in range(0, len(is_records), 10):
            batch = is_records[i:i+10]
            payload = {
                'records': [
                    {
                        'id': r['id'],
                        'fields': {
                            'publication_status': 'published',
                            'published_by': admin_email,
                            'published_date': datetime.now().strftime('%Y-%m-%d')
                        }
                    }
                    for r in batch
                ]
            }
            response = requests.patch(f"{base_url}/income_statement_data", headers=headers, json=payload)
            if response.status_code == 200:
                is_count += len(batch)
            else:
                errors.append(f"IS batch {i//10 + 1} failed: {response.text}")

        return {
            'success': len(errors) == 0,
            'message': f'Successfully published all data for {period_name}' if not errors else f'Partial: {len(errors)} batch(es) failed',
            'is_count': is_count,
            'bs_count': bs_count,
            'errors': errors
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Publication failed: {str(e)}',
            'is_count': is_count,
            'bs_count': bs_count,
            'errors': [str(e)]
        }


@st.cache_data(ttl=60, show_spinner=False)
def get_pending_wc_submissions():
    """
    Fetch all pending W&C submissions (status='draft') grouped by period.
    Cached for 60 seconds to avoid re-fetching on every rerun.

    Returns:
        {
            'has_pending': bool,
            'by_period': {
                '2024 Annual': [
                    {
                        'company_name': 'A-1',
                        'wins_count': 3,
                        'challenges_count': 2,
                        'action_items_count': 4
                    }
                ]
            }
        }
    """
    base_id, pat = get_airtable_credentials()
    headers = {'Authorization': f'Bearer {pat}', 'Content-Type': 'application/json'}
    base_url = f"https://api.airtable.com/v0/{base_id}"

    try:
        # Fetch all draft records from wins, challenges, action_items
        tables = ['wins', 'challenges', 'action_items']
        all_drafts = {'wins': [], 'challenges': [], 'action_items': []}

        for table in tables:
            response = requests.get(
                f"{base_url}/{table}",
                headers=headers,
                params={'filterByFormula': "AND({status}='draft',{is_active}=TRUE())"}
            )
            if response.status_code == 200:
                all_drafts[table] = response.json().get('records', [])

        # Collect unique period IDs
        period_ids = set()
        for table in tables:
            for record in all_drafts[table]:
                period = record['fields'].get('period', [])
                if period and len(period) > 0:
                    period_ids.add(period[0])

        # Fetch period info (company name and period name)
        period_info = {}  # period_id -> {company_name, period_name}
        company_ids_to_fetch = set()

        # First pass: get period data and collect company IDs
        for period_id in period_ids:
            try:
                period_response = requests.get(
                    f"{base_url}/financial_periods/{period_id}",
                    headers=headers
                )
                if period_response.status_code == 200:
                    period_data = period_response.json()
                    fields = period_data.get('fields', {})
                    period_name = fields.get('period_name', 'Unknown')

                    # Try lookup field first, otherwise get company linked record
                    company_name = None
                    if fields.get('company_name'):
                        # Lookup field - could be array or string
                        cn = fields.get('company_name')
                        company_name = cn[0] if isinstance(cn, list) else cn

                    # Get linked company ID for fallback
                    company_link = fields.get('company', [])
                    company_id = company_link[0] if company_link else None

                    period_info[period_id] = {
                        'period_name': period_name,
                        'company_name': company_name,
                        'company_id': company_id
                    }

                    if not company_name and company_id:
                        company_ids_to_fetch.add(company_id)
            except:
                period_info[period_id] = {'period_name': 'Unknown', 'company_name': 'Unknown', 'company_id': None}

        # Fetch company names for any missing
        company_names = {}
        for company_id in company_ids_to_fetch:
            try:
                company_response = requests.get(
                    f"{base_url}/companies/{company_id}",
                    headers=headers
                )
                if company_response.status_code == 200:
                    company_data = company_response.json()
                    company_names[company_id] = company_data.get('fields', {}).get('company_name', 'Unknown')
            except:
                company_names[company_id] = 'Unknown'

        # Update period_info with fetched company names
        for period_id, info in period_info.items():
            if not info['company_name'] and info.get('company_id'):
                info['company_name'] = company_names.get(info['company_id'], 'Unknown')

        # Group by period name and company
        pending_by_period = {}

        for table in tables:
            for record in all_drafts[table]:
                period_list = record['fields'].get('period', [])
                if not period_list:
                    continue
                period_id = period_list[0]
                info = period_info.get(period_id, {'period_name': 'Unknown', 'company_name': 'Unknown'})
                period_name = info['period_name']
                company_name = info['company_name']

                if period_name not in pending_by_period:
                    pending_by_period[period_name] = {}
                if company_name not in pending_by_period[period_name]:
                    pending_by_period[period_name][company_name] = {
                        'company_name': company_name,
                        'wins_count': 0,
                        'challenges_count': 0,
                        'action_items_count': 0
                    }

                # Increment count
                if table == 'wins':
                    pending_by_period[period_name][company_name]['wins_count'] += 1
                elif table == 'challenges':
                    pending_by_period[period_name][company_name]['challenges_count'] += 1
                else:
                    pending_by_period[period_name][company_name]['action_items_count'] += 1

        return {
            'has_pending': len(pending_by_period) > 0,
            'by_period': {p: list(c.values()) for p, c in pending_by_period.items()}
        }
    except Exception as e:
        return {'has_pending': False, 'by_period': {}, 'error': str(e)}


def publish_all_wc_for_period(period_name, admin_email):
    """
    Bulk publish all W&C draft records for a period.
    Updates status from 'draft' to 'published'.

    Returns:
        {
            'success': bool,
            'message': str,
            'wins_count': int,
            'challenges_count': int,
            'action_items_count': int,
            'errors': list
        }
    """
    base_id, pat = get_airtable_credentials()
    headers = {'Authorization': f'Bearer {pat}', 'Content-Type': 'application/json'}
    base_url = f"https://api.airtable.com/v0/{base_id}"

    errors = []
    counts = {'wins': 0, 'challenges': 0, 'action_items': 0}

    try:
        # Get all period IDs for this period_name
        periods_response = requests.get(
            f"{base_url}/financial_periods",
            headers=headers,
            params={'filterByFormula': f"{{period_name}}='{_escape_airtable_value(period_name)}'"}
        )
        if periods_response.status_code != 200:
            return {
                'success': False,
                'message': f'Failed to fetch periods: {periods_response.text}',
                'wins_count': 0, 'challenges_count': 0, 'action_items_count': 0,
                'errors': [periods_response.text]
            }

        period_records = periods_response.json().get('records', [])
        if not period_records:
            return {
                'success': False,
                'message': f'No period records found for {period_name}',
                'wins_count': 0, 'challenges_count': 0, 'action_items_count': 0,
                'errors': [f'Period {period_name} not found']
            }

        period_ids = set(r['id'] for r in period_records)

        # Process each table - fetch ALL drafts and filter by period in Python
        tables = ['wins', 'challenges', 'action_items']
        for table in tables:
            # Fetch all draft records
            filter_formula = "AND({status}='draft',{is_active}=TRUE())"
            response = requests.get(
                f"{base_url}/{table}",
                headers=headers,
                params={'filterByFormula': filter_formula}
            )
            if response.status_code != 200:
                errors.append(f"Failed to fetch {table}: {response.text}")
                continue

            all_records = response.json().get('records', [])

            # Filter to only records matching our period IDs
            records = []
            for r in all_records:
                record_period = r['fields'].get('period', [])
                if record_period and record_period[0] in period_ids:
                    records.append(r)

            if not records:
                continue

            # Batch update (10 per request)
            for i in range(0, len(records), 10):
                batch = records[i:i+10]
                payload = {
                    'records': [
                        {
                            'id': r['id'],
                            'fields': {'status': 'published'}
                        }
                        for r in batch
                    ]
                }
                update_response = requests.patch(f"{base_url}/{table}", headers=headers, json=payload)
                if update_response.status_code == 200:
                    counts[table] += len(batch)
                else:
                    errors.append(f"{table} batch {i//10 + 1} failed: {update_response.text}")

        total = counts['wins'] + counts['challenges'] + counts['action_items']
        return {
            'success': len(errors) == 0,
            'message': f'Published {total} W&C items for {period_name}' if not errors else f'Partial: {len(errors)} error(s)',
            'wins_count': counts['wins'],
            'challenges_count': counts['challenges'],
            'action_items_count': counts['action_items'],
            'errors': errors
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Publication failed: {str(e)}',
            'wins_count': 0, 'challenges_count': 0, 'action_items_count': 0,
            'errors': [str(e)]
        }


def create_user_management_page():
    """Create the user management admin interface"""

    # Require authentication
    require_auth()

    # Check if user is super admin
    if not is_super_admin():
        st.error("❌ Access Denied")
        st.info("Only super administrators can access this page.")
        st.stop()

    # Create custom sidebar with navigation
    create_user_management_sidebar()

    # If we get here, user is authenticated AND is super admin
    st.title("👥 User Management")
    st.markdown("**Manage user accounts and permissions**")
    st.markdown("---")

    # CSS for form submit buttons - MUST be at top to load before forms render
    st.markdown("""
    <style>
        /* Form submit buttons - Atlas blue styling */
        button[data-testid="baseButton-primary"],
        button[data-testid="baseButton-primaryFormSubmit"],
        div[data-testid="stForm"] button[type="submit"],
        form button[type="submit"] {
            background-color: #025a9a !important;
            background: #025a9a !important;
            border: 2px solid #025a9a !important;
            color: white !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
        }

        button[data-testid="baseButton-primary"]:hover,
        button[data-testid="baseButton-primaryFormSubmit"]:hover,
        div[data-testid="stForm"] button[type="submit"]:hover,
        form button[type="submit"]:hover {
            background-color: #014275 !important;
            background: #014275 !important;
            border-color: #014275 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(2, 90, 154, 0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 View Users", "➕ Create User", "✏️ Edit Permissions", "📊 Publish Financial", "🏆 Publish W&C"])

    # ====================================================================
    # TAB 1: VIEW USERS
    # ====================================================================
    with tab1:
        st.markdown("### 📋 All Users")

        # Fetch all users
        with st.spinner("Loading users..."):
            users = fetch_all_users()

        if not users:
            st.warning("No users found in the database.")
            return

        # Prepare data for display
        user_data = []
        for user in users:
            # Get company name (handle None case for super admins)
            company_info = user.get('companies')
            if company_info:
                company_name = company_info.get('display_name', 'N/A')
            else:
                company_name = 'All Companies' if user.get('role') == 'super_admin' else 'Not Assigned'

            # Format status
            status = '✅ Active' if user.get('is_active', True) else '❌ Inactive'

            # Format role
            role = user.get('role', 'N/A')
            if role == 'super_admin':
                role_display = '👑 Super Admin'
            elif role == 'company_user':
                role_display = '👤 Company User'
            else:
                role_display = role

            user_data.append({
                'Name': user.get('full_name', 'N/A'),
                'Email': user.get('email', 'N/A'),
                'Role': role_display,
                'Company': company_name,
                'Can Upload': '✓' if user.get('can_upload_data', False) else '✗',
                'Status': status,
                'Created': user.get('created_at', 'N/A')[:10] if user.get('created_at') else 'N/A'
            })

        # Create DataFrame
        df = pd.DataFrame(user_data)

        # Display count
        st.info(f"📊 **Total Users:** {len(users)}")

        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Name': st.column_config.TextColumn('Name', width='medium'),
                'Email': st.column_config.TextColumn('Email', width='large'),
                'Role': st.column_config.TextColumn('Role', width='medium'),
                'Company': st.column_config.TextColumn('Company', width='medium'),
                'Can Upload': st.column_config.TextColumn('Upload', width='small'),
                'Status': st.column_config.TextColumn('Status', width='small'),
                'Created': st.column_config.TextColumn('Created', width='small')
            }
        )

    # ====================================================================
    # TAB 2: CREATE USER
    # ====================================================================
    with tab2:
        st.markdown("### ➕ Create New User")

        # Initialize form state
        initialize_create_form_state()

        # Display success message OUTSIDE form (persists across reruns)
        if st.session_state.create_form_success_msg:
            st.success(f"✅ {st.session_state.create_form_success_msg}")
            if st.session_state.create_form_success_info:
                st.info(st.session_state.create_form_success_info)
            st.markdown("---")

        # Create user form
        with st.form("create_user_form"):
            st.markdown("**User Information**")

            # Email and Full Name
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input(
                    "Email Address *",
                    value=st.session_state.create_form_email,
                    placeholder="user@example.com",
                    help="User's email address for login",
                    key="create_email_input"
                )
            with col2:
                full_name = st.text_input(
                    "Full Name *",
                    value=st.session_state.create_form_name,
                    placeholder="John Doe",
                    help="User's full name",
                    key="create_name_input"
                )

            st.markdown("---")
            st.markdown("**Role & Permissions**")

            # Role selection
            role = st.selectbox(
                "User Role *",
                options=["company_user", "super_admin"],
                index=0 if st.session_state.create_form_role == "company_user" else 1,
                format_func=lambda x: "👤 Company User" if x == "company_user" else "👑 Super Admin",
                help="Company User: Access to assigned company only. Super Admin: Access to all companies",
                key="create_role_selector"
            )

            # Company assignment (only show for company_user)
            company_id = None
            if role == "company_user":
                companies = fetch_all_companies()
                if companies:
                    company_options = {comp['id']: comp['display_name'] for comp in companies}
                    company_list = list(company_options.keys())

                    # Calculate index from stored value (safe fallback to 0)
                    if st.session_state.create_form_company_id in company_list:
                        default_index = company_list.index(st.session_state.create_form_company_id)
                    else:
                        default_index = 0

                    company_id = st.selectbox(
                        "Assigned Company *",
                        options=company_list,
                        index=default_index,
                        format_func=lambda x: company_options[x],
                        help="Select the company this user will have access to",
                        key="create_company_selector"
                    )
                else:
                    st.error("No companies found. Please add companies first.")

            # Upload permission
            can_upload = st.checkbox(
                "Can Upload Data",
                value=st.session_state.create_form_can_upload,
                help="Allow this user to upload financial data",
                key="create_upload_checkbox"
            )

            st.markdown("---")
            st.markdown("**User Creation Method**")

            # Method selector - choose between email invitation or manual password
            creation_method = st.radio(
                "How should this user be created?",
                options=["manual_password", "email_invitation"],
                index=0 if st.session_state.create_form_method == "manual_password" else 1,
                format_func=lambda x: "🔑 Manual Password (Recommended)" if x == "manual_password" else "📧 Email Invitation (Experimental)",
                help="Manual Password: Most reliable - you set initial password, user changes it via 'Forgot Password'. Email Invitation: May have delays.",
                key="create_method_radio"
            )

            # Only show password field for manual method
            temporary_password = None
            if creation_method == "manual_password":
                st.success("✅ **Recommended Method**: This is the most reliable way to create users.")

                # Add custom CSS for highlighted password field
                st.markdown("""
                    <style>
                        div[data-testid="stTextInput"] input[type="password"] {
                            border: 2px solid #025a9a !important;
                            background-color: #f0f8ff !important;
                            font-weight: 600 !important;
                        }
                    </style>
                """, unsafe_allow_html=True)

                temporary_password = st.text_input(
                    "Temporary Password *",
                    value=st.session_state.create_form_temp_password,
                    type="password",
                    placeholder="e.g., Welcome2024!",
                    help="User will use this to log in initially, then change it",
                    key="create_password_input"
                )
            else:
                st.warning("⚠️ Email invitations may have configuration issues. Manual password method is more reliable.")
                st.info("💡 User will receive an email invitation to set their own password. The link expires in 24 hours.")

            # Submit button - right-aligned with inline CSS for maximum specificity
            st.markdown("""
            <style>
                /* Create User button - ultra specific targeting */
                div[data-testid="column"]:has(button:contains("✅ Create User")) button,
                form button:has-text("✅ Create User"),
                button:has-text("Create User") {
                    background-color: #025a9a !important;
                    background: #025a9a !important;
                    border: 2px solid #025a9a !important;
                    color: white !important;
                }
            </style>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col2:
                submitted = st.form_submit_button("✅ Create User", use_container_width=True, type="primary")

            if submitted:
                # Update session state with current values
                st.session_state.create_form_email = email
                st.session_state.create_form_name = full_name
                st.session_state.create_form_role = role
                st.session_state.create_form_company_id = company_id
                st.session_state.create_form_can_upload = can_upload
                st.session_state.create_form_method = creation_method
                st.session_state.create_form_temp_password = temporary_password if temporary_password else ''

                # Validate inputs based on creation method
                if not email or not full_name:
                    st.error("❌ Please fill in all required fields (*).")
                elif role == "company_user" and not company_id:
                    st.error("❌ Please select a company for the company user.")
                elif creation_method == "manual_password" and not temporary_password:
                    st.error("❌ Please enter a temporary password.")
                elif creation_method == "manual_password" and len(temporary_password) < 6:
                    st.error("❌ Temporary password must be at least 6 characters long.")
                else:
                    # Create the user based on selected method
                    with st.spinner("Creating user..."):
                        if creation_method == "email_invitation":
                            result = create_new_user_with_invitation(
                                email=email,
                                full_name=full_name,
                                role=role,
                                company_id=company_id,
                                can_upload_data=can_upload
                            )
                        else:
                            result = create_new_user(
                                email=email,
                                full_name=full_name,
                                role=role,
                                company_id=company_id,
                                can_upload_data=can_upload,
                                temporary_password=temporary_password
                            )

                    # Handle success/error
                    if result["success"]:
                        # Store success message in session state
                        st.session_state.create_form_success_msg = result['message']

                        # Build info message based on method
                        if result.get("method") == "invitation":
                            # Email invitation success message
                            company_access = 'All Companies' if role == 'super_admin' else company_options.get(company_id, 'N/A')
                            st.session_state.create_form_success_info = f"""
📧 **Invitation Sent!**

{email} will receive an email with:
- Welcome message
- "Set Password" button
- Link valid for 24 hours

They'll be able to access: **{company_access}**
                            """
                        else:
                            # Manual password success message
                            company_access = 'All Companies' if role == 'super_admin' else company_options.get(company_id, 'N/A')
                            st.session_state.create_form_success_info = f"""
📧 **Next Steps:**

1. Share the following credentials with the user:
   - Email: `{email}`
   - Temporary Password: `{temporary_password}`

2. Ask them to log in and change their password

3. They will have access to: **{company_access}**
                            """

                        # CLEAR FORM FIELDS
                        clear_create_form_fields()

                        # RERUN to show cleared form + success message
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")

    # ====================================================================
    # TAB 3: EDIT PERMISSIONS
    # ====================================================================
    with tab3:
        st.markdown("### ✏️ Edit User Permissions")

        # Initialize edit form state
        initialize_edit_form_state()

        # Display success message OUTSIDE form with option to edit another user
        if st.session_state.edit_form_success_msg:
            st.success(f"✅ {st.session_state.edit_form_success_msg}")
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 Edit Another User", key="edit_another_user_btn", use_container_width=True):
                    clear_edit_form()
                    st.rerun()
            st.markdown("---")

        # Fetch all users for selection
        users = fetch_all_users()

        if not users:
            st.warning("No users found to edit.")
            return

        # Create user selection dropdown in a constrained column with filter styling
        st.markdown("""
        <style>
            /* Filter selectbox styling */
            div[data-testid="stSelectbox"] {
                max-width: 500px !important;
            }
        </style>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([2, 3])  # 40% width for filter, 60% empty

        with col1:
            user_options = {user['id']: f"{user['full_name']} ({user.get('email', 'N/A')})" for user in users}

            # Add visual container around the filter WITH the selectbox inside
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #f0f7ff 0%, #e6f2ff 100%);
                    border: 2px solid #025a9a;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 8px rgba(2, 90, 154, 0.15);
                ">
                    <div style="
                        color: #025a9a;
                        font-weight: 600;
                        font-size: 14px;
                        margin-bottom: 12px;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    ">
                        🔍 Filter Users
                    </div>
            """, unsafe_allow_html=True)

            selected_user_id = st.selectbox(
                "Select User to Edit",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x],
                help="Choose a user to edit their permissions",
                key="edit_user_selector",
                label_visibility="collapsed"
            )

            # Close the container div
            st.markdown("</div>", unsafe_allow_html=True)

        # Clear success message if user changed
        handle_edit_user_selection_change(selected_user_id)

        # Get selected user data
        selected_user = next((u for u in users if u['id'] == selected_user_id), None)

        if not selected_user:
            st.error("User not found.")
            return

        st.markdown("---")

        # Edit form
        with st.form("edit_user_form"):
            st.markdown("**User Information**")

            # Full Name (editable)
            full_name = st.text_input(
                "Full Name *",
                value=selected_user.get('full_name', ''),
                help="User's full name"
            )

            st.markdown("---")
            st.markdown("**Role & Permissions**")

            # Role selection
            current_role = selected_user.get('role', 'company_user')
            role = st.selectbox(
                "User Role *",
                options=["company_user", "super_admin"],
                index=0 if current_role == "company_user" else 1,
                format_func=lambda x: "👤 Company User" if x == "company_user" else "👑 Super Admin",
                help="Company User: Access to assigned company only. Super Admin: Access to all companies"
            )

            # Company assignment (only show for company_user)
            company_id = None
            if role == "company_user":
                companies = fetch_all_companies()
                if companies:
                    company_options = {comp['id']: comp['display_name'] for comp in companies}
                    current_company_id = selected_user.get('company_id')

                    # Find index of current company
                    company_list = list(company_options.keys())
                    default_index = company_list.index(current_company_id) if current_company_id in company_list else 0

                    company_id = st.selectbox(
                        "Assigned Company *",
                        options=company_list,
                        index=default_index,
                        format_func=lambda x: company_options[x],
                        help="Select the company this user will have access to"
                    )
                else:
                    st.error("No companies found.")

            # Upload permission
            can_upload = st.checkbox(
                "Can Upload Data",
                value=selected_user.get('can_upload_data', False),
                help="Allow this user to upload financial data"
            )

            # Active status
            is_active = st.checkbox(
                "Active User",
                value=selected_user.get('is_active', True),
                help="Inactive users cannot log in"
            )

            st.markdown("---")

            # Submit button - right-aligned with inline CSS for maximum specificity
            st.markdown("""
            <style>
                /* Save Changes button - ultra specific targeting */
                div[data-testid="column"]:has(button:contains("💾 Save Changes")) button,
                form button:has-text("💾 Save Changes"),
                button:has-text("Save Changes") {
                    background-color: #025a9a !important;
                    background: #025a9a !important;
                    border: 2px solid #025a9a !important;
                    color: white !important;
                }
            </style>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col2:
                update_submitted = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")

            # Handle form submission
            if update_submitted:
                # Validate inputs
                if not full_name:
                    st.error("❌ Full name is required.")
                elif role == "company_user" and not company_id:
                    st.error("❌ Please select a company for the company user.")
                else:
                    # Update the user
                    with st.spinner("Updating user..."):
                        result = update_user_permissions(
                            user_id=selected_user_id,
                            full_name=full_name,
                            role=role,
                            company_id=company_id,
                            can_upload_data=can_upload,
                            is_active=is_active
                        )

                    if result["success"]:
                        # Store success message in session state
                        st.session_state.edit_form_success_msg = result['message']
                        # Rerun to refresh and show message
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")

        # Delete user section (outside the form)
        st.markdown("---")
        st.markdown("### 🗑️ Danger Zone")

        # Prevent deleting yourself
        if selected_user_id == st.session_state.user.id:
            st.warning("⚠️ You cannot delete your own account.")
        else:
            # Initialize delete confirmation state
            if 'confirm_delete_user' not in st.session_state:
                st.session_state.confirm_delete_user = False

            # First delete button
            if not st.session_state.confirm_delete_user:
                if st.button("🗑️ Delete This User", key="delete_user_btn", type="secondary"):
                    st.session_state.confirm_delete_user = True
                    st.rerun()

            # Confirmation step
            if st.session_state.confirm_delete_user:
                st.error(f"⚠️ **Are you sure you want to delete {selected_user.get('full_name', 'this user')}?**")
                st.warning("This action cannot be undone!")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Delete Permanently", key="confirm_delete_yes", type="primary"):
                        with st.spinner("Deleting user..."):
                            result = delete_user(selected_user_id)

                        if result["success"]:
                            st.success(f"✅ {result['message']}")
                            st.info("🔄 Refresh the page to see changes.")
                            st.session_state.confirm_delete_user = False
                        else:
                            st.error(f"❌ {result['message']}")
                            st.session_state.confirm_delete_user = False

                with col2:
                    if st.button("❌ Cancel", key="confirm_delete_no"):
                        st.session_state.confirm_delete_user = False
                        st.rerun()

    # ====================================================================
    # TAB 4: PUBLISH DATA
    # ====================================================================
    with tab4:
        st.markdown("### 📊 Publish Financial Data")
        st.info("💡 Company users upload → status='submitted' (hidden). Super admin publishes → visible to all.")

        # Fetch pending submissions
        with st.spinner("Loading pending submissions..."):
            pending_data = get_pending_data_submissions()

        # Handle errors
        if 'error' in pending_data:
            st.error(f"Error loading pending submissions: {pending_data['error']}")
        elif not pending_data['has_pending']:
            st.success("✅ No pending submissions. All data is published.")
            st.info("💡 When company users upload new data, it will appear here for publication.")
        else:
            # Display pending submissions summary
            st.markdown("#### 📋 Pending Submissions by Period")

            # Period selector
            periods = sorted(list(pending_data['by_period'].keys()), reverse=True)
            selected_period = st.selectbox(
                "Select Period to Publish",
                options=periods,
                help="Choose which period's data to publish to the dashboard",
                index=0
            )

            # Show companies with pending data for this period
            period_data = pending_data['by_period'][selected_period]
            st.markdown(f"**Companies with pending data for {selected_period}:**")

            # Create DataFrame for display
            summary_rows = [
                {
                    'Company': item['company_name'],
                    'Income Statement': '✅ Submitted' if item['has_is'] else '❌ Missing',
                    'Balance Sheet': '✅ Submitted' if item['has_bs'] else '❌ Missing',
                    'Submitted By': item['submitted_by'],
                    'Submitted Date': item['submitted_date']
                }
                for item in period_data
            ]

            st.dataframe(
                pd.DataFrame(summary_rows),
                hide_index=True,
                use_container_width=True
            )

            # Count companies with complete vs. incomplete submissions
            complete_count = sum(1 for item in period_data if item['has_is'] and item['has_bs'])
            incomplete_count = len(period_data) - complete_count

            if incomplete_count > 0:
                st.warning(f"⚠️ {incomplete_count} compan{'y' if incomplete_count == 1 else 'ies'} with incomplete submissions (missing IS or BS)")

            st.markdown("---")

            # Bulk publish section
            st.markdown("#### 🚀 Publish All Data")
            st.warning(f"⚠️ This will publish ALL pending data for {selected_period} and make it visible to all users.")

            # Confirmation checkbox
            confirm = st.checkbox(f"I confirm I want to publish all data for {selected_period}")

            # Publish button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "🚀 Publish All Data",
                    type="primary",
                    disabled=not confirm,
                    use_container_width=True
                ):
                    with st.spinner("Publishing..."):
                        result = publish_all_data_for_period(selected_period, st.session_state.user.email)

                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        st.info(f"📊 Published {result['is_count']} IS and {result['bs_count']} BS records.")
                        st.balloons()
                        st.info("📧 Next: Send email notification to users (manual). Data visible within 30 min.")
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
                        if result['errors']:
                            for error in result['errors']:
                                st.warning(f"- {error}")

    # ====================================================================
    # TAB 5: PUBLISH W&C
    # ====================================================================
    with tab5:
        st.markdown("### 🏆 Publish Wins & Challenges Data")
        st.info("💡 W&C data is uploaded as drafts via the W&C Admin page. Publish here to make visible on dashboard.")

        # Fetch pending W&C submissions
        with st.spinner("Loading pending W&C submissions..."):
            wc_pending = get_pending_wc_submissions()

        # Handle errors
        if 'error' in wc_pending:
            st.error(f"Error loading W&C submissions: {wc_pending['error']}")
        elif not wc_pending['has_pending']:
            st.success("✅ No pending W&C drafts. All W&C data is published.")
            st.info("💡 Upload W&C data from the W&C Admin page. Drafts will appear here for publication.")
        else:
            # Display pending W&C summary
            st.markdown("#### 📋 Pending W&C Drafts by Period")

            # Period selector for W&C
            wc_periods = sorted(list(wc_pending['by_period'].keys()), reverse=True)
            selected_wc_period = st.selectbox(
                "Select Period to Publish W&C",
                options=wc_periods,
                help="Choose which period's W&C data to publish",
                key="wc_period_selector"
            )

            # Show companies with pending W&C for this period
            wc_period_data = wc_pending['by_period'][selected_wc_period]
            st.markdown(f"**Companies with pending W&C drafts for {selected_wc_period}:**")

            # Create DataFrame for W&C display
            wc_summary_rows = [
                {
                    'Company': item['company_name'],
                    'Wins': item['wins_count'],
                    'Challenges': item['challenges_count'],
                    'Action Items': item['action_items_count'],
                    'Total': item['wins_count'] + item['challenges_count'] + item['action_items_count']
                }
                for item in wc_period_data
            ]

            st.dataframe(
                pd.DataFrame(wc_summary_rows),
                hide_index=True,
                use_container_width=True
            )

            # Calculate totals
            total_wins = sum(item['wins_count'] for item in wc_period_data)
            total_challenges = sum(item['challenges_count'] for item in wc_period_data)
            total_action_items = sum(item['action_items_count'] for item in wc_period_data)
            total_wc = total_wins + total_challenges + total_action_items

            st.markdown(f"""
            <div style="background: #e6f7ff; padding: 0.75rem; border-radius: 6px; margin: 1rem 0;">
                <strong style="color: #025a9a;">Total Pending:</strong> {total_wc} items
                ({total_wins} wins, {total_challenges} challenges, {total_action_items} action items)
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            # Bulk publish W&C section
            st.markdown("#### 🚀 Publish All W&C Data")
            st.warning(f"⚠️ This will publish ALL pending W&C drafts for {selected_wc_period} and make them visible on the dashboard.")

            # Confirmation checkbox for W&C
            wc_confirm = st.checkbox(f"I confirm I want to publish all W&C data for {selected_wc_period}", key="wc_confirm")

            # Publish W&C button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "🏆 Publish All W&C Data",
                    type="primary",
                    disabled=not wc_confirm,
                    use_container_width=True,
                    key="publish_wc_btn"
                ):
                    with st.spinner("Publishing W&C data..."):
                        wc_result = publish_all_wc_for_period(selected_wc_period, st.session_state.user.email)

                    if wc_result['success']:
                        st.success(f"✅ {wc_result['message']}")
                        st.info(f"🏆 Published {wc_result['wins_count']} wins, {wc_result['challenges_count']} challenges, {wc_result['action_items_count']} action items.")
                        st.balloons()
                        # Clear all caches so updated data is shown on dashboard
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {wc_result['message']}")
                        if wc_result['errors']:
                            for error in wc_result['errors']:
                                st.warning(f"- {error}")


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="User Management - BPC Dashboard",
        page_icon="👥",
        layout="wide"
    )
    create_user_management_page()
