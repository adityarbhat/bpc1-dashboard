# CRITICAL: Supabase Email Template Update Required

## What You Need to Do

The code has been updated to use PKCE flow for password reset, but you must **manually update the Supabase email template** to complete the fix.

## Steps to Update Email Template

1. **Go to Supabase Dashboard**:
   - Navigate to: https://supabase.com/dashboard
   - Select your project: `xxkpdvpsryaytbsvzhph`

2. **Open Email Templates**:
   - Click on **Authentication** in the left sidebar
   - Click on **Email Templates**
   - Select **Reset Password** template

3. **Update the Link Format**:

   **FIND THIS (old implicit flow - doesn't work):**
   ```html
   <a href="{{ .SiteURL }}/reset_landing#access_token={{ .AccessToken }}&type=recovery">
     Reset My Password
   </a>
   ```

   **REPLACE WITH THIS (new PKCE flow - works with Streamlit):**
   ```html
   <a href="{{ .SiteURL }}/reset_landing?token_hash={{ .TokenHash }}&type=recovery">
     Reset My Password
   </a>
   ```

   **Key Changes:**
   - Changed `#` (hash) to `?` (query parameter)
   - Changed `{{ .AccessToken }}` to `{{ .TokenHash }}`
   - Removed `refresh_token` parameter (not needed for PKCE)

4. **Save the Template**:
   - Click **Save** button at the bottom of the page
   - The change takes effect immediately

## Why This Is Necessary

- **Streamlit strips URL hash fragments** before JavaScript can access them
- The old approach using `#access_token={{ .AccessToken }}` never worked because:
  1. Supabase sends user to: `https://site.com/reset_landing#access_token=xyz`
  2. Streamlit processes URL server-side and removes everything after `#`
  3. JavaScript receives: `https://site.com/reset_landing` (hash already gone)
  4. Result: Empty query params `{}`

- **PKCE flow uses query parameters** which Streamlit preserves:
  1. Supabase sends user to: `https://site.com/reset_landing?token_hash=xyz&type=recovery`
  2. Streamlit preserves query parameters
  3. Python code reads via `st.query_params.get('token_hash')`
  4. Result: Token successfully captured ✅

## Testing After Update

1. Request a new password reset from the login page
2. Check your email - the link should now show `?token_hash=` instead of `#access_token=`
3. Click the link
4. Debug output should show: `token_hash present: True`
5. Enter new password and submit
6. Password reset should complete successfully

## What the Code Changes Did

The following files were updated to support PKCE flow:

- **`pages/reset_landing.py`**:
  - ✅ Removed ineffective JavaScript hash conversion (lines 98-122)
  - ✅ Changed token extraction from `access_token` to `token_hash`
  - ✅ Replaced `set_session()` with `verify_otp()` for PKCE authentication
  - ✅ Updated validation logic to check `token_hash` instead of `access_token`
  - ✅ Updated docstring to document PKCE flow requirement

## Need Help?

If the password reset still doesn't work after updating the email template:

1. Verify the email link shows `?token_hash=` in the URL
2. Check the debug output on the reset page for `token_hash present: True`
3. If you still see `token_hash present: False`, the email template may not have saved correctly

## Reference

- Plan documentation: `/Users/adityaravindrabhat/.claude/plans/fluttering-hugging-lark.md`
- Supabase PKCE documentation: https://supabase.com/docs/guides/auth/server-side/pkce-flow
