-- ============================================================================
-- BPC Dashboard Authentication - Database Schema Setup
-- ============================================================================
-- Run this script in Supabase SQL Editor to create all tables and indexes
-- This creates 3 tables: companies, user_profiles, audit_logs
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. COMPANIES TABLE
-- ----------------------------------------------------------------------------
-- Master data for all 10 companies (synced with Airtable)

CREATE TABLE IF NOT EXISTS public.companies (
  id                      SERIAL PRIMARY KEY,
  airtable_company_name   TEXT UNIQUE NOT NULL,  -- Exact match to Airtable
  display_name            TEXT NOT NULL,
  is_active               BOOLEAN DEFAULT true NOT NULL,
  created_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE public.companies IS 'Master list of companies from Airtable';
COMMENT ON COLUMN public.companies.airtable_company_name IS 'Must match exactly with company names in Airtable';

-- Seed all 10 companies from Airtable
INSERT INTO public.companies (airtable_company_name, display_name) VALUES
  ('Ace Relo', 'Ace Relo'),
  ('Ace Worldwide', 'Ace Worldwide'),
  ('Alexanders', 'Alexanders'),
  ('AMJ', 'AMJ'),
  ('Apex', 'Apex'),
  ('Guardian', 'Guardian'),
  ('InterWest', 'InterWest'),
  ('Smith Dray', 'Smith Dray'),
  ('Weleski', 'Weleski')
ON CONFLICT (airtable_company_name) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 2. USER PROFILES TABLE
-- ----------------------------------------------------------------------------
-- Extended user information linked to Supabase Auth users
-- Simplified schema: ONE company per user (company_id stored directly)

CREATE TABLE IF NOT EXISTS public.user_profiles (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name       TEXT NOT NULL,
  role            TEXT NOT NULL CHECK (role IN ('company_user', 'super_admin')),
  company_id      INTEGER REFERENCES public.companies(id),  -- NULL for super_admins
  can_upload_data BOOLEAN DEFAULT false NOT NULL,
  is_active       BOOLEAN DEFAULT true NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  created_by_id   UUID REFERENCES auth.users(id),

  -- Constraint: company_users MUST have a company assigned
  CONSTRAINT company_required_for_company_user CHECK (
    role = 'super_admin' OR (role = 'company_user' AND company_id IS NOT NULL)
  )
);

COMMENT ON TABLE public.user_profiles IS 'User business roles and permissions - simplified single-company model';
COMMENT ON COLUMN public.user_profiles.company_id IS 'NULL for super_admins (access all companies), NOT NULL for company_users';
COMMENT ON COLUMN public.user_profiles.can_upload_data IS 'Permission to upload financial data for assigned company';

-- ----------------------------------------------------------------------------
-- 3. TRIGGER FOR AUTOMATIC UPDATED_AT TIMESTAMP
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 4. AUDIT LOGS TABLE
-- ----------------------------------------------------------------------------
-- Comprehensive logging for security and compliance

CREATE TABLE IF NOT EXISTS public.audit_logs (
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

COMMENT ON TABLE public.audit_logs IS 'Security and compliance audit trail';
COMMENT ON COLUMN public.audit_logs.action IS 'What action was performed';
COMMENT ON COLUMN public.audit_logs.resource IS 'What resource was affected';
COMMENT ON COLUMN public.audit_logs.metadata IS 'Additional JSON context for the action';

-- ----------------------------------------------------------------------------
-- 5. PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------
-- Optimize query performance for common access patterns

-- User profiles indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON user_profiles(role);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON user_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_user_profiles_company ON user_profiles(company_id);

-- Audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_company ON audit_logs(company_id);

-- Companies index
CREATE INDEX IF NOT EXISTS idx_companies_is_active ON companies(is_active);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these after the script completes to verify everything is set up

-- Check companies table (should show 10 companies)
-- SELECT * FROM companies ORDER BY display_name;

-- Check user_profiles table (should be empty initially)
-- SELECT * FROM user_profiles;

-- Check audit_logs table (should be empty initially)
-- SELECT * FROM audit_logs;

-- ============================================================================
-- SUCCESS!
-- ============================================================================
-- If no errors appeared, your database schema is ready!
-- Next step: Enable Row-Level Security (RLS) policies
