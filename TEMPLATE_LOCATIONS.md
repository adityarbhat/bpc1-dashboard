# BPC Upload Template Locations

## Current Active Template
**Location**: `bpc_upload_template/BPC2_Upload_Template.xlsx`
**Status**: ✅ ACTIVE - Used by upload page download button
**Features**:
- Two sheets: Income Statement and Balance Sheet
- Three columns per sheet: Line Item | Description | 12/31/25 (Amount)
- Descriptions pulled from Chart of Accounts glossary
- Professional formatting with Atlas BPC branding
- 53 Income Statement line items
- 25 Balance Sheet line items

## Old Template (Deprecated)
**Location**: `assets/upload_template.xlsx`
**Status**: ⚠️ DEPRECATED - Kept for reference only
**Note**: This older template did not include descriptions column

## Upload Page Configuration
The upload page (`pages/data_input/data_input_page.py`) downloads the template from:
```python
'bpc_upload_template/BPC2_Upload_Template.xlsx'
```

## To Regenerate Template
Run the generation script:
```bash
python3 create_upload_template.py
```

This will create a fresh template at `bpc_upload_template/BPC2_Upload_Template.xlsx` with all line items and descriptions.

## Test Template
**Location**: `bpc_upload_template/BPC2_Upload_Template_TEST.xlsx`
**Status**: FOR TESTING ONLY
**Note**: Contains sample data for testing upload functionality
