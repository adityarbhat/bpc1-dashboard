# Authentication Flow - BPC Dashboard

## Visual Flowchart

```mermaid
flowchart TD
    Start([User Opens Dashboard]) --> CheckSession{Session<br/>Exists?}

    CheckSession -->|Yes| ValidateToken{Token<br/>Valid?}
    CheckSession -->|No| LoginPage[Show Login Page]

    ValidateToken -->|Yes| LoadDashboard[Load Dashboard]
    ValidateToken -->|No| LoginPage

    LoginPage --> EnterCreds[User Enters<br/>Email & Password]
    EnterCreds --> SendHTTPS[Send Credentials<br/>via HTTPS to Supabase]

    SendHTTPS --> ValidateCreds{Credentials<br/>Valid?}

    ValidateCreds -->|No| FailedLogin[Log Failed Attempt]
    FailedLogin --> SendFailEmail[Send Failed Login<br/>Email Alert]
    SendFailEmail --> ShowError[Show Error Message]
    ShowError --> LoginPage

    ValidateCreds -->|Yes| CheckPassword[Validate Password<br/>bcrypt hash]
    CheckPassword --> GenerateTokens[Generate JWT Tokens<br/>Access: 60 min<br/>Refresh: 24 hours]

    GenerateTokens --> StoreSession[Store Tokens in<br/>Server-Side Session]
    StoreSession --> LoadProfile[Load User Profile<br/>& Permissions]

    LoadProfile --> VerifyProfile{Profile<br/>Loaded?}

    VerifyProfile -->|No| ClearSession[Clear Session]
    ClearSession --> ShowError

    VerifyProfile -->|Yes| LogSuccess[Log Successful Login<br/>to Audit Trail]
    LogSuccess --> SendSuccessEmail[Send Successful Login<br/>Email Alert]
    SendSuccessEmail --> LoadDashboard

    LoadDashboard --> Timer[Start 60-Minute<br/>Session Timer]
    Timer --> UserActivity{User<br/>Activity?}

    UserActivity -->|Active| CheckExpiry{Token<br/>Expired?}
    UserActivity -->|Inactive 60min| AutoLogout[Auto-Logout]

    CheckExpiry -->|No| UserActivity
    CheckExpiry -->|Yes| RefreshToken{Refresh<br/>Available?}

    RefreshToken -->|Yes| GetNewToken[Get New Access Token]
    RefreshToken -->|No| AutoLogout

    GetNewToken --> UserActivity

    AutoLogout --> LogLogout[Log Logout Event]
    LogLogout --> ClearSessionData[Clear All Session Data<br/>& Cookies]
    ClearSessionData --> LoginPage

    LoadDashboard -.->|User Clicks Logout| ManualLogout[Manual Logout]
    ManualLogout --> LogLogout

    style Start fill:#e1f5ff
    style LoadDashboard fill:#c8e6c9
    style ValidateCreds fill:#fff9c4
    style FailedLogin fill:#ffcdd2
    style SendSuccessEmail fill:#c8e6c9
    style SendFailEmail fill:#ffcdd2
    style AutoLogout fill:#ffe0b2
    style CheckExpiry fill:#fff9c4
```

---

## Simplified Flow for CFOs

```mermaid
flowchart LR
    A[User Enters<br/>Email/Password] --> B[Supabase<br/>Validates]
    B --> C{Valid?}
    C -->|No| D[Email Alert:<br/>Failed Login]
    C -->|Yes| E[Create Secure<br/>Session]
    E --> F[Email Alert:<br/>Successful Login]
    F --> G[Dashboard Opens]
    G --> H[Auto-Logout<br/>After 60 Minutes]

    style A fill:#e1f5ff
    style B fill:#fff9c4
    style D fill:#ffcdd2
    style E fill:#c8e6c9
    style F fill:#c8e6c9
    style G fill:#c8e6c9
    style H fill:#ffe0b2
```

---

## Key Security Features

### 🔒 **Email Notifications**
- **Successful Login**: You receive an email every time your account is accessed
- **Failed Login**: You receive an email when wrong password is entered
- **Why it matters**: Immediate alert if someone tries to hack your account

### ⏱️ **60-Minute Auto-Logout**
- Sessions expire automatically after 1 hour
- **Analogy**: Like an ATM that cancels your transaction if you walk away
- **Why it matters**: Prevents hijacking if you forget to log out

### 🔐 **Password Security**
- Passwords are scrambled immediately (never stored as plain text)
- Even admins can't see your password
- **Analogy**: One-way shredder - once paper goes in, you can't get it back

### 📝 **Audit Trail**
- Every login/logout logged with timestamp and IP address
- Failed login attempts tracked
- **Why it matters**: Complete accountability - you can always see who did what and when

---

## Technical Details (For IT Manager)

### Authentication Protocol
- **Method**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt with cost factor 10 (1,024 iterations)
- **Token Expiry**: Access token = 60 minutes, Refresh token = 24 hours
- **Cookie Settings**: `HttpOnly=true`, `Secure=true`, `SameSite=strict`

### Session Management
- Server-side session storage (not browser-based)
- Token signature validation on every request
- Automatic token refresh within 24-hour window
- Server-side token invalidation on logout

### Email Notification System
- SMTP-based email delivery
- HTML email templates with security details
- Includes: timestamp, IP address, login status
- Sent for both successful and failed login attempts

### Security Standards
- **Encryption in Transit**: TLS 1.2+ (HTTPS)
- **Encryption at Rest**: AES-256
- **Compliance**: OWASP Top 10 aligned, GDPR compatible
- **Platform**: Supabase (SOC 2 Type II certified)

---

## Flow Explanation

### Step-by-Step Authentication

1. **User Visits Dashboard**
   - System checks if valid session exists
   - If yes, validates token signature and expiry
   - If valid, loads dashboard immediately

2. **Login Required**
   - User enters email and password
   - Credentials sent over HTTPS to Supabase
   - Supabase validates against bcrypt-hashed password

3. **Failed Login**
   - Attempt logged to audit trail
   - Failed login email sent to user
   - Error message shown to user
   - User can try again

4. **Successful Login**
   - JWT tokens generated (access + refresh)
   - Tokens stored in server-side session
   - User profile and permissions loaded
   - Successful login logged to audit trail
   - Success email sent to user
   - Dashboard loads

5. **Active Session**
   - 60-minute timer starts
   - Every page load validates token
   - Token automatically refreshed if within 24-hour window
   - User activity resets idle timer

6. **Session Expiry**
   - After 60 minutes of inactivity, auto-logout
   - Or user manually clicks logout
   - Logout event logged to audit trail
   - All session data and cookies cleared
   - User redirected to login page

---

## Security Benefits

### Defense in Depth (7 Layers)

1. **Network Layer**: TLS 1.2+ encryption (HTTPS)
2. **Platform Layer**: Render DDoS protection
3. **Application Layer**: Supabase authentication
4. **Session Layer**: JWT token validation
5. **Database Layer**: PostgreSQL Row-Level Security
6. **Audit Layer**: Complete logging of all events
7. **User Layer**: Email notifications for awareness

### Zero Trust Model

- Every request is validated (no assumed trust)
- Tokens expire quickly (reduces hijack window)
- Permissions checked at 3 levels:
  1. UI (hide/disable unauthorized elements)
  2. Application (permission checks before actions)
  3. Database (RLS policies block unauthorized queries)

---

**Created for**: BPC Dashboard Presentation
**Audience**: CFOs + IT Manager
**Last Updated**: December 2025
