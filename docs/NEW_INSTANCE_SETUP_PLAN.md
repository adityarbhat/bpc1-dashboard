# Plan: Create Separate Dashboard Instance for New Competition

**Estimated Time: 2-3 hours** (assuming infrastructure accounts are already created)

## Overview
Create a completely separate BPC dashboard for 10 different companies with isolated users.

**Decisions Made:**
- Codebase: Copy to new folder/repo
- Branding: Keep same Atlas Van Lines theme

## Approach: Copy Codebase to New Folder/Repo

Copy the entire codebase to a new repository/folder and deploy separately.

### What You Need to Create

| Service | Current Instance | New Instance |
|---------|-----------------|--------------|
| **Airtable Base** | Existing BPC2 base | NEW base (copy structure) |
| **Supabase Project** | Existing project | NEW project |
| **Deployment** | bpc2-dashboard.onrender.com | New URL on Render/Streamlit Cloud |
| **Git Repository** | Current repo | Copy or new repo |

---

## Step-by-Step Implementation

### Phase 1: Infrastructure Setup (~45 min)
1. **Create new Airtable base**
   - Copy table structure from existing base (or use template)
   - Tables needed: `companies`, `balance_sheet_data`, `income_statement_data`, `financial_periods`, `wins`, `challenges`, `action_items`
   - Populate with your 10 new company names
   - Generate new Personal Access Token (PAT)

2. **Create new Supabase project**
   - Go to supabase.com, create new project
   - Run `database_setup.sql` (modify company names first)
   - Note the new URL and API keys

### Phase 2: Code Setup (~30 min)
1. **Copy codebase**
   - Copy entire folder to new location, or
   - Create new git repo from existing code

2. **Update configuration files**

   **`.env` (create new)**:
   ```
   AIRTABLE_BASE_ID=<new_base_id>
   AIRTABLE_PAT=<new_pat>
   SUPABASE_URL=<new_supabase_url>
   SUPABASE_ANON_KEY=<new_anon_key>
   SUPABASE_SERVICE_KEY=<new_service_key>
   COOKIE_ENCRYPTION_KEY=<generate_new_key>
   APP_URL=<your_deployed_url>
   SMTP_HOST=smtp.zoho.com
   SMTP_USER=<your_email>
   SMTP_PASSWORD=<your_password>
   SMTP_FROM_EMAIL=<your_email>
   ```

3. **Update hardcoded values**

   | File | Line | Change |
   |------|------|--------|
   | `shared/auth_utils.py` | ~1017 | Update password reset redirect URL |
   | `shared/email_notifications.py` | Various | Update branding/footer text |
   | `database_setup.sql` | 25-35 | Replace 10 company names |
   | `.streamlit/config.toml` | Theme | Optional: change colors if different branding |
   | `financial_dashboard.py` | ~818 | Optional: change page title/icon |

### Phase 3: Deployment (~30 min)
1. Deploy to Render/Streamlit Cloud/Railway
2. Add all environment variables as secrets
3. Note the deployment URL
4. Update password reset URL in code with actual deployment URL
5. Redeploy

### Phase 4: User Setup (~15 min)
1. Create initial super_admin via Supabase dashboard OR first deployment
2. Login and use Admin > User Management to create company users
3. Assign each user to their company

---

## Files to Modify (Summary)

```
database_setup.sql          # Company names for Supabase
.env                        # All credentials (create new)
shared/auth_utils.py        # Password reset URL (line ~1017)
shared/email_notifications.py # Email branding (optional)
.streamlit/config.toml      # Theme colors (optional)
financial_dashboard.py      # Page title (optional)
```

---

## Verification Steps
1. Run locally with `streamlit run app.py`
2. Test login with super_admin
3. Verify Airtable data loads correctly
4. Test company user can only see their company
5. Test Excel upload workflow
6. Test password reset email flow

---

## Implementation Checklist

### Phase 1: Infrastructure Setup
- [ ] Create new Airtable base (copy structure, add 10 new companies)
- [ ] Generate new Airtable Personal Access Token (PAT)
- [ ] Create new Supabase project
- [ ] Modify `database_setup.sql` with new company names
- [ ] Run SQL setup in new Supabase project

### Phase 2: Code Setup
- [ ] Copy codebase to new folder/repo
- [ ] Create new `.env` with all new credentials
- [ ] Update `shared/auth_utils.py` line ~1017 (password reset URL placeholder)

### Phase 3: Deployment
- [ ] Deploy to Render/Streamlit Cloud
- [ ] Add environment variables as secrets
- [ ] Update password reset URL with actual deployment URL
- [ ] Redeploy

### Phase 4: User Setup
- [ ] Create super_admin user
- [ ] Create company users via Admin panel
- [ ] Test login and data isolation
