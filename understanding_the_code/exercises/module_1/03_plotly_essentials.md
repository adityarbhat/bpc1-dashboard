# Exercise 03: Display Ratio as Gauge Chart

## Goal

Replace the plain metric with a color-coded gauge chart.

---

## Task

Create a gauge that shows:
- Current ratio value with needle
- Color zones: Red (< 1.5), Yellow (1.5-2.4), Green (> 2.4)
- Value displayed below

```
        ╭─────────────╮
       /   GREEN      \
      /  ─────────────  \
     │  YELLOW │ needle │
      \  RED   ↓       /
       ╰───────────────╯
            2.15
```

---

<details>
<summary>Hint 1: Plotly Indicator Gauge</summary>

```python
import plotly.graph_objects as go

fig = go.Figure(go.Indicator(
    mode="gauge+number",     # Show gauge and number
    value=2.15,              # The value to display
    title={'text': "Current Ratio"},
    gauge={
        'axis': {'range': [0, 4]},  # Min and max of gauge
    }
))

st.plotly_chart(fig)
```

</details>

---

<details>
<summary>Hint 2: Add Color Zones (Steps)</summary>

```python
gauge={
    'axis': {'range': [0, 4]},
    'steps': [
        {'range': [0, 1.5], 'color': '#ff4444'},      # Red zone
        {'range': [1.5, 2.4], 'color': '#ffcc00'},    # Yellow zone
        {'range': [2.4, 4], 'color': '#00cc44'},      # Green zone
    ],
}
```

</details>

---

<details>
<summary>Hint 3: Add Needle (Threshold)</summary>

```python
gauge={
    'axis': {'range': [0, 4]},
    'steps': [...],
    'threshold': {
        'line': {'color': "black", 'width': 4},
        'thickness': 0.75,
        'value': 2.15  # Needle points here
    },
    'bar': {'color': "black", 'thickness': 0.1},  # Thin bar
}
```

</details>

---

<details>
<summary>Hint 4: Full Solution</summary>

```python
# mini_dashboard.py - Final Version
import streamlit as st
import plotly.graph_objects as go
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

# === Exercise 3: Gauge Chart ===
def create_gauge(value: float, title: str) -> go.Figure:
    """Create a color-coded gauge chart."""

    # Determine value color based on zones
    if value < 1.5:
        value_color = "#dc3545"  # Red
    elif value < 2.4:
        value_color = "#ffc107"  # Yellow
    else:
        value_color = "#28a745"  # Green

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'font': {'color': value_color, 'size': 40}},
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {
                'range': [0, 4],
                'tickwidth': 1,
                'tickcolor': "#666",
            },
            'bar': {'color': "black", 'thickness': 0.1},
            'steps': [
                {'range': [0, 1.5], 'color': '#ff4444'},
                {'range': [1.5, 2.4], 'color': '#ffcc00'},
                {'range': [2.4, 4], 'color': '#00cc44'},
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': value
            },
        }
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig

# === Streamlit App ===
st.title("Mini Company Dashboard")

companies = get_all_companies()

if 'company' not in st.session_state:
    st.session_state.company = companies[0]

st.selectbox("Select Company", options=companies, key="company")

ratio = get_company_ratio(st.session_state.company, "2024 Annual")

if ratio:
    fig = create_gauge(ratio, "Current Ratio")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data available")

if st.button("Refresh"):
    st.cache_data.clear()
    st.rerun()
```

Run: `streamlit run mini_dashboard.py`

</details>

---

## What You Built

A complete mini-dashboard with:
- **Airtable data fetching** (Exercise 1)
- **Persistent company selector** (Exercise 2)
- **Color-coded gauge chart** (Exercise 3)

---

## Module 1 Complete!

You now understand the three core patterns used throughout the BPC Dashboard:

| Pattern | Where It's Used |
|---------|-----------------|
| Airtable queries | All data fetching |
| Session state | Navigation, filters, user selections |
| Plotly gauges | Company ratios page, group ratios page |

**Next:** Read the documentation files referenced in Week 1 of your learning plan to deepen your understanding of these patterns.
