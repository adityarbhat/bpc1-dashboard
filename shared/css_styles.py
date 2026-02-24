"""
Centralized CSS styling for BPC Dashboard
This module provides consistent styling across all pages
"""

import streamlit as st

def apply_base_styles():
    """Apply base styles - fonts, app defaults, and core layout"""
    st.markdown("""
    <style>
        /* Import Google Fonts - Montserrat for Atlas branding */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
        
        /* Force CSS priority and ensure proper loading - Multiple fallbacks */
        .stApp,
        [data-testid="stApp"],
        .css-fg4pbf,
        .css-1x8cf1d,
        .css-10trblm,
        .css-1629p8f {
            font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
            background-color: #f8f9fa;
        }
        
        /* Override Streamlit defaults - Multiple fallbacks */
        .main .block-container,
        [data-testid="stAppViewContainer"] .block-container,
        .css-k1vhr4,
        .css-18e3th9,
        .css-1d391kg .block-container,
        .css-1lcbmhc .block-container,
        .appview-container .block-container {
            padding-top: 0rem !important;
            padding-bottom: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Additional fallback for main containers */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 1rem !important;
        }
            /* Also target the view container just in case */
        [data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 0rem !important; 
        }

        /* Fix table rendering issues */
        .stMarkdown {
            width: 100% !important;
        }
        
        /* Hide Streamlit default elements - Multiple fallbacks */
        #MainMenu,
        [data-testid="MainMenu"],
        .css-9s5bis,
        .css-fblp2m {
            visibility: hidden !important;
        }
        
        footer,
        .css-1lsmgbg,
        .css-164nlkn,
        [data-testid="stFooter"] {
            visibility: hidden !important;
        }
        
        .stDeployButton,
        [data-testid="stDeployButton"],
        .css-1rs6os,
        .css-1cpxqw2 {
            display: none !important;
        }
        
        /* Hide hamburger menu */
        .css-14xtw13,
        .css-hxt7ib,
        [data-testid="collapsedControl"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def apply_layout_styles():
    """Apply layout styles - sidebar positioning, containers, responsive design"""
    st.markdown("""
    <style>
        /* Sidebar styling - Minimal padding to move everything up */
        .css-1d391kg,
        .css-1lcbmhc,
        .css-1y4p8pa,
        .css-12oz5g7,
        .css-17eq0hr,
        .css-1544g2n,
        section[data-testid="stSidebar"] .element-container,
        section[data-testid="stSidebar"] > div > div,
        .stSidebar .element-container {
            padding-top: 0.3rem !important;
            padding-bottom: 0.3rem !important;
        }
        
        section[data-testid="stSidebar"] .block-container,
        section[data-testid="stSidebar"] .main,
        .stSidebar .block-container {
            padding-top: 0.3rem !important;
            padding-bottom: 0.3rem !important;
        }
        
        section[data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] > div > div > div,
        .stSidebar > div,
        [data-testid="stSidebar"] {
            padding-top: 0.3rem !important;
        }
        
        /* Main content container */
        .main-content {
            padding: 1rem;
            background: white;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        /* Header styling */
        .header-container {
            background: white;
            padding: 1rem 2rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #0066cc;
        }
        
        .company-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #2d3748;
            margin: 0;
            text-align: center;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            
            .header-container {
                padding: 0.8rem 1rem;
            }
            
            .company-title {
                font-size: 1.5rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def apply_navigation_styles():
    """Apply navigation styles - Group/Company tabs, period selectors"""
    st.markdown("""
    <style>
        /* Main navigation container */
        .main-nav-container {
            margin: 0.5rem 0;
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }
        
        /* Top navigation tabs - consistent across all pages */
        .top-nav {
            display: flex;
            gap: 0.5rem;
            margin: 1rem 0;
            justify-content: center;
            align-items: center;
        }
        
        .nav-tab {
            padding: 0.5rem 1.2rem;
            background: #e2e8f0;
            border-radius: 6px;
            font-weight: 500;
            color: #4a5568;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .nav-tab.active {
            background: #025a9a;
            color: white;
        }
        
        .nav-tab:hover {
            background: #cbd5e0;
        }
        
        /* Period selector */
        .period-selector {
            display: flex;
            gap: 0.3rem;
            margin: 0.5rem 0;
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

def apply_button_styles():
    """Apply button styles - consistent button appearance across all pages"""
    st.markdown("""
    <style>
        /* Default button styling for general use - Multiple fallbacks */
        .stButton > button,
        [data-testid="baseButton-secondary"],
        [data-testid="baseButton-primary"],
        button[data-baseweb="button"],
        .css-1cpxqw2 button,
        .css-1erivf3 button {
            background: linear-gradient(135deg, #025a9a 0%, #0e9cd5 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 10px rgba(2, 90, 154, 0.3) !important;
            width: 100% !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 20px rgba(2, 90, 154, 0.4) !important;
            background: linear-gradient(135deg, #c2002f 0%, #025a9a 100%) !important;
        }
        
        .stButton > button:focus {
            box-shadow: 0 0 0 3px rgba(2, 90, 154, 0.5) !important;
            outline: none !important;
        }
        
        /* NAVIGATION BUTTON OVERRIDES - Higher specificity for consistency */
        div.main-nav-container .stButton > button {
            background: #e2e8f0 !important;
            color: #4a5568 !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.5rem 1.2rem !important;
            font-weight: 500 !important;
            font-family: 'Montserrat', sans-serif !important;
            transition: all 0.2s ease !important;
            margin: 0 !important;
            box-shadow: none !important;
            white-space: nowrap !important;
            min-width: auto !important;
            width: auto !important;
            font-size: 0.9rem !important;
            transform: none !important;
        }
        
        div.main-nav-container .stButton > button:hover {
            background: #cbd5e0 !important;
            transform: none !important;
            box-shadow: none !important;
        }
        
        div.nav-active .stButton > button {
            background: #025a9a !important;
            color: white !important;
            box-shadow: none !important;
            transform: none !important;
        }
        
        div.nav-active .stButton > button:hover {
            background: #025a9a !important;
            transform: none !important;
            box-shadow: none !important;
        }
        
        /* Period selector button overrides */
        div.period-selector-buttons .stButton > button {
            background: #f7fafc !important;
            color: #4a5568 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 4px !important;
            padding: 0.4rem 0.8rem !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            font-family: 'Montserrat', sans-serif !important;
            transition: all 0.2s ease !important;
            white-space: nowrap !important;
            width: auto !important;
            min-width: auto !important;
            height: auto !important;
            box-shadow: none !important;
            transform: none !important;
        }
        
        div.period-selector-buttons .stButton > button:hover {
            background: #e2e8f0 !important;
            border-color: #cbd5e0 !important;
            transform: none !important;
            box-shadow: none !important;
        }
        
        div.period-selector-buttons .period-active-btn .stButton > button {
            background: #025a9a !important;
            color: white !important;
            border: 1px solid #025a9a !important;
            box-shadow: none !important;
            transform: none !important;
        }
        
        div.period-active-btn .stButton > button:hover {
            background: #025a9a !important;
            border-color: #025a9a !important;
            transform: none !important;
            box-shadow: none !important;
        }
        
        /* Sidebar button styling - Multiple fallbacks with compact spacing */
        .css-1d391kg .stButton > button,
        .css-1lcbmhc .stButton > button,
        .css-1y4p8pa .stButton > button,
        .css-12oz5g7 .stButton > button,
        .css-17eq0hr .stButton > button,
        .css-1544g2n .stButton > button,
        section[data-testid="stSidebar"] .stButton > button,
        .stSidebar .stButton > button,
        [data-testid="stSidebar"] .stButton > button {
            background: linear-gradient(135deg, #025a9a 0%, #0e9cd5 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.35rem 0.8rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
            font-size: 0.85rem !important;
        }
        
        .css-1d391kg .stButton > button:hover,
        .css-1lcbmhc .stButton > button:hover,
        .css-1y4p8pa .stButton > button:hover,
        .css-12oz5g7 .stButton > button:hover,
        .css-17eq0hr .stButton > button:hover,
        .css-1544g2n .stButton > button:hover,
        section[data-testid="stSidebar"] .stButton > button:hover,
        .stSidebar .stButton > button:hover,
        [data-testid="stSidebar"] .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(2, 90, 154, 0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)

def apply_header_styles():
    """Apply header and top action button styles"""
    st.markdown("""
    <style>
        /* Top navigation header */
        .nav-header-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            margin: 0 0 0.5rem 0;
            padding: 0;
        }
        
        .nav-header-buttons .stButton {
            flex: 0 0 auto;
            margin: 0 !important;
        }
        
        .nav-header-buttons .stButton > button {
            background: linear-gradient(135deg, #025a9a 0%, #0e9cd5 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 6px 12px !important;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 4px rgba(2, 90, 154, 0.2) !important;
            width: auto !important;
            min-width: auto !important;
            height: 35px !important;
        }
        
        .nav-header-buttons .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(2, 90, 154, 0.3) !important;
            background: linear-gradient(135deg, #0e9cd5 0%, #025a9a 100%) !important;
        }
        
        /* Action buttons */
        .action-buttons {
            background: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
        }
        
        .action-btn {
            padding: 0.4rem 0.8rem;
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            font-size: 0.8rem;
            cursor: pointer;
            color: #4a5568;
        }
        
        .action-btn:hover {
            background: #e2e8f0;
        }
        
        /* Welcome message and main header */
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1a202c;
            text-align: center;
            margin-bottom: 1rem;
            letter-spacing: -0.025em;
        }
        
        .welcome-message {
            font-size: 1.1rem;
            color: #025a9a;
            text-align: center;
            margin: 0.3rem 0 0.5rem 0;
            font-weight: 600;
            background: linear-gradient(135deg, #025a9a 0%, #0e9cd5 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .instructions {
            background: linear-gradient(135deg, #c2002f 0%, #025a9a 100%);
            color: white;
            padding: 0.6rem;
            border-radius: 8px;
            margin: 0.3rem 0 0.5rem 0;
            border: none;
            box-shadow: 0 2px 8px rgba(194, 0, 47, 0.2);
        }
        
        .instructions ul {
            margin: 0;
            padding-left: 1rem;
        }
        
        .instructions li {
            margin: 0.2rem 0;
            font-weight: 500;
            font-size: 0.8rem;
        }
    </style>
    """, unsafe_allow_html=True)

def apply_table_styles():
    """Apply table and rankings styles"""
    st.markdown("""
    <style>
        /* Visible scrollbars for all group table containers */
        .group-ratio-table-container,
        .balance-sheet-table-container,
        .income-statement-table-container,
        .cash-flow-table-container,
        .labor-cost-table-container,
        .value-trends-table-container {
            overflow-x: auto !important;
            overflow-y: auto !important;
        }
        .group-ratio-table-container::-webkit-scrollbar,
        .balance-sheet-table-container::-webkit-scrollbar,
        .income-statement-table-container::-webkit-scrollbar,
        .cash-flow-table-container::-webkit-scrollbar,
        .labor-cost-table-container::-webkit-scrollbar,
        .value-trends-table-container::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        .group-ratio-table-container::-webkit-scrollbar-track,
        .balance-sheet-table-container::-webkit-scrollbar-track,
        .income-statement-table-container::-webkit-scrollbar-track,
        .cash-flow-table-container::-webkit-scrollbar-track,
        .labor-cost-table-container::-webkit-scrollbar-track,
        .value-trends-table-container::-webkit-scrollbar-track {
            background: #e2e8f0;
            border-radius: 5px;
        }
        .group-ratio-table-container::-webkit-scrollbar-thumb,
        .balance-sheet-table-container::-webkit-scrollbar-thumb,
        .income-statement-table-container::-webkit-scrollbar-thumb,
        .cash-flow-table-container::-webkit-scrollbar-thumb,
        .labor-cost-table-container::-webkit-scrollbar-thumb,
        .value-trends-table-container::-webkit-scrollbar-thumb {
            background: #a0aec0;
            border-radius: 5px;
        }
        .group-ratio-table-container::-webkit-scrollbar-thumb:hover,
        .balance-sheet-table-container::-webkit-scrollbar-thumb:hover,
        .income-statement-table-container::-webkit-scrollbar-thumb:hover,
        .cash-flow-table-container::-webkit-scrollbar-thumb:hover,
        .labor-cost-table-container::-webkit-scrollbar-thumb:hover,
        .value-trends-table-container::-webkit-scrollbar-thumb:hover {
            background: #718096;
        }
        .group-ratio-table-container::-webkit-scrollbar-corner,
        .balance-sheet-table-container::-webkit-scrollbar-corner,
        .income-statement-table-container::-webkit-scrollbar-corner,
        .cash-flow-table-container::-webkit-scrollbar-corner,
        .labor-cost-table-container::-webkit-scrollbar-corner,
        .value-trends-table-container::-webkit-scrollbar-corner {
            background: #e2e8f0;
        }

        /* Rankings section styling */
        .rankings-section {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 6px 20px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
        }
        
        .rankings-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #2d3748;
            text-align: center;
            margin-bottom: 1.5rem;
            position: relative;
        }
        
        .rankings-title::after {
            content: '';
            display: block;
            width: 60px;
            height: 3px;
            background: linear-gradient(135deg, #025a9a 0%, #0e9cd5 100%);
            margin: 0.3rem auto;
            border-radius: 2px;
        }
        
        /* Enhanced table styling */
        .rankings-table {
            background: white !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08) !important;
            border: 2px solid #e2e8f0 !important;
            margin: 1rem auto !important;
            width: 100% !important;
            max-width: 900px !important;
            display: block !important;
        }
        
        .table-container {
            width: 100% !important;
            max-width: 900px !important;
            margin: 0 auto !important;
            display: block !important;
        }
        
        .table-header-row {
            background: linear-gradient(135deg, #025a9a 0%, #0e9cd5 100%) !important;
            color: white !important;
            padding: 0.7rem !important;
            display: flex !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            width: 100% !important;
        }
        
        .table-data-row {
            display: flex !important;
            padding: 0.7rem !important;
            border-bottom: 1px solid #e2e8f0 !important;
            transition: background-color 0.2s ease !important;
            width: 100% !important;
        }
        
        .table-data-row:hover {
            background-color: #f7fafc !important;
        }
        
        .table-data-row:last-child {
            border-bottom: none !important;
        }
        
        .table-cell {
            flex: 1;
            padding: 0 0.7rem;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .table-cell.rank {
            flex: 0.8;
            justify-content: center;
            font-weight: 700;
            font-size: 1.1rem;
            color: #025a9a;
        }
        
        .table-cell.company {
            flex: 2.5;
            font-weight: 500;
            color: #2d3748;
        }
        
        .table-cell.score {
            flex: 1.2;
            justify-content: center;
            font-weight: 600;
            color: #38a169;
        }
        
        /* Ratios section styling */
        .ratios-section {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .section-title {
            font-size: 1.4rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

def apply_sidebar_styles():
    """Apply sidebar-specific styles"""
    st.markdown("""
    <style>
        /* Sidebar header */
        .sidebar-header {
            background: linear-gradient(135deg, #025a9a 0%, #0e9cd5 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
            font-weight: 600;
        }
        
        .sidebar-section {
            margin: 0.5rem 0;
        }
        
        .sidebar-section h3 {
            color: #2d3748;
            font-size: 0.9rem;
            margin-bottom: 0.3rem;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 0.2rem;
        }
        
        /* Compact spacing for sidebar markdown headers */
        section[data-testid="stSidebar"] h3,
        .stSidebar h3,
        [data-testid="stSidebar"] h3 {
            margin-top: 0.3rem !important;
            margin-bottom: 0.2rem !important;
            font-size: 0.85rem !important;
            color: #2d3748 !important;
        }
        
        /* Enhanced company filter header */
        .company-filter-header {
            background: linear-gradient(135deg, #025a9a 0%, #0e9cd5 100%);
            color: white;
            padding: 0.6rem 1rem;
            border-radius: 6px;
            margin-bottom: 0.5rem;
            text-align: center;
            font-weight: 600;
            font-size: 0.9rem;
            box-shadow: 0 2px 8px rgba(2, 90, 154, 0.2);
        }
    </style>
    """, unsafe_allow_html=True)

def apply_all_styles():
    """Apply all styles in the correct order"""
    apply_base_styles()
    apply_layout_styles()
    apply_navigation_styles()
    apply_button_styles()
    apply_header_styles()
    apply_table_styles()
    apply_sidebar_styles()