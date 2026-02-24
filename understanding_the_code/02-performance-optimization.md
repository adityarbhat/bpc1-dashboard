# 02: Performance Optimization

## Overview

Learn how the BPC Dashboard went from slow and sluggish to lightning-fast through smart caching and bulk fetching strategies. By the end, you'll understand:

- Why performance matters for user experience
- Streamlit's caching decorators (`@st.cache_data` and `@st.cache_resource`)
- TTL (Time-To-Live) decisions and trade-offs
- The bulk fetching optimization that achieved 15-20x speed improvement
- Memory management in Streamlit apps
- When to optimize and when not to

**Estimated Time:** 45-60 minutes

---

## The Performance Problem

### Initial Dashboard Performance (Before Optimization)

When the dashboard was first built, loading a single page took **10-20 seconds**. Here's what was happening:

**Company Value Page - Before Optimization:**

```python
# Fetching balance sheet data for 5 years
data_2020 = airtable.get_balance_sheet_data_by_period(company, '2020 Annual')  # 2 seconds
data_2021 = airtable.get_balance_sheet_data_by_period(company, '2021 Annual')  # 2 seconds
data_2022 = airtable.get_balance_sheet_data_by_period(company, '2022 Annual')  # 2 seconds
data_2023 = airtable.get_balance_sheet_data_by_period(company, '2023 Annual')  # 2 seconds
data_2024 = airtable.get_balance_sheet_data_by_period(company, '2024 Annual')  # 2 seconds

# Fetching income statement data for 5 years
income_2020 = airtable.get_income_statement_data_by_period(company, '2020 Annual')  # 2 seconds
income_2021 = airtable.get_income_statement_data_by_period(company, '2021 Annual')  # 2 seconds
income_2022 = airtable.get_income_statement_data_by_period(company, '2022 Annual')  # 2 seconds
income_2023 = airtable.get_income_statement_data_by_period(company, '2023 Annual')  # 2 seconds
income_2024 = airtable.get_income_statement_data_by_period(company, '2024 Annual')  # 2 seconds

# Total: 10 API calls × 2 seconds = 20 seconds! 😱
```

**User Experience:**
- Users waited 20 seconds staring at loading spinners
- Every navigation to the page triggered another 20 seconds
- Dashboard felt unresponsive and "broken"

**Root Causes:**
1. **Too many individual API calls** (10+ per page)
2. **No caching** - same data fetched on every rerun
3. **Sequential fetching** - waiting for each call to complete
4. **Repeated data requests** - fetching same data multiple times

---

## Solution 1: Streamlit Caching

### Understanding Streamlit's Execution Model

**Key Concept:** Streamlit reruns your entire script on every interaction!

```python
# Every time user clicks a button or changes a dropdown:
# Line 1 runs
# Line 2 runs
# Line 3 runs
# ... entire script runs again!
```

**Without Caching:**

```python
def expensive_function():
    time.sleep(5)  # Simulate slow API call
    return "data"

# This runs EVERY TIME the page reruns! 😱
data = expensive_function()
```

**With Caching:**

```python
@st.cache_data
def expensive_function():
    time.sleep(5)  # Only runs once!
    return "data"

# First run: Takes 5 seconds
# Subsequent runs: Returns cached result instantly! 🚀
data = expensive_function()
```

### The Two Types of Caching

#### 1. `@st.cache_data` - For Data

**Use for:** API calls, data transformations, calculations

```python
@st.cache_data(ttl=1800, show_spinner=False)
def get_companies(_self):
    """Returns a list/dict - cache the data"""
    # Fetch from API
    return companies_list
```

**Key Features:**
- Caches the **data returned** (lists, dicts, DataFrames)
- Creates a **copy** each time (prevents mutation issues)
- Automatic **serialization** for storage
- TTL support for auto-expiration

#### 2. `@st.cache_resource` - For Objects

**Use for:** Database connections, model instances, expensive objects

```python
@st.cache_resource
def get_airtable_connection():
    """Returns a connection object - cache the resource"""
    return AirtableConnection()
```

**Key Features:**
- Caches the **actual object** (not a copy)
- Returns **same instance** every time
- No serialization needed
- Persists across all users and sessions

### Cache Key Mechanism

**How Streamlit Decides What to Cache:**

```python
@st.cache_data
def fetch_data(company_name, year):
    # API call here
    return data

# These create different cache entries:
fetch_data("Coastal", 2024)  # Cache key: ("Coastal", 2024)
fetch_data("Coastal", 2023)  # Cache key: ("Coastal", 2023)
fetch_data("Ace", 2024)      # Cache key: ("Ace", 2024)
```

**Cache Key = Function Name + All Parameter Values**

### The Underscore Convention: `_self`

**Problem:**

```python
class AirtableConnection:
    @st.cache_data
    def get_companies(self):  # 'self' changes with each instance!
        return data

# Two instances create separate caches (wasteful!)
conn1 = AirtableConnection()
conn2 = AirtableConnection()
```

**Solution:**

```python
class AirtableConnection:
    @st.cache_data
    def get_companies(_self):  # Underscore excludes from cache key
        return data

# All instances share the same cache! 🎯
conn1 = AirtableConnection()
conn2 = AirtableConnection()
```

**The underscore tells Streamlit:** "Ignore this parameter when creating cache keys."

---

## Solution 2: TTL (Time-To-Live) Strategy

### What is TTL?

**TTL** = How long cached data stays valid before being refreshed

```python
@st.cache_data(ttl=1800)  # Cache expires after 1800 seconds (30 minutes)
def get_data():
    return fetch_from_api()
```

**Timeline:**

```
Time 0:00  → Function runs, result cached
Time 0:01  → Returns cached result (no API call)
Time 15:00 → Returns cached result (no API call)
Time 29:59 → Returns cached result (no API call)
Time 30:00 → Cache expired! Function runs again
Time 30:01 → Returns new cached result
```

### Choosing the Right TTL

The BPC Dashboard uses **30 minutes (1800 seconds)**. Here's why:

**Considerations:**

| Factor | Impact on TTL |
|--------|---------------|
| **Data Update Frequency** | Financial data changes monthly/quarterly → Longer TTL OK |
| **User Tolerance** | Users OK with 30-min-old data → Longer TTL OK |
| **API Rate Limits** | Airtable has request limits → Longer TTL safer |
| **Memory Usage** | Longer TTL = more memory → 30 min is balanced |

**Different TTL Strategies:**

```python
# Real-time stock prices - short TTL
@st.cache_data(ttl=60)  # 1 minute
def get_stock_price():
    return fetch_price()

# Historical financial data - long TTL
@st.cache_data(ttl=3600)  # 1 hour
def get_historical_data():
    return fetch_data()

# Static reference data - no expiration
@st.cache_data()  # Never expires automatically
def get_company_list():
    return fetch_companies()
```

**BPC Dashboard TTL:**

```python
@st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes
```

**Why 30 minutes?**
- Data doesn't change during a typical user session
- Balances freshness with performance
- Reduces API calls by 95%+
- Users can manually refresh if needed

### Manual Cache Clearing

```python
# Add a refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
```

**When to use:**
- User uploads new data
- User reports stale information
- Testing new features

---

## Solution 3: Bulk Fetching Pattern

### The Problem: N+1 Queries

**Company Actuals Page - Before Optimization:**

```python
# Fetching data year by year (N+1 query problem)
for year in ['2020', '2021', '2022', '2023', '2024']:
    balance_data = airtable.get_balance_sheet_data_by_period(company, f'{year} Annual')
    income_data = airtable.get_income_statement_data_by_period(company, f'{year} Annual')
    # Process each year...

# Result: 10 separate API calls (5 balance + 5 income)
```

**Performance:**
- 10 API calls × 2 seconds each = **20 seconds** 😱
- Each call has network overhead
- User sees multiple loading spinners

### The Solution: Fetch All at Once

**Create a Bulk Fetch Method:**

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

    # Fetch data for all years in one loop
    for year in years:
        period_filter = f"{year} Annual"
        try:
            # These are already cached individually!
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

**How It Works:**

1. **First Call (Cache Miss):**
   ```
   User requests data → Function runs → Makes 10 API calls → Caches result → Returns data
   Time: ~20 seconds
   ```

2. **Second Call (Cache Hit):**
   ```
   User requests same data → Returns cached result instantly
   Time: ~0.01 seconds! 🚀
   ```

3. **Different Company (Partial Cache Hit):**
   ```
   User switches to another company → New cache key → Individual fetches use their own cache
   Time: ~2 seconds (much better than 20!)
   ```

### Using the Bulk Fetch Method

**Before:**

```python
# Company Value Page - OLD
balance_2020 = airtable.get_balance_sheet_data_by_period(company, '2020 Annual')
balance_2021 = airtable.get_balance_sheet_data_by_period(company, '2021 Annual')
balance_2022 = airtable.get_balance_sheet_data_by_period(company, '2022 Annual')
balance_2023 = airtable.get_balance_sheet_data_by_period(company, '2023 Annual')
balance_2024 = airtable.get_balance_sheet_data_by_period(company, '2024 Annual')

income_2020 = airtable.get_income_statement_data_by_period(company, '2020 Annual')
income_2021 = airtable.get_income_statement_data_by_period(company, '2021 Annual')
income_2022 = airtable.get_income_statement_data_by_period(company, '2022 Annual')
income_2023 = airtable.get_income_statement_data_by_period(company, '2023 Annual')
income_2024 = airtable.get_income_statement_data_by_period(company, '2024 Annual')
```

**After:**

```python
# Company Value Page - NEW
all_data = airtable.get_all_data_for_company(company)

# Access data easily
balance_2020 = all_data['balance_sheet'].get('2020', {})
balance_2021 = all_data['balance_sheet'].get('2021', {})
balance_2022 = all_data['balance_sheet'].get('2022', {})
balance_2023 = all_data['balance_sheet'].get('2023', {})
balance_2024 = all_data['balance_sheet'].get('2024', {})

income_2020 = all_data['income_statement'].get('2020', {})
income_2021 = all_data['income_statement'].get('2021', {})
income_2022 = all_data['income_statement'].get('2022', {})
income_2023 = all_data['income_statement'].get('2023', {})
income_2024 = all_data['income_statement'].get('2024', {})
```

**Benefits:**

✅ **Single cache entry** for all data
✅ **Cleaner code** - one function call
✅ **Better error handling** - try/except in one place
✅ **Easy to extend** - add more years by changing list

---

## Solution 4: Group Data Optimization

### Fetching All Companies at Once

**Group Ratios Page - Before:**

```python
# Fetch each company's data separately
for company in companies:
    data = airtable.get_balance_sheet_data_by_period(company['name'], '2024 Annual')
    # Process...

# Result: 10 companies × 1 call each = 10 API calls
```

**Group Ratios Page - After:**

```python
# Fetch all companies in one call
@st.cache_data(ttl=1800, show_spinner=False)
def get_all_companies_balance_sheet_by_period(_self, period):
    """Fetch balance sheet data for ALL companies for a specific period"""
    url = f"{_self.base_url}/balance_sheet_data"
    filter_formula = f"{{period}}='{period}'"
    url += f"?filterByFormula={filter_formula}"

    response = requests.get(url, headers=_self.headers)
    # Returns all companies' data in one response!
    return process_all_records(response)

# Usage
all_data = airtable.get_all_companies_balance_sheet_by_period('2024 Annual')

# Filter by company
for company_data in all_data:
    if company_data['company_name'] == 'Coastal':
        # Process Coastal's data
```

**Performance:**
- **Before**: 10 API calls (one per company)
- **After**: 1 API call (all companies)
- **Improvement**: 10x faster! 🚀

**Trade-off:**
- **Memory**: Loads all companies' data (but still small ~100KB)
- **Speed**: Much faster initial load
- **Cache Efficiency**: All companies cached together

---

## Real-World Performance Metrics

### Before vs After Comparison

| Page | Before Optimization | After Optimization | Improvement |
|------|--------------------|--------------------|-------------|
| **Company Value** | 10-20 seconds (47 API calls) | 1-2 seconds (10 calls, cached) | **15-20x faster** |
| **Company Actuals** | 15 seconds (47 API calls) | 2-3 seconds (10 calls, cached) | **5-7x faster** |
| **Company Income Statement** | 12 seconds (42 calls) | 2 seconds (10 calls) | **6x faster** |
| **Group Ratios** | 8 seconds (10 calls) | 1 second (1 call) | **8x faster** |

### Caching Impact Timeline

```
User Session Timeline:

00:00 - User opens Company Value page for "Coastal"
        → 10 API calls (first load)
        → Takes 2 seconds

00:05 - User clicks to Company Actuals page
        → 0 API calls (uses cached data)
        → Instant load! 🚀

00:10 - User returns to Company Value page
        → 0 API calls (still cached)
        → Instant load! 🚀

15:00 - User switches to "Ace" company
        → 10 API calls (new company, cache miss)
        → Takes 2 seconds

30:00 - Cache expires for "Coastal" data
        → Next request will refresh cache
```

**Key Insight:** After the first page load, most navigation is **instant** due to caching!

---

## Memory Management

### Understanding Memory Usage

**What Gets Stored in Memory:**

1. **Cached Data** - Results from `@st.cache_data`
2. **Session State** - User-specific data in `st.session_state`
3. **Resource Objects** - Connections from `@st.cache_resource`

**BPC Dashboard Memory Profile:**

```
Cached Data (per 30-min window):
- Company data: ~5 KB
- Balance sheet (5 years, 1 company): ~50 KB
- Income statement (5 years, 1 company): ~50 KB
- Group data (all companies): ~200 KB

Total per user session: ~300-500 KB

For 10 concurrent users: ~5 MB
For 100 concurrent users: ~50 MB
```

**Conclusion:** Memory usage is **minimal** - modern servers handle this easily!

### Cache Eviction Strategy

Streamlit automatically manages cache:

1. **TTL Expiration** - Removes entries after TTL
2. **Memory Pressure** - Evicts LRU (Least Recently Used) if memory fills
3. **Manual Clear** - `st.cache_data.clear()`

---

## Advanced Optimization Techniques

### 1. Lazy Loading

**Concept:** Only load data when needed

**Example:**

```python
# Don't do this - loads all data upfront
all_companies_data = load_all_companies()

# Do this - load on demand
if user_selects_company:
    company_data = load_company_data(selected_company)
```

### 2. Progressive Loading

**Show data as it arrives:**

```python
with st.spinner("Loading balance sheet..."):
    balance_data = fetch_balance_sheet()
st.dataframe(balance_data)  # Show immediately

with st.spinner("Loading income statement..."):
    income_data = fetch_income_statement()
st.dataframe(income_data)  # Show as soon as ready
```

### 3. Background Data Prefetching

**Prefetch likely next requests:**

```python
# User is viewing 2024 data
current_data = fetch_data('2024 Annual')

# Prefetch 2023 in background (user might click "Previous Year")
@st.cache_data
def prefetch_previous_year():
    return fetch_data('2023 Annual')

# This runs and caches the result
prefetch_previous_year()
```

### 4. Selective Field Fetching

**Only fetch fields you need:**

```python
# Bad - fetches all 50 fields
data = airtable.get_all_fields(company)

# Good - only fetches needed fields
data = airtable.get_specific_fields(company, fields=['revenue', 'profit'])
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Over-Caching

**Problem:**

```python
@st.cache_data  # No TTL - never expires!
def get_live_stock_price():
    return fetch_current_price()

# Shows outdated price forever!
```

**Solution:**

```python
@st.cache_data(ttl=60)  # Expires every minute
def get_live_stock_price():
    return fetch_current_price()
```

**Rule:** Always set TTL for data that changes!

### Pitfall 2: Caching Mutable Objects

**Problem:**

```python
@st.cache_data
def get_data():
    return {"value": 10}

data = get_data()
data["value"] = 20  # Modifies cached data! 😱

# Next call returns modified data!
data2 = get_data()  # {"value": 20} instead of {"value": 10}
```

**Solution:** `@st.cache_data` automatically creates copies (this is safe!)

But with `@st.cache_resource`, be careful:

```python
@st.cache_resource
def get_connection():
    return DatabaseConnection()

conn = get_connection()
conn.close()  # Don't do this - affects all users! 😱
```

### Pitfall 3: Cache Key Collisions

**Problem:**

```python
@st.cache_data
def fetch_data(company, period):
    return data

# These have DIFFERENT cache keys (good!)
fetch_data("Coastal", "2024 Annual")
fetch_data("Coastal", "2023 Annual")

# But watch out for this:
fetch_data(company="Coastal", period="2024 Annual")  # Cache key 1
fetch_data("Coastal", "2024 Annual")                 # Cache key 2 (different!)
```

**Solution:** Be consistent with parameter passing (positional vs keyword)

### Pitfall 4: Ignoring Cache Warm-up

**Problem:**

First user waits 20 seconds, next users get instant load.

**Solution:** Pre-warm cache on app startup:

```python
# In main app file
@st.cache_data
def warm_up_cache():
    """Prefetch common data on app start"""
    airtable = get_airtable_connection()
    airtable.get_companies()
    airtable.get_all_companies_balance_sheet_by_period('2024 Annual')
    airtable.get_all_companies_income_statement_by_period('2024 Annual')

# Run once when app starts
warm_up_cache()
```

---

## Monitoring Performance

### Built-in Performance Tracking

Streamlit provides performance metrics:

```python
# Enable in .streamlit/config.toml
[server]
enableStaticServing = true
enableXsrfProtection = true

# View in browser console:
# - Cache hit rates
# - Function execution times
# - Memory usage
```

### Custom Performance Logging

```python
import time

def log_performance(func_name):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        st.write(f"⏱️ {func_name} took {elapsed:.2f}s")
        return result
    return wrapper

@log_performance("fetch_company_data")
@st.cache_data(ttl=1800)
def fetch_company_data(company):
    return airtable.get_data(company)
```

---

## Key Takeaways

✅ **Cache everything** that's expensive to compute
✅ **Use `@st.cache_data`** for data, `@st.cache_resource` for connections
✅ **Set appropriate TTL** based on data update frequency
✅ **Bulk fetch** when loading multiple related records
✅ **Use `_self`** in class methods to share cache across instances
✅ **Monitor performance** and iterate on optimization
✅ **Balance** memory usage vs speed gains
✅ **Provide manual refresh** for users who need latest data

**Performance Formula:**

```
Fast App = Smart Caching + Bulk Fetching + Appropriate TTL
```

---

## Try It Yourself

### Exercise 1: Add Caching to a Function

**Task:** Add caching with 10-minute TTL to this function:

```python
def get_company_revenue(company_name):
    airtable = get_airtable_connection()
    data = airtable.get_income_statement_data(company_name)
    if data:
        return data[0].get('total_revenue', 0)
    return 0
```

<details>
<summary>Show Solution</summary>

```python
@st.cache_data(ttl=600, show_spinner=False)  # 600 seconds = 10 minutes
def get_company_revenue(company_name):
    airtable = get_airtable_connection()
    data = airtable.get_income_statement_data(company_name)
    if data:
        return data[0].get('total_revenue', 0)
    return 0
```

</details>

### Exercise 2: Create a Bulk Fetch Method

**Task:** Write a method to fetch balance sheet data for multiple companies at once.

**Hint:** Similar to `get_all_data_for_company` but for multiple companies, single year.

<details>
<summary>Show Solution</summary>

```python
@st.cache_data(ttl=1800, show_spinner=False)
def get_multiple_companies_data(_self, company_names, period='2024 Annual'):
    """Fetch balance sheet data for multiple companies"""
    result = {}

    for company in company_names:
        try:
            data = _self.get_balance_sheet_data_by_period(company, period)
            if data:
                result[company] = data[0]
        except Exception:
            continue

    return result

# Usage
companies = ['Coastal', 'Ace', 'Winter']
all_data = airtable.get_multiple_companies_data(companies)
```

</details>

### Exercise 3: Calculate Cache Efficiency

**Task:** If a page makes 10 API calls the first time and is viewed 50 times in 30 minutes, how many total API calls are made?

<details>
<summary>Show Solution</summary>

**Answer: 10 API calls**

Explanation:
- First view: 10 API calls (cache miss)
- Next 49 views: 0 API calls (cache hit)
- Total: 10 calls

**Cache hit rate: 98% (49 out of 50 views)**

Without caching: 500 API calls (10 × 50)
Savings: 490 API calls (98% reduction!) 🚀

</details>

---

## Related Topics

- **[01-airtable-integration.md](01-airtable-integration.md)** - Understanding the data fetching foundation
- **[06-data-transformation.md](06-data-transformation.md)** - Efficiently transforming cached data
- **[feature-deep-dives/value-trend-analysis.md](feature-deep-dives/value-trend-analysis.md)** - Real-world bulk fetching example

---

## Next Steps

Now that you understand performance optimization, learn about **[03-session-state-navigation.md](03-session-state-navigation.md)** to manage user interactions and multi-page navigation efficiently!

---

*Remember: Premature optimization is the root of all evil, but knowing when and how to optimize is the root of all performance! 🚀*
