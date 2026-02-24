# Supabase Email Setup Guide

This guide explains how to configure email templates in Supabase for password resets and user invitations.

## Overview

Supabase provides built-in email functionality for:
1. **Password Reset** - Users can request a password reset link
2. **User Invitations** - Admins can invite users who set their own password

## Current Implementation

### 1. Forgot Password (⚠️ PARTIAL - LOCAL TESTING LIMITATION)

**Current Status:**
- ✅ Email sending works
- ✅ User receives reset link
- ❌ Reset link redirects to Supabase (not your app) when testing locally
- ✅ Will work properly in production deployment

**How it works:**
- User clicks "Forgot Password?" on login page
- Enters their email address
- Supabase sends a password reset email
- User clicks link in email to reset password
- User creates new password and logs in

**Already implemented:**
- Forgot password page: `pages/auth/forgot_password.py`
- Integration with login page
- Uses Supabase's `reset_password_for_email()` function

**To test:**
1. Log out of the dashboard
2. Click "Forgot Password?"
3. Enter your email
4. Check your inbox for reset link
5. Click link and set new password

---

## Future Enhancement: Email Invitations

### Current User Creation Flow (Manual)

Right now, when you create a user:
1. Admin fills out form with temporary password
2. User is created in Supabase Auth
3. Admin manually shares credentials with user
4. User logs in with temporary password

### Proposed: Email Invitation Flow (Self-Service)

**Better approach:**
1. Admin fills out form (NO password needed)
2. User receives invitation email automatically
3. User clicks "Set Password" link in email
4. User creates their own password
5. User logs in with their chosen password

---

## How to Implement Email Invitations

### Step 1: Configure Supabase Email Templates

1. Go to Supabase Dashboard → **Authentication** → **Email Templates**

2. Find the **"Invite user"** template

3. Customize the template:

```html
<h2>Welcome to BPC2 Financial Dashboard!</h2>

<p>Hello {{ .Name }},</p>

<p>You've been invited to join the BPC2 Financial Dashboard. Click the link below to set your password and get started:</p>

<p><a href="{{ .ConfirmationURL }}">Set My Password</a></p>

<p>This link expires in 24 hours.</p>

<p>If you have any questions, please contact your administrator.</p>

<p>Powered by IM AI</p>
```

4. Save the template

### Step 2: Update User Creation Function

Modify `pages/admin/user_management.py`:

```python
def create_new_user_with_invitation(email, full_name, role, company_id, can_upload_data):
    """
    Create a new user and send them an invitation email.
    User will set their own password when they accept.
    """
    try:
        supabase = get_supabase_admin_client()

        # Create user with Supabase invite (NO PASSWORD)
        auth_response = supabase.auth.admin.invite_user_by_email(
            email,
            options={
                "data": {
                    "full_name": full_name
                }
            }
        )

        user_id = auth_response.user.id

        # Create user profile in database
        profile_data = {
            "id": user_id,
            "full_name": full_name,
            "role": role,
            "company_id": company_id if role == "company_user" else None,
            "can_upload_data": can_upload_data,
            "is_active": True
        }

        supabase.table('user_profiles').insert(profile_data).execute()

        return {
            "success": True,
            "message": f"Invitation sent to {email}! They will receive an email to set their password."
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating user: {str(e)}"
        }
```

### Step 3: Update Create User Form

Remove the temporary password field:

```python
# OLD - Remove this:
temporary_password = st.text_input(
    "Temporary Password *",
    type="password"
)

# NEW - No password field needed!
# Just show info message:
st.info("💡 User will receive an email invitation to set their own password.")
```

### Step 4: Update Success Message

```python
if result["success"]:
    st.success(f"✅ {result['message']}")
    st.info(f"""
    📧 **Invitation Sent!**

    {email} will receive an email with:
    - Welcome message
    - "Set Password" button
    - Link valid for 24 hours

    They'll be able to access: {'All Companies' if role == 'super_admin' else company_name}
    """)
```

---

## Benefits of Email Invitation System

| Current (Manual) | Proposed (Invitation) |
|-----------------|----------------------|
| ❌ Admin creates temporary password | ✅ User creates their own password |
| ❌ Admin must share credentials manually | ✅ Email sent automatically |
| ❌ Less secure (password shared) | ✅ More secure (never shared) |
| ❌ User must change password later | ✅ User sets password immediately |
| ❌ Extra step for everyone | ✅ One-click setup |

---

## Testing the System

### Test Password Reset

1. Go to dashboard login page
2. Click "Forgot Password?"
3. Enter your email
4. Check inbox for reset email
5. Click link and create new password
6. Log in with new password

### Test User Invitation (After Implementation)

1. Log in as super admin
2. Go to User Management
3. Create a new user (enter email and details only)
4. Check the new user's inbox
5. User clicks "Set Password" link
6. User creates password
7. User logs in successfully

---

## Email Configuration in Supabase

### Required Settings

Go to **Authentication** → **Settings** → **SMTP**:

1. **Enable Custom SMTP** (optional, for branded emails)
   - Host: Your SMTP server
   - Port: 587 (TLS) or 465 (SSL)
   - Username: Your email username
   - Password: Your email password

2. **Or Use Supabase's Default SMTP**
   - Works out of the box
   - Emails sent from `noreply@mail.app.supabase.io`

### Email Templates Available

- **Confirm signup** - Email confirmation for new signups
- **Invite user** - Invitation email (what we'll use)
- **Magic link** - Passwordless login
- **Change email address** - Confirm email change
- **Reset password** - Password reset link (already working)

---

## Security Considerations

✅ **Password Reset:**
- Links expire in 1 hour
- One-time use only
- Requires email access

✅ **User Invitations:**
- Links expire in 24 hours
- One-time use only
- User creates secure password
- Email verification required

✅ **Best Practices:**
- Use strong passwords (8+ characters, mixed case, numbers, symbols)
- Never share passwords
- Change password if compromised
- Log out on shared devices

---

## Troubleshooting

### "Email not sent"
- Check Supabase SMTP settings
- Verify email address is valid
- Check spam/junk folder
- Ensure Supabase project is not paused

### "Link expired"
- Password reset: Valid for 1 hour
- Invitation: Valid for 24 hours
- Request a new link if expired

### "User already exists"
- Email already registered
- Delete old user first (if needed)
- Or use password reset instead

### "Password reset link doesn't work locally"
**This is expected when testing on localhost!**

**Why it happens:**
- Supabase reset links redirect to a URL you configure in Supabase
- Default: Supabase's hosted page (not your localhost)
- Your Streamlit app on localhost doesn't receive the reset token

**Workarounds:**
1. **For Development:** Super admins can manually reset passwords by:
   - Deleting the user
   - Recreating with new password
   - Or using `create_admin_quick.py` script

2. **For Production:** Once deployed to a real URL:
   - Configure that URL in Supabase → Authentication → URL Configuration
   - Set Site URL and Redirect URLs to your deployment URL
   - Password resets will work properly

**Current best practice:** For small teams during development, manual password sharing is acceptable. Implement full email flow when deploying to production.

---

## Next Steps

1. ✅ Test forgot password functionality (already working)
2. ⏳ Customize Supabase email templates
3. ✅ Implement invitation-based user creation (COMPLETE)
4. ✅ Update user management UI (COMPLETE)
5. ⏳ Test end-to-end invitation flow

---

## Questions?

Contact: [Add support email or admin contact]

Last Updated: November 2025
