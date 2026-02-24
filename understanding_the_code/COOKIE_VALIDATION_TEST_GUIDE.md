# Cookie Validation Testing Guide - Mozilla Firefox

## Overview
This guide helps you test the three new cookie/session validation cases implemented in `shared/auth_utils.py:156-183`.

## Prerequisites
- Firefox browser installed
- Streamlit app running (`streamlit run financial_dashboard.py`)
- Logged in as a test user

---

## Test Case 1: Cookie ≠ Session User ID Mismatch

**What it tests:** Detects when cookie user_id doesn't match session user_id

### Steps:
1. **Login normally** and navigate to any dashboard page
2. Open Firefox Dev Tools (F12) → **Console** tab
3. Run this command to modify session state:
   ```javascript
   // This simulates session corruption
   sessionStorage.clear();
   ```
4. Refresh the page (F5)

### Expected Result:
- ✅ App redirects to login page
- ✅ Session cleared completely
- ✅ Terminal shows: `SECURITY: User ID mismatch - cookie=X, session=Y`

---

## Test Case 2: Cookie Exists But No Session User

**What it tests:** Detects suspicious state where cookies are present but no session exists

### Steps:
1. **Login normally** and navigate to any dashboard page
2. Open Firefox Dev Tools (F12) → **Storage** tab
3. In left sidebar: Expand **Cookies** → Click your domain (`http://localhost:8501`)
4. Verify you see these cookies:
   - `access_token`
   - `refresh_token`
   - `user_id`
5. Open **Console** tab
6. Run this command:
   ```javascript
   // Force complete page reload (hard refresh)
   window.location.reload(true);
   ```
7. **Immediately** open a new tab and visit the same URL

### Alternative Method (Simpler):
1. While logged in, **close the browser tab completely**
2. **Reopen Firefox**
3. Navigate to `http://localhost:8501`
4. Cookies should still exist, but session state is fresh

### Expected Result:
- ✅ App attempts session recovery from cookies
- ✅ If cookies are valid → successful login
- ✅ If cookies are invalid or expired → redirect to login
- ✅ Terminal shows: `SECURITY: Cookie exists but no session user - cookie=<user_id>` (only if cookies exist but session can't be recovered)

---

## Test Case 3: Session Exists But No Cookie

**What it tests:** Detects potential session hijacking (session without cookies)

### Steps:
1. **Login normally** and stay on dashboard
2. Open Firefox Dev Tools (F12) → **Storage** tab
3. Expand **Cookies** → Click `http://localhost:8501`
4. **Delete ALL auth cookies**:
   - Right-click `access_token` → Delete
   - Right-click `refresh_token` → Delete
   - Right-click `user_id` → Delete
5. **DO NOT refresh** - just click a navigation button in the sidebar
6. The app will detect session exists but cookies are gone

### Expected Result:
- ✅ App redirects to login page
- ✅ Session cleared completely
- ✅ Terminal shows: `SECURITY: Session exists but no cookie - session_user=<user_id>`

---

## Test Case 4: Normal Session Recovery (Baseline Test)

**What it tests:** Verifies normal cookie-based session recovery still works

### Steps:
1. **Login normally**
2. Navigate to any page (e.g., Company Ratios)
3. **Refresh the page** (F5)

### Expected Result:
- ✅ You stay logged in (no redirect to login)
- ✅ Page loads normally with your user data
- ✅ Terminal shows: `Session recovered successfully - User: <email>, ID: <id>, Name: <name>, Role: <role>`

---

## How to View Logs in Terminal

Your Streamlit terminal will show:

### ✅ Success Messages:
```
INFO - Session recovered successfully - User: user@example.com, ID: abc123, Name: John Doe, Role: company_user
```

### ⚠️ Security Warnings (These are GOOD - validation is working!):
```
ERROR - SECURITY: User ID mismatch - cookie=abc123, session=xyz789
WARNING - SECURITY: Cookie exists but no session user - cookie=abc123
WARNING - SECURITY: Session exists but no cookie - session_user=abc123
```

### ❌ Normal Validation Failures (Expected when logged out):
```
DEBUG - Session recovery failed - No tokens in cookies
```

---

## Quick Reference: Firefox Dev Tools Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Dev Tools | `F12` or `Ctrl+Shift+I` |
| Console Tab | `Ctrl+Shift+K` |
| Storage Tab | `Shift+F9` |
| Hard Refresh | `Ctrl+Shift+R` or `Ctrl+F5` |
| Close Tab | `Ctrl+W` |

---

## Common Issues & Solutions

### Issue 1: No SECURITY warnings appear
**Cause:** Validation is working correctly, no suspicious behavior detected
**Solution:** Try the test cases above to trigger validation

### Issue 2: Can't see cookies in Storage tab
**Cause:** Cookies might be set with secure flag or wrong domain
**Solution:** Make sure you're viewing cookies for `http://localhost:8501`

### Issue 3: Always redirected to login
**Cause:** Cookies might be expiring too quickly
**Solution:** Check cookie expiry settings in `shared/auth_utils.py` (should be 1 hour for access_token)

---

## Summary of What Each Case Protects Against

| Case | Scenario | Security Risk | Protection |
|------|----------|---------------|------------|
| 1 | Cookie ≠ Session | Session confusion/switching | Forces re-login on mismatch |
| 2 | Cookie but no session | Partial authentication | Prevents half-logged-in state |
| 3 | Session but no cookie | Session hijacking | Detects stolen session state |

---

## Next Steps After Testing

1. ✅ Verify all 4 test cases pass
2. ✅ Check terminal for SECURITY warnings
3. ✅ Confirm normal login flow still works
4. ✅ Test with multiple users in different browsers (Chrome vs Firefox)
5. ✅ Update CLAUDE.md with test results

---

## Need Help?

If you see unexpected behavior:
1. Check terminal logs for detailed error messages
2. Clear all cookies and session storage
3. Restart Streamlit server
4. Try logging in fresh

**Files involved:**
- Cookie validation: `shared/auth_utils.py:156-183`
- Supabase client validation: `shared/supabase_connection.py:115-143`
- Config security: `.streamlit/config.toml:13-14`
