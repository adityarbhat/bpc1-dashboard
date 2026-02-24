"""
Validation Script: Compare Python-calculated cash flow ratios vs Airtable-stored values

This script validates that our new calculation function produces the same results
as the manually-entered values in Airtable for existing data.

Run this BEFORE switching the dashboard to use calculated values.

Usage:
    source venv/bin/activate
    python scripts/validate_cash_flow_calculations.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.airtable_connection import get_airtable_connection, get_companies_cached
from shared.cash_flow_utils import get_cash_flow_ratios

# Suppress Streamlit warnings when running as script
import streamlit as st
st.cache_data.clear()


def validate_cash_flow_calculations():
    """Compare calculated values vs Airtable values for all companies/years."""

    print("=" * 70)
    print("CASH FLOW RATIO VALIDATION")
    print("Comparing Python calculations vs Airtable stored values")
    print("=" * 70)

    airtable = get_airtable_connection()
    companies = get_companies_cached()
    years = ['2021', '2022', '2023', '2024']  # 2020 won't have prior year data

    # Tolerance for floating point comparison (0.5% difference allowed)
    TOLERANCE = 0.005

    results = {
        'matches': 0,
        'mismatches': 0,
        'missing_airtable': 0,
        'missing_calculated': 0,
        'details': []
    }

    for company in companies:
        company_name = company['name']
        print(f"\n📊 {company_name}")
        print("-" * 50)

        for year in years:
            period = f"{year} Annual"

            # Get Airtable values
            bs_data = airtable.get_balance_sheet_data_by_period(company_name, period)
            airtable_values = bs_data[0] if bs_data else {}

            # Get calculated values
            calculated = get_cash_flow_ratios(airtable, company_name, year)

            for metric in ['ocf_rev', 'fcf_rev', 'ncf_rev']:
                airtable_val = airtable_values.get(metric)
                calc_val = calculated.get(metric)

                # Convert Airtable percentage to decimal if needed
                if airtable_val is not None and abs(airtable_val) > 1:
                    airtable_val = airtable_val / 100  # Convert 7.2 to 0.072

                # Compare values
                if airtable_val is None and calc_val is None:
                    status = "⚪ Both None"
                    results['missing_airtable'] += 1
                elif airtable_val is None:
                    status = "🟡 Airtable missing"
                    results['missing_airtable'] += 1
                elif calc_val is None:
                    status = "🟠 Calc missing (no prior year?)"
                    results['missing_calculated'] += 1
                else:
                    diff = abs(airtable_val - calc_val)
                    if diff <= TOLERANCE:
                        status = "✅ Match"
                        results['matches'] += 1
                    else:
                        status = f"❌ MISMATCH (diff: {diff:.4f})"
                        results['mismatches'] += 1
                        results['details'].append({
                            'company': company_name,
                            'year': year,
                            'metric': metric,
                            'airtable': airtable_val,
                            'calculated': calc_val,
                            'diff': diff
                        })

                # Format values for display
                at_display = f"{airtable_val*100:.1f}%" if airtable_val is not None else "None"
                calc_display = f"{calc_val*100:.1f}%" if calc_val is not None else "None"

                print(f"  {year} {metric}: AT={at_display:>8} | Calc={calc_display:>8} | {status}")

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"✅ Matches:           {results['matches']}")
    print(f"❌ Mismatches:        {results['mismatches']}")
    print(f"🟡 Missing Airtable:  {results['missing_airtable']}")
    print(f"🟠 Missing Calculated: {results['missing_calculated']}")

    if results['mismatches'] > 0:
        print("\n⚠️  MISMATCH DETAILS:")
        for detail in results['details']:
            print(f"  {detail['company']} {detail['year']} {detail['metric']}:")
            print(f"    Airtable:   {detail['airtable']*100:.2f}%")
            print(f"    Calculated: {detail['calculated']*100:.2f}%")
            print(f"    Difference: {detail['diff']*100:.2f}%")

    if results['mismatches'] == 0:
        print("\n🎉 All values match! Safe to proceed with the switchover.")
    else:
        print("\n⚠️  Some mismatches found. Investigate before switching over.")

    return results


if __name__ == "__main__":
    validate_cash_flow_calculations()
