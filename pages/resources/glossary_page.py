#!/usr/bin/env python3
"""
Financial Glossary Page
Atlas BPC 2 Financial Dashboard - Comprehensive financial terms, definitions, and formulas
"""

import streamlit as st
from dotenv import load_dotenv

# Import from shared modules
from shared.page_components import create_page_header
from shared.auth_utils import require_auth

# Load environment variables from .env file for local development
load_dotenv()

# NOTE: Page configuration is handled by financial_dashboard.py
# Do not call st.set_page_config() here as it can only be called once per app


def display_term_card(term, definition, formula=None, example=None, range_key=None):
    """Display a styled term card with optional formula and range key"""

    # Build the card HTML
    card_html = f"""
    <div style="background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                border-left: 4px solid #025a9a;
                border-radius: 8px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="color: #025a9a; font-family: 'Montserrat', sans-serif; margin-top: 0; font-size: 1.3rem;">
            {term}
        </h3>
    """

    # Add formula if provided
    if formula:
        card_html += f"""
        <div style="background-color: #e6f2ff;
                    border-radius: 5px;
                    padding: 0.8rem;
                    margin: 0.8rem 0;
                    font-family: 'Courier New', monospace;
                    font-size: 1.0rem;">
            <strong>Formula:</strong> {formula}
        </div>
        """

    # Add definition
    card_html += f"""
        <p style="color: #1a202c;
                  font-family: 'Montserrat', sans-serif;
                  line-height: 1.6;
                  font-size: 1.0rem;
                  margin: 0.8rem 0;">
            {definition}
        </p>
    """

    # Add example if provided
    if example:
        card_html += f"""
        <div style="background-color: #f0f8ff;
                    border-left: 3px solid #0e9cd5;
                    padding: 0.8rem;
                    margin: 0.8rem 0;
                    font-size: 0.95rem;">
            <strong>Example:</strong> {example}
        </div>
        """

    # Add range key if provided
    if range_key:
        card_html += f"""
        <div style="background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 0.8rem;
                    margin: 0.8rem 0;">
            <strong style="color: #025a9a;">Performance Ranges:</strong>
            <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
        """
        for key, value in range_key.items():
            color = '#2e7d32' if 'Great' in key else ('#f57c00' if 'Caution' in key else '#d32f2f')
            card_html += f'<li style="color: {color}; margin: 0.3rem 0;"><strong>{key}:</strong> {value}</li>'
        card_html += """
            </ul>
        </div>
        """

    card_html += "</div>"

    st.html(card_html)


def create_glossary_page():
    """Create the financial glossary page with tabs for different categories"""

    # Require authentication
    require_auth()

    # Use centralized page header
    create_page_header(
        page_title="📚 Financial Glossary",
        subtitle="Comprehensive guide to financial terms, definitions, and ratio formulas used in this dashboard",
        show_period_selector=False
    )

    # Add styling for tabs
    st.markdown("""
    <style>
        /* Make tabs larger and more readable for seniors */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
            padding: 1rem 1.5rem !important;
            font-family: 'Montserrat', sans-serif !important;
        }

        .stTabs [aria-selected="true"] {
            font-weight: 700 !important;
            background-color: #e6f2ff !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)

    # Create tabs for different categories
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Balance Sheet",
        "📈 Income Statement",
        "💸 Cash Flow & Other",
        "📋 Chart of Accounts"
    ])

    # Tab 1: Balance Sheet Terms & Ratios
    with tab1:
        st.markdown("### Balance Sheet Terms & Ratios")
        st.markdown("Understanding balance sheet line items and key financial health ratios.")

        # Balance Sheet Ratios
        st.markdown("#### 🎯 Key Balance Sheet Ratios")

        display_term_card(
            term="Current Ratio (Liquidity)",
            definition="A measure of liquidity and the company's ability to pay its bills. It indicates how many dollars of current assets are available to pay each dollar of current liabilities.",
            formula="Current Assets ÷ Current Liabilities",
            example="If Current Assets = $2,000,000 and Current Liabilities = $800,000, then Current Ratio = 2.5",
            range_key={
                "Great": "≥ 2.3",
                "Caution": "1.5 - 2.2",
                "Improve": "< 1.5"
            }
        )

        display_term_card(
            term="Debt-to-Equity Ratio (Safety)",
            definition="A measure of the company's safety and ability to survive adversity. It shows how much debt the company has relative to its equity. Lower is better for this ratio.",
            formula="Total Liabilities ÷ Equity (Net Worth)",
            example="If Total Liabilities = $1,500,000 and Equity = $1,000,000, then Debt-to-Equity = 1.5",
            range_key={
                "Great": "≤ 1.1",
                "Caution": "1.2 - 1.7",
                "Improve": "> 1.7"
            }
        )

        display_term_card(
            term="Working Capital % of Total Assets",
            definition="Represents the percentage of total assets that are working capital (current assets minus current liabilities). Higher percentages indicate better short-term financial health.",
            formula="(Current Assets - Current Liabilities) ÷ Total Assets × 100",
            example="If Current Assets = $2M, Current Liabilities = $800K, Total Assets = $4M, then Working Capital % = 30%",
            range_key={
                "Great": "> 35%",
                "Caution": "20% - 35%",
                "Improve": "< 20%"
            }
        )

        display_term_card(
            term="Survival Score",
            definition="A composite metric that evaluates overall financial health based on multiple factors including liquidity, profitability, and leverage. Higher scores indicate stronger financial position.",
            formula="(Working Capital ÷ Total Assets × 6.56) + (Equity ÷ Total Assets × 3.26) + (Profit ÷ Total Assets × 6.72) + (Equity ÷ Debt × 1.05)",
            example="If WC=$1M, Equity=$2M, Profit=$300K, Debt=$1.5M, Total Assets=$4M, then Survival Score = (1/4 × 6.56) + (2/4 × 3.26) + (0.3/4 × 6.72) + (2/1.5 × 1.05) = 1.64 + 1.63 + 0.50 + 1.40 = 5.17",
            range_key={
                "Great": "> 3.0",
                "Caution": "2.0 - 3.0",
                "Improve": "< 2.0"
            }
        )

        display_term_card(
            term="Sales-to-Assets Ratio",
            definition="Measures how efficiently a company uses its assets to generate revenue. Higher values indicate better asset utilization.",
            formula="Total Revenue ÷ Total Assets"
        )

        # Balance Sheet Terms
        st.markdown("#### 📖 Balance Sheet Terms")

        balance_sheet_terms = {
            "Assets": "Anything owned by an individual or a business. Assets may consist of specific property or claims against others. Assets are reflected on the balance sheet at the lower of cost or current value.",
            "Current Assets": "Assets that are reasonably expected to be converted to cash or consumed during the next twelve months. Includes cash, accounts receivable, inventories, and prepaid expenses.",
            "Fixed Assets": "Assets of a noncurrent nature which will not normally be converted into cash during the next twelve months. Examples include furniture and fixtures, land, buildings, and equipment.",
            "Liabilities": "Amounts owed to creditors by a person or a business.",
            "Current Liabilities": "Liabilities that are due within twelve months of the balance sheet date. Includes bank line of credit, accrued liabilities, accounts payable, and current portion of long-term debt.",
            "Long-term Debt": "Liabilities that are due more than one year from the date of the balance sheet.",
            "Equity": "The net worth or ownership interest in a company. It is the difference between the assets and the liabilities. Also referred to as Capital or Net Worth.",
            "Working Capital": "Current assets minus current liabilities. All financially stable companies need adequate working capital to make payments when due.",
            "Accounts Receivable": "A current asset representing money owed for merchandise or services sold on open account.",
            "Accounts Payable": "A current liability representing the amount owed to trade creditors for merchandise or services purchased on open account.",
            "Accumulated Depreciation": "The total of all depreciation taken on a fixed asset since its purchase. Also referred to as allowance or reserve for depreciation.",
            "Retained Earnings": "Earnings of the business that have been retained in the business and not paid out to stockholders."
        }

        for term, definition in balance_sheet_terms.items():
            display_term_card(term=term, definition=definition)

    # Tab 2: Income Statement Terms & Ratios
    with tab2:
        st.markdown("### Income Statement Terms & Ratios")
        st.markdown("Understanding revenue, expenses, and profitability metrics.")

        # Income Statement Ratios
        st.markdown("#### 🎯 Key Income Statement Ratios")

        display_term_card(
            term="Gross Profit Margin (GPM)",
            definition="The gross profit expressed as a percentage of revenue. It shows how much profit remains after deducting the cost of goods sold, before paying overhead expenses.",
            formula="(Revenue - Cost of Goods Sold) ÷ Revenue × 100",
            example="If Revenue = $1,000,000 and COGS = $650,000, then GPM = 35%",
            range_key={
                "Great": "> 25%",
                "Caution": "20% - 25%",
                "Improve": "< 20%"
            }
        )

        display_term_card(
            term="Operating Profit Margin (OPM)",
            definition="The operating profit expressed as a percentage of revenue. It shows the profit generated from operations after deducting both direct costs and operating expenses.",
            formula="Operating Profit ÷ Revenue × 100",
            example="If Operating Profit = $50,000 and Revenue = $1,000,000, then OPM = 5%",
            range_key={
                "Great": "> 6.5%",
                "Caution": "4% - 6.5%",
                "Improve": "< 4%"
            }
        )

        display_term_card(
            term="Net Profit Margin (NPM)",
            definition="The net profit (before tax) expressed as a percentage of revenue. It represents the bottom line profitability after all expenses.",
            formula="Net Profit ÷ Revenue × 100",
            example="If Net Profit = $30,000 and Revenue = $1,000,000, then NPM = 3%"
        )

        display_term_card(
            term="EBITDA/Revenue",
            definition="Earnings Before Interest, Taxes, Depreciation, and Amortization as a percentage of revenue. Measures operating performance independent of capital structure and tax environment.",
            formula="EBITDA ÷ Revenue × 100",
            range_key={
                "Great": "> 5%",
                "Caution": "3% - 5%",
                "Improve": "< 3%"
            }
        )

        display_term_card(
            term="Revenue Per Admin Employee",
            definition="Measures productivity by showing how much revenue is generated per administrative employee. Higher values indicate better efficiency.",
            formula="Total Revenue ÷ Number of Administrative Employees",
            example="If Revenue = $5,000,000 and Admin Employees = 10, then Revenue per Admin Employee = $500K",
            range_key={
                "Great": "> $580K",
                "Caution": "$325K - $580K",
                "Improve": "< $325K"
            }
        )

        # Income Statement Terms
        st.markdown("#### 📖 Income Statement Terms")

        income_statement_terms = {
            "Revenue": "Synonymous with sales. Usually used in a service business. Total income generated from business operations.",
            "Cost of Goods Sold (COGS)": "Expenses related directly to the production of revenue. Includes raw materials, direct labor, freight, and factory overhead for manufacturing; merchandise costs for wholesalers/retailers; direct labor and materials for service companies.",
            "Gross Profit": "The difference between revenue and the cost of goods sold. This is the profit available to pay overhead expenses.",
            "Operating Expenses": "Expenses pertaining to the normal operation of the business. Also referred to as overhead, indirect expenses, or G&A (General and Administrative).",
            "Operating Profit": "The difference between gross profit and overhead/indirect expenses. This shows the profit generated from operations before interest and taxes.",
            "Net Profit": "The excess of total income over total expenses for a fiscal period, before income taxes.",
            "EBITDA": "Earnings Before Interest, Taxes, Depreciation, and Amortization. A measure of operating performance.",
            "Direct Wages": "Salaries, wages, and bonuses paid to operations personnel including drivers, helpers, packers, and warehousemen. Excludes admin, office, dispatch, and sales.",
            "Depreciation Expense": "The amount of expense charged against earnings to write off the cost of fixed assets over their useful lives. A non-cash charge.",
            "Administrative Expenses": "Also called G&A (General & Administrative), operating expenses, or overhead. Typically includes utilities, advertising, legal, accounting, travel, entertainment, office expenses, professional fees, taxes and licenses.",
            "Contribution Margin": "The difference between revenue and variable expenses. Shows the amount available to pay fixed expenses.",
            "Break-even Point": "The point at which revenue and expenses are equal, yielding zero net profit.",
            "Variable Expenses": "Expenses that vary directly with sales or revenue volume. Examples include commissions, direct wages, supplies, and bad debts.",
            "Fixed Expenses": "Expenses that do not vary directly with sales or revenue. Examples include rent, depreciation, lease expense, office expenses, legal, and accounting."
        }

        for term, definition in income_statement_terms.items():
            display_term_card(term=term, definition=definition)

    # Tab 3: Cash Flow & Other Terms
    with tab3:
        st.markdown("### Cash Flow & Other Financial Terms")
        st.markdown("Understanding cash flow metrics and other important financial concepts.")

        # Cash Flow Ratios
        st.markdown("#### 🎯 Cash Flow Ratios")

        display_term_card(
            term="Days Sales Outstanding (DSO)",
            definition="Represents the length of time it typically takes to collect outstanding accounts receivable. Lower is better - indicates faster collection.",
            formula="(Accounts Receivable ÷ Revenue) × 365",
            example="If AR = $200,000 and Annual Revenue = $2,000,000, then DSO = 36.5 days",
            range_key={
                "Great": "< 40 days",
                "Caution": "40 - 60 days",
                "Improve": "> 60 days"
            }
        )

        display_term_card(
            term="Operating Cash Flow (OCF) / Revenue",
            definition="The cash flow generated from day-to-day operations as a percentage of revenue. Positive values indicate the company generates cash from operations.",
            formula="Operating Cash Flow ÷ Revenue × 100",
            range_key={
                "Great": "> 0.5%",
                "Caution": "-0.5% to 0.5%",
                "Improve": "< -0.5%"
            }
        )

        display_term_card(
            term="Financing Cash Flow (FCF) / Revenue",
            definition="Cash flows related to debt and equity financing activities as a percentage of revenue.",
            formula="Financing Cash Flow ÷ Revenue × 100"
        )

        display_term_card(
            term="Net Cash Flow (NCF) / Revenue",
            definition="The total change in cash position as a percentage of revenue. Combines operating and financing cash flows.",
            formula="Net Cash Flow ÷ Revenue × 100"
        )

        # Detailed Cash Flow Calculation Methodology
        st.markdown("#### 🧮 Cash Flow Calculation Methodology")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-radius: 10px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                    border: 1px solid #dee2e6;">
            <p style="color: #495057; font-size: 1rem; margin-bottom: 1rem;">
                The following cash flow metrics are <strong>automatically calculated</strong> from Balance Sheet and
                Income Statement data using year-over-year changes. These calculations ensure consistency and
                accuracy across all dashboard views.
            </p>
        </div>
        """, unsafe_allow_html=True)

        display_term_card(
            term="Operating Cash Flow (OCF) - Detailed Formula",
            definition="""Operating Cash Flow measures the cash generated from core business operations.
            It starts with net profit and adjusts for changes in working capital and fixed assets between
            the current and prior year.""",
            formula="""OCF = Net Profit + Δ Current Assets + Δ Current Liabilities + Δ Net Fixed Assets + Δ Non-Current Assets""",
            example="""<strong>Component Calculations:</strong><br><br>
            <table style="width:100%; border-collapse: collapse; font-size: 0.95rem;">
                <tr style="background-color: #e6f2ff;">
                    <td style="padding: 8px; border: 1px solid #ccc;"><strong>Net Profit</strong></td>
                    <td style="padding: 8px; border: 1px solid #ccc;">Profit Before Tax (from Income Statement)</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;"><strong>Δ Current Assets</strong></td>
                    <td style="padding: 8px; border: 1px solid #ccc;">(Prior Year TCA - Cash) − (Current Year TCA - Cash - Notes Payable Owners)</td>
                </tr>
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 8px; border: 1px solid #ccc;"><strong>Δ Current Liabilities</strong></td>
                    <td style="padding: 8px; border: 1px solid #ccc;">(Current TCL - CPLTD - Notes Payable Bank) − (Prior TCL - CPLTD - NPB - NP Owners)</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;"><strong>Δ Net Fixed Assets</strong></td>
                    <td style="padding: 8px; border: 1px solid #ccc;">Prior Year Net Fixed Assets − Current Year Net Fixed Assets</td>
                </tr>
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 8px; border: 1px solid #ccc;"><strong>Δ Non-Current Assets</strong></td>
                    <td style="padding: 8px; border: 1px solid #ccc;">(Prior Other Assets + Inter-Co Recv) − (Current Other Assets + Inter-Co Recv)</td>
                </tr>
            </table>"""
        )

        display_term_card(
            term="Financing Cash Flow (FCF) - Detailed Formula",
            definition="""Financing Cash Flow measures cash flows from debt and equity activities.
            It captures changes in bank debt, owner debt, other liabilities, and equity adjustments.""",
            formula="""FCF = Δ Bank Debt + Δ Owner Debt + Δ Non-Current Liabilities + Equity Adjustment""",
            example="""<strong>Component Calculations:</strong><br><br>
            <table style="width:100%; border-collapse: collapse; font-size: 0.95rem;">
                <tr style="background-color: #e6f2ff;">
                    <td style="padding: 8px; border: 1px solid #ccc;"><strong>Δ Bank Debt</strong></td>
                    <td style="padding: 8px; border: 1px solid #ccc;">(Current NPB + CPLTD + LTD) − (Prior NPB + CPLTD + LTD)</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;"><strong>Δ Owner Debt</strong></td>
                    <td style="padding: 8px; border: 1px solid #ccc;">(Current NP Owners + NP Owners LT) − (Prior NP Owners + NP Owners LT)</td>
                </tr>
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 8px; border: 1px solid #ccc;"><strong>Δ Non-Current Liabilities</strong></td>
                    <td style="padding: 8px; border: 1px solid #ccc;">(Current Inter-Co Debt + Other LT Liab) − (Prior Inter-Co Debt + Other LT Liab)</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ccc;"><strong>Equity Adjustment</strong></td>
                    <td style="padding: 8px; border: 1px solid #ccc;">(Current Owners Equity − Prior Owners Equity) − Net Profit</td>
                </tr>
            </table>"""
        )

        display_term_card(
            term="Net Cash Flow (NCF) - Detailed Formula",
            definition="""Net Cash Flow represents the total change in the company's cash position
            for the period. It combines both operating and financing activities.""",
            formula="""NCF = Operating Cash Flow (OCF) + Financing Cash Flow (FCF)""",
            example="""<strong>Example:</strong><br>
            If OCF = $150,000 and FCF = -$80,000, then NCF = $70,000<br><br>
            <strong>Revenue Ratio:</strong><br>
            If Total Revenue = $2,000,000, then NCF/Revenue = 70,000 ÷ 2,000,000 = 3.5%"""
        )

        st.markdown("""
        <div style="background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    border-radius: 5px;
                    padding: 1rem;
                    margin: 1rem 0;">
            <p style="font-size: 0.95rem; color: #856404; margin: 0;">
                <strong>📝 Note:</strong> These calculations require data from both the current year
                and prior year to compute year-over-year changes. If prior year data is unavailable,
                the cash flow ratios cannot be calculated.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background-color: #e8f5e9;
                    border-left: 4px solid #4caf50;
                    border-radius: 5px;
                    padding: 1rem;
                    margin: 1rem 0;">
            <p style="font-size: 0.95rem; color: #2e7d32; margin: 0;">
                <strong>💡 Abbreviations Used:</strong><br>
                TCA = Total Current Assets | TCL = Total Current Liabilities | CPLTD = Current Portion Long Term Debt<br>
                NPB = Notes Payable Bank | NP Owners = Notes Payable Owners | LTD = Long Term Debt<br>
                Inter-Co = Inter-Company | LT = Long Term | Recv = Receivable | Liab = Liabilities
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Cash Flow & Other Terms
        st.markdown("#### 📖 Cash Flow & Other Terms")

        other_terms = {
            "Cash Flow": "May have different meanings depending on context. Bankers usually define it as net profit plus all noncash expenses (depreciation and amortization). Can also be the difference between cash receipts and disbursements over a specified period.",
            "Operating Cash Flow": "The cash flow the company generates from its day-to-day operations.",
            "Financing Cash Flow": "Cash flows from debt and equity financing activities.",
            "Accrual-basis Accounting": "The practice of recording revenue when earned and expenses when incurred, even though cash may not be received or paid until later.",
            "Cash-basis Accounting": "The practice of recording income and expenses only when cash is received or paid out.",
            "Line of Credit": "An agreement whereby a bank agrees to lend funds up to an agreed maximum amount. Typically used for seasonal needs to finance inventory and/or accounts receivable.",
            "Liquidity": "A term describing a firm's ability to meet its current obligations. Measured by the current ratio.",
            "Collateral": "Assets that secure a loan.",
            "Accounts Payable Period": "Expressed in days, represents the length of time it typically takes to pay trade creditors.",
            "Budget": "An itemized listing of estimated revenue and expenses for a given period.",
            "Capital": "The amount of money invested in the business by shareholders. Consists of initial stock investment and retained earnings. Also referred to as equity or net worth.",
            "Comprehensive Financial Plan": "Comprised of historical review and 1-3 year projection of income statement, balance sheet, cash flow, and financial ratios.",
            "Corporation": "A type of business organization chartered by a state and given legal rights as a separate entity.",
            "Dividend": "That portion of a corporation's earnings paid to stockholders and not retained in the business.",
            "Financial Gap": "The amount of funding the business cannot generate internally to purchase required assets. Must be made up with debt or equity.",
            "Goodwill": "An intangible asset created when the purchase price of a company exceeds the fair market value of total assets.",
            "Markup": "The difference between cost and selling prices of merchandise, expressed as a percentage of cost.",
            "Net Present Value (NPV)": "The present value of future returns minus the present value of future payments.",
            "Return on Assets (ROA)": "The ratio of net profit (before taxes) to total assets. Formula: Net Profit ÷ Total Assets",
            "Return on Equity (ROE)": "The ratio of net profit (before taxes) to equity. Also called ROI. Formula: Net Profit ÷ Equity",
            "Trend Analysis": "The process of measuring financial data over a given period to note significant changes in performance from period to period.",
            "Secured Loan": "A loan secured by some sort of collateral, as opposed to an unsecured loan."
        }

        for term, definition in other_terms.items():
            display_term_card(term=term, definition=definition)

    # Tab 4: Chart of Accounts
    with tab4:
        st.markdown("### Chart of Accounts Reference")
        st.markdown("Standard account categories and descriptions used in financial reporting.")

        st.markdown("#### 📊 Balance Sheet Accounts")

        with st.expander("**Current Assets**", expanded=True):
            st.markdown("""
            - **Cash and Cash Equivalents**: All cash and money market type investments
            - **Trade Accounts Receivable**: Receivables generated from customers in the course of business
            - **Receivables**: Amount owed by Van Line (if positive) or owed to Van Line (if negative)
            - **Other Receivables**: Amounts owed by drivers, employees, etc.
            - **Prepaid Expenses**: Any prepaid expenses
            - **Related Company Receivables**: All receivables owing from related companies
            - **Owner Receivables**: All receivables owing from owners
            - **Other Current Assets**: Packing supplies, investments not included in cash, etc.
            """)

        with st.expander("**Fixed Assets**"):
            st.markdown("""
            - **Gross Fixed Assets**: All equipment, land, buildings, leasehold improvements, furniture and fixtures
            - **Accumulated Depreciation**: All accumulated depreciation and amortization (enter as negative number)
            - **Net Fixed Assets**: Gross Fixed Assets minus Accumulated Depreciation
            """)

        with st.expander("**Other Assets**"):
            st.markdown("""
            - **Inter Company Receivables**: All amounts owed by a related company
            - **Other Assets**: Hauling authorities, cash value life insurance, investment in other companies, condos, boats, long term owner receivables, etc.
            """)

        with st.expander("**Current Liabilities**"):
            st.markdown("""
            - **Notes Payable - Bank**: Bank revolving line of credit outstanding
            - **Trade Accounts Payable**: Accounts payable to vendors, suppliers, other agents, etc.
            - **Accrued Expenses**: Salary, vacation pay, interest, etc.
            - **Current Portion LTD**: Current portion of interest bearing long term debt
            - **Inter Company Payable**: All amounts owed to a related company
            - **Other Current Liabilities**: Deferred taxes, income tax payable, etc.
            """)

        with st.expander("**Long-Term Liabilities**"):
            st.markdown("""
            - **Long-Term Debt**: All interest bearing non-owner debt and non inter-company debt
            - **Notes Payable to Owners - LT**: Amounts due to owners - long term
            - **Inter Company Debt**: All amounts owed to a related company
            - **Other LT Liabilities**: Life insurance loans, etc.
            """)

        with st.expander("**Equity**"):
            st.markdown("""
            - **Owners' Equity**: Assets minus liabilities (Net Worth)
            """)

        st.markdown("#### 📈 Income Statement Accounts")

        with st.expander("**Revenue Categories**", expanded=True):
            st.markdown("""
            - **Intra State HHG**: Transportation revenues generated under an intrastate tariff
            - **Local HHG**: Revenues defined by an intrastate tariff as local
            - **Inter State HHG**: Transportation revenues generated under an interstate tariff
            - **Office & Industrial**: All local commercial revenue except HHG
            - **Warehouse (Non-commercial)**: All permanent and SIT revenue
            - **International**: All international revenue including pickup, packing, crating, delivery
            - **Packing & Unpacking**: All revenue for packing, unpacking and container revenue
            - **Booking & Royalties**: Sales booking revenue and Operating Authority royalties
            - **Special Products**: All special product revenue and HVP transportation
            - **Records Storage**: All records storage revenue
            - **Military DPM Contracts**: Revenues from Direct Procurement Method military contracts
            - **Distribution**: All distribution revenue
            - **Hotel Deliveries**: All revenues from hotel deliveries
            - **Other Revenue**: Any misc. operational revenue not listed elsewhere
            """)

        with st.expander("**Direct Expenses / Cost of Revenue**"):
            st.markdown("""
            - **Direct Wages**: Salaries, wages, and bonuses paid to operations personnel
            - **Vehicle Operating Expense**: Repairs, fuel, license, registration, tires, permits for revenue equipment
            - **Packing & Warehouse Supplies**: Moving and packing supplies
            - **Owner Operator Expenses**: All payments to owner operators (by job type if tracked)
            - **Claims**: All operational claims
            - **Other Transportation Expense**: Trip expense, deadhead miles, agent fees, freight, BIPD
            - **Lease Expense - Revenue Equipment**: All lease expense on revenue equipment
            - **Other Direct Expenses**: Credit card fees and other direct expenses not otherwise classified
            - **Rent and/or Building Expense**: Actual or estimated fair market rent
            - **Depreciation/Amortization**: Depreciation on assets (excluding buildings)
            """)

        with st.expander("**Operating Expenses**"):
            st.markdown("""
            - **Advertising & Marketing**: Advertising, brochures, yellow pages, promotional items
            - **Bad Debts**: Uncollectible accounts receivable written off
            - **Sales Compensation**: Salaries, commissions, and draws for sales people
            - **Computer Support**: IT expenses, software licensing, satellite tracking
            - **Payroll Taxes & Benefits**: Payroll taxes, health insurance, drug testing, DOT physicals, training
            - **Insurance**: Cargo, fleet, general liability insurance
            - **Legal & Accounting**: Legal and accounting work, tax return preparation
            - **Office Expense**: Office & printer supplies, printed forms, coffee, janitorial
            - **Professional Fees**: Consultants, detectives, non-trade professionals
            - **Salaries - Administrative**: All non-operations salaries (admin, office, dispatch, sales support)
            - **Taxes & Licenses**: All taxes and licenses not related to vehicles or income
            - **Telephone/Fax/Utilities/Internet**: All communication and utility expenses
            - **Travel & Entertainment**: Admin/sales related transportation, meals, lodging
            """)

        with st.expander("**Other Income / Expense**"):
            st.markdown("""
            - **PPP Funds Received (forgiven)**: Forgiven PPP money, employee retention tax credits
            - **Other Income**: Interest income, gain on sale of asset, litigation income
            - **CEO Comp/Perks**: All salaries, bonuses or perks paid to CEO (enter as negative)
            - **Other Expense**: Loss on sale of asset, research of new business lines (enter as negative)
            - **Interest Expense**: All interest paid on interest bearing debt (enter as negative)
            """)

        # Add note about the source
        st.markdown("---")
        st.markdown("""
        <div style="background-color: #f0f8ff; padding: 1rem; border-radius: 5px; margin: 1rem 0;">
            <p style="font-size: 0.9rem; color: #1a202c; margin: 0;">
                <strong>Note:</strong> This glossary is compiled from industry-standard financial definitions and
                the specific metrics used in this dashboard. For more detailed information about any term,
                please consult with your financial advisor or CFO.
            </p>
        </div>
        """, unsafe_allow_html=True)


# Entry point for testing
if __name__ == "__main__":
    st.set_page_config(
        page_title="Financial Glossary - BPC Dashboard",
        page_icon="📚",
        layout="wide"
    )
    create_glossary_page()
