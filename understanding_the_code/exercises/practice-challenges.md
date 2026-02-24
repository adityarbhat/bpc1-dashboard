# Practice Challenges

## Overview

Hands-on coding exercises to reinforce your understanding of the BPC Dashboard. Work through these challenges to solidify your knowledge and build confidence.

**Difficulty Levels:**
- 🟢 Beginner - Basic concepts
- 🟡 Intermediate - Combining multiple concepts
- 🔴 Advanced - Complex features and optimization

---

## Challenge 1: Add a New Metric (🟢 Beginner)

### Task

Add a "Quick Ratio" gauge to the Company Ratios page.

**Quick Ratio Formula:** `(Current Assets - Inventory) / Current Liabilities`

**Requirements:**
- Range: 0-2
- Red zone: < 0.8
- Yellow zone: 0.8-1.2
- Green zone: > 1.2
- Format: Ratio (2 decimals)
- Higher is better

<details>
<summary>Hints</summary>

1. Look at the existing Current Ratio implementation
2. You'll need to fetch current assets and current liabilities
3. Assume inventory = 0 for simplicity (or fetch if available)
4. Use `create_gauge_chart()` from `shared/chart_utils.py`
5. Add to the gauge grid display

</details>

<details>
<summary>Solution</summary>

```python
# In company_ratios.py

# Fetch data
balance_data = airtable.get_balance_sheet_data_by_period(company_name, period)
record = balance_data[0] if balance_data else {}

current_assets = record.get('total_current_assets', 0)
current_liabilities = record.get('total_current_liabilities', 0)

# Calculate Quick Ratio (assuming inventory = 0)
if current_liabilities != 0:
    quick_ratio = current_assets / current_liabilities
else:
    quick_ratio = 0

# Create gauge
from shared.chart_utils import create_gauge_chart

fig = create_gauge_chart(
    value=quick_ratio,
    title="Quick Ratio",
    min_val=0,
    max_val=2,
    threshold_red=0.8,
    threshold_yellow=1.2,
    format_type="ratio",
    reverse_colors=False
)

# Display in column
st.plotly_chart(fig, use_container_width=True)
```

</details>

---

## Challenge 2: Create a Summary Card Component (🟡 Intermediate)

### Task

Build a reusable "metric card" component that displays a metric with icon, value, and change indicator.

**Requirements:**
- Shows metric name
- Displays current value (large, bold)
- Shows change from previous period (+/- percentage)
- Color-coded based on change (green for positive, red for negative)
- Optional icon parameter

**Example Usage:**

```python
create_metric_card(
    title="Total Revenue",
    current_value=1500000,
    previous_value=1350000,
    format_type="currency",
    icon="💰"
)
```

**Expected Output:**

```
┌─────────────────────┐
│ 💰 Total Revenue    │
│                     │
│   $1.50M            │  ← Large, bold
│   ↑ +11.1%          │  ← Green, with arrow
└─────────────────────┘
```

<details>
<summary>Solution</summary>

```python
# In shared/page_components.py

def create_metric_card(title, current_value, previous_value, format_type="currency", icon=None):
    """
    Create a metric card with value and change indicator

    Args:
        title (str): Metric name
        current_value (float): Current period value
        previous_value (float): Previous period value
        format_type (str): "currency", "percent", or "number"
        icon (str): Optional emoji icon
    """
    # Calculate change percentage
    if previous_value != 0:
        change_pct = ((current_value - previous_value) / abs(previous_value)) * 100
    else:
        change_pct = 0

    # Determine color and arrow
    if change_pct > 0:
        color = "#28a745"  # Green
        arrow = "↑"
    elif change_pct < 0:
        color = "#dc3545"  # Red
        arrow = "↓"
    else:
        color = "#6c757d"  # Gray
        arrow = "→"

    # Format current value
    if format_type == "currency":
        if current_value >= 1000000:
            display_value = f"${current_value/1000000:.2f}M"
        elif current_value >= 1000:
            display_value = f"${current_value/1000:.2f}K"
        else:
            display_value = f"${current_value:.0f}"
    elif format_type == "percent":
        display_value = f"{current_value:.1f}%"
    else:
        display_value = f"{current_value:,.0f}"

    # Build HTML
    icon_html = f"{icon} " if icon else ""

    st.markdown(f"""
    <div style="
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem;">
            {icon_html}<strong>{title}</strong>
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: #1a202c; margin: 0.5rem 0;">
            {display_value}
        </div>
        <div style="font-size: 0.9rem; color: {color}; font-weight: 600;">
            {arrow} {abs(change_pct):.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# Usage example
create_metric_card(
    title="Total Revenue",
    current_value=1500000,
    previous_value=1350000,
    format_type="currency",
    icon="💰"
)
```

</details>

---

## Challenge 3: Implement Cached Company Selector (🟡 Intermediate)

### Task

Create an optimized company selector component that:
1. Caches the company list
2. Preserves selection across page navigation
3. Provides search/filter capability

<details>
<summary>Solution</summary>

```python
# In shared/page_components.py

def create_company_selector(key_suffix=""):
    """
    Create optimized company selector with caching and state persistence

    Args:
        key_suffix (str): Unique suffix for widget key (prevents conflicts)

    Returns:
        str: Selected company name
    """
    # Get cached companies
    from shared.airtable_connection import get_companies_cached

    companies = get_companies_cached()

    if not companies:
        st.warning("No companies found")
        return None

    company_names = [c['name'] for c in companies]

    # Get current selection from session state
    current_selection = st.session_state.get('selected_company_name', company_names[0])

    # Ensure current selection is valid
    if current_selection not in company_names:
        current_selection = company_names[0]

    # Create selector
    selected = st.selectbox(
        "**Select Company**",
        options=company_names,
        index=company_names.index(current_selection),
        key=f"company_selector_{key_suffix}"
    )

    # Update session state
    st.session_state.selected_company_name = selected

    return selected

# Usage
selected_company = create_company_selector(key_suffix="ratios_page")
```

</details>

---

## Challenge 4: Build a Trend Sparkline (🔴 Advanced)

### Task

Create mini trend charts (sparklines) showing metric trends over 5 years.

**Requirements:**
- Small, inline chart (height: 60px)
- Shows trend for 2020-2024
- No axes labels (minimal design)
- Color-coded: green for upward trend, red for downward
- Displays final value at end

**Example:**

```
Revenue Trend: ───╱──╱─  $1.5M
                  2020    2024
```

<details>
<summary>Solution</summary>

```python
import plotly.graph_objects as go

def create_sparkline(values, years, metric_name, current_value_display):
    """
    Create a mini trend chart (sparkline)

    Args:
        values (list): Values for each year
        years (list): Year labels
        metric_name (str): Metric name for title
        current_value_display (str): Formatted current value
    """
    # Determine trend color
    if len(values) >= 2:
        if values[-1] > values[0]:
            color = "#28a745"  # Green (upward)
        elif values[-1] < values[0]:
            color = "#dc3545"  # Red (downward)
        else:
            color = "#6c757d"  # Gray (flat)
    else:
        color = "#6c757d"

    # Create minimal line chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years,
        y=values,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba({color[1:]}, 0.1)',  # Light fill
        hovertemplate='%{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        height=60,
        margin=dict(l=0, r=40, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    ))

    # Add current value annotation
    fig.add_annotation(
        x=years[-1],
        y=values[-1],
        text=current_value_display,
        showarrow=False,
        xanchor='left',
        font=dict(size=10, weight='bold', color=color)
    )

    return fig

# Usage
years = ['2020', '2021', '2022', '2023', '2024']
revenue_values = [1000000, 1100000, 1080000, 1250000, 1500000]

fig = create_sparkline(
    values=revenue_values,
    years=years,
    metric_name="Revenue",
    current_value_display="$1.50M"
)

col1, col2 = st.columns([3, 1])
with col1:
    st.write("**Revenue Trend (2020-2024)**")
with col2:
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
```

</details>

---

## Challenge 5: Add Data Export Feature (🔴 Advanced)

### Task

Implement Excel export for the Value Trend table.

**Requirements:**
- Export button
- Downloads Excel file with all trend data
- Includes calculated metrics
- Formatted with headers
- Filename includes company name and date

<details>
<summary>Solution</summary>

```python
import pandas as pd
from datetime import datetime
import io

def export_value_trend_to_excel(company_name, all_data):
    """
    Export value trend data to Excel

    Args:
        company_name (str): Company name
        all_data (dict): All company data from bulk fetch
    """
    # Prepare data
    years = ['2020', '2021', '2022', '2023', '2024']
    rows = []

    for year in years:
        balance = all_data['balance_sheet'].get(year, {})

        debt = balance.get('interest_bearing_debt', 0)
        ebitda = balance.get('ebitda_000', 0)
        equity = balance.get('equity_000', 0)

        ebitda_x3 = ebitda * 3
        company_val = ebitda_x3 - debt
        val_equity = company_val / equity if equity != 0 else 0

        rows.append({
            'Year': year,
            'Interest Bearing Debt ($K)': debt,
            'EBITDA ($K)': ebitda,
            'EBITDA x 3 ($K)': ebitda_x3,
            'Company Value ($K)': company_val,
            'Equity ($K)': equity,
            'Value to Equity Ratio': val_equity
        })

    # Create DataFrame
    df = pd.DataFrame(rows)

    # Create Excel file in memory
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Value Trends')

        # Auto-adjust column widths
        worksheet = writer.sheets['Value Trends']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length

    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{company_name}_Value_Trends_{timestamp}.xlsx"

    # Download button
    st.download_button(
        label="📥 Download Excel",
        data=output.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Usage in page
if st.button("Export to Excel"):
    export_value_trend_to_excel(company_name, all_data)
```

</details>

---

## Challenge 6: Implement Search Filter (🟡 Intermediate)

### Task

Add search functionality to filter the wins and challenges list.

**Requirements:**
- Text input for search
- Filters both wins AND challenges
- Case-insensitive
- Highlights matching text
- Shows count of results

<details>
<summary>Solution</summary>

```python
def display_searchable_wins_challenges(wins, challenges):
    """
    Display wins and challenges with search filter

    Args:
        wins (list): List of win statements
        challenges (list): List of challenge statements
    """
    # Search input
    search_term = st.text_input("🔍 Search wins and challenges", "")

    # Filter function
    def matches_search(text, search):
        return search.lower() in text.lower() if search else True

    # Filter wins and challenges
    if search_term:
        filtered_wins = [w for w in wins if matches_search(w, search_term)]
        filtered_challenges = [c for c in challenges if matches_search(c, search_term)]

        # Show count
        total_found = len(filtered_wins) + len(filtered_challenges)
        st.info(f"Found {total_found} results for '{search_term}'")
    else:
        filtered_wins = wins
        filtered_challenges = challenges

    # Display in two columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Wins")
        if filtered_wins:
            for win in filtered_wins:
                # Highlight search term
                if search_term:
                    highlighted = win.replace(
                        search_term,
                        f"**{search_term}**"
                    )
                    st.markdown(f"✅ {highlighted}")
                else:
                    st.markdown(f"✅ {win}")
        else:
            st.info("No wins match your search")

    with col2:
        st.markdown("### Challenges")
        if filtered_challenges:
            for challenge in filtered_challenges:
                if search_term:
                    highlighted = challenge.replace(
                        search_term,
                        f"**{search_term}**"
                    )
                    st.markdown(f"⚠️ {highlighted}")
                else:
                    st.markdown(f"⚠️ {challenge}")
        else:
            st.info("No challenges match your search")
```

</details>

---

## Bonus Challenge: Build a Custom Dashboard Page (🔴 Advanced)

### Task

Create a complete custom analysis page that:
1. Lets user select 2-3 companies
2. Compares them side-by-side
3. Shows gauges for each company
4. Includes YoY trends
5. Has export functionality

**This is a comprehensive project - plan it out first!**

---

## New Challenges (January 2026 Features)

---

## Challenge 7: Implement Session Timeout (🟡 Intermediate)

### Task

Add a session timeout feature that logs users out after inactivity.

**Requirements:**
- Auto-logout after 30 minutes of inactivity
- Show warning toast 5 minutes before timeout
- Allow user to click "Stay Logged In" to extend
- Log timeout event to audit table

<details>
<summary>Hints</summary>

1. Store `last_activity` timestamp in `st.session_state`
2. Check elapsed time on each page load
3. Use `st.toast()` for non-blocking warning
4. Call `logout_user()` when timeout expires
5. Update `last_activity` on any user interaction

</details>

<details>
<summary>Solution</summary>

```python
from datetime import datetime, timedelta
from shared.auth_utils import logout_user, log_audit_event

def check_session_timeout():
    """Check and handle session timeout."""
    TIMEOUT_MINUTES = 30
    WARNING_MINUTES = 25

    # Initialize last activity if not set
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()
        return  # First load, no timeout check

    last_activity = st.session_state.last_activity
    inactive_seconds = (datetime.now() - last_activity).total_seconds()
    inactive_minutes = inactive_seconds / 60

    if inactive_minutes >= TIMEOUT_MINUTES:
        # Timed out
        log_audit_event(action='session_timeout')
        logout_user()
        st.warning("Your session has expired due to inactivity.")
        st.stop()

    elif inactive_minutes >= WARNING_MINUTES:
        # Show warning
        remaining = TIMEOUT_MINUTES - inactive_minutes
        st.toast(
            f"Session expires in {remaining:.0f} minutes. "
            "Click anywhere to stay logged in.",
            icon="⚠️"
        )

    # Update last activity timestamp
    st.session_state.last_activity = datetime.now()

# Usage: Call at start of each protected page
def my_page():
    require_auth()
    check_session_timeout()
    # ... rest of page
```

</details>

---

## Challenge 8: Add Excel Export Sheet (🔴 Advanced)

### Task

Add a new "Summary" sheet to the multi-sheet Excel export.

**Requirements:**
- First sheet in workbook (before Ratios)
- Contains: Export date, period, company count
- Lists all sheet names with row counts
- Atlas blue header styling
- Auto-width columns

<details>
<summary>Hints</summary>

1. Modify `create_multi_sheet_export()` in `export_utils.py`
2. Create summary DataFrame before other sheets
3. Use `openpyxl.styles.PatternFill` for blue header
4. Track row counts from each sheet
5. Insert summary as first sheet

</details>

<details>
<summary>Solution</summary>

```python
from openpyxl.styles import PatternFill, Font, Alignment
from datetime import datetime
import pandas as pd

def create_summary_sheet(writer, period: str, year: int, sheet_stats: dict):
    """
    Create summary sheet as first sheet in workbook.

    Args:
        writer: ExcelWriter object
        period: Period string
        year: Year
        sheet_stats: Dict of sheet_name -> row_count
    """
    # Build summary data
    rows = [
        {'Item': 'Export Date', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M')},
        {'Item': 'Period', 'Value': period},
        {'Item': 'Year', 'Value': year},
        {'Item': 'Total Companies', 'Value': 10},
        {'Item': '---', 'Value': '---'},
    ]

    for sheet_name, count in sheet_stats.items():
        rows.append({'Item': f'{sheet_name} Rows', 'Value': count})

    df = pd.DataFrame(rows)
    df.to_excel(writer, sheet_name='Summary', index=False)

    # Apply formatting
    worksheet = writer.sheets['Summary']

    # Atlas blue header
    header_fill = PatternFill(start_color='025a9a', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    # Auto-width columns
    worksheet.column_dimensions['A'].width = 25
    worksheet.column_dimensions['B'].width = 30

# Usage in create_multi_sheet_export():
sheet_stats = {}
for sheet_name, extractor, formatter in sheets:
    df = extractor(period)
    sheet_stats[sheet_name] = len(df)
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    # ... formatting

# Add summary as first sheet
create_summary_sheet(writer, period, year, sheet_stats)

# Reorder sheets to put Summary first
workbook = writer.book
workbook.move_sheet('Summary', offset=-len(sheets))
```

</details>

---

## Challenge 9: Build Upload Progress Tracker (🟡 Intermediate)

### Task

Create a progress indicator for Excel upload with multiple sheets.

**Requirements:**
- Shows overall progress bar
- Displays current sheet being processed
- Shows success/failure status per sheet
- Handles errors gracefully (continues on failure)
- Final summary of results

<details>
<summary>Solution</summary>

```python
def upload_with_progress(uploaded_file, company_name: str, period_name: str):
    """Upload Excel file with progress tracking."""

    sheets_to_process = [
        ('Income Statement', parse_income_statement_data, upload_income_statement_to_airtable),
        ('Balance Sheet', parse_balance_sheet_data, upload_balance_sheet_to_airtable),
    ]

    total_sheets = len(sheets_to_process)
    results = []

    # Create progress container
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, (sheet_name, parser, uploader) in enumerate(sheets_to_process):
        # Update progress
        progress = (i + 1) / total_sheets
        progress_bar.progress(progress)
        status_text.write(f"Processing: **{sheet_name}**...")

        try:
            # Parse sheet
            import pandas as pd
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
            success, data, errors = parser(df)

            if not success:
                results.append({
                    'sheet': sheet_name,
                    'status': 'failed',
                    'message': f"Parse errors: {errors[:3]}"
                })
                continue

            # Upload
            upload_success, message = uploader(company_name, period_name, data)

            results.append({
                'sheet': sheet_name,
                'status': 'success' if upload_success else 'failed',
                'message': message
            })

        except Exception as e:
            results.append({
                'sheet': sheet_name,
                'status': 'error',
                'message': str(e)
            })

    # Clear progress
    progress_bar.empty()
    status_text.empty()

    # Show results
    st.subheader("Upload Results")

    for result in results:
        if result['status'] == 'success':
            st.success(f"✅ {result['sheet']}: {result['message']}")
        else:
            st.error(f"❌ {result['sheet']}: {result['message']}")

    # Summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    st.info(f"Completed: {success_count}/{total_sheets} sheets uploaded successfully")

    return results
```

</details>

---

## Challenge 10: Implement Draft Preview (🔴 Advanced)

### Task

Build a preview feature for draft W&C data before publishing.

**Requirements:**
- Super admin only access
- Shows draft W&C in preview mode (styled differently)
- Side-by-side: Draft vs Published
- "Approve and Publish" button
- Visual diff highlighting changes

<details>
<summary>Solution</summary>

```python
def draft_preview_page():
    """Preview draft W&C data before publishing."""
    from shared.auth_utils import require_auth, is_super_admin
    from pages.data_input.wins_challenges_manager import WinsChallengesActionItemsManager

    require_auth()

    if not is_super_admin():
        st.error("Super admin access required")
        return

    st.header("Draft Preview")

    # Company and period selection
    company = st.selectbox("Company", get_all_company_names())
    period = st.selectbox("Period", ["2024 Annual", "2023 Annual"])

    manager = WinsChallengesActionItemsManager()
    period_id = manager.get_period_id(company, period)

    if not period_id:
        st.warning("No period found")
        return

    # Get draft and published data
    draft_wins = manager.get_items_by_status('wins', period_id, 'draft')
    published_wins = manager.get_items_by_status('wins', period_id, 'published')

    draft_challenges = manager.get_items_by_status('challenges', period_id, 'draft')
    published_challenges = manager.get_items_by_status('challenges', period_id, 'published')

    # Side-by-side display
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Draft (Pending)")
        st.markdown("""
        <style>
        .draft-item { background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 5px; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("**Wins:**")
        for win in draft_wins:
            st.markdown(f'<div class="draft-item">🆕 {win["win_text"]}</div>',
                       unsafe_allow_html=True)

        st.markdown("**Challenges:**")
        for challenge in draft_challenges:
            st.markdown(f'<div class="draft-item">🆕 {challenge["challenge_text"]}</div>',
                       unsafe_allow_html=True)

    with col2:
        st.subheader("✅ Published (Current)")

        st.markdown("**Wins:**")
        for win in published_wins:
            st.write(f"✅ {win['win_text']}")

        st.markdown("**Challenges:**")
        for challenge in published_challenges:
            st.write(f"⚠️ {challenge['challenge_text']}")

    # Publish button
    st.divider()

    if draft_wins or draft_challenges:
        if st.button("Approve and Publish All Drafts", type="primary"):
            with st.spinner("Publishing..."):
                manager.publish_all_wins(period_id)
                manager.publish_all_challenges(period_id)
                st.success("All drafts published!")
                st.rerun()
    else:
        st.info("No drafts pending for this period")
```

</details>

---

## Challenge 11: Cash Flow Trend Sparklines (🔴 Advanced)

### Task

Create mini sparkline charts showing 5-year cash flow trends.

**Requirements:**
- Small inline charts (60px height)
- Shows OCF, FCF, NCF trends for 2020-2024
- Color based on trend direction (green=improving, red=declining)
- Display current value at end
- No axis labels (minimal design)

<details>
<summary>Solution</summary>

```python
import plotly.graph_objects as go
from shared.cash_flow_utils import get_cash_flow_ratios_for_trends

def create_cash_flow_sparkline(
    company_name: str,
    metric: str,  # 'ocf_rev', 'fcf_rev', or 'ncf_rev'
    airtable
) -> go.Figure:
    """
    Create mini sparkline for cash flow metric.

    Args:
        company_name: Company to show
        metric: Which cash flow metric
        airtable: AirtableConnection

    Returns:
        Plotly figure
    """
    # Get 5-year data
    trends = get_cash_flow_ratios_for_trends(airtable, company_name)

    years = []
    values = []

    for year in [2020, 2021, 2022, 2023, 2024]:
        year_data = trends.get(year, {})
        value = year_data.get(metric) if year_data else None

        years.append(str(year))
        values.append(value * 100 if value else 0)  # Convert to percentage

    # Determine trend color
    if len(values) >= 2 and values[-1] > values[0]:
        color = "#28a745"  # Green - improving
    elif len(values) >= 2 and values[-1] < values[0]:
        color = "#dc3545"  # Red - declining
    else:
        color = "#6c757d"  # Gray - flat

    # Create minimal sparkline
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years,
        y=values,
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=4, color=color),
        hovertemplate='%{y:.1f}%<extra></extra>'
    ))

    # Add current value annotation
    fig.add_annotation(
        x=years[-1],
        y=values[-1],
        text=f"{values[-1]:.1f}%",
        showarrow=False,
        xanchor='left',
        xshift=5,
        font=dict(size=10, color=color, weight='bold')
    )

    # Minimal layout
    fig.update_layout(
        height=60,
        margin=dict(l=5, r=40, t=5, b=5),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )

    return fig

# Usage
col1, col2 = st.columns([3, 1])
with col1:
    st.write("**OCF/Revenue Trend (2020-2024)**")
with col2:
    fig = create_cash_flow_sparkline(company_name, 'ocf_rev', airtable)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
```

</details>

---

## Learning Path

**Recommended Order:**

### Phase 1: Core Concepts (Weeks 1-2)
1. ✅ Challenge 1 (Beginner) - Get comfortable with gauges
2. ✅ Challenge 2 (Intermediate) - Build reusable components
3. ✅ Challenge 6 (Intermediate) - Add interactivity
4. ✅ Challenge 3 (Intermediate) - Work with state and caching

### Phase 2: Advanced Visualizations (Weeks 3-4)
5. ✅ Challenge 4 (Advanced) - Advanced visualizations (sparklines)
6. ✅ Challenge 11 (Advanced) - Cash flow trend sparklines
7. ✅ Challenge 5 (Advanced) - Data export basics

### Phase 3: Data Pipeline (Weeks 5-6)
8. ✅ Challenge 9 (Intermediate) - Upload progress tracking
9. ✅ Challenge 8 (Advanced) - Excel export customization
10. ✅ Challenge 10 (Advanced) - Draft preview system

### Phase 4: Security & Auth (Week 7)
11. ✅ Challenge 7 (Intermediate) - Session timeout
12. ✅ Bonus Challenge (Advanced) - Full page implementation

---

## Tips for Success

✅ **Read the related guides** before attempting challenges
✅ **Start with hints** if you're stuck
✅ **Look at similar code** in the existing codebase
✅ **Test incrementally** - don't write everything at once
✅ **Ask questions** - learning is a journey!

---

*Practice makes perfect - work through these challenges to master the BPC Dashboard patterns! 💪*
