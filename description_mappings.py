"""
Description mappings for Balance Sheet and Income Statement line items.
Descriptions are sourced from the Chart of Accounts in the Glossary page.
"""

# Balance Sheet Descriptions
BALANCE_SHEET_DESCRIPTIONS = {
    # Current Assets
    'cash_and_cash_equivalents': 'All cash and money market type investments',
    'trade_accounts_receivable': 'Receivables generated from customers in the course of business',
    'receivables': 'Amount owed by Van Line (if positive) or owed to Van Line (if negative)',
    'other_receivables': 'Amounts owed by drivers, employees, etc.',
    'prepaid_expenses': 'Any prepaid expenses',
    'related_company_receivables': 'All receivables owing from related companies',
    'owner_receivables': 'All receivables owing from owners',
    'other_current_assets': 'Packing supplies, investments not included in cash, etc.',

    # Fixed Assets
    'gross_fixed_assets': 'All equipment, land, buildings, leasehold improvements, furniture and fixtures',
    'accumulated_depreciation': 'All accumulated depreciation and amortization (enter as negative number)',

    # Other Assets
    'inter_company_receivable': 'All amounts owed by a related company',
    'other_assets': 'Hauling authorities, cash value life insurance, investment in other companies, condos, boats, long term owner receivables, etc.',

    # Current Liabilities
    'notes_payable_bank': 'Bank revolving line of credit outstanding',
    'notes_payable_owners': '',  # Not in glossary
    'trade_accounts_payable': 'Accounts payable to vendors, suppliers, other agents, etc.',
    'accrued_expenses': 'Salary, vacation pay, interest, etc.',
    'current_portion_ltd': 'Current portion of interest bearing long term debt',
    'inter_company_payable': 'All amounts owed to a related company',
    'other_current_liabilities': 'Deferred taxes, income tax payable, etc.',

    # Long-term Liabilities
    'eid_loan': '',  # Not in glossary
    'long_term_debt': 'All interest bearing non-owner debt and non inter-company debt',
    'notes_payable_owners_lt': 'Amounts due to owners - long term',
    'inter_company_debt': 'All amounts owed to a related company',
    'other_lt_liabilities': 'Life insurance loans, etc.',

    # Equity
    'owners_equity': 'Assets minus liabilities (Net Worth)',
}

# Income Statement Descriptions
INCOME_STATEMENT_DESCRIPTIONS = {
    # Revenue
    'intra_state_hhg': 'Transportation revenues generated under an intrastate tariff',
    'local_hhg': 'Revenues defined by an intrastate tariff as local',
    'inter_state_hhg': 'Transportation revenues generated under an interstate tariff',
    'office_industrial': 'All local commercial revenue except HHG',
    'warehouse': 'All permanent and SIT revenue',
    'warehouse_handling': '',  # Not in glossary - warehouse handling revenue
    'international': 'All international revenue including pickup, packing, crating, delivery',
    'packing_unpacking': 'All revenue for packing, unpacking and container revenue',
    'booking_royalties': 'Sales booking revenue and Operating Authority royalties',
    'special_products': 'All special product revenue and HVP transportation',
    'records_storage': 'All records storage revenue',
    'military_dpm_contracts': 'Revenues from Direct Procurement Method military contracts',
    'distribution': 'All distribution revenue',
    'hotel_deliveries': 'All revenues from hotel deliveries',
    'other_revenue': 'Any misc. operational revenue not listed elsewhere',

    # Direct Expenses
    'direct_wages': 'Salaries, wages, and bonuses paid to operations personnel',
    'vehicle_operating_expenses': 'Repairs, fuel, license, registration, tires, permits for revenue equipment',
    'packing_warehouse_supplies': 'Moving and packing supplies',
    'oo_exp_intra_state': 'Payments to owner operators for intrastate jobs',
    'oo_inter_state': 'Payments to owner operators for interstate jobs',
    'oo_oi': 'Payments to owner operators for office & industrial jobs',
    'oo_packing': 'Payments to owner operators for packing jobs',
    'oo_other': 'Payments to owner operators for other job types',
    'claims': 'All operational claims',
    'other_trans_exp': 'Trip expense, deadhead miles, agent fees, freight, BIPD',
    'depreciation': 'Depreciation on assets (excluding buildings)',
    'lease_expense_rev_equip': 'All lease expense on revenue equipment',
    'rent': 'Actual or estimated fair market rent',
    'other_direct_expenses': 'Credit card fees and other direct expenses not otherwise classified',

    # Operating Expenses
    'advertising_marketing': 'Advertising, brochures, yellow pages, promotional items',
    'bad_debts': 'Uncollectible accounts receivable written off',
    'sales_commissions': 'Salaries, commissions, and draws for sales people',
    'contributions': '',  # Not in glossary - charitable contributions
    'computer_support': 'IT expenses, software licensing, satellite tracking',
    'dues_sub': '',  # Not in glossary - dues and subscriptions
    'pr_taxes_benefits': 'Payroll taxes, health insurance, drug testing, DOT physicals, training',
    'equipment_leases_office_equip': '',  # Not in glossary - office equipment leases
    'workmans_comp_insurance': '',  # Not in glossary - workers compensation insurance
    'insurance': 'Cargo, fleet, general liability insurance',
    'legal_accounting': 'Legal and accounting work, tax return preparation',
    'office_expense': 'Office & printer supplies, printed forms, coffee, janitorial',
    'other_admin': '',  # Not in glossary - other administrative expenses
    'pension_profit_sharing_401k': '',  # Not in glossary - retirement benefits
    'prof_fees': 'Consultants, detectives, non-trade professionals',
    'repairs_maint': '',  # Not in glossary - repairs and maintenance
    'salaries_admin': 'All non-operations salaries (admin, office, dispatch, sales support)',
    'taxes_licenses': 'All taxes and licenses not related to vehicles or income',
    'tel_fax_utilities_internet': 'All communication and utility expenses',
    'travel_ent': 'Admin/sales related transportation, meals, lodging',
    'vehicle_expense_admin': '',  # Not in glossary - administrative vehicle expenses

    # Other Income/Expenses
    'other_income': 'Interest income, gain on sale of asset, litigation income',
    'ceo_comp': 'All salaries, bonuses or perks paid to CEO (enter as negative)',
    'other_expense': 'Loss on sale of asset, research of new business lines (enter as negative)',
    'interest_expense': 'All interest paid on interest bearing debt (enter as negative)',

    # Labor Analysis
    'administrative_employees': 'Total number of admin employees (FTE). Include CEO, dispatch, office, managers, salaried sales. Exclude commissioned and hourly warehouse.',
}
