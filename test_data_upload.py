"""
Quick test script for data upload functionality
Run this to test upload logic without the UI
"""

from pages.data_input.data_validator import validate_balance_sheet, validate_income_statement
from pages.data_input.data_uploader import upload_balance_sheet_to_airtable, upload_income_statement_to_airtable

# Test 1: Validate Balance Sheet
print("=" * 60)
print("TEST 1: Balance Sheet Validation")
print("=" * 60)

test_bs_data = {
    'total_assets': 1000000,
    'total_liabilities': 600000,
    'owners_equity': 400000,
    'total_liabilities_equity': 1000000,
    'total_current_assets': 500000,
    'total_current_liabilities': 300000,
    'accumulated_depreciation': -200000  # Should be negative
}

is_valid, errors = validate_balance_sheet(test_bs_data)
if is_valid:
    print("✅ Balance Sheet Validation: PASS")
else:
    print("❌ Balance Sheet Validation: FAIL")
    for error in errors:
        print(f"   - {error}")

# Test 2: Validate Income Statement
print("\n" + "=" * 60)
print("TEST 2: Income Statement Validation")
print("=" * 60)

test_is_data = {
    'total_revenue': 1000000,
    'total_cost_of_revenue': 600000,
    'gross_profit': 400000,  # Should equal revenue - cost
    'total_operating_expenses': 200000,
    'operating_profit': 200000,  # Should equal gross profit - operating expenses
}

is_valid, errors = validate_income_statement(test_is_data)
if is_valid:
    print("✅ Income Statement Validation: PASS")
else:
    print("❌ Income Statement Validation: FAIL")
    for error in errors:
        print(f"   - {error}")

# Test 3: Test with unbalanced data
print("\n" + "=" * 60)
print("TEST 3: Unbalanced Balance Sheet (should fail)")
print("=" * 60)

unbalanced_bs = {
    'total_assets': 1000000,
    'total_liabilities': 500000,
    'owners_equity': 400000,  # Total = 900000 (unbalanced!)
    'total_liabilities_equity': 900000,
    'total_current_assets': 500000,
    'total_current_liabilities': 300000,
}

is_valid, errors = validate_balance_sheet(unbalanced_bs)
if not is_valid:
    print("✅ Correctly detected unbalanced sheet")
    for error in errors:
        print(f"   - {error}")
else:
    print("❌ Should have failed validation!")

print("\n" + "=" * 60)
print("Validation Tests Complete!")
print("=" * 60)
print("\nTo test actual upload to Airtable:")
print("1. Make sure your .env file has AIRTABLE_BASE_ID and AIRTABLE_PAT")
print("2. Use the Streamlit UI: streamlit run financial_dashboard.py")
print("3. Navigate to 📝 Upload Data and submit real data")
