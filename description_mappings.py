"""
Description mappings for Balance Sheet and Income Statement line items.
Descriptions are sourced from the BPC Upload Template Chart of Accounts.
"""

# Balance Sheet Descriptions
BALANCE_SHEET_DESCRIPTIONS = {
    # Current Assets
    'cash_and_cash_equivalents': 'All cash and money market type investments',
    'trade_accounts_receivable': 'All receivables generated in the course of business from customers',
    'receivables': 'Amount owed by Van Line (if positive) or owed to Van Line (if negative)',
    'other_receivables': 'All other receivables such as drivers, employees, etc.',
    'prepaid_expenses': 'Any prepaid expenses',
    'related_company_receivables': 'All receivables owing from related companies',
    'owner_receivables': 'All receivables owing from owners',
    'other_current_assets': 'All other current assets, such as packing supplies and investments not included in cash above',

    # Fixed Assets
    'gross_fixed_assets': 'All equipment, land, buildings, leasehold improvements, furniture and fixtures',
    'accumulated_depreciation': 'All accumulated depreciation and amortization (enter as negative number)',

    # Other Assets
    'inter_company_receivable': 'All amounts owed by a related company',
    'other_assets': 'All other assets such as hauling authorities, cash value life insurance, investment in other companies, condos, boats, long term owner receivables, etc.',

    # Current Liabilities
    'notes_payable_bank': 'Bank revolving line of credit outstanding',
    'notes_payable_owners': 'Current portion of notes payable to owners',
    'trade_accounts_payable': 'Accounts payable to vendors, suppliers, other agents, etc.',
    'accrued_expenses': 'Salary, vacation pay, interest, etc.',
    'current_portion_ltd': 'Current portion of interest bearing long term debt, excluding related company and owner debt',
    'inter_company_payable': 'All amounts owed to a related company',
    'other_current_liabilities': 'All other current liabilities such as deferred taxes, income tax payable, etc.',

    # Long-term Liabilities
    'eid_loan': 'Amounts due on EIDL and/or PPP Loans (not forgiven)',
    'long_term_debt': 'All interest bearing non-owner debt and non inter-company debt',
    'notes_payable_owners_lt': 'Amounts due to owners - long term',
    'inter_company_debt': 'All amounts owed to a related company',
    'other_lt_liabilities': 'All other long term liabilities such as life insurance loans, etc.',

    # Equity
    'owners_equity': 'Assets minus liabilities',
}

# Income Statement Descriptions
INCOME_STATEMENT_DESCRIPTIONS = {
    # Revenue
    'intra_state_hhg': 'All transportation and accessorial revenues generated under an intrastate tariff (military, GSA, or civilian), or if no tariff, all revenues generated within your state, but not local',
    'local_hhg': 'All revenues defined by an intrastate tariff as local, or if no tariff, all revenues generated within the commercial zone of your city',
    'inter_state_hhg': 'All transportation and accessorial revenues generated under an interstate tariff (military, GSA, or civilian)',
    'office_industrial': 'All local commercial revenue except HHG and local distribution transportation',
    'warehouse': 'All permanent and SIT revenue, including delivery out of SIT, but excluding distribution revenues',
    'warehouse_handling': 'All warehouse handling revenue',
    'international': 'All international revenue including pickup, packing, crating, delivery and accessorials; except for booking & storage',
    'packing_unpacking': 'All revenue for packing, unpacking and container revenue for domestic HHG shipments',
    'booking_royalties': 'Sales booking revenue for all business lines & Operating Authority royalties',
    'special_products': 'All special product revenue and HVP transportation, non HHG brokerage 3rd party, new lines of business',
    'records_storage': 'All records storage revenue',
    'military_dpm_contracts': 'All revenues from Direct Procurement Method military contracts, except storage revenues included in Warehouse above',
    'distribution': 'All distribution revenue, including commercial warehousing, logistics, kitting, hotel FFE projects, including handling',
    'self_storage': 'Revenue generated from self-storage',
    'hotel_deliveries': 'All revenues generated from hotel deliveries',
    'other_revenue': 'Any misc. operational revenue not listed elsewhere (ex. surveys, estimates, etc.)',

    # Direct Expenses
    'direct_wages': 'All salaries, wages, and bonuses paid to operations personnel; including drivers, helpers, packers, warehousemen; excluding admin, office, dispatch and sales',
    'vehicle_operating_expenses': 'All expenses for revenue equipment: repairs and maintenance, fuel, license, registration, tires/tubes, permits, painting, decaling, washing, etc.',
    'packing_warehouse_supplies': 'All moving and packing supplies, including cartons, newsprint, blankets, labels, liftvans, dollies, tools, and misc.',
    'oo_exp_intra_state': 'All payments to O/O for intrastate moves',
    'oo_inter_state': 'All payments to O/O for interstate moves',
    'oo_oi': 'All payments to O/O for O/I',
    'oo_packing': 'All payments to O/O for packing/unpacking',
    'oo_other': 'All payments to O/O for other work (if you do not track O/O expenses by type, put all O/O expenses here)',
    'claims': 'All operational claims',
    'other_trans_exp': 'Trip expense, deadhead miles, agent fees, PUC, freight, BIPD, O/O physical damage insurance, employee per diems',
    'depreciation': 'All depreciation and amortization of intangible assets, vehicles, revenue equipment, office furniture, fixtures, equipment, computer hardware & software; excluding depreciation on buildings or leasehold improvements',
    'lease_expense_rev_equip': 'All lease expense on any revenue equipment',
    'rent': 'Actual rent/lease expenses if paid to an unrelated third party, or estimated Fair Market Rent on a triple net basis if building is owned by the company or a related party',
    'other_direct_expenses': 'Credit card fees and all other direct expenses not otherwise classified (uniforms, CBS charges, meals, laundry, tolls, delivery service, parking, etc.)',

    # Operating Expenses
    'advertising_marketing': 'All advertising and marketing expense, brochures, yellow pages, promotional items, telemarketing, web page expense, etc.',
    'bad_debts': 'Uncollectible accounts receivable written off and offsetting entries for Allowance for Doubtful Accounts',
    'sales_commissions': 'All salaries, wages, and bonuses paid to sales people, including commissions & draws (not including sales support people)',
    'contributions': 'All charitable donations',
    'computer_support': 'All IT expenses, including computer & networking support, consultants, software licensing/maintenance, service agreements, training, satellite tracking',
    'dues_sub': 'All club dues, organization dues and publication subscriptions',
    'pr_taxes_benefits': 'All payroll taxes; life and health insurance; drug testing; MVR reports; background checks; DOT physicals; employee recognition & awards; training; recruiting; convention expenses',
    'equipment_leases_office_equip': 'All non-revenue equipment leases such as copy machines, computers, etc.',
    'workmans_comp_insurance': "Insurance premiums for workmen's comp",
    'insurance': 'All cargo, fleet, general liability and insurance not otherwise classified',
    'legal_accounting': 'Expenses for legal and accounting work, preparation of tax returns, financial statements, etc.',
    'office_expense': 'Office & printer supplies; printed forms; coffee, sundries; janitorial; alarm, security & camera systems; postage; FedEx; etc.',
    'other_admin': 'All expenses not otherwise classified such as bank charges, payroll processing, credit checks, PowerTrack fees, other fees',
    'pension_profit_sharing_401k': 'Company contributions & administrative costs of pension, profit sharing and 401k plans',
    'prof_fees': 'All fees paid to consultants, detectives, non-trade professionals; does not include legal, accounting, or computer professionals',
    'repairs_maint': 'All repairs & maintenance for warehouses, offices & office equipment, other vehicles & equipment not included in Vehicle Operating Expense',
    'salaries_admin': 'All salaries, wages, and bonuses paid to non-operations personnel; including admin, office, dispatch, sales support; excluding CEO compensation and sales compensation',
    'taxes_licenses': 'All taxes and licenses NOT related to vehicles, income tax, or real estate taxes (examples: personal property, intangible, city/county/state business licenses, franchise)',
    'tel_fax_utilities_internet': 'All expenses for telephone, cellular phones, internet connectivity, radios, heat, water, lights, gas, garbage, etc.',
    'travel_ent': 'All admin or sales related transportation, meals, lodging, vehicle rental; excludes seminar & convention fees',
    'vehicle_expense_admin': 'All expenses for sales & admin vehicles: repairs and maintenance, fuel, license, registration, tires/tubes, etc.',

    # Operating Expenses - Rent & Depreciation (optional placement)
    'rent_opex': 'If you consider rent an operational expense - Actual rent/lease expenses if paid to an unrelated third party, or estimated Fair Market Rent on a triple net basis if building is owned by the company or a related party',
    'depreciation_opex': 'If you consider depreciation an operational expense - All depreciation and amortization of intangible assets, vehicles, revenue equipment, office furniture, fixtures, equipment, computer hardware & software; excluding depreciation on buildings or leasehold improvements',

    # Other Income/Expenses
    'other_income': 'All non-operational income such as interest income, gain on sale of asset, litigation income (forgiven PPP money, employee retention tax credits)',
    'ceo_comp': 'All salaries, bonuses or perks paid to CEO (not all owners). Enter as a negative number',
    'other_expense': 'All non-operational expenses such as loss on sale of asset, research of new lines of business, including depreciation on building over Fair Market Rent. Enter as a negative number',
    'interest_expense': 'All interest paid on interest bearing debt owed. Enter as a negative number',

    # Labor Analysis
    'administrative_employees': 'Admin employee headcount (FTE). Include: CEO, dispatch, office workers, managers, salaried sales. Exclude: commissioned employees, hourly warehouse employees. Use decimals for part-time',
    'number_of_branches': 'Count of locations/branches with admin staff. Include: multiple office branches in different or same cities. Exclude: warehouses without admin staff',
}
