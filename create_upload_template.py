"""
Script to create BPC Upload Template Excel file
Creates an Excel file with Balance Sheet and Income Statement sheets
Each sheet has: Line Item, Description, and Date (12/31/25) columns
"""

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, Protection
from openpyxl.utils import get_column_letter

# Import descriptions
from description_mappings import BALANCE_SHEET_DESCRIPTIONS, INCOME_STATEMENT_DESCRIPTIONS


def create_excel_template():
    """Create the BPC Upload Template Excel file"""

    # Create workbook
    wb = Workbook()

    # Remove default sheet
    wb.remove(wb.active)

    # Create Income Statement sheet first (as it's the primary input)
    create_income_statement_sheet(wb)

    # Create Balance Sheet sheet
    create_balance_sheet_sheet(wb)

    # Save the file
    output_path = 'bpc_upload_template/BPC2_Upload_Template.xlsx'
    wb.save(output_path)
    print(f"✅ Template created successfully: {output_path}")


def create_income_statement_sheet(wb):
    """Create Income Statement sheet with all line items"""

    ws = wb.create_sheet("Income Statement", 0)

    # Define all Income Statement line items in order
    is_line_items = [
        # Revenue
        ('REVENUE', '', True),  # Header row
        ('intra_state_hhg', 'Intra State HHG', False),
        ('local_hhg', 'Local HHG', False),
        ('inter_state_hhg', 'Inter State HHG', False),
        ('office_industrial', 'Office & Industrial', False),
        ('warehouse', 'Warehouse (Non-commercial)', False),
        ('warehouse_handling', 'Warehouse Handling (Non-commercial)', False),
        ('international', 'International', False),
        ('packing_unpacking', 'Packing & Unpacking', False),
        ('booking_royalties', 'Booking & Royalties', False),
        ('special_products', 'Special Products', False),
        ('records_storage', 'Records Storage', False),
        ('military_dpm_contracts', 'Military DPM Contracts', False),
        ('distribution', 'Distribution', False),
        ('hotel_deliveries', 'Hotel Deliveries', False),
        ('other_revenue', 'Other Revenue', False),

        # Direct Expenses
        ('', '', False),  # Blank row
        ('DIRECT EXPENSES (COST OF REVENUE)', '', True),  # Header row
        ('direct_wages', 'Direct Wages', False),
        ('vehicle_operating_expenses', 'Vehicle Operating Expense', False),
        ('packing_warehouse_supplies', 'Packing/Warehouse Supplies', False),
        ('oo_exp_intra_state', 'OO Exp Intra State', False),
        ('oo_inter_state', 'OO Inter State', False),
        ('oo_oi', 'OO O&I', False),
        ('oo_packing', 'OO Packing', False),
        ('oo_other', 'OO Other', False),
        ('claims', 'Claims', False),
        ('other_trans_exp', 'Other Trans Exp', False),
        ('depreciation', 'Depreciation', False),
        ('lease_expense_rev_equip', 'Lease Expense Rev Equip', False),
        ('rent', 'Rent', False),
        ('other_direct_expenses', 'Other Direct Expenses', False),

        # Operating Expenses
        ('', '', False),  # Blank row
        ('OPERATING EXPENSES', '', True),  # Header row
        ('advertising_marketing', 'Advertising/Marketing', False),
        ('bad_debts', 'Bad Debts', False),
        ('sales_commissions', 'Sales Commissions', False),
        ('contributions', 'Contributions', False),
        ('computer_support', 'Computer Support', False),
        ('dues_sub', 'Dues & Subscriptions', False),
        ('pr_taxes_benefits', 'PR Taxes & Benefits', False),
        ('equipment_leases_office_equip', 'Equipment Leases Office Equip', False),
        ('workmans_comp_insurance', "Workman's Comp Insurance", False),
        ('insurance', 'Insurance', False),
        ('legal_accounting', 'Legal & Accounting', False),
        ('office_expense', 'Office Expense', False),
        ('other_admin', 'Other Admin', False),
        ('pension_profit_sharing_401k', 'Pension/Profit Sharing/401k', False),
        ('prof_fees', 'Professional Fees', False),
        ('repairs_maint', 'Repairs & Maintenance', False),
        ('salaries_admin', 'Salaries Admin', False),
        ('taxes_licenses', 'Taxes & Licenses', False),
        ('tel_fax_utilities_internet', 'Tel/Fax/Utilities/Internet', False),
        ('travel_ent', 'Travel & Entertainment', False),
        ('vehicle_expense_admin', 'Vehicle Expense Admin', False),

        # Other Income/Expenses
        ('', '', False),  # Blank row
        ('OTHER INCOME/EXPENSES', '', True),  # Header row
        ('other_income', 'Other Income', False),
        ('ceo_comp', 'CEO Comp', False),
        ('other_expense', 'Other Expense', False),
        ('interest_expense', 'Interest Expense', False),
    ]

    # Add header row
    add_header_row(ws, "Income Statement Data Entry")

    # Add data rows
    add_data_rows(ws, is_line_items, INCOME_STATEMENT_DESCRIPTIONS)

    # Format the sheet
    format_sheet(ws)


def create_balance_sheet_sheet(wb):
    """Create Balance Sheet sheet with all line items"""

    ws = wb.create_sheet("Balance Sheet", 1)

    # Define all Balance Sheet line items in order
    bs_line_items = [
        # Current Assets
        ('CURRENT ASSETS', '', True),  # Header row
        ('cash_and_cash_equivalents', 'Cash & Cash Equivalents', False),
        ('trade_accounts_receivable', 'Trade Accounts Receivable', False),
        ('receivables', 'Receivables', False),
        ('other_receivables', 'Other Receivables', False),
        ('prepaid_expenses', 'Prepaid Expenses', False),
        ('related_company_receivables', 'Related Company Receivables', False),
        ('owner_receivables', 'Owner Receivables', False),
        ('other_current_assets', 'Other Current Assets', False),

        # Fixed Assets
        ('', '', False),  # Blank row
        ('FIXED ASSETS', '', True),  # Header row
        ('gross_fixed_assets', 'Gross Fixed Assets', False),
        ('accumulated_depreciation', 'Accumulated Depreciation', False),

        # Other Assets
        ('', '', False),  # Blank row
        ('OTHER ASSETS', '', True),  # Header row
        ('inter_company_receivable', 'Inter Company Receivable', False),
        ('other_assets', 'Other Assets', False),

        # Current Liabilities
        ('', '', False),  # Blank row
        ('CURRENT LIABILITIES', '', True),  # Header row
        ('notes_payable_bank', 'Notes Payable/Bank', False),
        ('notes_payable_owners', 'Notes Payable/Owners', False),
        ('trade_accounts_payable', 'Trade Accounts Payable', False),
        ('accrued_expenses', 'Accrued Expenses', False),
        ('current_portion_ltd', 'Current Portion LTD', False),
        ('inter_company_payable', 'Inter Company Payable', False),
        ('other_current_liabilities', 'Other Current Liabilities', False),

        # Long-term Liabilities
        ('', '', False),  # Blank row
        ('LONG-TERM LIABILITIES', '', True),  # Header row
        ('eid_loan', 'EID Loan', False),
        ('long_term_debt', 'Long-term Debt', False),
        ('notes_payable_owners_lt', 'Notes Payable Owners (LT)', False),
        ('inter_company_debt', 'Inter Company Debt', False),
        ('other_lt_liabilities', 'Other LT Liabilities', False),

        # Equity
        ('', '', False),  # Blank row
        ('EQUITY', '', True),  # Header row
        ('owners_equity', "Owner's Equity", False),
    ]

    # Add header row
    add_header_row(ws, "Balance Sheet Data Entry")

    # Add data rows
    add_data_rows(ws, bs_line_items, BALANCE_SHEET_DESCRIPTIONS)

    # Format the sheet
    format_sheet(ws)


def add_header_row(ws, sheet_title):
    """Add the header row with column names"""

    # Row 1: Sheet title
    ws['A1'] = sheet_title
    ws['A1'].font = Font(size=14, bold=True, color="FFFFFF")
    ws['A1'].fill = PatternFill(start_color="025a9a", end_color="025a9a", fill_type="solid")
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.merge_cells('A1:C1')
    ws.row_dimensions[1].height = 25

    # Row 2: Column headers
    headers = ['Line Item', 'Description', '12/31/25']
    header_fill = PatternFill(start_color="0e9cd5", end_color="0e9cd5", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    ws.row_dimensions[2].height = 20


def add_data_rows(ws, line_items, description_dict):
    """Add data rows with line items, descriptions, and date column"""

    row_num = 3  # Start after header rows

    for field_key, field_label, is_header in line_items:
        if is_header:
            # Category header row
            cell_a = ws.cell(row=row_num, column=1)
            cell_a.value = field_key
            cell_a.font = Font(bold=True, size=11, color="FFFFFF")
            cell_a.fill = PatternFill(start_color="4a5568", end_color="4a5568", fill_type="solid")
            cell_a.alignment = Alignment(horizontal='left', vertical='center')

            # Merge across all columns for category headers
            ws.merge_cells(f'A{row_num}:C{row_num}')
            ws.row_dimensions[row_num].height = 18

        elif field_key == '' and field_label == '':
            # Blank row for spacing
            ws.row_dimensions[row_num].height = 8

        else:
            # Regular data row
            # Column A: Line Item
            cell_a = ws.cell(row=row_num, column=1)
            cell_a.value = field_label
            cell_a.alignment = Alignment(horizontal='left', vertical='center')
            cell_a.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            # Column B: Description
            description = description_dict.get(field_key, '')
            cell_b = ws.cell(row=row_num, column=2)
            cell_b.value = description
            cell_b.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            cell_b.font = Font(italic=True, size=9, color="4a5568")
            cell_b.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            # Column C: Date (editable by user)
            cell_c = ws.cell(row=row_num, column=3)
            cell_c.value = None  # Leave blank for user to enter amount
            cell_c.alignment = Alignment(horizontal='right', vertical='center')
            cell_c.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            cell_c.number_format = '$#,##0.00'  # Currency format

            ws.row_dimensions[row_num].height = 30  # Taller rows for wrapped descriptions

        row_num += 1


def format_sheet(ws):
    """Apply formatting to the entire sheet"""

    # Set column widths
    ws.column_dimensions['A'].width = 35  # Line Item
    ws.column_dimensions['B'].width = 65  # Description (wider for full text)
    ws.column_dimensions['C'].width = 15  # Date/Amount

    # Freeze top two rows (title and headers) AND first two columns (Line Item and Description)
    # This allows users to scroll horizontally while keeping the line item labels visible
    ws.freeze_panes = 'C3'

    # Protect columns A and B from accidental editing while keeping column C editable
    # By default, all cells are locked. We unlock column C (Amount) so users can edit it.
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=3, max_col=3):
        for cell in row:
            cell.protection = Protection(locked=False)

    # Enable worksheet protection
    # This prevents editing of locked cells (columns A and B) but allows editing of unlocked cells (column C)
    # Note: No password is set, so users can unprotect if needed, but it prevents accidental edits
    ws.protection.sheet = True
    ws.protection.enable()


if __name__ == "__main__":
    create_excel_template()
