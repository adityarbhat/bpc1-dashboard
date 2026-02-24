# Course Plan: Building Production-Ready Streamlit Dashboards with Supabase

## Course Overview

**Title:** Building Production-Ready Streamlit Dashboards with Supabase
**Subtitle:** Master enterprise-grade authentication, session management, and reusable component patterns
**Target Audience:** Intermediate to advanced Python programmers
**Duration:** ~9.5 hours
**Price Point:** $19.99
**Goal:** 500-1000 enrollments

**Marketing Angle:** "Don't just leave the coding to AI - learn the fundamentals so you can understand and fix the errors in your dashboard. Master the patterns that AI tools often get wrong."

---

## Module Structure (10 Modules, ~9.5 hours total)

### Module 1: Foundations and Project Setup (45 min)

**Key Concepts:**
- Streamlit's execution model (reruns on every interaction)
- Why this matters for authentication (session bleeding risks)
- `st.session_state` persistence behavior
- Supabase project setup (Auth + Database)
- Environment configuration (.env local, st.secrets production)
- Scalable project structure

**Hands-On:** Create Supabase project, set up skeleton app with `app.py`, `shared/`, `pages/`

**Pattern from codebase:** `shared/supabase_connection.py` - environment variable handling

---

### Module 2: Authentication Deep Dive (90 min)

**Key Concepts:**
- Multi-layer session validation architecture
- Cookie-based session persistence with `same_site='strict'`
- **Critical:** Why module-level globals cause session bleeding between users
- Token management with 5-minute expiry buffer
- "Paranoid verification" pattern (email, user_id, profile_id checks after login)
- Session hijacking prevention (cookie-session mismatch detection)
- Audit logging for security events

**Common AI Mistakes to Fix:**
- Storing auth state in module-level variables
- Missing cookie/session mismatch detection
- Not clearing all session state on logout
- Token refresh without error handling

**Hands-On:** Build complete login/logout system with session recovery

**Pattern from codebase:** `shared/auth_utils.py:47-66` (per-session cookie manager), `auth_utils.py:467-481` (paranoid verification)

---

### Module 3: Role-Based Access Control (60 min)

**Key Concepts:**
- User roles: `super_admin` vs `company_user`
- Permission functions: `is_super_admin()`, `can_upload_data()`
- Company-based data isolation with `get_user_company_id()`
- Page protection with `require_auth()` and `require_role()`
- Supabase Row-Level Security (RLS) integration

**Hands-On:** Create user_profiles table, implement permission checks, build admin-only page

**Pattern from codebase:** `auth_utils.py:717-822` (RBAC functions)

---

### Module 4: Reusable Component Architecture (75 min)

**Key Concepts:**
- Centralized page header pattern (banner, period selector, title)
- Modular CSS system (separate functions: `apply_base_styles`, `apply_layout_styles`, etc.)
- **Critical order:** header -> content -> `apply_all_styles()` (LAST)
- Sidebar patterns for different page types
- Button wrapper with active state indicator (`"▶ {label}"`)
- Navigation state management

**Hands-On:** Build `create_page_header()`, modular CSS system, sidebar navigation

**Pattern from codebase:** `shared/page_components.py:16-43`, `shared/css_styles.py`

---

### Module 5: Performance Optimization (60 min)

**Key Concepts:**
- `@st.cache_data(ttl=900)` for API calls
- When NOT to cache (auth state, user-specific data)
- Bulk fetch methods vs individual calls (15-20x faster)
- Lazy loading for heavy modules (export utilities)
- Cached client validation before reuse
- `st.spinner` for user feedback

**Hands-On:** Implement cached data fetching, build bulk fetch functions, add lazy loading

**Pattern from codebase:** Caching throughout, lazy loading in `financial_dashboard.py`

---

### Module 6: Dynamic Forms and Data Input (90 min)

**Key Concepts:**
- `st.file_uploader` with type restrictions
- `st.form()` for grouped submissions
- `st.data_editor` for interactive tables
- Form state initialization and clearing patterns
- **Critical:** Success messages OUTSIDE form context
- `st.rerun()` for state synchronization
- Widget key management (avoiding DuplicateWidgetID)

**Hands-On:** Build user creation form with proper state management and clearing

**Pattern from codebase:** `pages/admin/user_management.py:20-93` (form state), `:42-65` (clearing)

---

### Module 7: File Upload and Excel Parsing (60 min)

**Key Concepts:**
- Two-tier field matching (direct label mapping + normalized fallback)
- Excel parsing with pandas (`pd.read_excel`)
- Data validation (balance sheet equation, required fields)
- Progress feedback with `st.spinner`
- Error handling with user-friendly warnings

**Hands-On:** Build Excel template parser with validation

**Pattern from codebase:** `pages/data_input/excel_parser.py` (two-tier matching)

---

### Module 8: User Management System (60 min)

**Key Concepts:**
- User creation (manual password vs email invitation via `invite_user_by_email`)
- Profile creation in separate table (Supabase auth + user_profiles)
- Permission editing with role-based conditional fields
- Delete with confirmation pattern
- Admin-only page protection

**Hands-On:** Build complete user management page with CRUD operations

**Pattern from codebase:** `user_management.py:176-279` (user creation methods)

---

### Module 9: Draft/Publish Workflow (45 min)

**Key Concepts:**
- Publication status field pattern (`draft` -> `submitted` -> `published`)
- Data visibility control based on status
- Bulk publish operations (batch 10 records per API call)
- Admin approval workflows
- Cache invalidation after publish

**Hands-On:** Implement draft submission and admin publish dashboard

**Pattern from codebase:** `user_management.py:375-664` (publication workflow)

---

### Module 10: Page Template Generator & Capstone (90 min)

**Key Concepts:**
- Creating CLI skills/commands for page generation
- Template patterns for group pages vs company pages vs admin pages
- Capstone project integration

**Skill Command Output:**
```bash
python create_page.py --type group --name "Custom Analysis"
# Generates: pages/group_pages/group_custom_analysis.py with standard template
```

**Capstone Project:** "Team Task Manager" dashboard with:
- Full authentication
- RBAC (admin vs team member)
- Task CRUD with forms
- Excel import
- Draft/publish workflow
- User management

---

## Additional Concepts to Include (Identified Gaps)

1. **Error Boundary Patterns** - Graceful fallbacks when imports fail
2. **Navigation State Persistence** - Saving current_page to cookies
3. **CSS Specificity Battles** - Multiple fallback selectors for Streamlit's dynamic classes
4. **Login Page Isolation** - Hiding sidebar during auth flow
5. **Widget Key Management** - Avoiding DuplicateWidgetID errors
6. **Multi-Tab Handling** - Detecting multiple browser tabs
7. **Deployment** - Render/Streamlit Cloud configuration

---

## Platform Comparison & Recommendation

### Option 1: Udemy (RECOMMENDED for your goals)

**Pros:**
- Built-in marketplace with massive traffic (200M+ users)
- Discovery - students find you organically
- No monthly fees to publish
- Trust factor for new creators
- Perfect for $19.99 price point (Udemy's sweet spot)

**Cons:**
- Keep only 37% from organic sales ($7.40 per sale)
- Keep 97% from your own marketing ($19.40 per sale)
- Heavy competition in programming category
- Limited community features
- Frequent deep discounts hurt perceived value

**Math for 500-1000 enrollments:**
- If 50% organic, 50% your marketing: ~$13.40 avg per sale
- 500 enrollments = ~$6,700
- 1000 enrollments = ~$13,400

### Option 2: Skool.com

**Pros:**
- Keep 100% of revenue (minus payment processing ~3%)
- Built-in community features
- Gamification for engagement
- Full control over pricing

**Cons:**
- $99/month fee ($1,188/year)
- **Subscription-only model** - no one-time $19.99 option
- Zero built-in discovery - you drive ALL traffic
- Smaller brand recognition
- Better suited for $29-99/month memberships

**Why NOT Skool for this course:**
- Your $19.99 one-time price doesn't work with Skool's subscription model
- You'd need to charge monthly, changing your entire business model
- No marketplace discovery means heavy marketing investment

### Option 3: Teachable/Thinkific

**Pros:**
- Keep 90-100% of revenue (depending on plan)
- One-time purchase model works
- Professional course experience
- Full branding control

**Cons:**
- $36-149/month depending on features
- Zero marketplace discovery
- Must build audience yourself
- Transaction fees on lower plans

### Recommendation: Start with Udemy

For your specific goals ($19.99, 500-1000 enrollments, technical content):

1. **Launch on Udemy first** - leverage their marketplace for discovery
2. **Build email list** from Udemy students
3. **Promote your own Udemy link** (97% revenue) via:
   - YouTube tutorials (free content -> course upsell)
   - Dev.to / Medium technical articles
   - Reddit (r/streamlit, r/learnpython)
   - Twitter/X developer community
4. **Later:** Consider Teachable for premium version ($49-99) once you have audience

---

## Success Strategy for 500-1000 Enrollments

1. **Pre-launch:** Create 3-5 free YouTube videos on Streamlit auth basics
2. **SEO:** Target "Streamlit authentication tutorial", "Streamlit Supabase"
3. **Udemy optimization:** Strong title, good thumbnail, first 5 reviews critical
4. **Cross-promotion:** Link from GitHub repos, Stack Overflow answers
5. **Timing:** Launch during Udemy sale periods for visibility boost

---

## Critical Files Reference (from BPC2 Dashboard)

| File | Module | Purpose |
|------|--------|---------|
| `shared/auth_utils.py` | 2, 3 | Authentication patterns |
| `shared/supabase_connection.py` | 1, 2 | Client management |
| `shared/page_components.py` | 4 | Reusable components |
| `shared/css_styles.py` | 4 | Modular CSS system |
| `pages/admin/user_management.py` | 6, 8, 9 | Forms, user mgmt, workflows |
| `pages/data_input/excel_parser.py` | 7 | Excel parsing patterns |
| `financial_dashboard.py` | 4 | Routing, sidebar, page structure |

---

## Verification Plan

After creating course content:
1. Build sample project following only the course materials
2. Test all code samples work with current Streamlit/Supabase versions
3. Have 2-3 beta testers (intermediate Python devs) complete course
4. Verify capstone project is completable in stated time

---

## Sources

Platform comparison research:
- [Best Online Course Platform Comparison Guide](https://jdmeier.com/course-platform-comparison/)
- [Skool Community Platform Review 2025](https://www.globalselfpublishing.com/post/skool-community-platform-review)
- [Best Udemy Alternatives for Course Creators](https://www.wp-tonic.com/best-udemy-alternatives-for-course-creators/)
- [Udemy Alternatives 2026 - Best Sites To Sell Online Courses](https://www.learningrevolution.net/alternative-to-udemy/)
