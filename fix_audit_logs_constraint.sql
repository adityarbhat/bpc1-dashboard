-- ============================================================================
-- Fix audit_logs foreign key constraint to allow user deletion
-- ============================================================================
-- This script fixes the foreign key constraint on audit_logs.user_id to:
-- 1. Allow NULL values (for deleted users)
-- 2. Set user_id to NULL when a user is deleted (ON DELETE SET NULL)
--
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Step 1: Drop the existing foreign key constraint
ALTER TABLE public.audit_logs
DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;

-- Step 2: Allow NULL values for user_id (for deleted users)
ALTER TABLE public.audit_logs
ALTER COLUMN user_id DROP NOT NULL;

-- Step 3: Add the foreign key constraint with ON DELETE SET NULL
ALTER TABLE public.audit_logs
ADD CONSTRAINT audit_logs_user_id_fkey
FOREIGN KEY (user_id)
REFERENCES auth.users(id)
ON DELETE SET NULL;

-- Step 4: Add a comment explaining the change
COMMENT ON COLUMN public.audit_logs.user_id IS
'User ID - set to NULL when user is deleted to preserve audit trail';

-- Verify the change
SELECT
    constraint_name,
    table_name,
    column_name
FROM information_schema.key_column_usage
WHERE table_name = 'audit_logs' AND column_name = 'user_id';
