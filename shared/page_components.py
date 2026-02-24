"""
Centralized Page Components for BPC Dashboard
Provides consistent header components across all pages
"""

import streamlit as st


def get_period_display_text():
    """Get formatted period text for display in headers"""
    if st.session_state.get('period') == 'june_end':
        return "Mid Year"
    return "Year End"


def create_page_header(page_title=None, subtitle=None, show_period_selector=True, banner_text="BPC 1 Financial Dashboard"):
    """
    Create standardized page header with consistent spacing

    Args:
        page_title (str): Main page title (H1)
        subtitle (str): Optional subtitle text
        show_period_selector (bool): Whether to show period selector
        banner_text (str): Text to display in red banner
    """
    # Red banner with custom text
    create_red_banner(banner_text)
    
    # Period selector (if requested)
    if show_period_selector:
        create_period_selector()
    
    # Main title (if provided)
    if page_title:
        st.markdown(f'<h1 style="color: #1a202c; text-align: center; font-weight: 800; font-size: 2.5rem; margin: 0.2rem 0 0.5rem 0;">{page_title}</h1>', unsafe_allow_html=True)
    
    # Subtitle (if provided)
    if subtitle:
        st.markdown(f"""
        <div class="welcome-message" style="margin: 0.1rem 0 0.3rem 0; font-size: 2.0rem; font-weight: 800; color: #f56500; text-align: center;">
            {subtitle}
        </div>
        """, unsafe_allow_html=True)


def create_red_banner(banner_text="BPC 1 Financial Dashboard"):
    """
    Create the red banner with customizable title

    Args:
        banner_text (str): Text to display in banner (default: "BPC 1 Financial Dashboard")
    """
    # Add CSS for the red banner
    st.markdown("""
    <style>
        .header-banner {
            background: linear-gradient(135deg, #c2002f 0%, #a50026 100%);
            color: white;
            text-align: center;
            padding: 1rem 0;
            margin: -2rem -1rem 0.5rem -1rem;
            width: calc(100% + 2rem);
            position: relative;
            left: -1rem;
            box-shadow: 0 2px 4px rgba(194, 0, 47, 0.3);
        }

        .banner-title {
            font-size: 1.8rem;
            font-weight: 700;
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            letter-spacing: 0.5px;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }

        @media (max-width: 768px) {
            .banner-title {
                font-size: 1.4rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Create the red banner with custom text
    st.markdown(f"""
    <div class="header-banner">
        <div class="banner-title">{banner_text}</div>
    </div>
    """, unsafe_allow_html=True)


def create_period_selector():
    """Create period selector with consistent spacing"""
    # Initialize period if not exists
    if 'period' not in st.session_state:
        st.session_state.period = 'year_end'
    
    # Add CSS for period selector
    st.markdown("""
    <style>
        .period-selector {
            display: flex;
            gap: 0.3rem;
            margin: -0.3rem 0 0.3rem 0;
            justify-content: flex-start;
        }
        
        .period-btn {
            padding: 0.4rem 0.8rem;
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            font-size: 0.9rem;
            cursor: pointer;
            color: #4a5568;
            font-weight: 500;
            font-family: 'Montserrat', sans-serif;
            transition: all 0.2s ease;
        }
        
        .period-btn.active {
            background: #025a9a;
            color: white;
            border-color: #025a9a;
        }
        
        .period-btn:hover {
            background: #e2e8f0;
            border-color: #cbd5e0;
        }
        
        .period-btn.active:hover {
            background: #025a9a;
            border-color: #025a9a;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create period selector using HTML divs - display only
    active_year = "active" if st.session_state.period == 'year_end' else ""
    active_june = "active" if st.session_state.period == 'june_end' else ""

    st.markdown(f"""
    <div class="period-selector">
        <div class="period-btn {active_year}">Year End</div>
        <div class="period-btn {active_june}">Mid Year</div>
    </div>
    """, unsafe_allow_html=True)


def sort_companies_by_rank(companies_list, period):
    """
    Sort companies by their overall group rank (rank 1 on the left, rank 10 on the right).

    Args:
        companies_list: List of company names to sort
        period: Period filter for rankings (e.g., "2024 Annual" or "June 2024")

    Returns:
        List of companies sorted by rank (best performer first/leftmost)
    """
    from pages.group_pages.group_ratios import calculate_group_rankings

    # Get rankings
    rankings_data = calculate_group_rankings(period)

    if not rankings_data or 'rankings' not in rankings_data:
        # Fallback to alphabetical if rankings unavailable
        return sorted(companies_list)

    rankings = rankings_data['rankings']
    scores = rankings_data['scores']

    # Sort by score ascending (lowest score = best rank = leftmost)
    sorted_companies = sorted(
        companies_list,
        key=lambda company: scores.get(company, 999999),  # Companies without scores go to the right
    )

    return sorted_companies