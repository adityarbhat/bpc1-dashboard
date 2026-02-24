# Dynamic Year Range - Company Pages Only

## Problem

The dashboard hardcodes `['2020', '2021', '2022', '2023', '2024']` across **8 company page files** (~30+ locations). When 2025 data is added, every list must be manually updated. We want:

- Default view shows the most recent 5 years (sliding window)
- When 2025 data is added, window shifts to 2021-2025 automatically
- Company owners can optionally look back further (2014+) for growth analysis
- Dashboard stays fast — very few users will use the history feature

**Scope: Company pages only.** Group pages stay as-is because some companies weren't part of the group until the last 5 years, making historical group comparisons misleading.

---

## Files That Need Changes

| File | Hardcoded Year Locations |
|------|--------------------------|
| `company_income_statement.py` | Lines 30, 550, 770, 943, 1127, 1320, 1542, 1746, 1920+ |
| `company_balance_sheet.py` | Lines 31, 522, 531, 557, 576, 701, 1153, 1614 |
| `company_cash_flow.py` | Lines 26, 68, 198, 272, 816, 1191, 1327, 1463 |
| `company_ratios.py` | Line 538 |
| `company_actuals.py` | Lines 23, 543, 688 |
| `company_value.py` | Lines 452, 819, 997 |
| `company_labor_cost.py` | Lines 469, 515, 658-786 |
| `company_wins_challenges.py` | Lines 165, 254, 857-860 |

---

## Options

### Option A: Single Config Constant + Sidebar Toggle (Recommended)

**The idea:**
One constant (`CURRENT_YEAR = 2024`) in a shared config. All company pages calculate their 5-year window from it. A small sidebar toggle lets users expand to full history.

**What users see:**
- By default: exactly what they see today (last 5 years)
- A small "Show Full History" checkbox in the sidebar (company pages only)
- When checked: year selectors and trend tables expand back to 2014+

**What changes each year:**
```python
# shared/year_config.py — the ONLY file to update
CURRENT_YEAR = 2025  # Change this one number
```

Dashboard auto-shifts from [2020-2024] to [2021-2025].

**Performance:**
- Default loads 5 years (same as today)
- History toggle fetches older years on demand
- Cached like all other data (15-min TTL)

**Pros:**
- Simplest possible change — one number, one file, once a year
- No new Airtable queries or API changes needed
- Minimal UI addition (one checkbox)
- Default experience is unchanged
- Easy to remove the toggle later if nobody uses it

**Cons:**
- Still manual (you update `CURRENT_YEAR` when adding new year data)
- Toggle is all-or-nothing (shows all history, not a custom range)

---

### Option B: Auto-Detect Years from Airtable (Zero Maintenance)

**The idea:**
Query Airtable at startup to discover which years have published data. No config to update — ever.

**What changes each year:** Nothing. Upload 2025 data to Airtable and the dashboard auto-discovers it.

**Pros:**
- Truly zero maintenance
- Reflects actual data availability per company

**Cons:**
- Extra Airtable API call on startup (even if cached, adds a dependency)
- If bad data gets uploaded with wrong year, it could shift the window
- More complex implementation
- Overkill given that data uploads happen once a year

---

### Option C: Year Range Slider

**The idea:** Replace year dropdowns with a range slider. Default position: last 5 years. Drag left to see older data.

**Pros:**
- Precise control over which years to view
- Native Streamlit widget (`st.slider`)

**Cons:**
- Takes more sidebar space
- Tables/charts must handle variable column counts
- Confusing for users who just want to see current data
- More complex than needed given low historical usage

---

## Recommendation: Option A

Given that very few users will use historical data, Option A is the right call:

1. **Biggest win is the consolidation** — going from 30+ hardcoded year lists to 1 config constant
2. **Toggle is unobtrusive** — users who don't need it won't notice it
3. **Zero risk to current experience** — default view is identical to today
4. **5 minutes per year to maintain** — change one number when adding new year data
5. **Foundation for more** — if demand grows, can evolve to slider or dedicated page later

---

## Decision Needed

- [ ] Confirm Option A (or choose another)
- [ ] Confirm earliest historical year to support (2014? earlier?)
- [ ] Confirm toggle should be a checkbox in sidebar vs. an expander at bottom of trend tables
