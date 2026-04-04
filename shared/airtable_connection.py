import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def _escape_airtable_value(value):
    """Escape a value for safe use in Airtable filterByFormula strings.

    Prevents formula injection by escaping single quotes and backslashes
    in user-supplied values before they are interpolated into filter formulas.
    """
    if not isinstance(value, str):
        value = str(value)
    # Escape backslashes first, then single quotes
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _parse_percentage_or_float(value):
    """Parse a value that might be a percentage string or a float"""
    if value is None:
        return 0.0
    
    if isinstance(value, str):
        # Remove percentage sign and convert to float
        if value.endswith('%'):
            try:
                return float(value.replace('%', '').strip())
            except ValueError:
                return 0.0
        # Try to convert string to float
        try:
            return float(value.strip())
        except ValueError:
            return 0.0
    
    # If it's already a number, return as float
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _build_publication_filter(is_admin):
    """Return Airtable publication_status filter clause based on role."""
    if is_admin:
        # Admin sees submitted + published + legacy records (BLANK = no status set)
        return "OR({publication_status}='submitted',{publication_status}='published',{publication_status}=BLANK())"
    else:
        # Company user sees only published + legacy records
        return "OR({publication_status}='published',{publication_status}=BLANK())"


class AirtableConnection:
    def __init__(self):
        # Try to get from Streamlit secrets first, then fall back to .env
        try:
            self.base_id = st.secrets.get("AIRTABLE_BASE_ID") or os.getenv("AIRTABLE_BASE_ID")
            self.pat = st.secrets.get("AIRTABLE_PAT") or os.getenv("AIRTABLE_PAT")
        except FileNotFoundError:
            self.base_id = os.getenv("AIRTABLE_BASE_ID")
            self.pat = os.getenv("AIRTABLE_PAT")
        
        if not self.base_id or not self.pat:
            st.error("⚠️ Airtable credentials not found!")
            st.info("**Setup Required**: Create a `.env` file in the project root with your Airtable credentials:")
            st.code("AIRTABLE_BASE_ID=your_base_id_here\nAIRTABLE_PAT=your_personal_access_token_here", language="bash")
            st.info("💡 You can get these from your Airtable account settings.")
            st.stop()
            
        self.headers = {
            'Authorization': f'Bearer {self.pat}',
            'Content-Type': 'application/json'
        }
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}"
    
    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_companies(_self):
        """Fetch all companies from Airtable"""
        try:
            url = f"{_self.base_url}/companies"
            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                companies = []
                for record in data['records']:
                    companies.append({
                        'id': record['id'],
                        'name': record['fields'].get('company_name', 'Unknown'),
                        'industry': record['fields'].get('industry', 'Unknown'),
                        'status': record['fields'].get('status', 'Unknown')
                    })
                return companies
            else:
                st.error(f"Error fetching companies: {response.text}")
                return []
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return []
    
    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_balance_sheet_data(_self, company_name=None, is_admin=False):
        """Fetch balance sheet data from Airtable for 2024 Annual period"""
        try:
            url = f"{_self.base_url}/balance_sheet_data"
            if company_name:
                safe_name = _escape_airtable_value(company_name)
                pub_filter = _build_publication_filter(is_admin)
                filter_formula = f"AND({{company}}='{safe_name}',{{period}}='2024 Annual',{pub_filter})"
                url += f"?filterByFormula={filter_formula}"

            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                balance_data = []
                for record in data['records']:
                    fields = record['fields']
                    balance_data.append({
                        'id': record['id'],
                        'company_name': fields.get('company_name'),
                        'current_ratio': _parse_percentage_or_float(fields.get('current_ratio', 0)),
                        'debt_to_equity': _parse_percentage_or_float(fields.get('debt_to_equity', 0)),
                        'working_capital_pct_asset': _parse_percentage_or_float(fields.get('working_capital_pct_asset', 0)),
                        'survival_score': _parse_percentage_or_float(fields.get('survival_score', 0)),
                        'period': fields.get('period', '2024 Annual'),
                        # Balance sheet amounts for charts
                        'total_current_assets': _parse_percentage_or_float(fields.get('total_current_assets', 0)),
                        'total_current_liabilities': _parse_percentage_or_float(fields.get('total_current_liabilities', 0)),
                        'total_liabilities': _parse_percentage_or_float(fields.get('total_liabilities', 0)),
                        'owners_equity': _parse_percentage_or_float(fields.get('owners_equity', 0)),
                        'interest_bearing_debt': _parse_percentage_or_float(fields.get('interest_bearing_debt', 0)),
                        'equity_000': _parse_percentage_or_float(fields.get('equity_000', 0))
                    })
                return balance_data
            else:
                st.error(f"Error fetching balance sheet data: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            st.error(f"Balance sheet connection error: {str(e)}")
            return []
    
    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_income_statement_data(_self, company_name=None, is_admin=False):
        """Fetch income statement data from Airtable for 2024 Annual period"""
        try:
            url = f"{_self.base_url}/income_statement_data"
            if company_name:
                safe_name = _escape_airtable_value(company_name)
                pub_filter = _build_publication_filter(is_admin)
                filter_formula = f"AND({{company}}='{safe_name}',{{period}}='2024 Annual',{pub_filter})"
                url += f"?filterByFormula={filter_formula}"

            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                income_data = []
                for record in data['records']:
                    fields = record['fields']
                    income_data.append({
                        'id': record['id'],
                        'company_name': fields.get('company_name'),
                        'gpm': _parse_percentage_or_float(fields.get('gpm', 0)),
                        'opm': _parse_percentage_or_float(fields.get('opm', 0)),
                        'rev_admin_employee': _parse_percentage_or_float(fields.get('rev_admin_employee', 0)),
                        'ebitda_margin': _parse_percentage_or_float(fields.get('ebitda_margin', 0)),
                        'ebitda': _parse_percentage_or_float(fields.get('ebitda', 0)),
                        'ebitda_000': _parse_percentage_or_float(fields.get('ebitda_000', 0)),
                        'net_profit': _parse_percentage_or_float(fields.get('net_profit', 0)),
                        'sales_assets': _parse_percentage_or_float(fields.get('sales_assets', 0)),
                        'period': fields.get('period', '2024 Annual'),
                        # Labor cost fields for labor cost table
                        'admin_labor_cost': _parse_percentage_or_float(fields.get('admin_labor_cost', 0)),
                        'admin_labor_cost_pct_rev': _parse_percentage_or_float(fields.get('admin_labor_cost_pct_rev', 0)),
                        'rev_producing_labor_expenses': _parse_percentage_or_float(fields.get('rev_producing_labor_expenses', 0)),
                        'rev_producing_labor_expenses_pct_rev': _parse_percentage_or_float(fields.get('rev_producing_labor_expenses_pct_rev', 0)),
                        'labor_ratio': _parse_percentage_or_float(fields.get('labor_ratio', 0)),
                        'tot_labor_expenses': _parse_percentage_or_float(fields.get('tot_labor_expenses', 0)),
                        'tot_labor_expenses_pct_rev': _parse_percentage_or_float(fields.get('tot_labor_expenses_pct_rev', 0)),
                        # Additional income statement fields for charts
                        'total_revenue': _parse_percentage_or_float(fields.get('total_revenue', 0)),
                        'total_cost_of_revenue': _parse_percentage_or_float(fields.get('total_cost_of_revenue', 0)),
                        'gross_profit': _parse_percentage_or_float(fields.get('gross_profit', 0)),
                        'total_operating_expenses': _parse_percentage_or_float(fields.get('total_operating_expenses', 0)),
                        'operating_profit': _parse_percentage_or_float(fields.get('operating_profit', 0)),
                        'profit_before_tax_with_ppp': _parse_percentage_or_float(fields.get('profit_before_tax_with_ppp', 0)),
                        'npm': _parse_percentage_or_float(fields.get('npm', 0)),
                        # Revenue diversification fields
                        'local_hhg': _parse_percentage_or_float(fields.get('local_hhg', 0)),
                        'inter_state_hhg': _parse_percentage_or_float(fields.get('inter_state_hhg', 0)),
                        'office_industrial': _parse_percentage_or_float(fields.get('office_industrial', 0)),
                        'distribution': _parse_percentage_or_float(fields.get('distribution', 0))
                    })
                return income_data
            else:
                st.error(f"Error fetching income statement data: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            st.error(f"Income statement connection error: {str(e)}")
            return []
    
    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_balance_sheet_data_by_period(_self, company_name, period, is_admin=False):
        """Fetch balance sheet data from Airtable for a specific period"""
        try:
            url = f"{_self.base_url}/balance_sheet_data"
            safe_name = _escape_airtable_value(company_name)
            safe_period = _escape_airtable_value(period)
            pub_filter = _build_publication_filter(is_admin)
            filter_formula = f"AND({{company}}='{safe_name}',{{period}}='{safe_period}',{pub_filter})"
            url += f"?filterByFormula={filter_formula}"

            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                balance_data = []
                for record in data['records']:
                    fields = record['fields']
                    balance_data.append({
                        'id': record['id'],
                        'company_name': fields.get('company_name'),
                        'current_ratio': _parse_percentage_or_float(fields.get('current_ratio', 0)),
                        'debt_to_equity': _parse_percentage_or_float(fields.get('debt_to_equity', 0)),
                        'working_capital_pct_asset': _parse_percentage_or_float(fields.get('working_capital_pct_asset', 0)),
                        'survival_score': _parse_percentage_or_float(fields.get('survival_score', 0)),
                        'period': fields.get('period', period),
                        # Balance sheet amounts for charts
                        'total_current_assets': _parse_percentage_or_float(fields.get('total_current_assets', 0)),
                        'total_current_liabilities': _parse_percentage_or_float(fields.get('total_current_liabilities', 0)),
                        'total_liabilities': _parse_percentage_or_float(fields.get('total_liabilities', 0)),
                        'owners_equity': _parse_percentage_or_float(fields.get('owners_equity', 0)),
                        'total_assets': _parse_percentage_or_float(fields.get('total_assets', 0)),
                        
                        # Individual Balance Sheet Line Items for Trend Table
                        # Current Assets
                        'cash_and_cash_equivalents': _parse_percentage_or_float(fields.get('cash_and_cash_equivalents', 0)),
                        'trade_accounts_receivable': _parse_percentage_or_float(fields.get('trade_accounts_receivable', 0)),
                        'receivables': _parse_percentage_or_float(fields.get('receivables', 0)),
                        'other_receivables': _parse_percentage_or_float(fields.get('other_receivables', 0)),
                        'prepaid_expenses': _parse_percentage_or_float(fields.get('prepaid_expenses', 0)),
                        'related_company_receivables': _parse_percentage_or_float(fields.get('related_company_receivables', 0)),
                        'owner_receivables': _parse_percentage_or_float(fields.get('owner_receivables', 0)),
                        'other_current_assets': _parse_percentage_or_float(fields.get('other_current_assets', 0)),
                        
                        # Fixed Assets
                        'gross_fixed_assets': _parse_percentage_or_float(fields.get('gross_fixed_assets', 0)),
                        'accumulated_depreciation': _parse_percentage_or_float(fields.get('accumulated_depreciation', 0)),
                        'net_fixed_assets': _parse_percentage_or_float(fields.get('net_fixed_assets', 0)),
                        
                        # Other Assets
                        'inter_company_receivable': _parse_percentage_or_float(fields.get('inter_company_receivable', 0)),
                        'other_assets': _parse_percentage_or_float(fields.get('other_assets', 0)),
                        
                        # Current Liabilities
                        'notes_payable_bank': _parse_percentage_or_float(fields.get('notes_payable_bank', 0)),
                        'notes_payable_owners': _parse_percentage_or_float(fields.get('notes_payable_owners', 0)),
                        'trade_accounts_payable': _parse_percentage_or_float(fields.get('trade_accounts_payable', 0)),
                        'accrued_expenses': _parse_percentage_or_float(fields.get('accrued_expenses', 0)),
                        'current_portion_ltd': _parse_percentage_or_float(fields.get('current_portion_ltd', 0)),
                        'inter_company_payable': _parse_percentage_or_float(fields.get('inter_company_payable', 0)),
                        'other_current_liabilities': _parse_percentage_or_float(fields.get('other_current_liabilities', 0)),
                        
                        # Long-term Liabilities
                        'eid_loan': _parse_percentage_or_float(fields.get('eid_loan', 0)),
                        'long_term_debt': _parse_percentage_or_float(fields.get('long_term_debt', 0)),
                        'interest_bearing_debt': _parse_percentage_or_float(fields.get('interest_bearing_debt', 0)),
                        'notes_payable_owners_lt': _parse_percentage_or_float(fields.get('notes_payable_owners_lt', 0)),
                        'inter_company_debt': _parse_percentage_or_float(fields.get('inter_company_debt', 0)),
                        'other_lt_liabilities': _parse_percentage_or_float(fields.get('other_lt_liabilities', 0)),
                        'total_long_term_liabilities': _parse_percentage_or_float(fields.get('total_long_term_liabilities', 0)),
                        
                        # Total Liabilities & Equity (the missing field!)
                        'total_liabilities_equity': _parse_percentage_or_float(fields.get('total_liabilities_equity', 0)),
                        
                        # Cash flow metrics from balance sheet table
                        'dso': _parse_percentage_or_float(fields.get('dso', 0)),
                        # DEPRECATED: ocf_rev, fcf_rev, ncf_rev are now calculated in shared/cash_flow_utils.py
                        # These fields are kept for backward compatibility but should not be used
                        'ocf_rev': _parse_percentage_or_float(fields.get('ocf_rev', 0)),
                        'fcf_rev': _parse_percentage_or_float(fields.get('fcf_rev', 0)),
                        'ncf_rev': _parse_percentage_or_float(fields.get('ncf_rev', 0)),

                        # Equity field for value trends table
                        'equity_000': _parse_percentage_or_float(fields.get('equity_000', 0))
                    })
                return balance_data
            else:
                return []
        except Exception as e:
            return []
    
    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_income_statement_data_by_period(_self, company_name, period, is_admin=False):
        """Fetch income statement data from Airtable for a specific period"""
        try:
            url = f"{_self.base_url}/income_statement_data"
            safe_name = _escape_airtable_value(company_name)
            safe_period = _escape_airtable_value(period)
            pub_filter = _build_publication_filter(is_admin)
            filter_formula = f"AND({{company}}='{safe_name}',{{period}}='{safe_period}',{pub_filter})"
            url += f"?filterByFormula={filter_formula}"

            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                income_data = []
                for record in data['records']:
                    fields = record['fields']
                    income_data.append({
                        'id': record['id'],
                        'company_name': fields.get('company_name'),
                        'gpm': _parse_percentage_or_float(fields.get('gpm', 0)),
                        'opm': _parse_percentage_or_float(fields.get('opm', 0)),
                        'rev_admin_employee': _parse_percentage_or_float(fields.get('rev_admin_employee', 0)),
                        'ebitda_margin': _parse_percentage_or_float(fields.get('ebitda_margin', 0)),
                        'ebitda': _parse_percentage_or_float(fields.get('ebitda', 0)),
                        'ebitda_000': _parse_percentage_or_float(fields.get('ebitda_000', 0)),
                        'net_profit': _parse_percentage_or_float(fields.get('net_profit', 0)),
                        'sales_assets': _parse_percentage_or_float(fields.get('sales_assets', 0)),
                        'period': fields.get('period', period),
                        # Labor cost fields for labor cost table
                        'admin_labor_cost': _parse_percentage_or_float(fields.get('admin_labor_cost', 0)),
                        'admin_labor_cost_pct_rev': _parse_percentage_or_float(fields.get('admin_labor_cost_pct_rev', 0)),
                        'rev_producing_labor_expenses': _parse_percentage_or_float(fields.get('rev_producing_labor_expenses', 0)),
                        'rev_producing_labor_expenses_pct_rev': _parse_percentage_or_float(fields.get('rev_producing_labor_expenses_pct_rev', 0)),
                        'labor_ratio': _parse_percentage_or_float(fields.get('labor_ratio', 0)),
                        'tot_labor_expenses': _parse_percentage_or_float(fields.get('tot_labor_expenses', 0)),
                        'tot_labor_expenses_pct_rev': _parse_percentage_or_float(fields.get('tot_labor_expenses_pct_rev', 0)),
                        # Additional income statement fields for charts
                        'total_revenue': _parse_percentage_or_float(fields.get('total_revenue', 0)),
                        'total_cost_of_revenue': _parse_percentage_or_float(fields.get('total_cost_of_revenue', 0)),
                        'total_operating_expenses': _parse_percentage_or_float(fields.get('total_operating_expenses', 0)),
                        'operating_profit': _parse_percentage_or_float(fields.get('operating_profit', 0)),
                        'profit_before_tax_with_ppp': _parse_percentage_or_float(fields.get('profit_before_tax_with_ppp', 0)),
                        'npm': _parse_percentage_or_float(fields.get('npm', 0)),
                        
                        # All Revenue fields from INCOME_STATEMENT_MAPPING
                        'intra_state_hhg': _parse_percentage_or_float(fields.get('intra_state_hhg', 0)),
                        'local_hhg': _parse_percentage_or_float(fields.get('local_hhg', 0)),
                        'inter_state_hhg': _parse_percentage_or_float(fields.get('inter_state_hhg', 0)),
                        'office_industrial': _parse_percentage_or_float(fields.get('office_industrial', 0)),
                        'warehouse': _parse_percentage_or_float(fields.get('warehouse', 0)),
                        'warehouse_handling': _parse_percentage_or_float(fields.get('warehouse_handling', 0)),
                        'international': _parse_percentage_or_float(fields.get('international', 0)),
                        'packing_unpacking': _parse_percentage_or_float(fields.get('packing_unpacking', 0)),
                        'booking_royalties': _parse_percentage_or_float(fields.get('booking_royalties', 0)),
                        'special_products': _parse_percentage_or_float(fields.get('special_products', 0)),
                        'records_storage': _parse_percentage_or_float(fields.get('records_storage', 0)),
                        'military_dpm_contracts': _parse_percentage_or_float(fields.get('military_dpm_contracts', 0)),
                        'distribution': _parse_percentage_or_float(fields.get('distribution', 0)),
                        'hotel_deliveries': _parse_percentage_or_float(fields.get('hotel_deliveries', 0)),
                        'other_revenue': _parse_percentage_or_float(fields.get('other_revenue', 0)),
                        
                        # Cost of Revenue fields from INCOME_STATEMENT_MAPPING  
                        'direct_wages': _parse_percentage_or_float(fields.get('direct_wages', 0)),
                        'vehicle_operating_expenses': _parse_percentage_or_float(fields.get('vehicle_operating_expenses', 0)),
                        'packing_warehouse_supplies': _parse_percentage_or_float(fields.get('packing_warehouse_supplies', 0)),
                        'oo_exp_intra_state': _parse_percentage_or_float(fields.get('oo_exp_intra_state', 0)),
                        'oo_inter_state': _parse_percentage_or_float(fields.get('oo_inter_state', 0)),
                        'oo_oi': _parse_percentage_or_float(fields.get('oo_oi', 0)),
                        'oo_packing': _parse_percentage_or_float(fields.get('oo_packing', 0)),
                        'oo_other': _parse_percentage_or_float(fields.get('oo_other', 0)),
                        'claims': _parse_percentage_or_float(fields.get('claims', 0)),
                        'other_trans_exp': _parse_percentage_or_float(fields.get('other_trans_exp', 0)),
                        'depreciation': _parse_percentage_or_float(fields.get('depreciation', 0)),
                        'lease_expense_rev_equip': _parse_percentage_or_float(fields.get('lease_expense_rev_equip', 0)),
                        'rent': _parse_percentage_or_float(fields.get('rent', 0)),
                        'other_direct_expenses': _parse_percentage_or_float(fields.get('other_direct_expenses', 0)),
                        'gross_profit': _parse_percentage_or_float(fields.get('gross_profit', 0)),
                        
                        # Operating Expenses fields from INCOME_STATEMENT_MAPPING
                        'advertising_marketing': _parse_percentage_or_float(fields.get('advertising_marketing', 0)),
                        'bad_debts': _parse_percentage_or_float(fields.get('bad_debts', 0)),
                        'sales_commissions': _parse_percentage_or_float(fields.get('sales_commissions', 0)),
                        'contributions': _parse_percentage_or_float(fields.get('contributions', 0)),
                        'computer_support': _parse_percentage_or_float(fields.get('computer_support', 0)),
                        'dues_sub': _parse_percentage_or_float(fields.get('dues_sub', 0)),
                        'pr_taxes_benefits': _parse_percentage_or_float(fields.get('pr_taxes_benefits', 0)),
                        'equipment_leases_office_equip': _parse_percentage_or_float(fields.get('equipment_leases_office_equip', 0)),
                        'workmans_comp_insurance': _parse_percentage_or_float(fields.get('workmans_comp_insurance', 0)),
                        'insurance': _parse_percentage_or_float(fields.get('insurance', 0)),
                        'legal_accounting': _parse_percentage_or_float(fields.get('legal_accounting', 0)),
                        'office_expense': _parse_percentage_or_float(fields.get('office_expense', 0)),
                        'other_admin': _parse_percentage_or_float(fields.get('other_admin', 0)),
                        'pension_profit_sharing_401k': _parse_percentage_or_float(fields.get('pension_profit_sharing_401k', 0)),
                        'prof_fees': _parse_percentage_or_float(fields.get('prof_fees', 0)),
                        'repairs_maint': _parse_percentage_or_float(fields.get('repairs_maint', 0)),
                        'salaries_admin': _parse_percentage_or_float(fields.get('salaries_admin', 0)),
                        'taxes_licenses': _parse_percentage_or_float(fields.get('taxes_licenses', 0)),
                        'tel_fax_utilities_internet': _parse_percentage_or_float(fields.get('tel_fax_utilities_internet', 0)),
                        'travel_ent': _parse_percentage_or_float(fields.get('travel_ent', 0)),
                        'vehicle_expense_admin': _parse_percentage_or_float(fields.get('vehicle_expense_admin', 0)),
                        
                        # Non-Operating fields from INCOME_STATEMENT_MAPPING
                        'other_income': _parse_percentage_or_float(fields.get('other_income', 0)),
                        'ceo_comp': _parse_percentage_or_float(fields.get('ceo_comp', 0)),
                        'other_expense': _parse_percentage_or_float(fields.get('other_expense', 0)),
                        'interest_expense': _parse_percentage_or_float(fields.get('interest_expense', 0)),
                        'total_nonoperating_income': _parse_percentage_or_float(fields.get('total_nonoperating_income', 0)),
                        
                        # Other fields from INCOME_STATEMENT_MAPPING
                        'administrative_employees': _parse_percentage_or_float(fields.get('administrative_employees', 0)),
                        'number_of_branches': _parse_percentage_or_float(fields.get('number_of_branches', 0))
                    })
                return income_data
            else:
                return []
        except Exception as e:
            return []

    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_all_companies_balance_sheet_by_period(_self, period, is_admin=False):
        """Fetch balance sheet data from Airtable for all companies for a specific period"""
        try:
            url = f"{_self.base_url}/balance_sheet_data"
            safe_period = _escape_airtable_value(period)
            pub_filter = _build_publication_filter(is_admin)
            filter_formula = f"AND({{period}}='{safe_period}',{pub_filter})"
            url += f"?filterByFormula={filter_formula}"

            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                balance_data = []
                for record in data['records']:
                    fields = record['fields']
                    balance_data.append({
                        'id': record['id'],
                        'company_name': fields.get('company_name'),
                        'current_ratio': _parse_percentage_or_float(fields.get('current_ratio', 0)),
                        'debt_to_equity': _parse_percentage_or_float(fields.get('debt_to_equity', 0)),
                        'working_capital_pct_asset': _parse_percentage_or_float(fields.get('working_capital_pct_asset', 0)),
                        'survival_score': _parse_percentage_or_float(fields.get('survival_score', 0)),
                        'interest_bearing_debt': _parse_percentage_or_float(fields.get('interest_bearing_debt', 0)),
                        'equity_000': _parse_percentage_or_float(fields.get('equity_000', 0)),
                        'dso': _parse_percentage_or_float(fields.get('dso', 0)),
                        # DEPRECATED: ocf_rev, fcf_rev, ncf_rev are now calculated in shared/cash_flow_utils.py
                        'ocf_rev': _parse_percentage_or_float(fields.get('ocf_rev', 0)),
                        'fcf_rev': _parse_percentage_or_float(fields.get('fcf_rev', 0)),
                        'ncf_rev': _parse_percentage_or_float(fields.get('ncf_rev', 0)),
                        'period': fields.get('period', period)
                    })
                return balance_data
            else:
                return []
        except Exception as e:
            return []

    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_all_companies_income_statement_by_period(_self, period, is_admin=False):
        """Fetch income statement data from Airtable for all companies for a specific period"""
        try:
            url = f"{_self.base_url}/income_statement_data"
            safe_period = _escape_airtable_value(period)
            pub_filter = _build_publication_filter(is_admin)
            filter_formula = f"AND({{period}}='{safe_period}',{pub_filter})"
            url += f"?filterByFormula={filter_formula}"

            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                income_data = []
                for record in data['records']:
                    fields = record['fields']
                    income_data.append({
                        'id': record['id'],
                        'company_name': fields.get('company_name'),
                        'gpm': _parse_percentage_or_float(fields.get('gpm', 0)),
                        'opm': _parse_percentage_or_float(fields.get('opm', 0)),
                        'npm': _parse_percentage_or_float(fields.get('npm', 0)),
                        'rev_admin_employee': _parse_percentage_or_float(fields.get('rev_admin_employee', 0)),
                        'ebitda_margin': _parse_percentage_or_float(fields.get('ebitda_margin', 0)),
                        'sales_assets': _parse_percentage_or_float(fields.get('sales_assets', 0)),
                        'ebitda_000': _parse_percentage_or_float(fields.get('ebitda_000', 0)),
                        'ebitda': _parse_percentage_or_float(fields.get('ebitda', 0)),
                        'profit_before_tax_with_ppp': _parse_percentage_or_float(fields.get('profit_before_tax_with_ppp', 0)),
                        'gross_profit': _parse_percentage_or_float(fields.get('gross_profit', 0)),
                        'operating_profit': _parse_percentage_or_float(fields.get('operating_profit', 0)),
                        'period': fields.get('period', period),
                        # Add fields needed for admin labor calculation
                        'pr_taxes_benefits': _parse_percentage_or_float(fields.get('pr_taxes_benefits', 0)),
                        'pension_profit_sharing_401k': _parse_percentage_or_float(fields.get('pension_profit_sharing_401k', 0)),
                        'salaries_admin': _parse_percentage_or_float(fields.get('salaries_admin', 0)),
                        'total_revenue': _parse_percentage_or_float(fields.get('total_revenue', 0)),
                        # Add fields needed for revenue producing labor calculation
                        'direct_wages': _parse_percentage_or_float(fields.get('direct_wages', 0)),
                        'vehicle_operating_expenses': _parse_percentage_or_float(fields.get('vehicle_operating_expenses', 0)),
                        'oo_exp_intra_state': _parse_percentage_or_float(fields.get('oo_exp_intra_state', 0)),
                        'oo_inter_state': _parse_percentage_or_float(fields.get('oo_inter_state', 0)),
                        'oo_packing': _parse_percentage_or_float(fields.get('oo_packing', 0)),
                        'oo_oi': _parse_percentage_or_float(fields.get('oo_oi', 0)),
                        'lease_expense_rev_equip': _parse_percentage_or_float(fields.get('lease_expense_rev_equip', 0)),
                        'oo_other': _parse_percentage_or_float(fields.get('oo_other', 0)),
                        # Pre-computed labor cost fields
                        'admin_labor_cost': _parse_percentage_or_float(fields.get('admin_labor_cost', 0)),
                        'admin_labor_cost_pct_rev': _parse_percentage_or_float(fields.get('admin_labor_cost_pct_rev', 0)),
                        'rev_producing_labor_expenses': _parse_percentage_or_float(fields.get('rev_producing_labor_expenses', 0)),
                        'rev_producing_labor_expenses_pct_rev': _parse_percentage_or_float(fields.get('rev_producing_labor_expenses_pct_rev', 0)),
                        'labor_ratio': _parse_percentage_or_float(fields.get('labor_ratio', 0)),
                        'tot_labor_expenses': _parse_percentage_or_float(fields.get('tot_labor_expenses', 0)),
                        'tot_labor_expenses_pct_rev': _parse_percentage_or_float(fields.get('tot_labor_expenses_pct_rev', 0))
                    })
                return income_data
            else:
                return []
        except Exception as e:
            return []

    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_all_data_for_company(_self, company_name, years=None, is_admin=False):
        """Fetch all balance sheet and income statement data for a company across multiple years"""
        if years is None:
            from shared.year_config import get_default_years
            years = get_default_years()

        result = {
            'balance_sheet': {},
            'income_statement': {}
        }

        # Fetch data for all years
        for year in years:
            period_filter = f"{year} Annual"
            try:
                # Get both balance sheet and income statement data
                balance_data = _self.get_balance_sheet_data_by_period(company_name, period_filter, is_admin=is_admin)
                income_data = _self.get_income_statement_data_by_period(company_name, period_filter, is_admin=is_admin)
                
                if balance_data:
                    result['balance_sheet'][year] = balance_data[0]
                if income_data:
                    result['income_statement'][year] = income_data[0]
                    
            except Exception:
                # Skip years with errors
                continue
                
        return result

    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_wins(_self, company_name, period_name, include_drafts=False):
        """
        Fetch wins for a specific company and period
        Uses period link to filter by company

        Args:
            company_name: Company name
            period_name: Period name (e.g., "2024 Annual")
            include_drafts: If True, return all items (for admin). If False, only published items.
        """
        try:
            # First, get the period record ID for this company+period
            period_id = _self._get_period_id(company_name, period_name)
            if not period_id:
                # Return debug info as empty list with error marker
                return [{'_debug_error': f'No period found for {company_name}/{period_name}'}] if include_drafts else []

            # Query wins table - filter by status/is_active, then filter by period in Python
            # (FIND/ARRAYJOIN doesn't work reliably with linked record fields)
            url = f"{_self.base_url}/wins"
            if include_drafts:
                filter_formula = "{is_active}=TRUE()"
            else:
                filter_formula = "AND({is_active}=TRUE(), {status}='published')"
            url += f"?filterByFormula={filter_formula}&sort[0][field]=display_order&sort[0][direction]=asc"

            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                wins = []
                for record in data['records']:
                    fields = record['fields']
                    # Filter by period_id in Python
                    record_period = fields.get('period', [])
                    if record_period and record_period[0] == period_id:
                        wins.append({
                            'id': record['id'],
                            'win_text': fields.get('win_text', ''),
                            'display_order': fields.get('display_order', 99),
                            'is_active': fields.get('is_active', True),
                            'status': fields.get('status', 'draft')
                        })
                return wins
            # Return error info for debugging
            if include_drafts:
                return [{'_debug_error': f'API returned {response.status_code}'}]
            return []
        except Exception as e:
            if include_drafts:
                return [{'_debug_error': f'Exception: {str(e)}'}]
            return []

    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_challenges(_self, company_name, period_name, include_drafts=False):
        """
        Fetch challenges for a specific company and period
        Uses period link to filter by company

        Args:
            company_name: Company name
            period_name: Period name (e.g., "2024 Annual")
            include_drafts: If True, return all items (for admin). If False, only published items.
        """
        try:
            # First, get the period record ID for this company+period
            period_id = _self._get_period_id(company_name, period_name)
            if not period_id:
                return []

            # Query challenges table - filter by status/is_active, then filter by period in Python
            url = f"{_self.base_url}/challenges"
            if include_drafts:
                filter_formula = "{is_active}=TRUE()"
            else:
                filter_formula = "AND({is_active}=TRUE(), {status}='published')"
            url += f"?filterByFormula={filter_formula}&sort[0][field]=display_order&sort[0][direction]=asc"

            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                challenges = []
                for record in data['records']:
                    fields = record['fields']
                    # Filter by period_id in Python
                    record_period = fields.get('period', [])
                    if record_period and record_period[0] == period_id:
                        challenges.append({
                            'id': record['id'],
                            'challenge_text': fields.get('challenge_text', ''),
                            'display_order': fields.get('display_order', 99),
                            'is_active': fields.get('is_active', True),
                            'status': fields.get('status', 'draft')
                        })
                return challenges
            return []
        except Exception as e:
            return []

    @st.cache_data(ttl=1800, show_spinner=False)  # 30 minutes for better performance
    def get_action_items(_self, company_name, period_name, include_drafts=False):
        """
        Fetch action items for a specific company and period
        Uses period link to filter by company

        Args:
            company_name: Company name
            period_name: Period name (e.g., "2024 Annual")
            include_drafts: If True, return all items (for admin). If False, only published items.
        """
        try:
            # First, get the period record ID for this company+period
            period_id = _self._get_period_id(company_name, period_name)
            if not period_id:
                return []

            # Query action_items table - filter by status/is_active, then filter by period in Python
            # (FIND/ARRAYJOIN doesn't work reliably with linked record fields)
            url = f"{_self.base_url}/action_items"
            if include_drafts:
                filter_formula = "{is_active}=TRUE()"
            else:
                filter_formula = "AND({is_active}=TRUE(), {status}='published')"
            url += f"?filterByFormula={filter_formula}&sort[0][field]=display_order&sort[0][direction]=asc"

            response = requests.get(url, headers=_self.headers)
            if response.status_code == 200:
                data = response.json()
                action_items = []
                for record in data['records']:
                    fields = record['fields']
                    # Filter by period_id in Python
                    record_period = fields.get('period', [])
                    if record_period and record_period[0] == period_id:
                        action_items.append({
                            'id': record['id'],
                            'action_item_text': fields.get('action_item_text', ''),
                            'display_order': fields.get('display_order', 99),
                            'is_active': fields.get('is_active', True),
                            'status': fields.get('status', 'draft')
                        })
                return action_items
            return []
        except Exception as e:
            return []

    def _get_period_id(self, company_name, period_name):
        """
        Helper method to get the period record ID for a company+period combination
        This is needed because financial_periods has separate records per company

        Note: company field is a linked record, so we search for company name in the array
        """
        try:
            url = f"{self.base_url}/financial_periods"
            # Use FIND to search for company name within the linked field
            safe_name = _escape_airtable_value(company_name)
            safe_period = _escape_airtable_value(period_name)
            filter_formula = f"AND(FIND('{safe_name}', ARRAYJOIN({{company}})), {{period_name}}='{safe_period}')"
            url += f"?filterByFormula={filter_formula}"

            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data['records']:
                    return data['records'][0]['id']
            return None
        except Exception as e:
            # Log error for debugging
            st.warning(f"Error getting period ID: {str(e)}")
            return None

# Session-level company caching for better performance
def get_companies_cached():
    """Get companies with session-level caching for optimal performance"""
    if 'companies_cache' not in st.session_state:
        airtable = get_airtable_connection()
        st.session_state.companies_cache = airtable.get_companies()
    return st.session_state.companies_cache

# Initialize connection as a cached resource
@st.cache_resource
def get_airtable_connection():
    return AirtableConnection()