# BPC Upload Template

This folder contains the Excel template for uploading financial data to the BPC Dashboard.

## Template File

**BPC2_Upload_Template.xlsx** - Excel workbook with two sheets:

### Income Statement Sheet
- Contains all revenue, direct expenses, operating expenses, and other income/expense line items
- Three columns:
  1. **Line Item** - The name of the financial line item
  2. **Description** - Detailed description from the financial glossary
  3. **12/31/25** - Amount column (enter your financial data here)

### Balance Sheet Sheet
- Contains all assets, liabilities, and equity line items organized by category:
  - Current Assets
  - Fixed Assets
  - Other Assets
  - Current Liabilities
  - Long-term Liabilities
  - Equity
- Three columns:
  1. **Line Item** - The name of the financial line item
  2. **Description** - Detailed description from the financial glossary
  3. **12/31/25** - Amount column (enter your financial data here)

## How to Use

1. Download the template: `BPC2_Upload_Template.xlsx`
2. Fill in the **12/31/25** column with your financial data
3. Enter amounts as positive numbers (except where noted to enter as negative)
4. Upload the completed file to the BPC Dashboard via the Upload Data page

## Notes

- **Descriptions are read-only** - They are provided as reference from the Chart of Accounts
- **Category headers** (like "REVENUE", "CURRENT ASSETS") are for organization only - do not enter data in those rows
- **Currency format** - All amounts should be in US Dollars ($)
- **Negative values** - Some fields like Accumulated Depreciation and CEO Comp should be entered as negative numbers
- **Date column** - Currently shows 12/31/25 for 2025 year-end data; this will be updated as needed for future periods

## Generation Script

The template is generated using `create_upload_template.py` script which:
- Pulls line items from the data transformation mappings
- Adds descriptions from `description_mappings.py`
- Creates formatted Excel sheets with Atlas BPC branding
- Applies consistent styling and formatting

To regenerate the template:
```bash
python3 create_upload_template.py
```

## Integration

This template is referenced in the Data Input page (`pages/data_input/data_input_page.py`) and available for download via the sidebar.
