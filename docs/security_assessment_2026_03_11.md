# BPC1 Dashboard — Security Assessment Report

**Date:** 2026-03-11
**Scope:** Full application security review
**Framework:** Streamlit (Python) + Supabase Auth + Airtable API
**Assessor:** Automated code review (Claude)

---

## Executive Summary

The BPC1 Dashboard has **several strong security practices** already in place — per-session cookie isolation, profile ID validation, comprehensive audit logging, XSRF protection, and proper `.gitignore` exclusions. However, the assessment identified **4 critical/high findings** that should be addressed promptly, primarily around Airtable query injection, client-side-only RBAC enforcement, cross-user data exposure in exports, and a debug line leaking auth tokens.

---

## Findings

### FINDING-01 | CRITICAL | Airtable Formula Injection via Unsanitized User Input

- **Description:** Company names and period values are interpolated directly into Airtable `filterByFormula` query strings without escaping. Single quotes in user-controlled values can break out of the formula and alter query logic.
- **Location:**
  - `shared/airtable_connection.py` — lines 86, 125, 180, 267, 383, 419, 654
  - `pages/data_input/wc_uploader.py` — line 159
  - `pages/data_input/wins_challenges_manager.py` — lines 34, 380, 428
  - `pages/admin/user_management.py` — lines 805, 834
  - `data_transformation_bs.py` — lines 357, 406
  - `data_transformation_is.py` — lines 361, 410
- **Impact:** An attacker with a crafted company name (e.g., `Company', TRUE(), '`) could bypass filters and access other companies' financial records, or cause Airtable errors that leak metadata.
- **Proof of Concept:**
  ```python
  # Current vulnerable pattern:
  filter_formula = f"AND({{company}}='{company_name}',{{period}}='{period}')"

  # Injected company_name = "Acme', TRUE(), '"
  # Produces: AND({company}='Acme', TRUE(), '',{period}='2024 Annual')
  # → TRUE() bypasses the company filter
  ```
- **Remediation:**
  ```python
  def escape_airtable_value(value: str) -> str:
      """Escape single quotes for Airtable formula injection prevention."""
      if not isinstance(value, str):
          return str(value)
      return value.replace("'", "\\'")

  # Usage:
  safe_name = escape_airtable_value(company_name)
  safe_period = escape_airtable_value(period)
  filter_formula = f"AND({{company}}='{safe_name}',{{period}}='{safe_period}')"
  ```
  Additionally, validate `company_name` against the known company list before using it in any query.
- **Effort:** 2-3 hours (create helper function, apply to all query sites)

---

### FINDING-02 | HIGH | RBAC Enforcement is Client-Side Only

- **Description:** Role checks (`require_role()`, `can_upload_data()`, `is_super_admin()`) read from `st.session_state.user_profile` and call `st.stop()` to halt rendering. However, there is no server-side enforcement at the data layer — Airtable API calls use a single master PAT regardless of the caller's role.
- **Location:**
  - `shared/auth_utils.py` — lines 717-764 (`require_role`), 766-782 (`can_upload_data`)
  - `pages/data_input/data_input_page.py` — lines 37-41 (upload gate)
  - `pages/data_input/data_uploader.py` — lines 39-98 (no re-check before upload)
- **Impact:** A `company_user` role cannot be promoted to `super_admin` via the UI alone (Supabase RLS protects the `user_profiles` table). However, the Airtable data layer has zero per-user access control — if a user can call any Airtable-fetching function with an arbitrary `company_name`, they get that company's data.
- **Remediation:**
  1. In every data-fetching function, validate that the requesting user's `company_id` matches the requested `company_name` (or that the user is `super_admin`).
  2. In upload functions, re-validate `can_upload_data` and company assignment before writing to Airtable.
  ```python
  def validate_company_access(company_name: str) -> bool:
      """Verify current user has access to this company's data."""
      profile = st.session_state.get('user_profile', {})
      if profile.get('role') == 'super_admin':
          return True
      user_company = profile.get('company_name')
      return user_company == company_name
  ```
- **Effort:** 4-6 hours (add validation layer, apply to all data access paths)

---

### FINDING-03 | HIGH | Cross-Company Data Exposure in Group Exports

- **Description:** The multi-sheet Excel export (`shared/export_utils.py`) fetches ALL companies' financial data for the selected period without filtering by the logged-in user's company assignment. A `company_user` can download every company's ratios, balance sheets, and income statements.
- **Location:**
  - `shared/export_utils.py` — lines 85-91
  - Group page extract functions called without user context
- **Impact:** Complete financial data exposure across all 10 companies to any authenticated user.
- **Remediation:** Either restrict group export to `super_admin` only, or filter exported data to only the requesting user's company.
  ```python
  if not is_super_admin():
      st.error("Access denied. Group exports require admin privileges.")
      st.stop()
  ```
- **Effort:** 1 hour

---

### FINDING-04 | HIGH | Debug Statement Leaks Auth Tokens in UI

- **Description:** A `st.write()` debug line in the login page displays all query parameters (which may contain access tokens, refresh tokens, or reset tokens) directly in the browser.
- **Location:** `pages/auth/login.py` — line 166
- **Impact:** Auth tokens visible in the browser UI, potentially captured by screen sharing, screenshots, or shoulder surfing.
- **Remediation:** Delete the line or wrap in a dev-only flag:
  ```python
  # DELETE THIS LINE:
  # st.write(f"Debug - Query params: {dict(st.query_params)}")
  ```
- **Effort:** 5 minutes

---

### FINDING-05 | MEDIUM | JWT Tokens Moved from Hash to Query String

- **Description:** JavaScript in the login page converts URL hash fragments (which are NOT sent to the server or logged) into query string parameters (which ARE logged in browser history, server logs, and Referer headers).
- **Location:** `pages/auth/login.py` — lines 170-185
- **Impact:** Password reset tokens leak into browser history and potentially server logs.
- **Remediation:** Keep tokens in hash fragments and read them client-side, or use Supabase PKCE flow exclusively (which the app already supports as a primary path).
- **Effort:** 2 hours

---

### FINDING-06 | MEDIUM | No Formula Injection Detection in Excel Uploads

- **Description:** When users upload Excel files, cell values (especially text fields like line item names) are not checked for formula injection patterns (`=`, `+`, `-`, `@` prefixes). If exported data is later opened in Excel, malicious formulas could execute.
- **Location:** `pages/data_input/excel_parser.py` — lines 196-237, 310-351, 469-531
- **Impact:** A user could upload a file with `=cmd|' /c calc'!A1` in a text field. When another user exports and opens data containing that value, their Excel could execute commands.
- **Remediation:**
  ```python
  def sanitize_cell_value(value):
      """Strip formula injection prefixes from string values."""
      if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@'):
          return "'" + value  # Prefix with single quote to prevent formula execution
      return value
  ```
- **Effort:** 1-2 hours

---

### FINDING-07 | MEDIUM | No File Size Limit on Excel Uploads

- **Description:** `st.file_uploader()` accepts `.xlsx` files without enforcing a maximum size. An attacker could upload a very large file to cause memory exhaustion.
- **Location:** `pages/data_input/data_input_page.py` — line 201
- **Impact:** Denial of service via memory exhaustion on the Streamlit server.
- **Remediation:** Streamlit has a global config `server.maxUploadSize` (default 200MB). Set it to a reasonable value:
  ```toml
  # .streamlit/config.toml
  [server]
  maxUploadSize = 5
  ```
  Also validate after upload:
  ```python
  if uploaded_file.size > 5 * 1024 * 1024:
      st.error("File too large. Maximum 5MB allowed.")
  ```
- **Effort:** 15 minutes

---

### FINDING-08 | MEDIUM | Global Cache Keys Not User-Scoped

- **Description:** All `@st.cache_data(ttl=1800)` decorators in `airtable_connection.py` use function parameters (company_name, period) as cache keys but not user ID. While Streamlit sessions are isolated, the cache is global — if RBAC bypass occurs, cached data serves the wrong user.
- **Location:** `shared/airtable_connection.py` — all cached methods (11 functions)
- **Impact:** If an access control bypass exists (see FINDING-02), cached data amplifies the exposure window to the full 30-minute TTL.
- **Remediation:** This is a defense-in-depth concern. Fixing FINDING-02 (server-side RBAC) is the primary mitigation. Optionally, reduce TTL for company-specific data or add user_id to cache keys.
- **Effort:** 1 hour (if desired as additional hardening)

---

### FINDING-09 | MEDIUM | Unsafe HTML Rendering with Potential XSS

- **Description:** 50+ instances of `st.markdown(..., unsafe_allow_html=True)` throughout the codebase. Most render static HTML/CSS, but some embed dynamic values (company names, financial figures) without HTML escaping.
- **Location:** `pages/data_input/data_input_page.py`, `financial_dashboard.py`, `pages/auth/login.py`, and others
- **Impact:** If a company name or data value ever contains `<script>` tags, it would execute in the browser. Current risk is low since company names come from Airtable (admin-controlled), but defense-in-depth recommends escaping.
- **Remediation:**
  ```python
  import html
  safe_name = html.escape(company_name)
  st.markdown(f"<h2>{safe_name}</h2>", unsafe_allow_html=True)
  ```
- **Effort:** 2-3 hours (audit all instances)

---

### FINDING-10 | MEDIUM | Error Messages Expose Airtable API Details

- **Description:** Airtable API error responses are displayed directly to users via `st.error()`, potentially leaking table names, field names, or API metadata.
- **Location:** `shared/airtable_connection.py` — lines 74, 113-117, 169-173, 665
- **Impact:** Information disclosure that aids reconnaissance.
- **Remediation:** Log detailed errors server-side; show generic messages to users:
  ```python
  logger.error(f"Airtable API error: {response.status_code} - {response.text}")
  st.error("Unable to fetch financial data. Please try again or contact support.")
  ```
- **Effort:** 1 hour

---

### FINDING-11 | MEDIUM | Logging Exposes PII

- **Description:** Auth debug logging includes email addresses, user IDs, full names, roles, and IP addresses via both `logger.info()` and raw `print()` statements.
- **Location:** `shared/auth_utils.py` — lines 160, 238, 263, 427, 430-445
- **Impact:** If logs are accessible (Render dashboard, log aggregation), PII exposure occurs.
- **Remediation:** Log only user ID (not email/name). Remove all `print()` debug statements. Use structured logging.
- **Effort:** 1-2 hours

---

### FINDING-12 | LOW | Hardcoded Redirect URL

- **Description:** The password reset flow uses a hardcoded production URL.
- **Location:** `shared/auth_utils.py` — line 1017
  ```python
  "redirect_to": "https://bpc1-dashboard.onrender.com/reset_landing"
  ```
- **Impact:** Breaks development/staging environments. Not a direct security vulnerability but a maintainability risk.
- **Remediation:** Use an environment variable: `os.getenv("RESET_REDIRECT_URL", "https://bpc1-dashboard.onrender.com/reset_landing")`
- **Effort:** 10 minutes

---

### FINDING-13 | LOW | Company Names in Browser Tab Titles

- **Description:** Selected company name appears in `st.set_page_config(page_title=...)`, visible in browser history and tab bar.
- **Location:** `pages/company_pages/company_wins_challenges.py`, `company_cash_flow.py`, `company_value.py`
- **Impact:** Minor information leakage via browser history.
- **Remediation:** Use generic titles: `page_title="Company Analysis"` instead of `f"{company_name} Analysis"`.
- **Effort:** 15 minutes

---

### FINDING-14 | LOW | Dependencies Not Pinned to Exact Versions

- **Description:** `requirements.txt` uses `>=` version specifiers instead of `==`, which could introduce breaking changes or vulnerable versions.
- **Location:** `requirements.txt`
- **Impact:** Potential for supply chain risk during deployment.
- **Remediation:** Generate a lock file: `pip freeze > requirements-lock.txt` and use pinned versions in production.
- **Effort:** 15 minutes

---

### FINDING-15 | INFO | Extension-Only File Type Validation

- **Description:** `st.file_uploader(type=['xlsx'])` only checks file extension, not MIME type or magic bytes.
- **Location:** `pages/data_input/data_input_page.py` — line 201
- **Impact:** Low — `pd.read_excel()` will fail on non-Excel files, but a crafted file exploiting openpyxl vulnerabilities could theoretically bypass.
- **Remediation:** Add magic byte check (PK header for xlsx ZIP files):
  ```python
  if uploaded_file.read(2) != b'PK':
      st.error("Invalid file format.")
  uploaded_file.seek(0)
  ```
- **Effort:** 15 minutes

---

## Summary Table

| ID | Severity | Title | Status |
|----|----------|-------|--------|
| FINDING-01 | CRITICAL | Airtable formula injection | Open |
| FINDING-02 | HIGH | RBAC enforcement is client-side only | Open |
| FINDING-03 | HIGH | Cross-company data exposure in exports | Open |
| FINDING-04 | HIGH | Debug statement leaks auth tokens | Open |
| FINDING-05 | MEDIUM | JWT tokens moved from hash to query string | Open |
| FINDING-06 | MEDIUM | No formula injection detection in uploads | Open |
| FINDING-07 | MEDIUM | No file size limit on uploads | Open |
| FINDING-08 | MEDIUM | Global cache keys not user-scoped | Open |
| FINDING-09 | MEDIUM | Unsafe HTML rendering (XSS risk) | Open |
| FINDING-10 | MEDIUM | Error messages expose API details | Open |
| FINDING-11 | MEDIUM | Logging exposes PII | Open |
| FINDING-12 | LOW | Hardcoded redirect URL | Open |
| FINDING-13 | LOW | Company names in browser tab titles | Open |
| FINDING-14 | LOW | Dependencies not pinned | Open |
| FINDING-15 | INFO | Extension-only file validation | Open |

---

## Top 3 Immediate Priorities

1. **Fix FINDING-01 (Airtable formula injection)** — Create an `escape_airtable_value()` helper and apply it everywhere user input enters a filter formula. Also whitelist-validate company names against the known company list. ~3 hours.

2. **Fix FINDING-03 + FINDING-04 (data exposure + debug leak)** — Delete the debug `st.write()` line immediately. Restrict group exports to `super_admin` role. ~1 hour combined.

3. **Fix FINDING-02 (server-side RBAC)** — Add a `validate_company_access(company_name)` check to all Airtable data-fetching and upload functions. This is the most labor-intensive fix but eliminates the entire class of cross-company access issues. ~4-6 hours.

---

## Supabase RLS Checklist

Based on `docs/fix_rls_policies.sql` and `database_setup.sql`:

| Table | RLS Enabled | Policies | Status |
|-------|-------------|----------|--------|
| `user_profiles` | Yes | Users can SELECT/UPDATE only their own row (`auth.uid() = id`) | Correct |
| `companies` | Yes | Any authenticated user can SELECT (needed for joins) | Acceptable |
| `audit_logs` | Yes | Only `service_role` can INSERT/SELECT (bypasses client access) | Correct |
| Airtable tables | N/A | Airtable has no RLS — access controlled by single master PAT | Risk (see FINDING-02) |

**Note:** Supabase RLS is properly configured for the three Supabase tables. The gap is that Airtable (the primary data store) has no per-user access control — all queries use the same PAT.

---

## Correctly Implemented (Do NOT Change)

These security practices are well-implemented and should be preserved:

1. **Per-session cookie manager** (`shared/auth_utils.py:47-66`) — Each Streamlit session gets its own `CookieManager()` instance, preventing the critical session-bleeding vulnerability in multi-user deployments.

2. **Profile ID validation after login** (`shared/auth_utils.py:416-424`) — After authentication, the system verifies the loaded profile's `id` matches the authenticated user's `id`, preventing profile hijacking.

3. **Comprehensive audit logging** (`shared/auth_utils.py:899-944`) — Login success, login failure, session recovery, and logout events are all logged with IP address, user context, and timestamps. Audit log table is restricted to `service_role` access only.

4. **XSRF protection enabled** (`.streamlit/config.toml:14`) — `enableXsrfProtection = true` is set.

5. **Cookie SameSite=Strict for auth cookies** (`shared/auth_utils.py:382-393`) — Access token, refresh token, and user ID cookies all use `same_site='strict'`.

6. **Query params cleared on logout** (`shared/auth_utils.py:600-603`) — Prevents re-authentication via stale URL parameters.

7. **Session mismatch detection** (`shared/auth_utils.py:156-182`) — Comprehensive validation comparing cookie user ID vs session state user ID, with session clearing on any mismatch.

8. **Secrets in .env / st.secrets, not hardcoded** — Credentials are loaded from environment variables with `st.secrets` fallback. `.env` is properly gitignored and was never committed.

9. **Admin client isolated for audit writes** (`shared/auth_utils.py:928`) — The Supabase admin client (service_role) is only used for audit log writes, not for general data access.

10. **No eval/exec/subprocess with user input** — No dangerous code execution patterns found anywhere in the codebase.
