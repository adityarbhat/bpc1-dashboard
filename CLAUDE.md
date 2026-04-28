# CLAUDE.md

## Project Overview

Streamlit financial dashboard for Atlas BPC 1 (Business Performance Competition). Copied from the BPC2 dashboard codebase. Connects to Airtable for data, provides financial analysis tools for comparing 10 companies across various metrics.

**Setup Status:** See `docs/BPC1_INITIAL_SETUP_PLAN.md` for the detailed setup checklist. This is a new instance — Airtable base, Supabase project, and deployment are being configured separately from BPC2.

**Key Difference from BPC2:** Same codebase, different set of 10 companies, separate Airtable base, separate Supabase project, separate deployment. All "BPC 2" text references need to be changed to "BPC 1".

## Commands

```bash
# Run the app
streamlit run app.py

# Install dependencies
pip install -r requirements.txt
```

- Python 3.12.0 (see `runtime.txt`)
- Uses venv - activate before development

## Environment Variables

Create `.env` file:
```
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_PAT=your_personal_access_token
```

Production uses Streamlit secrets.

## Architecture

```
app.py                      # Entry point
financial_dashboard.py      # Main app with routing & sidebar
pages/
├── company_pages/          # Company-specific analysis
├── group_pages/            # Group comparisons (7 pages)
└── data_input/             # Upload & admin pages
shared/
├── airtable_connection.py  # API + caching (30-min TTL)
├── auth_utils.py           # Supabase auth + RBAC
├── chart_utils.py          # Plotly gauge charts
├── css_styles.py           # Centralized CSS
├── page_components.py      # Reusable UI components
├── ratio_thresholds.py     # CANONICAL threshold definitions (import here, never inline)
└── export_utils.py         # Excel export (lazy loaded)
```

## Key Patterns

**State Management** - `st.session_state` for:
- `current_page`: Active view
- `period`: "year_end" or "june_end"
- `selected_company_name`: Company filter

**Page Structure** - All pages follow:
1. CSS injection
2. `create_page_header()` first (critical for layout)
3. Sidebar creation
4. `apply_all_styles()` last
5. Content rendering

**Caching** - Use `@st.cache_data(ttl=900)` for API calls. Bulk fetch methods in `airtable_connection.py` are 15-20x faster than individual calls.

**Auth** - Supabase with Row-Level Security. Roles: `company_user` (upload own data), `super_admin` (full access). Check with `is_super_admin()`.

## Theme

Atlas Van Lines branding:
- Primary: `#025a9a` (Atlas Blue)
- Secondary: `#0e9cd5`, `#c2002f`
- Font: Montserrat
- Config: `.streamlit/config.toml`

## Important Files

| File | Purpose |
|------|---------|
| `shared/ratio_thresholds.py` | **Single source of truth** for all ratio color thresholds — edit here only |
| `company_ratios.py` | Gauge charts; imports thresholds from `ratio_thresholds.py` |
| `group_ratios.py` | Group ratio table + `get_cell_color()`; imports from `ratio_thresholds.py` |
| `group_income_statement.py` | Profit margin rows color-coded via `get_cell_color` from `group_ratios` |
| `excel_formatter.py` | Export color coding; imports `DISPLAY_THRESHOLDS` from `ratio_thresholds.py` |
| `shared/cash_flow_utils.py` | Centralized OCF/FCF/NCF calculation — both company and group pages call this |
| `pages/data_input/excel_parser.py` | Upload template parsing |

## Cross-Surface Consistency Invariant

The same metric for the same company and the same period **must render identically** — same numeric value and same color band (green/yellow/red) — on the Company page, the Group ratios page, and the Excel export.

> **Guardrail:** If a proposed change would modify a metric's calculation, formatting, or color threshold on one surface but not the others, **stop before writing code** and surface the conflict. List every file that displays that metric and confirm they will all receive the same change.

### Canonical Sources of Truth

| What | Source |
|------|--------|
| Raw balance sheet fields | `airtable_connection.get_balance_sheet_data_by_period()` |
| Raw income statement fields | `airtable_connection.get_income_statement_data_by_period()` |
| Cash flow ratios (ocf/fcf/ncf) | `shared/cash_flow_utils.py → get_cash_flow_ratios()` — single shared function |
| Color thresholds (all surfaces) | `shared/ratio_thresholds.py → THRESHOLDS` / `DISPLAY_THRESHOLDS` |

**Ratio computation pattern (both surfaces):** Re-derive from raw dollar fields when available; fall back to Airtable's stored ratio field if the divisor is zero. Keep this pattern identical on both surfaces when changing a formula.

### Required Workflow When Modifying Thresholds or Calculations

1. Edit `shared/ratio_thresholds.py` only — all three consumers (`company_ratios`, `group_ratios`, `excel_formatter`) import from it automatically.
2. If changing a *calculation* (not just a threshold), find every file that computes that ratio and update them together.
3. Spot-check one company end-to-end: Company page → Group ratios page → Excel export. Values and colors must match.

### Known Failure Modes

- **New ratio added on one surface only:** Adding a metric to `fetch_group_ratio_data()` in `group_ratios.py` without adding its key to `ratio_thresholds.py` means it will be gray/uncolored. Always add to `ratio_thresholds.py` first.
- **Stale fallback values:** Both surfaces fall back to Airtable-stored ratio fields when raw dollar fields are zero. If Airtable stores a stale value, both surfaces show it consistently — but still wrong.
- **`ebitda` field units:** Both surfaces multiply the `ebitda` Airtable field by 1000 (`ebitda * 1000 / revenue`) because Airtable stores EBITDA in thousands. If this ever changes, update both `company_ratios.py` and `group_ratios.py` together.
- **Cash flow requires prior year data:** `get_cash_flow_ratios()` needs the prior-year balance sheet. Companies missing prior-year data will show N/A for OCF/FCF/NCF — this is correct behavior, not a bug.

## Testing

Run the app and verify:
1. Login flow works
2. Company/Group analysis pages load
3. Gauge charts show correct colors
4. Excel export includes formatting

## Gotchas

- IMPORTANT: Airtable stores percentages as decimals (0.35 not 35%)
- IMPORTANT: Airtable `ebitda` and `interest_bearing_debt` fields are stored in thousands (e.g., 780.277 = $780,277)
- Admin pages must call `create_page_header()` BEFORE `apply_all_styles()`
- Export utils are lazy-loaded - don't import at module level
- Cookie validation runs on EVERY request for security
- Homepage rankings are **hardcoded** in `financial_dashboard.py` for performance — must be manually updated when companies submit new data
- `CURRENT_YEAR` in `shared/year_config.py` controls which period all pages fetch — update it when rolling to a new competition year
- `get_balance_sheet_data()` and `get_income_statement_data()` in `airtable_connection.py` use `CURRENT_YEAR` for their period filter (not hardcoded year)
- Custom analysis tool uses `calculated_percentage` type with explicit `calculation` key for NPM and EBITDA% — do NOT map to Airtable formula fields that don't exist or are wrong
- Negative percentage detection: use `abs(value) < 1 and value != 0` not `0 < value < 1` (the latter misses negatives like -0.062)
- Companies without prior year data will have cash flow ratios unavailable since CF calculation requires YoY balance sheet changes
---
*See `docs/CHANGELOG.md` for detailed implementation history.*
