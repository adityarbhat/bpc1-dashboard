# Personalized Learning Plan: Master Your BPC Dashboard Codebase

## About This Plan

This is your personalized roadmap for deeply understanding the BPC Dashboard codebase. Since you built this, the goal isn't to learn from scratch but to **systematically cement your knowledge** of each major system so you can maintain, extend, and teach it confidently.

---

## Your Dashboard at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    BPC Dashboard Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PRESENTATION LAYER                                              │
│  ├── Company Pages (8 pages)                                    │
│  │   ├── Ratios, Balance Sheet, Income Statement               │
│  │   ├── Cash Flow, Labor Cost, Value, Actuals                 │
│  │   └── Wins & Challenges                                      │
│  └── Group Pages (8 pages)                                      │
│      ├── Same analysis + Export page                            │
│      └── Used for 10-company comparison                         │
│                                                                  │
│  DATA LAYER                                                      │
│  ├── Airtable Connection (cached, bulk fetching)               │
│  ├── Cash Flow Utils (OCF/FCF/NCF calculations)                │
│  └── Data Transformation (YoY, formatting)                      │
│                                                                  │
│  INPUT/OUTPUT                                                    │
│  ├── Excel Parser (IS/BS template)                              │
│  ├── W&C Parser (Wins & Challenges template)                    │
│  ├── Export Utils (7-sheet professional Excel)                  │
│  └── Publication Control (draft/publish workflow)               │
│                                                                  │
│  SECURITY LAYER                                                  │
│  ├── Auth Utils (Supabase + cookies + session)                  │
│  ├── Role-Based Access (super_admin, company_user)              │
│  ├── Audit Logging (all security events)                        │
│  └── Email Notifications (login alerts)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Week-by-Week Learning Plan

### Week 1: Foundation Refresh

**Goal:** Reconnect with the core architecture patterns

**You'll build:** A mini company dashboard that fetches data, remembers selections, and displays gauges.

---

**Day 1-2: Airtable Integration**

| Read | Then Do |
|------|---------|
| `01-airtable-integration.md` | **Exercise 01** → `exercises/module_1/01_airtable_essentials.md` |

- [ ] Read the documentation first
- [ ] Complete Exercise 01: Build `get_company_ratio()` function
- [ ] Explore `shared/airtable_connection.py` - trace how your function connects

---

**Day 3-4: Session State & Navigation**

| Read | Then Do |
|------|---------|
| `03-session-state-navigation.md` | **Exercise 02** → `exercises/module_1/02_session_state_essentials.md` |

- [ ] Read the documentation first
- [ ] Complete Exercise 02: Add company selector with persistence
- [ ] Your mini dashboard now has a dropdown that remembers selections

---

**Day 5-7: Plotly Visualizations**

| Read | Then Do |
|------|---------|
| `04-plotly-visualizations.md` | **Exercise 03** → `exercises/module_1/03_plotly_essentials.md` |
| `feature-deep-dives/gauge-charts-implementation.md` | |

- [ ] Read both documentation files
- [ ] Complete Exercise 03: Display ratio as gauge chart
- [ ] Your mini dashboard is now complete!

---

**Week 1 Checkpoint:**

Run your `mini_dashboard.py` - you should have:
- [x] Company dropdown that persists across interactions
- [x] Data fetched from Airtable
- [x] Color-coded gauge chart

You can now explain how data flows from Airtable → session state → Plotly charts.

---

### Week 2: Security Deep Dive

**Goal:** Fully understand the authentication system you built

**Day 1-2: Authentication Architecture**
- [ ] Read `authentication-security.md`
- [ ] Trace the login flow step by step in `shared/auth_utils.py`
- [ ] Find: Where exactly does session isolation happen?
- [ ] Find: What prevents session bleeding between users?

**Day 3-4: Cookie & Token Management**
- [ ] Understand: `attempt_session_recovery()` logic
- [ ] Understand: `validate_session_consistency()` checks
- [ ] Trace: What happens when a token expires mid-session?
- [ ] Exercise: Add logging to see token refresh in action

**Day 5-7: Audit & Email System**
- [ ] Trace all places `log_audit_event()` is called
- [ ] Read `shared/email_notifications.py`
- [ ] Complete **Challenge 7** (Session timeout)
- [ ] Review: `pages/auth/*` password reset flow

**Checkpoint:** You should be able to whiteboard the complete auth flow and explain every security decision.

---

### Week 3: Data Pipeline Mastery

**Goal:** Own the upload and publication system

**Day 1-2: Excel Upload System**
- [ ] Read `excel-upload-system.md`
- [ ] Trace parsing: `excel_parser.py` label mappings
- [ ] Trace validation: `data_validator.py` checks
- [ ] Find: How does overwrite logic work?

**Day 3-4: Publication Control**
- [ ] Read `publication-control.md`
- [ ] Trace: How does `publication_status` filter queries?
- [ ] Find: Where is draft data hidden from users?
- [ ] Complete **Challenge 10** (Draft preview)

**Day 5-7: W&C System**
- [ ] Read `pages/data_input/wins_challenges_manager.py`
- [ ] Trace: CRUD operations for W&C
- [ ] Trace: The draft → publish workflow
- [ ] Complete **Challenge 9** (Upload progress tracker)

**Checkpoint:** You should be able to trace data from Excel upload through validation, storage, and publication.

---

### Week 4: Export & Cash Flow

**Goal:** Master the export system and financial calculations

**Day 1-2: Excel Export System**
- [ ] Read `excel-export-system.md`
- [ ] Trace lazy loading: When are dependencies imported?
- [ ] Find: How does color coding match web display?
- [ ] Complete **Challenge 8** (Add summary sheet)

**Day 3-4: Cash Flow Calculations**
- [ ] Read `cash-flow-calculations.md`
- [ ] Work through OCF/FCF/NCF formulas on paper
- [ ] Trace: `cash_flow_utils.py` calculation logic
- [ ] Verify: Match calculations against a real company's data

**Day 5-7: Trend Analysis**
- [ ] Read `yoy-calculations.md` and `value-trend-analysis.md`
- [ ] Complete **Challenge 11** (Cash flow sparklines)
- [ ] Build: A custom 5-year trend table for any metric

**Checkpoint:** You should be able to explain every formula and export every data point correctly.

---

### Week 5: Component Architecture

**Goal:** Understand the reusable component system

**Day 1-2: CSS & Styling**
- [ ] Read `05-reusable-components.md`
- [ ] Map: All CSS classes in `shared/css_styles.py`
- [ ] Find: How does Atlas branding get applied?
- [ ] Experiment: Change a color theme variable

**Day 3-4: Page Components**
- [ ] Explore `shared/page_components.py`
- [ ] Find: How does `create_page_header()` work?
- [ ] Find: Why must header come before `apply_all_styles()`?
- [ ] Complete **Challenge 2** (Metric card component)

**Day 5-7: Error Handling**
- [ ] Read `07-error-handling.md`
- [ ] Find: All `try/except` patterns in the codebase
- [ ] Find: How are errors displayed to users?
- [ ] Exercise: Add graceful error handling to a new feature

**Checkpoint:** You should be able to create a new page following all architectural patterns.

---

### Week 6: Performance & Optimization

**Goal:** Understand what makes the dashboard fast

**Day 1-2: Caching Strategies**
- [ ] Read `02-performance-optimization.md`
- [ ] Map: All `@st.cache_data` decorators and their TTLs
- [ ] Find: What's the API call reduction from bulk fetching?
- [ ] Experiment: Measure page load with/without caching

**Day 3-4: Bulk Fetching**
- [ ] Find all `get_*_bulk` methods in `airtable_connection.py`
- [ ] Trace: How bulk fetching works for group pages
- [ ] Compare: Individual vs bulk API call patterns

**Day 5-7: Lazy Loading**
- [ ] Find: Where is lazy loading used?
- [ ] Trace: Export utils lazy import chain
- [ ] Measure: Import time for export page vs other pages
- [ ] Complete **Challenge 4** (Trend sparklines)

**Checkpoint:** You should be able to explain every performance optimization decision.

---

### Week 7: Integration & Capstone

**Goal:** Tie everything together

**Day 1-3: Full Page Build**
- [ ] Complete **Bonus Challenge** (Custom comparison page)
- [ ] Use: Auth, data fetching, caching, charts, export
- [ ] Follow: All architectural patterns

**Day 4-5: Code Review Simulation**
- [ ] Pick 3 random files and explain every line
- [ ] Identify: Any code you'd refactor differently now
- [ ] Document: Any "gotchas" you discover

**Day 6-7: Teach It**
- [ ] Write a 5-minute explanation of the dashboard for a new developer
- [ ] Create a diagram of your favorite pattern
- [ ] Add comments to any confusing code sections

**Final Checkpoint:** You should be able to onboard a new developer to this codebase.

---

## Quick Reference: Key Files

| System | Primary File | Support Files |
|--------|--------------|---------------|
| **Auth** | `shared/auth_utils.py` | `supabase_connection.py`, `email_notifications.py` |
| **Data** | `shared/airtable_connection.py` | `cash_flow_utils.py` |
| **Upload** | `pages/data_input/excel_parser.py` | `data_validator.py`, `data_uploader.py` |
| **Export** | `shared/export_utils.py` | `excel_formatter.py` |
| **Publish** | `pages/admin/user_management.py` | `wins_challenges_manager.py` |
| **Charts** | `shared/chart_utils.py` | `page_components.py` |
| **Styles** | `shared/css_styles.py` | `.streamlit/config.toml` |

---

## How to Use This Plan

1. **Set aside 1-2 hours daily** - consistency beats intensity
2. **Read docs first, then code** - context helps understanding
3. **Complete exercises** - active learning beats passive reading
4. **Take notes** - write down insights and gotchas
5. **Teach it** - explaining forces understanding

---

## Progress Tracker

```
Week 1: Foundation Refresh      [ ] [ ] [ ] [ ] [ ] [ ] [ ]
Week 2: Security Deep Dive      [ ] [ ] [ ] [ ] [ ] [ ] [ ]
Week 3: Data Pipeline           [ ] [ ] [ ] [ ] [ ] [ ] [ ]
Week 4: Export & Cash Flow      [ ] [ ] [ ] [ ] [ ] [ ] [ ]
Week 5: Components              [ ] [ ] [ ] [ ] [ ] [ ] [ ]
Week 6: Performance             [ ] [ ] [ ] [ ] [ ] [ ] [ ]
Week 7: Integration             [ ] [ ] [ ] [ ] [ ] [ ] [ ]
```

---

## After 7 Weeks, You Will...

- Confidently explain any part of the codebase
- Know where to look when debugging any issue
- Understand every security decision and why it matters
- Be able to extend the dashboard with new features
- Onboard other developers to the codebase
- Have a documented reference for future maintenance

---

*Start with Week 1, Day 1. One step at a time!*
