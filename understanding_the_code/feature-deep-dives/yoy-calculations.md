# Feature Deep Dive: Year-over-Year Calculations

## Overview

Complete breakdown of the Year-over-Year (YoY) calculation system used in the Wins & Challenges page. Learn the math, implementation, and color-coded visualization.

**File:** `pages/company_pages/company_wins_challenges.py`
**Functions:** `calculate_yoy_percentages()`, `calculate_multi_year_yoy()`
**Difficulty:** Intermediate
**Time:** 30-40 minutes

---

## The YoY Formula

```
YoY % Change = ((Current Year - Previous Year) / |Previous Year|) × 100
```

**Why absolute value in denominator?**

Handles negative previous values correctly:

```python
# Profit went from -$100K to $50K
Previous = -100000
Current = 50000

YoY = ((50000 - (-100000)) / |-100000|) × 100
YoY = (150000 / 100000) × 100
YoY = 150%  # 150% improvement!
```

---

## Single Year Comparison

### Implementation

```python
def calculate_yoy_percentages(company_name):
    """Compare 2024 vs 2023"""
    airtable = get_airtable_connection()

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

    # Direct Expenses (aggregated from 8 fields)
    direct_expense_fields = [
        'direct_wages', 'vehicle_operating_expenses',
        'packing_warehouse_supplies', 'oo_exp_intra_state',
        'oo_inter_state', 'oo_oi', 'oo_packing', 'oo_other'
    ]

    dir_exp_2024 = sum(record_2024.get(field, 0) or 0 for field in direct_expense_fields)
    dir_exp_2023 = sum(record_2023.get(field, 0) or 0 for field in direct_expense_fields)

    if dir_exp_2023 != 0:
        results['Direct Expenses'] = ((dir_exp_2024 - dir_exp_2023) / abs(dir_exp_2023)) * 100
    else:
        results['Direct Expenses'] = 0.0

    # Gross Profit (single field from Airtable)
    gp_2024 = record_2024.get('gross_profit', 0) or 0
    gp_2023 = record_2023.get('gross_profit', 0) or 0

    if gp_2023 != 0:
        results['Gross Profit'] = ((gp_2024 - gp_2023) / abs(gp_2023)) * 100
    else:
        results['Gross Profit'] = 0.0

    # Operating Expenses
    op_exp_2024 = record_2024.get('total_operating_expenses', 0) or 0
    op_exp_2023 = record_2023.get('total_operating_expenses', 0) or 0

    if op_exp_2023 != 0:
        results['Operating Expenses'] = ((op_exp_2024 - op_exp_2023) / abs(op_exp_2023)) * 100
    else:
        results['Operating Expenses'] = 0.0

    # Operating Income (EBITDA)
    ebitda_2024 = record_2024.get('ebitda', 0) or 0
    ebitda_2023 = record_2023.get('ebitda', 0) or 0

    if ebitda_2023 != 0:
        results['Operating Income'] = ((ebitda_2024 - ebitda_2023) / abs(ebitda_2023)) * 100
    else:
        results['Operating Income'] = 0.0

    return results
```

### Example Output

```python
{
    'Total Revenue': 12.3,
    'Direct Expenses': 8.5,
    'Gross Profit': 3.5,
    'Operating Expenses': 15.7,
    'Operating Income': 20.1
}
```

---

## Multi-Year Trends (2021-2024)

### Implementation

```python
def calculate_multi_year_yoy(company_name):
    """Calculate YoY for each year from 2021-2024"""
    airtable = get_airtable_connection()

    years = ['2020', '2021', '2022', '2023', '2024']
    annual_data = {}

    # Fetch all years
    for year in years:
        period = f"{year} Annual"
        data = airtable.get_income_statement_data_by_period(company_name, period)
        if data and len(data) > 0:
            annual_data[year] = data[0]

    results = {}

    # Calculate YoY for 2021, 2022, 2023, 2024
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

        # Repeat for other metrics...

        results[current_year] = year_changes

    return results
```

### Example Output

```python
{
    '2021': {
        'Total Revenue': 5.2,
        'Direct Expenses': 3.1,
        'Gross Profit': 8.5,
        'Operating Expenses': 4.2,
        'Operating Income': 12.8
    },
    '2022': {
        'Total Revenue': -2.1,
        'Direct Expenses': 1.5,
        'Gross Profit': 3.5,  # ← The 3.5% you asked about
        'Operating Expenses': 5.8,
        'Operating Income': -5.4
    },
    '2023': {
        'Total Revenue': 8.5,
        'Direct Expenses': 7.2,
        'Gross Profit': 10.2,
        'Operating Expenses': 9.1,
        'Operating Income': 15.7
    },
    '2024': {
        'Total Revenue': 12.3,
        'Direct Expenses': 8.9,
        'Gross Profit': 18.5,
        'Operating Expenses': 15.2,
        'Operating Income': 20.1
    }
}
```

---

## The Ace 2022 Example Explained

### The Question

"Why does Ace show 3.5% Gross Profit growth in 2022 when other metrics are different?"

### The Data

```python
# From Airtable
Ace 2021 Gross Profit: $1,324,217
Ace 2022 Gross Profit: $1,370,128
```

### The Calculation

```python
gp_2022 = 1370128
gp_2021 = 1324217

yoy = ((1370128 - 1324217) / 1324217) * 100
yoy = (45911 / 1324217) * 100
yoy = 0.03467 * 100
yoy = 3.467%
yoy ≈ 3.5%  # Rounded to 1 decimal
```

### Why It Makes Sense

**Gross Profit Formula:**
```
Gross Profit = Total Revenue - Direct Expenses
```

If:
- Revenue grew 10%
- Direct Expenses also grew ~10%
- Then Gross Profit growth would be small!

**Example:**

```python
# 2021
Revenue: $10,000,000
Direct Exp: $8,675,783
Gross Profit: $1,324,217

# 2022
Revenue: $11,000,000 (+10%)
Direct Exp: $9,629,872 (+11%)
Gross Profit: $1,370,128 (+3.5%)
```

**Insight:** Even though revenue grew, expenses grew faster, compressing gross profit growth!

---

## Color-Coded Table

### Color Logic

```python
def get_cell_color(value):
    """Color based on YoY percentage"""
    if value is None:
        return '#f8f9fa'  # Light gray (no data)
    elif value > 5:
        return '#d4edda'  # Green (good growth)
    elif value < -5:
        return '#f8d7da'  # Red (decline)
    else:
        return '#fff3cd'  # Yellow (moderate)
```

### Table HTML Generation

```python
# For each metric and year
for metric in metrics:
    for year in years:
        value = multi_year_data[year].get(metric, None)
        bg_color = get_cell_color(value)
        formatted_value = f'{value:.1f}%' if value is not None else '-'

        html += f'<td style="background-color: {bg_color}; text-align: center;">'
        html += f'{formatted_value}</td>'
```

### Visual Result

```
Metric               2021    2022    2023    2024
─────────────────────────────────────────────────
Total Revenue        5.2%    -2.1%   8.5%    12.3%
                    (green) (yellow)(green) (green)

Direct Expenses      3.1%    1.5%    7.2%    8.9%
                    (yellow)(yellow)(green) (green)

Gross Profit         8.5%    3.5%    10.2%   18.5%
                    (green) (yellow)(green) (green)
```

---

## Common Scenarios

### Scenario 1: Revenue Up, Profit Down

```python
Revenue YoY: +10%
Direct Exp YoY: +15%
Gross Profit YoY: -5%  # Red zone!
```

**Interpretation:** Expenses growing faster than revenue - margin compression

### Scenario 2: All Metrics Improving

```python
Revenue YoY: +12%
Direct Exp YoY: +8%
Gross Profit YoY: +20%  # Green zone!
```

**Interpretation:** Strong performance - revenue growing faster than costs

### Scenario 3: Recovery Year

```python
2021 Profit: -$100K
2022 Profit: $50K
YoY: +150%  # Green zone!
```

**Interpretation:** Turned profitable - large percentage gain

---

## Key Takeaways

✅ **YoY formula** handles positives, negatives, and transitions
✅ **Absolute value** in denominator prevents wrong signs
✅ **Division by zero** check required for all calculations
✅ **Gross Profit is NOT calculated** - comes directly from Airtable
✅ **Direct Expenses aggregated** from 8 separate fields
✅ **Color coding** provides visual insight (>5% green, <-5% red)
✅ **Multi-year trends** show patterns over time

---

## Practice Exercise

Calculate YoY for this scenario:

```python
Company: Winter
2023 Revenue: $8,500,000
2024 Revenue: $9,350,000

What is the YoY percentage?
```

<details>
<summary>Show Solution</summary>

```python
rev_2024 = 9350000
rev_2023 = 8500000

yoy = ((9350000 - 8500000) / 8500000) * 100
yoy = (850000 / 8500000) * 100
yoy = 0.10 * 100
yoy = 10.0%

# Interpretation: 10% revenue growth (green zone)
```

</details>

---

*Understanding YoY calculations is essential for financial analysis - you now know exactly how it works! 📈*
