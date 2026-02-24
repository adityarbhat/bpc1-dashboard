# Feature Deep Dive: Excel Export System

## Overview

This deep dive covers the centralized Excel export system that generates professional, formatted multi-sheet workbooks from dashboard data. You'll learn about lazy loading patterns, color-coded formatting, and the export orchestration architecture.

**What You'll Learn:**
- Multi-sheet Excel generation architecture
- Lazy loading for performance optimization
- Professional formatting with color coding
- Data extraction from group pages
- Export page UI patterns

**Difficulty:** Intermediate
**Time:** 45-60 minutes

---

## The Export Challenge

### Requirements

Build an export system that:
1. Exports all 7 group analysis sheets in one file
2. Matches the web display exactly (colors, formatting)
3. Doesn't impact performance when not used (lazy loading)
4. Provides professional Excel formatting
5. Works with any period/year combination

### The Solution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Export System Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   group_export.py (UI)                                           │
│         │                                                        │
│         ↓ (user clicks export)                                   │
│   export_utils.py (Orchestration)                                │
│         │                                                        │
│         ├──→ extract_ratios_data_for_export()                   │
│         ├──→ extract_balance_sheet_data_for_export()            │
│         ├──→ extract_income_statement_data_for_export()         │
│         ├──→ extract_labor_cost_data_for_export()               │
│         ├──→ extract_business_mix_data_for_export()             │
│         ├──→ extract_value_data_for_export()                    │
│         └──→ extract_cash_flow_data_for_export()                │
│                     │                                            │
│                     ↓                                            │
│   excel_formatter.py (Professional Formatting)                   │
│         │                                                        │
│         ├──→ format_ratios_sheet()     → Color-coded thresholds │
│         ├──→ format_balance_sheet()    → Winner highlighting    │
│         ├──→ format_income_statement() → Winner highlighting    │
│         ├──→ format_labor_cost()       → Professional styling   │
│         ├──→ format_business_mix()     → Professional styling   │
│         ├──→ format_value()            → Winner highlighting    │
│         └──→ format_cash_flow()        → Professional styling   │
│                     │                                            │
│                     ↓                                            │
│              BytesIO (In-memory Excel file)                      │
│                     │                                            │
│                     ↓                                            │
│              st.download_button()                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Files

```
shared/
├── export_utils.py      # Orchestration (229 lines)
└── excel_formatter.py   # Professional formatting (400+ lines)

pages/group_pages/
└── group_export.py      # Export page UI (161 lines)
```

---

## Lazy Loading Pattern

### The Problem

```python
# ❌ WRONG - Imports happen on app load
from shared.export_utils import create_multi_sheet_export
from shared.excel_formatter import format_all_sheets

# Every page load imports openpyxl, pandas, etc.
# Even when user never uses export feature!
```

### The Solution: Lazy Import

```python
# ✅ CORRECT - Import only when needed
def export_page():
    if st.button("Generate Export"):
        # Import only when button clicked
        from shared.export_utils import create_multi_sheet_export

        data = create_multi_sheet_export(period, year)
        # ...
```

### Implementation in Export Utils

```python
# File: shared/export_utils.py

def create_multi_sheet_export(period: str, year: int) -> bytes:
    """
    Create multi-sheet Excel export with professional formatting.

    Lazy loads all dependencies for performance.
    """
    # Lazy imports - only loaded when function called
    import pandas as pd
    from io import BytesIO
    from openpyxl import Workbook

    # Also lazy import formatters
    from shared.excel_formatter import (
        format_ratios_sheet,
        format_balance_sheet_sheet,
        format_income_statement_sheet,
        format_labor_cost_sheet,
        format_business_mix_sheet,
        format_value_sheet,
        format_cash_flow_sheet
    )

    # Lazy import data extractors from group pages
    from pages.group_pages.group_ratios import extract_ratios_data_for_export
    from pages.group_pages.group_balance_sheet import extract_balance_sheet_data_for_export
    # ... etc

    # Create workbook in memory
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Phase 1: Extract and write data
        sheets = [
            ('Ratios', extract_ratios_data_for_export, format_ratios_sheet),
            ('Balance Sheet', extract_balance_sheet_data_for_export, format_balance_sheet_sheet),
            ('Income Statement', extract_income_statement_data_for_export, format_income_statement_sheet),
            ('Labor Cost', extract_labor_cost_data_for_export, format_labor_cost_sheet),
            ('Business Mix', extract_business_mix_data_for_export, format_business_mix_sheet),
            ('Value', extract_value_data_for_export, format_value_sheet),
            ('Cash Flow', extract_cash_flow_data_for_export, format_cash_flow_sheet),
        ]

        for sheet_name, extractor, formatter in sheets:
            try:
                # Extract data
                df = extractor(period)

                # Write to sheet
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Apply formatting
                worksheet = writer.sheets[sheet_name]
                formatter(worksheet, df)

            except Exception as e:
                # Log error but continue with other sheets
                st.warning(f"Could not export {sheet_name}: {e}")

    return output.getvalue()
```

---

## Professional Formatting

### Atlas Branding Colors

```python
# File: shared/excel_formatter.py

# Atlas Van Lines brand colors
ATLAS_BLUE = "025a9a"
ATLAS_SECONDARY = "0e9cd5"
ATLAS_RED = "c2002f"

# Performance indicator colors
COLOR_GREEN = "28a745"    # Great performance
COLOR_YELLOW = "ffc107"   # Caution
COLOR_RED = "dc3545"      # Needs improvement
COLOR_WHITE = "FFFFFF"    # Background
```

### Ratio Thresholds (Matching Web Display)

```python
# Critical: These must match the web dashboard exactly!
RATIO_THRESHOLDS = {
    'Current Ratio': {
        'great': 2.4,           # >= 2.4 is green
        'caution': [1.5, 2.3],  # 1.5-2.3 is yellow
        # < 1.5 is red
        'higher_is_better': True
    },
    'Debt to Equity': {
        'great': 1.1,           # <= 1.1 is green (reversed!)
        'caution': [1.2, 1.7],  # 1.2-1.7 is yellow
        # > 1.7 is red
        'higher_is_better': False
    },
    'Net Profit Margin': {
        'great': 0.05,          # >= 5% is green
        'caution': [0.03, 0.0499],  # 3-4.99% is yellow
        # < 3% is red
        'higher_is_better': True
    },
    'Operating Profit Margin': {
        'great': 0.06,
        'caution': [0.04, 0.0599],
        'higher_is_better': True
    },
    'Gross Margin': {
        'great': 0.40,
        'caution': [0.35, 0.399],
        'higher_is_better': True
    },
    'OCF / Revenue': {
        'great': 0.05,
        'caution': [0.02, 0.0499],
        'higher_is_better': True
    },
    'FCF / Revenue': {
        'great': 0.03,
        'caution': [0.0, 0.0299],
        'higher_is_better': True
    },
    'NCF / Revenue': {
        'great': 0.05,
        'caution': [0.02, 0.0499],
        'higher_is_better': True
    },
    # ... additional ratios
}
```

### Color Coding Implementation

```python
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

def get_performance_color(value: float, ratio_name: str) -> str:
    """
    Determine performance color based on ratio thresholds.

    Returns:
        Hex color code (without #)
    """
    if value is None:
        return COLOR_WHITE

    thresholds = RATIO_THRESHOLDS.get(ratio_name, {})

    if not thresholds:
        return COLOR_WHITE

    higher_is_better = thresholds.get('higher_is_better', True)
    great_threshold = thresholds.get('great')
    caution_range = thresholds.get('caution', [])

    if higher_is_better:
        # Higher values are better (e.g., Current Ratio)
        if great_threshold and value >= great_threshold:
            return COLOR_GREEN
        elif caution_range and caution_range[0] <= value <= caution_range[1]:
            return COLOR_YELLOW
        else:
            return COLOR_RED
    else:
        # Lower values are better (e.g., Debt to Equity)
        if great_threshold and value <= great_threshold:
            return COLOR_GREEN
        elif caution_range and caution_range[0] <= value <= caution_range[1]:
            return COLOR_YELLOW
        else:
            return COLOR_RED


def apply_cell_color(cell, color_hex: str):
    """Apply background color to cell."""
    cell.fill = PatternFill(
        start_color=color_hex,
        end_color=color_hex,
        fill_type='solid'
    )
```

### Formatting a Ratios Sheet

```python
def format_ratios_sheet(worksheet, df):
    """
    Apply professional formatting to ratios sheet.

    Args:
        worksheet: openpyxl worksheet object
        df: pandas DataFrame with ratios data
    """
    # Header styling
    header_fill = PatternFill(start_color=ATLAS_BLUE, end_color=ATLAS_BLUE, fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=11)

    for cell in worksheet[1]:  # First row is header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Data rows with color coding
    for row_idx, row in enumerate(worksheet.iter_rows(min_row=2), start=2):
        company_cell = row[0]  # First column is company name

        for col_idx, cell in enumerate(row[1:], start=1):  # Skip company column
            ratio_name = df.columns[col_idx]
            value = cell.value

            # Get performance color
            color = get_performance_color(value, ratio_name)
            apply_cell_color(cell, color)

            # Format number
            if value is not None:
                if 'Margin' in ratio_name or 'Revenue' in ratio_name:
                    cell.number_format = '0.0%'
                else:
                    cell.number_format = '0.00'

            cell.alignment = Alignment(horizontal='center')

    # Auto-width columns
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter

        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass

        adjusted_width = min(max_length + 2, 25)
        worksheet.column_dimensions[column_letter].width = adjusted_width

    # Freeze header row
    worksheet.freeze_panes = 'A2'
```

### Winner Highlighting

```python
def format_balance_sheet_sheet(worksheet, df):
    """
    Format balance sheet with winner highlighting.
    Winners (best performers) get special styling.
    """
    # ... header styling same as above ...

    # Identify winners per metric (column)
    for col_idx in range(1, len(df.columns)):
        column_data = df.iloc[:, col_idx]
        metric_name = df.columns[col_idx]

        # Determine if higher or lower is better
        if 'debt' in metric_name.lower() or 'liability' in metric_name.lower():
            winner_idx = column_data.idxmin()  # Lower is better
        else:
            winner_idx = column_data.idxmax()  # Higher is better

        # Apply winner styling
        winner_row = winner_idx + 2  # +2 for header and 0-indexing
        winner_cell = worksheet.cell(row=winner_row, column=col_idx + 1)
        winner_cell.font = Font(bold=True, color=COLOR_GREEN)
```

---

## Data Extraction Pattern

### Example: Ratios Data Extraction

```python
# File: pages/group_pages/group_ratios.py

def extract_ratios_data_for_export(period: str) -> pd.DataFrame:
    """
    Extract ratios data formatted for Excel export.

    Args:
        period: Period identifier (e.g., "2024 Annual")

    Returns:
        DataFrame with companies as rows, ratios as columns
    """
    from shared.airtable_connection import AirtableConnection

    airtable = AirtableConnection()
    companies = airtable.get_companies_cached()

    rows = []

    for company in companies:
        company_name = company['name']

        # Get balance sheet data for ratios
        balance_data = airtable.get_balance_sheet_data_by_period(company_name, period)
        record = balance_data[0] if balance_data else {}

        # Get income statement data for margins
        income_data = airtable.get_income_statement_data_by_period(company_name, period)
        income_record = income_data[0] if income_data else {}

        # Get cash flow ratios
        year = int(period.split()[0])
        from shared.cash_flow_utils import get_cash_flow_ratios
        cash_flow = get_cash_flow_ratios(airtable, company_name, year) or {}

        # Build row
        row = {
            'Company': company_name,
            'Current Ratio': record.get('current_ratio'),
            'Debt to Equity': record.get('debt_to_equity'),
            'Net Profit Margin': income_record.get('net_profit_margin'),
            'Operating Profit Margin': income_record.get('operating_profit_margin'),
            'Gross Margin': income_record.get('gross_margin'),
            'OCF / Revenue': cash_flow.get('ocf_rev'),
            'FCF / Revenue': cash_flow.get('fcf_rev'),
            'NCF / Revenue': cash_flow.get('ncf_rev'),
        }
        rows.append(row)

    return pd.DataFrame(rows)
```

---

## Export Page UI

```python
# File: pages/group_pages/group_export.py

import streamlit as st
from shared.page_components import create_page_header
from shared.css_styles import apply_all_styles
from shared.auth_utils import require_auth

def export_page():
    """Export page with year selection and download."""
    require_auth()

    create_page_header("Group Analysis Export")

    st.markdown("""
    Export all group analysis data to a professionally formatted Excel workbook.
    The export includes all 7 analysis sheets with color-coded performance indicators.
    """)

    # Year selection buttons
    st.subheader("Select Year")

    col1, col2, col3, col4, col5 = st.columns(5)
    years = [2024, 2023, 2022, 2021, 2020]

    selected_year = st.session_state.get('export_year', 2024)

    for i, (col, year) in enumerate(zip([col1, col2, col3, col4, col5], years)):
        with col:
            if st.button(str(year), key=f"year_{year}",
                        type="primary" if year == selected_year else "secondary"):
                st.session_state.export_year = year
                st.rerun()

    # Period selection
    period_type = st.radio(
        "Period Type",
        ["Annual (Year End)", "Mid-Year (June)"],
        horizontal=True
    )

    # Generate period string
    if "Annual" in period_type:
        period = f"{selected_year} Annual"
    else:
        period = f"June {selected_year}"

    st.divider()

    # Export button
    if st.button("Generate Export", type="primary"):
        with st.spinner("Generating export... This may take 5-15 seconds."):
            try:
                # Lazy import
                from shared.export_utils import (
                    create_multi_sheet_export,
                    generate_filename
                )

                # Generate Excel
                excel_data = create_multi_sheet_export(period, selected_year)
                filename = generate_filename(period, selected_year)

                # Store in session for download
                st.session_state.export_data = excel_data
                st.session_state.export_filename = filename
                st.session_state.export_ready = True

                st.success("Export generated successfully!")

            except Exception as e:
                st.error(f"Export failed: {e}")

    # Download button (appears after generation)
    if st.session_state.get('export_ready'):
        st.download_button(
            label="Download Excel File",
            data=st.session_state.export_data,
            file_name=st.session_state.export_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

        if st.button("Clear"):
            st.session_state.export_ready = False
            st.session_state.export_data = None
            st.rerun()

    apply_all_styles()
```

---

## Filename Generation

```python
def generate_filename(period: str, year: int) -> str:
    """
    Generate standardized filename for export.

    Format: BPC_Group_Analysis_2024_YearEnd_20240115.xlsx

    Args:
        period: Period string (e.g., "2024 Annual")
        year: Year number

    Returns:
        Formatted filename
    """
    from datetime import datetime

    # Determine period type
    if 'Annual' in period:
        period_suffix = 'YearEnd'
    else:
        period_suffix = 'MidYear'

    # Current date stamp
    date_stamp = datetime.now().strftime('%Y%m%d')

    return f"BPC_Group_Analysis_{year}_{period_suffix}_{date_stamp}.xlsx"
```

---

## Key Takeaways

- **Lazy loading** prevents performance impact when export isn't used
- **Two-phase process**: Extract data first, then apply formatting
- **Color thresholds must match web display** for consistency
- **Per-sheet error handling** prevents total failure if one sheet fails
- **BytesIO** enables in-memory Excel generation (no temp files)
- **Professional formatting** includes frozen panes, auto-width, and branding

---

## Practice Exercise

**Challenge:** Add a custom summary sheet to the export

**Requirements:**
- First sheet named "Summary"
- Shows company count and period
- Lists all sheet names with row counts
- Includes export timestamp
- Atlas blue header styling

<details>
<summary>Show Solution</summary>

```python
def create_summary_sheet(writer, period: str, sheet_stats: dict):
    """Create summary sheet as first sheet in workbook."""
    from datetime import datetime

    summary_data = {
        'Item': ['Export Date', 'Period', 'Total Companies', '---'] +
                [f'{name} Rows' for name in sheet_stats.keys()],
        'Value': [
            datetime.now().strftime('%Y-%m-%d %H:%M'),
            period,
            sheet_stats.get('Ratios', {}).get('rows', 0),
            '---'
        ] + [stats.get('rows', 0) for stats in sheet_stats.values()]
    }

    df = pd.DataFrame(summary_data)
    df.to_excel(writer, sheet_name='Summary', index=False)

    # Format
    worksheet = writer.sheets['Summary']
    header_fill = PatternFill(start_color=ATLAS_BLUE, fill_type='solid')

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = Font(color='FFFFFF', bold=True)

    worksheet.column_dimensions['A'].width = 25
    worksheet.column_dimensions['B'].width = 30
```

</details>

---

## Related Topics

- **[02-performance-optimization.md](../02-performance-optimization.md)** - More on lazy loading
- **[06-data-transformation.md](../06-data-transformation.md)** - Data preparation patterns
- **[gauge-charts-implementation.md](gauge-charts-implementation.md)** - Color threshold logic

---

*You now understand the complete Excel export system!*
