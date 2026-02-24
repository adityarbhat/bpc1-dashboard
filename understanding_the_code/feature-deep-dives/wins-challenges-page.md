# Feature Deep Dive: Wins & Challenges Page

## Overview

Complete breakdown of the Wins & Challenges analysis page, featuring manual content management, rank integration, and YoY visualization.

**File:** `pages/company_pages/company_wins_challenges.py`
**Key Features:** Dictionary-based content, ranking integration, YoY charts
**Difficulty:** Intermediate
**Time:** 25-30 minutes

---

## Architecture Overview

### Three Main Components

1. **Static Content** - Wins & Challenges dictionary (manually updated)
2. **Dynamic Rank** - Fetched from group rankings calculation
3. **YoY Analysis** - Calculated from Airtable income statement data

---

## Content Management System

### The WINS_CHALLENGES_DATA Dictionary

```python
WINS_CHALLENGES_DATA = {
    "Coastal": {
        "wins": [
            "Ranked #1 in overall group rankings...",
            "Exceptional Survival Score above 3.5...",
            "Industry-leading Current Ratio..."
        ],
        "challenges": [
            "Revenue growth rate modest...",
            "Administrative expense ratio slightly elevated...",
            "Capital expenditure needs increasing..."
        ]
    },
    "Ace": {
        "wins": [
            "Exceptional Revenue Per Admin Employee ratio...",
            "EBITDA margin shows strong operational performance...",
            "Consistent improvement in Survival Score..."
        ],
        "challenges": [
            "Current Ratio below optimal range...",
            "Days Sales Outstanding (DSO) increasing...",
            "Net Profit Margin remains below industry peers..."
        ]
    },
    # ... 8 more companies
}
```

### Why Dictionary-Based?

✅ **Easy to update** - Moderator edits text annually
✅ **No database** needed for static content
✅ **Version controlled** - Changes tracked in git
✅ **Fast loading** - No API calls for content

### Annual Update Process

```python
# At end of year, moderator reviews financial data and updates:

WINS_CHALLENGES_DATA["Company Name"] = {
    "wins": [
        "New win based on 2024 data...",
        "Another achievement...",
        "Third strength..."
    ],
    "challenges": [
        "Area needing improvement...",
        "Another challenge...",
        "Third challenge..."
    ]
}
```

---

## Rank Integration

### Fetching Current Rank

```python
def get_company_rank(company_name, period):
    """Get the overall group rank for a company in the selected period"""
    try:
        # Import from group ratios page
        from pages.group_pages.group_ratios import calculate_group_rankings

        rankings_data = calculate_group_rankings(period)

        if rankings_data and 'rankings' in rankings_data:
            return rankings_data['rankings'].get(company_name, None)

        return None

    except Exception as e:
        st.warning(f"Could not calculate rankings: {str(e)}")
        return None

# Usage
rank = get_company_rank("Coastal", "2024 Annual")
# Returns: 1 (Coastal is ranked #1)
```

### Display Rank Badge

```python
if company_rank:
    st.markdown(f"""
    <div class="rank-display">
        Current Group Rank: #{company_rank}
    </div>
    """, unsafe_allow_html=True)
```

**CSS Styling:**

```css
.rank-display {
    background: linear-gradient(135deg, #025a9a, #0e9cd5);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    font-family: 'Montserrat', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    text-align: center;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(2, 90, 154, 0.3);
}
```

---

## Wins & Challenges Display

### Two-Column Layout

```python
# Get wins and challenges from dictionary
wins_challenges = WINS_CHALLENGES_DATA.get(company_name, {})
wins = wins_challenges.get('wins', [])
challenges = wins_challenges.get('challenges', [])

# Display in two columns
col1, col2 = st.columns(2)

with col1:
    # Wins HTML
    wins_html = '<div class="wins-list"><h3>Wins</h3><ul>'
    for win in wins:
        wins_html += f'<li>{win}</li>'
    wins_html += '</ul></div>'
    st.markdown(wins_html, unsafe_allow_html=True)

with col2:
    # Challenges HTML
    challenges_html = '<div class="challenges-list"><h3>Challenges</h3><ul>'
    for challenge in challenges:
        challenges_html += f'<li>{challenge}</li>'
    challenges_html += '</ul></div>'
    st.markdown(challenges_html, unsafe_allow_html=True)
```

### Styled Lists

**CSS:**

```css
.wins-list {
    background-color: #f7fafc;
    padding: 1.5rem;
    border-radius: 8px;
    border-left: 4px solid #025a9a;  /* Blue border */
    margin: 1rem 0;
}

.challenges-list {
    background-color: #f7fafc;
    padding: 1.5rem;
    border-radius: 8px;
    border-left: 4px solid #c2002f;  /* Red border */
    margin: 1rem 0;
}

.wins-list li:before {
    content: "✓ ";
    color: #10b981;  /* Green checkmark */
    font-weight: bold;
}

.challenges-list li:before {
    content: "⚠ ";
    color: #ef4444;  /* Red warning */
    font-weight: bold;
}
```

---

## YoY Horizontal Bar Chart

### Chart Creation

```python
def create_yoy_chart(yoy_data):
    """Create horizontal bar chart for year-over-year percentage changes"""

    # Define Atlas blue color variants
    color_map = {
        'Total Revenue': '#025a9a',       # Atlas dark blue
        'Direct Expenses': '#0e9cd5',     # Atlas light blue
        'Gross Profit': '#4db8e8',        # Atlas lighter blue
        'Operating Expenses': '#1e7ba0',  # Atlas medium blue
        'Operating Income': '#0a4d73'     # Atlas darker blue
    }

    # Prepare data
    categories = ['Total Revenue', 'Direct Expenses', 'Gross Profit',
                  'Operating Expenses', 'Operating Income']
    values = [yoy_data.get(cat, 0.0) for cat in categories]
    colors = [color_map[cat] for cat in categories]

    # Create chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=categories,
        x=values,
        orientation='h',  # Horizontal!
        marker=dict(color=colors),
        text=[f"<b>{val:.1f}%</b>" for val in values],
        textposition='inside',
        textfont=dict(size=16, family='Montserrat', color='white')
    ))

    # Update layout
    fig.update_layout(
        title='<b>% Change over One-Year Period</b>',
        xaxis=dict(
            title='',
            showgrid=True,
            gridcolor='#e2e8f0',
            zeroline=True,
            zerolinecolor='#025a9a',
            zerolinewidth=2,
            ticksuffix='%'
        ),
        yaxis=dict(
            title='',
            autorange='reversed'  # Top to bottom
        ),
        height=500,
        showlegend=False
    ))

    return fig
```

### Example Output

```
Total Revenue        ████████████ 12.3%
Direct Expenses      ████████ 8.5%
Gross Profit         ███ 3.5%
Operating Expenses   ████████████████ 15.7%
Operating Income     ████████████████████ 20.1%
                     |
                     0%        10%       20%
```

---

## Multi-Year Color-Coded Table

### Table Generation

```python
def create_multi_year_table(multi_year_data):
    """Create color-coded table for multi-year YoY trends (2021-2024)"""

    metrics = ['Total Revenue', 'Direct Expenses', 'Gross Profit',
               'Operating Expenses', 'Operating Income']
    years = sorted(multi_year_data.keys())  # ['2021', '2022', '2023', '2024']

    # Helper function for cell color
    def get_cell_color(value):
        if value is None:
            return '#f8f9fa'  # Light gray
        elif value > 5:
            return '#d4edda'  # Green
        elif value < -5:
            return '#f8d7da'  # Red
        else:
            return '#fff3cd'  # Yellow

    # Build HTML table
    table_html = '<table class="yoy-trends-table">'

    # Header row
    table_html += '<thead><tr><th>Metric</th>'
    for year in years:
        table_html += f'<th>{year}</th>'
    table_html += '</tr></thead><tbody>'

    # Data rows
    for metric in metrics:
        table_html += f'<tr><td class="metric-name">{metric}</td>'

        for year in years:
            value = multi_year_data[year].get(metric, None)
            bg_color = get_cell_color(value)
            formatted_value = f'{value:.1f}%' if value is not None else '-'

            table_html += f'<td style="background-color: {bg_color}; text-align: center; font-weight: 600;">{formatted_value}</td>'

        table_html += '</tr>'

    table_html += '</tbody></table>'

    return table_html
```

### Visual Result

```
Metric              2021    2022    2023    2024
──────────────────────────────────────────────────
Total Revenue       5.2%    -2.1%   8.5%    12.3%
                   [green] [yellow][green] [green]

Direct Expenses     3.1%    1.5%    7.2%    8.9%
                   [yellow][yellow][green] [green]

Gross Profit        8.5%    3.5%    10.2%   18.5%
                   [green] [yellow][green] [green]

Operating Expenses  4.2%    5.8%    9.1%    15.2%
                   [yellow][green] [green] [green]

Operating Income    12.8%   -5.4%   15.7%   20.1%
                   [green] [yellow][green] [green]
```

---

## Complete Page Flow

```python
def display_wins_challenges_sections(balance_data, income_data):
    """Display the wins & challenges analysis sections"""

    company_name = st.session_state.selected_company_name

    # 1. Get static wins & challenges
    wins_challenges = WINS_CHALLENGES_DATA.get(company_name, {})
    wins = wins_challenges.get('wins', [])
    challenges = wins_challenges.get('challenges', [])

    # 2. Get dynamic rank
    company_rank = get_company_rank(company_name, "2024 Annual")

    # 3. Display rank badge
    if company_rank:
        st.markdown(f'<div class="rank-display">Current Group Rank: #{company_rank}</div>',
                    unsafe_allow_html=True)

    # 4. Display wins & challenges in two columns
    col1, col2 = st.columns(2)
    with col1:
        # Display wins list
    with col2:
        # Display challenges list

    # 5. Calculate and display single-year YoY chart
    yoy_data = calculate_yoy_percentages(company_name)
    if yoy_data:
        fig = create_yoy_chart(yoy_data)
        st.plotly_chart(fig, use_container_width=True)

    # 6. Calculate and display multi-year table
    multi_year_data = calculate_multi_year_yoy(company_name)
    if multi_year_data:
        table_html = create_multi_year_table(multi_year_data)
        st.markdown(table_html, unsafe_allow_html=True)
```

---

## Key Takeaways

✅ **Dictionary-based content** easy to maintain
✅ **Rank integration** shows current standing
✅ **Wins & challenges** provide strategic context
✅ **YoY chart** visualizes recent performance
✅ **Multi-year table** shows historical trends
✅ **Color coding** enables quick insights
✅ **Two-column layout** balances wins vs challenges

---

## Practice Exercise

Add a new company to the wins & challenges dictionary:

<details>
<summary>Show Solution</summary>

```python
WINS_CHALLENGES_DATA["New Company"] = {
    "wins": [
        "Strong revenue growth of 15% year-over-year",
        "Improved liquidity with Current Ratio of 2.1",
        "Successfully reduced debt-to-equity from 1.2 to 0.8"
    ],
    "challenges": [
        "Operating margin compressed due to rising labor costs",
        "Days Sales Outstanding increased from 45 to 52 days",
        "Capital expenditure backlog requiring $500K investment"
    ]
}
```

</details>

---

*You now understand how to build a comprehensive wins & challenges analysis page! 🏆*
