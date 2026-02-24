# Feature Deep Dive: Excel Upload & Data Input System

## Overview

This deep dive covers the comprehensive Excel upload system that allows users to submit financial data through structured Excel templates. You'll learn about template parsing, validation, and the data pipeline from Excel to Airtable.

**What You'll Learn:**
- Multi-sheet Excel template parsing
- Field mapping and validation patterns
- Financial data upload orchestration
- Wins & Challenges upload workflow
- Permission-based UI patterns

**Difficulty:** Intermediate to Advanced
**Time:** 60-75 minutes

---

## The Upload Challenge

### Requirements

Build an upload system that:
1. Parses structured Excel templates (IS, BS sheets)
2. Maps Excel labels to Airtable field names
3. Validates data before upload
4. Handles both financial data and Wins & Challenges
5. Supports draft/publish workflow
6. Respects user permissions

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Upload Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Excel File (.xlsx)                                            │
│         │                                                        │
│         ↓                                                        │
│   ┌─────────────────┐                                           │
│   │  excel_parser   │  ← Label-to-field mapping                 │
│   │  or             │  ← Sheet identification                    │
│   │  wc_excel_parser│  ← Data extraction                        │
│   └────────┬────────┘                                           │
│            ↓                                                     │
│   ┌─────────────────┐                                           │
│   │ data_validator  │  ← Required field checks                  │
│   │                 │  ← Type validation                         │
│   │                 │  ← Range validation                        │
│   └────────┬────────┘                                           │
│            ↓                                                     │
│   ┌─────────────────┐                                           │
│   │ data_uploader   │  ← Period record management               │
│   │ or              │  ← Airtable API calls                      │
│   │ wc_uploader     │  ← Status: 'submitted' or 'draft'         │
│   └────────┬────────┘                                           │
│            ↓                                                     │
│   Airtable Tables                                                │
│   ├── balance_sheet_data                                        │
│   ├── income_statement_data                                     │
│   ├── wins                                                       │
│   ├── challenges                                                 │
│   └── action_items                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Files

```
pages/data_input/
├── data_input_page.py    # Main UI (710 lines)
├── excel_parser.py       # Financial data parsing (580 lines)
├── wc_excel_parser.py    # W&C parsing (156 lines)
├── data_uploader.py      # Financial upload (210 lines)
├── wc_uploader.py        # W&C upload (219 lines)
├── data_validator.py     # Validation logic (138 lines)
├── wins_challenges_admin.py   # W&C admin UI (338 lines)
└── wins_challenges_manager.py # W&C CRUD (445 lines)

bpc_upload_template/
├── BPC2_Upload_Template.xlsx      # Financial data template
├── BPC2_WC_Upload_Template.xlsx   # Wins & Challenges template
└── README.md
```

---

## Excel Template Structure

### Financial Data Template

```
BPC2_Upload_Template.xlsx
├── Sheet: "Income Statement"
│   ├── Row 1: Headers (Company, Period, etc.)
│   ├── Row 2+: Label | Value format
│   │   ├── "Intra State HHG" | 150000
│   │   ├── "Direct Wages" | 75000
│   │   └── ... (72+ line items)
│
└── Sheet: "Balance Sheet"
    ├── Row 1: Headers
    └── Row 2+: Label | Value format
        ├── "Cash & Cash Equivalents" | 50000
        ├── "Total Current Assets" | 250000
        └── ... (30+ line items)
```

### Wins & Challenges Template

```
BPC2_WC_Upload_Template.xlsx
├── Sheet: "Wins"
│   ├── Column A: Win text
│   └── Column B: Display order (1, 2, 3...)
│
├── Sheet: "Challenges"
│   ├── Column A: Challenge text
│   └── Column B: Display order
│
└── Sheet: "Action Items"
    ├── Column A: Action item text
    └── Column B: Display order
```

---

## Financial Data Parsing

### Label-to-Field Mapping

```python
# File: pages/data_input/excel_parser.py

# Income Statement mappings (72+ fields)
IS_LABEL_MAPPING = {
    # Revenue categories
    'Intra State HHG': 'intra_state_hhg',
    'Interstate HHG Linehaul': 'interstate_hhg_linehaul',
    'Interstate SIT': 'interstate_sit',
    'Local & Intra State': 'local_and_intra_state',
    'Long Distance HHG': 'long_distance_hhg',
    'International': 'international',
    'Third Party/Brokerage': 'third_party_brokerage',
    'Office Moving': 'office_moving',
    'Storage': 'storage',
    'Other': 'other_revenue',

    # Direct costs
    'Direct Wages': 'direct_wages',
    'Direct Benefits': 'direct_benefits',
    'Direct Payroll Taxes': 'direct_payroll_taxes',
    'Linehaul': 'linehaul',
    'SIT': 'sit',
    'Origin/Destination Services': 'origin_destination_services',
    'Claims': 'claims',
    'Warehouse Operations': 'warehouse_operations',
    'Fuel': 'fuel',
    'Other Direct Expense': 'other_direct_expense',

    # Administrative costs
    'Salaries Admin': 'salaries_admin',
    'Benefits Admin': 'benefits_admin',
    'Payroll Taxes Admin': 'payroll_taxes_admin',
    'Sales Salaries': 'sales_salaries',
    'Sales Benefits': 'sales_benefits',
    'Sales Payroll Taxes': 'sales_payroll_taxes',

    # ... 50+ more mappings
}

# Balance Sheet mappings (30+ fields)
BS_LABEL_MAPPING = {
    # Current Assets
    'Cash & Cash Equivalents': 'cash_and_cash_equivalents',
    'Accounts Receivable': 'accounts_receivable',
    'Notes Receivable Owner': 'notes_receivable_owner',
    'Prepaid Expenses': 'prepaid_expenses',
    'Other Current Assets': 'other_current_assets',
    'Total Current Assets': 'total_current_assets',

    # Fixed Assets
    'Land': 'land',
    'Buildings': 'buildings',
    'Equipment': 'equipment',
    'Leasehold Improvements': 'leasehold_improvements',
    'Accumulated Depreciation': 'accumulated_depreciation',
    'Net Fixed Assets': 'net_fixed_assets',

    # Liabilities
    'Accounts Payable': 'accounts_payable',
    'Accrued Liabilities': 'accrued_liabilities',
    'Notes Payable Bank': 'notes_payable_bank',
    'Notes Payable Owners': 'notes_payable_owners',
    'Current Portion LTD': 'current_portion_ltd',
    'Total Current Liabilities': 'total_current_liabilities',

    # Long-term
    'Long Term Debt': 'long_term_debt',
    'Notes Payable Owners LT': 'notes_payable_owners_lt',
    'Inter Company Debt': 'inter_company_debt',

    # Equity
    'Paid In Capital': 'paid_in_capital',
    'Retained Earnings': 'retained_earnings',
    'Current Year Net Income': 'current_year_net_income',
    'Total Equity': 'total_equity',

    # ... additional fields
}
```

### Parsing Implementation

```python
def parse_income_statement_data(df: pd.DataFrame) -> tuple[bool, dict, list]:
    """
    Parse Income Statement sheet from Excel.

    Args:
        df: pandas DataFrame from Excel sheet

    Returns:
        (success: bool, data: dict, errors: list)
    """
    data = {}
    errors = []

    # Find the label column (usually A)
    label_col = df.columns[0]
    value_col = df.columns[1] if len(df.columns) > 1 else None

    if not value_col:
        return False, {}, ["Could not find value column"]

    # Iterate through rows
    for idx, row in df.iterrows():
        label = str(row[label_col]).strip()
        value = row[value_col]

        # Skip empty rows
        if not label or label == 'nan':
            continue

        # Find matching field
        field_name = IS_LABEL_MAPPING.get(label)

        if field_name:
            # Parse numeric value
            parsed_value = parse_numeric(value)

            if parsed_value is not None:
                data[field_name] = parsed_value
            else:
                errors.append(f"Invalid value for '{label}': {value}")

    # Validate required fields
    required_fields = ['total_revenue', 'direct_wages', 'net_profit']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    success = len(errors) == 0 and len(data) > 0
    return success, data, errors


def parse_numeric(value) -> float | None:
    """
    Parse numeric value from Excel cell.

    Handles:
    - Regular numbers: 1000
    - Currency: $1,000
    - Percentages: 35% or 0.35
    - Negative: (1000) or -1000
    """
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    # String parsing
    value_str = str(value).strip()

    # Remove currency symbols and commas
    value_str = value_str.replace('$', '').replace(',', '')

    # Handle parentheses for negative
    if value_str.startswith('(') and value_str.endswith(')'):
        value_str = '-' + value_str[1:-1]

    # Handle percentage
    if value_str.endswith('%'):
        value_str = value_str[:-1]
        try:
            return float(value_str) / 100  # Convert to decimal
        except ValueError:
            return None

    try:
        return float(value_str)
    except ValueError:
        return None
```

---

## Wins & Challenges Parsing

```python
# File: pages/data_input/wc_excel_parser.py

def parse_wc_excel(uploaded_file) -> tuple[dict, list]:
    """
    Parse Wins & Challenges Excel template.

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        (results: dict, warnings: list)
    """
    import pandas as pd

    results = {
        'wins': [],
        'challenges': [],
        'action_items': [],
        'wins_count': 0,
        'challenges_count': 0,
        'action_items_count': 0
    }
    warnings = []

    # Parse each sheet
    for sheet_name, item_type in [
        ('Wins', 'wins'),
        ('Challenges', 'challenges'),
        ('Action Items', 'action_items')
    ]:
        try:
            items, sheet_warnings = _parse_wc_sheet(
                uploaded_file, sheet_name, item_type
            )
            results[item_type] = items
            results[f'{item_type}_count'] = len(items)
            warnings.extend(sheet_warnings)

        except Exception as e:
            warnings.append(f"Could not parse {sheet_name} sheet: {e}")

    return results, warnings


def _parse_wc_sheet(
    uploaded_file,
    sheet_name: str,
    item_type: str
) -> tuple[list, list]:
    """
    Parse single W&C sheet.

    Expected format:
    - Column A: Text content
    - Column B: Display order (optional, defaults to row number)
    """
    import pandas as pd

    df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)

    items = []
    warnings = []

    for idx, row in df.iterrows():
        # Skip header row if present
        if idx == 0 and str(row[0]).lower() in ['text', 'content', item_type]:
            continue

        text = str(row[0]).strip() if pd.notna(row[0]) else ''

        if not text or text == 'nan':
            continue

        # Get display order (column B) or default to index
        if len(row) > 1 and pd.notna(row[1]):
            try:
                display_order = int(row[1])
            except (ValueError, TypeError):
                display_order = idx + 1
                warnings.append(
                    f"{sheet_name} row {idx + 1}: Invalid display order, using {display_order}"
                )
        else:
            display_order = idx + 1

        items.append({
            'text': text,
            'display_order': display_order
        })

    return items, warnings
```

---

## Data Validation

```python
# File: pages/data_input/data_validator.py

def validate_financial_data(data: dict, data_type: str) -> tuple[bool, list]:
    """
    Validate financial data before upload.

    Args:
        data: Dictionary of field values
        data_type: 'income_statement' or 'balance_sheet'

    Returns:
        (is_valid: bool, errors: list)
    """
    errors = []

    if data_type == 'income_statement':
        errors.extend(validate_income_statement(data))
    elif data_type == 'balance_sheet':
        errors.extend(validate_balance_sheet(data))

    return len(errors) == 0, errors


def validate_income_statement(data: dict) -> list:
    """Validate income statement data."""
    errors = []

    # Required fields
    required = ['total_revenue', 'gross_margin', 'net_profit']
    for field in required:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    # Logical validations
    if 'total_revenue' in data and data['total_revenue'] <= 0:
        errors.append("Total revenue must be positive")

    # Margin validations (stored as decimals)
    if 'gross_margin' in data:
        margin = data['gross_margin']
        if margin < -1 or margin > 1:
            errors.append("Gross margin must be between -100% and 100%")

    # Totals validation
    if all(k in data for k in ['gross_margin', 'total_revenue', 'gross_profit']):
        expected_gross = data['total_revenue'] * data['gross_margin']
        actual_gross = data['gross_profit']
        if abs(expected_gross - actual_gross) > 1:  # $1 tolerance
            errors.append(
                f"Gross profit ({actual_gross}) doesn't match "
                f"revenue × margin ({expected_gross})"
            )

    return errors


def validate_balance_sheet(data: dict) -> list:
    """Validate balance sheet data."""
    errors = []

    # Required fields
    required = ['total_current_assets', 'total_current_liabilities', 'total_equity']
    for field in required:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    # Balance equation: Assets = Liabilities + Equity
    if all(k in data for k in ['total_assets', 'total_liabilities', 'total_equity']):
        assets = data['total_assets']
        liab_equity = data['total_liabilities'] + data['total_equity']

        if abs(assets - liab_equity) > 1:  # $1 tolerance
            errors.append(
                f"Balance sheet doesn't balance: "
                f"Assets ({assets}) != Liabilities + Equity ({liab_equity})"
            )

    return errors
```

---

## Upload Orchestration

### Financial Data Upload

```python
# File: pages/data_input/data_uploader.py

def upload_balance_sheet_to_airtable(
    company_name: str,
    period_name: str,
    data: dict
) -> tuple[bool, str]:
    """
    Upload balance sheet data to Airtable.

    Args:
        company_name: Company name
        period_name: Period (e.g., "2024 Annual")
        data: Validated balance sheet data

    Returns:
        (success: bool, message: str)
    """
    from shared.airtable_connection import AirtableConnection
    from shared.auth_utils import get_user_company_id, log_audit_event

    try:
        airtable = AirtableConnection()

        # Validate period format
        if not validate_period_format(period_name):
            return False, f"Invalid period format: {period_name}"

        # Get or create period record
        period_id = airtable.get_or_create_period(company_name, period_name)

        if not period_id:
            return False, "Failed to get/create period record"

        # Prepare record
        record = {
            'company': company_name,
            'period': [period_id],  # Linked record
            'publication_status': 'submitted',  # Not yet published
            **data
        }

        # Check for existing record
        existing = airtable.get_balance_sheet_by_period(company_name, period_name)

        if existing:
            # Update existing
            record_id = existing[0]['id']
            airtable.update_balance_sheet(record_id, record)
            action = 'updated'
        else:
            # Create new
            airtable.create_balance_sheet(record)
            action = 'created'

        # Log audit event
        log_audit_event(
            action='upload_data',
            resource='balance_sheet',
            company_id=get_user_company_id(),
            metadata={
                'company': company_name,
                'period': period_name,
                'action': action
            }
        )

        return True, f"Balance sheet {action} successfully"

    except Exception as e:
        return False, f"Upload failed: {str(e)}"
```

### Wins & Challenges Upload

```python
# File: pages/data_input/wc_uploader.py

def upload_wc_to_airtable(
    company_name: str,
    period_name: str,
    parsed_data: dict
) -> tuple[bool, str, dict]:
    """
    Upload Wins & Challenges to Airtable as DRAFT.

    Args:
        company_name: Company name
        period_name: Period (e.g., "2024 Annual")
        parsed_data: Parsed W&C data from excel_parser

    Returns:
        (success: bool, message: str, counts: dict)
    """
    from pages.data_input.wins_challenges_manager import WinsChallengesActionItemsManager

    try:
        manager = WinsChallengesActionItemsManager()

        # Get period ID
        period_id = manager.get_period_id(company_name, period_name)

        if not period_id:
            return False, "Could not find period record", {}

        # Delete existing drafts (overwrite behavior)
        _delete_existing_drafts(manager, period_id)

        counts = {'wins': 0, 'challenges': 0, 'action_items': 0}

        # Upload wins
        for item in parsed_data.get('wins', []):
            manager.create_win(
                period_id=period_id,
                win_text=item['text'],
                display_order=item['display_order'],
                status='draft',  # Not published yet
                name=company_name
            )
            counts['wins'] += 1

        # Upload challenges
        for item in parsed_data.get('challenges', []):
            manager.create_challenge(
                period_id=period_id,
                challenge_text=item['text'],
                display_order=item['display_order'],
                status='draft',
                name=company_name
            )
            counts['challenges'] += 1

        # Upload action items
        for item in parsed_data.get('action_items', []):
            manager.create_action_item(
                period_id=period_id,
                action_item_text=item['text'],
                display_order=item['display_order'],
                status='draft',
                name=company_name
            )
            counts['action_items'] += 1

        return True, "Upload successful", counts

    except Exception as e:
        return False, f"Upload failed: {str(e)}", {}


def _delete_existing_drafts(manager, period_id: str):
    """
    Delete existing draft records before uploading new ones.
    Only deletes drafts, preserves published records.
    """
    # Get existing drafts
    draft_wins = manager.get_items_by_status('wins', period_id, 'draft')
    draft_challenges = manager.get_items_by_status('challenges', period_id, 'draft')
    draft_actions = manager.get_items_by_status('action_items', period_id, 'draft')

    # Hard delete (not soft delete)
    for win in draft_wins:
        manager.hard_delete_win(win['id'])

    for challenge in draft_challenges:
        manager.hard_delete_challenge(challenge['id'])

    for action in draft_actions:
        manager.hard_delete_action_item(action['id'])
```

---

## Permission-Based UI

```python
# File: pages/data_input/data_input_page.py

def data_input_page():
    """Main data input page with permission-based UI."""
    from shared.auth_utils import require_auth, is_super_admin, can_upload_data

    require_auth()

    create_page_header("Data Input")

    # Check permissions
    if not can_upload_data():
        st.error("You don't have permission to upload data.")
        st.stop()

    # Company selection based on role
    if is_super_admin():
        # Super admin can select any company
        companies = get_all_companies()
        selected_company = st.selectbox(
            "Select Company",
            options=[c['name'] for c in companies]
        )
    else:
        # Company user sees only their company
        company_name = get_user_company_name()
        st.info(f"Uploading data for: **{company_name}**")
        selected_company = company_name

    # Period selection
    col1, col2 = st.columns(2)

    with col1:
        year = st.selectbox(
            "Year",
            options=[2024, 2023, 2022, 2021, 2020],
            index=0
        )

    with col2:
        period_type = st.radio(
            "Period Type",
            ["Annual (Year End)", "Mid-Year (June)"],
            horizontal=True
        )

    # Build period string
    if "Annual" in period_type:
        period_name = f"{year} Annual"
    else:
        period_name = f"June {year}"

    st.divider()

    # Input method tabs
    tab1, tab2 = st.tabs(["Upload Excel", "Direct Entry"])

    with tab1:
        render_excel_upload(selected_company, period_name)

    with tab2:
        render_direct_entry(selected_company, period_name)
```

### Excel Upload Tab

```python
def render_excel_upload(company_name: str, period_name: str):
    """Render Excel upload interface."""

    st.subheader("Upload Financial Data")

    # Download template link
    st.markdown("""
    **Instructions:**
    1. Download the template below
    2. Fill in your financial data
    3. Upload the completed file

    [Download Template](templates/BPC2_Upload_Template.xlsx)
    """)

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload completed template",
        type=['xlsx'],
        key='financial_upload'
    )

    if uploaded_file:
        with st.spinner("Parsing file..."):
            # Parse Excel
            from pages.data_input.excel_parser import (
                parse_income_statement_data,
                parse_balance_sheet_data
            )

            import pandas as pd

            # Try to read both sheets
            try:
                is_df = pd.read_excel(uploaded_file, sheet_name='Income Statement')
                bs_df = pd.read_excel(uploaded_file, sheet_name='Balance Sheet')
            except Exception as e:
                st.error(f"Could not read Excel file: {e}")
                return

            # Parse data
            is_success, is_data, is_errors = parse_income_statement_data(is_df)
            bs_success, bs_data, bs_errors = parse_balance_sheet_data(bs_df)

            # Show results
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Income Statement**")
                if is_success:
                    st.success(f"Parsed {len(is_data)} fields")
                else:
                    st.error("Parsing failed")
                    for error in is_errors[:3]:  # Show first 3 errors
                        st.write(f"- {error}")

            with col2:
                st.markdown("**Balance Sheet**")
                if bs_success:
                    st.success(f"Parsed {len(bs_data)} fields")
                else:
                    st.error("Parsing failed")
                    for error in bs_errors[:3]:
                        st.write(f"- {error}")

            # Upload button
            if is_success and bs_success:
                if st.button("Upload to Airtable", type="primary"):
                    with st.spinner("Uploading..."):
                        # Upload income statement
                        is_result, is_msg = upload_income_statement_to_airtable(
                            company_name, period_name, is_data
                        )

                        # Upload balance sheet
                        bs_result, bs_msg = upload_balance_sheet_to_airtable(
                            company_name, period_name, bs_data
                        )

                        if is_result and bs_result:
                            st.success("Data uploaded successfully!")
                            st.balloons()
                        else:
                            st.error(f"Upload failed: {is_msg} / {bs_msg}")
```

---

## Template Protection

```python
# File: create_upload_template.py

def create_protected_template():
    """
    Create Excel template with protection to prevent accidental edits.
    """
    from openpyxl import Workbook
    from openpyxl.worksheet.protection import SheetProtection
    from openpyxl.styles import Protection

    wb = Workbook()

    # Create Income Statement sheet
    ws_is = wb.active
    ws_is.title = "Income Statement"

    # Add headers and labels (protected)
    headers = ['Field', 'Value']
    for col, header in enumerate(headers, 1):
        cell = ws_is.cell(row=1, column=col, value=header)
        cell.protection = Protection(locked=True)

    # Add labels in column A (protected)
    for row, label in enumerate(IS_LABEL_MAPPING.keys(), 2):
        cell = ws_is.cell(row=row, column=1, value=label)
        cell.protection = Protection(locked=True)

        # Column B (values) is unlocked for user input
        value_cell = ws_is.cell(row=row, column=2)
        value_cell.protection = Protection(locked=False)

    # Enable sheet protection (labels locked, values unlocked)
    ws_is.protection = SheetProtection(
        sheet=True,
        objects=True,
        scenarios=True,
        password='bpc2024'  # Simple protection
    )

    # Freeze header row
    ws_is.freeze_panes = 'A2'

    # ... repeat for Balance Sheet ...

    wb.save('bpc_upload_template/BPC2_Upload_Template.xlsx')
```

---

## Key Takeaways

- **Label mapping** translates Excel labels to Airtable field names
- **Multi-sheet parsing** handles IS and BS in single file
- **Validation before upload** catches errors early
- **Draft status** allows review before publication
- **Permission checks** ensure proper access control
- **Overwrite handling** replaces existing drafts cleanly
- **Template protection** prevents accidental label edits

---

## Practice Exercise

**Challenge:** Add a new field to the upload template

**Requirements:**
- Add "Working Capital" to Balance Sheet
- Formula: Total Current Assets - Total Current Liabilities
- Validate it's calculated correctly
- Upload to new Airtable field

<details>
<summary>Show Solution</summary>

```python
# 1. Add to BS_LABEL_MAPPING
BS_LABEL_MAPPING['Working Capital'] = 'working_capital'

# 2. Add validation
def validate_balance_sheet(data: dict) -> list:
    errors = []

    # ... existing validations ...

    # Working capital validation
    if all(k in data for k in [
        'total_current_assets',
        'total_current_liabilities',
        'working_capital'
    ]):
        expected = (
            data['total_current_assets'] -
            data['total_current_liabilities']
        )
        actual = data['working_capital']

        if abs(expected - actual) > 1:
            errors.append(
                f"Working capital ({actual}) doesn't match "
                f"CA - CL ({expected})"
            )

    return errors

# 3. Add to template
labels_to_add = [
    # ... existing labels ...
    'Working Capital',  # New field
]
```

</details>

---

## Related Topics

- **[01-airtable-integration.md](../01-airtable-integration.md)** - Airtable API patterns
- **[publication-control.md](publication-control.md)** - Draft/publish workflow
- **[authentication-security.md](authentication-security.md)** - Permission system

---

*You now understand the complete Excel upload system!*
