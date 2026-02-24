# Feature Deep Dive: Cash Flow Calculations

## Overview

This deep dive covers the centralized cash flow calculation system that computes OCF, FCF, and NCF ratios from balance sheet and income statement data. You'll learn the financial formulas, the implementation approach, and caching strategies.

**What You'll Learn:**
- Operating Cash Flow (OCF) calculation
- Financing Cash Flow (FCF) calculation
- Net Cash Flow (NCF) calculation
- Year-over-year change methodology
- Caching patterns for expensive calculations

**Difficulty:** Intermediate
**Time:** 45-60 minutes

---

## The Cash Flow Challenge

### Requirements

Build a cash flow system that:
1. Calculates OCF, FCF, NCF from existing balance sheet and income statement data
2. Computes ratios as percentage of revenue
3. Handles missing prior-year data gracefully
4. Caches results for performance
5. Supports multi-year trend analysis

### Cash Flow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Cash Flow Components                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Operating Cash Flow (OCF)                                       │
│  ├── Net Profit                                                  │
│  ├── + Change in Current Assets (working capital)               │
│  ├── + Change in Current Liabilities                            │
│  ├── + Change in Net Fixed Assets (depreciation + capex)        │
│  └── + Change in Non-Current Assets                              │
│                                                                  │
│  Financing Cash Flow (FCF)                                       │
│  ├── Change in Bank Debt                                         │
│  ├── + Change in Owner Debt                                      │
│  ├── + Change in Non-Current Liabilities                         │
│  └── + Equity Adjustment (equity changes - net profit)          │
│                                                                  │
│  Net Cash Flow (NCF) = OCF + FCF                                │
│                                                                  │
│  Ratios expressed as: OCF/Revenue, FCF/Revenue, NCF/Revenue     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core File

```
shared/
└── cash_flow_utils.py    # Centralized calculations (228 lines)
```

---

## The Math: Operating Cash Flow

### Formula

```
OCF = Net Profit
    + Δ Current Assets (excluding cash and owner notes)
    + Δ Current Liabilities (excluding debt items)
    + Δ Net Fixed Assets
    + Δ Non-Current Assets
```

### Working Capital Components

```python
# Current Assets (for OCF calculation)
current_assets_for_ocf = (
    accounts_receivable
    + prepaid_expenses
    + other_current_assets
    # Excludes: cash, notes_receivable_owner
)

# Current Liabilities (for OCF calculation)
current_liabilities_for_ocf = (
    accounts_payable
    + accrued_liabilities
    # Excludes: notes_payable_bank, notes_payable_owners, current_portion_ltd
)

# Non-Current Assets
non_current_assets = (
    other_assets
    + inter_company_receivable
)
```

### Implementation

```python
# File: shared/cash_flow_utils.py

def _calculate_ocf(
    current_balance: dict,
    prior_balance: dict,
    current_income: dict
) -> float | None:
    """
    Calculate Operating Cash Flow.

    Args:
        current_balance: Current year balance sheet
        prior_balance: Prior year balance sheet
        current_income: Current year income statement

    Returns:
        OCF value or None if calculation not possible
    """
    # Get net profit
    net_profit = current_income.get('net_profit', 0)

    if net_profit is None:
        return None

    # Current year working capital components
    current_ca = (
        current_balance.get('accounts_receivable', 0) +
        current_balance.get('prepaid_expenses', 0) +
        current_balance.get('other_current_assets', 0)
    )

    current_cl = (
        current_balance.get('accounts_payable', 0) +
        current_balance.get('accrued_liabilities', 0)
    )

    current_nfa = current_balance.get('net_fixed_assets', 0)

    current_nca = (
        current_balance.get('other_assets', 0) +
        current_balance.get('inter_company_receivable', 0)
    )

    # Prior year working capital components
    prior_ca = (
        prior_balance.get('accounts_receivable', 0) +
        prior_balance.get('prepaid_expenses', 0) +
        prior_balance.get('other_current_assets', 0)
    )

    prior_cl = (
        prior_balance.get('accounts_payable', 0) +
        prior_balance.get('accrued_liabilities', 0)
    )

    prior_nfa = prior_balance.get('net_fixed_assets', 0)

    prior_nca = (
        prior_balance.get('other_assets', 0) +
        prior_balance.get('inter_company_receivable', 0)
    )

    # Calculate changes (note: increase in assets = cash outflow = negative)
    delta_ca = prior_ca - current_ca  # Decrease in CA = cash inflow
    delta_cl = current_cl - prior_cl  # Increase in CL = cash inflow
    delta_nfa = prior_nfa - current_nfa  # Decrease in NFA = cash inflow
    delta_nca = prior_nca - current_nca  # Decrease in NCA = cash inflow

    # OCF calculation
    ocf = net_profit + delta_ca + delta_cl + delta_nfa + delta_nca

    return ocf
```

---

## The Math: Financing Cash Flow

### Formula

```
FCF = Δ Bank Debt
    + Δ Owner Debt
    + Δ Non-Current Liabilities
    + Equity Adjustment
```

### Debt Components

```python
# Bank Debt
bank_debt = (
    notes_payable_bank
    + current_portion_ltd
    + long_term_debt
)

# Owner Debt
owner_debt = (
    notes_payable_owners
    + notes_payable_owners_lt
)

# Non-Current Liabilities
non_current_liabilities = (
    inter_company_debt
    + other_lt_liabilities
)

# Equity Adjustment (captures distributions/contributions)
equity_adjustment = (current_equity - prior_equity) - net_profit
```

### Implementation

```python
def _calculate_fcf(
    current_balance: dict,
    prior_balance: dict,
    current_income: dict
) -> float | None:
    """
    Calculate Financing Cash Flow.
    """
    net_profit = current_income.get('net_profit', 0)

    # Current year debt components
    current_bank_debt = (
        current_balance.get('notes_payable_bank', 0) +
        current_balance.get('current_portion_ltd', 0) +
        current_balance.get('long_term_debt', 0)
    )

    current_owner_debt = (
        current_balance.get('notes_payable_owners', 0) +
        current_balance.get('notes_payable_owners_lt', 0)
    )

    current_ncl = (
        current_balance.get('inter_company_debt', 0) +
        current_balance.get('other_lt_liabilities', 0)
    )

    current_equity = current_balance.get('total_equity', 0)

    # Prior year debt components
    prior_bank_debt = (
        prior_balance.get('notes_payable_bank', 0) +
        prior_balance.get('current_portion_ltd', 0) +
        prior_balance.get('long_term_debt', 0)
    )

    prior_owner_debt = (
        prior_balance.get('notes_payable_owners', 0) +
        prior_balance.get('notes_payable_owners_lt', 0)
    )

    prior_ncl = (
        prior_balance.get('inter_company_debt', 0) +
        prior_balance.get('other_lt_liabilities', 0)
    )

    prior_equity = prior_balance.get('total_equity', 0)

    # Calculate changes (increase in debt/equity = cash inflow)
    delta_bank = current_bank_debt - prior_bank_debt
    delta_owner = current_owner_debt - prior_owner_debt
    delta_ncl = current_ncl - prior_ncl

    # Equity adjustment: equity changes not from profit
    equity_adjustment = (current_equity - prior_equity) - net_profit

    # FCF calculation
    fcf = delta_bank + delta_owner + delta_ncl + equity_adjustment

    return fcf
```

---

## Net Cash Flow

```python
def _calculate_ncf(ocf: float | None, fcf: float | None) -> float | None:
    """
    Calculate Net Cash Flow.

    NCF = OCF + FCF
    """
    if ocf is None or fcf is None:
        return None

    return ocf + fcf
```

---

## Revenue Ratios

### Why Ratios?

Raw cash flow numbers aren't comparable across companies of different sizes. Revenue ratios normalize the data:

```
Company A: OCF = $500,000, Revenue = $10,000,000
→ OCF/Revenue = 5%

Company B: OCF = $50,000, Revenue = $1,000,000
→ OCF/Revenue = 5%

Both companies have the same cash flow efficiency!
```

### Implementation

```python
def _calculate_cash_flow_for_year(
    current_balance: dict,
    prior_balance: dict,
    current_income: dict
) -> dict:
    """
    Calculate all cash flow ratios for a year.

    Returns:
        {
            'ocf_rev': float,  # OCF / Revenue (decimal, e.g., 0.072 = 7.2%)
            'fcf_rev': float,  # FCF / Revenue
            'ncf_rev': float,  # NCF / Revenue
        }
    """
    result = {
        'ocf_rev': None,
        'fcf_rev': None,
        'ncf_rev': None,
    }

    # Get revenue for ratio calculation
    revenue = current_income.get('total_revenue', 0)

    if not revenue or revenue == 0:
        return result  # Can't calculate ratios without revenue

    # Calculate components
    ocf = _calculate_ocf(current_balance, prior_balance, current_income)
    fcf = _calculate_fcf(current_balance, prior_balance, current_income)
    ncf = _calculate_ncf(ocf, fcf)

    # Calculate ratios (as decimals)
    if ocf is not None:
        result['ocf_rev'] = ocf / revenue

    if fcf is not None:
        result['fcf_rev'] = fcf / revenue

    if ncf is not None:
        result['ncf_rev'] = ncf / revenue

    return result
```

---

## Caching Strategy

### Single Company/Year

```python
@st.cache_data(ttl=1800)  # 30 minute cache
def get_cash_flow_ratios(
    _airtable,
    company_name: str,
    year: int
) -> dict | None:
    """
    Get cash flow ratios for a single company/year.
    Cached for 30 minutes.

    Args:
        _airtable: AirtableConnection (prefixed with _ for cache compatibility)
        company_name: Company name
        year: Year to calculate

    Returns:
        Dict with ocf_rev, fcf_rev, ncf_rev or None
    """
    # Get current year data
    current_period = f"{year} Annual"
    prior_period = f"{year - 1} Annual"

    current_balance = _airtable.get_balance_sheet_data_by_period(
        company_name, current_period
    )
    prior_balance = _airtable.get_balance_sheet_data_by_period(
        company_name, prior_period
    )
    current_income = _airtable.get_income_statement_data_by_period(
        company_name, current_period
    )

    # Need current year data and prior year for changes
    if not current_balance or not current_income:
        return None

    # Prior year can be empty (first year)
    prior_bs = prior_balance[0] if prior_balance else {}
    current_bs = current_balance[0]
    current_is = current_income[0]

    return _calculate_cash_flow_for_year(current_bs, prior_bs, current_is)
```

### Bulk Calculation (Group Pages)

```python
@st.cache_data(ttl=1800)
def get_all_companies_cash_flow_ratios(
    _airtable,
    year: int,
    companies: list
) -> dict:
    """
    Get cash flow ratios for all companies in one pass.
    Optimized for group analysis pages.

    Args:
        _airtable: AirtableConnection
        year: Year to calculate
        companies: List of company dicts with 'name' key

    Returns:
        Dict[company_name] -> {ocf_rev, fcf_rev, ncf_rev}
    """
    results = {}
    current_period = f"{year} Annual"
    prior_period = f"{year - 1} Annual"

    for company in companies:
        company_name = company['name']

        try:
            # Get data
            current_balance = _airtable.get_balance_sheet_data_by_period(
                company_name, current_period
            )
            prior_balance = _airtable.get_balance_sheet_data_by_period(
                company_name, prior_period
            )
            current_income = _airtable.get_income_statement_data_by_period(
                company_name, current_period
            )

            if current_balance and current_income:
                prior_bs = prior_balance[0] if prior_balance else {}
                current_bs = current_balance[0]
                current_is = current_income[0]

                results[company_name] = _calculate_cash_flow_for_year(
                    current_bs, prior_bs, current_is
                )
            else:
                results[company_name] = None

        except Exception:
            results[company_name] = None

    return results
```

### Multi-Year Trends

```python
@st.cache_data(ttl=1800)
def get_cash_flow_ratios_for_trends(
    _airtable,
    company_name: str,
    years: list = None
) -> dict:
    """
    Get cash flow ratios for multiple years (trend analysis).

    Args:
        _airtable: AirtableConnection
        company_name: Company name
        years: List of years (default: [2020, 2021, 2022, 2023, 2024])

    Returns:
        Dict[year] -> {ocf_rev, fcf_rev, ncf_rev}
    """
    if years is None:
        years = [2020, 2021, 2022, 2023, 2024]

    results = {}

    for year in years:
        ratios = get_cash_flow_ratios(_airtable, company_name, year)
        results[year] = ratios

    return results
```

---

## Special Cases

### Hopkins 2024 Exception

Some companies have hardcoded values when historical data isn't available:

```python
# In _calculate_cash_flow_for_year

def _calculate_cash_flow_for_year(
    current_balance: dict,
    prior_balance: dict,
    current_income: dict,
    company_name: str = None,
    year: int = None
) -> dict:
    """Calculate with special case handling."""

    # Hopkins 2024 special case (no prior year data available)
    if company_name == 'Hopkins' and year == 2024:
        return {
            'ocf_rev': -0.274,   # -27.4%
            'fcf_rev': 0.449,    # 44.9%
            'ncf_rev': 0.176,    # 17.6%
        }

    # Normal calculation...
```

---

## Usage in Dashboard

### Company Ratios Page

```python
# File: pages/company_pages/company_ratios.py

from shared.cash_flow_utils import get_cash_flow_ratios

def display_cash_flow_ratios(company_name: str, year: int):
    """Display cash flow ratio gauges."""
    from shared.airtable_connection import AirtableConnection
    from shared.chart_utils import create_gauge_chart

    airtable = AirtableConnection()
    ratios = get_cash_flow_ratios(airtable, company_name, year)

    if not ratios:
        st.warning("Cash flow data not available")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        fig = create_gauge_chart(
            value=ratios['ocf_rev'] * 100,  # Convert to percentage
            title="OCF / Revenue",
            min_val=-20,
            max_val=20,
            threshold_red=2,
            threshold_yellow=5,
            format_type="percent",
            reverse_colors=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = create_gauge_chart(
            value=ratios['fcf_rev'] * 100,
            title="FCF / Revenue",
            min_val=-20,
            max_val=20,
            threshold_red=0,
            threshold_yellow=3,
            format_type="percent",
            reverse_colors=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        fig = create_gauge_chart(
            value=ratios['ncf_rev'] * 100,
            title="NCF / Revenue",
            min_val=-20,
            max_val=20,
            threshold_red=2,
            threshold_yellow=5,
            format_type="percent",
            reverse_colors=False
        )
        st.plotly_chart(fig, use_container_width=True)
```

### Group Cash Flow Page

```python
# File: pages/group_pages/group_cash_flow.py

from shared.cash_flow_utils import get_all_companies_cash_flow_ratios

def group_cash_flow_page():
    """Display all companies' cash flow ratios."""
    airtable = AirtableConnection()
    companies = airtable.get_companies_cached()
    year = st.session_state.get('selected_year', 2024)

    # Get all ratios in one batch
    all_ratios = get_all_companies_cash_flow_ratios(airtable, year, companies)

    # Build comparison table
    rows = []
    for company in companies:
        name = company['name']
        ratios = all_ratios.get(name, {})

        rows.append({
            'Company': name,
            'OCF/Rev': format_percent(ratios.get('ocf_rev')),
            'FCF/Rev': format_percent(ratios.get('fcf_rev')),
            'NCF/Rev': format_percent(ratios.get('ncf_rev')),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
```

---

## Key Takeaways

- **OCF** measures cash from operations (working capital changes + profit)
- **FCF** measures cash from financing activities (debt + equity changes)
- **NCF = OCF + FCF** shows overall cash position change
- **Revenue ratios** normalize for company size comparison
- **Prior year data required** for YoY change calculations
- **30-minute caching** balances freshness with performance
- **Bulk calculations** optimize group page performance

---

## Practice Exercise

**Challenge:** Add "Cash Conversion Cycle" metric

**Requirements:**
- Formula: (DSO + DIO) - DPO
- DSO = Days Sales Outstanding = (A/R / Revenue) * 365
- DIO = Days Inventory Outstanding = (Inventory / COGS) * 365
- DPO = Days Payable Outstanding = (A/P / COGS) * 365
- Lower is better (faster cash conversion)

<details>
<summary>Show Solution</summary>

```python
def calculate_cash_conversion_cycle(
    balance: dict,
    income: dict
) -> float | None:
    """
    Calculate Cash Conversion Cycle.

    CCC = DSO + DIO - DPO (lower is better)
    """
    ar = balance.get('accounts_receivable', 0)
    inventory = balance.get('inventory', 0)
    ap = balance.get('accounts_payable', 0)
    revenue = income.get('total_revenue', 0)
    cogs = income.get('cost_of_goods_sold', 0)

    if not revenue or not cogs:
        return None

    # Calculate components
    dso = (ar / revenue) * 365 if revenue else 0
    dio = (inventory / cogs) * 365 if cogs else 0
    dpo = (ap / cogs) * 365 if cogs else 0

    # Cash Conversion Cycle
    ccc = dso + dio - dpo

    return ccc
```

</details>

---

## Related Topics

- **[gauge-charts-implementation.md](gauge-charts-implementation.md)** - How gauges display these metrics
- **[06-data-transformation.md](../06-data-transformation.md)** - Data transformation patterns
- **[excel-export-system.md](excel-export-system.md)** - How cash flow is exported

---

*You now understand the complete cash flow calculation system!*
