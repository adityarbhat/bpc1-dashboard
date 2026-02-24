# 07: Error Handling & User Experience

## Overview

Learn how the BPC Dashboard handles errors gracefully to provide a robust user experience. This guide covers defensive programming, error recovery, and user-friendly messaging. You'll understand:

- Try-except patterns in Python
- Graceful degradation strategies
- User-friendly error messages
- Data validation before processing
- Handling API failures
- Fallback mechanisms

**Estimated Time:** 25-30 minutes

---

## Why Error Handling Matters

### Bad UX: Crash on Error

```python
# User clicks button
data = airtable.get_companies()
first_company = data[0]  # KeyError if data is empty!
# App crashes 💥
```

### Good UX: Graceful Error Handling

```python
try:
    data = airtable.get_companies()
    if data and len(data) > 0:
        first_company = data[0]
    else:
        st.warning("No companies found. Please add data.")
        first_company = None
except Exception as e:
    st.error(f"Error loading companies: {str(e)}")
    first_company = None
```

**Result:** App continues working, user gets helpful feedback!

---

## Try-Except Patterns

### Basic Pattern

```python
try:
    # Code that might fail
    result = risky_operation()
except Exception as e:
    # Handle error
    st.error(f"Error: {str(e)}")
    result = None  # Provide fallback
```

### Specific Exception Handling

```python
try:
    data = airtable.get_data()
except requests.exceptions.Timeout:
    st.error("Request timed out. Please try again.")
except requests.exceptions.ConnectionError:
    st.error("Network error. Check your internet connection.")
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")
```

### BPC Dashboard Pattern

```python
# From airtable_connection.py
def get_companies(_self):
    try:
        url = f"{_self.base_url}/companies"
        response = requests.get(url, headers=_self.headers)

        if response.status_code == 200:
            data = response.json()
            # Process data
            return companies
        else:
            st.error(f"Error fetching companies: {response.text}")
            return []  # Empty list fallback

    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return []  # Empty list fallback
```

**Key Points:**
- Returns empty list (not None) for consistency
- User gets specific error message
- App continues running

---

## User-Friendly Error Messages

### Bad Messages

```python
❌ st.error("Error")  # Too vague
❌ st.error("KeyError: 'company_name'")  # Too technical
❌ st.error(str(e))  # Raw exception text
```

### Good Messages

```python
✅ st.error("⚠️ No companies found in database")
✅ st.info("💡 Please upload company data to continue")
✅ st.warning("Unable to load balance sheet data. Using cached version.")
```

### Message Types

```python
# Error - Something went wrong
st.error("⚠️ Failed to connect to database")

# Warning - Proceed with caution
st.warning("⚠️ Some data may be outdated")

# Info - Helpful information
st.info("💡 Tip: Upload data in Excel format")

# Success - Operation completed
st.success("✅ Data uploaded successfully!")
```

---

## Validation Before Processing

### Checking Data Exists

```python
# BAD - Assumes data exists
total = data[0]['total_revenue']  # Crashes if empty!

# GOOD - Validates first
if data and len(data) > 0:
    total = data[0].get('total_revenue', 0)
else:
    st.warning("No revenue data available")
    total = 0
```

### Type Validation

```python
def calculate_ratio(numerator, denominator):
    """Calculate ratio with validation"""
    # Validate types
    if not isinstance(numerator, (int, float)):
        st.error("Invalid numerator type")
        return 0

    if not isinstance(denominator, (int, float)):
        st.error("Invalid denominator type")
        return 0

    # Validate values
    if denominator == 0:
        st.warning("Cannot divide by zero")
        return 0

    return numerator / denominator
```

---

## Graceful Degradation

### Fallback to Defaults

```python
# Try to get from session state, fallback to default
period = st.session_state.get('period', 'year_end')
company = st.session_state.get('selected_company', 'Coastal')
```

### Fallback to Cached Data

```python
try:
    # Try fresh fetch
    data = airtable.get_fresh_data()
except Exception:
    # Fall back to cached
    data = load_from_cache()
    st.warning("Using cached data (fresh data unavailable)")
```

### Fallback to Static Data

```python
# From group overview page - static rankings
try:
    rankings = calculate_dynamic_rankings()
except Exception:
    # Use static hardcoded rankings
    rankings = STATIC_RANKINGS
    st.info("Showing static rankings")
```

---

## Handling API Failures

### Retry Logic

```python
def fetch_with_retry(url, max_retries=3):
    """Fetch data with automatic retry"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                st.warning(f"Timeout. Retrying... (Attempt {attempt + 1}/{max_retries})")
                continue
            else:
                st.error("Maximum retries reached. Please try again later.")
                return None
```

### Timeout Handling

```python
try:
    response = requests.get(url, timeout=30)  # 30 second timeout
except requests.exceptions.Timeout:
    st.error("Request timed out after 30 seconds")
    return []
```

---

## Data Validation Patterns

### Safe Dictionary Access

```python
# BAD
value = data['field_name']  # KeyError if missing!

# GOOD
value = data.get('field_name', 0)  # Returns 0 if missing
```

### Safe List Access

```python
# BAD
first_item = items[0]  # IndexError if empty!

# GOOD
first_item = items[0] if items else None
```

### Safe Number Operations

```python
# BAD
ratio = a / b  # ZeroDivisionError if b is 0!

# GOOD
ratio = a / b if b != 0 else 0
```

---

## Defensive Programming

### The `.get()` Pattern

```python
# Chained .get() for nested data
value = record.get('fields', {}).get('company_name', 'Unknown')
#                            ^^                      ^^^^^^^^^
#                            Default empty dict      Default value
```

### The `or` Pattern

```python
# Handle None values
value = record.get('amount', 0) or 0
#                                ^^^
#                                If None, use 0
```

### Early Returns

```python
def process_data(data):
    # Validate early, return early
    if not data:
        return None

    if len(data) == 0:
        return None

    # Only process if data is valid
    return transform(data)
```

---

## User Guidance

### Helpful Instructions

```python
if not data:
    st.info("⚠️ No data found")
    st.info("**Setup Required**: Upload financial data")
    st.code("File → Upload Data → Select Excel file", language="text")
    st.info("💡 Sample files available in documentation")
    st.stop()  # Prevent further execution
```

### Progressive Disclosure

```python
with st.expander("Troubleshooting"):
    st.markdown("""
    **Common Issues:**

    1. No companies showing?
       - Check Airtable connection
       - Verify companies table exists

    2. Missing data?
       - Upload data for selected period
       - Check date formats

    3. Slow performance?
       - Click 'Refresh Data' button
       - Check internet connection
    """)
```

---

## Common Error Scenarios

### 1. Missing Credentials

```python
if not self.base_id or not self.pat:
    st.error("⚠️ Airtable credentials not found!")
    st.info("**Setup Required**: Create `.env` file")
    st.code("AIRTABLE_BASE_ID=your_id\nAIRTABLE_PAT=your_token")
    st.stop()
```

### 2. Empty Data Response

```python
if not balance_data:
    st.info(f"⚠️ No data found for {company} in {period}")
    st.info("💡 Data may not be uploaded yet")
    return
```

### 3. Invalid Data Types

```python
try:
    percentage = float(value)
except (ValueError, TypeError):
    st.warning(f"Invalid percentage value: {value}")
    percentage = 0.0
```

---

## Key Takeaways

✅ **Always use try-except** for risky operations
✅ **Provide fallback values** (empty list, 0, None)
✅ **Show user-friendly messages** with icons and context
✅ **Validate before processing** (check types, ranges)
✅ **Use `.get()` with defaults** for dictionaries
✅ **Return early** on invalid input
✅ **Provide helpful guidance** when errors occur
✅ **Graceful degradation** better than crashes

---

## Try It Yourself

### Exercise: Add Error Handling

**Task:** Add complete error handling to this function

```python
def get_company_revenue(company_name):
    data = airtable.get_income_statement_data(company_name)
    return data[0]['total_revenue']
```

<details>
<summary>Show Solution</summary>

```python
def get_company_revenue(company_name):
    """
    Get company revenue with full error handling

    Args:
        company_name (str): Company name

    Returns:
        float: Revenue amount or 0 if error
    """
    # Validate input
    if not company_name:
        st.warning("No company name provided")
        return 0

    try:
        # Attempt to fetch data
        data = airtable.get_income_statement_data(company_name)

        # Validate response
        if not data:
            st.info(f"No data found for {company_name}")
            return 0

        if len(data) == 0:
            st.info(f"Empty data set for {company_name}")
            return 0

        # Safely get revenue
        revenue = data[0].get('total_revenue', 0) or 0

        # Validate revenue value
        if not isinstance(revenue, (int, float)):
            st.warning(f"Invalid revenue type for {company_name}")
            return 0

        return revenue

    except Exception as e:
        st.error(f"Error fetching revenue for {company_name}: {str(e)}")
        return 0
```

</details>

---

## Related Topics

- **[01-airtable-integration.md](01-airtable-integration.md)** - Error handling in API calls
- **[06-data-transformation.md](06-data-transformation.md)** - Validating transformed data

---

## Next Steps

Move on to the **[feature-deep-dives/](feature-deep-dives/)** folder for advanced implementation examples!

---

*Remember: The best error message is one the user never sees - validate early, handle gracefully! 🛡️*
