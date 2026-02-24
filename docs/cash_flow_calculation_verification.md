# Cash Flow Calculation Verification Document

**Purpose:** Document the cash flow calculation formulas and identify discrepancies for company verification.

---

## Cash Flow Calculation Formulas

The following formulas are used to calculate cash flow metrics from Balance Sheet and Income Statement data. All calculations require both **current year** and **prior year** data to compute year-over-year changes.

### Operating Cash Flow (OCF)

```
OCF = Net Profit
    + Change in Current Assets
    + Change in Current Liabilities
    + Change in Net Fixed Assets
    + Change in Non-Current Assets
```

**Component Details:**

| Component | Formula |
|-----------|---------|
| **Net Profit** | Profit Before Tax (from Income Statement) |
| **Δ Current Assets** | (Prior Year Total Current Assets - Prior Cash) − (Current Year Total Current Assets - Current Cash - Notes Payable Owners) |
| **Δ Current Liabilities** | (Current TCL - CPLTD - Notes Payable Bank) − (Prior TCL - CPLTD - Notes Payable Bank - Notes Payable Owners) |
| **Δ Net Fixed Assets** | Prior Year Net Fixed Assets − Current Year Net Fixed Assets |
| **Δ Non-Current Assets** | (Prior Other Assets + Prior Inter-Company Receivable) − (Current Other Assets + Current Inter-Company Receivable) |

---

### Financing Cash Flow (FCF)

```
FCF = Change in Bank Debt
    + Change in Owner Debt
    + Change in Non-Current Liabilities
    + Equity Adjustment
```

**Component Details:**

| Component | Formula |
|-----------|---------|
| **Δ Bank Debt** | (Current Notes Payable Bank + CPLTD + Long Term Debt) − (Prior Notes Payable Bank + CPLTD + Long Term Debt) |
| **Δ Owner Debt** | (Current Notes Payable Owners + NP Owners LT) − (Prior Notes Payable Owners + NP Owners LT) |
| **Δ Non-Current Liabilities** | (Current Inter-Company Debt + Other LT Liabilities) − (Prior Inter-Company Debt + Other LT Liabilities) |
| **Equity Adjustment** | (Current Owners Equity − Prior Owners Equity) − Net Profit |

---

### Net Cash Flow (NCF)

```
NCF = OCF + FCF
```

---

### Revenue Ratios

```
OCF/Revenue = Operating Cash Flow ÷ Total Revenue
FCF/Revenue = Financing Cash Flow ÷ Total Revenue
NCF/Revenue = Net Cash Flow ÷ Total Revenue
```

---

## Discrepancy Report: Companies Requiring Verification

The following companies show discrepancies between previously stored values (in Airtable) and newly calculated values. These differences may be due to:
1. Manual entry errors in the original data
2. Different calculation methodology used previously
3. Balance sheet data corrections made after ratios were originally entered

### ACE Moving & WH

| Year | Metric | Previously Stored | Calculated | Difference |
|------|--------|-------------------|------------|------------|
| 2021 | FCF/Revenue | 0.40% | 1.14% | 0.74% |
| 2021 | NCF/Revenue | -1.80% | -1.10% | 0.70% |
| 2022 | FCF/Revenue | 14.60% | 3.47% | **11.13%** |
| 2022 | NCF/Revenue | 19.10% | 7.98% | **11.12%** |
| 2024 | FCF/Revenue | -22.50% | -8.14% | **14.36%** |
| 2024 | NCF/Revenue | -9.40% | 4.95% | **14.35%** |

**Note:** OCF/Revenue values match for all years. The discrepancies are isolated to FCF and NCF calculations, suggesting a difference in how financing cash flow components were originally calculated.

---

### RC Mason

| Year | Metric | Previously Stored | Calculated | Difference |
|------|--------|-------------------|------------|------------|
| 2021 | OCF/Revenue | 13.60% | 11.51% | 2.09% |
| 2021 | FCF/Revenue | -5.50% | -0.35% | **5.15%** |
| 2021 | NCF/Revenue | 8.10% | 11.16% | 3.06% |
| 2022 | OCF/Revenue | 2.60% | 1.47% | 1.13% |
| 2022 | FCF/Revenue | -5.10% | -4.05% | 1.05% |

**Note:** 2023 and 2024 values match correctly. Discrepancies are limited to 2021 and 2022.

---

### Mabeys (Minor)

| Year | Metric | Previously Stored | Calculated | Difference |
|------|--------|-------------------|------------|------------|
| 2023 | NCF/Revenue | -11.50% | -12.00% | 0.50% |

**Note:** This is a minor rounding difference (within tolerance).

---

## Companies with Perfect Match

The following companies show **100% match** between stored and calculated values:

- ✅ Kaster (all years)
- ✅ Hopkins (2024 - only year with data)
- ✅ Bisson (2024 - only year with data)
- ✅ Coastal (all years)
- ✅ Winter (all years)
- ✅ Spirit (all years)
- ✅ A-1 (all years)

---

## Recommended Actions

1. **For Ace:** Review 2021, 2022, and 2024 balance sheet data, particularly:
   - Bank debt components (Notes Payable Bank, CPLTD, Long Term Debt)
   - Owner debt components (Notes Payable Owners)
   - Inter-company debt and other LT liabilities
   - Equity changes

2. **For RC Mason:** Review 2021 and 2022 balance sheet data, particularly:
   - Current asset and liability changes
   - Debt component changes
   - Equity adjustments

3. **General:** Confirm the calculation methodology above matches your expected approach for cash flow analysis.

---

## Abbreviations

| Abbreviation | Meaning |
|--------------|---------|
| TCA | Total Current Assets |
| TCL | Total Current Liabilities |
| CPLTD | Current Portion of Long Term Debt |
| NPB | Notes Payable Bank |
| NP Owners | Notes Payable Owners |
| LTD | Long Term Debt |
| NP Owners LT | Notes Payable Owners (Long Term) |
| Inter-Co | Inter-Company |
| LT | Long Term |

---

