import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from shared.airtable_connection import get_airtable_connection, get_companies_cached
from shared.page_components import create_page_header, get_period_display_text
from shared.auth_utils import require_auth

# ============================================================================
# CUSTOM ANALYSIS - METRIC COMPARISON FUNCTIONALITY
# ============================================================================

# Metric definitions for custom analysis comparison tool
METRIC_DEFINITIONS = {
    # Revenue Breakdown (Percentages)
    'HHG Moving %': {
        'fields': ['intra_state_hhg', 'local_hhg', 'inter_state_hhg', 'international', 'packing_unpacking', 'military_dpm_contracts'],
        'type': 'calculated_percentage',
        'category': 'Revenue Breakdown (%)',
        'description': 'HHG Moving revenue as % of total revenue',
        'calculation': 'sum_fields_pct_of_total_revenue'
    },
    'Non-HHG %': {
        'fields': ['office_industrial', 'special_products', 'distribution', 'hotel_deliveries'],
        'type': 'calculated_percentage',
        'category': 'Revenue Breakdown (%)',
        'description': 'Non-HHG revenue as % of total revenue',
        'calculation': 'sum_fields_pct_of_total_revenue'
    },
    'Warehouse %': {
        'fields': ['warehouse', 'warehouse_handling', 'records_storage'],
        'type': 'calculated_percentage',
        'category': 'Revenue Breakdown (%)',
        'description': 'Warehouse revenue as % of total revenue',
        'calculation': 'sum_fields_pct_of_total_revenue'
    },
    'Other %': {
        'fields': ['booking_royalties', 'other_revenue'],
        'type': 'calculated_percentage',
        'category': 'Revenue Breakdown (%)',
        'description': 'Other revenue as % of total revenue',
        'calculation': 'sum_fields_pct_of_total_revenue'
    },

    # Profitability Metrics
    'Gross Profit Margin': {
        'field': 'gpm',
        'type': 'percentage',
        'category': 'Profitability',
        'description': 'Gross profit as % of revenue',
        'format': '{:.1f}%'
    },
    'Operating Profit Margin': {
        'field': 'opm',
        'type': 'percentage',
        'category': 'Profitability',
        'description': 'Operating profit as % of revenue',
        'format': '{:.1f}%'
    },
    'EBITDA / Revenue %': {
        'field': 'ebitda_pct_rev',
        'type': 'percentage',
        'category': 'Profitability',
        'description': 'EBITDA as % of revenue',
        'format': '{:.1f}%'
    },
    'Net Profit Margin': {
        'field': 'net_income_pct',
        'type': 'percentage',
        'category': 'Profitability',
        'description': 'Net income as % of revenue',
        'format': '{:.1f}%'
    },

    # Balance Sheet Ratios
    'Current Ratio': {
        'field': 'current_ratio',
        'type': 'ratio',
        'category': 'Balance Sheet Ratios',
        'description': 'Current assets divided by current liabilities',
        'format': '{:.2f}'
    },
    'Debt to Equity': {
        'field': 'debt_to_equity',
        'type': 'ratio',
        'category': 'Balance Sheet Ratios',
        'description': 'Total liabilities divided by total equity',
        'format': '{:.2f}'
    },
    'Working Capital %': {
        'field': 'working_capital_pct',
        'type': 'percentage',
        'category': 'Balance Sheet Ratios',
        'description': 'Working capital as % of total assets',
        'format': '{:.1f}%'
    },
    'Survival Ratio': {
        'field': 'survival_score',
        'type': 'ratio',
        'category': 'Balance Sheet Ratios',
        'description': 'Months company can survive without revenue',
        'format': '{:.1f}'
    },

    # Efficiency Metrics
    'Revenue per Employee': {
        'field': 'rev_per_employee',
        'type': 'currency',
        'category': 'Efficiency',
        'description': 'Total revenue divided by number of employees',
        'format': '${:,.0f}'
    },
    'Labor Ratio': {
        'field': 'labor_ratio',
        'type': 'percentage',
        'category': 'Efficiency',
        'description': 'Labor costs as % of revenue (excluding warehouse, booking, other)',
        'format': '{:.1f}%'
    },
    'Admin Labor %': {
        'field': 'admin_labor_cost_pct_rev',
        'type': 'percentage',
        'category': 'Efficiency',
        'description': 'Admin labor and expenses as % of revenue',
        'format': '{:.1f}%'
    },
    'Revenue Producing Labor %': {
        'field': 'rev_producing_labor_expenses_pct_rev',
        'type': 'percentage',
        'category': 'Efficiency',
        'description': 'Revenue producing labor as % of revenue',
        'format': '{:.1f}%'
    },
    'Total Labor %': {
        'field': 'tot_labor_expenses_pct_rev',
        'type': 'percentage',
        'category': 'Efficiency',
        'description': 'Total labor and expenses as % of revenue',
        'format': '{:.1f}%'
    },

    # Value Metrics
    'Company Value': {
        'fields': ['ebitda', 'interest_bearing_debt'],
        'type': 'calculated_currency',
        'category': 'Value Metrics',
        'description': '(3 x EBITDA) - Interest Bearing Debt',
        'format': '${:,.0f}',
        'calculation': 'company_value'
    },
    '3x EBITDA': {
        'field': 'ebitda',
        'type': 'currency',
        'category': 'Value Metrics',
        'description': 'EBITDA multiplied by 3',
        'format': '${:,.0f}',
        'multiplier': 3
    },
    'Value to Equity': {
        'fields': ['ebitda', 'interest_bearing_debt', 'equity'],
        'type': 'calculated_ratio',
        'category': 'Value Metrics',
        'description': 'Company Value divided by Equity',
        'format': '{:.2f}',
        'calculation': 'value_to_equity'
    },
    'Interest Bearing Debt': {
        'field': 'interest_bearing_debt',
        'type': 'currency',
        'category': 'Value Metrics',
        'description': 'Total interest bearing debt',
        'format': '${:,.0f}'
    },
    'Total Equity': {
        'field': 'equity',
        'type': 'currency',
        'category': 'Value Metrics',
        'description': 'Total shareholder equity',
        'format': '${:,.0f}'
    },

    # Raw Revenue Metrics
    'Total Revenue': {
        'field': 'total_revenue',
        'type': 'currency',
        'category': 'Revenue ($)',
        'description': 'Total company revenue',
        'format': '${:,.0f}'
    },
    'EBITDA': {
        'field': 'ebitda',
        'type': 'currency',
        'category': 'Revenue ($)',
        'description': 'Earnings Before Interest, Taxes, Depreciation, and Amortization',
        'format': '${:,.0f}'
    },
    'Gross Profit': {
        'field': 'gross_profit',
        'type': 'currency',
        'category': 'Revenue ($)',
        'description': 'Total gross profit',
        'format': '${:,.0f}'
    },
    'Operating Income': {
        'field': 'operating_income',
        'type': 'currency',
        'category': 'Revenue ($)',
        'description': 'Operating income (EBIT)',
        'format': '${:,.0f}'
    },

    # Balance Sheet Dollar Metrics
    'Total Assets': {
        'field': 'total_assets',
        'type': 'currency',
        'category': 'Balance Sheet ($)',
        'description': 'Total company assets',
        'format': '${:,.0f}'
    },
    'Total Liabilities': {
        'field': 'total_liabilities',
        'type': 'currency',
        'category': 'Balance Sheet ($)',
        'description': 'Total company liabilities',
        'format': '${:,.0f}'
    },
    'Working Capital': {
        'field': 'working_capital',
        'type': 'currency',
        'category': 'Balance Sheet ($)',
        'description': 'Current assets minus current liabilities',
        'format': '${:,.0f}'
    },
}


@st.cache_data(ttl=900, show_spinner=False)
def get_available_metrics():
    """Returns categorized dictionary of available metrics for custom analysis"""
    categorized = {}
    for metric_name, metric_info in METRIC_DEFINITIONS.items():
        category = metric_info['category']
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(metric_name)

    # Sort categories in desired order
    category_order = [
        'Revenue Breakdown (%)',
        'Profitability',
        'Balance Sheet Ratios',
        'Efficiency',
        'Value Metrics',
        'Revenue ($)',
        'Balance Sheet ($)'
    ]

    ordered = {}
    for cat in category_order:
        if cat in categorized:
            ordered[cat] = sorted(categorized[cat])

    return ordered


@st.cache_data(ttl=900, show_spinner=False)
def fetch_metric_data(metric_name, company_list, period):
    """Fetch metric values for specified companies and period"""
    if metric_name not in METRIC_DEFINITIONS:
        return {}

    metric_def = METRIC_DEFINITIONS[metric_name]
    airtable = get_airtable_connection()

    # Fetch data for all companies
    all_data = {}

    for company_name in company_list:
        # Fetch income statement data
        income_data = airtable.get_income_statement_data_by_period(company_name, period)

        # Also fetch balance sheet data for ratios
        balance_data = airtable.get_balance_sheet_data_by_period(company_name, period)

        if not income_data or len(income_data) == 0:
            continue

        income_record = income_data[0]
        balance_record = balance_data[0] if balance_data and len(balance_data) > 0 else {}

        # Merge both records
        record = {**income_record, **balance_record}

        # Calculate metric value based on type
        value = None

        if metric_def['type'] == 'calculated_percentage':
            # Sum specified fields and calculate percentage of total revenue
            if metric_def['calculation'] == 'sum_fields_pct_of_total_revenue':
                total_revenue = record.get('total_revenue', 0) or 0
                if total_revenue > 0:
                    sum_value = sum([record.get(field, 0) or 0 for field in metric_def['fields']])
                    value = (sum_value / total_revenue) * 100

        elif metric_def['type'] == 'percentage':
            # Direct percentage field
            value = record.get(metric_def['field'], 0) or 0
            # Convert to percentage if stored as decimal
            if 0 < value < 1:
                value = value * 100

        elif metric_def['type'] == 'ratio':
            # Direct ratio field
            value = record.get(metric_def['field'], 0) or 0

        elif metric_def['type'] == 'currency':
            # Direct currency field
            value = record.get(metric_def['field'], 0) or 0
            # Apply multiplier if specified
            if 'multiplier' in metric_def:
                value = value * metric_def['multiplier']

        elif metric_def['type'] == 'calculated_currency':
            # Special calculations
            if metric_def['calculation'] == 'company_value':
                ebitda = record.get('ebitda', 0) or 0
                debt = record.get('interest_bearing_debt', 0) or 0
                value = (3 * ebitda) - debt

        elif metric_def['type'] == 'calculated_ratio':
            # Special calculations
            if metric_def['calculation'] == 'value_to_equity':
                ebitda = record.get('ebitda', 0) or 0
                debt = record.get('interest_bearing_debt', 0) or 0
                equity = record.get('equity', 0) or 0
                company_value = (3 * ebitda) - debt
                if equity != 0:
                    value = company_value / equity

        if value is not None:
            all_data[company_name] = value

    return all_data


def create_dual_comparison_chart(metric1_name, metric1_data, metric2_name, metric2_data):
    """Create two side-by-side Plotly bar charts for metric comparison"""

    # Get metric definitions for formatting
    metric1_def = METRIC_DEFINITIONS.get(metric1_name, {})
    metric2_def = METRIC_DEFINITIONS.get(metric2_name, {})

    # Create two separate figures
    col1, col2 = st.columns(2)

    with col1:
        if metric1_data:
            # Prepare data
            companies = list(metric1_data.keys())
            values = list(metric1_data.values())

            # Determine formatting
            metric1_type = metric1_def.get('type', 'raw')

            # Create hover text
            hover_texts = []
            for comp, val in zip(companies, values):
                if 'percentage' in metric1_type or '%' in metric1_name:
                    hover_text = f"<b>{comp}</b><br><b>{metric1_name}:</b> {val:.1f}%"
                elif 'currency' in metric1_type or '$' in metric1_def.get('format', ''):
                    hover_text = f"<b>{comp}</b><br><b>{metric1_name}:</b> ${val:,.0f}"
                elif 'ratio' in metric1_type:
                    hover_text = f"<b>{comp}</b><br><b>{metric1_name}:</b> {val:.2f}"
                else:
                    hover_text = f"<b>{comp}</b><br><b>{metric1_name}:</b> {val:,.1f}"
                hover_texts.append(hover_text)

            # Create bar chart
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=companies,
                y=values,
                marker_color='#025a9a',  # Atlas blue
                customdata=hover_texts,
                hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
            ))

            # Determine y-axis format
            if 'percentage' in metric1_type or '%' in metric1_name:
                yaxis_format = '.1f'
                yaxis_suffix = '%'
                yaxis_title = f'{metric1_name}'
            elif 'currency' in metric1_type:
                yaxis_format = ',.0f'
                yaxis_suffix = ''
                yaxis_title = f'{metric1_name} ($)'
            else:
                yaxis_format = '.2f'
                yaxis_suffix = ''
                yaxis_title = metric1_name

            fig1.update_layout(
                title={
                    'text': metric1_name,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16, 'family': 'Montserrat', 'color': '#1a202c'}
                },
                xaxis_title='Company',
                yaxis_title=yaxis_title,
                height=450,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font={'family': 'Montserrat', 'size': 12},
                xaxis=dict(
                    showgrid=False,
                    showline=True,
                    linewidth=1,
                    linecolor='#e2e8f0'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='#f0f0f0',
                    tickformat=yaxis_format,
                    ticksuffix=yaxis_suffix
                ),
                margin=dict(l=60, r=20, t=60, b=80)
            )

            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info(f"📊 No data available for {metric1_name}")

    with col2:
        if metric2_data:
            # Prepare data
            companies = list(metric2_data.keys())
            values = list(metric2_data.values())

            # Determine formatting
            metric2_type = metric2_def.get('type', 'raw')

            # Create hover text
            hover_texts = []
            for comp, val in zip(companies, values):
                if 'percentage' in metric2_type or '%' in metric2_name:
                    hover_text = f"<b>{comp}</b><br><b>{metric2_name}:</b> {val:.1f}%"
                elif 'currency' in metric2_type or '$' in metric2_def.get('format', ''):
                    hover_text = f"<b>{comp}</b><br><b>{metric2_name}:</b> ${val:,.0f}"
                elif 'ratio' in metric2_type:
                    hover_text = f"<b>{comp}</b><br><b>{metric2_name}:</b> {val:.2f}"
                else:
                    hover_text = f"<b>{comp}</b><br><b>{metric2_name}:</b> {val:,.1f}"
                hover_texts.append(hover_text)

            # Create bar chart
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=companies,
                y=values,
                marker_color='#0e9cd5',  # Lighter Atlas blue
                customdata=hover_texts,
                hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
            ))

            # Determine y-axis format
            if 'percentage' in metric2_type or '%' in metric2_name:
                yaxis_format = '.1f'
                yaxis_suffix = '%'
                yaxis_title = f'{metric2_name}'
            elif 'currency' in metric2_type:
                yaxis_format = ',.0f'
                yaxis_suffix = ''
                yaxis_title = f'{metric2_name} ($)'
            else:
                yaxis_format = '.2f'
                yaxis_suffix = ''
                yaxis_title = metric2_name

            fig2.update_layout(
                title={
                    'text': metric2_name,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16, 'family': 'Montserrat', 'color': '#1a202c'}
                },
                xaxis_title='Company',
                yaxis_title=yaxis_title,
                height=450,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font={'family': 'Montserrat', 'size': 12},
                xaxis=dict(
                    showgrid=False,
                    showline=True,
                    linewidth=1,
                    linecolor='#e2e8f0'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='#f0f0f0',
                    tickformat=yaxis_format,
                    ticksuffix=yaxis_suffix
                ),
                margin=dict(l=60, r=20, t=60, b=80)
            )

            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(f"📊 No data available for {metric2_name}")


def create_group_custom_analysis_page():
    """Create custom analysis page with interactive metric comparison"""

    # Require authentication
    require_auth()

    # Get current period for data fetching
    current_period = st.session_state.get('period', 'year_end')
    period_display = get_period_display_text()

    # Apply page header with period selector
    create_page_header(
        page_title=f"Custom Analysis - {period_display}",
        subtitle="Compare any two metrics across selected companies to discover insights and relationships in your data.",
        show_period_selector=True
    )

    st.markdown('<div style="border-bottom: 2px solid #e2e8f0; margin: 1.5rem 0;"></div>', unsafe_allow_html=True)

    # Get available metrics
    available_metrics = get_available_metrics()

    # Flatten metrics for selectbox
    all_metric_names = []
    for category, metrics in available_metrics.items():
        all_metric_names.extend(metrics)

    # Create two columns for metric settings
    col_metric1, col_metric2 = st.columns(2)

    # Add CSS for larger font sizes
    st.markdown("""
    <style>
        /* Increase font size for metric selection labels */
        div[data-testid="stSelectbox"] label {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
        }

        /* Increase font size for selectbox options */
        div[data-baseweb="select"] {
            font-size: 1.2rem !important;
        }

        /* Increase font size for multiselect labels */
        div[data-testid="stMultiSelect"] label {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
        }

        /* Increase font size for checkbox labels */
        div[data-testid="stCheckbox"] label {
            font-size: 1.2rem !important;
        }

        /* Increase font size for selected options in dropdowns */
        div[data-baseweb="select"] > div {
            font-size: 1.2rem !important;
        }

        /* Increase caption text size */
        .stCaption {
            font-size: 1.1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    with col_metric1:
        st.markdown('<p style="font-size: 1.3rem; font-weight: 600; margin-bottom: 0.5rem;">📊 Metric 1</p>', unsafe_allow_html=True)
        metric1 = st.selectbox(
            "Metric 1",
            options=all_metric_names,
            index=all_metric_names.index('Gross Profit Margin') if 'Gross Profit Margin' in all_metric_names else 0,
            key="custom_analysis_metric1",
            help="Select the first metric to compare",
            label_visibility="collapsed"
        )

    with col_metric2:
        st.markdown('<p style="font-size: 1.3rem; font-weight: 600; margin-bottom: 0.5rem;">📊 Metric 2</p>', unsafe_allow_html=True)
        metric2 = st.selectbox(
            "Metric 2",
            options=all_metric_names,
            index=all_metric_names.index('Operating Profit Margin') if 'Operating Profit Margin' in all_metric_names else 1,
            key="custom_analysis_metric2",
            help="Select the second metric to compare",
            label_visibility="collapsed"
        )

    # Company selection
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Get all companies
    companies = get_companies_cached()

    if not companies:
        st.error("❌ Unable to fetch company list")
        return

    company_names = sorted([comp['name'] for comp in companies])

    # Initialize session state for company selection
    if 'custom_analysis_select_all' not in st.session_state:
        st.session_state.custom_analysis_select_all = False
    if 'custom_analysis_selected_companies' not in st.session_state:
        # Default to first 5 companies
        st.session_state.custom_analysis_selected_companies = company_names[:5] if len(company_names) >= 5 else company_names

    st.markdown('<p style="font-size: 1.3rem; font-weight: 600; margin-bottom: 0.5rem;">🏢 Select Companies</p>', unsafe_allow_html=True)

    # Select All checkbox
    select_all = st.checkbox(
        "Select All Companies",
        value=st.session_state.custom_analysis_select_all,
        key="custom_analysis_select_all_check"
    )

    if select_all:
        selected_companies = company_names
        st.session_state.custom_analysis_selected_companies = company_names
        st.session_state.custom_analysis_select_all = True
    else:
        st.session_state.custom_analysis_select_all = False
        # Company multi-select
        selected_companies = st.multiselect(
            "Choose companies to compare",
            options=company_names,
            default=st.session_state.custom_analysis_selected_companies,
            key="custom_analysis_company_select"
        )
        st.session_state.custom_analysis_selected_companies = selected_companies

    # Year selection
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)
    year_col, reset_col = st.columns([3, 1])

    with year_col:
        st.markdown('<p style="font-size: 1.3rem; font-weight: 600; margin-bottom: 0.5rem;">📅 Year</p>', unsafe_allow_html=True)
        selected_year = st.selectbox(
            "Year",
            options=[2024, 2023, 2022, 2021, 2020],
            index=0,
            key="custom_analysis_year_select",
            help="Select year for comparison",
            label_visibility="collapsed"
        )

    with reset_col:
        st.markdown('<div style="margin-top: 1.85rem;"></div>', unsafe_allow_html=True)
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.custom_analysis_select_all = False
            st.session_state.custom_analysis_selected_companies = company_names[:5] if len(company_names) >= 5 else company_names
            st.rerun()

    # Validation
    if not selected_companies:
        st.warning("⚠️ Please select at least one company to compare")
        return

    # Determine period filter
    if current_period == 'year_end':
        period_filter = f"{selected_year} Annual"
    else:
        period_filter = f"June {selected_year}"

    # Show loading and fetch data
    st.markdown('<div style="border-bottom: 2px solid #e2e8f0; margin: 2rem 0;"></div>', unsafe_allow_html=True)

    with st.spinner("Loading comparison data..."):
        metric1_data = fetch_metric_data(metric1, selected_companies, period_filter)
        metric2_data = fetch_metric_data(metric2, selected_companies, period_filter)

    # Display info about data
    data_info_col1, data_info_col2 = st.columns(2)
    with data_info_col1:
        st.caption(f"📊 Showing {len(metric1_data)} of {len(selected_companies)} companies for {metric1}")
    with data_info_col2:
        st.caption(f"📊 Showing {len(metric2_data)} of {len(selected_companies)} companies for {metric2}")

    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Create and display charts
    if not metric1_data and not metric2_data:
        st.warning(f"⚠️ No data available for the selected metrics and companies in {selected_year}")
        st.info("💡 Try selecting different metrics, companies, or year")
    else:
        create_dual_comparison_chart(metric1, metric1_data, metric2, metric2_data)


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="Custom Analysis - BPC Dashboard",
        page_icon="📈",
        layout="wide"
    )
    create_group_custom_analysis_page()
