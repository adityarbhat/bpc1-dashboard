# Financial Data Input Module

## Overview
The Data Input module provides a user-friendly interface for entering Balance Sheet and Income Statement data directly into the dashboard, which then uploads to Airtable. This eliminates the need for Excel files and manual data transformation scripts.

## Features

### 1. Interactive Data Entry
- **Spreadsheet-like Interface**: Uses Streamlit's `st.data_editor` for familiar Excel-like data entry
- **Two Tabs**: Separate tabs for Income Statement and Balance Sheet data
- **Pre-populated Fields**: Automatically loads existing data from Airtable for editing

### 2. Smart Validation
- **Real-time Calculations**: Automatically calculates totals as you enter data
- **Balance Sheet Equation**: Validates that Assets = Liabilities + Equity
- **Income Statement Logic**: Ensures Gross Profit = Revenue - COGS, etc.
- **Error Prevention**: Submit button disabled if validation fails

### 3. Flexible Period Selection
- **Multi-year Support**: Input data for 2020-2025
- **Period Types**: Annual, H1 (Mid Year), or H2
- **Company Selection**: Choose which company's data to input

### 4. Automatic Upload
- **Direct to Airtable**: Uploads validated data directly to your Airtable base
- **Period Management**: Automatically creates financial periods if they don't exist
- **Audit Trail**: Logs all uploads with timestamp and data source

## File Structure

```
pages/data_input/
├── __init__.py                 # Module initialization
├── data_input_page.py         # Main UI with Income Statement & Balance Sheet tabs
├── data_validator.py          # Validation logic for financial data
├── data_uploader.py           # Airtable upload functionality
└── README.md                  # This file
```

## Usage

### Accessing the Data Input Page

1. **From the Dashboard**: Click the "📝 Upload Data" button in the sidebar under the "Admin" section
2. **Direct Navigation**: Set `st.session_state.current_page = 'data_input'`

### Entering Data

#### Income Statement

1. Select the company and period (year + period type)
2. Enter revenue data in the Revenue section
3. Enter direct expenses (Cost of Revenue)
4. Enter operating expenses
5. Enter non-operating income/expenses
6. Review auto-calculated totals:
   - Total Revenue
   - Total Cost of Revenue
   - Gross Profit
   - Total Operating Expenses
   - Operating Profit
   - Profit Before Tax
7. Click "✅ Submit Income Statement to Airtable"

#### Balance Sheet

1. Select the company and period
2. Enter Current Assets data
3. Enter Fixed Assets (Gross Fixed Assets and Accumulated Depreciation)
4. Enter Other Assets
5. Review Total Assets calculation
6. Enter Current Liabilities
7. Enter Long-term Liabilities
8. Enter Owner's Equity
9. Verify the balance sheet equation: Assets = Liabilities + Equity
10. Click "✅ Submit Balance Sheet to Airtable" (enabled only if balanced)

### Field Mappings

The module uses the same field mappings as the existing data transformation scripts:

- **Balance Sheet**: See `BALANCE_SHEET_MAPPING` in `data_transformation_bs.py`
- **Income Statement**: See `INCOME_STATEMENT_MAPPING` in `data_transformation_is.py`

## Validation Rules

### Balance Sheet
- ✅ Total Assets = Total Liabilities + Owner's Equity (±$0.01 tolerance)
- ✅ Net Fixed Assets = Gross Fixed Assets - Accumulated Depreciation
- ✅ Total Assets ≥ 0
- ✅ Total Current Assets ≥ 0
- ✅ Owner's Equity ≥ 0
- ⚠️ Accumulated Depreciation should be ≤ 0

### Income Statement
- ✅ Gross Profit = Total Revenue - Total Cost of Revenue
- ✅ Operating Profit = Gross Profit - Total Operating Expenses
- ✅ Profit Before Tax = Operating Profit + Total Non-Operating Income
- ⚠️ Warning if Total Revenue = 0

### Period Format
- Valid formats: "YYYY Annual", "YYYY H1", "YYYY H2"
- Examples: "2025 Annual", "2024 H1", "2024 H2"

## API Integration

### Airtable Tables Used

1. **companies** - Company master data
2. **financial_periods** - Period definitions (created automatically if needed)
3. **balance_sheet_data** - Balance sheet records
4. **income_statement_data** - Income statement records
5. **data_import_log** - Audit trail of all uploads

### Upload Process

1. **Validation**: Data is validated before upload
2. **Company Lookup**: Retrieves company ID from Airtable
3. **Period Management**:
   - Checks if period exists for the company
   - Creates new period record if needed with smart detection
4. **Data Upload**:
   - Uploads financial data to appropriate table
   - Links to company and period records
   - Adds data source timestamp
5. **Logging**: Records import activity in data_import_log

### Error Handling

- Missing credentials → User-friendly error message
- Validation failures → Detailed error list shown to user
- Company not found → Clear error message
- Airtable API errors → Error details logged and displayed
- Network issues → Graceful degradation with retry option

## Advanced Features

### Future Enhancements (Planned)

1. **Excel Upload**: Upload Excel file and parse automatically
2. **Copy from Previous Year**: Pre-fill with last year's data
3. **Bulk Upload**: Input multiple years at once
4. **Export Template**: Download Excel template for offline editing
5. **Approval Workflow**: Submit for review before committing to Airtable
6. **Version History**: Track changes and allow rollback
7. **Calculated Fields**: Auto-calculate ratios and metrics
8. **Role-based Access**: Restrict companies based on user role

### Configuration Options

```python
# In data_input_page.py, you can customize:

# Years available for selection
years = ['2020', '2021', '2022', '2023', '2024', '2025']

# Period types
period_types = ['Annual', 'H1 (Mid Year)', 'H2']

# Field configurations for each section
revenue_fields = [...]
direct_expense_fields = [...]
operating_expense_fields = [...]
```

## Troubleshooting

### Common Issues

**Issue**: Submit button is disabled
- **Solution**: Check that all validation rules are met. For Balance Sheet, ensure Assets = Liabilities + Equity

**Issue**: Data not appearing in Airtable
- **Solution**: Verify Airtable credentials in `.env` file. Check console for error messages.

**Issue**: Company not found
- **Solution**: Ensure the company exists in the `companies` table in Airtable

**Issue**: Import error when loading page
- **Solution**: Ensure virtual environment is activated and all dependencies are installed

### Debug Mode

To enable verbose logging:

```python
# In data_uploader.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

Required packages (already in requirements.txt):
- streamlit >= 1.37.0
- pandas >= 2.0.0
- requests >= 2.31.0
- python-dotenv >= 1.0.0

## Testing

### Unit Tests (Manual)

```python
# Test validation
from pages.data_input.data_validator import validate_balance_sheet

test_data = {
    'total_assets': 1000000,
    'total_liabilities': 600000,
    'owners_equity': 400000,
    'total_liabilities_equity': 1000000,
    'total_current_assets': 500000,
    'total_current_liabilities': 300000
}

is_valid, errors = validate_balance_sheet(test_data)
print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
```

### Integration Tests

1. Launch Streamlit app: `streamlit run financial_dashboard.py`
2. Click "📝 Upload Data" in sidebar
3. Select a company and period
4. Enter sample data
5. Verify calculations are correct
6. Submit and verify data appears in Airtable

## Security Considerations

- **Environment Variables**: Airtable credentials stored in `.env` (not committed to git)
- **Input Sanitization**: All user inputs validated before upload
- **Error Messages**: No sensitive data exposed in error messages
- **Audit Trail**: All uploads logged with timestamp and source

## Support

For questions or issues:
1. Check this README
2. Review validation error messages
3. Check Airtable API documentation
4. Contact the development team

## Version History

- **v1.0** (2025-10-14): Initial release
  - Income Statement data entry
  - Balance Sheet data entry
  - Real-time validation
  - Direct Airtable upload
  - Period management
