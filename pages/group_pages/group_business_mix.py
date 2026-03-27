import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import os
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Import from shared modules
from shared.airtable_connection import get_airtable_connection
from shared.page_components import create_page_header, get_period_display_text, sort_companies_by_rank
from shared.auth_utils import require_auth, is_super_admin
from shared.year_config import CURRENT_YEAR

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def fetch_all_companies_income_statement(period):
    """Fetch income statement data for all companies for a specific period"""
    airtable = get_airtable_connection()

    # Get all companies
    from shared.airtable_connection import get_companies_cached
    companies = get_companies_cached()

    if not companies:
        return None

    company_data = {}

    for company in companies:
        company_name = company.get('name')
        if not company_name:
            continue

        # Fetch income statement data for this company
        income_data = airtable.get_income_statement_data_by_period(company_name, period, is_admin=is_super_admin())

        if income_data and len(income_data) > 0:
            company_data[company_name] = income_data[0]

    return company_data


def extract_business_mix_data_for_export(period):
    """
    Extract business mix data as a pandas DataFrame for Excel export.
    Shows revenue mix percentages by category for each company.

    Returns:
        pandas.DataFrame with revenue categories as rows, companies as columns
    """
    # Reuse cached data from income statement
    company_data = fetch_all_companies_income_statement(period)

    if not company_data:
        return None

    # Define revenue line items and categories
    revenue_items = [
        ('intra_state_hhg', 'HHG_MOVING'),
        ('local_hhg', 'HHG_MOVING'),
        ('inter_state_hhg', 'HHG_MOVING'),
        ('office_industrial', 'NON_HHG'),
        ('warehouse', 'WAREHOUSE'),
        ('warehouse_handling', 'WAREHOUSE'),
        ('international', 'HHG_MOVING'),
        ('packing_unpacking', 'HHG_MOVING'),
        ('booking_royalties', 'OTHER'),
        ('special_products', 'NON_HHG'),
        ('records_storage', 'WAREHOUSE'),
        ('military_dpm_contracts', 'HHG_MOVING'),
        ('distribution', 'NON_HHG'),
        ('hotel_deliveries', 'NON_HHG'),
        ('other_revenue', 'OTHER')
    ]

    # Filter companies with data
    companies_with_data = []
    for company_name, data in company_data.items():
        total_revenue = data.get('total_revenue', 0) or 0
        if total_revenue > 0:
            companies_with_data.append(company_name)

    if not companies_with_data:
        return None

    # Calculate category percentages for each company
    categories = ['HHG_MOVING', 'NON_HHG', 'WAREHOUSE', 'OTHER']

    data_dict = {}

    for company in sorted(companies_with_data):
        data = company_data[company]
        total_revenue = data.get('total_revenue', 0) or 0

        # Calculate totals for each category
        category_totals = {}
        for category in categories:
            category_total = 0
            for field_name, cat in revenue_items:
                if cat == category:
                    value = data.get(field_name, 0) or 0
                    category_total += value
            category_totals[category] = category_total

        # Convert to percentages
        category_percentages = []
        for category in categories:
            if total_revenue > 0:
                pct = (category_totals[category] / total_revenue) * 100
                formatted = f'{pct:.1f}%'
            else:
                formatted = '-'
            category_percentages.append(formatted)

        data_dict[company] = category_percentages

    # Create DataFrame
    df = pd.DataFrame(data_dict, index=categories)
    df.index.name = 'Revenue Category'

    return df


def create_revenue_mix_charts(company_data, selected_year, period, margin_overlay='None'):
    """Create stacked bar charts showing revenue mix by category for each company as percentages

    Args:
        company_data: Dictionary of company income statement data
        selected_year: Year for the chart title
        period: Period filter for ranking (e.g., "2024 Annual" or "June 2024")
        margin_overlay: One of 'None', 'Gross Profit Margin', 'Operating Profit Margin'
    """

    # Define revenue line items and their categories based on the user's table
    revenue_items = [
        ('intra_state_hhg', 'HHG_MOVING'),
        ('local_hhg', 'HHG_MOVING'),
        ('inter_state_hhg', 'HHG_MOVING'),
        ('office_industrial', 'NON_HHG'),
        ('warehouse', 'WAREHOUSE'),
        ('warehouse_handling', 'WAREHOUSE'),
        ('international', 'HHG_MOVING'),
        ('packing_unpacking', 'HHG_MOVING'),
        ('booking_royalties', 'OTHER'),
        ('special_products', 'NON_HHG'),
        ('records_storage', 'WAREHOUSE'),
        ('military_dpm_contracts', 'HHG_MOVING'),
        ('distribution', 'NON_HHG'),
        ('hotel_deliveries', 'NON_HHG'),
        ('other_revenue', 'OTHER')
    ]

    # Get list of companies with data
    companies_with_data = []
    for company_name, data in company_data.items():
        total_revenue = data.get('total_revenue', 0) or 0
        if total_revenue > 0:
            companies_with_data.append(company_name)

    # Sort by rank (rank 1 on the right)
    companies_with_data = sort_companies_by_rank(companies_with_data, period)

    if not companies_with_data:
        st.warning(f"⚠️ No revenue data available for {selected_year}.")
        return

    # Calculate category percentages for each company
    company_categories = {}

    for company_name in companies_with_data:
        data = company_data[company_name]
        total_revenue = data.get('total_revenue', 0) or 0

        categories = {
            'HHG_MOVING': 0,
            'NON_HHG': 0,
            'WAREHOUSE': 0,
            'OTHER': 0
        }

        # Sum up dollar values first
        for field_name, category in revenue_items:
            value = data.get(field_name, 0) or 0
            categories[category] += value

        # Convert to percentages
        percentages = {}
        dollar_values = {}
        for cat, value in categories.items():
            if total_revenue > 0:
                percentages[cat] = (value / total_revenue) * 100
                dollar_values[cat] = value
            else:
                percentages[cat] = 0
                dollar_values[cat] = 0

        company_categories[company_name] = {
            'percentages': percentages,
            'dollar_values': dollar_values,
            'total_revenue': total_revenue
        }

    # Define category display names and colors
    category_names = {
        'HHG_MOVING': 'HHG Moving',
        'NON_HHG': 'Non-HHG',
        'WAREHOUSE': 'Warehouse',
        'OTHER': 'Other'
    }

    category_colors = {
        'HHG_MOVING': '#025a9a',
        'NON_HHG': '#0e9cd5',
        'WAREHOUSE': '#5bb4e5',
        'OTHER': '#a8d8f0'
    }

    # Create stacked bar chart with secondary y-axis for profit margin overlay
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Category order for stacking (bottom to top)
    # Reversed so largest category (HHG_MOVING) appears at bottom
    category_list = ['OTHER', 'WAREHOUSE', 'NON_HHG', 'HHG_MOVING']

    # Add bars for each category (in reverse order for legend display)
    for category in reversed(category_list):
        percentages = [company_categories[comp]['percentages'][category] for comp in companies_with_data]
        dollar_values = [company_categories[comp]['dollar_values'][category] for comp in companies_with_data]

        # Create comprehensive hover text showing all categories for each company
        hover_texts = []
        for comp in companies_with_data:
            # Build hover text with all categories - using bold formatting like company pages
            hover_lines = [f"<b>{comp}</b>", ""]  # Company name and blank line
            for cat in category_list:
                pct = company_categories[comp]['percentages'][cat]
                dollar = company_categories[comp]['dollar_values'][cat]
                hover_lines.append(f"<b>{category_names[cat]}:</b> {pct:.1f}% (${dollar:,.0f})")

            # Add total revenue line
            total_rev = company_categories[comp]['total_revenue']
            hover_lines.append("")
            hover_lines.append(f"<b>Total Revenue:</b> ${total_rev:,.0f}")

            # Add profit margin if overlay is selected
            if margin_overlay != 'None':
                margin_field = 'gpm' if margin_overlay == 'Gross Profit Margin' else 'opm'
                margin_val = company_data[comp].get(margin_field, 0) or 0
                # Convert to percentage if stored as decimal
                if 0 < margin_val < 1:
                    margin_val = margin_val * 100
                hover_lines.append(f"<b>{margin_overlay}:</b> {margin_val:.1f}%")

            hover_text = "<br>".join(hover_lines)
            hover_texts.append(hover_text)

        fig.add_trace(go.Bar(
            name=category_names[category],
            x=companies_with_data,
            y=percentages,
            marker_color=category_colors[category],
            text=[f'{p:.1f}%' if p >= 5 else '' for p in percentages],  # Only show text if >= 5%
            textposition='inside',
            textfont=dict(color='white', size=14, family='Montserrat'),
            customdata=hover_texts,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
        ), secondary_y=False)

    # Add profit margin line overlay if selected
    if margin_overlay != 'None':
        # Determine which margin to use
        margin_field = 'gpm' if margin_overlay == 'Gross Profit Margin' else 'opm'
        margin_color = '#c2002f'  # Atlas red for both margin types

        # Extract margin values for each company
        margin_values = []
        for comp in companies_with_data:
            margin_val = company_data[comp].get(margin_field, 0) or 0
            # Convert to percentage (multiply by 100 if stored as decimal)
            if 0 < margin_val < 1:  # Likely stored as decimal
                margin_val = margin_val * 100
            margin_values.append(margin_val)

        # Create hover text for margin line
        margin_hover_texts = []
        for comp, margin_val in zip(companies_with_data, margin_values):
            hover_text = f"<b>{comp}</b><br><b>{margin_overlay}:</b> {margin_val:.1f}%"
            margin_hover_texts.append(hover_text)

        # Add line trace on secondary y-axis
        fig.add_trace(go.Scatter(
            name=margin_overlay,
            x=companies_with_data,
            y=margin_values,
            mode='lines+markers',
            line=dict(color=margin_color, width=3),
            marker=dict(size=8, color=margin_color),
            customdata=margin_hover_texts,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
        ), secondary_y=True)

    # Update layout with dynamic year in title
    fig.update_layout(
        title={
            'text': f'{selected_year} Revenue Mix by Category (% of Total Revenue)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='',
        barmode='stack',
        height=600,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.25,
            xanchor='center',
            x=0.5,
            font=dict(size=16, family='Montserrat'),
            traceorder='normal'
        ),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='#e2e8f0',
            tickfont=dict(size=16, family='Montserrat, sans-serif'),
            tickangle=-45
        ),
        margin=dict(
            l=60,
            r=60,
            t=80,
            b=120
        )
    )

    # Update primary y-axis (for stacked bars)
    fig.update_yaxes(
        title_text='Percentage of Revenue (%)',
        tickformat='.0f',
        ticksuffix='%',
        gridcolor='#f0f0f0',
        range=[0, 100],
        secondary_y=False
    )

    # Update secondary y-axis (for profit margin line) - only visible when overlay is active
    if margin_overlay != 'None':
        fig.update_yaxes(
            title_text='Profit Margin (%)',
            tickformat='.0f',
            ticksuffix='%',
            gridcolor='#f0f0f0',
            range=[0, 100],
            showgrid=False,  # Don't show gridlines for secondary axis to avoid clutter
            secondary_y=True
        )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# NOTE: Custom Analysis (Playground) functionality has been moved to
# group_custom_analysis.py for easier access via sidebar navigation
# ============================================================================


def display_category_reference_table():
    """Display a reference table showing which line items belong to each category"""

    # Define line items and their categories
    category_items = {
        'HHG_MOVING': [
            'intra_state_hhg',
            'local_hhg',
            'inter_state_hhg',
            'international',
            'packing_unpacking',
            'military_dpm_contracts'
        ],
        'NON_HHG': [
            'office_industrial',
            'special_products',
            'distribution',
            'hotel_deliveries'
        ],
        'WAREHOUSE': [
            'warehouse',
            'warehouse_handling',
            'records_storage'
        ],
        'OTHER': [
            'booking_royalties',
            'other_revenue'
        ]
    }

    # Category display names
    category_names = {
        'HHG_MOVING': 'HHG Moving',
        'NON_HHG': 'Non-HHG',
        'WAREHOUSE': 'Warehouse',
        'OTHER': 'Other'
    }

    # Helper function to format line item names professionally
    def format_line_item(item_name):
        """Convert snake_case to Title Case"""
        return item_name.replace('_', ' ').title()

    # Add some spacing before table
    st.markdown('<div style="margin: 2rem 0;"></div>', unsafe_allow_html=True)

    # Table title - centered
    st.markdown("""
    <div style="margin: 1.5rem 0; text-align: center;">
        <h3 style="color: #1a202c; font-family: 'Montserrat', sans-serif; font-weight: 600; margin-bottom: 1rem;">Revenue Category Reference</h3>
    </div>
    """, unsafe_allow_html=True)

    # Create table HTML with centering wrapper
    table_html = """
    <style>
    .category-reference-container {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    .category-reference-table {
        width: 100%;
        max-width: 600px;
        border-collapse: collapse;
        margin: 1rem 0;
        font-family: 'Montserrat', sans-serif;
        font-size: 1rem;
        border: 1px solid #025a9a;
    }
    .category-reference-table th {
        background-color: #025a9a;
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: 600;
        border: 1px solid #025a9a;
    }
    .category-reference-table td {
        padding: 10px;
        border: 1px solid #025a9a;
        background-color: white;
    }
    .category-reference-table .line-item-cell {
        color: #1a202c;
    }
    .category-reference-table .category-cell {
        font-weight: 500;
        color: #1a202c;
    }
    </style>

    <div class="category-reference-container">
        <table class="category-reference-table">
            <thead>
                <tr>
                    <th>Line Items</th>
                    <th>Category</th>
                </tr>
            </thead>
            <tbody>
    """

    # Add rows for each category and its items
    for category_key in ['HHG_MOVING', 'NON_HHG', 'WAREHOUSE', 'OTHER']:
        items = category_items[category_key]
        category_display = category_names[category_key]

        for item in items:
            formatted_item = format_line_item(item)
            table_html += f'<tr><td class="line-item-cell">{formatted_item}</td><td class="category-cell">{category_display}</td></tr>'

    table_html += """
            </tbody>
        </table>
    </div>
    """

    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)


def create_expense_mix_charts(company_data, selected_year, period, margin_overlay='None'):
    """Create stacked bar charts showing expense mix by category for each company as percentages

    Args:
        company_data: Dictionary of company income statement data
        selected_year: Year for the chart title
        period: Period filter for ranking (e.g., "2024 Annual" or "June 2024")
        margin_overlay: One of 'None', 'Gross Profit Margin', 'Operating Profit Margin'
    """

    # Define expense line items and their categories based on user requirements
    expense_items = [
        ('direct_wages', 'DIRECT_WAGES'),
        ('vehicle_operating_expenses', 'VEHICLE_OPERATING_EXPENSES'),
        ('packing_warehouse_supplies', 'PACKING_WAREHOUSE_SUPPLIES'),
        ('oo_exp_intra_state', 'OWNER_OPERATOR_EXPENSES'),
        ('oo_inter_state', 'OWNER_OPERATOR_EXPENSES'),
        ('oo_oi', 'OWNER_OPERATOR_EXPENSES'),
        ('oo_packing', 'OWNER_OPERATOR_EXPENSES'),
        ('oo_other', 'OWNER_OPERATOR_EXPENSES'),
        ('lease_expense_rev_equip', 'LEASE_EXPENSE_REV_EQUIP'),
    ]

    # Get list of companies with data
    companies_with_data = []
    for company_name, data in company_data.items():
        total_revenue = data.get('total_revenue', 0) or 0
        if total_revenue > 0:
            companies_with_data.append(company_name)

    # Sort by rank (rank 1 on the right)
    companies_with_data = sort_companies_by_rank(companies_with_data, period)

    if not companies_with_data:
        st.warning(f"⚠️ No expense data available for {selected_year}.")
        return

    # Calculate category percentages for each company
    company_categories = {}

    for company_name in companies_with_data:
        data = company_data[company_name]
        total_revenue = data.get('total_revenue', 0) or 0

        categories = {
            'DIRECT_WAGES': 0,
            'VEHICLE_OPERATING_EXPENSES': 0,
            'PACKING_WAREHOUSE_SUPPLIES': 0,
            'OWNER_OPERATOR_EXPENSES': 0,
            'LEASE_EXPENSE_REV_EQUIP': 0
        }

        # Sum up dollar values first
        for field_name, category in expense_items:
            value = data.get(field_name, 0) or 0
            categories[category] += value

        # Convert to percentages of revenue
        percentages = {}
        dollar_values = {}
        for cat, value in categories.items():
            if total_revenue > 0:
                percentages[cat] = (value / total_revenue) * 100
                dollar_values[cat] = value
            else:
                percentages[cat] = 0
                dollar_values[cat] = 0

        company_categories[company_name] = {
            'percentages': percentages,
            'dollar_values': dollar_values,
            'total_revenue': total_revenue
        }

    # Define category display names and colors (using Atlas blue scheme like revenue mix)
    category_names = {
        'DIRECT_WAGES': 'Direct Wages',
        'VEHICLE_OPERATING_EXPENSES': 'Vehicle Operating Expenses',
        'PACKING_WAREHOUSE_SUPPLIES': 'Packing/Warehouse Supplies',
        'OWNER_OPERATOR_EXPENSES': 'Owner Operator Expenses',
        'LEASE_EXPENSE_REV_EQUIP': 'Lease Expense - Revenue Equipment'
    }

    category_colors = {
        'DIRECT_WAGES': '#025a9a',
        'VEHICLE_OPERATING_EXPENSES': '#0e9cd5',
        'PACKING_WAREHOUSE_SUPPLIES': '#5bb4e5',
        'OWNER_OPERATOR_EXPENSES': '#a8d8f0',
        'LEASE_EXPENSE_REV_EQUIP': '#1a75bb'
    }

    # Create stacked bar chart with secondary y-axis for profit margin overlay
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Category order for stacking (bottom to top)
    # Reversed so largest categories appear at bottom for easier comparison
    category_list = ['LEASE_EXPENSE_REV_EQUIP', 'OWNER_OPERATOR_EXPENSES', 'PACKING_WAREHOUSE_SUPPLIES', 'VEHICLE_OPERATING_EXPENSES', 'DIRECT_WAGES']

    # Add bars for each category (in reverse order for legend display)
    for category in reversed(category_list):
        percentages = [company_categories[comp]['percentages'][category] for comp in companies_with_data]
        dollar_values = [company_categories[comp]['dollar_values'][category] for comp in companies_with_data]

        # Create comprehensive hover text showing all categories for each company
        hover_texts = []
        for comp in companies_with_data:
            # Build hover text with all categories
            hover_lines = [f"<b>{comp}</b>", ""]  # Company name and blank line
            for cat in category_list:
                pct = company_categories[comp]['percentages'][cat]
                dollar = company_categories[comp]['dollar_values'][cat]
                hover_lines.append(f"<b>{category_names[cat]}:</b> {pct:.1f}% (${dollar:,.0f})")

            # Add total revenue line
            total_rev = company_categories[comp]['total_revenue']
            hover_lines.append("")
            hover_lines.append(f"<b>Total Revenue:</b> ${total_rev:,.0f}")

            # Add profit margin if overlay is selected
            if margin_overlay != 'None':
                margin_field = 'gpm' if margin_overlay == 'Gross Profit Margin' else 'opm'
                margin_val = company_data[comp].get(margin_field, 0) or 0
                # Convert to percentage if stored as decimal
                if 0 < margin_val < 1:
                    margin_val = margin_val * 100
                hover_lines.append(f"<b>{margin_overlay}:</b> {margin_val:.1f}%")

            hover_text = "<br>".join(hover_lines)
            hover_texts.append(hover_text)

        fig.add_trace(go.Bar(
            name=category_names[category],
            x=companies_with_data,
            y=percentages,
            marker_color=category_colors[category],
            text=[f'{p:.1f}%' if p >= 5 else '' for p in percentages],  # Only show text if >= 5%
            textposition='inside',
            textfont=dict(color='white', size=14, family='Montserrat'),
            customdata=hover_texts,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
        ), secondary_y=False)

    # Add profit margin line overlay if selected
    if margin_overlay != 'None':
        # Determine which margin to use
        margin_field = 'gpm' if margin_overlay == 'Gross Profit Margin' else 'opm'
        margin_color = '#c2002f'  # Atlas red for margin line

        # Extract margin values for each company
        margin_values = []
        for comp in companies_with_data:
            margin_val = company_data[comp].get(margin_field, 0) or 0
            # Convert to percentage (multiply by 100 if stored as decimal)
            if 0 < margin_val < 1:  # Likely stored as decimal
                margin_val = margin_val * 100
            margin_values.append(margin_val)

        # Create hover text for margin line
        margin_hover_texts = []
        for comp, margin_val in zip(companies_with_data, margin_values):
            hover_text = f"<b>{comp}</b><br><b>{margin_overlay}:</b> {margin_val:.1f}%"
            margin_hover_texts.append(hover_text)

        # Add line trace on secondary y-axis
        fig.add_trace(go.Scatter(
            name=margin_overlay,
            x=companies_with_data,
            y=margin_values,
            mode='lines+markers',
            line=dict(color=margin_color, width=3),
            marker=dict(size=8, color=margin_color),
            customdata=margin_hover_texts,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
        ), secondary_y=True)

    # Update layout with dynamic year in title
    fig.update_layout(
        title={
            'text': f'{selected_year} Direct Labor & Equipment Expenses (% of Total Revenue)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='',
        barmode='stack',
        height=600,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=16, family='Montserrat'),
            traceorder='normal'
        ),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='#e2e8f0',
            tickfont=dict(size=16, family='Montserrat, sans-serif'),
            tickangle=-45
        ),
        margin=dict(
            l=60,
            r=60,
            t=120,
            b=80
        )
    )

    # Calculate maximum stacked bar height for dynamic y-axis
    max_total = 0
    for comp in companies_with_data:
        total = sum(company_categories[comp]['percentages'].values())
        if total > max_total:
            max_total = total

    # Set y-axis range to 120% of max value for better spacing
    y_max = max_total * 1.2

    # Update primary y-axis (for stacked bars)
    fig.update_yaxes(
        title_text='Percentage of Revenue (%)',
        tickformat='.0f',
        ticksuffix='%',
        gridcolor='#f0f0f0',
        range=[0, y_max],
        secondary_y=False
    )

    # Update secondary y-axis (for profit margin line) - only visible when overlay is active
    if margin_overlay != 'None':
        fig.update_yaxes(
            title_text='Profit Margin (%)',
            tickformat='.0f',
            ticksuffix='%',
            gridcolor='#f0f0f0',
            range=[0, 100],
            showgrid=False,  # Don't show gridlines for secondary axis to avoid clutter
            secondary_y=True
        )

    st.plotly_chart(fig, use_container_width=True)


def create_additional_expense_mix_charts(company_data, selected_year, period, margin_overlay='None'):
    """Create stacked bar charts showing additional expense categories as percentages

    Args:
        company_data: Dictionary of company income statement data
        selected_year: Year for the chart title
        period: Period filter for ranking (e.g., "2024 Annual" or "June 2024")
        margin_overlay: One of 'None', 'Gross Profit Margin', 'Operating Profit Margin'
    """

    # Define additional expense line items and their categories
    expense_items = [
        ('claims', 'CLAIMS'),
        ('other_trans_exp', 'OTHER_TRANS_EXP'),
        ('depreciation', 'DEPRECIATION'),
        ('rent', 'RENT'),
        ('other_direct_expenses', 'OTHER_DIRECT_EXPENSES'),
    ]

    # Get list of companies with data
    companies_with_data = []
    for company_name, data in company_data.items():
        total_revenue = data.get('total_revenue', 0) or 0
        if total_revenue > 0:
            companies_with_data.append(company_name)

    # Sort by rank (rank 1 on the right)
    companies_with_data = sort_companies_by_rank(companies_with_data, period)

    if not companies_with_data:
        st.warning(f"⚠️ No additional expense data available for {selected_year}.")
        return

    # Calculate category percentages for each company
    company_categories = {}

    for company_name in companies_with_data:
        data = company_data[company_name]
        total_revenue = data.get('total_revenue', 0) or 0

        categories = {
            'CLAIMS': 0,
            'OTHER_TRANS_EXP': 0,
            'DEPRECIATION': 0,
            'RENT': 0,
            'OTHER_DIRECT_EXPENSES': 0
        }

        # Sum up dollar values first
        for field_name, category in expense_items:
            value = data.get(field_name, 0) or 0
            categories[category] += value

        # Convert to percentages of revenue
        percentages = {}
        dollar_values = {}
        for cat, value in categories.items():
            if total_revenue > 0:
                percentages[cat] = (value / total_revenue) * 100
                dollar_values[cat] = value
            else:
                percentages[cat] = 0
                dollar_values[cat] = 0

        company_categories[company_name] = {
            'percentages': percentages,
            'dollar_values': dollar_values,
            'total_revenue': total_revenue
        }

    # Define category display names and colors (using Atlas blue scheme)
    category_names = {
        'CLAIMS': 'Claims',
        'OTHER_TRANS_EXP': 'Other Transportation Expense',
        'DEPRECIATION': 'Depreciation',
        'RENT': 'Rent',
        'OTHER_DIRECT_EXPENSES': 'Other Direct Expenses'
    }

    category_colors = {
        'CLAIMS': '#025a9a',
        'OTHER_TRANS_EXP': '#0e9cd5',
        'DEPRECIATION': '#5bb4e5',
        'RENT': '#a8d8f0',
        'OTHER_DIRECT_EXPENSES': '#7ec8e3'
    }

    # Create stacked bar chart with secondary y-axis for profit margin overlay
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Category order for stacking (bottom to top)
    # Reversed so largest categories appear at bottom for easier comparison
    category_list = ['OTHER_DIRECT_EXPENSES', 'RENT', 'DEPRECIATION', 'OTHER_TRANS_EXP', 'CLAIMS']

    # Add bars for each category (in reverse order for legend display)
    for category in reversed(category_list):
        percentages = [company_categories[comp]['percentages'][category] for comp in companies_with_data]
        dollar_values = [company_categories[comp]['dollar_values'][category] for comp in companies_with_data]

        # Create comprehensive hover text showing all categories for each company
        hover_texts = []
        for comp in companies_with_data:
            # Build hover text with all categories
            hover_lines = [f"<b>{comp}</b>", ""]  # Company name and blank line
            for cat in category_list:
                pct = company_categories[comp]['percentages'][cat]
                dollar = company_categories[comp]['dollar_values'][cat]
                hover_lines.append(f"<b>{category_names[cat]}:</b> {pct:.1f}% (${dollar:,.0f})")

            # Add total revenue line
            total_rev = company_categories[comp]['total_revenue']
            hover_lines.append("")
            hover_lines.append(f"<b>Total Revenue:</b> ${total_rev:,.0f}")

            # Add profit margin if overlay is selected
            if margin_overlay != 'None':
                margin_field = 'gpm' if margin_overlay == 'Gross Profit Margin' else 'opm'
                margin_val = company_data[comp].get(margin_field, 0) or 0
                # Convert to percentage if stored as decimal
                if 0 < margin_val < 1:
                    margin_val = margin_val * 100
                hover_lines.append(f"<b>{margin_overlay}:</b> {margin_val:.1f}%")

            hover_text = "<br>".join(hover_lines)
            hover_texts.append(hover_text)

        fig.add_trace(go.Bar(
            name=category_names[category],
            x=companies_with_data,
            y=percentages,
            marker_color=category_colors[category],
            text=[f'{p:.1f}%' if p >= 5 else '' for p in percentages],  # Only show text if >= 5%
            textposition='inside',
            textfont=dict(color='white', size=14, family='Montserrat'),
            customdata=hover_texts,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
        ), secondary_y=False)

    # Add profit margin line overlay if selected
    if margin_overlay != 'None':
        # Determine which margin to use
        margin_field = 'gpm' if margin_overlay == 'Gross Profit Margin' else 'opm'
        margin_color = '#c2002f'  # Atlas red for margin line

        # Extract margin values for each company
        margin_values = []
        for comp in companies_with_data:
            margin_val = company_data[comp].get(margin_field, 0) or 0
            # Convert to percentage (multiply by 100 if stored as decimal)
            if 0 < margin_val < 1:  # Likely stored as decimal
                margin_val = margin_val * 100
            margin_values.append(margin_val)

        # Create hover text for margin line
        margin_hover_texts = []
        for comp, margin_val in zip(companies_with_data, margin_values):
            hover_text = f"<b>{comp}</b><br><b>{margin_overlay}:</b> {margin_val:.1f}%"
            margin_hover_texts.append(hover_text)

        # Add line trace on secondary y-axis
        fig.add_trace(go.Scatter(
            name=margin_overlay,
            x=companies_with_data,
            y=margin_values,
            mode='lines+markers',
            line=dict(color=margin_color, width=3),
            marker=dict(size=8, color=margin_color),
            customdata=margin_hover_texts,
            hovertemplate='<span style="font-size: 16px;">%{customdata}</span><extra></extra>'
        ), secondary_y=True)

    # Update layout with dynamic year in title
    fig.update_layout(
        title={
            'text': f'{selected_year} All Other Direct Expenses (% of Total Revenue)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat', 'color': '#1a202c'}
        },
        xaxis_title='',
        barmode='stack',
        height=600,
        font=dict(family='Montserrat'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=16, family='Montserrat'),
            traceorder='normal'
        ),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='#e2e8f0',
            tickfont=dict(size=16, family='Montserrat, sans-serif'),
            tickangle=-45
        ),
        margin=dict(
            l=60,
            r=60,
            t=120,
            b=80
        )
    )

    # Calculate maximum stacked bar height for dynamic y-axis
    max_total = 0
    for comp in companies_with_data:
        total = sum(company_categories[comp]['percentages'].values())
        if total > max_total:
            max_total = total

    # Set y-axis range to 120% of max value for better spacing
    y_max = max_total * 1.2

    # Update primary y-axis (for stacked bars)
    fig.update_yaxes(
        title_text='Percentage of Revenue (%)',
        tickformat='.0f',
        ticksuffix='%',
        gridcolor='#f0f0f0',
        range=[0, y_max],
        secondary_y=False
    )

    # Update secondary y-axis (for profit margin line) - only visible when overlay is active
    if margin_overlay != 'None':
        fig.update_yaxes(
            title_text='Profit Margin (%)',
            tickformat='.0f',
            ticksuffix='%',
            gridcolor='#f0f0f0',
            range=[0, 100],
            showgrid=False,  # Don't show gridlines for secondary axis to avoid clutter
            secondary_y=True
        )

    st.plotly_chart(fig, use_container_width=True)


def create_group_business_mix_page():
    """Create group business mix comparison page with tabs for Revenue Mix and Expense Mix"""

    # Require authentication
    require_auth()

    # Initialize year selection in session state (default to most recent year)
    if 'group_business_mix_selected_year' not in st.session_state:
        st.session_state.group_business_mix_selected_year = CURRENT_YEAR

    # Get current period for data fetching
    current_period = st.session_state.get('period', 'year_end')
    period_display = get_period_display_text()

    # Remove any custom selectbox styling to match homepage
    st.markdown("""
    <style>
    /* Remove blue border from Analysis Type selector in sidebar */
    div[data-testid="stSelectbox"] > div > div {
        border-color: #e2e8f0 !important;
    }
    div[data-testid="stSelectbox"] > div > div:focus,
    div[data-testid="stSelectbox"] > div > div:focus-within {
        border-color: #cbd5e0 !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Apply page header with period selector and dynamic title
    create_page_header(
        page_title=f"Group Business Mix Comparison - {period_display}",
        subtitle=None,
        show_period_selector=True
    )

    # Add some spacing before filter section
    st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

    # Create layout: Title on left, large spacer, compact year filter aligned with table
    col_title, col_spacer, col_filter = st.columns([3, 6, 1])

    with col_title:
        # Show selected year prominently - reduced font size to fit on one line
        st.markdown(f"""
        <div style="margin: 1rem 0;">
            <h2 style="color: #1a202c; font-family: 'Montserrat', sans-serif; font-weight: 600; margin: 0; font-size: 1.5rem; white-space: nowrap;">
                {st.session_state.group_business_mix_selected_year} Business Mix
            </h2>
        </div>
        """, unsafe_allow_html=True)

    with col_filter:
        # Year filter - same default size as homepage selectboxes
        year_options = list(range(CURRENT_YEAR, CURRENT_YEAR - 5, -1))
        selected_year = st.selectbox(
            "**Select Year**",
            options=year_options,
            index=year_options.index(st.session_state.group_business_mix_selected_year) if st.session_state.group_business_mix_selected_year in year_options else 0,
            key="group_business_mix_year_selector"
        )

        # Update session state if year changed
        if selected_year != st.session_state.group_business_mix_selected_year:
            st.session_state.group_business_mix_selected_year = selected_year
            st.rerun()

    # Add some spacing
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Get Airtable connection
    conn = get_airtable_connection()

    if not conn:
        st.error("❌ Unable to connect to Airtable. Please check your credentials.")
        return

    # Get selected year from session state
    selected_year = st.session_state.group_business_mix_selected_year

    # Determine period filter based on selection and year
    if current_period == 'year_end':
        period_filter = f"{selected_year} Annual"
    else:
        period_filter = f"June {selected_year}"

    # Fetch data for selected year
    with st.spinner("Loading business mix data..."):
        company_data = fetch_all_companies_income_statement(period_filter)

    if not company_data:
        st.warning(f"⚠️ No business mix data available for {selected_year} - {period_display}.")
        st.info("💡 Try selecting a different year or period.")
        return

    # Create tabs for Revenue Mix, Direct Expense Mix, and All Other Direct Expense Mix
    tab1, tab2, tab3 = st.tabs(["📊 Revenue Mix", "💸 Direct Expense Mix", "📉 All Other Direct Expense Mix"])

    with tab1:
        # Add profit margin overlay control with enhanced styling
        st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Add custom CSS for enhanced radio buttons with pill-shaped background
        st.markdown("""
        <style>
            /* Increase radio button size and spacing */
            div[data-testid="stRadio"] > div {
                gap: 2.5rem !important;
                background: linear-gradient(135deg, #e6f2ff 0%, #f0f8ff 100%) !important;
                border: 3px solid #025a9a !important;
                border-radius: 50px !important;
                padding: 1.5rem 2rem !important;
                margin: 1rem 0 !important;
                box-shadow: 0 3px 10px rgba(2, 90, 154, 0.2) !important;
            }

            /* Larger radio circles */
            div[data-testid="stRadio"] input[type="radio"] {
                width: 24px !important;
                height: 24px !important;
                cursor: pointer !important;
                margin-right: 0.5rem !important;
            }

            /* Larger label text */
            div[data-testid="stRadio"] label {
                font-size: 1.3rem !important;
                font-weight: 600 !important;
                cursor: pointer !important;
                padding: 0.5rem 0.8rem !important;
                border-radius: 8px !important;
                transition: background-color 0.2s ease !important;
            }

            /* Hover effect on labels */
            div[data-testid="stRadio"] label:hover {
                background-color: rgba(2, 90, 154, 0.15) !important;
            }

            /* Larger main label - the title text */
            div[data-testid="stRadio"] > label {
                font-size: 1.6rem !important;
                font-weight: 700 !important;
                color: #025a9a !important;
                margin-bottom: 1rem !important;
            }

            /* Larger tab text for better readability */
            div[data-testid="stTabs"] button[role="tab"] {
                font-size: 2rem !important;
                font-weight: 700 !important;
                padding: 1rem 2rem !important;
            }
        </style>
        """, unsafe_allow_html=True)

        margin_overlay = st.radio(
            "📈 Click to Overlay Profit Margin on Chart",
            options=['None', 'Gross Profit Margin', 'Operating Profit Margin'],
            index=0,
            horizontal=True,
            help="Overlay a profit margin line on the revenue mix chart for additional insight",
            key="group_business_mix_margin_overlay"
        )

        st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Display revenue mix charts with margin overlay
        create_revenue_mix_charts(company_data, selected_year, period_filter, margin_overlay)

        # Display category reference table below the chart
        display_category_reference_table()

    with tab2:
        st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # First chart - Primary expense categories
        margin_overlay_expense = st.radio(
            "📈 Click to Overlay Profit Margin on Chart",
            options=['None', 'Gross Profit Margin', 'Operating Profit Margin'],
            index=0,
            horizontal=True,
            help="Overlay a profit margin line on the direct expense mix chart for additional insight",
            key="group_business_mix_margin_overlay_expense"
        )

        st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Display primary expense mix charts with margin overlay
        create_expense_mix_charts(company_data, selected_year, period_filter, margin_overlay_expense)

    with tab3:
        st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Second chart - Additional expense categories
        margin_overlay_additional = st.radio(
            "📈 Click to Overlay Profit Margin on Chart",
            options=['None', 'Gross Profit Margin', 'Operating Profit Margin'],
            index=0,
            horizontal=True,
            help="Overlay a profit margin line on the chart for additional insight",
            key="group_business_mix_margin_overlay_additional"
        )

        st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        # Display additional expense mix charts with margin overlay
        create_additional_expense_mix_charts(company_data, selected_year, period_filter, margin_overlay_additional)


# For testing the page independently
if __name__ == "__main__":
    st.set_page_config(
        page_title="Group Business Mix - BPC Dashboard",
        page_icon="📊",
        layout="wide"
    )
    create_group_business_mix_page()
