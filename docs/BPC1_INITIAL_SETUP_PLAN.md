# BPC1 Dashboard - Initial Setup Plan

**Created:** 2026-02-24
**Status:** In Progress

---

## What's Already Done

- [x] Codebase copied from BPC2 dashboard
- [x] GitHub repo created: `adityarbhat/bpc1-dashboard` (private)
- [x] Python venv set up with all dependencies installed (`venv/`)
- [x] Initial commit pushed to GitHub
- [x] `.gitignore` updated to include `venv/`

---

## What Needs To Be Done

### Phase 1: Airtable Setup

The dashboard reads all financial data from Airtable. We need a new, empty Airtable base with the same structure as BPC2.

#### Step 1A: Duplicate the BPC2 Airtable Base

1. Go to [airtable.com](https://airtable.com) and open the existing BPC2 base
2. Click the dropdown arrow next to the base name → **Duplicate base**
3. Name it `BPC1 Dashboard` (or similar)
4. This copies all tables, fields, views, AND existing data

#### Step 1B: Clear All Data from the Duplicate

After duplicating, delete all records from every table (keep the structure):

| Table | Action |
|-------|--------|
| `companies` | Delete all 10 BPC2 companies, add 10 BPC1 companies |
| `balance_sheet_data` | Delete ALL records (will be populated via uploads) |
| `income_statement_data` | Delete ALL records (will be populated via uploads) |
| `financial_periods` | Delete ALL records (will be created per company) |
| `wins` | Delete ALL records |
| `challenges` | Delete ALL records |
| `action_items` | Delete ALL records |
| `data_import_log` | Delete ALL records |

**To bulk delete in Airtable:** Select all rows (Ctrl+A / Cmd+A), right-click → Delete records.

#### Step 1C: Add BPC1 Companies

In the `companies` table, add the 10 new BPC1 company names. The `company_name` field is the primary field and must match exactly what will be used in Supabase.

> **TODO:** Fill in the 10 BPC1 company names once finalized.

#### Step 1D: Generate New Airtable PAT

1. Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Click **Create new token**
3. Name: `BPC1 Dashboard`
4. Scopes needed:
   - `data.records:read`
   - `data.records:write`
   - `schema.bases:read`
5. Access: Select ONLY the new BPC1 base
6. Copy the token (starts with `pat...`)

#### Step 1E: Note the Base ID

1. Open the new BPC1 base in Airtable
2. The Base ID is in the URL: `https://airtable.com/appXXXXXXXXXXXXXX/...`
3. It starts with `app` followed by 14 characters

**Save these values:**
```
AIRTABLE_PAT=pat...
AIRTABLE_BASE_ID=app...
```

---

### Phase 1 Reference: Complete Airtable Table Structure

Below is the exact table and field structure that must exist in the new base (this is what the code expects).

#### Table: `companies`
| Field | Type | Notes |
|-------|------|-------|
| `company_name` | Text (Primary) | Must match Supabase exactly |
| `industry` | Text | Optional |
| `status` | Single Select | Optional |

#### Table: `financial_periods`
| Field | Type | Notes |
|-------|------|-------|
| `period_name` | Text (Primary) | e.g., "2024 Annual", "2025 H1" |
| `company` | Linked Record → companies | |
| `period_type` | Single Select | "Annual", "Semi-Annual" |
| `half_year` | Single Select | "H1", "H2" (for semi-annual only) |
| `start_date` | Date | |
| `end_date` | Date | |

#### Table: `balance_sheet_data`

**Metadata fields:**
| Field | Type | Notes |
|-------|------|-------|
| `company` | Linked Record → companies | |
| `company_name` | Lookup (from company) | Auto-populated |
| `period` | Linked Record → financial_periods | |
| `period_name` | Lookup (from period) | Auto-populated |
| `publication_status` | Single Select | 'submitted', 'published' |
| `submitted_by` | Email | |
| `submitted_date` | Date | |
| `published_by` | Email | |
| `published_date` | Date | |
| `upload_date` | Date | |

**Ratio fields (pre-computed on upload):**
| Field | Type |
|-------|------|
| `current_ratio` | Number |
| `debt_to_equity` | Number |
| `working_capital_pct_asset` | Number |
| `survival_score` | Number |
| `dso` | Number |

**Current Assets:**
| Field | Type |
|-------|------|
| `cash_and_cash_equivalents` | Currency |
| `trade_accounts_receivable` | Currency |
| `receivables` | Currency |
| `other_receivables` | Currency |
| `prepaid_expenses` | Currency |
| `related_company_receivables` | Currency |
| `owner_receivables` | Currency |
| `other_current_assets` | Currency |
| `total_current_assets` | Currency |

**Fixed Assets:**
| Field | Type |
|-------|------|
| `gross_fixed_assets` | Currency |
| `accumulated_depreciation` | Currency |
| `net_fixed_assets` | Currency |

**Other Assets:**
| Field | Type |
|-------|------|
| `inter_company_receivable` | Currency |
| `other_assets` | Currency |
| `total_assets` | Currency |

**Current Liabilities:**
| Field | Type |
|-------|------|
| `notes_payable_bank` | Currency |
| `notes_payable_owners` | Currency |
| `trade_accounts_payable` | Currency |
| `accrued_expenses` | Currency |
| `current_portion_ltd` | Currency |
| `inter_company_payable` | Currency |
| `other_current_liabilities` | Currency |
| `total_current_liabilities` | Currency |

**Long-Term Liabilities:**
| Field | Type |
|-------|------|
| `eid_loan` | Currency |
| `long_term_debt` | Currency |
| `notes_payable_owners_lt` | Currency |
| `inter_company_debt` | Currency |
| `other_lt_liabilities` | Currency |
| `total_long_term_liabilities` | Currency |
| `total_liabilities` | Currency |

**Equity & Totals:**
| Field | Type |
|-------|------|
| `owners_equity` | Currency |
| `equity_000` | Currency (in thousands) |
| `total_liabilities_equity` | Currency |
| `interest_bearing_debt` | Currency |

**Cash Flow ratios (legacy, may be blank):**
| Field | Type |
|-------|------|
| `ocf_rev` | Number |
| `fcf_rev` | Number |
| `ncf_rev` | Number |

#### Table: `income_statement_data`

**Metadata fields:** Same as balance_sheet_data (company, period, publication_status, etc.)

**Ratio fields (pre-computed on upload):**
| Field | Type |
|-------|------|
| `gpm` | Number (decimal, e.g., 0.35 = 35%) |
| `opm` | Number |
| `npm` | Number |
| `rev_admin_employee` | Number |
| `ebitda_margin` | Number |
| `ebitda` | Currency |
| `ebitda_000` | Currency (in thousands) |
| `sales_assets` | Number |

**Revenue Streams:**
| Field | Type |
|-------|------|
| `intra_state_hhg` | Currency |
| `local_hhg` | Currency |
| `inter_state_hhg` | Currency |
| `office_industrial` | Currency |
| `warehouse` | Currency |
| `warehouse_handling` | Currency |
| `international` | Currency |
| `packing_unpacking` | Currency |
| `booking_royalties` | Currency |
| `special_products` | Currency |
| `records_storage` | Currency |
| `military_dpm_contracts` | Currency |
| `distribution` | Currency |
| `hotel_deliveries` | Currency |
| `other_revenue` | Currency |
| `total_revenue` | Currency |

**Cost of Revenue:**
| Field | Type |
|-------|------|
| `direct_wages` | Currency |
| `vehicle_operating_expenses` | Currency |
| `packing_warehouse_supplies` | Currency |
| `oo_exp_intra_state` | Currency |
| `oo_inter_state` | Currency |
| `oo_oi` | Currency |
| `oo_packing` | Currency |
| `oo_other` | Currency |
| `claims` | Currency |
| `other_trans_exp` | Currency |
| `depreciation` | Currency |
| `lease_expense_rev_equip` | Currency |
| `rent` | Currency |
| `other_direct_expenses` | Currency |
| `total_cost_of_revenue` | Currency |
| `gross_profit` | Currency |

**Operating Expenses (SG&A):**
| Field | Type |
|-------|------|
| `advertising_marketing` | Currency |
| `bad_debts` | Currency |
| `sales_commissions` | Currency |
| `contributions` | Currency |
| `computer_support` | Currency |
| `dues_sub` | Currency |
| `pr_taxes_benefits` | Currency |
| `equipment_leases_office_equip` | Currency |
| `workmans_comp_insurance` | Currency |
| `insurance` | Currency |
| `legal_accounting` | Currency |
| `office_expense` | Currency |
| `other_admin` | Currency |
| `pension_profit_sharing_401k` | Currency |
| `prof_fees` | Currency |
| `repairs_maint` | Currency |
| `salaries_admin` | Currency |
| `taxes_licenses` | Currency |
| `tel_fax_utilities_internet` | Currency |
| `travel_ent` | Currency |
| `vehicle_expense_admin` | Currency |
| `total_operating_expenses` | Currency |
| `operating_profit` | Currency |

**Non-Operating:**
| Field | Type |
|-------|------|
| `other_income` | Currency |
| `ceo_comp` | Currency |
| `other_expense` | Currency |
| `interest_expense` | Currency |
| `total_nonoperating_income` | Currency |
| `profit_before_tax_with_ppp` | Currency |
| `net_profit` | Currency |

**Labor Analysis (pre-computed):**
| Field | Type |
|-------|------|
| `admin_labor_cost` | Currency |
| `admin_labor_cost_pct_rev` | Number |
| `rev_producing_labor_expenses` | Currency |
| `rev_producing_labor_expenses_pct_rev` | Number |
| `labor_ratio` | Number |
| `tot_labor_expenses` | Currency |
| `tot_labor_expenses_pct_rev` | Number |
| `administrative_employees` | Number (count, not currency) |

#### Table: `wins`
| Field | Type |
|-------|------|
| `Name` | Text (Primary) |
| `period` | Linked Record → financial_periods |
| `win_text` | Long Text |
| `display_order` | Number |
| `is_active` | Checkbox |
| `status` | Single Select ('draft', 'published') |
| `created_date` | Date |

#### Table: `challenges`
| Field | Type |
|-------|------|
| `Name` | Text (Primary) |
| `period` | Linked Record → financial_periods |
| `challenge_text` | Long Text |
| `display_order` | Number |
| `is_active` | Checkbox |
| `status` | Single Select ('draft', 'published') |
| `created_date` | Date |

#### Table: `action_items`
| Field | Type |
|-------|------|
| `Name` | Text (Primary) |
| `period` | Linked Record → financial_periods |
| `action_item_text` | Long Text |
| `display_order` | Number |
| `is_active` | Checkbox |
| `status` | Single Select ('draft', 'published') |
| `created_date` | Date |

#### Table: `data_import_log`
| Field | Type |
|-------|------|
| `company` | Linked Record → companies |
| `import_description` | Text |
| `records_count` | Number |
| `status` | Single Select |
| `error_message` | Long Text |
| `imported_by` | Email |
| `import_date` | Date |

---

### Phase 2: Supabase Setup

#### Step 2A: Create New Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project (name: `bpc1-dashboard` or similar)
3. Choose a region close to your users
4. Set a strong database password
5. Wait for project to provision (~2 min)

#### Step 2B: Update `database_setup.sql` with BPC1 Companies

Before running the SQL, update lines 25-35 in `database_setup.sql` with the 10 BPC1 company names:

```sql
-- Replace these with BPC1 company names
INSERT INTO public.companies (airtable_company_name, display_name) VALUES
  ('Company1', 'Company1'),
  ('Company2', 'Company2'),
  -- ... etc for all 10
ON CONFLICT (airtable_company_name) DO NOTHING;
```

> **IMPORTANT:** The `airtable_company_name` values must match EXACTLY with what's in the Airtable `companies` table.

#### Step 2C: Run SQL Setup

1. In Supabase Dashboard → **SQL Editor**
2. Paste the contents of `database_setup.sql`
3. Run it
4. Verify: Run `SELECT * FROM companies ORDER BY display_name;` — should show 10 companies

#### Step 2D: Note Supabase Credentials

Go to **Settings → API** and copy:
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
```

---

### Phase 3: Code Changes (BPC2 → BPC1 Branding)

All references to "BPC2" or "BPC 2" need to change to "BPC1" or "BPC 1". Here is the complete list:

#### 3A: Main Dashboard Title & Banner
| File | Line(s) | Current | Change To |
|------|---------|---------|-----------|
| `financial_dashboard.py` | 623 | `BPC 2 Financial Dashboard` (banner) | `BPC 1 Financial Dashboard` |
| `financial_dashboard.py` | 638 | `Welcome to the 2025 BPC 2 Financial Analysis!` | `Welcome to the 2025 BPC 1 Financial Analysis!` |
| `financial_dashboard.py` | 818 | `page_title="BPC 2 - Financial Dashboard"` | `page_title="BPC 1 - Financial Dashboard"` |

#### 3B: Page Components (Banner Default)
| File | Line(s) | Current | Change To |
|------|---------|---------|-----------|
| `shared/page_components.py` | 16 | `banner_text="BPC 2 Financial Dashboard"` | `banner_text="BPC 1 Financial Dashboard"` |
| `shared/page_components.py` | 46 | `banner_text="BPC 2 Financial Dashboard"` | `banner_text="BPC 1 Financial Dashboard"` |

#### 3C: Data Input Page
| File | Line(s) | Current | Change To |
|------|---------|---------|-----------|
| `pages/data_input/data_input_page.py` | 46 | `banner_text="BPC 2 Financial Data"` | `banner_text="BPC 1 Financial Data"` |
| `pages/data_input/data_input_page.py` | 175 | `BPC2_Upload_Template.xlsx` (file path) | Update path if template renamed |
| `pages/data_input/data_input_page.py` | 179 | `file_name="BPC2_Upload_Template.xlsx"` | `file_name="BPC1_Upload_Template.xlsx"` |

#### 3D: Upload Templates
| File | Line(s) | Current | Change To |
|------|---------|---------|-----------|
| `pages/data_input/wins_challenges_admin.py` | 126 | `BPC2 W&C Upload Template` | `BPC1 W&C Upload Template` |
| `pages/data_input/wins_challenges_admin.py` | 150 | `BPC2_WC_Upload_Template.xlsx` | Update path if template renamed |
| `pages/data_input/wins_challenges_admin.py` | 156 | `file_name="BPC2_WC_Upload_Template.xlsx"` | `file_name="BPC1_WC_Upload_Template.xlsx"` |
| `create_upload_template.py` | 31 | `BPC2_Upload_Template.xlsx` | `BPC1_Upload_Template.xlsx` |
| `create_wc_upload_template.py` | 27 | `BPC2_WC_Upload_Template.xlsx` | `BPC1_WC_Upload_Template.xlsx` |
| `create_wc_upload_template.py` | 46 | `BPC2 Wins & Challenges Upload Template` | `BPC1 Wins & Challenges Upload Template` |

#### 3E: Auth & Login Pages
| File | Line(s) | Current | Change To |
|------|---------|---------|-----------|
| `pages/auth/login.py` | 198, 211 | `BPC2 Dashboard` | `BPC1 Dashboard` |
| `pages/auth/set_password.py` | 141, 154 | `Welcome to BPC2 Dashboard` | `Welcome to BPC1 Dashboard` |
| `pages/reset_landing.py` | 2 | `BPC2 Dashboard` | `BPC1 Dashboard` |
| `pages/reset_landing.py` | 42 | `page_title="Reset Password - BPC2 Dashboard"` | `BPC1 Dashboard` |

#### 3F: Email Notifications
| File | Line(s) | Current | Change To |
|------|---------|---------|-----------|
| `shared/email_notifications.py` | 42 | `BPC2 Dashboard` | `BPC1 Dashboard` |
| `shared/email_notifications.py` | 60, 115 | `BPC2 Dashboard \| Powered by IM AI Consultants` | `BPC1 Dashboard \| Powered by IM AI Consultants` |
| `shared/email_notifications.py` | 178 | `Successful Login to BPC2 Dashboard` | `BPC1 Dashboard` |
| `shared/email_notifications.py` | 181 | `Failed Login Attempt on BPC2 Dashboard` | `BPC1 Dashboard` |
| `shared/email_notifications.py` | 226 | `noreply@bpc2dashboard.com` | `noreply@bpc1dashboard.com` |

#### 3G: Password Reset Redirect URL
| File | Line | Current | Change To |
|------|------|---------|-----------|
| `shared/auth_utils.py` | 1017 | `https://bpc2-dashboard.onrender.com/reset_landing` | Deployment URL TBD (update after deploying) |

#### 3H: Group Ratios Function Name
| File | Line(s) | Current | Change To |
|------|---------|---------|-----------|
| `pages/group_pages/group_ratios.py` | 190-191 | `calculate_bpc2_average` | `calculate_group_average` (or keep as-is, internal only) |
| `pages/company_pages/company_ratios.py` | 643, 696, 734, 776 | `calculate_bpc2_average` | Match whatever group_ratios uses |

#### 3I: Docstrings (low priority, cosmetic)
| File | Current |
|------|---------|
| `pages/company_pages/company_income_statement.py:4` | `Atlas BPC 2 Financial Dashboard` |
| `pages/company_pages/company_cash_flow.py:4` | `Atlas BPC 2 Financial Dashboard` |
| `pages/company_pages/company_wins_challenges.py:4` | `Atlas BPC 2 Financial Dashboard` |
| `pages/company_pages/company_actuals.py:4` | `Atlas BPC 2 Financial Dashboard` |
| `pages/company_pages/company_value.py:4` | `Atlas BPC 2 Financial Dashboard` |
| `pages/resources/glossary_page.py:4` | `Atlas BPC 2 Financial Dashboard` |

#### 3J: Template Files to Rename
```
bpc_upload_template/BPC2_Upload_Template.xlsx      → BPC1_Upload_Template.xlsx
bpc_upload_template/BPC2_Upload_Template_TEST.xlsx  → BPC1_Upload_Template_TEST.xlsx
bpc_upload_template/BPC2_WC_Upload_Template.xlsx    → BPC1_WC_Upload_Template.xlsx
```

---

### Phase 4: Environment Configuration

#### Step 4A: Create `.env` File

```bash
# In /Users/adi/Documents/imai_codebases/bpc1-dashboard/
cp .env.example .env
```

Then fill in:
```env
# Airtable (from Phase 1)
AIRTABLE_PAT=pat_from_step_1D
AIRTABLE_BASE_ID=app_from_step_1E

# Supabase (from Phase 2)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# SMTP (use same Zoho config as BPC2)
SMTP_HOST=smtp.zoho.com
SMTP_USER=<your_email>
SMTP_PASSWORD=<your_password>
SMTP_FROM_EMAIL=<your_email>
```

---

### Phase 5: Deployment

#### Step 5A: Deploy to Render (or Streamlit Cloud)

1. Create new Web Service on Render
2. Connect to `adityarbhat/bpc1-dashboard` repo
3. Settings:
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Add all environment variables from `.env` as Render secrets
5. Deploy

#### Step 5B: Update Password Reset URL

After deployment, update `shared/auth_utils.py` line 1017 with the actual deployment URL:
```python
"redirect_to": "https://YOUR-BPC1-URL.onrender.com/reset_landing"
```

Commit and redeploy.

---

### Phase 6: User Setup

1. Create super_admin user via Supabase Auth dashboard or `create_super_admin.py`
2. Log in to the deployed dashboard
3. Go to Admin → User Management
4. Create company_user accounts for each of the 10 companies
5. Test: each user should only see their own company

---

## Important Notes

- **Percentages:** Airtable stores as decimals (0.35 = 35%). The code handles conversion.
- **Linked Records:** Company and period fields in financial data tables are linked records (return arrays).
- **Publication Workflow:** Data goes through submitted → published states. Only published data shows on dashboard pages.
- **Caching:** Dashboard caches Airtable data for 30 minutes. Use the refresh button or wait for cache expiry.
- **Same branding:** Atlas Van Lines theme (blue `#025a9a`) is kept — only "BPC 2" text changes to "BPC 1".

---

## Quick Reference: Files to Modify

```
database_setup.sql                              # Company names (Phase 2B)
.env                                            # Credentials (Phase 4A)
financial_dashboard.py                          # Title/banner (Phase 3A)
shared/page_components.py                       # Banner default (Phase 3B)
shared/auth_utils.py                            # Reset URL (Phase 3G)
shared/email_notifications.py                   # Email branding (Phase 3F)
pages/auth/login.py                             # Login title (Phase 3E)
pages/auth/set_password.py                      # Set password title (Phase 3E)
pages/reset_landing.py                          # Reset page title (Phase 3E)
pages/data_input/data_input_page.py             # Upload page banner (Phase 3C)
pages/data_input/wins_challenges_admin.py       # W&C template refs (Phase 3D)
pages/group_pages/group_ratios.py               # Function name (Phase 3H)
pages/company_pages/company_ratios.py           # Function import (Phase 3H)
create_upload_template.py                       # Template output path (Phase 3D)
create_wc_upload_template.py                    # Template output path (Phase 3D)
bpc_upload_template/*.xlsx                      # Rename files (Phase 3J)
```
