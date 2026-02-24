# Exercise 01: Fetch Company Data from Airtable

## Goal

Create a function that fetches company ratios. You'll use this in the next exercises.

---

## Task

Write `get_company_ratio()` that:
1. Takes a company name and period
2. Returns the current ratio (or None if not found)

```python
# Usage
ratio = get_company_ratio("Ace", "2024 Annual")
print(ratio)  # 2.15
```

---

<details>
<summary>Hint 1: Import & Connect</summary>

```python
from shared.airtable_connection import AirtableConnection

# Create connection (handles auth automatically)
airtable = AirtableConnection()
```

</details>

---

<details>
<summary>Hint 2: Fetch Balance Sheet Data</summary>

```python
# Method returns a LIST (empty if no data found)
data = airtable.get_balance_sheet_data_by_period(company_name, period)

# data = [{'current_ratio': 2.15, 'debt_to_equity': 0.85, ...}]
# or data = [] if no match
```

</details>

---

<details>
<summary>Hint 3: Safe Field Access</summary>

```python
# Check if data exists, then get field safely
if data:
    record = data[0]
    ratio = record.get('current_ratio')  # Returns None if field missing
else:
    ratio = None
```

</details>

---

<details>
<summary>Hint 4: Full Solution</summary>

```python
# mini_dashboard.py - Exercise 1
from shared.airtable_connection import AirtableConnection

def get_company_ratio(company_name: str, period: str) -> float | None:
    """Fetch current ratio for a company."""
    airtable = AirtableConnection()
    data = airtable.get_balance_sheet_data_by_period(company_name, period)

    if data:
        return data[0].get('current_ratio')
    return None

def get_all_companies() -> list[str]:
    """Get list of company names."""
    airtable = AirtableConnection()
    companies = airtable.get_companies_cached()
    return sorted([c['name'] for c in companies])

# Test it
if __name__ == "__main__":
    print("Companies:", get_all_companies())
    print("Ace ratio:", get_company_ratio("Ace", "2024 Annual"))
```

Run: `python mini_dashboard.py`

</details>

---

## What You Built

Two reusable functions:
- `get_company_ratio(company, period)` → returns ratio or None
- `get_all_companies()` → returns sorted list of names

**Keep this file open** - you'll add to it in Exercise 2.

---

## Next

Continue to **[02_session_state_essentials.md](02_session_state_essentials.md)** to add a company selector.
