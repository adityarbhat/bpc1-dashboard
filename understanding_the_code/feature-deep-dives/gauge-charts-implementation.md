# Feature Deep Dive: Gauge Charts Implementation

## Overview

This deep dive provides a complete walkthrough of the semicircular gauge chart implementation in the BPC Dashboard. You'll get the full mathematical breakdown, design decisions, and implementation details for creating professional financial gauge charts.

**What You'll Learn:**
- Complete mathematical breakdown of gauge positioning
- Needle indicator algorithm
- Zone threshold calculations with dynamic ranges
- Performance range color coding
- Real-world usage in Company Ratios page

**Difficulty:** Advanced
**Time:** 45-60 minutes

---

## The Design Challenge

### Requirements

Create gauge charts that:
1. ✅ Show semicircular "speedometer" design
2. ✅ Have three color zones (Red/Yellow/Green)
3. ✅ Display a needle pointing to current value
4. ✅ Handle values outside expected range gracefully
5. ✅ Color-code the displayed value
6. ✅ Support "reverse" metrics (lower is better)
7. ✅ Format values appropriately (%, $, ratio)

### Visual Blueprint

```
        Green Zone (70-100)
       /                  \
   Yellow Zone          Yellow Zone
     (30-70)            (30-70)
    /                        \
Red Zone                   Red Zone
 (0-30)                     (0-30)
  |                            |
  0          Needle → 75      100
              ↓
           [75.0%]  ← Color-coded value
```

---

## Complete Function Breakdown

### Function Signature

```python
def create_gauge_chart(
    value,                    # Required: The actual value
    title,                    # Required: Chart title
    min_val=0,               # Optional: Range minimum
    max_val=100,             # Optional: Range maximum
    threshold_red=30,        # Optional: Red→Yellow boundary
    threshold_yellow=70,     # Optional: Yellow→Green boundary
    format_type="percent",   # Optional: Display format
    reverse_colors=False     # Optional: Invert color logic
):
```

---

## Step 1: Input Validation and Edge Cases

### Handling None Values

```python
# Handle None or invalid values
if value is None:
    value = min_val
```

**Why?**

Missing data shouldn't crash the app. Default to minimum value for safe display.

**Example:**

```python
create_gauge_chart(value=None, ...)
# Becomes: value = 0 (if min_val = 0)
```

---

## Step 2: Dynamic Range Extension (The Math)

### The Problem

Value might exceed expected range:

```python
# Expected: 0-100
# Actual: 125 ← Goes off the chart!
```

### The Solution: Proportional Range Extension

```python
# Extend range if value is outside of min/max bounds
if value < min_val:
    padding = abs(value - min_val) * 0.2
    actual_min = value - padding
else:
    actual_min = min_val

if value > max_val:
    padding = abs(value - max_val) * 0.2
    actual_max = value + padding
else:
    actual_max = max_val
```

### Mathematical Example

**Scenario 1: Value exceeds maximum**

```python
min_val = 0
max_val = 100
value = 125

# Calculate padding
padding = abs(125 - 100) * 0.2
padding = 25 * 0.2
padding = 5

# New maximum
actual_max = 125 + 5 = 130

# Result: Range extends from 0-100 to 0-130
```

**Scenario 2: Value below minimum**

```python
min_val = 0
max_val = 2.0
value = -0.5  # Negative debt-to-equity (rare but possible)

# Calculate padding
padding = abs(-0.5 - 0) * 0.2
padding = 0.5 * 0.2
padding = 0.1

# New minimum
actual_min = -0.5 - 0.1 = -0.6

# Result: Range extends from 0-2.0 to -0.6-2.0
```

**Why 20% Padding?**

- Ensures needle isn't at absolute edge (better visibility)
- Provides visual breathing room
- Tested to look good across various ranges

---

## Step 3: Proportional Zone Mapping

### The Challenge

When range extends, color zones must scale proportionally!

**Original Setup:**
```
Range: 0-100
Red zone: 0-30 (30% of range)
Yellow zone: 30-70 (40% of range)
Green zone: 70-100 (30% of range)
```

**Extended Range:**
```
Range: 0-130
Zones should maintain proportions:
Red: 0-39 (30% of 130)
Yellow: 39-91 (40% of 130)
Green: 91-130 (30% of 130)
```

### Implementation

```python
total_range = actual_max - actual_min
original_range = max_val - min_val

if total_range > original_range:
    # Calculate proportion of original range for each threshold
    red_proportion = (threshold_red - min_val) / original_range
    yellow_proportion = (threshold_yellow - min_val) / original_range

    # Map to new range
    adjusted_threshold_red = actual_min + (red_proportion * total_range)
    adjusted_threshold_yellow = actual_min + (yellow_proportion * total_range)
else:
    adjusted_threshold_red = threshold_red
    adjusted_threshold_yellow = threshold_yellow
```

### Step-by-Step Calculation

```python
# Original
min_val = 0
max_val = 100
threshold_red = 30
threshold_yellow = 70

# Extended (value = 125)
actual_min = 0
actual_max = 130
total_range = 130 - 0 = 130
original_range = 100 - 0 = 100

# Calculate proportions
red_proportion = (30 - 0) / 100 = 0.30 (30%)
yellow_proportion = (70 - 0) / 100 = 0.70 (70%)

# Map to new range
adjusted_threshold_red = 0 + (0.30 × 130) = 39
adjusted_threshold_yellow = 0 + (0.70 × 130) = 91

# Result:
# Red zone: 0-39
# Yellow zone: 39-91
# Green zone: 91-130
```

---

## Step 4: Color Determination Logic

### Normal Metrics (Higher is Better)

```python
if value <= threshold_red:
    value_color = "#dc3545"  # Red (bad)
    zone = "red"
elif value <= threshold_yellow:
    value_color = "#ffc107"  # Yellow (caution)
    zone = "yellow"
else:
    value_color = "#28a745"  # Green (great!)
    zone = "green"
```

**Example: Current Ratio**

```python
threshold_red = 1.0
threshold_yellow = 1.5

value = 0.8  → Red (< 1.0 - poor liquidity)
value = 1.2  → Yellow (1.0-1.5 - moderate)
value = 1.8  → Green (> 1.5 - excellent!)
```

### Reverse Metrics (Lower is Better)

```python
if reverse_colors:
    if value < 0:
        value_color = "#dc3545"  # Red (very bad - negative)
        zone = "red"
    elif value <= threshold_red:
        value_color = "#28a745"  # Green (good - low value)
        zone = "green"
    elif value <= threshold_yellow:
        value_color = "#ffc107"  # Yellow (moderate)
        zone = "yellow"
    else:
        value_color = "#dc3545"  # Red (bad - high value)
        zone = "red"
```

**Example: Debt-to-Equity**

```python
threshold_red = 0.5
threshold_yellow = 1.0
reverse_colors = True

value = 0.3  → Green (< 0.5 - low debt, good!)
value = 0.7  → Yellow (0.5-1.0 - moderate debt)
value = 1.5  → Red (> 1.0 - high debt, risky!)
value = -0.2 → Red (negative - very unusual, bad!)
```

---

## Step 5: Value Formatting

### Format Type Options

```python
if format_type == "percent":
    display_value = f"{value:.1f}%"
elif format_type == "ratio":
    display_value = f"{value:.2f}"
elif format_type == "currency":
    display_value = f"${value:,.0f}"
elif format_type == "currency_k":
    display_value = f"${value:.0f}K"
elif format_type == "currency_auto":
    if value >= 1000000:
        display_value = f"${value/1000000:.2f}M"
    elif value >= 1000:
        display_value = f"${value/1000:.2f}K"
    else:
        display_value = f"${value:.0f}"
else:
    display_value = f"{value:.1f}"
```

### Real Examples

```python
# Percent
value = 15.789, format_type = "percent"
→ "15.8%"

# Ratio
value = 1.567, format_type = "ratio"
→ "1.57"

# Currency Auto
value = 750, format_type = "currency_auto"
→ "$750"

value = 15250, format_type = "currency_auto"
→ "$15.25K"

value = 2500000, format_type = "currency_auto"
→ "$2.50M"
```

---

## Step 6: Creating the Plotly Gauge

### The Indicator Configuration

```python
fig = go.Figure(go.Indicator(
    mode = "gauge",
    value = value,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {
        'text': f"<b>{title}</b>",
        'font': {'size': 12, 'color': '#1a202c', 'family': 'Montserrat'}
    },
    gauge = {
        # Configuration below
    }
))
```

### Gauge Axis Setup

```python
'axis': {
    'range': [actual_min, actual_max],  # Extended range
    'tickwidth': 1,
    'tickcolor': "#4a5568",
    'tickfont': {'size': 10, 'color': '#4a5568'},
    'showticklabels': True
}
```

**What This Creates:**

```
0    25    50    75    100  ← Tick labels
|     |     |     |     |
```

### Progress Bar (Needle Effect)

```python
'bar': {
    'color': '#000000',     # Black
    'thickness': 0.08,      # 8% of gauge height
    'line': {
        'color': '#000000',
        'width': 1
    }
}
```

**Visual Effect:**

The bar fills from start to current value, creating a progress indicator.

### Color Zone Steps

```python
'steps': [
    {
        'range': [actual_min, adjusted_threshold_red],
        'color': '#ff4444'  # Bright red
    },
    {
        'range': [adjusted_threshold_red, adjusted_threshold_yellow],
        'color': '#ffcc00'  # Bright yellow
    },
    {
        'range': [adjusted_threshold_yellow, actual_max],
        'color': '#00cc44'  # Bright green
    }
]
```

**Why Bright Colors?**

Background zones use brighter shades for visibility. Value text uses darker Bootstrap colors for readability.

### The Needle (Threshold Line)

```python
'threshold': {
    'line': {'color': "#000000", 'width': 4},  # Thick black line
    'thickness': 1.0,
    'value': value
}
```

**This creates the speedometer needle** pointing to the current value!

### Gauge Shape

```python
'shape': 'angular'  # Semicircle
```

---

## Step 7: Value Annotation

```python
fig.add_annotation(
    x=0.5,  # Center horizontally
    y=0.05, # Near bottom
    text=f"<b>{display_value}</b>",
    showarrow=False,
    font=dict(size=20, color=value_color, family='Montserrat'),
    xref="paper",  # Use paper coordinates (0-1)
    yref="paper"
)
```

**Coordinate System:**

```
(0,1) ─────────────── (1,1)
  │                      │
  │    (0.5, 0.5)        │  ← Center
  │        ●             │
  │                      │
(0,0) ─────────────── (1,0)
           (0.5, 0.05) ← Value position
```

---

## Step 8: Layout Configuration

```python
fig.update_layout(
    height=180,  # Consistent sizing
    font={'color': "#4a5568", 'family': "Montserrat", 'size': 10},
    paper_bgcolor='rgba(0,0,0,0)',  # Transparent
    plot_bgcolor='rgba(0,0,0,0)',   # Transparent
    margin=dict(l=20, r=20, t=60, b=20)
)
```

**Layout Decisions:**

- **Height 180px**: Consistent across all gauges
- **Transparent background**: Blends with Streamlit
- **Montserrat font**: Matches dashboard branding
- **Margins**: Prevents label clipping

---

## Real-World Usage Example

### Company Ratios Page

```python
# File: pages/company_pages/company_ratios.py

from shared.chart_utils import create_gauge_chart

# Fetch data from Airtable
balance_data = airtable.get_balance_sheet_data(company_name)
current_ratio = balance_data[0].get('current_ratio', 0)

# Create gauge
col1, col2, col3, col4 = st.columns(4)

with col1:
    fig = create_gauge_chart(
        value=current_ratio,
        title="Current Ratio",
        min_val=0,
        max_val=3,
        threshold_red=1.0,
        threshold_yellow=1.5,
        format_type="ratio",
        reverse_colors=False
    )
    st.plotly_chart(fig, use_container_width=True)
```

### All 8 Ratios Configuration

```python
# Balance Sheet Ratios
ratios = [
    {
        'value': current_ratio,
        'title': 'Current Ratio',
        'min': 0, 'max': 3,
        'red': 1.0, 'yellow': 1.5,
        'format': 'ratio',
        'reverse': False
    },
    {
        'value': debt_to_equity,
        'title': 'Debt to Equity',
        'min': 0, 'max': 2,
        'red': 0.5, 'yellow': 1.0,
        'format': 'ratio',
        'reverse': True  # Lower is better!
    },
    # ... more ratios
]

# Display in grid
cols = st.columns(4)
for i, ratio in enumerate(ratios):
    with cols[i % 4]:
        fig = create_gauge_chart(
            value=ratio['value'],
            title=ratio['title'],
            min_val=ratio['min'],
            max_val=ratio['max'],
            threshold_red=ratio['red'],
            threshold_yellow=ratio['yellow'],
            format_type=ratio['format'],
            reverse_colors=ratio['reverse']
        )
        st.plotly_chart(fig, use_container_width=True)
```

---

## Design Decisions & Rationale

### Why Semicircular?

✅ **Familiar metaphor** - Like car speedometer
✅ **Space efficient** - Fits more gauges per row
✅ **Clear zones** - Easy to see performance ranges
✅ **Professional** - Common in financial dashboards

### Why Black Needle?

✅ **Maximum contrast** - Visible on all background colors
✅ **Precision** - Stands out from colored zones
✅ **Traditional** - Matches analog gauge design

### Why Three Zones?

✅ **Simple categorization** - Bad/OK/Good
✅ **Traffic light metaphor** - Universally understood
✅ **Not overwhelming** - More zones = confusion

### Why 20% Padding?

✅ **Tested extensively** - Looks good at all scales
✅ **Not too much** - Doesn't distort proportions
✅ **Not too little** - Prevents edge clipping

---

## Key Takeaways

✅ **Dynamic range extension** handles unexpected values
✅ **Proportional zone mapping** maintains visual consistency
✅ **Reverse color logic** supports "lower is better" metrics
✅ **Smart formatting** adapts to value magnitude
✅ **Needle indicator** provides precise value location
✅ **Color-coded value** reinforces performance assessment
✅ **Professional styling** matches financial dashboard standards

---

## Practice Exercise

**Challenge:** Create a custom gauge for a new metric

**Task:** Implement a gauge for "Days Sales Outstanding (DSO)"

**Requirements:**
- Lower is better (reverse colors)
- Great: < 30 days (green)
- Caution: 30-60 days (yellow)
- Improve: > 60 days (red)
- Range: 0-90 days
- Format: Show as number with "days" suffix

<details>
<summary>Show Solution</summary>

```python
def create_dso_gauge(dso_value):
    """Create DSO gauge with custom formatting"""
    # Create gauge
    fig = create_gauge_chart(
        value=dso_value,
        title="Days Sales Outstanding",
        min_val=0,
        max_val=90,
        threshold_red=30,      # Below 30 is green (reversed)
        threshold_yellow=60,    # 30-60 is yellow
        format_type="ratio",    # Use ratio (we'll customize display)
        reverse_colors=True     # Lower is better!
    )

    # Add custom "days" suffix to annotation
    # (Would need to modify create_gauge_chart to support this)
    # Or display separately:
    st.caption(f"{dso_value:.0f} days")

    return fig

# Usage
dso = 45  # 45 days
fig = create_dso_gauge(dso)
st.plotly_chart(fig, use_container_width=True)
```

</details>

---

## Related Topics

- **[04-plotly-visualizations.md](../04-plotly-visualizations.md)** - General Plotly concepts
- **[06-data-transformation.md](../06-data-transformation.md)** - Preparing data for gauges

---

*You now understand the complete implementation of professional gauge charts! 🎯*
