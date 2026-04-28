"""Single source of truth for ratio color thresholds.

All three coloring surfaces (company_ratios, group_ratios, excel_formatter)
import from here. Never define thresholds inline in those files.
"""

THRESHOLDS = {
    'current_ratio':       {'great': 2.0,   'caution': [1.2, 2.0],     'improve': 1.3,   'reverse': False},
    'debt_to_equity':      {'great': 1.4,   'caution': [1.5, 2.9],     'improve': 3.0,   'reverse': True},
    'working_capital_pct': {'great': 0.30,  'caution': [0.15, 0.2999], 'improve': 0.15,  'reverse': False},
    'survival_score':      {'great': 3.0,   'caution': [2.0, 3.0],     'improve': 2.0,   'reverse': False},
    'sales_assets':        {'great': 3.7,   'caution': [2.0, 3.6],     'improve': 2.0,   'reverse': False},
    'gpm':                 {'great': 0.25,  'caution': [0.20, 0.25],   'improve': 0.20,  'reverse': False},
    'opm':                 {'great': 0.055, 'caution': [0.03, 0.0549], 'improve': 0.03,  'reverse': False},
    'npm':                 {'great': 0.0,   'caution': None,            'improve': None,  'reverse': False},
    'rev_per_employee':    {'great': 550,   'caution': [325, 550],     'improve': 325,   'reverse': False},
    'ebitda_margin':       {'great': 0.05,  'caution': [0.025, 0.05],  'improve': 0.025, 'reverse': False},
    'dso':                 {'great': 30,    'caution': [30, 60],       'improve': 60,    'reverse': True},
    'ocf_rev':             {'great': 0.0,   'caution': [-0.03, 0.0],   'improve': -0.03, 'reverse': False},
    'fcf_rev':             {'great': 0.005, 'caution': [-0.005, 0.005],'improve': -0.005,'reverse': False},
    'ncf_rev':             {'great': 0.005, 'caution': [-0.005, 0.005],'improve': -0.005,'reverse': False},
}

# Percentage metrics that may arrive as full-percent (e.g. 8.1 instead of 0.081).
PCT_METRICS = frozenset({
    'working_capital_pct', 'gpm', 'opm', 'npm',
    'ebitda_margin', 'ocf_rev', 'fcf_rev', 'ncf_rev',
})

_DISPLAY_NAME_MAP = {
    'current_ratio':       'Current Ratio',
    'debt_to_equity':      'Debt to Equity',
    'working_capital_pct': 'Working Capital %',
    'survival_score':      'Survival Score',
    'sales_assets':        'Sales/Assets',
    'gpm':                 'Gross Profit Margin',
    'opm':                 'Operating Profit Margin',
    'npm':                 'Net Profit Margin',
    'rev_per_employee':    'Revenue Per Employee',
    'ebitda_margin':       'EBITDA/Revenue',
    'dso':                 'Days Sales Outstanding (DSO)',
    'ocf_rev':             'OCF/Revenue',
    'fcf_rev':             'FCF/Revenue',
    'ncf_rev':             'NCF/Revenue',
}

# Display-name-keyed dict for excel_formatter backward compatibility.
DISPLAY_THRESHOLDS = {_DISPLAY_NAME_MAP[k]: v for k, v in THRESHOLDS.items()}
