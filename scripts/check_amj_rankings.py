"""
Standalone ranking calculator — fetches live Airtable data and replicates
the calculate_group_rankings() logic from group_ratios.py.

Run from project root:
    python scripts/check_amj_rankings.py

Uses admin-level filter (sees submitted + published + legacy records),
so it includes any newly uploaded data.
"""

import os, sys, requests
from dotenv import load_dotenv

load_dotenv()
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
PAT = os.getenv("AIRTABLE_PAT")
if not BASE_ID or not PAT:
    sys.exit("ERROR: AIRTABLE_BASE_ID and AIRTABLE_PAT must be set in .env")

HEADERS = {"Authorization": f"Bearer {PAT}"}
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}"

# Admin filter: sees submitted, published, and legacy (blank) records
PUB_FILTER = "OR({publication_status}='submitted',{publication_status}='published',{publication_status}=BLANK())"

CURRENT_YEAR = "2025"
PRIOR_YEAR = "2024"
CURRENT_PERIOD = f"{CURRENT_YEAR} Annual"
PRIOR_PERIOD = f"{PRIOR_YEAR} Annual"


def fetch_all(table, params=None):
    url = f"{BASE_URL}/{table}"
    out, offset = [], None
    while True:
        p = dict(params or {})
        if offset:
            p["offset"] = offset
        r = requests.get(url, headers=HEADERS, params=p)
        if r.status_code != 200:
            print(f"  ERROR fetching {table}: {r.status_code} — {r.text[:200]}")
            return out
        d = r.json()
        out.extend(d.get("records", []))
        offset = d.get("offset")
        if not offset:
            break
    return out


def parse_float(v):
    if v is None:
        return 0.0
    if isinstance(v, str):
        v = v.replace('%', '').strip()
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def build_company_id_map():
    """Build {record_id: company_name} map from the companies table."""
    records = fetch_all("companies")
    return {
        r["id"]: (r["fields"].get("company_name") or r["fields"].get("Name") or r["id"])
        for r in records
    }


def fetch_table_by_period(table_name, period, id_to_name):
    """Fetch all records for a given period across all companies (admin view)."""
    filter_formula = f"AND({{period}}='{period}',{PUB_FILTER})"
    records = fetch_all(table_name, {"filterByFormula": filter_formula})
    # company field is a linked-record array of rec IDs — resolve to name
    by_company = {}
    for r in records:
        f = r["fields"]
        company_ref = f.get("company", [])
        if isinstance(company_ref, list) and company_ref:
            name = id_to_name.get(company_ref[0], company_ref[0])
        else:
            name = str(company_ref)
        if name:
            by_company[name] = f
    return by_company


def calc_cash_flow(current_bs, prior_bs, current_is):
    """Replicate _calculate_cash_flow_for_year() from cash_flow_utils.py"""
    result = {"ocf_rev": None, "fcf_rev": None, "ncf_rev": None}
    if not prior_bs or not current_bs or not current_is:
        return result

    # Revenue — fall back to summing line items if total is 0
    revenue = parse_float(current_is.get("total_revenue", 0))
    if not revenue:
        line_items = [
            "intra_state_hhg", "local_hhg", "inter_state_hhg", "office_industrial",
            "warehouse", "warehouse_handling", "international", "packing_unpacking",
            "booking_royalties", "special_products", "records_storage",
            "military_dpm_contracts", "distribution", "hotel_deliveries", "other_revenue",
        ]
        revenue = sum(parse_float(current_is.get(f, 0)) for f in line_items)
    if not revenue:
        return result

    # Net profit — fall back to computing from components if 0
    net_profit = parse_float(current_is.get("profit_before_tax_with_ppp", 0))
    if not net_profit:
        direct_fields = [
            "direct_wages", "vehicle_operating_expenses", "packing_warehouse_supplies",
            "oo_exp_intra_state", "oo_inter_state", "oo_oi", "oo_packing", "oo_other",
            "claims", "other_trans_exp", "depreciation", "lease_expense_rev_equip",
            "rent", "other_direct_expenses",
        ]
        op_fields = [
            "advertising_marketing", "bad_debts", "sales_commissions", "contributions",
            "computer_support", "dues_sub", "pr_taxes_benefits",
            "equipment_leases_office_equip", "workmans_comp_insurance", "insurance",
            "legal_accounting", "office_expense", "other_admin",
            "pension_profit_sharing_401k", "prof_fees", "repairs_maint", "salaries_admin",
            "taxes_licenses", "tel_fax_utilities_internet", "travel_ent",
            "vehicle_expense_admin",
        ]
        total_direct = sum(parse_float(current_is.get(f, 0)) for f in direct_fields)
        total_op = sum(parse_float(current_is.get(f, 0)) for f in op_fields)
        gross = revenue - total_direct
        op_profit = gross - total_op
        non_op = sum(
            parse_float(current_is.get(f, 0))
            for f in ["other_income", "ceo_comp", "other_expense", "interest_expense"]
        )
        net_profit = op_profit + non_op

    # OCF
    prior_ca = parse_float(prior_bs.get("total_current_assets", 0)) - parse_float(prior_bs.get("cash_and_cash_equivalents", 0))
    current_ca = (parse_float(current_bs.get("total_current_assets", 0))
                  - parse_float(current_bs.get("cash_and_cash_equivalents", 0))
                  - parse_float(current_bs.get("notes_payable_owners", 0)))
    change_ca = prior_ca - current_ca

    current_cl = (parse_float(current_bs.get("total_current_liabilities", 0))
                  - parse_float(current_bs.get("current_portion_ltd", 0))
                  - parse_float(current_bs.get("notes_payable_bank", 0)))
    prior_cl = (parse_float(prior_bs.get("total_current_liabilities", 0))
                - parse_float(prior_bs.get("current_portion_ltd", 0))
                - parse_float(prior_bs.get("notes_payable_bank", 0))
                - parse_float(prior_bs.get("notes_payable_owners", 0)))
    change_cl = current_cl - prior_cl

    change_nfa = parse_float(prior_bs.get("net_fixed_assets", 0)) - parse_float(current_bs.get("net_fixed_assets", 0))
    change_nca = (
        (parse_float(prior_bs.get("other_assets", 0)) + parse_float(prior_bs.get("inter_company_receivable", 0)))
        - (parse_float(current_bs.get("other_assets", 0)) + parse_float(current_bs.get("inter_company_receivable", 0)))
    )

    ocf = net_profit + change_ca + change_cl + change_nfa + change_nca
    result["ocf_rev"] = ocf / revenue

    # FCF
    current_bank = (parse_float(current_bs.get("notes_payable_bank", 0))
                    + parse_float(current_bs.get("current_portion_ltd", 0))
                    + parse_float(current_bs.get("long_term_debt", 0)))
    prior_bank = (parse_float(prior_bs.get("notes_payable_bank", 0))
                  + parse_float(prior_bs.get("current_portion_ltd", 0))
                  + parse_float(prior_bs.get("long_term_debt", 0)))
    change_bank = current_bank - prior_bank

    current_owner = parse_float(current_bs.get("notes_payable_owners", 0)) + parse_float(current_bs.get("notes_payable_owners_lt", 0))
    prior_owner = parse_float(prior_bs.get("notes_payable_owners", 0)) + parse_float(prior_bs.get("notes_payable_owners_lt", 0))
    change_owner = current_owner - prior_owner

    current_ncl = parse_float(current_bs.get("inter_company_debt", 0)) + parse_float(current_bs.get("other_lt_liabilities", 0))
    prior_ncl = parse_float(prior_bs.get("inter_company_debt", 0)) + parse_float(prior_bs.get("other_lt_liabilities", 0))
    change_ncl = current_ncl - prior_ncl

    equity_adj = (parse_float(current_bs.get("owners_equity", 0)) - parse_float(prior_bs.get("owners_equity", 0))) - net_profit

    fcf = change_bank + change_owner + change_ncl + equity_adj
    result["fcf_rev"] = fcf / revenue

    result["ncf_rev"] = (ocf + fcf) / revenue
    return result


def calculate_rankings(ratio_data, metric_key, reverse=False):
    """Replicates calculate_rankings() from group_ratios.py."""
    company_values = [
        (company, metrics[metric_key])
        for company, metrics in ratio_data.items()
        if metrics.get(metric_key) not in (None, 0)
    ]
    if reverse:
        pos = sorted([(c, v) for c, v in company_values if v >= 0], key=lambda x: x[1])
        neg = sorted([(c, v) for c, v in company_values if v < 0], key=lambda x: x[1], reverse=True)
        ordered = pos + neg
    else:
        ordered = sorted(company_values, key=lambda x: x[1], reverse=True)
    return {company: rank for rank, (company, _) in enumerate(ordered, start=1)}


def main():
    print(f"\n{'='*70}")
    print(f"  BPC1 GROUP RANKINGS — {CURRENT_PERIOD} (live Airtable data, admin view)")
    print(f"{'='*70}\n")

    # ── 1. Fetch all data ──────────────────────────────────────────────────
    print("Building company ID map...")
    id_to_name = build_company_id_map()
    print(f"  → {len(id_to_name)} companies: {sorted(id_to_name.values())}\n")

    print("Fetching balance sheet data (2025 Annual)...")
    bs_2025 = fetch_table_by_period("balance_sheet_data", CURRENT_PERIOD, id_to_name)
    print(f"  → {len(bs_2025)} companies found: {sorted(bs_2025.keys())}\n")

    print("Fetching income statement data (2025 Annual)...")
    is_2025 = fetch_table_by_period("income_statement_data", CURRENT_PERIOD, id_to_name)
    print(f"  → {len(is_2025)} companies found: {sorted(is_2025.keys())}\n")

    print("Fetching balance sheet data (2024 Annual) for cash flow calc...")
    bs_2024 = fetch_table_by_period("balance_sheet_data", PRIOR_PERIOD, id_to_name)
    print(f"  → {len(bs_2024)} companies found: {sorted(bs_2024.keys())}\n")

    # ── 2. Build ratio_data ────────────────────────────────────────────────
    all_companies = sorted(set(bs_2025.keys()) | set(is_2025.keys()))
    ratio_data = {}

    for company in all_companies:
        bs = bs_2025.get(company, {})
        is_ = is_2025.get(company, {})
        prior_bs = bs_2024.get(company, {})

        ca = parse_float(bs.get("total_current_assets", 0))
        cl = parse_float(bs.get("total_current_liabilities", 0))
        total_liab = parse_float(bs.get("total_liabilities", 0))
        equity = parse_float(bs.get("owners_equity", 0))
        total_assets = parse_float(bs.get("total_assets", 0))

        # Revenue for sales/assets
        rev = parse_float(is_.get("total_revenue", 0))
        if not rev:
            line_items = [
                "intra_state_hhg", "local_hhg", "inter_state_hhg", "office_industrial",
                "warehouse", "warehouse_handling", "international", "packing_unpacking",
                "booking_royalties", "special_products", "records_storage",
                "military_dpm_contracts", "distribution", "hotel_deliveries", "other_revenue",
            ]
            rev = sum(parse_float(is_.get(f, 0)) for f in line_items)

        gpm = (parse_float(is_.get("gross_profit", 0)) / rev) if rev > 0 else parse_float(is_.get("gpm", 0))
        opm = (parse_float(is_.get("operating_profit", 0)) / rev) if rev > 0 else parse_float(is_.get("opm", 0))
        npm_val = (parse_float(is_.get("profit_before_tax_with_ppp", 0)) / rev) if rev > 0 else parse_float(is_.get("npm", 0))
        ebitda_raw = parse_float(is_.get("ebitda", 0))
        ebitda_m = (ebitda_raw * 1000 / rev) if rev > 0 and ebitda_raw != 0 else parse_float(is_.get("ebitda_margin", 0))

        cf = calc_cash_flow(bs, prior_bs, is_)

        ratio_data[company] = {
            # AL metrics
            "current_ratio": (ca / cl) if cl > 0 else parse_float(bs.get("current_ratio", 0)),
            "debt_to_equity": (total_liab / equity) if equity > 0 else parse_float(bs.get("debt_to_equity", 0)),
            "working_capital_pct": parse_float(bs.get("working_capital_pct_asset", 0)),
            "survival_score": parse_float(bs.get("survival_score", 0)),
            "sales_assets": (rev / total_assets) if total_assets > 0 else 0,
            # Prof metrics
            "gpm": gpm,
            "opm": opm,
            "npm": npm_val,
            "rev_per_employee": parse_float(is_.get("rev_admin_employee", 0)),
            "ebitda_margin": ebitda_m,
            # CF metrics
            "dso": parse_float(bs.get("dso", 0)),
            "ocf_rev": cf.get("ocf_rev") or 0,
            "fcf_rev": cf.get("fcf_rev") or 0,
            "ncf_rev": cf.get("ncf_rev") or 0,
        }

    # ── 3. Calculate scores ────────────────────────────────────────────────
    al_metrics  = [("current_ratio", False), ("debt_to_equity", True),
                   ("working_capital_pct", False), ("survival_score", False), ("sales_assets", False)]
    prof_metrics = [("gpm", False), ("opm", False), ("npm", False),
                    ("rev_per_employee", False), ("ebitda_margin", False)]
    cf_metrics  = [("dso", True), ("ocf_rev", False), ("fcf_rev", False), ("ncf_rev", False)]

    al_points, prof_points, cf_points = {}, {}, {}
    for company in all_companies:
        al_points[company]   = sum(calculate_rankings(ratio_data, k, r).get(company, 0) for k, r in al_metrics)
        prof_points[company] = sum(calculate_rankings(ratio_data, k, r).get(company, 0) for k, r in prof_metrics)
        cf_points[company]   = sum(calculate_rankings(ratio_data, k, r).get(company, 0) for k, r in cf_metrics)

    total_scores = {
        c: al_points[c] + prof_points[c] + (cf_points[c] / 2)
        for c in all_companies
    }

    scored = sorted(((c, s) for c, s in total_scores.items() if s > 0), key=lambda x: x[1])

    # ── 4. Print results ───────────────────────────────────────────────────
    HARDCODED = {
        "Ace Worldwide": (1, 37.5),
        "AMJ":           (2, 46.5),
        "Guardian":      (3, 54.0),
        "Ace Relo":      (4, 55.0),
        "Alexanders":    (5, 58.5),
    }

    print(f"{'Rank':<6} {'Company':<20} {'Total':>7}  {'AL Pts':>7} {'Prof Pts':>9} {'CF Pts':>7}  {'Old Rank':>9} {'Old Score':>10}  {'Change':>8}")
    print("-" * 95)
    for rank, (company, score) in enumerate(scored, start=1):
        old_rank, old_score = HARDCODED.get(company, ("-", "-"))
        if isinstance(old_rank, int):
            delta = old_rank - rank
            change = f"▲ {delta}" if delta > 0 else (f"▼ {-delta}" if delta < 0 else "—")
            score_diff = f"({score - old_score:+.1f})"
        else:
            change = "NEW"
            score_diff = ""
        marker = " ◄ AMJ" if company == "AMJ" else ""
        print(f"  #{rank:<4} {company:<20} {score:>7.1f}  {al_points[company]:>7} {prof_points[company]:>9} {cf_points[company]:>7}  "
              f"{str(old_rank):>9} {str(old_score):>10}  {change:>8} {score_diff}{marker}")

    print()
    print("Metric-level raw values for AMJ:")
    amj = ratio_data.get("AMJ", {})
    if amj:
        fields = [
            ("current_ratio",    "Current Ratio",          "x",  False),
            ("debt_to_equity",   "Debt/Equity",             "x",  True),
            ("working_capital_pct","Working Capital %",     "%",  False),
            ("survival_score",   "Survival Score",          "x",  False),
            ("sales_assets",     "Sales/Assets",            "x",  False),
            ("gpm",              "Gross Profit Margin",     "%",  False),
            ("opm",              "Oper Profit Margin",      "%",  False),
            ("npm",              "Net Profit Margin",       "%",  False),
            ("rev_per_employee", "Rev/Employee ($K)",       "$K", False),
            ("ebitda_margin",    "EBITDA Margin",           "%",  False),
            ("dso",              "DSO (days)",              "d",  True),
            ("ocf_rev",          "OCF/Revenue",             "%",  False),
            ("fcf_rev",          "FCF/Revenue",             "%",  False),
            ("ncf_rev",          "NCF/Revenue",             "%",  False),
        ]
        for key, label, fmt, rev in fields:
            v = amj.get(key, 0) or 0
            rank = calculate_rankings(ratio_data, key, rev).get("AMJ", "-")
            if fmt == "%":
                print(f"  {label:<25}: {v*100:>7.2f}%   rank #{rank}")
            elif fmt == "x":
                print(f"  {label:<25}: {v:>7.2f}x   rank #{rank}")
            elif fmt == "$K":
                print(f"  {label:<25}: {v:>7.0f}    rank #{rank}")
            else:
                print(f"  {label:<25}: {v:>7.1f}    rank #{rank}")
    else:
        print("  No AMJ data found for 2025 Annual!")

    print()
    print("NOTE: Homepage rankings are hardcoded in financial_dashboard.py:707.")
    print("      If rankings changed, update that dict manually.")


if __name__ == "__main__":
    main()
