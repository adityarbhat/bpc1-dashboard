#!/usr/bin/env python3
"""
Company Wins & Challenges Analysis Page
Atlas BPC 1 Financial Dashboard - Wins & Challenges focused analysis
"""

import html
import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv

# Import from shared modules
from shared.airtable_connection import get_airtable_connection
from shared.page_components import get_period_display_text
from shared.auth_utils import require_auth, logout_user, get_current_user_name, get_current_user_email, is_super_admin
from shared.year_config import get_selected_years, CURRENT_YEAR

# Import ranking calculation function from group ratios
from pages.group_pages.group_ratios import calculate_group_rankings

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


# Wins and Challenges Dictionary - Updated annually by moderator
# Format: "Company Name": {"wins": [...], "challenges": [...]}
WINS_CHALLENGES_DATA = {
    "A-1": {
        "wins": [
            "Strong liquidity position with Current Ratio above 2.0, indicating excellent ability to meet short-term obligations",
            "Gross Profit Margin consistently above industry average, demonstrating effective cost management and pricing strategy",
            "Working Capital as % of Total Assets shows healthy operational efficiency and financial flexibility"
        ],
        "challenges": [
            "Operating Profit Margin below industry benchmark, suggesting need to optimize operating expenses",
            "Debt-to-Equity ratio trending upward, indicating increasing leverage that requires monitoring",
            "Revenue growth has plateaued compared to prior year, requiring strategic initiatives to drive top-line expansion"
        ]
    },
    "Ace": {
        "wins": [
            "Exceptional Revenue Per Admin Employee ratio, demonstrating superior productivity and operational efficiency",
            "EBITDA margin shows strong operational performance independent of financing and tax structures",
            "Consistent improvement in Survival Score over past 3 years, indicating strengthening financial health"
        ],
        "challenges": [
            "Current Ratio below optimal range, suggesting potential liquidity constraints that need addressing",
            "Days Sales Outstanding (DSO) increasing, indicating slower collection cycles and potential cash flow pressure",
            "Net Profit Margin remains below industry peers, requiring focus on bottom-line profitability improvement"
        ]
    },
    "Bisson": {
        "wins": [
            "Debt-to-Equity ratio well within safe range, demonstrating conservative capital structure and low financial risk",
            "Strong Sales-to-Assets ratio indicating efficient asset utilization and productivity",
            "Operating Cash Flow positive and improving, showing strong cash generation from core operations"
        ],
        "challenges": [
            "Gross Profit Margin declining year-over-year, requiring analysis of cost structure and pricing strategy",
            "Working Capital percentage below industry standard, potentially limiting operational flexibility",
            "Operating Profit Margin volatility suggests inconsistent cost control and operational efficiency"
        ]
    },
    "Coastal": {
        "wins": [
            "Ranked #1 in overall group rankings, demonstrating superior performance across multiple financial metrics",
            "Exceptional Survival Score above 3.5, indicating excellent overall financial health and resilience",
            "Industry-leading Current Ratio provides strong buffer for economic downturns and opportunities for growth investment"
        ],
        "challenges": [
            "Revenue growth rate modest compared to expansion opportunities in current market",
            "Administrative expense ratio slightly elevated, suggesting potential for operational efficiency gains",
            "Capital expenditure needs increasing as fixed assets age, requiring planned investment strategy"
        ]
    },
    "Hopkins": {
        "wins": [
            "Significant improvement in Working Capital management, with percentage of assets increasing year-over-year",
            "Gross Profit Margin expansion demonstrates successful pricing strategies and cost optimization",
            "Strong EBITDA generation provides flexibility for debt service and strategic investments"
        ],
        "challenges": [
            "Debt-to-Equity ratio above comfort zone, requiring focus on deleveraging or equity strengthening",
            "Operating Profit Margin compressed due to rising operating expenses outpacing revenue growth",
            "Days Sales Outstanding elevated, indicating collection challenges and potential receivables quality issues"
        ]
    },
    "Kaster": {
        "wins": [
            "Revenue Per Admin Employee among highest in peer group, reflecting strong productivity and lean operations",
            "Sales-to-Assets ratio indicates efficient capital deployment and strong return on assets",
            "Positive trajectory in key profitability metrics showing improving operational performance"
        ],
        "challenges": [
            "Lowest overall group ranking (#10), indicating significant performance gaps across multiple dimensions",
            "Current Ratio below safe threshold, creating liquidity concerns and limiting financial flexibility",
            "Survival Score in caution range, requiring immediate attention to fundamental financial health metrics"
        ]
    },
    "Mabeys": {
        "wins": [
            "Balanced capital structure with appropriate mix of debt and equity financing",
            "Operating Cash Flow generation strong relative to revenue, supporting ongoing operations and growth",
            "Working Capital percentage improving, providing increased operational cushion"
        ],
        "challenges": [
            "Gross Profit Margin trending downward, requiring review of pricing strategy and cost structure",
            "Operating Profit Margin under pressure from rising SG&A expenses",
            "Revenue growth lagging industry peers, necessitating market share analysis and growth strategy development"
        ]
    },
    "RC Mason": {
        "wins": [
            "Strong EBITDA margins demonstrate effective operational management and core business profitability",
            "Debt levels well-managed with Debt-to-Equity ratio in healthy range",
            "Consistent Revenue Per Employee metrics showing stable productivity"
        ],
        "challenges": [
            "Current Ratio declining over past 2 years, indicating tightening liquidity position",
            "Working Capital as % of Assets below peer average, limiting operational flexibility",
            "Days Sales Outstanding increasing, suggesting need for enhanced credit and collection practices"
        ]
    },
    "Spirit": {
        "wins": [
            "Top-tier ranking (#3 overall), reflecting strong performance across balanced scorecard of metrics",
            "Excellent Debt-to-Equity ratio demonstrating financial strength and low leverage risk",
            "Operating Cash Flow generation robust, providing strong foundation for growth and investment"
        ],
        "challenges": [
            "Operating Profit Margin compressed compared to historical levels, requiring cost structure review",
            "Revenue growth rate below market potential, suggesting opportunity for market share expansion",
            "Capital intensity increasing, requiring strategic evaluation of asset efficiency and ROI"
        ]
    },
    "Winter": {
        "wins": [
            "Second-best overall group ranking (#2), demonstrating comprehensive financial strength",
            "Superior Survival Score indicates exceptional resilience and multi-faceted financial health",
            "Gross Profit Margin among highest in peer group, showing strong value capture and cost management"
        ],
        "challenges": [
            "Operating expenses growing faster than revenue, creating margin pressure that needs addressing",
            "Days Sales Outstanding elevated, suggesting opportunities to improve working capital through better A/R management",
            "Fixed asset base aging, requiring capital planning for equipment refreshment and technology upgrades"
        ]
    }
}


def get_company_rank(company_name, period):
    """Get the overall group rank for a company in the selected period"""
    try:
        rankings_data = calculate_group_rankings(period)
        if rankings_data and 'rankings' in rankings_data:
            return rankings_data['rankings'].get(company_name, None)
        return None
    except Exception as e:
        st.warning(f"Could not calculate rankings: {str(e)}")
        return None


def calculate_yoy_percentages(company_name, current_year=None):
    """
    Calculate year-over-year percentage changes for key income statement metrics
    Compares current year Annual vs previous year Annual

    Args:
        company_name: Company to analyze
        current_year: Current year to compare (default '2024')

    Returns dictionary with margin percentages for:
    - Total Cost of Revenue
    - Operating Expenses
    - Gross Profit
    - Operating Profit
    - Net Profit
    """
    if current_year is None:
        current_year = str(CURRENT_YEAR)
    airtable = get_airtable_connection()

    # Calculate previous year
    previous_year = str(int(current_year) - 1)

    # Fetch current and previous year data
    data_current = airtable.get_income_statement_data_by_period(company_name, f"{current_year} Annual", is_admin=is_super_admin())
    data_previous = airtable.get_income_statement_data_by_period(company_name, f"{previous_year} Annual", is_admin=is_super_admin())

    if not data_current or not data_previous:
        return None

    # Get first record from each year
    record_current = data_current[0] if len(data_current) > 0 else {}
    record_previous = data_previous[0] if len(data_previous) > 0 else {}

    # Get revenue for margin calculations
    rev_current = record_current.get('total_revenue', 0) or 0
    rev_previous = record_previous.get('total_revenue', 0) or 0

    if rev_current == 0 or rev_previous == 0:
        return None

    # Calculate margin percentages for both years
    results = {}

    # Direct Expenses - calculate from individual fields (all fields that make up Total Cost of Revenue)
    direct_expense_fields = [
        'direct_wages', 'vehicle_operating_expenses', 'packing_warehouse_supplies',
        'oo_exp_intra_state', 'oo_inter_state', 'oo_oi', 'oo_packing', 'oo_other',
        'claims', 'other_trans_exp', 'depreciation', 'lease_expense_rev_equip',
        'rent', 'other_direct_expenses'
    ]
    dir_exp_current = sum(record_current.get(field, 0) or 0 for field in direct_expense_fields)
    dir_exp_previous = sum(record_previous.get(field, 0) or 0 for field in direct_expense_fields)

    # Total Cost of Revenue - sum of all direct expense fields (per Excel definition)
    results['Total Cost of Revenue'] = (dir_exp_current / rev_current) * 100

    # Operating Expenses - use total_operating_expenses field
    op_exp_current = record_current.get('total_operating_expenses', 0) or 0
    op_exp_previous = record_previous.get('total_operating_expenses', 0) or 0
    results['Operating Expenses'] = (op_exp_current / rev_current) * 100

    # Gross Profit Margin %
    gp_current = record_current.get('gross_profit', 0) or 0
    results['Gross Profit'] = (gp_current / rev_current) * 100

    # Operating Profit Margin %
    op_profit_current = record_current.get('operating_profit', 0) or 0
    results['Operating Profit'] = (op_profit_current / rev_current) * 100

    # Net Profit Margin %
    net_profit_current = record_current.get('profit_before_tax_with_ppp', 0) or 0
    results['Net Profit'] = (net_profit_current / rev_current) * 100

    return results


def calculate_multi_year_yoy(company_name):
    """
    Calculate margin percentages for years 2020-2024
    Each metric is shown as a percentage of revenue (margin %)

    Returns dictionary with structure:
    {
        '2020': {'Gross Profit': 25.3, 'Operating Profit': 6.4, ...},
        '2021': {'Gross Profit': 28.1, 'Operating Profit': 10.4, ...},
        ...
    }
    """
    airtable = get_airtable_connection()

    years = get_selected_years()
    annual_data = {}

    # Fetch data for all years
    for year in years:
        period = f"{year} Annual"
        data = airtable.get_income_statement_data_by_period(company_name, period, is_admin=is_super_admin())
        if data and len(data) > 0:
            annual_data[year] = data[0]

    # Calculate margin percentages for all years
    results = {}

    for year in years:
        if year not in annual_data:
            continue

        record = annual_data[year]
        year_margins = {}

        # Get total revenue for margin calculations
        total_revenue = record.get('total_revenue', 0) or 0

        if total_revenue == 0:
            # Skip this year if no revenue
            continue

        # Direct Expenses - as % of Revenue (all fields that make up Total Cost of Revenue)
        direct_expense_fields = [
            'direct_wages', 'vehicle_operating_expenses', 'packing_warehouse_supplies',
            'oo_exp_intra_state', 'oo_inter_state', 'oo_oi', 'oo_packing', 'oo_other',
            'claims', 'other_trans_exp', 'depreciation', 'lease_expense_rev_equip',
            'rent', 'other_direct_expenses'
        ]
        dir_exp = sum(record.get(field, 0) or 0 for field in direct_expense_fields)

        # Total Cost of Revenue - sum of all direct expense fields (per Excel definition)
        year_margins['Total Cost of Revenue'] = (dir_exp / total_revenue) * 100

        # Operating Expenses - as % of Revenue
        op_exp = record.get('total_operating_expenses', 0) or 0
        year_margins['Operating Expenses'] = (op_exp / total_revenue) * 100

        # Gross Profit Margin %
        gp = record.get('gross_profit', 0) or 0
        year_margins['Gross Profit'] = (gp / total_revenue) * 100

        # Operating Profit Margin %
        op_profit = record.get('operating_profit', 0) or 0
        year_margins['Operating Profit'] = (op_profit / total_revenue) * 100

        # Net Profit Margin %
        net_profit = record.get('profit_before_tax_with_ppp', 0) or 0
        year_margins['Net Profit'] = (net_profit / total_revenue) * 100

        results[year] = year_margins

    return results if results else None


def create_yoy_chart(yoy_data, current_year=None, previous_year=None):
    """Create horizontal bar chart for margin analysis showing each metric as % of revenue"""
    if current_year is None:
        current_year = str(CURRENT_YEAR)
    if previous_year is None:
        previous_year = str(CURRENT_YEAR - 1)
    if not yoy_data:
        return None

    # Define Atlas blue color variants
    color_map = {
        'Total Cost of Revenue': '#025a9a',  # Atlas dark blue
        'Operating Expenses': '#0e9cd5',     # Atlas light blue
        'Gross Profit': '#4db8e8',           # Atlas lighter blue
        'Operating Profit': '#1e7ba0',       # Atlas medium blue
        'Net Profit': '#0a4d73'              # Atlas darker blue
    }

    # Prepare data for plotting - ensure specific order
    categories = ['Total Cost of Revenue', 'Operating Expenses', 'Gross Profit', 'Operating Profit', 'Net Profit']
    values = [yoy_data.get(cat, 0.0) for cat in categories]
    colors = [color_map[cat] for cat in categories]

    # Create horizontal bar chart
    fig = go.Figure()

    # Create text labels - all inside bars for consistent formatting
    text_labels = [f"<b>{val:.1f}%</b>" for val in values]

    # Create custom hover data showing all metrics
    hover_data = []
    for i in range(len(categories)):
        hover_text = (
            '<span style="font-size: 16px;">'
            f'<b>{current_year} Margin % - All Metrics</b><br><br>'
            f'<b>Total Cost of Revenue:</b> {values[0]:.1f}%<br>'
            f'<b>Operating Expenses:</b> {values[1]:.1f}%<br>'
            f'<b>Gross Profit:</b> {values[2]:.1f}%<br>'
            f'<b>Operating Profit:</b> {values[3]:.1f}%<br>'
            f'<b>Net Profit:</b> {values[4]:.1f}%'
            '</span>'
        )
        hover_data.append(hover_text)

    fig.add_trace(go.Bar(
        y=categories,
        x=values,
        orientation='h',
        marker=dict(color=colors),
        text=text_labels,
        textposition='inside',  # All labels inside for consistency
        textfont=dict(size=16, family='Montserrat', color='white'),
        customdata=hover_data,
        hovertemplate='%{customdata}<extra></extra>',
        constraintext='none'
    ))

    # Update layout
    fig.update_layout(
        title={
            'text': f'<b>Margin Analysis - {current_year}</b>',
            'font': {'size': 20, 'family': 'Montserrat', 'color': '#1a202c'},
            'x': 0,
            'xanchor': 'left'
        },
        xaxis=dict(
            title='',
            showgrid=True,
            gridcolor='#e2e8f0',
            zeroline=True,
            zerolinecolor='#025a9a',
            zerolinewidth=2,
            ticksuffix='%',
            tickfont=dict(size=14, family='Montserrat')
        ),
        yaxis=dict(
            title='',
            tickfont=dict(size=14, family='Montserrat'),
            autorange='reversed'  # To match screenshot order
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=500,  # 5 bars
        margin=dict(l=180, r=80, t=80, b=120),  # Bottom margin for legend
        showlegend=False,
        bargap=0.3
    )

    # Add legend below chart with larger font - split into two rows
    legend_row1 = ' · '.join([
        f'<span style="color: {color_map[cat]};">●</span> {cat}'
        for cat in categories[:3]
    ])
    legend_row2 = ' · '.join([
        f'<span style="color: {color_map[cat]};">●</span> {cat}'
        for cat in categories[3:]
    ])
    legend_html = f'{legend_row1}<br>{legend_row2}'

    fig.add_annotation(
        text=legend_html,
        xref='paper',
        yref='paper',
        x=0.5,
        y=-0.10,  # Adjusted position for 5 bars
        showarrow=False,
        font=dict(size=14, family='Montserrat'),
        xanchor='center',
        yanchor='top',
        align='center'
    )

    return fig


def create_multi_year_table(multi_year_data):
    """Create plain white table for multi-year margin analysis (2020-2024)"""
    if not multi_year_data:
        return None

    # Prepare data - grouped logically: Total Costs → Operating Expenses → Profits
    metrics = ['Total Cost of Revenue', 'Operating Expenses', 'Gross Profit', 'Operating Profit', 'Net Profit']
    years = sorted(multi_year_data.keys())  # ['2020', '2021', '2022', '2023', '2024']

    # Helper function to format percentage
    def format_percentage(value):
        if value is None:
            return '-'
        else:
            return f'{value:.1f}%'

    # Create the table HTML
    table_html = '''
    <div class="yoy-trends-table-container">
        <table class="yoy-trends-table">
            <thead>
                <tr>
                    <th class="metric-header">Metric</th>
    '''

    # IMAI competition standards for each metric (from Ratios sheet)
    standards = {
        'Gross Profit':      '25–45%',
        'Operating Profit':  '8%',
        'Net Profit':        '6%',
        'Total Cost of Revenue': '—',
        'Operating Expenses':    '—',
    }

    # Add year headers
    for year in years:
        table_html += f'<th>{year}</th>'

    # Standard column header — dark blue background, golden font (matches Group Avg in company_ratios.py)
    table_html += '<th style="background-color: #025a9a; color: #ffe082; border: 1px solid #ddd; padding: 12px 16px; text-align: center; font-weight: 600; font-size: 14px;">Standard</th>'

    table_html += '''
                </tr>
            </thead>
            <tbody>
    '''

    # Add rows for each metric
    for metric in metrics:
        table_html += f'<tr><td class="metric-name">{metric}</td>'

        # Add cells for each year
        for year in years:
            value = multi_year_data[year].get(metric, None)
            formatted_value = format_percentage(value)

            table_html += f'<td style="background-color: white; text-align: center; font-weight: 600;">{formatted_value}</td>'

        # Standard cell — light blue tint to visually separate from year columns
        standard_value = standards.get(metric, '—')
        table_html += f'<td style="background-color: #e3f2fd; text-align: center; font-weight: 600; border: 1px solid #ddd;">{standard_value}</td>'

        table_html += '</tr>'

    table_html += '''
            </tbody>
        </table>
    </div>

    <style>
    .yoy-trends-table-container {
        margin: 2rem 0;
        overflow-x: auto;
    }

    .yoy-trends-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', sans-serif;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .yoy-trends-table thead {
        background-color: #025a9a;
        color: white;
    }

    .yoy-trends-table th {
        padding: 12px 16px;
        text-align: center;
        font-weight: 600;
        font-size: 14px;
        border: 1px solid #ddd;
    }

    .yoy-trends-table th.metric-header {
        text-align: left;
    }

    .yoy-trends-table td {
        padding: 12px 16px;
        border: 1px solid #ddd;
        font-size: 14px;
    }

    .yoy-trends-table td.metric-name {
        font-weight: 600;
        background-color: #f8f9fa;
        text-align: left;
    }

    .yoy-trends-table tbody tr:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    </style>
    '''

    return table_html


def create_company_sidebar():
    """Create company-specific sidebar navigation"""
    with st.sidebar:        
        # Get current page for active state detection
        current_page = st.session_state.get('current_page', 'company_wins_challenges')

        # CSS for consistent button styling with active state highlighting
        st.markdown("""
        <style>
            /* Remove default borders from all sidebar buttons first */
            section[data-testid="stSidebar"] .stButton > button {
                border: 1px solid #e2e8f0 !important;
            }

            /* Active button styling */
            section[data-testid="stSidebar"] .stButton > button.active-nav-button {
                border: 3px solid #1a202c !important;
                background-color: #edf2f7 !important;
                font-weight: 700 !important;
                box-shadow: inset 0 0 0 1px #1a202c, 0 2px 4px rgba(26, 32, 44, 0.2) !important;
            }
        </style>
        <script>
            // Add active-nav-button class to buttons with ▶ symbol
            function highlightActiveButtons() {
                const buttons = document.querySelectorAll('section[data-testid="stSidebar"] .stButton > button');
                buttons.forEach(button => {
                    if (button.textContent.includes('▶')) {
                        button.classList.add('active-nav-button');
                    } else {
                        button.classList.remove('active-nav-button');
                    }
                });
            }

            // Run on load and periodically to catch Streamlit rerenders
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', highlightActiveButtons);
            } else {
                highlightActiveButtons();
            }

            // Use MutationObserver to detect sidebar changes
            const observer = new MutationObserver(highlightActiveButtons);
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            if (sidebar) {
                observer.observe(sidebar, { childList: true, subtree: true });
            }

            // Also run after a short delay to catch late renders
            setTimeout(highlightActiveButtons, 100);
            setTimeout(highlightActiveButtons, 500);
        </script>
        """, unsafe_allow_html=True)

        # Helper function to create buttons with visual active indicator
        def button_wrapper(label, key, page_id, **kwargs):
            is_active = current_page == page_id
            # Add visual marker to active button label
            if is_active:
                display_label = f"▶ {label}"
            else:
                display_label = f"   {label}"  # Add spacing to align with active marker

            return st.button(display_label, key=key, **kwargs)


        # Overview button at the top
        # Overview button at the top
        if button_wrapper("🏠 Overview", key="wins_nav_overview", page_id="overview", use_container_width=True):
            st.session_state.current_page = "overview"
            st.session_state.nav_tab = "group"
            st.rerun()
        
        # Analysis Type filter
        if 'nav_tab' not in st.session_state:
            st.session_state.nav_tab = 'company'
            
        analysis_options = ["Group", "Company"]
        current_selection = "Group" if st.session_state.nav_tab == 'group' else "Company"
        
        selected_analysis = st.selectbox(
            "**Analysis Type**",
            options=analysis_options,
            index=analysis_options.index(current_selection),
            key="wins_analysis_type_selector"
        )
        
        # Handle analysis type changes
        if selected_analysis == "Group" and st.session_state.nav_tab != 'group':
            st.session_state.nav_tab = 'group'
            st.session_state.current_page = 'overview'
            st.rerun()
        elif selected_analysis == "Company" and st.session_state.nav_tab != 'company':
            st.session_state.nav_tab = 'company'
            st.session_state.current_page = 'company_ratios'
            st.rerun()
        
        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
        
        # Get companies for dropdown using shared connection
        airtable = get_airtable_connection()
        companies = airtable.get_companies()
        
        if companies:
            company_options = {comp['name']: comp['name'] for comp in sorted(companies, key=lambda x: x['name'])}
            
            # Get current selection or default to first company
            current_company = st.session_state.get('selected_company_name', list(company_options.keys())[0])
            if current_company not in company_options:
                current_company = list(company_options.keys())[0]
            
            # Company selector with unique key and preserved state
            selected_company_name = st.selectbox(
                "**Select Company Below**",
                options=list(company_options.keys()),
                key="company_wins_challenges_selector",
                index=list(company_options.keys()).index(current_company)
            )
            st.session_state.selected_company_name = selected_company_name
        else:
            st.error("No companies found")
            return

        from shared.year_config import render_year_selector
        render_year_selector()

        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Navigation buttons (matches other company pages)
        if button_wrapper("% Ratios", key="wins_nav_ratios", page_id="company_ratios", use_container_width=True):
            st.session_state.current_page = "company_ratios"
            st.rerun()
        
        if button_wrapper("📊 Balance Sheet", key="wins_nav_balance", page_id="company_balance_sheet", use_container_width=True):
            st.session_state.current_page = "company_balance_sheet"
            st.rerun()
        if button_wrapper("📈 Income Statement", key="wins_nav_income", page_id="company_income_statement", use_container_width=True):
            st.session_state.current_page = "company_income_statement"
            st.rerun()
        if button_wrapper("💸 Cash Flow", key="wins_nav_cash_flow", page_id="company_cash_flow", use_container_width=True):
            st.session_state.current_page = "company_cash_flow"
            st.rerun()
        if button_wrapper("👥 Labor Cost", key="wins_nav_labor", page_id="company_labor_cost", use_container_width=True):
            st.session_state.current_page = "company_labor_cost"
            st.rerun()
        if button_wrapper("💎 Value", key="wins_nav_value", page_id="company_value", use_container_width=True):
            st.session_state.current_page = "company_value"
            st.rerun()
        if button_wrapper("📋 Actuals", key="wins_nav_actuals", page_id="company_actuals", use_container_width=True):
            st.session_state.current_page = "company_actuals"
            st.rerun()
        if button_wrapper("🏆 Wins & Challenges", key="wins_nav_wins", page_id="company_wins_challenges", use_container_width=True):
            st.session_state.current_page = "company_wins_challenges"
            st.rerun()

        # ====================================================================
        # USER INFO & LOGOUT SECTION
        # ====================================================================
        st.markdown('<div style="border-bottom: 1px solid #e2e8f0; margin: 1rem 0;"></div>', unsafe_allow_html=True)

        # User info display
        # Get user display info with validation
        user_name = get_current_user_name()
        user_email = get_current_user_email()

        # Validate consistency: if we have profile but no user, or vice versa, clear session
        if (user_name and not user_email) or (user_email and not user_name):
            from shared.auth_utils import clear_session, clear_cookies
            clear_session()
            clear_cookies()
            st.rerun()

        # If we have both, verify user_id matches between session.user and session.user_profile
        if user_name and user_email and st.session_state.user and st.session_state.user_profile:
            session_user_id = st.session_state.user.id
            profile_user_id = st.session_state.user_profile.get('id')

            if session_user_id != profile_user_id:
                from shared.auth_utils import clear_session, clear_cookies
                clear_session()
                clear_cookies()
                st.rerun()

        if user_name:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                    padding: 0.75rem;
                    border-radius: 8px;
                    margin-bottom: 0.5rem;
                    border-left: 3px solid #025a9a;
                ">
                    <div style="font-size: 0.7rem; color: #718096; margin-bottom: 0.2rem;">
                        Logged in as
                    </div>
                    <div style="font-weight: 600; color: #2d3748; font-size: 0.85rem; margin-bottom: 0.1rem;">
                        {user_name}
                    </div>
                    <div style="font-size: 0.7rem; color: #a0aec0;">
                        {user_email}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Admin badge if user is super admin
            if is_super_admin():
                st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #9f7aea 0%, #805ad5 100%);
                        color: white;
                        padding: 0.3rem 0.6rem;
                        border-radius: 6px;
                        text-align: center;
                        font-size: 0.75rem;
                        font-weight: 600;
                        margin-bottom: 0.5rem;
                    ">
                        🔑 Super Admin
                    </div>
                """, unsafe_allow_html=True)

        # Logout button
        st.markdown("""
            <style>
                /* Logout button styling */
                div[data-testid="column"] button[key="logout_button"] {
                    background: linear-gradient(135deg, #fc8181 0%, #f56565 100%) !important;
                    color: white !important;
                    border: none !important;
                    font-weight: 600 !important;
                    border-radius: 8px !important;
                    padding: 0.5rem !important;
                    box-shadow: 0 2px 4px rgba(245, 101, 101, 0.3) !important;
                }

                div[data-testid="column"] button[key="logout_button"]:hover {
                    background: linear-gradient(135deg, #f56565 0%, #fc8181 100%) !important;
                    transform: translateY(-1px) !important;
                }
            </style>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", key="logout_button", use_container_width=True):
            logout_user()  # This will clear session and reload the page


def create_company_wins_challenges_page():
    # Require authentication
    require_auth()

    # CSS is already applied by main function - no need to duplicate
    
    # Initialize session state
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'wins_challenges_overview'
    if 'selected_company_name' not in st.session_state:
        st.session_state.selected_company_name = None
    
    # Create company wins & challenges specific sidebar with proper error handling (BEFORE page routing)
    try:
        # Clear the entire sidebar first
        st.sidebar.empty()
        
        # Create company wins & challenges specific sidebar
        create_company_sidebar()
    except Exception as e:
        st.sidebar.error(f"Error creating sidebar: {str(e)}")
    
    # Handle page routing to other company pages
    if st.session_state.get('current_page') == 'company_ratios':
        from company_ratios import create_company_ratios_page
        create_company_ratios_page()
        return
    
    if st.session_state.get('current_page') == 'company_balance_sheet':
        from company_balance_sheet import create_company_balance_sheet_page
        create_company_balance_sheet_page()
        return
    
    if st.session_state.get('current_page') == 'company_income_statement':
        from company_income_statement import create_company_income_statement_page
        create_company_income_statement_page()
        return
    
    if st.session_state.get('current_page') == 'company_cash_flow':
        from company_cash_flow import create_company_cash_flow_page
        create_company_cash_flow_page()
        return
    
    if st.session_state.get('current_page') == 'company_labor_cost':
        from company_labor_cost import create_company_labor_cost_page
        create_company_labor_cost_page()
        return
    
    if st.session_state.get('current_page') == 'company_actuals':
        from company_actuals import create_company_actuals_page
        create_company_actuals_page()
        return
    
    if st.session_state.get('current_page') == 'company_value':
        from company_value import create_company_value_page
        create_company_value_page()
        return

    # Import centralized page components
    from shared.page_components import create_page_header

    # Determine page title based on selected company
    if st.session_state.selected_company_name:
        page_title = f"{st.session_state.selected_company_name} Wins & Challenges"
    else:
        page_title = f"Company Wins & Challenges Analysis"

    # Use centralized page header with period selector
    create_page_header(
        page_title=page_title,
        show_period_selector=True
    )

    # Add year selector on the right side
    # Initialize session state for year
    if 'wins_challenges_year' not in st.session_state:
        st.session_state.wins_challenges_year = str(CURRENT_YEAR)

    col1, col2 = st.columns([8.5, 1])

    with col1:
        pass  # Empty space

    year_options = [str(y) for y in range(CURRENT_YEAR - 1, CURRENT_YEAR + 2)]
    with col2:
        selected_year = st.selectbox(
            "**Year**",
            options=year_options,
            index=year_options.index(st.session_state.wins_challenges_year) if st.session_state.wins_challenges_year in year_options else 0,
            key="wins_challenges_year_selector"
        )
        st.session_state.wins_challenges_year = selected_year

    st.markdown('<div style="margin-bottom: 0.5rem;"></div>', unsafe_allow_html=True)

    # Main content
    if st.session_state.selected_company_name:
        
        # Initialize Airtable connection using shared connection
        airtable = get_airtable_connection()
        
        # Get data for selected company
        balance_data = airtable.get_balance_sheet_data(st.session_state.selected_company_name, is_admin=is_super_admin())
        income_data = airtable.get_income_statement_data(st.session_state.selected_company_name, is_admin=is_super_admin())
        
        # Check if we have any data to display
        if not balance_data and not income_data:
            st.info(f"⚠️ No financial data found for {st.session_state.selected_company_name} for the 2024 Annual period.")
            st.info("💡 This might be because the data hasn't been uploaded yet or the company name doesn't match exactly.")
        
        # Display wins & challenges sections
        if balance_data or income_data:
            display_wins_challenges_sections(balance_data, income_data)
        else:
            # Show clear message when no real data is available
            st.info(f"📊 No financial data available for {st.session_state.selected_company_name}.")
            st.info("💡 Data may not have been uploaded yet for this company.")
    
    else:
        st.info("Please select a company from the sidebar to view wins & challenges analysis.")


def display_wins_challenges_sections(balance_data, income_data):
    """Display the wins & challenges analysis sections"""

    # Get company name
    company_name = st.session_state.selected_company_name

    # Get selected year and period from selectors
    selected_year = st.session_state.get('wins_challenges_year', str(CURRENT_YEAR))
    period = st.session_state.get('period', 'year_end')

    # Convert to period_name format for Airtable query
    if period == 'year_end':
        period_name = f"{selected_year} Annual"
        selected_period_type = 'Year End'
    else:  # june_end (Mid Year)
        period_name = f"{selected_year} H1"
        selected_period_type = 'Mid Year'

    # Fetch wins, challenges, and action items from Airtable
    # Super admins see drafts + published (preview before publish); company users see published only
    airtable = get_airtable_connection()
    admin_view = is_super_admin()
    wins_data = airtable.get_wins(company_name, period_name, include_drafts=admin_view)
    challenges_data = airtable.get_challenges(company_name, period_name, include_drafts=admin_view)
    action_items_data = airtable.get_action_items(company_name, period_name, include_drafts=admin_view)

    # Extract text from data (get_wins returns list of dicts with 'win_text' field)
    wins = [item['win_text'] for item in wins_data] if wins_data else []
    challenges = [item['challenge_text'] for item in challenges_data] if challenges_data else []
    action_items = [item['action_item_text'] for item in action_items_data] if action_items_data else []

    # Get company rank for current year Annual (most recent)
    period_for_rank = f"{CURRENT_YEAR} Annual"
    company_rank = get_company_rank(company_name, period_for_rank)

    # Add CSS for the analysis section - compact layout
    st.markdown("""
    <style>
    .wins-challenges-analysis-section {
        margin: 0.75rem 0 0.5rem 0;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 0.5rem;
        font-family: 'Montserrat', sans-serif;
    }
    .rank-display {
        background: linear-gradient(135deg, #025a9a, #0e9cd5);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(2, 90, 154, 0.3);
    }
    .wins-list, .challenges-list {
        background-color: #f7fafc;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        border-left: 3px solid #025a9a;
        margin: 0.5rem 0;
    }
    .challenges-list {
        border-left: 3px solid #c2002f;
    }
    .wins-list h3, .challenges-list h3 {
        color: #1a202c;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
        font-family: 'Montserrat', sans-serif;
    }
    .wins-list ul, .challenges-list ul {
        list-style-type: none;
        padding-left: 0;
        margin: 0;
    }
    .wins-list li, .challenges-list li {
        padding: 0.35rem 0;
        border-bottom: 1px solid #e2e8f0;
        font-size: 1rem;
        line-height: 1.6;
    }
    .wins-list li:last-child, .challenges-list li:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }
    .wins-list li:before {
        content: "✓ ";
        color: #10b981;
        font-weight: bold;
        margin-right: 0.3rem;
    }
    .challenges-list li:before {
        content: "⚠ ";
        color: #ef4444;
        font-weight: bold;
        margin-right: 0.3rem;
    }
    .action-items-list {
        background-color: #f7fafc;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        border-left: 3px solid #0e9cd5;
        margin: 0.75rem 0 0.5rem 0;
        width: 100%;
    }
    .action-items-list h3 {
        color: #1a202c;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
        font-family: 'Montserrat', sans-serif;
    }
    .action-items-list ul {
        list-style-type: none;
        padding-left: 0;
        margin: 0;
    }
    .action-items-list li {
        padding: 0.35rem 0;
        border-bottom: 1px solid #e2e8f0;
        font-size: 1rem;
        line-height: 1.6;
    }
    .action-items-list li:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }
    .action-items-list li:before {
        content: "→ ";
        color: #0e9cd5;
        font-weight: bold;
        margin-right: 0.3rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Wins & Challenges Analysis Section
    st.markdown(f"""
    <div class="wins-challenges-analysis-section">
        <h2 class="section-title">Wins & Challenges for this period</h2>
    </div>
    """, unsafe_allow_html=True)

    # Display rank if available
    if company_rank:
        st.markdown(f"""
        <div class="rank-display">
            Current Group Rank: #{company_rank}
        </div>
        """, unsafe_allow_html=True)

    # Display wins and challenges in two columns
    col1, col2 = st.columns(2)

    def _render_wc_text(text):
        """Render W&C text with proper formatting for existing stored data."""
        t = html.escape(text)
        # Single *emphasis* → italic (before line processing)
        t = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', t)
        # Inline sub-bullets without a newline: " -Capital" → real newline before dash
        t = re.sub(r' -([A-Z])', r'\n-\1', t)

        # Process line by line to control spacing intelligently
        lines = t.split('\n')
        parts = []
        for i, line in enumerate(lines):
            if i == 0:
                parts.append(line)
                continue
            prev = lines[i - 1].strip()
            curr = line.strip()
            if not curr:
                # Empty line → paragraph break with explicit margin so it renders
                # visually distinct inside <li>, not just two squished line-feeds
                parts.append('<span style="display:block;margin-top:0.75em"></span>')
            elif curr.startswith('-') and prev and not prev.startswith('-'):
                # Transition from body/header text into sub-bullets → add half-line gap
                parts.append('<br><span style="display:block;height:0.5em"></span>' + line)
            elif prev == '':
                # Line after a paragraph break — separator already emitted
                parts.append(line)
            else:
                parts.append('<br>' + line)
        return ''.join(parts)

    with col1:
        if wins:
            wins_html = '<div class="wins-list"><h3>Wins</h3><ul>'
            for win in wins:
                wins_html += f'<li>{_render_wc_text(win)}</li>'
            wins_html += '</ul></div>'
            st.markdown(wins_html, unsafe_allow_html=True)
        else:
            st.info("No wins defined for this period. Use the admin form to add wins.")

    with col2:
        if challenges:
            challenges_html = '<div class="challenges-list"><h3>Challenges</h3><ul>'
            for challenge in challenges:
                challenges_html += f'<li>{_render_wc_text(challenge)}</li>'
            challenges_html += '</ul></div>'
            st.markdown(challenges_html, unsafe_allow_html=True)
        else:
            st.info("No challenges defined for this period. Use the admin form to add challenges.")

    # Action Items section - spans full width
    if action_items:
        action_items_html = '<div class="action-items-list"><h3>Action Items</h3><ul>'
        for item in action_items:
            action_items_html += f'<li>{_render_wc_text(item)}</li>'
        action_items_html += '</ul></div>'
        st.markdown(action_items_html, unsafe_allow_html=True)
    else:
        st.info("No action items defined for this period. Use the admin form to add action items.")

    # Add spacing before chart
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Calculate and display margin analysis chart
    # Only show margin chart for "Year End" (Annual) periods
    if selected_period_type == 'Year End':
        margin_data = calculate_yoy_percentages(company_name, selected_year)
        previous_year = str(int(selected_year) - 1)

        if margin_data:
            # Create and display chart with dynamic title
            fig = create_yoy_chart(margin_data, selected_year, previous_year)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Margin analysis data not available for {selected_year}.")
    else:
        st.info("📊 Margin analysis chart is only available for Year End (Annual) periods.")

    # Add spacing before multi-year table
    st.markdown('<div style="margin: 1.5rem 0 0.5rem 0;"></div>', unsafe_allow_html=True)

    # Add section title for multi-year trends
    st.markdown("""
    <div style="margin-bottom: 0.5rem;">
        <h2 style="font-size: 1.25rem; font-weight: 600; color: #1a202c; font-family: 'Montserrat', sans-serif; margin-bottom: 0.25rem;">
            Historical Margin Analysis (2020-2024)
        </h2>
        <p style="font-size: 0.85rem; color: #718096; font-family: 'Montserrat', sans-serif; margin-top: 0.25rem;">
            All metrics shown as percentage of revenue (margin %)
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Calculate and display multi-year margin analysis (2020-2024)
    multi_year_data = calculate_multi_year_yoy(company_name)

    if multi_year_data and len(multi_year_data) > 0:
        # Create and display multi-year table
        table_html = create_multi_year_table(multi_year_data)
        if table_html:
            st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("📊 Historical margin data not available for 2020-2024.")


if __name__ == "__main__":
    create_company_wins_challenges_page()