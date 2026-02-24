# Authentication System Implementation
## Technical Security Report for IT Review

**Project:** BPC Financial Dashboard
**Document Version:** 1.0
**Date:** November 5, 2025
**Classification:** Internal - For Client IT Review
**Prepared for:** IT Security Review Team

---

## Executive Summary

This document outlines the proposed authentication and authorization system for the BPC Financial Dashboard, hosted on Render and utilizing Supabase as the authentication and user management backend. The system implements role-based access control (RBAC) with company-level data segregation while maintaining read access to the dashboard for all authenticated users.

**Key Security Features:**
- Industry-standard JWT-based authentication
- bcrypt password hashing (cost factor 10)
- PostgreSQL Row-Level Security (RLS)
- Role-based access control (RBAC)
- Comprehensive audit logging
- Self-service password management
- TLS 1.2+ encryption for all data in transit

**Risk Assessment:** LOW to MEDIUM
**Compliance:** OWASP Top 10 aligned, NIST framework compatible

---

## 🎯 Project-Specific Simplifications

This implementation uses a **simplified architecture** tailored to the BPC Dashboard's specific requirements:

### **Key Simplifications:**

1. **Single Company per User**
   - Each user assigned to exactly ONE company
   - Simpler database schema (no multi-company join table)
   - Faster queries, easier to understand

2. **Manual User Creation Only**
   - No self-registration feature
   - Super admins create all user accounts
   - Tighter control over access

3. **Two-Role System**
   - **company_user** (95% of users): View all data, upload for assigned company only
   - **super_admin** (2 users): Full access to everything


4. **Email Service**
   - Supabase free tier (3 emails/hour) is sufficient
   - Low user count makes this viable
   - Can upgrade if needed in future

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Security Model](#2-security-model)
3. [Authentication Flows](#3-authentication-flows)
4. [Database Schema](#4-database-schema)
5. [Deployment Architecture](#5-deployment-architecture)
6. [Threat Model & Risk Mitigation](#6-threat-model--risk-mitigation)
7. [Compliance & Standards](#7-compliance--standards)
8. [Operational Security](#8-operational-security)
9. [Implementation Timeline](#9-implementation-timeline)
10. [Recommendations](#10-recommendations)

---

## 1. System Architecture

### 1.1 Current Architecture (No Authentication)

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ (unauthenticated access)
       ▼
┌─────────────────────┐
│  Streamlit App      │
│  (Render hosting)   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Airtable API       │
│  (Financial Data)   │
└─────────────────────┘
```

**Security Gaps:**
- ❌ No user authentication
- ❌ No access control
- ❌ Anyone with URL can view/modify all data
- ❌ No audit trail
- ❌ No user accountability

### 1.2 Proposed Architecture (With Authentication)

```
┌─────────────┐
│   Browser   │
│   (HTTPS)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  Streamlit App (Render)     │
│  ├─ Login/Logout UI         │
│  ├─ Session Management      │
│  ├─ Permission Checks       │
│  └─ Audit Logging           │
└──────┬──────────────────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────────┐
│  Supabase    │  │  Airtable API    │
│  ├─ Auth API │  │  ├─ Companies    │
│  ├─PostgreSQL│  │  ├─ Financials   │
│  ├─ RLS      │  │  └─ Wins/Challen.│
│  └─ Storage  │  └──────────────────┘
└──────────────┘
```

**Security Improvements:**
- ✅ JWT-based authentication
- ✅ Role-based authorization
- ✅ Company-level access control
- ✅ Complete audit trail
- ✅ User accountability
- ✅ Self-service password management

### 1.3 Component Responsibilities

| Component | Responsibility | Security Role |
|-----------|---------------|---------------|
| **Streamlit App** | UI, business logic, permission enforcement | Application-layer security |
| **Supabase Auth** | User authentication, JWT issuance | Identity provider |
| **PostgreSQL** | User data, roles, permissions | Database-layer security (RLS) |
| **Airtable** | Financial data storage | Data persistence |
| **Render** | Hosting, SSL termination, DDoS protection | Infrastructure security |

---

## 2. Security Model

### 2.1 Authentication Mechanism

**Technology Stack:**
- **Supabase Auth** (Built on GoTrue - industry-standard OAuth 2.0 implementation)
- **JWT Tokens** for session management
- **bcrypt** for password hashing (10 rounds)

**Authentication Process:**

1. **User Login:**
   - User submits email/password via HTTPS
   - Streamlit sends credentials to Supabase Auth API
   - Supabase validates against bcrypt hash
   - Returns JWT access token (1 hour TTL) + refresh token (7 days TTL)
   - Tokens stored in server-side session (not exposed to browser)

2. **Session Management:**
   - Every page load validates JWT signature and expiry
   - Automatic token refresh using refresh token
   - Logout invalidates tokens server-side
   - Session timeout after 30 minutes of inactivity (configurable)

3. **Password Security:**
   - Minimum 8 characters (configurable)
   - Strength requirements: uppercase, lowercase, number, special char
   - bcrypt hashing with salt (cost factor 10 = 2^10 iterations)
   - Passwords never stored in plaintext or logged

**Token Structure (JWT):**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "authenticated",
  "iat": 1699200000,
  "exp": 1699203600,
  "iss": "https://[project].supabase.co/auth/v1"
}
```

### 2.2 Authorization Model (RBAC)

**Role Definitions:**

| Role | Dashboard Access | Data Upload | Wins/Challenges | User Management | Use Case |
|------|-----------------|-------------|-----------------|-----------------|----------|
| **company_user** | ✅ All companies | ✅ Assigned company ONLY | ❌ | ❌ | Company representatives (95% of users) |
| **super_admin** | ✅ Full access | ✅ ALL companies | ✅ ALL companies | ✅ Full access | System administrators (2 users) |

**Note:** Each user is assigned to exactly ONE company. No multi-company access for regular users.

**Permission Matrix:**

```
Action                          | company_user       | super_admin
--------------------------------|--------------------|--------------
View dashboard (all companies)  | ✅                  | ✅
Upload balance sheet data       | ✅ (own company)    | ✅ (all companies)
Upload income statement data    | ✅ (own company)    | ✅ (all companies)
Create/edit wins                | ❌                  | ✅
Create/edit challenges          | ❌                  | ✅
View audit logs                 | ❌ (own only)       | ✅ (all logs)
Manage users                    | ❌                  | ✅
Assign companies to users       | ❌                  | ✅
```

**Company Assignment Model**

Each user is assigned to exactly ONE company:

```
User: john@ace.com
└─ Company: ACE
   └─ can_upload_data: true

User: sarah@bisson.com
└─ Company: Bisson
   └─ can_upload_data: true

User: tom@coastal.com
└─ Company: Coastal
   └─ can_upload_data: false (read-only user)
```

**Super Admins are not assigned to any specific company** - they have access to all companies.

**Permission Enforcement (Defense in Depth):**

1. **Database Layer (PostgreSQL RLS):**
   - Row-Level Security policies prevent unauthorized database queries
   - Enforced at SQL level (cannot be bypassed by application)
   - Example: Users can only SELECT their own company assignments

2. **Application Layer (Streamlit):**
   - Permission checks before rendering UI components
   - Company dropdowns filtered to user's assignments
   - Buttons disabled/hidden for unauthorized actions
   - API calls validated against user permissions

3. **API Layer (Airtable):**
   - Application uses single API key (not user-specific)
   - Results filtered based on user's company assignments
   - Prevents data leakage through direct API manipulation

### 2.3 Data Security

**Encryption at Rest:**
- **Supabase PostgreSQL:** AES-256 encryption
- **Airtable:** AES-256 encryption (Airtable infrastructure)
- **Render Storage:** Encrypted volumes

**Encryption in Transit:**
- **TLS 1.2+** enforced for all connections
- **HTTPS only** (HTTP automatically redirects to HTTPS)
- **Certificate management:** Automatic via Render + Let's Encrypt
- **Perfect Forward Secrecy** enabled

**Credential Management:**

```bash
# Environment Variables (Render Dashboard - Encrypted at rest)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...  # Public key, safe for client-side
SUPABASE_SERVICE_KEY=eyJhbGc...  # Secret key, server-only, bypasses RLS
AIRTABLE_PAT=patXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXX
```

**Security Best Practices:**
- ✅ All secrets in environment variables (never hardcoded)
- ✅ `.env` file in `.gitignore` (never committed to Git)
- ✅ Separate credentials for dev/staging/production
- ✅ Regular credential rotation (quarterly recommended)
- ✅ Service keys restricted to server-side use only

### 2.4 Audit Logging

**Logged Events:**
- User login/logout (timestamp, IP address, user agent)
- Data uploads (user, company, file metadata, timestamp)
- Wins/challenges creation/modification (user, content, timestamp)
- User management actions (admin, target user, action, timestamp)
- Failed login attempts (email, IP, timestamp)
- Permission changes (admin, user, old/new permissions)

**Log Retention:**
- **Standard:** 90 days
- **Storage:** PostgreSQL table with indexes for fast queries

**Log Structure:**
```sql
audit_logs (
  id SERIAL PRIMARY KEY,
  user_id UUID,
  action TEXT,  -- e.g., 'login', 'upload_balance_sheet', 'create_win'
  resource TEXT,  -- e.g., 'auth', 'data_input', 'wins'
  company_id INTEGER,
  ip_address INET,
  user_agent TEXT,
  metadata JSONB,  -- Additional context
  timestamp TIMESTAMPTZ DEFAULT NOW()
)
```

**Access to Logs:**
- **wins_admin:** Can view logs related to wins/challenges
- **super_admin:** Full access to all audit logs
- **Export:** CSV/Excel export for compliance audits

---

## 3. Authentication Flows

### 3.1 User Login Flow

```
┌─────────┐                ┌─────────┐              ┌──────────┐
│ Browser │                │Streamlit│              │ Supabase │
└────┬────┘                └────┬────┘              └────┬─────┘
     │                          │                        │
     │  1. Navigate to login    │                        │
     ├─────────────────────────>│                        │
     │                          │                        │
     │  2. Enter email/password │                        │
     ├─────────────────────────>│                        │
     │                          │                        │
     │                          │  3. sign_in_with_      │
     │                          │     password()         │
     │                          ├───────────────────────>│
     │                          │                        │
     │                          │  4. Validate bcrypt    │
     │                          │     hash               │
     │                          │                        │
     │                          │  5. Generate JWT       │
     │                          │     tokens             │
     │                          │                        │
     │                          │  6. Return tokens      │
     │                          │<───────────────────────┤
     │                          │                        │
     │                          │  7. Fetch user profile │
     │                          │     + permissions      │
     │                          ├───────────────────────>│
     │                          │                        │
     │                          │  8. User data          │
     │                          │<───────────────────────┤
     │                          │                        │
     │  9. Store in session_    │                        │
     │     state (server-side)  │                        │
     │                          │                        │
     │  10. Redirect to         │                        │
     │      dashboard           │                        │
     │<─────────────────────────┤                        │
     │                          │                        │
     │  11. Log audit event     │                        │
     │                          ├───────────────────────>│
```

**Security Controls:**
- ✅ Rate limiting: 5 failed attempts → 15-minute lockout
- ✅ Passwords transmitted over HTTPS only
- ✅ JWT tokens never exposed to browser JavaScript
- ✅ Session cookies: `HttpOnly=true, Secure=true, SameSite=Strict`
- ✅ Login attempts logged (including failures)

### 3.2 Password Reset Flow (Self-Service)

```
┌─────────┐                ┌─────────┐              ┌──────────┐       ┌──────┐
│ Browser │                │Streamlit│              │ Supabase │       │Email │
└────┬────┘                └────┬────┘              └────┬─────┘       └──┬───┘
     │                          │                        │                │
     │  1. Click "Forgot        │                        │                │
     │     Password"            │                        │                │
     ├─────────────────────────>│                        │                │
     │                          │                        │                │
     │  2. Enter email address  │                        │                │
     ├─────────────────────────>│                        │                │
     │                          │                        │                │
     │                          │  3. reset_password_    │                │
     │                          │     for_email()        │                │
     │                          ├───────────────────────>│                │
     │                          │                        │                │
     │                          │  4. Generate secure    │                │
     │                          │     one-time token     │                │
     │                          │     (1 hour expiry)    │                │
     │                          │                        │                │
     │                          │  5. Send email         │                │
     │                          │     with reset link    │                │
     │                          │                        ├───────────────>│
     │                          │                        │                │
     │  6. "Check your email"   │                        │                │
     │<─────────────────────────┤                        │                │
     │                          │                        │                │
     │  [User clicks link in email: https://app.com/reset?token=xyz]     │
     │                          │                        │                │
     │  7. Open reset page      │                        │                │
     │     with token           │                        │                │
     ├─────────────────────────>│                        │                │
     │                          │                        │                │
     │  8. Enter new password   │                        │                │
     ├─────────────────────────>│                        │                │
     │                          │                        │                │
     │                          │  9. update_user()      │                │
     │                          │     with token         │                │
     │                          ├───────────────────────>│                │
     │                          │                        │                │
     │                          │  10. Validate token    │                │
     │                          │      + expiry          │                │
     │                          │                        │                │
     │                          │  11. Hash new password │                │
     │                          │      (bcrypt)          │                │
     │                          │                        │                │
     │                          │  12. Invalidate token  │                │
     │                          │                        │                │
     │                          │  13. Success response  │                │
     │                          │<───────────────────────┤                │
     │                          │                        │                │
     │  14. "Password updated,  │                        │                │
     │       please login"      │                        │                │
     │<─────────────────────────┤                        │                │
```

**Security Controls:**
- ✅ Reset tokens expire after 1 hour
- ✅ One-time use tokens (invalidated after successful reset)
- ✅ Email verification required before sending reset link
- ✅ Rate limiting: 3 reset requests per hour per email
- ✅ Password strength requirements enforced
- ✅ Audit log records password resets

**Manual Reset (Admin):**
If user cannot access email:
1. User contacts super admin
2. Admin verifies identity (phone call, alternative email, etc.)
3. Admin accesses Supabase dashboard
4. Admin triggers password reset for user
5. User receives email with reset link
6. Action logged in audit trail

### 3.3 Data Upload Authorization Flow

```
┌─────────┐                ┌─────────┐              ┌──────────┐       ┌─────────┐
│ Browser │                │Streamlit│              │ Supabase │       │Airtable │
└────┬────┘                └────┬────┘              └────┬─────┘       └────┬────┘
     │                          │                        │                   │
     │  1. Navigate to Upload   │                        │                   │
     │     Data page            │                        │                   │
     ├─────────────────────────>│                        │                   │
     │                          │                        │                   │
     │                          │  2. Verify JWT valid   │                   │
     │                          │     + not expired      │                   │
     │                          │                        │                   │
     │                          │  3. Query user's       │                   │
     │                          │     company            │                   │
     │                          │     assignments        │                   │
     │                          ├───────────────────────>│                   │
     │                          │                        │                   │
     │                          │  4. SELECT * FROM      │                   │
     │                          │     user_company_      │                   │
     │                          │     assignments        │                   │
     │                          │     WHERE user_id =    │                   │
     │                          │     current_user       │                   │
     │                          │     [RLS enforced]     │                   │
     │                          │                        │                   │
     │                          │  5. Return companies   │                   │
     │                          │     (ACE, Bisson)      │                   │
     │                          │<───────────────────────┤                   │
     │                          │                        │                   │
     │  6. Show dropdown with   │                        │                   │
     │     ONLY ACE, Bisson     │                        │                   │
     │     (not all 10 cos.)    │                        │                   │
     │<─────────────────────────┤                        │                   │
     │                          │                        │                   │
     │  7. User selects ACE     │                        │                   │
     │     + uploads file       │                        │                   │
     ├─────────────────────────>│                        │                   │
     │                          │                        │                   │
     │                          │  8. Verify permission: │                   │
     │                          │     can_upload_data    │                   │
     │                          │     = true for ACE     │                   │
     │                          ├───────────────────────>│                   │
     │                          │                        │                   │
     │                          │  9. Permission         │                   │
     │                          │     granted            │                   │
     │                          │<───────────────────────┤                   │
     │                          │                        │                   │
     │                          │  10. Parse + validate  │                   │
     │                          │      file data         │                   │
     │                          │                        │                   │
     │                          │  11. Upload to         │                   │
     │                          │      Airtable API      │                   │
     │                          ├───────────────────────────────────────────>│
     │                          │                        │                   │
     │                          │  12. Success           │                   │
     │                          │<───────────────────────────────────────────┤
     │                          │                        │                   │
     │                          │  13. Log audit event   │                   │
     │                          ├───────────────────────>│                   │
     │                          │                        │                   │
     │  14. "Upload successful" │                        │                   │
     │<─────────────────────────┤                        │                   │
```

**Security Controls:**
- ✅ Permission check before showing upload UI
- ✅ Server-side validation before Airtable API call
- ✅ Company dropdown restricted to user's assignments
- ✅ File type validation (Excel only)
- ✅ File size limit (10 MB)
- ✅ Data validation (required columns, data types)
- ✅ Audit log: user, company, file name, row count, timestamp

**Unauthorized Access Attempt:**
```
User tries to upload for "Mabeys" (not assigned)
    → GET /upload?company=mabeys
    → Server checks permissions
    → can_upload_data = false for Mabeys
    → HTTP 403 Forbidden
    → "You do not have permission to upload data for this company"
    → Audit log: attempted_unauthorized_upload
```

---

## 4. Database Schema

### 4.1 PostgreSQL Tables (Supabase)

**Auth Schema (Managed by Supabase):**

```sql
-- Users table (managed by Supabase Auth)
CREATE SCHEMA auth;

CREATE TABLE auth.users (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  instance_id         UUID,
  email               TEXT UNIQUE NOT NULL,
  encrypted_password  TEXT NOT NULL,  -- bcrypt hash
  email_confirmed_at  TIMESTAMPTZ,
  invited_at          TIMESTAMPTZ,
  confirmation_token  TEXT,
  confirmation_sent_at TIMESTAMPTZ,
  recovery_token      TEXT,
  recovery_sent_at    TIMESTAMPTZ,
  email_change_token_new TEXT,
  email_change        TEXT,
  email_change_sent_at TIMESTAMPTZ,
  last_sign_in_at     TIMESTAMPTZ,
  raw_app_meta_data   JSONB,
  raw_user_meta_data  JSONB,
  is_super_admin      BOOLEAN,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW(),
  phone               TEXT,
  phone_confirmed_at  TIMESTAMPTZ,
  aud                 TEXT,
  role                TEXT,
  CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Indexes for performance
CREATE INDEX users_email_idx ON auth.users(email);
CREATE INDEX users_instance_id_idx ON auth.users(instance_id);
```

**Public Schema (Custom Tables):**

```sql
-- User profiles with business roles
CREATE TABLE public.user_profiles (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name       TEXT NOT NULL,
  role            TEXT NOT NULL CHECK (role IN ('company_user', 'super_admin')),
  company_id      INTEGER REFERENCES public.companies(id),  -- Each user assigned to ONE company
  can_upload_data BOOLEAN DEFAULT false NOT NULL,
  is_active       BOOLEAN DEFAULT true NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  created_by_id   UUID REFERENCES auth.users(id),
  CONSTRAINT company_required_for_company_user CHECK (
    role = 'super_admin' OR (role = 'company_user' AND company_id IS NOT NULL)
  )
);

COMMENT ON COLUMN user_profiles.company_id IS 'NULL for super_admins (access all), NOT NULL for company_users';
COMMENT ON TABLE user_profiles IS 'Simplified schema: one company per user, no join table needed';

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Company master data (synced with Airtable)
CREATE TABLE public.companies (
  id                      SERIAL PRIMARY KEY,
  airtable_company_name   TEXT UNIQUE NOT NULL,  -- Exact match to Airtable
  display_name            TEXT NOT NULL,
  is_active               BOOLEAN DEFAULT true NOT NULL,
  created_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Seed companies from Airtable
INSERT INTO public.companies (airtable_company_name, display_name) VALUES
  ('A-1', 'A-1'),
  ('ACE', 'ACE'),
  ('Bisson', 'Bisson'),
  ('Coastal', 'Coastal'),
  ('Hopkins', 'Hopkins'),
  ('Kaster', 'Kaster'),
  ('Mabeys', 'Mabeys'),
  ('RC Mason', 'RC Mason'),
  ('Spirit', 'Spirit'),
  ('Winter', 'Winter');

-- NOTE: No user_company_assignments table needed!
-- In the simplified schema, company_id is stored directly in user_profiles table.
-- This eliminates JOIN queries and simplifies the data model.

-- Audit logging for compliance and security monitoring
CREATE TABLE public.audit_logs (
  id            SERIAL PRIMARY KEY,
  user_id       UUID NOT NULL REFERENCES auth.users(id),
  action        TEXT NOT NULL,  -- 'login', 'logout', 'upload_balance_sheet', 'create_win', etc.
  resource      TEXT,           -- 'auth', 'balance_sheet', 'wins', 'users', etc.
  company_id    INTEGER REFERENCES public.companies(id),
  ip_address    INET,
  user_agent    TEXT,
  metadata      JSONB,  -- Additional context (file name, old/new values, etc.)
  timestamp     TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for query performance
CREATE INDEX idx_user_profiles_role ON user_profiles(role);
CREATE INDEX idx_user_profiles_is_active ON user_profiles(is_active);
CREATE INDEX idx_user_profiles_company ON user_profiles(company_id);  -- For filtering by company
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_company ON audit_logs(company_id);
```

### 4.2 Row-Level Security (RLS) Policies

**Enable RLS on all custom tables:**

```sql
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
-- Note: No user_company_assignments table in simplified schema
```

**User Profiles Policies:**

```sql
-- Users can view their own profile
CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = id);

-- Users can update their own name (not role)
CREATE POLICY "Users can update own name"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (
    auth.uid() = id
    AND role = (SELECT role FROM user_profiles WHERE id = auth.uid())  -- Cannot change own role
  );

-- Super admins can view all profiles
CREATE POLICY "Super admins view all profiles"
  ON user_profiles FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE id = auth.uid() AND role = 'super_admin' AND is_active = true
    )
  );

-- Super admins can manage all users
CREATE POLICY "Super admins manage users"
  ON user_profiles FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE id = auth.uid() AND role = 'super_admin' AND is_active = true
    )
  );
```

**Companies Policies:**

```sql
-- All authenticated users can view companies
CREATE POLICY "Authenticated users view companies"
  ON companies FOR SELECT
  TO authenticated
  USING (is_active = true);

-- Only super admins can modify companies
CREATE POLICY "Super admins manage companies"
  ON companies FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE id = auth.uid() AND role = 'super_admin' AND is_active = true
    )
  );
```

**Audit Logs Policies:**

```sql
-- All authenticated users can create audit logs (append-only)
CREATE POLICY "Users create audit logs"
  ON audit_logs FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- Users can view their own audit logs
CREATE POLICY "Users view own audit logs"
  ON audit_logs FOR SELECT
  USING (auth.uid() = user_id);

-- Wins admins and super admins can view all audit logs
CREATE POLICY "Admins view all audit logs"
  ON audit_logs FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE id = auth.uid()
        AND role IN ('wins_admin', 'super_admin')
        AND is_active = true
    )
  );

-- Only super admins can delete audit logs (data retention)
CREATE POLICY "Super admins delete old audit logs"
  ON audit_logs FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM user_profiles
      WHERE id = auth.uid() AND role = 'super_admin' AND is_active = true
    )
  );
```

**Security Benefits of RLS:**
- ✅ Enforced at database level (cannot be bypassed by application code)
- ✅ Protection against SQL injection (even if ORM is compromised)
- ✅ Defense in depth (multiple security layers)
- ✅ Automatic enforcement (no manual permission checks needed)
- ✅ Audit trail of policy changes (PostgreSQL logs)

---

## 5. Deployment Architecture (Render)

### 5.1 Render Configuration

**Service Type:** Web Service
**Environment:** Production
**Region:** Oregon (US West) - Configurable
**Instance Type:**
- **Production:** Starter Package 

**Build Configuration:**

```yaml
# render.yaml (Infrastructure as Code)
services:
  - type: web
    name: bpc-dashboard
    env: python
    region: oregon
    plan: starter  # $7/month
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.0
      - key: STREAMLIT_SERVER_HEADLESS
        value: true
      - key: STREAMLIT_SERVER_ENABLE_CORS
        value: false
      - key: STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION
        value: true
      # Secrets (set in Render dashboard)
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_ANON_KEY
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: AIRTABLE_PAT
        sync: false
      - key: AIRTABLE_BASE_ID
        sync: false
    healthCheckPath: /healthz
    autoDeploy: true
```

**Environment Variables (Secrets):**

Set in Render Dashboard → Environment → Environment Variables:

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Public key
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Secret key

# Airtable Configuration
AIRTABLE_PAT=patXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX

# Application Configuration
STREAMLIT_SERVER_PORT=$PORT  # Render sets this automatically
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

**Security Headers (Streamlit config.toml):**

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200  # MB
cookieSecret = "GENERATE_RANDOM_SECRET_HERE"

[browser]
gatherUsageStats = false
serverAddress = "0.0.0.0"

[security]
enableStaticServing = false
```

### 5.2 Network Flow & Security Layers

```
Internet (Public)
    │
    ▼
┌──────────────────────┐
│  Cloudflare CDN      │  ← DDoS protection, SSL termination
│  - WAF               │  ← Web Application Firewall
│  - Rate limiting     │  ← 100 req/sec per IP (configurable)
│  - Bot protection    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Render Load Balancer│  ← Load balancing, health checks
│  - SSL/TLS offload   │  ← Let's Encrypt auto-renewal
│  - Header injection  │  ← HSTS, CSP, X-Frame-Options
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Docker Container    │  ← Python runtime
│  - Streamlit App     │  ← Application code
│  - Gunicorn (opt)    │  ← Production WSGI server (optional)
└──────────┬───────────┘
           │
           ├────────────────────┐
           │                    │
           ▼                    ▼
    ┌──────────────┐    ┌──────────────┐
    │  Supabase    │    │  Airtable    │
    │  (Virginia)  │    │  (US region) │
    │  - Auth      │    │  - Financial │
    │  - PostgreSQL│    │    Data      │
    └──────────────┘    └──────────────┘
```

**Security Layers:**

| Layer | Security Control | Protection Against |
|-------|------------------|-------------------|
| **Layer 7 (CDN)** | Cloudflare WAF | DDoS, SQL injection, XSS, bot attacks |
| **Layer 6 (TLS)** | TLS 1.2+ | Man-in-the-middle, eavesdropping |
| **Layer 5 (LB)** | Rate limiting | Brute force, abuse |
| **Layer 4 (App)** | Authentication | Unauthorized access |
| **Layer 3 (App)** | Authorization | Privilege escalation |
| **Layer 2 (DB)** | Row-Level Security | Data leakage, injection |
| **Layer 1 (DB)** | Encryption at rest | Physical theft, disk access |

### 5.3 Performance & Scalability

**Expected Performance:**

- **Page Load Time:** 1-2 seconds (initial), <500ms (subsequent)
- **API Latency:**
  - Supabase: 20-50ms (same region)
  - Airtable: 100-200ms (US region)
- **Concurrent Users:** 20-50 simultaneous

**Caching Strategy:**

```python
import streamlit as st

# Cache Supabase data for 30 minutes
@st.cache_data(ttl=1800)
def get_user_companies(user_id):
    # Query Supabase for user's company assignments
    pass

# Cache Airtable data for 15 minutes
@st.cache_data(ttl=900)
def get_financial_data(company, period):
    # Query Airtable for financial data
    pass
```

## 6. Threat Model & Risk Mitigation

### 6.1 Identified Threats

| # | Threat | Likelihood | Impact | Risk Level | Mitigation |
|---|--------|------------|--------|-----------|------------|
| **T1** | Brute Force Login | Medium | Medium | **MEDIUM** | Rate limiting (5 attempts), account lockout (15 min), CAPTCHA (optional), audit logging |
| **T2** | Session Hijacking | Low | High | **MEDIUM** | HTTPS only, HttpOnly cookies, short token expiry (1h), secure token storage |
| **T3** | SQL Injection | Low | High | **LOW** | Parameterized queries, ORM (Supabase client), RLS policies, input validation |
| **T4** | Cross-Site Scripting (XSS) | Low | Medium | **LOW** | Streamlit auto-escapes output, CSP headers, input sanitization |
| **T5** | Credential Stuffing | Medium | Medium | **MEDIUM** | Email verification, password strength requirements, rate limiting |
| **T6** | Privilege Escalation | Low | High | **LOW** | RLS policies, application-layer checks, audit logging, role validation |
| **T7** | Data Exfiltration | Medium | High | **MEDIUM** | Company-level access control, audit logs, rate limiting, export restrictions |
| **T8** | Man-in-the-Middle | Very Low | High | **LOW** | TLS 1.2+, certificate pinning, HSTS headers, automatic HTTPS redirect |
| **T9** | Insider Threat | Medium | High | **MEDIUM** | Audit logs, least privilege, separation of duties, regular access reviews |
| **T10** | API Key Exposure | Low | Critical | **MEDIUM** | Environment variables, secrets management, never commit to Git, rotation policy |
| **T11** | Password Reset Abuse | Low | Medium | **LOW** | Rate limiting (3/hour), token expiry (1h), one-time use tokens, email verification |
| **T12** | Unauthorized Data Upload | Low | High | **LOW** | Permission checks, company filtering, server-side validation, audit logging |

**Risk Matrix:**

```
          Impact
          Low    Medium   High    Critical
        ┌───────┬────────┬───────┬────────┐
Low     │       │   T4   │  T3   │        │
        │       │   T11  │  T6   │        │
        │       │        │  T8   │        │
        │       │        │  T12  │        │
        ├───────┼────────┼───────┼────────┤
Medium  │       │   T1   │  T7   │        │
        │       │   T5   │  T9   │        │
        ├───────┼────────┼───────┼────────┤
High    │       │        │  T2   │        │
        ├───────┼────────┼───────┼────────┤
Critical│       │        │       │  T10   │
        └───────┴────────┴───────┴────────┘
```

### 6.2 Mitigation Strategies

**High Priority:**

1. **T10: API Key Exposure**
   - Store all secrets in environment variables
   - Add `.env` to `.gitignore`
   - Scan Git history for exposed secrets (truffleHog, git-secrets)
   - Rotate keys quarterly
   - Use separate keys for dev/staging/production

2. **T7: Data Exfiltration**
   - Implement company-level access control
   - Log all data access attempts
   - Rate limit API calls (100 req/min per user)
   - Restrict bulk data exports (require admin approval)
   - Monitor for anomalous access patterns

3. **T9: Insider Threat**
   - Comprehensive audit logging
   - Principle of least privilege (minimal permissions by default)
   - Regular access reviews (quarterly)
   - Separation of duties (no single user has full control)
   - Background checks for super admins (if applicable)

**Medium Priority (Implement in Phase 2):**

4. **T1: Brute Force Login**
   ```python
   # Implement rate limiting
   from datetime import datetime, timedelta

   failed_attempts = {}  # In production: use Redis

   def check_rate_limit(email):
       if email in failed_attempts:
           attempts, first_attempt = failed_attempts[email]
           if attempts >= 5:
               if datetime.now() - first_attempt < timedelta(minutes=15):
                   return False  # Locked out
               else:
                   del failed_attempts[email]  # Reset after 15 min
       return True

   def record_failed_attempt(email):
       if email in failed_attempts:
           attempts, first_attempt = failed_attempts[email]
           failed_attempts[email] = (attempts + 1, first_attempt)
       else:
           failed_attempts[email] = (1, datetime.now())
   ```

5. **T2: Session Hijacking**
   - Implement session timeout (30 min inactivity)
   - Bind sessions to IP address (optional, may break mobile)
   - Regenerate session ID after login
   - Implement "logout all devices" functionality

6. **T5: Credential Stuffing**
   - Enable email verification for new accounts
   - Implement password strength requirements (zxcvbn library)
   - Check against breached password database (HaveIBeenPwned API)
   - Encourage use of password managers

**Low Priority (Nice to Have):**

7. **T3: SQL Injection**
   - Already mitigated by Supabase client (parameterized queries)
   - Regular dependency updates (Dependabot)

8. **T4: XSS**
   - Already mitigated by Streamlit (auto-escaping)
   - Implement Content Security Policy (CSP) headers

9. **T6: Privilege Escalation**
   - Regular security audits of RLS policies
   - Automated testing of permission boundaries

### 6.3 Security Monitoring (Recommended)

**Metrics to Track:**

- Failed login attempts per hour
- New user registrations per day
- Data upload volumes per company
- API error rates (4xx, 5xx)
- Average session duration
- Geographic distribution of logins (detect anomalies)

**Alerting Rules:**

- Alert if >10 failed logins from same IP in 1 hour
- Alert if new user created by non-admin
- Alert if super admin role granted/revoked
- Alert if data uploaded for >5 companies by single user in 1 day
- Alert if API error rate >5% for 5 minutes

**Example Monitoring Query (Supabase SQL Editor):**

```sql
-- Detect potential brute force attacks
SELECT
  ip_address,
  COUNT(*) as failed_attempts,
  MIN(timestamp) as first_attempt,
  MAX(timestamp) as last_attempt
FROM audit_logs
WHERE action = 'failed_login'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
HAVING COUNT(*) >= 10
ORDER BY failed_attempts DESC;
```

---

## 7. Compliance & Standards

### 7.1 OWASP Top 10 (2021) Alignment

| # | Vulnerability | Risk Level | Mitigation Status | Controls |
|---|---------------|-----------|-------------------|----------|
| **A01** | Broken Access Control | **HIGH** | ✅ **MITIGATED** | RLS policies, RBAC, permission checks, audit logging |
| **A02** | Cryptographic Failures | **HIGH** | ✅ **MITIGATED** | TLS 1.2+, bcrypt, AES-256, no plaintext secrets |
| **A03** | Injection | **HIGH** | ✅ **MITIGATED** | Parameterized queries, ORM, input validation, RLS |
| **A04** | Insecure Design | **MEDIUM** | ✅ **MITIGATED** | Threat modeling, security by design, defense in depth |
| **A05** | Security Misconfiguration | **MEDIUM** | ✅ **MITIGATED** | Secure defaults, minimal permissions, hardened config |
| **A06** | Vulnerable Components | **MEDIUM** | ⚠️ **PARTIAL** | Dependabot enabled, manual dependency updates |
| **A07** | Identification & Auth Failures | **HIGH** | ✅ **MITIGATED** | JWT tokens, password policies, MFA-ready, session mgmt |
| **A08** | Software & Data Integrity | **MEDIUM** | ✅ **MITIGATED** | Dependency scanning, audit logs, code reviews |
| **A09** | Security Logging & Monitoring | **MEDIUM** | ✅ **MITIGATED** | Comprehensive audit trail, 90-day retention |
| **A10** | Server-Side Request Forgery | **MEDIUM** | ✅ **N/A** | No user-controlled URLs, no external URL fetching |

### 7.2 NIST Cybersecurity Framework

| Function | Category | Implementation |
|----------|----------|----------------|
| **IDENTIFY** | Asset Management | Documentation of all components, data classification |
| **IDENTIFY** | Risk Assessment | Threat modeling, risk matrix (Section 6.1) |
| **PROTECT** | Access Control | RBAC, RLS, authentication, least privilege |
| **PROTECT** | Data Security | Encryption (TLS, AES-256), secure key management |
| **PROTECT** | Protective Technology | Firewalls (Cloudflare WAF), secure configuration |
| **DETECT** | Anomalies & Events | Audit logging, failed login tracking |
| **DETECT** | Security Monitoring | Log analysis (manual), alerts (optional) |
| **RESPOND** | Response Planning | Incident response procedures (Section 8.2) |
| **RESPOND** | Communications | Security notification process |
| **RECOVER** | Recovery Planning | Database backups (Supabase automatic), RTO < 1 hour |

### 7.3 Data Privacy Considerations

**User Data Collected:**

| Data Type | Purpose | Retention | Sensitivity |
|-----------|---------|-----------|-------------|
| Email addresses | Authentication, communication | Until account deletion | **MEDIUM** |
| Full names | Display, audit logs | Until account deletion | **LOW** |
| Passwords | Authentication | Until changed/deleted | **CRITICAL** (hashed) |
| Company assignments | Authorization | Until removed | **LOW** |
| IP addresses | Security, audit logging | 90 days | **MEDIUM** |
| User agents | Security, troubleshooting | 90 days | **LOW** |
| Login timestamps | Audit, analytics | 90 days | **LOW** |
| Financial data views | Audit | 90 days | **LOW** (no PII) |


**Data Retention Policy:**

- **Active users:** Indefinite (while employed/contracted)
- **Inactive users:** 2 years after last login, then soft delete (is_active = false)
- **Deleted users:** Hard delete after 30 days (allow recovery period)
- **Audit logs:** 90 days minimum, 1 year recommended, 7 years for compliance (optional)

### 7.4 Compliance Certifications

**Current Status:**

- **SOC 2:** (Supabase is SOC 2 Type II compliant)
- **ISO 27001:** Not certified
- **GDPR:** Compliant architecture (data minimization, encryption, access controls)
- **HIPAA:** Not applicable (no health data)
- **PCI DSS:** Not applicable (no payment data)

**Certification Path (if required):**

1. **Phase 1:** Document security policies and procedures
2. **Phase 2:** Implement additional controls (MFA, advanced monitoring)
3. **Phase 3:** Engage third-party auditor for SOC 2 Type I
4. **Phase 4:** 6-12 month observation period for SOC 2 Type II

---

## 8. Operational Security

### 8.1 User Lifecycle Management

**User Onboarding Process:**

```
1. Request Received
   ↓
   Admin receives new user request (email, Slack, etc.)
   ↓
2. Identity Verification
   ↓
   Verify user's identity (company email, manager approval)
   ↓
3. Account Creation
   ↓
   Admin logs into dashboard → User Management
   ↓
   Create user account:
   - Email: user@company.com
   - Full Name: John Doe
   - Role: company_user
   - Assigned Companies: [ACE, Bisson]
   - Permissions: can_upload_data = true
   ↓
4. System Generates Invite
   ↓
   Supabase sends invitation email with setup link
   ↓
5. User Setup
   ↓
   User clicks link → Set password → Login
   ↓
6. Audit Log
   ↓
   Log: "Admin created user john@company.com with role company_user"
```

**User Offboarding Process:**

```
1. Termination/Resignation
   ↓
   HR notifies admin of user departure
   ↓
2. Immediate Deactivation
   ↓
   Admin logs in → User Management → Find user
   ↓
   Set is_active = false
   ↓
3. Logout All Sessions
   ↓
   User's JWT tokens invalidated (next page load)
   ↓
4. Review Access
   ↓
   Admin reviews audit logs for user's recent activity
   ↓
   Check for any suspicious behavior before departure
   ↓
5. Data Retention
   ↓
   User account retained for 30 days (recovery period)
   ↓
   Audit logs retained per policy (90 days - 1 year)
   ↓
6. Hard Delete (Optional)
   ↓
   After 30 days, admin can permanently delete account
   ↓
   User profile deleted, audit logs anonymized (user_id → "deleted_user")
```

### 8.2 Incident Response

**Incident Types:**

| Type | Severity | Response Time | Escalation |
|------|----------|---------------|------------|
| Suspected breach | **CRITICAL** | Immediate | CTO, Legal |
| Mass failed logins | **HIGH** | 15 minutes | Admin team |
| Unauthorized access attempt | **MEDIUM** | 1 hour | Security lead |
| User account compromise | **MEDIUM** | 1 hour | User, Admin |
| System outage | **HIGH** | 15 minutes | DevOps, CTO |

**Incident Response Playbook:**

**Scenario 1: Suspected Data Breach**

```
1. DETECT (Trigger: Alert or report)
   ↓
2. ASSESS
   - Review audit logs for unauthorized access
   - Check Supabase activity logs
   - Verify API key security (not exposed)
   ↓
3. CONTAIN
   - Revoke all Supabase service keys immediately
   - Rotate Airtable PAT token
   - Force logout all users (clear all sessions)
   - Disable affected user accounts
   ↓
4. INVESTIGATE
   - Review logs to identify scope of breach
   - Determine which data was accessed/exported
   - Identify root cause (phishing, credential stuffing, etc.)
   ↓
5. REMEDIATE
   - Fix vulnerability (patch, config change, etc.)
   - Generate new API keys
   - Re-enable users with forced password reset
   ↓
6. NOTIFY
   - Notify affected users if PII exposed
   - Report to management
   - Document incident (date, time, impact, actions taken)
   ↓
7. REVIEW
   - Post-incident review (PIR)
   - Update security policies
   - Implement additional controls if needed
```

**Scenario 2: Forgotten Password (Manual Reset)**

```
1. User contacts admin (email, phone, Slack)
   ↓
2. Admin verifies identity
   - Confirm via secondary channel (phone call, video)
   - Verify employment status
   ↓
3. Admin resets password
   Option A: Via Supabase Dashboard
   - Auth → Users → [User] → Send Magic Link

   Option B: Via Application
   - User Management → [User] → Reset Password
   ↓
4. User receives email with reset link
   ↓
5. User sets new password
   ↓
6. Audit log recorded
   - "Admin initiated password reset for user@example.com"
```

**Scenario 3: Suspicious Activity Detected**

```
Trigger: User uploading data for 8 different companies in 1 hour
   ↓
1. Alert generated (audit log query)
   ↓
2. Admin reviews activity
   - Check user's assigned companies
   - Review audit logs for context
   ↓
3. Decision:

   If LEGITIMATE (e.g., quarterly data load):
   - Document reason
   - No action needed

   If SUSPICIOUS:
   - Deactivate user account immediately
   - Contact user via phone/email
   - Review all recent uploads
   - If compromised: change passwords, review other users
   ↓
4. Document incident
```

### 8.3 Security Maintenance

**Weekly Tasks:**

- ✅ Review failed login attempts (audit log query)
- ✅ Check for new user accounts created
- ✅ Verify all super admins are still authorized

**Monthly Tasks:**

- ✅ Review all user accounts (remove inactive users)
- ✅ Audit permission assignments (least privilege check)
- ✅ Update Python dependencies (`pip list --outdated`)
- ✅ Review Supabase activity logs
- ✅ Backup audit logs (export to CSV)

**Quarterly Tasks:**

- ✅ Rotate API keys (Airtable PAT, Supabase service key)
- ✅ Review RLS policies for gaps
- ✅ Security audit of codebase (manual or automated scan)
- ✅ Update passwords for admin accounts
- ✅ Test incident response procedures (tabletop exercise)

**Annual Tasks:**

- ✅ Comprehensive security assessment (penetration test)
- ✅ Review and update security policies
- ✅ User security training (phishing awareness, password hygiene)
- ✅ Disaster recovery test (restore from backup)

---

## 9. Implementation Timeline

| Phase | Duration | Deliverables | Milestone |
|-------|----------|--------------|-----------|
| **Phase 0: Planning** | 2-3 days | Technical design, database schema, security policies | ✅ Complete |
| **Phase 1: Supabase Setup** | 3-5 days | Supabase project, PostgreSQL schema, RLS policies, seed data, test connection | 🔵 Database ready |
| **Phase 2: Authentication** | 5-7 days | Login/logout pages, session management, password reset, JWT validation | 🔵 Users can log in |
| **Phase 3: Authorization** | 7-10 days | Permission checks, company filtering, role-based UI, data upload restrictions | 🔵 RBAC enforced |
| **Phase 4: Admin Interface** | 5-7 days | User management UI, company assignments, role management, audit viewer | 🔵 Self-service admin |
| **Phase 5: Testing** | 3-5 days | Security testing, penetration testing (optional), user acceptance testing | 🔵 Production ready |
| **Phase 6: Deployment** | 2-3 days | Render configuration, environment variables, production deployment, monitoring | 🔵 Live in production |
| **Phase 7: Training** | 2-3 days | Admin training, user documentation, incident response training | 🔵 Team ready |
| **Total** | **25-37 days** | Fully functional authentication system with RBAC | ✅ Project complete |

**Critical Path:**

Phase 1 (Setup) → Phase 2 (Auth) → Phase 3 (Authz) → Phase 6 (Deploy)

**Parallel Tracks:**

- Phase 4 (Admin UI) can start after Phase 2 completes
- Documentation can be written throughout all phases

**Risk Buffer:**

- Add 20% time buffer for unexpected issues: **30-45 days total**

---

## 10. Recommendations

### 10.1 Must-Have (Phase 1 - Production Launch)

✅ **Security Baseline:**

1. **Password Policy:**
   - Minimum 8 characters
   - At least 1 uppercase, 1 lowercase, 1 number, 1 special character
   - Check against common passwords (top 10,000 list)

2. **Network Security:**
   - HTTPS enforcement (automatic redirect from HTTP)
   - TLS 1.2+ only (disable older protocols)
   - HSTS headers (max-age=31536000)

3. **Database Security:**
   - Row-Level Security policies enabled on all tables
   - Principle of least privilege for all roles
   - Regular backups (Supabase automatic daily backups)

4. **Audit Logging:**
   - Log all authentication events (login, logout, failed attempts)
   - Log all data modifications (uploads, wins/challenges)
   - Log all admin actions (user creation, permission changes)
   - 90-day retention minimum

5. **Environment Security:**
   - All secrets in environment variables
   - No secrets in Git repository (verify with git-secrets scan)
   - Separate credentials for dev/staging/production

### 10.2 Should-Have (Phase 2 - 3 Months Post-Launch)

⚠️ **Enhanced Security:**

1. **Rate Limiting:**
   - 5 failed login attempts → 15-minute lockout
   - 3 password reset requests per hour per email
   - 100 API requests per minute per user

2. **Email Verification:**
   - Require email verification for new accounts
   - Send notification emails for security events:
     - Login from new device/location
     - Password changed
     - Permission changes

3. **Session Management:**
   - 30-minute inactivity timeout
   - "Logout all devices" functionality
   - Show active sessions to users

4. **Advanced Monitoring:**
   - Set up alerts for suspicious activity
   - Dashboard for security metrics
   - Weekly security reports to admins

5. **Security Audits:**
   - Quarterly manual code reviews
   - Dependency vulnerability scanning (Snyk, Dependabot)
   - Annual penetration testing

### 10.3 Nice-to-Have (Future Enhancements)

🔵 **Enterprise Features:**

1. **Multi-Factor Authentication (MFA):**
   - TOTP (Google Authenticator, Authy)
   - SMS-based (Twilio integration)
   - Email-based (Supabase built-in)

2. **Single Sign-On (SSO):**
   - Google Workspace integration
   - Microsoft Azure AD integration
   - SAML 2.0 support

3. **Advanced Audit Logging:**
   - Real-time security dashboard
   - Anomaly detection (ML-based)
   - SIEM integration (Splunk, Datadog)
   - Forensic analysis tools

4. **Compliance Certifications:**
   - SOC 2 Type II audit
   - ISO 27001 certification
   - GDPR compliance documentation

5. **Advanced Access Control:**
   - Time-based access (e.g., access only during business hours)
   - Location-based access (IP whitelisting)
   - Context-aware access (device fingerprinting)

### 10.4 Cost-Benefit Analysis

| Feature | Implementation Cost | Ongoing Cost | Security Benefit | Business Value | Recommendation |
|---------|-------------------|--------------|------------------|----------------|----------------|
| Basic Auth (JWT) | 5 days | $0/month | **HIGH** | **HIGH** | ✅ Must-have |
| RBAC + RLS | 7 days | $0/month | **HIGH** | **HIGH** | ✅ Must-have |
| Audit Logging | 2 days | $0/month | **MEDIUM** | **HIGH** | ✅ Must-have |
| Rate Limiting | 1 day | $0/month | **MEDIUM** | **MEDIUM** | ⚠️ Should-have |
| Email Verification | 2 days | $0/month | **MEDIUM** | **MEDIUM** | ⚠️ Should-have |
| MFA (TOTP) | 3 days | $0/month | **HIGH** | **MEDIUM** | 🔵 Nice-to-have |
| SSO (Google) | 5 days | $0/month | **MEDIUM** | **HIGH** | 🔵 Nice-to-have |
| Penetration Testing | 0 days | $2-5K/year | **HIGH** | **LOW** | 🔵 Nice-to-have |
| SOC 2 Audit | 10 days | $15-30K/year | **MEDIUM** | **LOW** | 🔵 Only if required |

---

## 11. Conclusion

### 11.1 Summary

The proposed authentication system provides **enterprise-grade security** with **minimal operational overhead** by leveraging proven technologies:

- **Supabase Auth** for authentication (industry-standard OAuth 2.0 / JWT)
- **PostgreSQL Row-Level Security** for database-layer authorization
- **Role-Based Access Control** for business logic enforcement
- **Comprehensive Audit Logging** for compliance and security monitoring

**Key Benefits:**

✅ **Security:** Multiple defense layers (network, application, database)
✅ **Usability:** Self-service password reset, intuitive UI
✅ **Scalability:** Handles 20-100 users easily, scales to 1000+
✅ **Maintainability:** Managed services reduce operational burden
✅ **Cost-Effective:** Free tier for 50K MAU, ~$32/month max
✅ **Compliance-Ready:** OWASP Top 10 aligned, GDPR-compatible

### 11.2 Security Posture

**Overall Risk Rating:** **LOW to MEDIUM**

**Strengths:**
- Industry-standard cryptography (TLS 1.2+, bcrypt, AES-256)
- Defense-in-depth architecture (7 security layers)
- Database-level permission enforcement (RLS policies)
- Comprehensive audit trail (all critical actions logged)
- Managed infrastructure (Render, Supabase - security patches automatic)

**Residual Risks:**
- Reliance on third-party services (Supabase, Render uptime)
- No MFA in initial implementation (can be added in Phase 2)
- Email-based password reset (vulnerable to phishing - mitigated by training)
- Limited to 10 MB file uploads (larger files may require alternative approach)

**Risk Acceptance:**
The residual risks are **acceptable** for a B2B SaaS application handling financial data with 20-100 users. The system meets industry best practices and exceeds the security of most small-to-medium business applications.

### 11.3 Next Steps

**Immediate Actions:**

1. ✅ **Approval:** Review and approve this technical design with stakeholders
2. ✅ **Supabase Setup:** Create Supabase project and configure database schema
3. ✅ **Timeline Agreement:** Finalize implementation timeline (25-37 days)
4. ✅ **Resource Allocation:** Assign development resources (1-2 developers)

**Before Production Launch:**

- ✅ Security testing (penetration testing optional but recommended)
- ✅ User acceptance testing with real users
- ✅ Admin training on user management and incident response
- ✅ Documentation for end users (login, password reset, etc.)

**Post-Launch:**

- Week 1: Monitor audit logs closely for issues
- Week 2: Gather user feedback on usability
- Month 1: Review security metrics and adjust policies
- Month 3: Implement Phase 2 enhancements (rate limiting, email verification)
- Year 1: Annual security audit and policy review

### 11.4 Approval & Sign-Off

This technical design is ready for implementation upon approval from:

- [ ] **IT Security Lead** - Security architecture and risk assessment
- [ ] **CTO/VP Engineering** - Technical feasibility and resource allocation
- [ ] **Product Owner** - User experience and business requirements
- [ ] **Compliance Officer** - Regulatory requirements (if applicable)

**Questions or Concerns:**

For any questions about this implementation, please contact:
- **Technical Questions:** [Developer Email]
- **Security Questions:** [Security Lead Email]
- **Business Questions:** [Product Owner Email]

---

## Appendix A: Glossary

**Authentication:** Process of verifying a user's identity (e.g., login with email/password)

**Authorization:** Process of verifying what an authenticated user can access (e.g., company data)

**bcrypt:** Industry-standard password hashing algorithm (adaptive, salted)

**JWT (JSON Web Token):** Compact token format for secure authentication (digitally signed)

**OAuth 2.0:** Industry-standard protocol for authorization

**RBAC (Role-Based Access Control):** Authorization model based on user roles

**RLS (Row-Level Security):** PostgreSQL feature to restrict database row visibility per user

**TLS (Transport Layer Security):** Cryptographic protocol for secure network communication

**TOTP (Time-Based One-Time Password):** Algorithm for generating MFA codes

**WAF (Web Application Firewall):** Firewall that filters HTTP traffic to protect web apps

---

## Appendix B: References

**Security Standards:**

- OWASP Top 10 (2021): https://owasp.org/Top10/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- CIS Controls: https://www.cisecurity.org/controls

**Technologies:**

- Supabase Documentation: https://supabase.com/docs
- PostgreSQL RLS: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Streamlit Documentation: https://docs.streamlit.io
- Render Documentation: https://render.com/docs

**Security Resources:**

- OWASP Cheat Sheets: https://cheatsheetseries.owasp.org/
- Have I Been Pwned: https://haveibeenpwned.com/
- NIST Password Guidelines: https://pages.nist.gov/800-63-3/

---

**Document Version:** 1.0
**Last Updated:** November 5, 2025
**Classification:** Internal - For Client IT Review
**Author:** Development Team
**Approved By:** [Pending]

---

*END OF TECHNICAL REPORT*
