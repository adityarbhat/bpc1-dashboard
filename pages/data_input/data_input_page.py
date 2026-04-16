"""
Financial Data Input Page
Allows users to input Balance Sheet and Income Statement data directly via interactive tables
"""

import textwrap
import base64
import streamlit as st
import pandas as pd
from datetime import datetime
from shared.airtable_connection import get_airtable_connection, get_companies_cached
from shared.page_components import create_page_header
from shared.css_styles import apply_all_styles
from shared.auth_utils import require_auth, is_super_admin, get_user_company_name, can_upload_data
from shared.year_config import CURRENT_YEAR, EARLIEST_YEAR

# Import field mappings from transformation scripts
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from data_transformation_bs import BALANCE_SHEET_MAPPING
from data_transformation_is import INCOME_STATEMENT_MAPPING
from description_mappings import BALANCE_SHEET_DESCRIPTIONS, INCOME_STATEMENT_DESCRIPTIONS
from pages.data_input.excel_parser import enforce_negative


def _wrap_description(text, width=55):
    """Wrap long descriptions with newlines so they display on multiple lines in the data editor."""
    if not text or len(text) <= width:
        return text
    return '\n'.join(textwrap.wrap(text, width=width))


def create_data_input_page():
    """Main data input page with tabs for Income Statement and Balance Sheet"""
    # Require authentication - CRITICAL ADMIN PAGE
    require_auth()

    # Check if user has upload permission
    if not can_upload_data() and not is_super_admin():
        st.error("❌ Access Denied")
        st.warning("You do not have permission to upload financial data.")
        st.info("Please contact your administrator to request upload access.")
        st.stop()

    # 1. Minimal CSS for selectbox styling (matching working pages)
    st.markdown("""
    <style>
    div[data-testid="stSelectbox"] > div > div {
        border-color: #e2e8f0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 2. Page header FIRST (creates banner at top)
    create_page_header(
        banner_text="BPC 1 Financial Data",
        show_period_selector=False
    )

    # 3. Create sidebar AFTER header
    create_data_input_sidebar()

    # 4. Apply global styles LAST
    apply_all_styles()

    # Upload guide download
    upload_guide_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "BPC_Upload_Instructions.docx")
    if os.path.exists(upload_guide_path):
        with open(upload_guide_path, "rb") as f:
            guide_b64 = base64.b64encode(f.read()).decode()
        download_href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{guide_b64}" download="BPC_Upload_Instructions.docx" style="color: #b8860b; font-weight: 600; text-decoration: underline;">here</a>'
        st.markdown(f"""
        <div style="background: #fff8e1; padding: 0.75rem 1rem; border-radius: 8px; border-left: 4px solid #f9a825; margin-top: -1rem; margin-bottom: 1.5rem;">
            <p style="margin: 0; font-size: 1.05rem; color: #5d4e00; line-height: 1.6;">
                📄 <strong>First time uploading?</strong> Please download and read the upload guide {download_href} before your first upload to ensure everything goes smoothly.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Instructions
    st.markdown("""
    <div style="background: #f7fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #025a9a; margin-top: -1rem; margin-bottom: 1.5rem;">
        <p style="margin: 0; font-size: 1rem; color: #4a5568; line-height: 1.6;">
            <strong>Instructions:</strong> Use the tables below to input financial data directly or upload a spreadsheet.
            Select a company and period, fill in the data, review calculations, and submit to Airtable.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Company and period selection
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        # Check user role and filter companies accordingly
        if is_super_admin():
            # Super admin: show all companies
            companies = get_companies_cached()
            company_names = [c['name'] for c in companies]

            if 'selected_company_for_input' not in st.session_state:
                st.session_state.selected_company_for_input = company_names[0] if company_names else None

            selected_company = st.selectbox(
                "Select Company",
                options=company_names,
                index=company_names.index(st.session_state.selected_company_for_input) if st.session_state.selected_company_for_input in company_names else 0,
                key="company_selector_input"
            )
            st.session_state.selected_company_for_input = selected_company
        else:
            # Company user: only show their assigned company
            user_company = get_user_company_name()

            if not user_company:
                st.error("❌ No company assigned to your account. Please contact an administrator.")
                st.stop()

            # Display company as text input (disabled) to match layout
            st.text_input(
                "Your Company",
                value=user_company,
                disabled=True,
                key="company_display_readonly"
            )
            selected_company = user_company
            st.session_state.selected_company_for_input = selected_company

    with col2:
        # Period selection
        years = [str(y) for y in range(EARLIEST_YEAR, CURRENT_YEAR + 1)]
        period_types = ['Annual', 'Mid Year']

        if 'selected_year_input' not in st.session_state:
            st.session_state.selected_year_input = str(CURRENT_YEAR)
        if 'selected_period_type_input' not in st.session_state:
            st.session_state.selected_period_type_input = 'Annual'

        selected_year = st.selectbox(
            "Select Year",
            options=years,
            index=years.index(st.session_state.selected_year_input),
            key="year_selector_input"
        )
        st.session_state.selected_year_input = selected_year

    with col3:
        selected_period_type = st.selectbox(
            "Period Type",
            options=period_types,
            index=period_types.index(st.session_state.selected_period_type_input),
            key="period_type_selector_input"
        )
        st.session_state.selected_period_type_input = selected_period_type

    # Convert period type to period name
    if selected_period_type == 'Annual':
        period_name = f"{selected_year} Annual"
    elif selected_period_type == 'Mid Year':
        period_name = f"{selected_year} H1"
    else:
        # Fallback to Annual (shouldn't happen with current options)
        period_name = f"{selected_year} Annual"

    # Display selected period info
    st.markdown(f"""
    <div style="background: #e6f7ff; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; text-align: center;">
        <strong style="color: #025a9a;">Inputting data for: {selected_company} - {period_name}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Tabs for Income Statement and Balance Sheet
    tab1, tab2 = st.tabs(["📊 Income Statement", "📋 Balance Sheet"])

    with tab1:
        create_income_statement_input(selected_company, period_name, selected_year)

    with tab2:
        create_balance_sheet_input(selected_company, period_name, selected_year)


def create_data_input_sidebar():
    """Create sidebar navigation for data input page"""
    with st.sidebar:
        st.markdown("### 📝 Data Input")

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Navigation back to dashboard at the top
        if st.button("🏠 Back to Dashboard", key="back_to_dashboard", use_container_width=True):
            st.session_state.current_page = "overview"
            st.session_state.nav_tab = "group"  # Ensure we're on group tab for overview
            st.rerun()

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 1rem 0;"></div>', unsafe_allow_html=True)

        # Download Upload Guide Section
        st.markdown("#### 📥 Download Upload Guide")
        upload_guide_sidebar_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "BPC_Upload_Instructions.docx")
        if os.path.exists(upload_guide_sidebar_path):
            with open(upload_guide_sidebar_path, "rb") as gf:
                st.download_button(
                    label="📥 Download Upload Guide",
                    data=gf,
                    file_name="BPC_Upload_Instructions.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    help="Step-by-step guide for uploading financial data",
                    use_container_width=True
                )

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 1rem 0;"></div>', unsafe_allow_html=True)

        # Download Template Section
        st.markdown("#### 📥 Download Template")
        xlsx_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        new_template_path = 'bpc_upload_template/BPC1_Upload_Template_NEW_With_Subtotals.xlsx'
        old_template_path = 'bpc_upload_template/BPC1_Upload_Template_OLD.xlsx'

        if os.path.exists(new_template_path):
            with open(new_template_path, 'rb') as template_file:
                st.download_button(
                    label="📥 Download NEW Template (with live subtotals)",
                    data=template_file,
                    file_name="BPC1_Upload_Template_NEW_With_Subtotals.xlsx",
                    mime=xlsx_mime,
                    help="New template — subtotals calculate automatically as you type",
                    use_container_width=True
                )
        else:
            st.error("⚠️ New template not found. Run create_upload_template.py to generate it.")

        if os.path.exists(old_template_path):
            with open(old_template_path, 'rb') as template_file:
                st.download_button(
                    label="📥 Download OLD Template (no subtotals)",
                    data=template_file,
                    file_name="BPC1_Upload_Template_OLD.xlsx",
                    mime=xlsx_mime,
                    help="Old template — still uploads successfully, kept for backward compatibility",
                    use_container_width=True
                )

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 1rem 0;"></div>', unsafe_allow_html=True)

        # Upload Section - Consolidated Uploader
        st.markdown("#### 📤 Upload Data")
        st.markdown("Upload the BPC Excel template with both Income Statement and Balance Sheet data")

        uploaded_file = st.file_uploader(
            "Upload Excel Template",
            type=['xlsx'],
            key='consolidated_uploader_sidebar',
            help="Upload the BPC template with both IS and BS sheets",
            label_visibility="collapsed"
        )

        if uploaded_file:
            # Validate file size (10MB limit — template is ~15KB, generous buffer for large values)
            max_file_size_mb = 10
            if uploaded_file.size > max_file_size_mb * 1024 * 1024:
                st.error(f"File too large ({uploaded_file.size / (1024*1024):.1f} MB). Maximum allowed: {max_file_size_mb} MB.")
                uploaded_file = None

        if uploaded_file:
            # Only process the file once — the file_uploader widget retains the file
            # between reruns, so without this guard every rerun (including data_editor
            # cell edits) would re-parse the file and overwrite manual edits.
            file_fingerprint = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get('last_processed_upload_file') != file_fingerprint:
                from pages.data_input.excel_parser import parse_consolidated_excel
                with st.spinner("Parsing both Income Statement and Balance Sheet..."):
                    results, warnings = parse_consolidated_excel(uploaded_file)

                # Update Income Statement data
                if results['is_matched'] > 0:
                    if 'is_input_data' not in st.session_state:
                        st.session_state.is_input_data = {}
                    st.session_state.is_input_data.update(results['is_data'])
                    st.session_state.is_submitted = False  # Re-enable submit button
                    # Increment version so data_editor widgets reinitialize with fresh data
                    st.session_state.is_upload_version = st.session_state.get('is_upload_version', 0) + 1
                    st.success(f"✅ Income Statement: {results['is_matched']} items loaded")

                # Update Balance Sheet data
                if results['bs_matched'] > 0:
                    if 'bs_input_data' not in st.session_state:
                        st.session_state.bs_input_data = {}
                    st.session_state.bs_input_data.update(results['bs_data'])
                    st.session_state.bs_submitted = False  # Re-enable submit button
                    # Increment version so data_editor widgets reinitialize with fresh data
                    st.session_state.bs_upload_version = st.session_state.get('bs_upload_version', 0) + 1
                    st.success(f"✅ Balance Sheet: {results['bs_matched']} items loaded")

                    # Check balance
                    if results['is_balanced']:
                        st.success("✅ Balance Sheet is balanced")
                    else:
                        st.warning(f"⚠️ Balance Sheet unbalanced by: ${abs(results['balance_difference']):,.2f}")

                # Show warnings (limit to first 3)
                if warnings:
                    for warning in warnings[:3]:
                        st.warning(warning)

                # Show unmatched items summary
                total_unmatched = len(results['is_unmatched']) + len(results['bs_unmatched'])
                if total_unmatched > 0:
                    st.info(f"⚠️ {total_unmatched} unmatched items (IS: {len(results['is_unmatched'])}, BS: {len(results['bs_unmatched'])})")

                # Show success message if both sheets loaded
                if results['is_matched'] > 0 and results['bs_matched'] > 0:
                    st.success("🎉 Both sheets loaded successfully! Data is now populated in the forms below.")

                # Mark this file as processed so reruns don't re-parse it
                st.session_state.last_processed_upload_file = file_fingerprint


def create_income_statement_input(company_name, period_name, year):
    """Create Income Statement data input table"""

    st.markdown("### Revenue")

    # Define Income Statement structure with categories
    revenue_fields = [
        ('intra_state_hhg', 'Intra State HHG'),
        ('local_hhg', 'Local HHG'),
        ('inter_state_hhg', 'Inter State HHG'),
        ('office_industrial', 'Office & Industrial'),
        ('warehouse', 'Warehouse (Non-commercial)'),
        ('warehouse_handling', 'Warehouse Handling (Non-commercial)'),
        ('international', 'International'),
        ('packing_unpacking', 'Packing & Unpacking'),
        ('booking_royalties', 'Booking & Royalties'),
        ('special_products', 'Special Products'),
        ('records_storage', 'Records Storage'),
        ('military_dpm_contracts', 'Military DPM Contracts'),
        ('distribution', 'Distribution'),
        ('hotel_deliveries', 'Hotel Deliveries'),
        ('other_revenue', 'Other Revenue'),
    ]

    direct_expense_fields = [
        ('direct_wages', 'Direct Wages'),
        ('vehicle_operating_expenses', 'Vehicle Operating Expense'),
        ('packing_warehouse_supplies', 'Packing/Warehouse Supplies'),
        ('oo_exp_intra_state', 'OO Exp Intra State'),
        ('oo_inter_state', 'OO Inter State'),
        ('oo_oi', 'OO O&I'),
        ('oo_packing', 'OO Packing'),
        ('oo_other', 'OO Other'),
        ('claims', 'Claims'),
        ('other_trans_exp', 'Other Trans Exp'),
        ('depreciation', 'Depreciation'),
        ('lease_expense_rev_equip', 'Lease Expense Rev Equip'),
        ('rent', 'Rent'),
        ('other_direct_expenses', 'Other Direct Expenses'),
    ]

    operating_expense_fields = [
        ('advertising_marketing', 'Advertising/Marketing'),
        ('bad_debts', 'Bad Debts'),
        ('sales_commissions', 'Sales Commissions'),
        ('contributions', 'Contributions'),
        ('computer_support', 'Computer Support'),
        ('dues_sub', 'Dues & Subscriptions'),
        ('pr_taxes_benefits', 'PR Taxes & Benefits'),
        ('equipment_leases_office_equip', 'Equipment Leases Office Equip'),
        ('workmans_comp_insurance', "Workman's Comp Insurance"),
        ('insurance', 'Insurance'),
        ('legal_accounting', 'Legal & Accounting'),
        ('office_expense', 'Office Expense'),
        ('other_admin', 'Other Admin'),
        ('pension_profit_sharing_401k', 'Pension/Profit Sharing/401k'),
        ('prof_fees', 'Professional Fees'),
        ('repairs_maint', 'Repairs & Maintenance'),
        ('salaries_admin', 'Salaries Admin'),
        ('taxes_licenses', 'Taxes & Licenses'),
        ('tel_fax_utilities_internet', 'Tel/Fax/Utilities/Internet'),
        ('travel_ent', 'Travel & Entertainment'),
        ('vehicle_expense_admin', 'Vehicle Expense Admin'),
    ]

    other_fields = [
        ('other_income', 'Other Income'),
        ('ceo_comp', 'CEO Comp'),
        ('other_expense', 'Other Expense'),
        ('interest_expense', 'Interest Expense'),
    ]

    # Fetch existing data from Airtable if available
    airtable = get_airtable_connection()
    existing_data = airtable.get_income_statement_data_by_period(company_name, period_name, is_admin=True)
    existing_values = existing_data[0] if existing_data else {}

    # Store input data in session state
    if 'is_input_data' not in st.session_state:
        st.session_state.is_input_data = {}

    # Create input section for each category
    def create_input_section(section_title, fields, category_key, allow_negative=False):
        st.markdown(f"### {section_title}")

        # Create DataFrame for this section
        data = []
        for field_key, field_label in fields:
            current_value = st.session_state.is_input_data.get(field_key, existing_values.get(field_key, 0.0))
            description = _wrap_description(INCOME_STATEMENT_DESCRIPTIONS.get(field_key, ''))
            data.append({
                'Line Item': field_label,
                'Description': description,
                'Field Key': field_key,
                f'{year} Amount': float(current_value) if current_value else 0.0
            })

        df = pd.DataFrame(data)

        # Build NumberColumn config - only enforce min_value=0 for non-negative sections
        number_col_kwargs = {
            'format': "$%.2f",
            'width': 'medium'
        }
        if not allow_negative:
            number_col_kwargs['min_value'] = 0.0

        # Use data_editor for editable table
        edited_df = st.data_editor(
            df,
            hide_index=True,
            column_config={
                'Line Item': st.column_config.TextColumn('Line Item', disabled=True, width='medium'),
                'Description': st.column_config.TextColumn('Description', disabled=True, width='large'),
                'Field Key': None,  # Hide this column
                f'{year} Amount': st.column_config.NumberColumn(
                    f'{year} Amount ($)',
                    **number_col_kwargs
                )
            },
            use_container_width=True,
            key=f"is_{category_key}_{year}_v{st.session_state.get('is_upload_version', 0)}"
        )

        # Update session state with edited values
        for idx, row in edited_df.iterrows():
            field_key = row['Field Key']
            new_val = row[f'{year} Amount']
            # Ensure deduction fields (ceo_comp, other_expense, interest_expense) are negative
            new_val = enforce_negative(field_key, new_val)
            old_val = st.session_state.is_input_data.get(field_key, 0.0)
            if new_val != old_val:
                st.session_state.is_submitted = False  # Re-enable submit on edit
            st.session_state.is_input_data[field_key] = new_val

        return edited_df

    # Create sections
    revenue_df = create_input_section("Revenue", revenue_fields, "revenue")

    # Calculate Total Revenue
    total_revenue = sum([st.session_state.is_input_data.get(field[0], 0.0) for field in revenue_fields])
    st.markdown(f"""
    <div style="background: #d4edda; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Total Revenue: ${total_revenue:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.is_input_data['total_revenue'] = total_revenue

    st.markdown("---")

    direct_df = create_input_section("Direct Expenses (Cost of Revenue)", direct_expense_fields, "direct_expenses")

    # Calculate Total Cost of Revenue
    total_direct = sum([st.session_state.is_input_data.get(field[0], 0.0) for field in direct_expense_fields])
    st.markdown(f"""
    <div style="background: #fff3cd; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Total Cost of Revenue: ${total_direct:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.is_input_data['total_cost_of_revenue'] = total_direct

    # Calculate Gross Profit
    gross_profit = total_revenue - total_direct
    st.markdown(f"""
    <div style="background: #cfe2ff; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Gross Profit: ${gross_profit:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.is_input_data['gross_profit'] = gross_profit

    st.markdown("---")

    operating_df = create_input_section("Operating Expenses", operating_expense_fields, "operating_expenses")

    # Calculate Total Operating Expenses
    total_operating = sum([st.session_state.is_input_data.get(field[0], 0.0) for field in operating_expense_fields])
    st.markdown(f"""
    <div style="background: #fff3cd; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Total Operating Expenses: ${total_operating:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.is_input_data['total_operating_expenses'] = total_operating

    # Calculate Operating Profit
    operating_profit = gross_profit - total_operating
    st.markdown(f"""
    <div style="background: #cfe2ff; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Operating Profit: ${operating_profit:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.is_input_data['operating_profit'] = operating_profit

    st.markdown("---")

    other_df = create_input_section("Non-Operating Income/Expenses", other_fields, "other", allow_negative=True)

    # Calculate total non-operating (values are entered with correct sign, e.g. expenses as negative)
    total_nonoperating = (
        st.session_state.is_input_data.get('other_income', 0.0) +
        st.session_state.is_input_data.get('ceo_comp', 0.0) +
        st.session_state.is_input_data.get('other_expense', 0.0) +
        st.session_state.is_input_data.get('interest_expense', 0.0)
    )
    st.session_state.is_input_data['total_nonoperating_income'] = total_nonoperating
    st.markdown(f"""
    <div style="background: #cfe2ff; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Total Non-Operating Income: ${total_nonoperating:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Calculate Profit Before Tax
    profit_before_tax = operating_profit + total_nonoperating
    st.markdown(f"""
    <div style="background: #d1ecf1; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Profit Before Tax (with PPP): ${profit_before_tax:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.is_input_data['profit_before_tax_with_ppp'] = profit_before_tax

    # Labor Analysis - Administrative Employees (headcount, not dollars)
    st.markdown("---")
    st.markdown("### Labor Analysis")
    labor_fields = [
        ('administrative_employees', 'Administrative Employees (Count)'),
        ('number_of_branches', 'Number of Branches'),
    ]
    labor_data = []
    for field_key, field_label in labor_fields:
        current_value = st.session_state.is_input_data.get(field_key, existing_values.get(field_key, 0.0))
        description = _wrap_description(INCOME_STATEMENT_DESCRIPTIONS.get(field_key, ''))
        labor_data.append({
            'Line Item': field_label,
            'Description': description,
            'Field Key': field_key,
            f'{year} Value': float(current_value) if current_value else 0.0
        })
    labor_df = pd.DataFrame(labor_data)
    edited_labor_df = st.data_editor(
        labor_df,
        hide_index=True,
        column_config={
            'Line Item': st.column_config.TextColumn('Line Item', disabled=True, width='medium'),
            'Description': st.column_config.TextColumn('Description', disabled=True, width='large'),
            'Field Key': None,
            f'{year} Value': st.column_config.NumberColumn(
                f'{year} Value',
                min_value=0,
                step=1,
                format="%d",
                width='medium'
            )
        },
        use_container_width=True,
        key=f"is_labor_{year}_v{st.session_state.get('is_upload_version', 0)}"
    )
    for idx, row in edited_labor_df.iterrows():
        field_key = row['Field Key']
        new_val = row[f'{year} Value']
        old_val = st.session_state.is_input_data.get(field_key, 0.0)
        if new_val != old_val:
            st.session_state.is_submitted = False
        st.session_state.is_input_data[field_key] = new_val

    # Submit button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    is_submitted = st.session_state.get('is_submitted', False)
    with col2:
        if is_submitted:
            st.button("✅ Income Statement Submitted", use_container_width=True, type="primary", disabled=True)
            st.success("Data has been submitted. Edit values or upload a new file to re-enable.")
        else:
            if st.button("✅ Submit Income Statement to Airtable", use_container_width=True, type="primary"):
                submit_income_statement_data(company_name, period_name, year)


def create_balance_sheet_input(company_name, period_name, year):
    """Create Balance Sheet data input table"""

    st.markdown("### Assets")

    # Define Balance Sheet structure
    current_assets_fields = [
        ('cash_and_cash_equivalents', 'Cash and Cash Equivalents'),
        ('trade_accounts_receivable', 'Trade Accounts Receivable'),
        ('receivables', 'Receivables'),
        ('other_receivables', 'Other Receivables'),
        ('prepaid_expenses', 'Prepaid Expenses'),
        ('related_company_receivables', 'Related Company Receivables'),
        ('owner_receivables', 'Owner Receivables'),
        ('other_current_assets', 'Other Current Assets'),
    ]

    fixed_assets_fields = [
        ('gross_fixed_assets', 'Gross Fixed Assets'),
        ('accumulated_depreciation', 'Accumulated Depreciation'),
    ]

    other_assets_fields = [
        ('inter_company_receivable', 'Inter Company Receivable'),
        ('other_assets', 'Other Assets'),
    ]

    current_liabilities_fields = [
        ('notes_payable_bank', 'Notes Payable/Bank'),
        ('notes_payable_owners', 'Notes Payable/Owners'),
        ('trade_accounts_payable', 'Trade Accounts Payable'),
        ('accrued_expenses', 'Accrued Expenses'),
        ('current_portion_ltd', 'Current Portion LTD'),
        ('inter_company_payable', 'Inter Company Payable'),
        ('other_current_liabilities', 'Other Current Liabilities'),
    ]

    lt_liabilities_fields = [
        ('eid_loan', 'EID Loan'),
        ('long_term_debt', 'Long-term Debt'),
        ('notes_payable_owners_lt', 'Notes Payable Owners (LT)'),
        ('inter_company_debt', 'Inter Company Debt'),
        ('other_lt_liabilities', 'Other LT Liabilities'),
    ]

    equity_fields = [
        ('owners_equity', "Owner's Equity"),
    ]

    # Fetch existing data
    airtable = get_airtable_connection()
    existing_data = airtable.get_balance_sheet_data_by_period(company_name, period_name, is_admin=True)
    existing_values = existing_data[0] if existing_data else {}

    # Store input data in session state
    if 'bs_input_data' not in st.session_state:
        st.session_state.bs_input_data = {}

    # Create input section helper
    def create_bs_input_section(section_title, fields, category_key):
        st.markdown(f"### {section_title}")

        data = []
        for field_key, field_label in fields:
            current_value = st.session_state.bs_input_data.get(field_key, existing_values.get(field_key, 0.0))
            description = _wrap_description(BALANCE_SHEET_DESCRIPTIONS.get(field_key, ''))
            data.append({
                'Line Item': field_label,
                'Description': description,
                'Field Key': field_key,
                f'{year} Amount': float(current_value) if current_value else 0.0
            })

        df = pd.DataFrame(data)

        edited_df = st.data_editor(
            df,
            hide_index=True,
            column_config={
                'Line Item': st.column_config.TextColumn('Line Item', disabled=True, width='medium'),
                'Description': st.column_config.TextColumn('Description', disabled=True, width='large'),
                'Field Key': None,
                f'{year} Amount': st.column_config.NumberColumn(
                    f'{year} Amount ($)',
                    format="$%.2f",
                    width='medium'
                )
            },
            use_container_width=True,
            key=f"bs_{category_key}_{year}_v{st.session_state.get('bs_upload_version', 0)}"
        )

        for idx, row in edited_df.iterrows():
            field_key = row['Field Key']
            new_val = row[f'{year} Amount']
            old_val = st.session_state.bs_input_data.get(field_key, 0.0)
            if new_val != old_val:
                st.session_state.bs_submitted = False  # Re-enable submit on edit
            st.session_state.bs_input_data[field_key] = new_val

        return edited_df

    # Current Assets
    current_assets_df = create_bs_input_section("Current Assets", current_assets_fields, "current_assets")
    total_current_assets = sum([st.session_state.bs_input_data.get(field[0], 0.0) for field in current_assets_fields])
    st.markdown(f"""
    <div style="background: #d4edda; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Total Current Assets: ${total_current_assets:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.bs_input_data['total_current_assets'] = total_current_assets

    st.markdown("---")

    # Fixed Assets
    fixed_assets_df = create_bs_input_section("Fixed Assets", fixed_assets_fields, "fixed_assets")
    gross_fixed = st.session_state.bs_input_data.get('gross_fixed_assets', 0.0)
    accum_depreciation = st.session_state.bs_input_data.get('accumulated_depreciation', 0.0)
    net_fixed_assets = gross_fixed + accum_depreciation  # depreciation entered as negative
    st.markdown(f"""
    <div style="background: #cfe2ff; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Net Fixed Assets: ${net_fixed_assets:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.bs_input_data['net_fixed_assets'] = net_fixed_assets

    st.markdown("---")

    # Other Assets
    other_assets_df = create_bs_input_section("Other Assets", other_assets_fields, "other_assets")

    # Total Assets
    total_assets = total_current_assets + net_fixed_assets + sum([st.session_state.bs_input_data.get(field[0], 0.0) for field in other_assets_fields])
    st.markdown(f"""
    <div style="background: #d1ecf1; padding: 1rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong style="font-size: 1.1rem;">TOTAL ASSETS: ${total_assets:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.bs_input_data['total_assets'] = total_assets

    st.markdown("---")
    st.markdown("### Liabilities")

    # Current Liabilities
    current_liab_df = create_bs_input_section("Current Liabilities", current_liabilities_fields, "current_liabilities")
    total_current_liabilities = sum([st.session_state.bs_input_data.get(field[0], 0.0) for field in current_liabilities_fields])
    st.markdown(f"""
    <div style="background: #fff3cd; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Total Current Liabilities: ${total_current_liabilities:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.bs_input_data['total_current_liabilities'] = total_current_liabilities

    st.markdown("---")

    # Long-term Liabilities
    lt_liab_df = create_bs_input_section("Long-term Liabilities", lt_liabilities_fields, "lt_liabilities")
    total_lt_liabilities = sum([st.session_state.bs_input_data.get(field[0], 0.0) for field in lt_liabilities_fields])
    st.markdown(f"""
    <div style="background: #fff3cd; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Total Long-term Liabilities: ${total_lt_liabilities:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.bs_input_data['total_long_term_liabilities'] = total_lt_liabilities

    # Total Liabilities
    total_liabilities = total_current_liabilities + total_lt_liabilities
    st.markdown(f"""
    <div style="background: #e2e3e5; padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong>Total Liabilities: ${total_liabilities:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.bs_input_data['total_liabilities'] = total_liabilities

    st.markdown("---")
    st.markdown("### Equity")

    # Equity
    equity_df = create_bs_input_section("Owner's Equity", equity_fields, "equity")
    owners_equity = st.session_state.bs_input_data.get('owners_equity', 0.0)

    # Total Liabilities + Equity
    total_liab_equity = total_liabilities + owners_equity
    st.markdown(f"""
    <div style="background: #d1ecf1; padding: 1rem; border-radius: 6px; margin: 0.5rem 0;">
        <strong style="font-size: 1.1rem;">TOTAL LIABILITIES & EQUITY: ${total_liab_equity:,.2f}</strong>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.bs_input_data['total_liabilities_equity'] = total_liab_equity

    # Balance Sheet Equation Check
    is_balanced = abs(total_assets - total_liab_equity) < 0.01
    if is_balanced:
        st.success(f"✅ Balance Sheet is balanced! Assets = Liabilities + Equity (${total_assets:,.2f})")
    else:
        difference = total_assets - total_liab_equity
        st.error(f"⚠️ Balance Sheet is NOT balanced! Difference: ${difference:,.2f}")
        st.warning(f"Assets: ${total_assets:,.2f} | Liabilities + Equity: ${total_liab_equity:,.2f}")

    # Submit button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    bs_submitted = st.session_state.get('bs_submitted', False)
    with col2:
        if bs_submitted:
            st.button("✅ Balance Sheet Submitted", use_container_width=True, type="primary", disabled=True)
            st.success("Data has been submitted. Edit values or upload a new file to re-enable.")
        else:
            if st.button("✅ Submit Balance Sheet to Airtable", use_container_width=True, type="primary", disabled=not is_balanced):
                submit_balance_sheet_data(company_name, period_name, year)


def submit_income_statement_data(company_name, period_name, year):
    """Submit Income Statement data to Airtable"""
    from pages.data_input.data_uploader import upload_income_statement_to_airtable

    # Disable submit button immediately to prevent double-click duplicates
    st.session_state.is_submitted = True

    try:
        # Get user email from session state
        user_email = st.session_state.user.email if st.session_state.get('user') else 'unknown@user.com'

        with st.spinner("Uploading Income Statement data to Airtable..."):
            success, message = upload_income_statement_to_airtable(
                company_name,
                period_name,
                year,
                st.session_state.is_input_data,
                user_email
            )

            if success:
                st.success(f"✅ {message}")
                st.balloons()
                # Clear form data so user can upload another company
                st.session_state.is_input_data = {}
                st.cache_data.clear()
            else:
                st.error(f"❌ {message}")
                st.session_state.is_submitted = False  # Re-enable on failure
    except Exception as e:
        st.error(f"Error uploading data: {str(e)}")
        st.session_state.is_submitted = False  # Re-enable on error


def submit_balance_sheet_data(company_name, period_name, year):
    """Submit Balance Sheet data to Airtable"""
    from pages.data_input.data_uploader import upload_balance_sheet_to_airtable

    # Disable submit button immediately to prevent double-click duplicates
    st.session_state.bs_submitted = True

    try:
        # Get user email from session state
        user_email = st.session_state.user.email if st.session_state.get('user') else 'unknown@user.com'

        with st.spinner("Uploading Balance Sheet data to Airtable..."):
            success, message = upload_balance_sheet_to_airtable(
                company_name,
                period_name,
                year,
                st.session_state.bs_input_data,
                user_email
            )

            if success:
                st.success(f"✅ {message}")
                st.balloons()
                # Clear form data so user can upload another company
                st.session_state.bs_input_data = {}
                st.cache_data.clear()
            else:
                st.error(f"❌ {message}")
                st.session_state.bs_submitted = False  # Re-enable on failure
    except Exception as e:
        st.error(f"Error uploading data: {str(e)}")
        st.session_state.bs_submitted = False  # Re-enable on error
