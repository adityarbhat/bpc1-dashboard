# 06: Data Transformation & Calculations

## Overview

Learn how the BPC Dashboard transforms raw Airtable data into meaningful financial metrics. This guide covers calculation patterns, data formatting, and transformation logic. You'll understand:

- Year-over-year (YoY) percentage calculations
- Multi-year trend analysis
- Currency and percentage formatting
- Handling null/missing values
- Direct expense aggregation
- Computed metrics (EBITDA, margins, ratios)

**Estimated Time:** 40-50 minutes

---

## Why Data Transformation Matters

### Raw Data vs Display Data

**Raw Airtable Data:**

```python
{
    'gross_profit': 1370128,
    'total_revenue': '8500000',
    'gpm': '16.12',  # Stored as string!
    'current_ratio': None  # Missing!
}
```

**After Transformation:**

```python
{
    'gross_profit': 1370128.0,
    'total_revenue': 8500000.0,
    'gpm': 16.12,
    'current_ratio': 0.0,
    'gpm_display': '16.1%',
    'revenue_display': '$8.50M'
}
```

**Benefits:**
✅ Consistent data types
✅ Handled missing values
✅ Formatted for display
✅ Ready for calculations

---

## The `_parse_percentage_or_float()` Function

### Purpose

Convert Airtable values (which can be strings, numbers, percentages, or None) into consistent floats.

### Implementation

```python
def _parse_percentage_or_float(value):
    """Parse a value that might be a percentage string or a float"""
    if value is None:
        return 0.0

    if isinstance(value, str):
        # Remove percentage sign and convert
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

    # If it's already a number
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0
```

### Examples

| Input | Output | Reason |
|-------|--------|--------|
| `None` | `0.0` | Missing data → default to 0 |
| `"15.5%"` | `15.5` | Removes % sign, parses number |
| `"15.5"` | `15.5` | Parses string to float |
| `15.5` | `15.5` | Already a number → convert to float |
| `"invalid"` | `0.0` | Can't parse → default to 0 |
| `True` | `1.0` | Boolean converts to 1.0 |

### Usage in Data Fetching

```python
balance_data.append({
    'current_ratio': _parse_percentage_or_float(fields.get('current_ratio', 0)),
    'debt_to_equity': _parse_percentage_or_float(fields.get('debt_to_equity', 0)),
    'total_revenue': _parse_percentage_or_float(fields.get('total_revenue', 0))
})
```

---

## Year-over-Year (YoY) Calculations

### The Formula

```
YoY % Change = ((Current Year - Previous Year) / |Previous Year|) × 100
```

### Implementation

```python
def calculate_yoy_percentages(company_name):
    """
    Calculate year-over-year percentage changes
    Compares 2024 Annual vs 2023 Annual
    """
    airtable = get_airtable_connection()

    # Fetch both years
    data_2024 = airtable.get_income_statement_data_by_period(company_name, "2024 Annual")
    data_2023 = airtable.get_income_statement_data_by_period(company_name, "2023 Annual")

    if not data_2024 or not data_2023:
        return None

    record_2024 = data_2024[0]
    record_2023 = data_2023[0]

    results = {}

    # Total Revenue
    rev_2024 = record_2024.get('total_revenue', 0) or 0
    rev_2023 = record_2023.get('total_revenue', 0) or 0

    if rev_2023 != 0:
        results['Total Revenue'] = ((rev_2024 - rev_2023) / abs(rev_2023)) * 100
    else:
        results['Total Revenue'] = 0.0

    return results
```

### Step-by-Step Example

**Data:**
- 2023 Revenue: $1,000,000
- 2024 Revenue: $1,200,000

**Calculation:**

```python
rev_2024 = 1200000
rev_2023 = 1000000

yoy = ((1200000 - 1000000) / 1000000) * 100
yoy = (200000 / 1000000) * 100
yoy = 0.2 * 100
yoy = 20.0  # 20% increase!
```

### Handling Edge Cases

**Division by Zero:**

```python
if rev_2023 != 0:
    yoy = ((rev_2024 - rev_2023) / abs(rev_2023)) * 100
else:
    yoy = 0.0  # Avoid division by zero
```

**Negative Previous Values:**

```python
# Use abs() to handle negatives correctly
# If profit went from -$100K to $50K
profit_2023 = -100000
profit_2024 = 50000

yoy = ((50000 - (-100000)) / abs(-100000)) * 100
yoy = (150000 / 100000) * 100
yoy = 150.0  # 150% improvement!
```

**Missing Data:**

```python
# If data doesn't exist, return 0
rev_current = record.get('total_revenue', 0) or 0
#                                           ^^^
#                                           Handles None case
```

---

## Multi-Year Trend Analysis

### Calculating Trends for Multiple Years

```python
def calculate_multi_year_yoy(company_name):
    """
    Calculate YoY for years 2021-2024
    Each year compared to its previous year

    Returns:
        {
            '2021': {'Total Revenue': 5.2, ...},
            '2022': {'Total Revenue': -2.1, ...},
            '2023': {'Total Revenue': 8.5, ...},
            '2024': {'Total Revenue': 12.3, ...}
        }
    """
    airtable = get_airtable_connection()

    years = ['2020', '2021', '2022', '2023', '2024']
    annual_data = {}

    # Fetch all years
    for year in years:
        period = f"{year} Annual"
        data = airtable.get_income_statement_data_by_period(company_name, period)
        if data and len(data) > 0:
            annual_data[year] = data[0]

    # Calculate YoY for each year
    results = {}

    for i in range(1, len(years)):
        current_year = years[i]
        previous_year = years[i-1]

        if current_year not in annual_data or previous_year not in annual_data:
            continue

        current_record = annual_data[current_year]
        previous_record = annual_data[previous_year]

        year_changes = {}

        # Total Revenue YoY
        rev_current = current_record.get('total_revenue', 0) or 0
        rev_previous = previous_record.get('total_revenue', 0) or 0

        if rev_previous != 0:
            year_changes['Total Revenue'] = ((rev_current - rev_previous) / abs(rev_previous)) * 100
        else:
            year_changes['Total Revenue'] = 0.0

        results[current_year] = year_changes

    return results
```

### Example Output

```python
{
    '2021': {
        'Total Revenue': 5.2,
        'Gross Profit': 3.5,
        'Operating Income': 12.8
    },
    '2022': {
        'Total Revenue': -2.1,
        'Gross Profit': 3.5,
        'Operating Income': -5.4
    },
    '2023': {
        'Total Revenue': 8.5,
        'Gross Profit': 10.2,
        'Operating Income': 15.7
    },
    '2024': {
        'Total Revenue': 12.3,
        'Gross Profit': 8.9,
        'Operating Income': 20.1
    }
}
```

---

## Direct Expense Aggregation

### The Challenge

Direct expenses are split across multiple Airtable fields:

```
Direct Expenses =
    direct_wages +
    vehicle_operating_expenses +
    packing_warehouse_supplies +
    oo_exp_intra_state +
    oo_inter_state +
    oo_oi +
    oo_packing +
    oo_other
```

### Implementation

```python
def calculate_direct_expenses(record):
    """Calculate total direct expenses from individual fields"""
    direct_expense_fields = [
        'direct_wages',
        'vehicle_operating_expenses',
        'packing_warehouse_supplies',
        'oo_exp_intra_state',  # Outsource: Intra State
        'oo_inter_state',       # Outsource: Inter State
        'oo_oi',                # Outsource: O&I
        'oo_packing',           # Outsource: Packing
        'oo_other'              # Outsource: Other
    ]

    total = sum(record.get(field, 0) or 0 for field in direct_expense_fields)
    return total
```

### Using in YoY Calculations

```python
# Get direct expenses for both years
dir_exp_2024 = calculate_direct_expenses(record_2024)
dir_exp_2023 = calculate_direct_expenses(record_2023)

# Calculate YoY
if dir_exp_2023 != 0:
    results['Direct Expenses'] = ((dir_exp_2024 - dir_exp_2023) / abs(dir_exp_2023)) * 100
```

---

## Currency Formatting

### Auto-Formatting Function

```python
def format_currency_auto(value):
    """
    Automatically format currency based on magnitude

    Examples:
        750 → "$750"
        1500 → "$1.50K"
        2500000 → "$2.50M"
    """
    if value >= 1000000:
        return f"${value/1000000:.2f}M"
    elif value >= 1000:
        return f"${value/1000:.2f}K"
    else:
        return f"${value:.0f}"
```

### Usage in Tables

```python
# Display formatted values
revenue_display = format_currency_auto(1234567)  # "$1.23M"
profit_display = format_currency_auto(45000)     # "$45.00K"
cash_display = format_currency_auto(750)         # "$750"
```

### Negative Values

```python
def format_currency_with_negative(value):
    """Format currency, using parentheses for negatives"""
    if value < 0:
        return f"$({abs(value)/1000:.2f}K)"
    else:
        return f"${value/1000:.2f}K"

# Examples:
format_currency_with_negative(50000)   # "$50.00K"
format_currency_with_negative(-25000)  # "$(25.00K)"
```

---

## Percentage Formatting

### Basic Percentage

```python
def format_percentage(value):
    """Format as percentage with 1 decimal"""
    return f"{value:.1f}%"

# Examples:
format_percentage(15.789)  # "15.8%"
format_percentage(-3.2)    # "-3.2%"
```

### Conditional Color-Coding

```python
def get_percentage_color(value, reverse=False):
    """
    Get color based on percentage value

    Args:
        value (float): Percentage value
        reverse (bool): True if lower is better
    """
    if reverse:
        if value <= 5:
            return "green"
        elif value <= 10:
            return "yellow"
        else:
            return "red"
    else:
        if value > 5:
            return "green"
        elif value > -5:
            return "yellow"
        else:
            return "red"

# Usage
color = get_percentage_color(12.5)  # "green"
st.markdown(f'<span style="color: {color};">12.5%</span>', unsafe_allow_html=True)
```

---

## Computed Metrics

### Company Value Calculation

```python
def calculate_company_value(ebitda, interest_bearing_debt):
    """
    Company Value = (EBITDA × 3) - Interest Bearing Debt

    Args:
        ebitda (float): EBITDA in dollars
        interest_bearing_debt (float): Debt in dollars

    Returns:
        float: Company value in dollars
    """
    return (ebitda * 3) - interest_bearing_debt

# Example:
ebitda = 500000  # $500K
debt = 300000    # $300K
value = calculate_company_value(ebitda, debt)
# value = (500000 * 3) - 300000 = $1,200,000
```

### Value to Equity Ratio

```python
def calculate_value_to_equity(company_value, equity):
    """
    Value to Equity = Company Value / Equity

    Args:
        company_value (float): Calculated company value
        equity (float): Owner's equity

    Returns:
        float: Ratio (e.g., 2.5 means value is 2.5x equity)
    """
    if equity == 0:
        return 0.0
    return company_value / equity

# Example:
value = 1200000  # $1.2M
equity = 500000  # $500K
ratio = calculate_value_to_equity(value, equity)
# ratio = 1200000 / 500000 = 2.4
```

---

## Handling Missing Data

### Strategy 1: Default to Zero

```python
value = record.get('field_name', 0) or 0
#                                  ^^^^
#                                  Handles None
```

### Strategy 2: Skip Calculation

```python
if data_2024 and data_2023:
    yoy = calculate_yoy(data_2024, data_2023)
else:
    yoy = None  # Return None instead of calculating
```

### Strategy 3: Use Previous Value

```python
if current_value is None:
    current_value = previous_value  # Carry forward
```

---

## Color-Coded Table Generation

### YoY Trends Table

```python
def get_cell_color(value):
    """Determine cell background color based on YoY percentage"""
    if value is None:
        return '#f8f9fa'  # Light gray
    elif value > 5:
        return '#d4edda'  # Green
    elif value < -5:
        return '#f8d7da'  # Red
    else:
        return '#fff3cd'  # Yellow

# Usage in table
for metric in metrics:
    for year in years:
        value = data[year].get(metric, None)
        color = get_cell_color(value)
        html += f'<td style="background-color: {color};">{value:.1f}%</td>'
```

---

## Key Takeaways

✅ **Parse all inputs** with `_parse_percentage_or_float()`
✅ **Handle division by zero** in all percentage calculations
✅ **Use `abs()` for negatives** in YoY calculations
✅ **Default missing data** appropriately (0, None, or previous value)
✅ **Format for display** separately from calculations
✅ **Aggregate related fields** (direct expenses)
✅ **Color-code values** for quick insights
✅ **Document formulas** in code comments

---

## Try It Yourself

### Exercise 1: Calculate YoY Growth

<details>
<summary>Show Solution</summary>

```python
def calculate_revenue_growth(current, previous):
    """Calculate revenue YoY growth percentage"""
    if previous == 0:
        return 0.0

    growth = ((current - previous) / abs(previous)) * 100
    return growth

# Test
assert calculate_revenue_growth(1200, 1000) == 20.0
assert calculate_revenue_growth(800, 1000) == -20.0
assert calculate_revenue_growth(1000, 0) == 0.0
```

</details>

### Exercise 2: Format Currency Auto

<details>
<summary>Show Solution</summary>

```python
def format_currency_smart(value):
    """Smart currency formatting"""
    if value >= 1000000:
        return f"${value/1000000:.2f}M"
    elif value >= 1000:
        return f"${value/1000:.2f}K"
    else:
        return f"${value:.0f}"

# Test
assert format_currency_smart(750) == "$750"
assert format_currency_smart(1500) == "$1.50K"
assert format_currency_smart(2500000) == "$2.50M"
```

</details>

---

## Related Topics

- **[01-airtable-integration.md](01-airtable-integration.md)** - Where data comes from
- **[04-plotly-visualizations.md](04-plotly-visualizations.md)** - Displaying transformed data
- **[feature-deep-dives/yoy-calculations.md](feature-deep-dives/yoy-calculations.md)** - Advanced YoY patterns

---

## Next Steps

Learn about **[07-error-handling.md](07-error-handling.md)** to make your transformations robust and user-friendly!

---

*Remember: Good data transformation is like good cooking - handle ingredients carefully, measure precisely, and taste (test) before serving! 🧑‍🍳*
