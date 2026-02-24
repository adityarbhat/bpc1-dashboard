# Exercise 02: Add Company Selector with Session State

## Goal

Add a dropdown that remembers the selected company across interactions.

---

## The Problem

Without session state, Streamlit resets variables on every interaction:

```python
selected = "Ace"  # Resets every time!
if st.button("Do something"):
    pass  # After click, selected is "Ace" again
```

---

## Task

Convert your `mini_dashboard.py` into a Streamlit app:
1. Show a dropdown with all companies
2. Display the selected company's ratio
3. Selection should persist when clicking buttons

```
Select Company: [Baker ▼]
Current Ratio: 2.31
[Refresh]  ← clicking shouldn't reset dropdown
```

---

<details>
<summary>Hint 1: Initialize Session State Safely</summary>

```python
import streamlit as st

# WRONG - resets every rerun
st.session_state.company = "Ace"

# CORRECT - only sets if not already present
if 'company' not in st.session_state:
    st.session_state.company = "Ace"
```

</details>

---

<details>
<summary>Hint 2: Link Dropdown to Session State</summary>

```python
# The key parameter syncs widget with session state automatically
st.selectbox(
    "Select Company",
    options=companies,
    key="company"  # Now st.session_state.company updates automatically
)
```

</details>

---

<details>
<summary>Hint 3: Read from Session State</summary>

```python
# After the selectbox, read the current value
selected = st.session_state.company

# Use it to fetch data
ratio = get_company_ratio(selected, "2024 Annual")
```

</details>

---

<details>
<summary>Hint 4: Full Solution</summary>

```python
# mini_dashboard.py - Exercise 2 (adds to Exercise 1)
import streamlit as st
from shared.airtable_connection import AirtableConnection

# === Functions from Exercise 1 ===
def get_company_ratio(company_name: str, period: str) -> float | None:
    airtable = AirtableConnection()
    data = airtable.get_balance_sheet_data_by_period(company_name, period)
    if data:
        return data[0].get('current_ratio')
    return None

def get_all_companies() -> list[str]:
    airtable = AirtableConnection()
    companies = airtable.get_companies_cached()
    return sorted([c['name'] for c in companies])

# === Exercise 2: Streamlit UI ===
st.title("Mini Company Dashboard")

# Get company list
companies = get_all_companies()

# Initialize session state (only runs once)
if 'company' not in st.session_state:
    st.session_state.company = companies[0]

# Dropdown linked to session state
st.selectbox("Select Company", options=companies, key="company")

# Fetch and display ratio
ratio = get_company_ratio(st.session_state.company, "2024 Annual")

if ratio:
    st.metric("Current Ratio", f"{ratio:.2f}")
else:
    st.warning("No data available")

# This button won't reset the dropdown!
if st.button("Refresh"):
    st.cache_data.clear()
    st.rerun()
```

Run: `streamlit run mini_dashboard.py`

</details>

---

## What You Added

- `st.session_state.company` persists the selection
- `key="company"` links the dropdown to session state
- Button clicks don't reset the dropdown

---

## Next

Continue to **[03_plotly_essentials.md](03_plotly_essentials.md)** to display the ratio as a gauge chart.
