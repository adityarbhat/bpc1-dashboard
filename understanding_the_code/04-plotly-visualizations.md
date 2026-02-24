# 04: Plotly Visualizations

## Overview

Learn how to create professional, interactive visualizations using Plotly in Streamlit. This guide focuses on the sophisticated gauge charts used in the BPC Dashboard and other visualization patterns. By the end, you'll understand:

- Plotly basics and integration with Streamlit
- The semicircular gauge chart design and mathematics
- Needle positioning algorithm for gauge indicators
- Color zones and performance thresholds
- Dynamic value formatting (currency, percentages, ratios)
- Bar charts with group comparisons
- Custom hover templates
- Branding and styling

**Estimated Time:** 60-75 minutes

---

## Why Plotly?

### Plotly vs Other Visualization Libraries

| Feature | Plotly | Matplotlib | Altair |
|---------|--------|------------|--------|
| **Interactivity** | ✅ Built-in | ❌ Static | ✅ Good |
| **Streamlit Integration** | ✅ Excellent | ✅ Good | ✅ Good |
| **Customization** | ✅ Highly flexible | ✅ Flexible | ⚠️ Limited |
| **Gauge Charts** | ✅ Native support | ❌ Complex DIY | ❌ Not available |
| **Performance** | ✅ Fast | ✅ Fast | ✅ Fast |
| **Learning Curve** | ⚠️ Moderate | ⚠️ Steep | ✅ Gentle |

**BPC Dashboard Choice:** Plotly for gauge charts and interactive features

---

## Plotly Basics

### Installation

```bash
pip install plotly
```

### Basic Plotly Chart in Streamlit

```python
import streamlit as st
import plotly.graph_objects as go

# Create a simple bar chart
fig = go.Figure(data=[
    go.Bar(x=['A', 'B', 'C'], y=[10, 20, 15])
])

# Display in Streamlit
st.plotly_chart(fig, use_container_width=True)
```

**Key Components:**

1. **`go.Figure()`** - Creates the chart container
2. **`go.Bar()`** - Adds bar chart trace (data series)
3. **`st.plotly_chart()`** - Renders in Streamlit
4. **`use_container_width=True`** - Makes chart responsive

### Graph Objects vs Express

**Two Plotly APIs:**

#### 1. Plotly Express (High-Level, Simple)

```python
import plotly.express as px
import pandas as pd

df = pd.DataFrame({
    'company': ['Coastal', 'Ace', 'Winter'],
    'revenue': [1000, 850, 920]
})

fig = px.bar(df, x='company', y='revenue')
st.plotly_chart(fig)
```

**Pros:** Quick, easy, good defaults
**Cons:** Less customization

#### 2. Graph Objects (Low-Level, Powerful)

```python
import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Bar(
        x=['Coastal', 'Ace', 'Winter'],
        y=[1000, 850, 920],
        marker=dict(color='#025a9a'),
        text=[1000, 850, 920],
        textposition='outside'
    )
])

fig.update_layout(
    title='Company Revenue',
    xaxis_title='Company',
    yaxis_title='Revenue ($K)'
)

st.plotly_chart(fig)
```

**Pros:** Full control, unlimited customization
**Cons:** More verbose

**BPC Dashboard uses Graph Objects** for maximum control over gauge design.

---

## The Gauge Chart: Design Overview

### What We're Building

The BPC Dashboard features **semicircular gauge charts** with:

1. **Three color zones** (Red/Yellow/Green)
2. **Needle indicator** (speedometer-style)
3. **Threshold lines** separating zones
4. **Color-coded value display**
5. **Dynamic range adjustment** for extreme values
6. **Professional styling** matching Atlas brand

**Visual Structure:**

```
         Green Zone (Good)
        /              \
   Yellow Zone      Yellow Zone
     (Caution)      (Caution)
    /                    \
Red Zone                Red Zone
 (Improve)              (Improve)
   |                      |
  Min                    Max
        ↑
      Needle

  [Color-coded Value]
```

---

## Gauge Chart: Function Signature

```python
def create_gauge_chart(
    value,              # The actual value to display
    title,              # Chart title
    min_val=0,          # Minimum range value
    max_val=100,        # Maximum range value
    threshold_red=30,   # Red/Yellow boundary
    threshold_yellow=70, # Yellow/Green boundary
    format_type="percent", # How to format the value
    reverse_colors=False   # Reverse color logic (for metrics where lower is better)
):
```

**Parameter Examples:**

```python
# Current Ratio gauge
create_gauge_chart(
    value=1.75,
    title="Current Ratio",
    min_val=0,
    max_val=3,
    threshold_red=1.0,
    threshold_yellow=1.5,
    format_type="ratio",
    reverse_colors=False  # Higher is better
)

# Debt-to-Equity gauge
create_gauge_chart(
    value=0.82,
    title="Debt to Equity",
    min_val=0,
    max_val=2,
    threshold_red=0.5,
    threshold_yellow=1.0,
    format_type="ratio",
    reverse_colors=True  # Lower is better!
)
```

---

## Step-by-Step Gauge Chart Implementation

### Step 1: Handle Edge Cases

```python
# Handle None or invalid values
if value is None:
    value = min_val
```

**Why?**

If data is missing, default to minimum to avoid crashes.

```python
# Without this check
value = None
display_value = f"{value:.1f}%"  # TypeError: unsupported format string

# With check
if value is None:
    value = min_val  # Now safe to format
```

### Step 2: Dynamic Range Extension

**Problem:**

What if actual value exceeds your min/max range?

```python
# Gauge range: 0-100
# Actual value: 125 (outside range!)
# Without handling: Needle goes off the chart!
```

**Solution: Extend Range Dynamically**

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

**Example:**

```
Original range: 0-100
Value: 125
Padding: (125 - 100) × 0.2 = 5
New range: 0-130

Result: Value fits comfortably in extended range!
```

**Why 20% Padding?**

Ensures needle isn't at absolute edge - looks better and more readable.

### Step 3: Proportional Zone Mapping

**Challenge:**

If range extends, color zones need to scale proportionally!

```
Original range: 0-100
Zones: Red 0-30, Yellow 30-70, Green 70-100

Extended range: 0-130
Zones should be: Red 0-39, Yellow 39-91, Green 91-130
```

**Solution:**

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
    # No extension needed
    adjusted_threshold_red = threshold_red
    adjusted_threshold_yellow = threshold_yellow
```

**Math Example:**

```
Original: 0-100, Red threshold at 30
Red proportion: (30 - 0) / (100 - 0) = 0.3 (30%)

Extended: 0-130
New red threshold: 0 + (0.3 × 130) = 39

Result: Red zone still occupies 30% of range!
```

### Step 4: Value Color Determination

```python
# Determine value color based on thresholds
if reverse_colors:
    # For metrics where LOWER is better (e.g., Debt-to-Equity)
    if value < 0:
        value_color = "#dc3545"  # Red (very bad)
        zone = "red"
    elif value <= threshold_red:
        value_color = "#28a745"  # Green (good!)
        zone = "green"
    elif value <= threshold_yellow:
        value_color = "#ffc107"  # Yellow (caution)
        zone = "yellow"
    else:
        value_color = "#dc3545"  # Red (bad)
        zone = "red"
else:
    # Normal metrics where HIGHER is better
    if value <= threshold_red:
        value_color = "#dc3545"  # Red (improve)
        zone = "red"
    elif value <= threshold_yellow:
        value_color = "#ffc107"  # Yellow (caution)
        zone = "yellow"
    else:
        value_color = "#28a745"  # Green (great!)
        zone = "green"
```

**Color Codes (Bootstrap-inspired):**

| Color | Hex Code | Meaning |
|-------|----------|---------|
| Red | `#dc3545` | Bad/Improve |
| Yellow | `#ffc107` | Caution/OK |
| Green | `#28a745` | Good/Great |

**Reverse Colors Example:**

```python
# Debt-to-Equity: Lower is better
threshold_red = 0.5
threshold_yellow = 1.0

value = 0.3  → Green (good! low debt)
value = 0.7  → Yellow (moderate debt)
value = 1.5  → Red (high debt, risky)
```

### Step 5: Value Formatting

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
    # Dynamic formatting based on magnitude
    if value >= 10001000:
        display_value = f"${value/1000000:.2f}M"
    elif value >= 1000:
        display_value = f"${value/1000:.2f}K"
    else:
        display_value = f"${value:.0f}"
else:
    display_value = f"{value:.1f}"
```

**Format Examples:**

| Input | Format Type | Output |
|-------|-------------|--------|
| 15.789 | `percent` | `15.8%` |
| 1.567 | `ratio` | `1.57` |
| 1234567 | `currency` | `$1,234,567` |
| 1500 | `currency_k` | `$1500K` |
| 750 | `currency_auto` | `$750` |
| 1500 | `currency_auto` | `$1.50K` |
| 2500000 | `currency_auto` | `$2.50M` |

**Why `currency_auto`?**

Keeps display clean - shows appropriate units based on value size!

---

## Step 6: Creating the Gauge

### The Core Plotly Indicator

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
        # ... gauge configuration
    }
))
```

**Key Parameters:**

| Parameter | Purpose | Value |
|-----------|---------|-------|
| `mode` | Type of indicator | `"gauge"` |
| `value` | Actual value to display | The input value |
| `domain` | Position in figure | `{'x': [0, 1], 'y': [0, 1]}` (full space) |
| `title` | Chart title | Formatted with HTML bold |

### Gauge Axis Configuration

```python
'axis': {
    'range': [actual_min, actual_max],
    'tickwidth': 1,
    'tickcolor': "#4a5568",
    'tickfont': {'size': 10, 'color': '#4a5568'},
    'showticklabels': True
}
```

**What This Does:**

- **Range**: Sets min/max values for gauge scale
- **Tick styling**: Gray color, small font (professional look)
- **Labels**: Shows scale numbers (0, 50, 100, etc.)

### Progress Bar (The "Needle" Effect)

```python
'bar': {
    'color': '#000000',    # Black
    'thickness': 0.08,     # Thin (8% of gauge height)
    'line': {
        'color': '#000000',
        'width': 1
    }
}
```

**Visual Effect:**

```
Before needle reached value:  ░░░░░░░░░░
After needle reaches 75%:     ████████░░
                                      ↑ needle tip
```

### Color Zone Steps

```python
'steps': [
    {
        'range': [actual_min, adjusted_threshold_red],
        'color': '#ff4444'  # Red zone
    },
    {
        'range': [adjusted_threshold_red, adjusted_threshold_yellow],
        'color': '#ffcc00'  # Yellow zone
    },
    {
        'range': [adjusted_threshold_yellow, actual_max],
        'color': '#00cc44'  # Green zone
    }
]
```

**Zone Colors (Bright for background):**

| Zone | Color | Hex | Purpose |
|------|-------|-----|---------|
| Red | Bright Red | `#ff4444` | "Improve" range |
| Yellow | Bright Yellow | `#ffcc00` | "Caution" range |
| Green | Bright Green | `#00cc44` | "Great" range |

**Why Different from Value Colors?**

- **Zone colors**: Bright, for background visibility
- **Value colors**: Darker Bootstrap colors for text readability

### The Threshold Needle

```python
'threshold': {
    'line': {'color': "#000000", 'width': 4},
    'thickness': 1.0,
    'value': value
}
```

**What This Creates:**

A thick black line (the "needle") pointing to the current value!

```
      ↙ Needle (black line)
      |
   ███|░░░
   ███|░░░
Red  Y  Green
```

### Gauge Shape

```python
'shape': 'angular'
```

**Options:**

| Shape | Appearance |
|-------|------------|
| `'angular'` | Semicircle (what we use) |
| `'bullet'` | Linear horizontal |

---

## Step 7: Value Annotation

```python
fig.add_annotation(
    x=0.5, y=0.05,  # Center bottom
    text=f"<b>{display_value}</b>",
    showarrow=False,
    font=dict(size=20, color=value_color, family='Montserrat'),
    xref="paper", yref="paper"
)
```

**Coordinate System:**

- **`xref="paper"`**: x=0 is left, x=1 is right
- **`yref="paper"`**: y=0 is bottom, y=1 is top
- **`x=0.5, y=0.05`**: Center horizontally, near bottom

**Result:**

```
    [Gauge]
      |
      ↓
   [1.75]  ← Color-coded value
```

**Color Matching:**

Value inherits `value_color` from Step 4 - matches the zone it's in!

---

## Step 8: Layout Configuration

```python
fig.update_layout(
    height=180,  # Fixed height
    font={'color': "#4a5568", 'family': "Montserrat", 'size': 10},
    paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
    plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot area
    margin=dict(l=20, r=20, t=60, b=20)  # Padding around chart
)
```

**Key Settings:**

| Setting | Value | Purpose |
|---------|-------|---------|
| `height` | 180 | Consistent size across all gauges |
| `font.family` | Montserrat | Matches dashboard branding |
| `paper_bgcolor` | Transparent | Blends with Streamlit background |
| `margin` | Custom | Prevents clipping of labels |

---

## Using the Gauge Chart

### Example 1: Current Ratio

```python
from shared.chart_utils import create_gauge_chart

# Fetch data
current_ratio = 1.75  # From Airtable

# Create gauge
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

# Display in Streamlit
st.plotly_chart(fig, use_container_width=True)
```

**Interpretation:**

- Value: 1.75
- Zone: Green (above 1.5 threshold)
- Display: "1.75" in green
- Meaning: Great liquidity!

### Example 2: Debt-to-Equity (Reverse)

```python
# Fetch data
debt_to_equity = 0.82

# Create gauge
fig = create_gauge_chart(
    value=debt_to_equity,
    title="Debt to Equity",
    min_val=0,
    max_val=2,
    threshold_red=0.5,   # Green zone is 0-0.5
    threshold_yellow=1.0, # Yellow zone is 0.5-1.0
    format_type="ratio",
    reverse_colors=True  # Lower is better!
)

st.plotly_chart(fig, use_container_width=True)
```

**Reverse Colors Effect:**

| Value Range | Normal Colors | Reverse Colors |
|-------------|---------------|----------------|
| 0 - 0.5 | Red (bad) | Green (good!) |
| 0.5 - 1.0 | Yellow | Yellow |
| 1.0+ | Green | Red (risky!) |

### Example 3: Currency Auto-Formatting

```python
# Revenue per employee
rev_per_employee = 15250  # $15,250

fig = create_gauge_chart(
    value=rev_per_employee,
    title="Revenue per Employee",
    min_val=0,
    max_val=100000,
    threshold_red=30000,
    threshold_yellow=50000,
    format_type="currency_auto"
)

# Display shows: "$15.25K"
```

---

## Bar Charts with Comparisons

### Basic Bar Chart

```python
import plotly.graph_objects as go

companies = ['Coastal', 'Ace', 'Winter', 'Hopkins']
revenues = [1000, 850, 920, 780]

fig = go.Figure(data=[
    go.Bar(
        x=companies,
        y=revenues,
        marker=dict(color='#025a9a'),
        text=[f'${r}K' for r in revenues],
        textposition='outside'
    )
])

fig.update_layout(
    title='Company Revenue Comparison',
    xaxis_title='Company',
    yaxis_title='Revenue ($K)',
    height=400,
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)
```

### Side-by-Side Comparison

```python
companies = ['Coastal', 'Ace', 'Winter']
company_values = [500, 420, 450]
group_avg_values = [400, 400, 400]

fig = go.Figure()

# Company bars
fig.add_trace(go.Bar(
    name='Company',
    x=companies,
    y=company_values,
    marker=dict(color='#025a9a'),
    text=[f'${v}K' for v in company_values],
    textposition='outside'
))

# Group average bars
fig.add_trace(go.Bar(
    name='Group Average',
    x=companies,
    y=group_avg_values,
    marker=dict(color='#0e9cd5'),
    text=[f'${v}K' for v in group_avg_values],
    textposition='outside'
))

fig.update_layout(
    title='Company vs Group Average',
    barmode='group',  # Side-by-side
    xaxis_title='Company',
    yaxis_title='Value ($K)',
    height=400
)

st.plotly_chart(fig, use_container_width=True)
```

---

## Custom Hover Templates

### Default Hover (Basic)

```python
fig = go.Figure(data=[
    go.Bar(x=['A', 'B'], y=[100, 200])
])
# Hover shows: "x: A, y: 100"
```

### Custom Hover Template

```python
fig = go.Figure(data=[
    go.Bar(
        x=['Coastal', 'Ace'],
        y=[1000, 850],
        customdata=[[1000, 950], [850, 920]],  # Additional data
        hovertemplate='<b>%{x}</b><br>' +
                      'Revenue: $%{y}K<br>' +
                      'Last Year: $%{customdata[0]}K<br>' +
                      'Growth: %{customdata[1]}%<br>' +
                      '<extra></extra>'
    )
])

# Hover shows:
# Coastal
# Revenue: $1000K
# Last Year: $950K
# Growth: 5.3%
```

**Template Variables:**

| Variable | Data Source |
|----------|-------------|
| `%{x}` | X-axis value |
| `%{y}` | Y-axis value |
| `%{customdata[0]}` | First custom data value |
| `%{customdata[1]}` | Second custom data value |
| `<extra></extra>` | Removes trace name from tooltip |

---

## Atlas Branding

### Color Palette

```python
ATLAS_COLORS = {
    'primary_blue': '#025a9a',
    'light_blue': '#0e9cd5',
    'red': '#c2002f',
    'dark_gray': '#1a202c',
    'medium_gray': '#4a5568',
    'light_gray': '#e2e8f0'
}
```

### Applying Brand Colors

```python
fig = go.Figure(data=[
    go.Bar(
        x=companies,
        y=values,
        marker=dict(color='#025a9a'),  # Atlas blue
    )
])

fig.update_layout(
    title={'text': '<b>Company Analysis</b>', 'font': {'family': 'Montserrat'}},
    font={'family': 'Montserrat', 'color': '#1a202c'},
    plot_bgcolor='white',
    paper_bgcolor='white'
)
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Gauge Value Outside Range

**Problem:**

```python
create_gauge_chart(value=150, min_val=0, max_val=100)
# Needle goes off the chart!
```

**Solution:**

Already handled in Step 2 - range extends automatically! ✅

### Pitfall 2: Wrong Format Type

**Problem:**

```python
create_gauge_chart(value=1.75, format_type="percent")
# Shows "1.8%" instead of "1.75"
```

**Solution:**

```python
create_gauge_chart(value=1.75, format_type="ratio")
# Shows "1.75" correctly
```

### Pitfall 3: Forgetting Reverse Colors

**Problem:**

```python
# Debt-to-Equity: 1.5 is BAD (high debt)
create_gauge_chart(value=1.5, reverse_colors=False)
# Shows GREEN (wrong!)
```

**Solution:**

```python
create_gauge_chart(value=1.5, reverse_colors=True)
# Shows RED (correct!)
```

### Pitfall 4: Not Using Container Width

**Problem:**

```python
st.plotly_chart(fig)
# Chart has fixed width, doesn't resize
```

**Solution:**

```python
st.plotly_chart(fig, use_container_width=True)
# Chart fills available space, responsive!
```

---

## Key Takeaways

✅ **Use Graph Objects** for full customization control
✅ **Handle edge cases** (None values, range extensions)
✅ **Proportional zone mapping** for consistent appearance
✅ **Reverse colors** for metrics where lower is better
✅ **Dynamic formatting** for clean value display
✅ **Custom hover templates** for rich interactivity
✅ **Brand consistency** with color palette and fonts
✅ **Container width** for responsive design

---

## Try It Yourself

### Exercise 1: Create a Simple Gauge

**Task:** Create a gauge showing a percentage score

<details>
<summary>Show Solution</summary>

```python
import streamlit as st
from shared.chart_utils import create_gauge_chart

st.title("Student Test Score")

score = st.slider("Test Score", 0, 100, 75)

fig = create_gauge_chart(
    value=score,
    title="Test Score",
    min_val=0,
    max_val=100,
    threshold_red=60,    # Below 60 is failing
    threshold_yellow=80,  # 60-80 is passing
    format_type="percent",
    reverse_colors=False  # Higher is better
)

st.plotly_chart(fig, use_container_width=True)

if score >= 80:
    st.success("Excellent work!")
elif score >= 60:
    st.info("Good job!")
else:
    st.warning("Needs improvement")
```

</details>

### Exercise 2: Comparison Bar Chart

**Task:** Create a side-by-side bar chart comparing two metrics

<details>
<summary>Show Solution</summary>

```python
import streamlit as st
import plotly.graph_objects as go

companies = ['Company A', 'Company B', 'Company C']
revenue_2023 = [500, 650, 580]
revenue_2024 = [550, 700, 620]

fig = go.Figure()

fig.add_trace(go.Bar(
    name='2023',
    x=companies,
    y=revenue_2023,
    marker=dict(color='#4a5568')
))

fig.add_trace(go.Bar(
    name='2024',
    x=companies,
    y=revenue_2024,
    marker=dict(color='#025a9a')
))

fig.update_layout(
    title='Revenue Comparison: 2023 vs 2024',
    barmode='group',
    xaxis_title='Company',
    yaxis_title='Revenue ($K)',
    height=400,
    font=dict(family='Montserrat')
)

st.plotly_chart(fig, use_container_width=True)
```

</details>

### Exercise 3: Custom Hover Template

**Task:** Add a hover template showing percentage change

<details>
<summary>Show Solution</summary>

```python
import streamlit as st
import plotly.graph_objects as go

companies = ['Company A', 'Company B', 'Company C']
current = [550, 700, 620]
previous = [500, 650, 580]

# Calculate percentage change
pct_change = [((c - p) / p * 100) for c, p in zip(current, previous)]

fig = go.Figure(data=[
    go.Bar(
        x=companies,
        y=current,
        marker=dict(color='#025a9a'),
        customdata=list(zip(previous, pct_change)),
        hovertemplate='<b>%{x}</b><br>' +
                      'Current: $%{y}K<br>' +
                      'Previous: $%{customdata[0]}K<br>' +
                      'Change: %{customdata[1]:.1f}%<br>' +
                      '<extra></extra>'
    )
])

fig.update_layout(
    title='Revenue with YoY Change',
    xaxis_title='Company',
    yaxis_title='Revenue ($K)',
    height=400
)

st.plotly_chart(fig, use_container_width=True)
```

</details>

---

## Related Topics

- **[feature-deep-dives/gauge-charts-implementation.md](feature-deep-dives/gauge-charts-implementation.md)** - Complete gauge chart deep dive
- **[05-reusable-components.md](05-reusable-components.md)** - Building a chart component library
- **[06-data-transformation.md](06-data-transformation.md)** - Preparing data for visualization

---

## Next Steps

Now that you understand Plotly visualizations, move on to **[05-reusable-components.md](05-reusable-components.md)** to learn how to build a library of reusable UI components!

---

*Remember: Great visualizations tell a story - make your data speak clearly and beautifully! 📊*
