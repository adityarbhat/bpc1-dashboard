-- ============================================================================
-- Find and Clean Up Orphaned Users
-- ============================================================================
-- This script finds users in Supabase Auth who don't have profiles
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Step 1: Find orphaned users (exist in auth.users but not in user_profiles)
SELECT
    au.id,
    au.email,
    au.created_at AS auth_created_at,
    CASE WHEN up.id IS NULL THEN 'ORPHANED' ELSE 'HAS PROFILE' END AS status
FROM auth.users au
LEFT JOIN public.user_profiles up ON au.id = up.id
WHERE up.id IS NULL
ORDER BY au.created_at DESC;

-- Step 2: Delete orphaned users (UNCOMMENT to execute)
-- WARNING: This will permanently delete these users from Supabase Auth
--
-- DELETE FROM auth.users
-- WHERE id IN (
--     SELECT au.id
--     FROM auth.users au
--     LEFT JOIN public.user_profiles up ON au.id = up.id
--     WHERE up.id IS NULL
-- );

-- Step 3: Verify cleanup (run after delete)
-- SELECT COUNT(*) as remaining_orphaned_users
-- FROM auth.users au
-- LEFT JOIN public.user_profiles up ON au.id = up.id
-- WHERE up.id IS NULL;
