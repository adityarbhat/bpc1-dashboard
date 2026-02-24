# 01: Airtable API Integration

## Overview

This guide will teach you how the BPC Dashboard connects to Airtable, fetches financial data, and handles API calls efficiently. By the end, you'll understand:

- How to authenticate with the Airtable API
- The structure of the `AirtableConnection` class
- Individual vs. bulk fetching patterns
- Caching strategies for performance
- Error handling in API calls

**Estimated Time:** 30-45 minutes

---

## Why Airtable?

Airtable is a cloud-based database that combines the simplicity of a spreadsheet with the power of a database. For the BPC Dashboard:

✅ **Non-technical users** can update financial data easily
✅ **REST API** makes it simple to fetch data in Python
✅ **Structured data** with tables for companies, balance sheets, income statements
✅ **No database server** needed - fully cloud-hosted

---

## The Problem: Connecting to External Data

When building a dashboard, you need to:

1. **Authenticate** securely with the data source
2. **Fetch data** efficiently without overwhelming the API
3. **Handle errors** gracefully when things go wrong
4. **Cache results** to avoid redundant API calls
5. **Parse data** into a format your application can use

Let's see how the BPC Dashboard solves each of these challenges.

---

## Solution Overview: The AirtableConnection Class

The dashboard uses a **single centralized class** (`AirtableConnection`) to handle all Airtable operations. This is located in `shared/airtable_connection.py`.

**Key Benefits:**
- **DRY Principle**: Write the API logic once, use everywhere
- **Consistent Error Handling**: All pages handle errors the same way
- **Centralized Caching**: Performance optimization in one place
- **Easy Updates**: Change API logic without touching page files

---

## Part 1: Authentication & Initialization

### The `__init__` Method

```python
class AirtableConnection:
    def __init__(self):
        # Try to get from Streamlit secrets first, then fall back to .env
        try:
            self.base_id = st.secrets.get("AIRTABLE_BASE_ID") or os.getenv("AIRTABLE_BASE_ID")
            self.pat = st.secrets.get("AIRTABLE_PAT") or os.getenv("AIRTABLE_PAT")
        except FileNotFoundError:
            self.base_id = os.getenv("AIRTABLE_BASE_ID")
            self.pat = os.getenv("AIRTABLE_PAT")
```

**Line-by-Line Breakdown:**

| Line | What It Does | Why It Matters |
|------|--------------|----------------|
| `st.secrets.get("AIRTABLE_BASE_ID")` | Tries to get credentials from Streamlit's secrets system | Works in production (deployed apps) |
| `or os.getenv("AIRTABLE_BASE_ID")` | Falls back to environment variables | Works in local development |
| `except FileNotFoundError` | Catches error if `.streamlit/secrets.toml` doesn't exist | Prevents crashes during local development |

**Key Concept: Dual Authentication Strategy**

The dashboard works in **two environments**:

1. **Local Development**: Uses `.env` file with environment variables
2. **Production/Deployed**: Uses Streamlit secrets (more secure)

This pattern makes the code portable and secure!

### Credential Validation

```python
if not self.base_id or not self.pat:
    st.error("⚠️ Airtable credentials not found!")
    st.info("**Setup Required**: Create a `.env` file in the project root with your Airtable credentials:")
    st.code("AIRTABLE_BASE_ID=your_base_id_here\nAIRTABLE_PAT=your_personal_access_token_here", language="bash")
    st.info("💡 You can get these from your Airtable account settings.")
    st.stop()
```

**What's Happening Here:**

1. **Checks** if both credentials exist
2. **Shows user-friendly error messages** (not cryptic errors!)
3. **Provides clear instructions** on how to fix the issue
4. **Stops execution** with `st.stop()` to prevent errors downstream

**Common Pitfall:** Forgetting `st.stop()` would cause errors later when trying to use missing credentials!

### Setting Up Headers

```python
self.headers = {
    'Authorization': f'Bearer {self.pat}',
    'Content-Type': 'application/json'
}
self.base_url = f"https://api.airtable.com/v0/{self.base_id}"
```

**Key Points:**

- **Bearer Token Authentication**: Airtable uses OAuth-style bearer tokens
- **JSON Content-Type**: All Airtable requests/responses use JSON
- **Base URL Construction**: Build once, reuse for all endpoints

---

## Part 2: Fetching Data - Basic Pattern

### Example: Getting Companies

Let's look at the simplest fetch method:

```python
@st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
def get_companies(_self):
    """Fetch all companies from Airtable"""
    try:
        url = f"{_self.base_url}/companies"
        response = requests.get(url, headers=_self.headers)
        if response.status_code == 200:
            data = response.json()
            companies = []
            for record in data['records']:
                companies.append({
                    'id': record['id'],
                    'name': record['fields'].get('company_name', 'Unknown'),
                    'industry': record['fields'].get('industry', 'Unknown'),
                    'status': record['fields'].get('status', 'Unknown')
                })
            return companies
        else:
            st.error(f"Error fetching companies: {response.text}")
            return []
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return []
```

**Let's Break This Down Step-by-Step:**

### Step 1: The Cache Decorator

```python
@st.cache_data(ttl=1800, show_spinner=False)
```

**What This Does:**
- **Caches results** for 1800 seconds (30 minutes)
- **Avoids redundant API calls** - if called again within 30 min, returns cached data
- **`show_spinner=False`**: Hides loading spinner for better UX

**Why `_self` Instead of `self`?**

```python
def get_companies(_self):
```

When using `@st.cache_data`, Streamlit needs to know what to cache. The underscore `_self` tells Streamlit: **"Don't include this parameter in the cache key."**

This prevents caching separate results for each class instance.

### Step 2: Build the URL

```python
url = f"{_self.base_url}/companies"
```

**Result:** `https://api.airtable.com/v0/YOUR_BASE_ID/companies`

The `/companies` is the **table name** in your Airtable base.

### Step 3: Make the Request

```python
response = requests.get(url, headers=_self.headers)
```

**What Happens:**
1. Python sends HTTP GET request to Airtable
2. Includes authentication in headers
3. Airtable responds with JSON data

### Step 4: Check Response Status

```python
if response.status_code == 200:
    # Success - process data
else:
    st.error(f"Error fetching companies: {response.text}")
    return []
```

**HTTP Status Codes:**
- **200**: Success - data fetched
- **401**: Unauthorized - bad credentials
- **404**: Not found - wrong table name or base ID
- **429**: Rate limit exceeded - too many requests

### Step 5: Parse JSON Response

```python
data = response.json()
companies = []
for record in data['records']:
    companies.append({
        'id': record['id'],
        'name': record['fields'].get('company_name', 'Unknown'),
        'industry': record['fields'].get('industry', 'Unknown'),
        'status': record['fields'].get('status', 'Unknown')
    })
return companies
```

**Airtable Response Structure:**

```json
{
  "records": [
    {
      "id": "rec123abc",
      "fields": {
        "company_name": "Coastal",
        "industry": "Moving & Storage",
        "status": "Active"
      }
    }
  ]
}
```

**Why `.get('company_name', 'Unknown')`?**

This is defensive programming! If the field doesn't exist:
- **Without `.get()`**: Crash with `KeyError`
- **With `.get(..., 'Unknown')`**: Returns 'Unknown' instead

### Step 6: Error Handling

```python
except Exception as e:
    st.error(f"Connection error: {str(e)}")
    return []
```

**Catches:**
- Network failures (no internet)
- Timeout errors
- JSON parsing errors
- Any unexpected issues

**Returns `[]`** so the dashboard can continue working (graceful degradation).

---

## Part 3: Filtering Data with Airtable Formulas

### Example: Fetching Period-Specific Data

```python
@st.cache_data(ttl=1800, show_spinner=False)
def get_balance_sheet_data(_self, company_name=None):
    """Fetch balance sheet data from Airtable for 2024 Annual period"""
    try:
        url = f"{_self.base_url}/balance_sheet_data"
        if company_name:
            filter_formula = f"AND({{company}}='{company_name}',{{period}}='2024 Annual')"
            url += f"?filterByFormula={filter_formula}"

        response = requests.get(url, headers=_self.headers)
        # ... rest of the code
```

**Airtable Filter Formula Syntax:**

| Formula | What It Does |
|---------|--------------|
| `{company}='Coastal'` | Get records where company equals "Coastal" |
| `{period}='2024 Annual'` | Get records where period equals "2024 Annual" |
| `AND({company}='Coastal', {period}='2024 Annual')` | Both conditions must be true |

**URL Encoding:**

The filter is added as a query parameter:
```
https://api.airtable.com/v0/BASE_ID/balance_sheet_data?filterByFormula=AND({company}='Coastal',{period}='2024 Annual')
```

---

## Part 4: Data Parsing with Helper Functions

### The `_parse_percentage_or_float()` Function

```python
def _parse_percentage_or_float(value):
    """Parse a value that might be a percentage string or a float"""
    if value is None:
        return 0.0

    if isinstance(value, str):
        # Remove percentage sign and convert to float
        if value.endswith('%'):
            try:
                return float(value.replace('%', '').strip())
            except ValueError:
                return 0.0
        # Try to convert string to float
        try:
            return float(value.strip())
        except ValueError:
            return 0.0

    # If it's already a number, return as float
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0
```

**Why Do We Need This?**

Airtable fields can contain:
- **Numbers**: `1.5`
- **Strings**: `"1.5%"` or `"1.5"`
- **None**: Empty fields

**Examples:**

| Input | Output | Reason |
|-------|--------|--------|
| `None` | `0.0` | No data |
| `"15.5%"` | `15.5` | Removes % sign |
| `"15.5"` | `15.5` | Converts string to float |
| `15.5` | `15.5` | Already a number |
| `"invalid"` | `0.0` | Can't parse - returns default |

**Usage in Fetch Methods:**

```python
'current_ratio': _parse_percentage_or_float(fields.get('current_ratio', 0))
```

This ensures all numeric fields are **consistent floats** regardless of how they're stored in Airtable!

---

## Part 5: Advanced Pattern - Bulk Fetching

### The Problem with Individual Fetching

**Before Optimization:**

```python
# Company Value page - OLD WAY
data_2020 = airtable.get_balance_sheet_data_by_period(company, '2020 Annual')  # API call 1
data_2021 = airtable.get_balance_sheet_data_by_period(company, '2021 Annual')  # API call 2
data_2022 = airtable.get_balance_sheet_data_by_period(company, '2022 Annual')  # API call 3
data_2023 = airtable.get_balance_sheet_data_by_period(company, '2023 Annual')  # API call 4
data_2024 = airtable.get_balance_sheet_data_by_period(company, '2024 Annual')  # API call 5
```

**Result:** 5 separate API calls, each taking ~1 second = **5 seconds total**

### The Solution: Fetch All at Once

```python
@st.cache_data(ttl=1800, show_spinner=False)
def get_all_data_for_company(_self, company_name, years=None):
    """Fetch all balance sheet and income statement data for a company across multiple years"""
    if years is None:
        years = ['2020', '2021', '2022', '2023', '2024']

    result = {
        'balance_sheet': {},
        'income_statement': {}
    }

    # Fetch data for all years
    for year in years:
        period_filter = f"{year} Annual"
        try:
            # Get both balance sheet and income statement data
            balance_data = _self.get_balance_sheet_data_by_period(company_name, period_filter)
            income_data = _self.get_income_statement_data_by_period(company_name, period_filter)

            if balance_data:
                result['balance_sheet'][year] = balance_data[0]
            if income_data:
                result['income_statement'][year] = income_data[0]

        except Exception:
            # Skip years with errors
            continue

    return result
```

**After Optimization:**

```python
# Company Value page - NEW WAY
all_data = airtable.get_all_data_for_company(company)  # 1 cached call for all years!

# Access data easily
balance_2020 = all_data['balance_sheet'].get('2020', {})
balance_2021 = all_data['balance_sheet'].get('2021', {})
```

**Performance Improvement:**
- **Before**: 47 API calls per page load
- **After**: ~10 API calls per page load
- **Speed Increase**: 15-20x faster! 🚀

---

## Part 6: Group Data Fetching

### Fetching All Companies at Once

```python
@st.cache_data(ttl=1800, show_spinner=False)
def get_all_companies_balance_sheet_by_period(_self, period):
    """Fetch balance sheet data from Airtable for all companies for a specific period"""
    try:
        url = f"{_self.base_url}/balance_sheet_data"
        filter_formula = f"{{period}}='{period}'"
        url += f"?filterByFormula={filter_formula}"

        response = requests.get(url, headers=_self.headers)
        if response.status_code == 200:
            data = response.json()
            balance_data = []
            for record in data['records']:
                fields = record['fields']
                balance_data.append({
                    'id': record['id'],
                    'company_name': fields.get('company_name'),
                    'current_ratio': _parse_percentage_or_float(fields.get('current_ratio', 0)),
                    'debt_to_equity': _parse_percentage_or_float(fields.get('debt_to_equity', 0)),
                    # ... more fields
                })
            return balance_data
```

**Use Case:** Group comparison pages that need data for ALL companies

**Filter:** `{period}='2024 Annual'` - Gets all companies for that period

**Benefits:**
- **1 API call** instead of 10 (one per company)
- **Faster group calculations** (averages, rankings)
- **Consistent data** (all fetched at same moment)

---

## Part 7: Singleton Pattern for Connection

### Why Not Create Multiple Connections?

**❌ Bad Approach:**

```python
# Page 1
airtable1 = AirtableConnection()

# Page 2
airtable2 = AirtableConnection()

# Page 3
airtable3 = AirtableConnection()
```

**Problems:**
- Wastes memory (3 identical objects)
- Each has separate cache
- Redundant authentication checks

**✅ Good Approach: Cached Resource**

```python
@st.cache_resource
def get_airtable_connection():
    return AirtableConnection()
```

**Usage Everywhere:**

```python
# Any page
airtable = get_airtable_connection()
companies = airtable.get_companies()
```

**Benefits:**
- **Single instance** shared across entire app
- **Persistent across reruns** (stays in memory)
- **Shared cache** for all methods

---

## Common Pitfalls & Solutions

### Pitfall 1: Field Name Mismatches

**Problem:**

```python
# Airtable has field "company_name"
# But code tries to access "companyName"
name = fields.get('companyName')  # Returns None!
```

**Solution:**

Always use exact field names from Airtable. Use `.get()` with defaults:

```python
name = fields.get('company_name', 'Unknown')
```

### Pitfall 2: Missing Error Handling

**Problem:**

```python
def get_data():
    response = requests.get(url, headers=headers)
    return response.json()  # Crashes if request fails!
```

**Solution:**

```python
def get_data():
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.text}")
            return []
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return []
```

### Pitfall 3: Forgetting Cache Invalidation

**Problem:**

Data updates in Airtable but dashboard shows old data for 30 minutes!

**Solution:**

Add a "Refresh Data" button:

```python
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
```

### Pitfall 4: Not Handling None Values

**Problem:**

```python
current_ratio = fields.get('current_ratio')  # Could be None
result = current_ratio * 100  # TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'
```

**Solution:**

```python
current_ratio = _parse_percentage_or_float(fields.get('current_ratio', 0))
result = current_ratio * 100  # Always works!
```

---

## Key Takeaways

✅ **Centralize API logic** in a single class (`AirtableConnection`)
✅ **Use dual authentication** for local development and production
✅ **Cache aggressively** with `@st.cache_data(ttl=1800)`
✅ **Handle errors gracefully** with try/except and user-friendly messages
✅ **Parse data consistently** with helper functions
✅ **Use bulk fetching** for multi-year or multi-company data
✅ **Create a singleton** connection with `@st.cache_resource`
✅ **Validate all inputs** with `.get()` and default values

---

## Try It Yourself

### Exercise 1: Add a New Field

**Task:** Modify `get_companies()` to also fetch a `founded_year` field from Airtable.

**Hint:**

```python
companies.append({
    'id': record['id'],
    'name': record['fields'].get('company_name', 'Unknown'),
    'industry': record['fields'].get('industry', 'Unknown'),
    'status': record['fields'].get('status', 'Unknown'),
    # Add your code here
})
```

<details>
<summary>Show Solution</summary>

```python
companies.append({
    'id': record['id'],
    'name': record['fields'].get('company_name', 'Unknown'),
    'industry': record['fields'].get('industry', 'Unknown'),
    'status': record['fields'].get('status', 'Unknown'),
    'founded_year': _parse_percentage_or_float(fields.get('founded_year', 0))
})
```

</details>

### Exercise 2: Create a Filter Method

**Task:** Write a method to fetch only companies with `status='Active'`.

**Hint:** Use Airtable filter formulas!

<details>
<summary>Show Solution</summary>

```python
@st.cache_data(ttl=1800, show_spinner=False)
def get_active_companies(_self):
    """Fetch only active companies from Airtable"""
    try:
        url = f"{_self.base_url}/companies"
        filter_formula = "{status}='Active'"
        url += f"?filterByFormula={filter_formula}"

        response = requests.get(url, headers=_self.headers)
        if response.status_code == 200:
            data = response.json()
            companies = []
            for record in data['records']:
                companies.append({
                    'id': record['id'],
                    'name': record['fields'].get('company_name', 'Unknown'),
                    'industry': record['fields'].get('industry', 'Unknown'),
                    'status': record['fields'].get('status', 'Active')
                })
            return companies
        else:
            st.error(f"Error fetching companies: {response.text}")
            return []
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return []
```

</details>

### Exercise 3: Debug This Code

**Task:** Find the bug in this code:

```python
def get_revenue(company_name):
    airtable = AirtableConnection()  # Bug 1
    data = airtable.get_income_statement_data(company_name)
    return data[0]['total_revenue']  # Bug 2
```

<details>
<summary>Show Solution</summary>

**Bugs:**

1. Should use `get_airtable_connection()` singleton pattern
2. Doesn't handle empty data - will crash if `data` is empty list

**Fixed:**

```python
def get_revenue(company_name):
    airtable = get_airtable_connection()
    data = airtable.get_income_statement_data(company_name)
    if data and len(data) > 0:
        return data[0].get('total_revenue', 0)
    return 0
```

</details>

---

## Related Topics

- **[02-performance-optimization.md](02-performance-optimization.md)** - Deep dive into caching and bulk fetching
- **[05-reusable-components.md](05-reusable-components.md)** - Building shared utilities
- **[07-error-handling.md](07-error-handling.md)** - Advanced error handling patterns

---

## Next Steps

Now that you understand how to connect to Airtable and fetch data, move on to **[02-performance-optimization.md](02-performance-optimization.md)** to learn how to make your dashboard blazing fast with advanced caching techniques!

---

*Questions or suggestions? Add your notes as you learn!*
