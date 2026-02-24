# 05: Reusable Components

## Overview

Learn how to build reusable UI components that maintain consistency across your dashboard. This guide covers the BPC Dashboard's component library approach. You'll understand:

- The DRY (Don't Repeat Yourself) principle
- Creating centralized CSS styling
- Building reusable page headers
- Period selectors and navigation elements
- Component architecture patterns
- When to componentize vs inline code

**Estimated Time:** 30-40 minutes

---

## Why Reusable Components?

### The Problem: Code Duplication

**Before Components:**

```python
# Page 1
st.markdown("""
<div style="background: #c2002f; color: white; padding: 1rem; text-align: center;">
    <h1>BPC 2 Financial Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# Page 2
st.markdown("""
<div style="background: #c2002f; color: white; padding: 1rem; text-align: center;">
    <h1>BPC 2 Financial Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# ... Repeated 20 times across pages!
```

**Problems:**
- Duplicated code (maintenance nightmare)
- Inconsistent styling (typos, variations)
- Hard to update (change 20 files!)

### The Solution: Centralized Components

**After Components:**

```python
# In shared/page_components.py
def create_red_banner():
    st.markdown("""
    <div class="header-banner">
        <div class="banner-title">BPC 2 Financial Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

# In every page
from shared.page_components import create_red_banner
create_red_banner()
```

**Benefits:**
✅ Write once, use everywhere
✅ Consistent appearance
✅ Update in one place
✅ Less code, fewer bugs

---

## BPC Dashboard Component Architecture

### File Structure

```
shared/
├── css_styles.py          # Centralized CSS
├── page_components.py     # Reusable UI components
├── chart_utils.py         # Chart creation utilities
└── airtable_connection.py # Data fetching
```

### Component Categories

1. **Styling Components** (`css_styles.py`)
   - Global CSS rules
   - Color palette
   - Typography

2. **Page Components** (`page_components.py`)
   - Red banner header
   - Period selector
   - Page headers

3. **Chart Components** (`chart_utils.py`)
   - Gauge charts
   - Comparison charts
   - Trend charts

---

## Building a Page Header Component

### The Comp lete Function

```python
def create_page_header(page_title=None, subtitle=None, show_period_selector=True):
    """
    Create standardized page header with consistent spacing

    Args:
        page_title (str): Main page title (H1)
        subtitle (str): Optional subtitle text
        show_period_selector (bool): Whether to show period selector
    """
    # Red banner
    create_red_banner()

    # Period selector (if requested)
    if show_period_selector:
        create_period_selector()

    # Main title (if provided)
    if page_title:
        st.markdown(f'<h1 style="...">{page_title}</h1>', unsafe_allow_html=True)

    # Subtitle (if provided)
    if subtitle:
        st.markdown(f'<div class="...">{subtitle}</div>', unsafe_allow_html=True)
```

### Usage Examples

**Simple Header:**

```python
from shared.page_components import create_page_header

create_page_header(page_title="Company Ratios")
```

**Full Header with All Elements:**

```python
create_page_header(
    page_title="Group Overview",
    subtitle="Welcome to the 2025 BPC 2 Financial Analysis!",
    show_period_selector=True
)
```

**Header Without Period Selector:**

```python
create_page_header(
    page_title="Data Upload",
    show_period_selector=False  # Admin pages don't need period
)
```

---

## CSS Styling Component

### Centralized Styles (`css_styles.py`)

```python
def apply_all_styles():
    """Apply all custom CSS styles to the dashboard"""
    st.markdown("""
    <style>
        /* Global Styles */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

        .stApp {
            font-family: 'Montserrat', sans-serif;
            background-color: #ffffff;
        }

        /* Button Styles */
        .stButton > button {
            background: #025a9a;
            color: white;
            border-radius: 50px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            border: none;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background: #0e9cd5;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(2, 90, 154, 0.3);
        }

        /* Table Styles */
        .dataframe {
            font-family: 'Montserrat', sans-serif !important;
            font-size: 0.9rem !important;
        }

        /* More styles... */
    </style>
    """, unsafe_allow_html=True)
```

### Applying Styles

```python
# In financial_dashboard.py main()
from shared.css_styles import apply_all_styles

def main():
    st.set_page_config(...)

    # Apply styles once at app start
    apply_all_styles()

    # ... rest of app
```

---

## Period Selector Component

### Visual Design

```
┌─────────┬──────────┐
│Year End │ Mid Year │  ← Buttons
└─────────┴──────────┘
   Active    Inactive
```

### Implementation

```python
def create_period_selector():
    """Create period selector with consistent spacing"""
    # Initialize state
    if 'period' not in st.session_state:
        st.session_state.period = 'year_end'

    # CSS for styling
    st.markdown("""
    <style>
        .period-btn {
            padding: 0.4rem 0.8rem;
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            font-size: 0.9rem;
        }

        .period-btn.active {
            background: #025a9a;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

    # Display buttons
    active_year = "active" if st.session_state.period == 'year_end' else ""
    active_june = "active" if st.session_state.period == 'june_end' else ""

    st.markdown(f"""
    <div class="period-selector">
        <div class="period-btn {active_year}">Year End</div>
        <div class="period-btn {active_june}">Mid Year</div>
    </div>
    """, unsafe_allow_html=True)
```

### Helper Function

```python
def get_period_display_text():
    """Get formatted period text for display in headers"""
    if st.session_state.get('period') == 'june_end':
        return "Mid Year"
    return "Year End"

# Usage
period_text = get_period_display_text()
st.title(f"Company Ratios - {period_text}")
```

---

## Component Design Principles

### 1. Single Responsibility

**Good:**

```python
def create_red_banner():
    """Creates ONLY the red banner"""
    # ...

def create_period_selector():
    """Creates ONLY the period selector"""
    # ...

def create_page_header(page_title, subtitle, show_period_selector):
    """Composes smaller components"""
    create_red_banner()
    if show_period_selector:
        create_period_selector()
    # ...
```

**Bad:**

```python
def create_everything():
    """Creates banner AND period selector AND title AND..."""
    # Too much in one function!
    # Hard to reuse parts independently
```

### 2. Optional Parameters

```python
def create_page_header(
    page_title=None,          # Optional
    subtitle=None,            # Optional
    show_period_selector=True # Has default
):
    # Handles all combinations
```

**Flexibility:**

```python
# Just banner
create_page_header()

# Banner + title
create_page_header(page_title="Analysis")

# Everything
create_page_header(page_title="Analysis", subtitle="Welcome", show_period_selector=True)
```

### 3. Clear Documentation

```python
def create_component(param1, param2):
    """
    Short description

    Args:
        param1 (type): What it does
        param2 (type): What it does

    Returns:
        type: What it returns

    Example:
        >>> create_component("value", True)
    """
```

---

## When to Create a Component

### Create a Component When:

✅ **Used 3+ times** across different pages
✅ **Complex enough** to benefit from encapsulation
✅ **Needs consistency** (headers, styling)
✅ **Likely to change** (update once vs many places)

### Keep Inline When:

❌ **Used only once** on a single page
❌ **Very simple** (1-2 lines of code)
❌ **Page-specific logic** that won't be reused

**Example Decision:**

```python
# CREATE COMPONENT: Used on 20 pages
def create_red_banner():
    st.markdown("""...""")

# KEEP INLINE: Used only on Company Ratios page
def display_ratio_range_key():
    st.markdown("""...""")  # Page-specific table
```

---

## Advanced Component Patterns

### 1. Component Composition

```python
def create_page_header(page_title, subtitle, show_period_selector):
    """Compose multiple smaller components"""
    create_red_banner()              # Component 1

    if show_period_selector:
        create_period_selector()      # Component 2

    if page_title:
        create_title(page_title)      # Component 3

    if subtitle:
        create_subtitle(subtitle)     # Component 4
```

**Benefits:**
- Build complex UI from simple parts
- Each part independently testable
- Mix and match as needed

### 2. Component with State

```python
def create_company_selector():
    """Component that manages its own state"""
    # Initialize state
    if 'selected_company' not in st.session_state:
        st.session_state.selected_company = 'Coastal'

    # Get companies
    airtable = get_airtable_connection()
    companies = airtable.get_companies()

    # Create selector
    selected = st.selectbox(
        "Select Company",
        options=[c['name'] for c in companies],
        index=[c['name'] for c in companies].index(st.session_state.selected_company)
    )

    # Update state
    st.session_state.selected_company = selected

    return selected
```

### 3. Configurable Components

```python
def create_metric_card(title, value, delta=None, color="blue"):
    """Reusable metric display card with configurable styling"""

    colors = {
        "blue": "#025a9a",
        "green": "#28a745",
        "red": "#dc3545"
    }

    st.markdown(f"""
    <div style="background: {colors[color]}; padding: 1rem; border-radius: 8px; color: white;">
        <h3>{title}</h3>
        <h1>{value}</h1>
        {f'<p>↑ {delta}%</p>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)

# Usage
create_metric_card("Revenue", "$1.5M", delta=5.2, color="green")
create_metric_card("Expenses", "$800K", delta=-3.1, color="red")
```

---

## Component Testing

### Manual Testing Checklist

For each component, verify:

- [ ] Works with all parameter combinations
- [ ] Handles None/missing values gracefully
- [ ] Looks good on mobile and desktop
- [ ] Consistent with design system
- [ ] No console errors
- [ ] Session state managed correctly

### Example Test Cases

```python
# Test create_page_header()
create_page_header()  # Minimal - just banner
create_page_header(page_title="Test")  # With title
create_page_header(page_title="Test", subtitle="Sub")  # With subtitle
create_page_header(page_title="Test", show_period_selector=False)  # No selector
create_page_header(page_title=None, subtitle="Sub")  # Subtitle only
```

---

## Migration Strategy

### Converting Inline Code to Components

**Step 1: Identify Duplication**

```python
# Count usage of similar code
# If appears 3+ times → componentize
```

**Step 2: Extract to Function**

```python
# Before (in page1.py)
st.markdown("""...""")

# Before (in page2.py)
st.markdown("""...""")

# After (in shared/components.py)
def create_banner():
    st.markdown("""...""")
```

**Step 3: Replace All Usages**

```python
# page1.py
from shared.components import create_banner
create_banner()

# page2.py
from shared.components import create_banner
create_banner()
```

**Step 4: Test Thoroughly**

```python
# Verify all pages still work
# Check visual consistency
```

---

## Key Takeaways

✅ **Centralize repeated UI** in component library
✅ **Use descriptive function names** (create_X, display_X)
✅ **Provide optional parameters** for flexibility
✅ **Document with docstrings** and examples
✅ **Apply DRY principle** (Don't Repeat Yourself)
✅ **Compose complex components** from simple ones
✅ **Test all parameter combinations**
✅ **Update styles in ONE place**

---

## Try It Yourself

### Exercise 1: Create a Simple Component

**Task:** Create a reusable alert box component

<details>
<summary>Show Solution</summary>

```python
def create_alert(message, alert_type="info"):
    """
    Create a colored alert box

    Args:
        message (str): Alert message
        alert_type (str): "info", "warning", "success", or "error"
    """
    colors = {
        "info": "#0e9cd5",
        "warning": "#ffc107",
        "success": "#28a745",
        "error": "#dc3545"
    }

    st.markdown(f"""
    <div style="background: {colors[alert_type]}; color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
        {message}
    </div>
    """, unsafe_allow_html=True)

# Usage
create_alert("Data loaded successfully!", "success")
create_alert("Warning: Low balance", "warning")
```

</details>

### Exercise 2: Compose Components

**Task:** Create a dashboard card that uses multiple components

<details>
<summary>Show Solution</summary>

```python
def create_dashboard_card(title, metrics):
    """
    Create a card with title and multiple metrics

    Args:
        title (str): Card title
        metrics (list): List of (name, value) tuples
    """
    st.markdown(f"""
    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
        <h3>{title}</h3>
    """, unsafe_allow_html=True)

    for name, value in metrics:
        create_metric_row(name, value)

    st.markdown("</div>", unsafe_allow_html=True)

def create_metric_row(name, value):
    """Display a single metric row"""
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #e2e8f0;">
        <span>{name}</span>
        <strong>{value}</strong>
    </div>
    """, unsafe_allow_html=True)

# Usage
create_dashboard_card("Financial Summary", [
    ("Revenue", "$1.5M"),
    ("Expenses", "$800K"),
    ("Profit", "$700K")
])
```

</details>

---

## Related Topics

- **[04-plotly-visualizations.md](04-plotly-visualizations.md)** - Chart components
- **[03-session-state-navigation.md](03-session-state-navigation.md)** - State in components
- **[06-data-transformation.md](06-data-transformation.md)** - Next topic

---

## Next Steps

Learn about **[06-data-transformation.md](06-data-transformation.md)** to understand how to prepare and transform data for your components!

---

*Remember: Good components are like LEGO bricks - simple, reusable, and composable! 🧱*
