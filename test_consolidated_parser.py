"""
Test the consolidated Excel parser to verify it works correctly
"""

from pages.data_input.excel_parser import parse_consolidated_excel

# Test with the sample template
test_file_path = 'bpc_upload_template/BPC2_Upload_Template_TEST.xlsx'

print("Testing consolidated Excel parser...")
print(f"File: {test_file_path}\n")

with open(test_file_path, 'rb') as f:
    results, warnings = parse_consolidated_excel(f)

# Display results
print("=" * 60)
print("INCOME STATEMENT RESULTS")
print("=" * 60)
print(f"Matched items: {results['is_matched']}")
print(f"Unmatched items: {len(results['is_unmatched'])}")
if results['is_unmatched']:
    print(f"Unmatched: {results['is_unmatched'][:5]}")  # Show first 5
print(f"Sample data (first 5 items):")
for i, (key, value) in enumerate(list(results['is_data'].items())[:5]):
    print(f"  {key}: ${value:,.2f}")
print()

print("=" * 60)
print("BALANCE SHEET RESULTS")
print("=" * 60)
print(f"Matched items: {results['bs_matched']}")
print(f"Unmatched items: {len(results['bs_unmatched'])}")
if results['bs_unmatched']:
    print(f"Unmatched: {results['bs_unmatched'][:5]}")  # Show first 5
print(f"Sample data (first 5 items):")
for i, (key, value) in enumerate(list(results['bs_data'].items())[:5]):
    print(f"  {key}: ${value:,.2f}")
print()

print("=" * 60)
print("BALANCE SHEET VALIDATION")
print("=" * 60)
print(f"Is balanced: {results['is_balanced']}")
if not results['is_balanced']:
    print(f"Difference: ${abs(results['balance_difference']):,.2f}")
print()

# Show warnings if any
if warnings:
    print("=" * 60)
    print("WARNINGS")
    print("=" * 60)
    for warning in warnings:
        print(f"  {warning}")
    print()

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"✅ Income Statement: {results['is_matched']} items loaded")
print(f"✅ Balance Sheet: {results['bs_matched']} items loaded")
if results['is_balanced']:
    print("✅ Balance Sheet is balanced")
else:
    print(f"⚠️  Balance Sheet unbalanced by: ${abs(results['balance_difference']):,.2f}")
print()

if results['is_matched'] > 0 and results['bs_matched'] > 0:
    print("🎉 SUCCESS: Both sheets loaded successfully!")
else:
    print("❌ FAILED: Not all sheets loaded correctly")
