"""
Script to create BPC Upload Template Excel file
Creates an Excel file with Balance Sheet and Income Statement sheets
Each sheet has: Line Item, Description, and Date (12/31/25) columns
"""

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# Import descriptions
from description_mappings import BALANCE_SHEET_DESCRIPTIONS, INCOME_STATEMENT_DESCRIPTIONS


def create_excel_template():
    """Create the BPC Upload Template Excel file"""

    # Create workbook
    wb = Workbook()

    # Remove default sheet
    wb.remove(wb.active)

    # Create Instructions sheet first
    create_instructions_sheet(wb)

    # Create Income Statement sheet
    create_income_statement_sheet(wb)

    # Create Balance Sheet sheet
    create_balance_sheet_sheet(wb)

    # Save the file
    output_path = 'bpc_upload_template/BPC1_Upload_Template.xlsx'
    wb.save(output_path)
    print(f"✅ Template created successfully: {output_path}")


def create_instructions_sheet(wb):
    """Create Instructions sheet with user guidance"""

    ws = wb.create_sheet("Instructions", 0)

    atlas_blue = "025A9A"
    light_blue = "E8F4FD"
    dark_gray = "333333"

    title_font = Font(name="Montserrat", size=22, bold=True, color="FFFFFF")
    header_font = Font(name="Montserrat", size=16, bold=True, color=atlas_blue)
    number_font = Font(name="Montserrat", size=14, bold=True, color=dark_gray)
    body_font = Font(name="Montserrat", size=14, bold=True, color=dark_gray)
    note_bullet = Font(name="Montserrat", size=13, bold=True, color=dark_gray)
    note_font = Font(name="Montserrat", size=13, bold=True, italic=True, color="444444")

    title_fill = PatternFill(start_color=atlas_blue, end_color=atlas_blue, fill_type="solid")
    alt_fill = PatternFill(start_color=light_blue, end_color=light_blue, fill_type="solid")

    wrap_top = Alignment(wrap_text=True, vertical="top")

    # Column widths - A narrow for numbers, B-H wide for text
    ws.column_dimensions['A'].width = 5
    for col_letter in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
        ws.column_dimensions[col_letter].width = 18

    # Row 1: Title
    ws.merge_cells('A1:H1')
    cell = ws['A1']
    cell.value = "BPC1 Upload Template \u2014 Instructions"
    cell.font = title_font
    cell.fill = title_fill
    cell.alignment = Alignment(vertical="center", horizontal="center")
    ws.row_dimensions[1].height = 55

    # Row 2: Spacer
    ws.row_dimensions[2].height = 10

    # Row 3: Step 1 header
    ws.merge_cells('A3:H3')
    ws['A3'].value = "Step 1: Fill Out the Template"
    ws['A3'].font = header_font
    ws.row_dimensions[3].height = 40

    # Step 1 instructions
    step1_items = [
        ("1.", 'Open the "Income Statement" and "Balance Sheet" tabs in this workbook.'),
        ("2.", "Enter the dollar amounts for each line item in the Amount column (Column C). Each line item matches what you see on the dashboard's Income Statement and Balance Sheet pages."),
        ("3.", 'Enter raw numbers only \u2014 no dollar signs ($), commas, or other formatting. For example, enter 150000 not $150,000.'),
        ("4.", "Enter negative values with a minus sign (e.g., -5000 for accumulated depreciation)."),
        ("5.", "Enter 0 for any line item that does not apply to your company. Do not leave cells blank."),
        ("6.", "Do NOT modify the line item names in Column A or the descriptions in Column B. The system uses these names to match your data."),
        ("7.", "Do NOT fill in any rows labeled as totals (e.g., Total Revenue, Total Assets). These are calculated automatically by the dashboard."),
    ]

    row = 4
    for num, text in step1_items:
        ws[f'A{row}'].value = num
        ws[f'A{row}'].font = number_font
        ws[f'A{row}'].alignment = Alignment(vertical="top", horizontal="right")
        ws.merge_cells(f'B{row}:H{row}')
        ws[f'B{row}'].value = text
        ws[f'B{row}'].font = body_font
        ws[f'B{row}'].alignment = wrap_top
        ws.row_dimensions[row].height = 42
        row += 1

    # Spacer
    ws.row_dimensions[row].height = 10
    row += 1

    # Step 2 header
    ws.merge_cells(f'A{row}:H{row}')
    ws[f'A{row}'].value = "Step 2: Upload Your Data"
    ws[f'A{row}'].font = header_font
    ws.row_dimensions[row].height = 40
    row += 1

    step2_items = [
        ("1.", "Log in to the BPC1 Dashboard and navigate to the Upload page."),
        ("2.", "At the top of the page, select your company name from the dropdown."),
        ("3.", "Select the correct reporting period \u2014 choose whether this is a Full Year or Mid Year report, and select the correct year."),
        ("4.", "On the sidebar of the upload page, you will find an option to upload this Excel file. Click it and select this file."),
        ("5.", "The system will parse your data and show you a preview. Review it carefully before submitting."),
        ("6.", 'Click the Submit button to upload your data. Once submitted, your data will be in "Submitted" status until an admin publishes it to the dashboard.'),
    ]

    for num, text in step2_items:
        ws[f'A{row}'].value = num
        ws[f'A{row}'].font = number_font
        ws[f'A{row}'].alignment = Alignment(vertical="top", horizontal="right")
        ws.merge_cells(f'B{row}:H{row}')
        ws[f'B{row}'].value = text
        ws[f'B{row}'].font = body_font
        ws[f'B{row}'].alignment = wrap_top
        ws.row_dimensions[row].height = 42
        row += 1

    # Spacer
    ws.row_dimensions[row].height = 10
    row += 1

    # Important Notes header
    ws.merge_cells(f'A{row}:H{row}')
    ws[f'A{row}'].value = "Important Notes"
    ws[f'A{row}'].font = header_font
    ws.row_dimensions[row].height = 40
    row += 1

    notes = [
        ("\u2022", "Make sure you select the correct company and period before uploading \u2014 the system will save data under whichever company and period you have selected."),
        ("\u2022", "This Instructions sheet is ignored during upload. Only the Income Statement and Balance Sheet sheets are processed."),
        ("\u2022", "If you see warnings after upload about unmatched line items, check that the line item names in your file have not been modified."),
    ]

    for bullet, text in notes:
        ws[f'A{row}'].value = bullet
        ws[f'A{row}'].font = note_bullet
        ws[f'A{row}'].alignment = Alignment(vertical="top", horizontal="center")
        ws.merge_cells(f'B{row}:H{row}')
        ws[f'B{row}'].value = text
        ws[f'B{row}'].font = note_font
        ws[f'B{row}'].alignment = wrap_top
        ws.row_dimensions[row].height = 45
        row += 1

    # Alternating row shading for readability
    step1_rows = list(range(4, 11))
    step2_rows = list(range(13, 19))
    note_rows = list(range(21, 24))
    all_content_rows = step1_rows + step2_rows + note_rows

    for i, r in enumerate(all_content_rows):
        if i % 2 == 0:
            for col_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                ws[f'{col_letter}{r}'].fill = alt_fill

    # Protect sheet so users don't accidentally edit instructions
    ws.protection.sheet = True
    ws.protection.enable()
    ws.sheet_properties.tabColor = atlas_blue


def create_income_statement_sheet(wb):
    """Create Income Statement sheet with all line items"""

    ws = wb.create_sheet("Income Statement", 1)

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

    ws = wb.create_sheet("Balance Sheet", 2)

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
    ws['A1'].font = Font(name="Montserrat", size=16, bold=True, color="FFFFFF")
    ws['A1'].fill = PatternFill(start_color="025a9a", end_color="025a9a", fill_type="solid")
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.merge_cells('A1:C1')
    ws.row_dimensions[1].height = 35

    # Row 2: Column headers
    headers = ['Line Item', 'Description', 'Amount']
    header_fill = PatternFill(start_color="0e9cd5", end_color="0e9cd5", fill_type="solid")
    header_font = Font(name="Montserrat", bold=True, color="FFFFFF", size=13)

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

    ws.row_dimensions[2].height = 28


def add_data_rows(ws, line_items, description_dict):
    """Add data rows with line items, descriptions, and date column"""

    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Data validation: only allow decimal numbers in column C
    number_validation = DataValidation(
        type="decimal",
        operator="between",
        formula1=-999999999999,
        formula2=999999999999,
        allow_blank=True
    )
    number_validation.error = "Please enter a number only. No dollar signs, commas, or text."
    number_validation.errorTitle = "Invalid Entry"
    number_validation.prompt = "Enter the dollar amount as a number (e.g., 150000 or -5000)"
    number_validation.promptTitle = "Amount"
    number_validation.showErrorMessage = True
    number_validation.showInputMessage = True
    ws.add_data_validation(number_validation)

    row_num = 3  # Start after header rows

    for field_key, field_label, is_header in line_items:
        if is_header:
            # Category header row
            cell_a = ws.cell(row=row_num, column=1)
            cell_a.value = field_key
            cell_a.font = Font(name="Montserrat", bold=True, size=12, color="FFFFFF")
            cell_a.fill = PatternFill(start_color="4a5568", end_color="4a5568", fill_type="solid")
            cell_a.alignment = Alignment(horizontal='left', vertical='center')

            # Merge across all columns for category headers
            ws.merge_cells(f'A{row_num}:C{row_num}')
            ws.row_dimensions[row_num].height = 25

        elif field_key == '' and field_label == '':
            # Blank row for spacing
            ws.row_dimensions[row_num].height = 8

        else:
            # Regular data row
            # Column A: Line Item
            cell_a = ws.cell(row=row_num, column=1)
            cell_a.value = field_label
            cell_a.font = Font(name="Montserrat", size=12, bold=True, color="333333")
            cell_a.alignment = Alignment(horizontal='left', vertical='center')
            cell_a.border = thin_border

            # Column B: Description
            description = description_dict.get(field_key, '')
            cell_b = ws.cell(row=row_num, column=2)
            cell_b.value = description
            cell_b.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            cell_b.font = Font(name="Montserrat", size=11, color="4a5568")
            cell_b.border = thin_border

            # Column C: Amount (editable by user, numbers only)
            cell_c = ws.cell(row=row_num, column=3)
            cell_c.value = None
            cell_c.font = Font(name="Montserrat", size=12)
            cell_c.alignment = Alignment(horizontal='right', vertical='center')
            cell_c.border = thin_border
            cell_c.number_format = '#,##0.0000'
            number_validation.add(cell_c)

            ws.row_dimensions[row_num].height = 32

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
