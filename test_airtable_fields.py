#!/usr/bin/env python3
"""
Quick diagnostic script to check what fields exist in Airtable
and what data was actually uploaded.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Get credentials
base_id = os.getenv("AIRTABLE_BASE_ID")
pat = os.getenv("AIRTABLE_PAT")

headers = {
    'Authorization': f'Bearer {pat}',
    'Content-Type': 'application/json'
}

base_url = f"https://api.airtable.com/v0/{base_id}"

# Fetch the most recent income statement records (last 3)
print("=" * 80)
print("CHECKING INCOME STATEMENT DATA TABLE")
print("=" * 80)

response = requests.get(
    f"{base_url}/income_statement_data",
    headers=headers,
    params={'maxRecords': 3, 'sort[0][field]': 'upload_date', 'sort[0][direction]': 'desc'}
)

if response.status_code == 200:
    records = response.json().get('records', [])
    print(f"\nFound {len(records)} recent records\n")

    for i, record in enumerate(records, 1):
        print(f"Record {i} (ID: {record['id']}):")
        fields = record.get('fields', {})
        print(f"  Fields present: {sorted(fields.keys())}")

        # Check for publication fields
        if 'publication_status' in fields:
            print(f"  ✅ publication_status: {fields['publication_status']}")
        else:
            print(f"  ❌ publication_status: FIELD NOT FOUND")

        if 'submitted_by' in fields:
            print(f"  ✅ submitted_by: {fields['submitted_by']}")
        else:
            print(f"  ❌ submitted_by: FIELD NOT FOUND")

        if 'submitted_date' in fields:
            print(f"  ✅ submitted_date: {fields['submitted_date']}")
        else:
            print(f"  ❌ submitted_date: FIELD NOT FOUND")

        # Show company and period info
        if 'company' in fields:
            print(f"  Company: {fields.get('company', 'N/A')}")
        if 'period' in fields:
            print(f"  Period: {fields.get('period', 'N/A')}")
        if 'upload_date' in fields:
            print(f"  Upload Date: {fields.get('upload_date', 'N/A')}")

        print()
else:
    print(f"❌ Failed to fetch records: {response.status_code}")
    print(f"Response: {response.text}")

print("=" * 80)
print("DONE")
print("=" * 80)
