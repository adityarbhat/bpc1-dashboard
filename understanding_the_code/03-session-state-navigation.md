# 03: Session State & Navigation

## Overview

Streamlit's session state is the key to building interactive, stateful applications. This guide will teach you how the BPC Dashboard uses session state to manage user navigation, preserve selections, and create a seamless multi-page experience. By the end, you'll understand:

- What session state is and why it's essential
- How to initialize and manage state variables
- Building multi-page navigation without `st.page_link`
- Preventing infinite rerun loops
- State persistence patterns
- Navigation architecture in the BPC Dashboard

**Estimated Time:** 45-60 minutes

---

## The Streamlit Rerun Challenge

### Understanding Streamlit's Execution Model

**Critical Concept:** Streamlit reruns your entire script from top to bottom on EVERY interaction!

```python
# This entire file runs again when user clicks ANYTHING
import streamlit as st

print("Script started!")  # Prints EVERY TIME

x = 5  # Resets to 5 EVERY TIME
x += 1  # Always equals 6, never increments

st.write(f"x = {x}")  # Always shows 6
```

**Problem:**

Variables reset on every rerun - you lose all state!

```python
# User clicks button
if st.button("Click me"):
    counter = 0  # This line runs AGAIN next time
    counter += 1  # Always 1, never increments
    st.write(f"Clicked {counter} times")  # Always shows "Clicked 1 times"
```

**Why This Happens:**

```
User clicks button → Script runs top to bottom → counter = 0 → counter += 1 → Display
User clicks again  → Script runs top to bottom → counter = 0 → counter += 1 → Display (still 1!)
```

---

## Solution: Session State

### What is Session State?

Session state is a **dictionary-like object** that **persists across reruns**:

```python
import streamlit as st

# Initialize counter in session state
if 'counter' not in st.session_state:
    st.session_state.counter = 0

# Increment on button click
if st.button("Click me"):
    st.session_state.counter += 1

st.write(f"Clicked {st.session_state.counter} times")  # Increments properly!
```

**Timeline:**

```
Initial load → counter = 0 → Display "Clicked 0 times"
User clicks → counter += 1 → Display "Clicked 1 times"
User clicks → counter += 1 → Display "Clicked 2 times"
User clicks → counter += 1 → Display "Clicked 3 times"
```

**Key Insight:** Values in `st.session_state` survive across reruns!

---

## Session State Basics

### 1. Initializing State Variables

**Pattern:**

```python
if 'variable_name' not in st.session_state:
    st.session_state.variable_name = initial_value
```

**BPC Dashboard Example:**

```python
# In financial_dashboard.py main() function
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'

if 'nav_tab' not in st.session_state:
    st.session_state.nav_tab = 'group'

if 'period' not in st.session_state:
    st.session_state.period = 'year_end'
```

**Line-by-Line:**

| Line | Purpose |
|------|---------|
| `if 'current_page' not in st.session_state:` | Check if variable exists (only False on first run) |
| `st.session_state.current_page = 'overview'` | Set default value |

**Why the `if` Check?**

Without it, you'd reset the value on every rerun!

```python
# BAD - Resets every time
st.session_state.current_page = 'overview'  # Always goes back to overview!

# GOOD - Only sets initial value
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'
```

### 2. Reading State Variables

**Two ways:**

```python
# Method 1: Dictionary-style access
current_page = st.session_state['current_page']

# Method 2: Attribute-style access (more readable)
current_page = st.session_state.current_page
```

**BPC Dashboard uses Method 2:**

```python
if st.session_state.current_page == 'overview':
    create_group_overview_page(companies)
```

### 3. Updating State Variables

**Direct assignment:**

```python
st.session_state.current_page = 'company_ratios'
```

**Common pattern in button callbacks:**

```python
if st.button("Go to Ratios"):
    st.session_state.current_page = 'company_ratios'
    st.rerun()  # Force immediate rerun to show new page
```

### 4. The `.get()` Method for Safe Access

**Problem:**

```python
period = st.session_state.period  # KeyError if not initialized!
```

**Solution:**

```python
period = st.session_state.get('period', 'year_end')  # Returns 'year_end' if not found
```

**Use Case:**

When you're not sure if a variable has been initialized yet.

---

## Navigation Architecture in BPC Dashboard

### Overview of Navigation System

The BPC Dashboard uses session state to manage a **multi-page single-file application**:

```
financial_dashboard.py (main file)
    ├── Session State Variables
    │   ├── current_page (which page to show)
    │   ├── nav_tab (group vs company)
    │   ├── period (year_end vs june_end)
    │   └── selected_company_name (for company pages)
    │
    ├── Sidebar Navigation
    │   └── Buttons update session state
    │
    └── Page Routing
        └── Shows page based on current_page
```

### Key Session State Variables

| Variable | Purpose | Possible Values | Default |
|----------|---------|-----------------|---------|
| `current_page` | Which page to display | `'overview'`, `'company_ratios'`, `'balance_sheet_comparison'`, etc. | `'overview'` |
| `nav_tab` | Group or Company analysis | `'group'`, `'company'` | `'group'` |
| `period` | Time period for data | `'year_end'`, `'june_end'` | `'year_end'` |
| `selected_company_name` | Selected company for analysis | `'Coastal'`, `'Ace'`, etc. | `None` |

---

## Building the Navigation System

### Step 1: Initialize Session State

```python
def main():
    # Page configuration
    st.set_page_config(...)

    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'overview'
    if 'nav_tab' not in st.session_state:
        st.session_state.nav_tab = 'group'
    if 'period' not in st.session_state:
        st.session_state.period = 'year_end'
```

**Why in `main()`?**

This runs on EVERY script execution, so state is always initialized before use.

### Step 2: Create Navigation Sidebar

```python
def create_sidebar_navigation():
    """Create the sidebar navigation matching the Atlas BPC layout"""
    st.sidebar.empty()  # Clear existing content

    with st.sidebar:
        # Overview button
        if st.button("🏠 Overview", key="nav_overview", use_container_width=True):
            st.session_state.current_page = "overview"
            st.session_state.nav_tab = "group"
            st.rerun()  # Force immediate page change
```

**Let's Break This Down:**

#### The Button Pattern

```python
if st.button("🏠 Overview", key="nav_overview", use_container_width=True):
    st.session_state.current_page = "overview"
    st.session_state.nav_tab = "group"
    st.rerun()
```

**What Happens:**

1. **User clicks "Overview"**
2. **`st.button()` returns `True`** (only for this rerun)
3. **State updates**: `current_page = "overview"`, `nav_tab = "group"`
4. **`st.rerun()`** triggers script to run again immediately
5. **Next rerun**: Main routing shows overview page

#### The `key` Parameter

```python
key="nav_overview"
```

**Purpose:**

Every Streamlit widget needs a unique key. Without it, widgets can conflict:

```python
# BAD - Both buttons have same default key!
if st.button("Click"):  # Key: "button_0"
    do_something()

if st.button("Click"):  # Key: "button_0" - CONFLICT!
    do_something_else()

# GOOD - Explicit unique keys
if st.button("Click", key="btn1"):
    do_something()

if st.button("Click", key="btn2"):
    do_something_else()
```

### Step 3: Analysis Type Selector (Dropdown)

```python
# Analysis Type filter
if 'nav_tab' not in st.session_state:
    st.session_state.nav_tab = 'group'

analysis_options = ["Group", "Company"]
current_selection = "Group" if st.session_state.nav_tab == 'group' else "Company"

selected_analysis = st.selectbox(
    "**Analysis Type**",
    options=analysis_options,
    index=analysis_options.index(current_selection),
    key="analysis_type_selector"
)

# Handle analysis type changes
if selected_analysis == "Group" and st.session_state.nav_tab != 'group':
    st.session_state.nav_tab = 'group'
    st.session_state.current_page = 'overview'
    st.rerun()
elif selected_analysis == "Company" and st.session_state.nav_tab != 'company':
    st.session_state.nav_tab = 'company'
    st.session_state.current_page = 'company_ratios'
    st.rerun()
```

**How This Works:**

1. **`current_selection`**: Maps session state to display value
   ```python
   # If nav_tab = 'group' → Show "Group" in dropdown
   # If nav_tab = 'company' → Show "Company" in dropdown
   ```

2. **`index` Parameter**: Sets which option is selected
   ```python
   options = ["Group", "Company"]
   # If current_selection = "Company"
   index = options.index("Company")  # = 1
   # Dropdown shows "Company" as selected
   ```

3. **Change Detection**: Only update state if value actually changed
   ```python
   if selected_analysis == "Group" and st.session_state.nav_tab != 'group':
       # Only runs if user switched FROM company TO group
   ```

**Why Check Before Updating?**

Prevents infinite rerun loops!

```python
# BAD - Infinite loop!
if selected_analysis == "Group":
    st.session_state.nav_tab = 'group'
    st.rerun()  # Reruns → selectbox shows "Group" → code runs again → rerun again → INFINITE!

# GOOD - Only updates if changed
if selected_analysis == "Group" and st.session_state.nav_tab != 'group':
    st.session_state.nav_tab = 'group'
    st.rerun()  # Reruns → selectbox shows "Group" → code doesn't run (already 'group') → STOPS
```

### Step 4: Page Routing

```python
def main():
    # ... initialization ...

    # Main content area - route to appropriate page
    if st.session_state.current_page == 'overview':
        create_group_overview_page(companies)

    elif st.session_state.current_page == 'company_ratios':
        create_company_ratios_page()

    elif st.session_state.current_page == 'company_balance_sheet':
        create_company_balance_sheet_page()

    elif st.session_state.current_page == 'balance_sheet_comparison':
        create_group_balance_sheet_page()

    # ... more pages ...
```

**Pattern:**

```python
if st.session_state.current_page == 'page_name':
    show_that_page()
```

**Why `elif` Instead of Multiple `if`s?**

```python
# BAD - Checks every condition (slower)
if st.session_state.current_page == 'overview':
    create_group_overview_page()
if st.session_state.current_page == 'company_ratios':  # Still checks even if overview was True
    create_company_ratios_page()

# GOOD - Stops at first match (faster)
if st.session_state.current_page == 'overview':
    create_group_overview_page()
elif st.session_state.current_page == 'company_ratios':  # Skipped if overview was True
    create_company_ratios_page()
```

---

## Advanced Patterns

### Pattern 1: Cross-Page Navigation

**Company pages navigate to other company pages:**

```python
# In company_wins_challenges.py sidebar
if st.button("% Ratios", key="wins_nav_ratios", use_container_width=True):
    st.session_state.current_page = "company_ratios"
    st.rerun()

if st.button("📊 Balance Sheet", key="wins_nav_balance", use_container_width=True):
    st.session_state.current_page = "company_balance_sheet"
    st.rerun()
```

**Key Insight:**

Each company page creates its own sidebar, but all use the same session state variables for consistency!

### Pattern 2: Preserving Company Selection

**Problem:**

User selects "Coastal" on Ratios page, navigates to Balance Sheet - should still show "Coastal"!

**Solution:**

```python
# Company selector
selected_company_name = st.selectbox(
    "**Select Company Below**",
    options=list(company_options.keys()),
    key="company_wins_challenges_selector",
    index=list(company_options.keys()).index(current_company)
)

# Save to session state
st.session_state.selected_company_name = selected_company_name
```

**On next page:**

```python
# Get current selection or default
current_company = st.session_state.get('selected_company_name', 'Coastal')
```

**Result:** Company selection persists across all company pages! 🎯

### Pattern 3: Conditional Sidebar Creation

**Challenge:**

Some pages create their own custom sidebar (like company pages). Don't want two sidebars!

**Solution:**

```python
# Define which pages handle their own sidebar
company_pages = ['company_ratios', 'company_balance_sheet', ...]
data_input_pages = ['data_input']

# Only create main sidebar for other pages
if st.session_state.current_page not in company_pages and st.session_state.current_page not in data_input_pages:
    create_sidebar_navigation()
```

**Alternative: Early Return Pattern**

```python
# In company page file
def create_company_ratios_page():
    # Create custom sidebar for this page
    create_company_sidebar()

    # Handle navigation to other pages BEFORE showing content
    if st.session_state.get('current_page') == 'company_balance_sheet':
        from company_balance_sheet import create_company_balance_sheet_page
        create_company_balance_sheet_page()
        return  # Exit early!

    # If we got here, show this page's content
    st.title("Company Ratios")
    # ... page content ...
```

---

## The Rerun Mechanism

### What is `st.rerun()`?

**Immediately stops execution and reruns the script from top to bottom.**

```python
st.write("Before rerun")
st.rerun()
st.write("Never executes!")  # This line NEVER runs
```

### When to Use `st.rerun()`

**Use Case 1: Immediate State Changes**

```python
if st.button("Switch to Company View"):
    st.session_state.nav_tab = 'company'
    st.rerun()  # Show change immediately

# Without st.rerun(), change wouldn't show until next user interaction!
```

**Use Case 2: After Data Updates**

```python
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()  # Clear cache
    st.rerun()  # Reload page with fresh data
```

**Use Case 3: Navigation**

```python
if st.button("Go to Overview"):
    st.session_state.current_page = 'overview'
    st.rerun()  # Navigate immediately
```

### When NOT to Use `st.rerun()`

**Avoid Infinite Loops:**

```python
# BAD - Infinite loop!
if True:  # Always true
    st.rerun()  # Reruns forever!

# BAD - Subtle infinite loop
if st.session_state.counter > 0:
    st.session_state.counter += 1
    st.rerun()  # If counter starts at 1, infinite loop!

# GOOD - Conditional with termination
if st.button("Increment"):  # Only True once per click
    st.session_state.counter += 1
    st.rerun()
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Forgetting to Initialize State

**Problem:**

```python
# No initialization!
if st.session_state.current_page == 'overview':  # KeyError!
    show_overview()
```

**Solution:**

```python
# Always initialize
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'

if st.session_state.current_page == 'overview':
    show_overview()
```

### Pitfall 2: Infinite Rerun Loops

**Problem:**

```python
# Runs on every rerun, causing infinite loop!
st.session_state.counter += 1
st.rerun()
```

**Solution:**

```python
# Only rerun on specific user action
if st.button("Increment"):
    st.session_state.counter += 1
    st.rerun()
```

**Debugging Infinite Loops:**

Add print statements:

```python
import time

print(f"[{time.time()}] Rerun triggered")

if some_condition:
    print("About to rerun!")
    st.rerun()
```

If you see rapid repeated prints, you have a loop!

### Pitfall 3: State Not Persisting

**Problem:**

```python
# Using local variable instead of session state
selected_company = st.selectbox("Company", companies)
# Lost on next rerun!
```

**Solution:**

```python
# Save to session state
selected_company = st.selectbox("Company", companies)
st.session_state.selected_company = selected_company

# Access later
company = st.session_state.selected_company
```

### Pitfall 4: Widget Key Conflicts

**Problem:**

```python
# In sidebar
st.button("Home", key="nav_button")

# In main area
st.button("Home", key="nav_button")  # Duplicate key error!
```

**Solution:**

```python
st.button("Home", key="sidebar_nav_home")
st.button("Home", key="main_nav_home")
```

**Naming Convention:**

```python
key="{location}_{widget_type}_{purpose}"

Examples:
- "sidebar_nav_overview"
- "main_btn_submit"
- "filter_select_company"
```

### Pitfall 5: Accessing State Before Initialization

**Problem:**

```python
# Runs before initialization
companies = fetch_companies(st.session_state.period)  # KeyError!

# Later...
if 'period' not in st.session_state:
    st.session_state.period = 'year_end'
```

**Solution:**

```python
# Initialize FIRST
if 'period' not in st.session_state:
    st.session_state.period = 'year_end'

# Then use
companies = fetch_companies(st.session_state.period)
```

**Rule:** Initialize ALL state variables at the top of `main()`!

---

## Multi-Page Architecture Comparison

### Option 1: Single File with Session State (BPC Dashboard)

**Structure:**

```python
# financial_dashboard.py
def main():
    initialize_state()
    create_sidebar()

    if st.session_state.current_page == 'page1':
        show_page1()
    elif st.session_state.current_page == 'page2':
        show_page2()
```

**Pros:**
✅ Single entry point
✅ Easy to share state across pages
✅ Simple deployment

**Cons:**
❌ Large file can get unwieldy
❌ All imports happen upfront

### Option 2: Streamlit Pages (Folder Structure)

**Structure:**

```
app.py
pages/
    ├── 1_page1.py
    ├── 2_page2.py
```

**Pros:**
✅ Automatic navigation
✅ Separate files for organization

**Cons:**
❌ Harder to share state
❌ Less control over navigation

**BPC Dashboard Choice:**

Uses Option 1 with **modular imports** to get best of both:

```python
from pages.company_pages.company_ratios import create_company_ratios_page
from pages.group_pages.group_ratios import create_group_ratios_page
```

- Organized in folders
- Single main routing file
- Full control over navigation
- Shared session state

---

## Debugging Session State

### View All State Variables

```python
st.write("Current Session State:")
st.write(st.session_state)
```

**Output:**

```python
{
    'current_page': 'company_ratios',
    'nav_tab': 'company',
    'period': 'year_end',
    'selected_company_name': 'Coastal',
    'companies_cache': [...]
}
```

### Debugging Specific Variables

```python
with st.expander("Debug Info"):
    st.write(f"Current Page: {st.session_state.get('current_page', 'NOT SET')}")
    st.write(f"Nav Tab: {st.session_state.get('nav_tab', 'NOT SET')}")
    st.write(f"Period: {st.session_state.get('period', 'NOT SET')}")
```

### Reset State (For Testing)

```python
if st.button("Reset State"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
```

---

## Key Takeaways

✅ **Session state persists** across reruns - use it for all stateful data
✅ **Initialize state early** - in `main()` before any usage
✅ **Use `st.rerun()`** for immediate state changes
✅ **Avoid infinite loops** - only rerun on specific user actions
✅ **Unique widget keys** - prevent conflicts with descriptive naming
✅ **Check before updating** - prevent unnecessary reruns
✅ **`.get()` for safety** - provide defaults for uninitialized state
✅ **Navigation with session state** - `current_page` pattern for routing

---

## Try It Yourself

### Exercise 1: Build a Simple Counter

**Task:** Create a counter that increments on button click

<details>
<summary>Show Solution</summary>

```python
import streamlit as st

# Initialize counter
if 'counter' not in st.session_state:
    st.session_state.counter = 0

# Display current count
st.write(f"Count: {st.session_state.counter}")

# Increment button
if st.button("Increment"):
    st.session_state.counter += 1
    st.rerun()

# Reset button
if st.button("Reset"):
    st.session_state.counter = 0
    st.rerun()
```

</details>

### Exercise 2: Multi-Page Navigation

**Task:** Create a simple two-page app with navigation

<details>
<summary>Show Solution</summary>

```python
import streamlit as st

# Initialize current page
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

# Sidebar navigation
with st.sidebar:
    if st.button("Home"):
        st.session_state.current_page = 'home'
        st.rerun()

    if st.button("About"):
        st.session_state.current_page = 'about'
        st.rerun()

# Page routing
if st.session_state.current_page == 'home':
    st.title("Home Page")
    st.write("Welcome to the home page!")

elif st.session_state.current_page == 'about':
    st.title("About Page")
    st.write("This is the about page.")
```

</details>

### Exercise 3: Persistent Form

**Task:** Create a form where selections persist even after submission

<details>
<summary>Show Solution</summary>

```python
import streamlit as st

# Initialize state
if 'name' not in st.session_state:
    st.session_state.name = ""
if 'age' not in st.session_state:
    st.session_state.age = 18

# Form
with st.form("my_form"):
    name = st.text_input("Name", value=st.session_state.name)
    age = st.number_input("Age", value=st.session_state.age, min_value=0, max_value=120)

    submitted = st.form_submit_button("Submit")

    if submitted:
        st.session_state.name = name
        st.session_state.age = age
        st.rerun()

# Display saved values
if st.session_state.name:
    st.success(f"Saved: {st.session_state.name}, Age {st.session_state.age}")
```

</details>

---

## Related Topics

- **[02-performance-optimization.md](02-performance-optimization.md)** - Caching strategies that work with session state
- **[05-reusable-components.md](05-reusable-components.md)** - Building components that use session state
- **[04-plotly-visualizations.md](04-plotly-visualizations.md)** - Next topic: creating interactive charts

---

## Next Steps

Now that you understand session state and navigation, learn about **[04-plotly-visualizations.md](04-plotly-visualizations.md)** to create stunning interactive charts and visualizations!

---

*Remember: Session state is your friend - use it to make your Streamlit app feel like a true web application! 🎯*
