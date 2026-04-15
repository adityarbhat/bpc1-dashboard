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
| `company_ratios.py` | Gauge charts with red/yellow/green thresholds |
| `group_ratios.py:307-319` | Ratio threshold definitions |
| `group_income_statement.py` | Profit margin rows color-coded via `get_cell_color` from `group_ratios` (Range Key thresholds) |
| `excel_formatter.py` | Export color coding (matches web display) |
| `pages/data_input/excel_parser.py` | Upload template parsing |

## Testing

Run the app and verify:
1. Login flow works
2. Company/Group analysis pages load
3. Gauge charts show correct colors
4. Excel export includes formatting

## Gotchas

- IMPORTANT: Airtable stores percentages as decimals (0.35 not 35%)
- Admin pages must call `create_page_header()` BEFORE `apply_all_styles()`
- Export utils are lazy-loaded - don't import at module level
- Cookie validation runs on EVERY request for security
- Homepage rankings are **hardcoded** in `financial_dashboard.py` for performance — must be manually updated when companies submit new data
- `CURRENT_YEAR` in `shared/year_config.py` controls which period all pages fetch — update it when rolling to a new competition year
- `get_balance_sheet_data()` and `get_income_statement_data()` in `airtable_connection.py` use `CURRENT_YEAR` for their period filter (not hardcoded year)
- Companies without prior year data (e.g., AMJ missing 2024) will have cash flow ratios unavailable since CF calculation requires YoY balance sheet changes

---
*See `docs/CHANGELOG.md` for detailed implementation history.*
