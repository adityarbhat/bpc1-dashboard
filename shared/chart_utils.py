import plotly.graph_objects as go
import streamlit as st

# Formula definitions for each gauge ratio
GAUGE_FORMULAS = {
    "current_ratio": "Current Assets ÷ Current Liabilities",
    "debt_to_equity": "Total Liabilities ÷ Equity (Net Worth)",
    "working_capital_pct": "(Current Assets − Current Liabilities) ÷ Total Assets × 100",
    "survival_score": "(WC ÷ TA × 6.56) + (E ÷ TA × 3.26) + (P ÷ TA × 6.72) + (E ÷ D × 1.05)",
    "gpm": "(Revenue − Cost of Goods Sold) ÷ Revenue × 100",
    "opm": "Operating Profit ÷ Revenue × 100",
    "npm": "Net Profit ÷ Revenue × 100",
    "ebitda_margin": "EBITDA ÷ Revenue × 100",
    "rev_admin_employee": "Total Revenue ÷ Number of Admin Employees",
}


def render_gauge_with_formula(fig, formula_key):
    """Render a gauge chart with a hover tooltip showing the formula."""
    st.plotly_chart(fig, use_container_width=True)
    formula = GAUGE_FORMULAS.get(formula_key)
    if formula:
        st.markdown(f"""
        <div class="gauge-formula-tooltip" data-formula="{formula}">
            ℹ Formula
        </div>
        <style>
        .gauge-formula-tooltip {{
            text-align: center;
            font-size: 0.75rem;
            color: #718096;
            cursor: default;
            margin-top: -10px;
            margin-bottom: 8px;
            position: relative;
            display: inline-block;
            width: 100%;
        }}
        .gauge-formula-tooltip::after {{
            content: attr(data-formula);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #1a202c;
            color: #fff;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.7rem;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
            z-index: 1000;
        }}
        .gauge-formula-tooltip:hover::after {{
            opacity: 1;
        }}
        </style>
        """, unsafe_allow_html=True)


def create_gauge_chart(value, title, min_val=0, max_val=100, threshold_red=30, threshold_yellow=70, format_type="percent", reverse_colors=False):
    """Create a semicircular gauge chart with needle indicator matching the reference design"""

    # Handle None or invalid values
    if value is None:
        value = min_val

    # Extend range if value is outside of min/max bounds
    # For extreme values, add some padding to ensure visibility
    if value < min_val:
        # Add 20% padding for negative values to ensure good visualization
        padding = abs(value - min_val) * 0.2
        actual_min = value - padding
    else:
        actual_min = min_val

    if value > max_val:
        # Add 20% padding for values above max to ensure good visualization
        padding = abs(value - max_val) * 0.2
        actual_max = value + padding
    else:
        actual_max = max_val

    # Calculate proportional zone boundaries for the extended range
    # Always ensure all three zones are visible by proportionally mapping thresholds
    total_range = actual_max - actual_min
    original_range = max_val - min_val

    # Map original thresholds to new range proportionally
    if total_range > original_range:
        # For extended ranges, create proportional zones
        red_proportion = (threshold_red - min_val) / original_range
        yellow_proportion = (threshold_yellow - min_val) / original_range

        adjusted_threshold_red = actual_min + (red_proportion * total_range)
        adjusted_threshold_yellow = actual_min + (yellow_proportion * total_range)
    else:
        adjusted_threshold_red = threshold_red
        adjusted_threshold_yellow = threshold_yellow

    # Determine value color based on thresholds (for color-coded display)
    if reverse_colors:
        # For reverse metrics (lower is better), special logic for extreme values
        if value < 0:
            # Extreme negative values are always very bad for debt-to-equity
            value_color = "#dc3545"  # Dark red (very bad)
            zone = "red"
        elif value <= threshold_red:
            value_color = "#28a745"  # Dark green (good for low values)
            zone = "green"
        elif value <= threshold_yellow:
            value_color = "#ffc107"  # Dark yellow (caution)
            zone = "yellow"
        else:
            value_color = "#dc3545"  # Dark red (bad for high values)
            zone = "red"
    else:
        # Normal metrics (higher is better)
        if value <= threshold_red:
            value_color = "#dc3545"  # Dark red
            zone = "red"
        elif value <= threshold_yellow:
            value_color = "#ffc107"  # Dark yellow
            zone = "yellow"
        else:
            value_color = "#28a745"  # Dark green
            zone = "green"
    
    # Format value for display
    if format_type == "percent":
        display_value = f"{value:.1f}%"
    elif format_type == "ratio":
        display_value = f"{value:.2f}"
    elif format_type == "currency":
        display_value = f"${value:,.0f}"
    elif format_type == "currency_k":
        display_value = f"${value:.0f}K"
    elif format_type == "currency_auto":
        # Dynamic currency formatting based on value
        if value >= 10001000:
            display_value = f"${value/1000000:.2f}M"
        elif value >= 1000:
            display_value = f"${value/1000:.2f}K"
        else:
            display_value = f"${value:.0f}"
    else:
        display_value = f"{value:.1f}"
    
    # Create semicircular gauge with solid color zones and speedometer needle
    fig = go.Figure(go.Indicator(
        mode = "gauge",
        value = value,  # Use actual value for proper bar rendering
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {
            'text': f"<b>{title}</b>",
            'font': {'size': 12, 'color': '#1a202c', 'family': 'Montserrat'}
        },
        gauge = {
            'axis': {
                'range': [actual_min, actual_max],  # Use extended range
                'tickwidth': 1,
                'tickcolor': "#4a5568",
                'tickfont': {'size': 10, 'color': '#4a5568'},
                'showticklabels': True
            },
            'bar': {
                'color': '#000000',    # Black progress bar for clean look
                'thickness': 0.08,     # Thinner for cleaner appearance
                'line': {
                    'color': '#000000',
                    'width': 1
                }
            },
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e2e8f0",
            'steps': [
                # For reverse_colors (lower is better): green on left, yellow middle, red on right
                # For normal (higher is better): red on left, yellow middle, green on right
                {'range': [actual_min, adjusted_threshold_red], 'color': '#00cc44' if reverse_colors else '#ff4444'},
                {'range': [adjusted_threshold_red, adjusted_threshold_yellow], 'color': '#ffcc00'},  # Yellow in middle (caution zone)
                {'range': [adjusted_threshold_yellow, actual_max], 'color': '#ff4444' if reverse_colors else '#00cc44'}
            ],
            'shape': 'angular',
            'threshold': {
                'line': {'color': "#000000", 'width': 4},  # Black line for maximum visibility
                'thickness': 1.0,  # Full thickness
                'value': value
            }
        }
    ))
    
    # Add custom text annotation for the color-coded value (bold)
    fig.add_annotation(
        x=0.5, y=0.05,  # Position at bottom
        text=f"<b>{display_value}</b>",
        showarrow=False,
        font=dict(size=20, color=value_color, family='Montserrat'),
        xref="paper", yref="paper"
    )
    
    # Update layout for semicircular appearance
    fig.update_layout(
        height=180,
        font={'color': "#4a5568", 'family': "Montserrat", 'size': 10},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig


def create_comparison_chart(data, chart_type="bar"):
    """Create comparison charts for multiple companies"""
    # Add your comparison chart logic here
    pass

def create_trend_chart(data, metric_name):
    """Create trend charts for historical data"""
    # Add your trend chart logic here
    pass