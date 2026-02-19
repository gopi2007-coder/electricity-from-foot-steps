# System Architecture & Authentication Flow

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Web Browser                          │
│  (User accesses application via HTTP)                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
        ┌──────────────────────────────┐
        │   Flask Web Application      │
        │   (app.py - Port 5000)       │
        └───────────┬──────────────────┘
                    │
        ┌───────────┴──────────────┐
        │                          │
        ↓                          ↓
  ┌──────────────┐         ┌──────────────┐
  │  HTML        │         │  Database    │
  │  Templates   │         │  Files       │
  │  (Jinja2)    │         │              │
  └──────────────┘         │  users.txt   │
                           │  mfa_sess... │
  ┌──────────────┐         │  sessions/   │
  │  routes/     │         └──────────────┘
  │  decorators  │
  └──────────────┘
```

## Authentication Flow Diagram

```
START
  │
  ├─→ /                (Home Page)
  │     │
  │     ├─→ Check session
  │     │
  │     ├─→ If logged in → Show user info + dashboard link
  │     └─→ If not → Show login/register buttons
  │
  ├─→ /register        (User Registration)
  │     │
  │     └─→ Create new user account
  │         ├─→ Generate TOTP secret
  │         ├─→ Hash password (SHA256)
  │         ├─→ Store in users.txt
  │         └─→ Success message
  │
  ├─→ /login           (User Login Page)
  │     │
  │     └─→ Submit credentials
  │         │
  │         ├─→ /login (POST)
  │         │
  │         ├─→ Check users.txt for username
  │         │
  │         ├─→ Verify password hash
  │         │
  │         ├─→ If invalid → Show error
  │         │
  │         └─→ If valid:
  │             ├─→ Generate 6-digit OTP
  │             ├─→ Store MFA session
  │             ├─→ Print OTP to console
  │             └─→ Redirect to /verify-mfa
  │
  ├─→ /verify-mfa      (MFA Verification)
  │     │
  │     └─→ Choose authentication method
  │         │
  │         ├─→ Email OTP (Method A)
  │         │   ├─→ Check console for code
  │         │   ├─→ Enter 6-digit OTP
  │         │   └─→ Validate → Create session
  │         │
  │         └─→ TOTP (Method B)
  │             ├─→ Open authenticator app
  │             ├─→ Enter 6-digit code
  │             └─→ Validate → Create session
  │
  ├─→ /admin-login     (Admin Login Page)
  │     │
  │     └─→ Similar flow as user login
  │         ├─→ Check ADMIN_CREDENTIALS
  │         ├─→ Generate OTP
  │         └─→ Proceed to /verify-mfa
  │
  └─→ /dashboard/<username> (Protected - User Only)
      │
      ├─→ Check @login_required decorator
      │
      ├─→ If not logged in → Redirect to /login
      │
      └─→ If logged in:
          ├─→ Load user energy data
          ├─→ Calculate stats
          ├─→ Display dashboard
          └─→ Show recent records

  └─→ /admin-panel     (Protected - Admin Only)
      │
      ├─→ Check @admin_login_required decorator
      │
      ├─→ If not admin → Redirect to /admin-login
      │
      └─→ If admin:
          ├─→ Load all user stats
          ├─→ Calculate totals
          └─→ Display admin panel
```

## Session Management Flow

```
                Login Successful
                      │
                      ↓
        ┌─────────────────────────────┐
        │   Create Session Data:      │
        │  ├─ username                │
        │  ├─ user_type (user/admin)  │
        │  └─ permissions             │
        └────────────┬────────────────┘
                     │
                     ↓
        ┌────────────────────────────┐
        │  Sign Session ID Cookie    │
        └────────────┬───────────────┘
                     │
                     ↓
        ┌────────────────────────────┐
        │  Store Session on Server   │
        │  (sessions/ folder)        │
        └────────────┬───────────────┘
                     │
                     ↓
        ┌────────────────────────────┐
        │  Send Cookie to Browser    │
        └────────────┬───────────────┘
                     │
        User makes request with cookie
                     │
                     ↓
        ┌────────────────────────────┐
        │  Validate Session:         │
        │  ├─ Session exists?        │
        │  ├─ Not expired?           │
        │  ├─ User type correct?     │
        │  └─ Permissions OK?        │
        └────────────┬───────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
    Valid ✓                     Invalid ✗
        │                           │
        ↓                           ↓
   Process request        Redirect to login
```

## Security Architecture

```
┌────────────────────────────────────────┐
│         SECURITY LAYERS                │
└────────────────────────────────────────┘

Layer 1: Input Validation
  ├─ Username format check
  ├─ Email validation
  ├─ Password length check
  └─ OTP format validation

Layer 2: Authentication
  ├─ Credentials verification
  ├─ Hash comparison
  └─ Session creation

Layer 3: Authorization
  ├─ Route decorators (@login_required)
  ├─ User type checking (user vs admin)
  └─ Dashboard access control

Layer 4: Encryption
  ├─ Password → SHA256 hash
  ├─ Session → Signed cookie
  └─ Session data → Server-side storage

Layer 5: MFA
  ├─ Email OTP verification
  ├─ TOTP verification
  └─ OTP expiration
```

## Data Flow Diagram

```
User Input (Browser)
        │
        ↓
┌────────────────┐
│  HTML Forms    │
└────────┬───────┘
         │
         ↓
┌────────────────┐
│  Flask Routes  │
│  (POST/GET)    │
└────────┬───────┘
         │
         ├─→ Validate Input
         │
         ├─→ Check Database
         │   (users.txt)
         │
         ├─→ Hash/Compare
         │   (Passwords)
         │
         ├─→ Generate Session
         │   (secrets module)
         │
         ├─→ Store Session
         │   (sessions/ folder)
         │
         └─→ Return Response
             (HTML + Cookie)
             │
             ↓
         Browser stores Cookie
             │
             ↓
    Next request includes Cookie
             │
             ↓
   Server verifies session is valid
             │
             ↓
    Grant/Deny access
```

## Component Interaction

```
┌──────────────┐
│  app.py      │  ← Main Flask application
│              │
│  Routes:     │
│  ├─ /login   │
│  ├─ /register│
│  ├─ /verify- │
│  │  mfa      │
│  ├─ /logout  │
│  ├─ /admin-  │
│  │  panel    │
│  └─ ...      │
└────────┬─────┘
         │
    ┌────┴──────────┬──────────────┐
    │               │              │
    ↓               ↓              ↓
┌─────────┐  ┌────────────┐  ┌──────────┐
│templates│  │ Data Files │  │decorators│
│  HTML   │  │            │  │          │
│ Jinja2  │  │users.txt   │  │@required │
└─────────┘  │mfa_sess... │  │decorators│
             └────────────┘  └──────────┘
```

## Authentication Methods Comparison

```
┌──────────────────┬──────────────────┬──────────────────┐
│  FEATURE         │   EMAIL OTP      │      TOTP        │
├──────────────────┼──────────────────┼──────────────────┤
│ Code Length      │  6 digits        │  6 digits        │
│ Delivery         │  Email console*  │  Authenticator   │
│ Time Window      │  15 minutes      │  30 seconds      │
│ Device Needed    │  None (console)  │  Authenticator   │
│ Backup Codes     │  Not shown       │  Not shown       │
│ Setup Time       │  Instant         │  Scan QR code    │
│ Reliability      │  100%            │  High (sync)     │
│ Industry         │  Common          │  Very Common     │
│ Examples         │  Banking sites   │  Google, GitHub  │
└──────────────────┴──────────────────┴──────────────────┘

* In production: Real email service
  In development: Printed to console
```

## File Storage Structure

```
c:\h\
│
├── app.py                        ← Main application
│
├── templates/
│   ├── home.html                 ← Homepage
│   ├── login.html                ← User login
│   ├── register.html             ← Registration
│   ├── admin_login.html          ← Admin login
│   ├── mfa.html                  ← MFA verification
│   ├── admin_panel.html          ← Admin dashboard
│   ├── dashboard.html            ← User dashboard
│   ├── leaderboard.html          ← Leaderboard
│   └── energy_tiles.html         ← Energy tiles map
│
├── users.txt                     ← User database
│   Format: username|password_hash|email|mfa_secret|otp_secret
│
├── mfa_sessions.txt              ← Active MFA sessions
│   Format: session_id|username|user_type|otp|timestamp
│
├── sessions/                     ← Flask-Session storage
│   ├── {session_id_1}
│   ├── {session_id_2}
│   └── ...
│
├── user_data.txt                 ← User energy records
├── energy_records.txt            ← IoT sensor data
│
├── AUTH_DOCUMENTATION.md         ← Full documentation
├── QUICK_START.md                ← Quick reference
├── IMPLEMENTATION_SUMMARY.md     ← Summary of changes
└── SYSTEM_ARCHITECTURE.md        ← This file
```

---

## Key Security Concepts Implemented

1. **Password Hashing**: SHA256 (one-way encryption)
   - User password → Hash → Store
   - Verification: New password → Hash → Compare with stored

2. **Session Management**: Secure cookies
   - Session ID: Random 32-byte hex string
   - Stored on server, cookie in browser
   - Server validates every request

3. **Two-Factor Authentication**: Dual verification
   - Step 1: Username + password
   - Step 2: OTP (email or TOTP)
   - Both must pass for access

4. **Route Protection**: Python decorators
   - @login_required: Check session exists
   - @admin_login_required: Check admin session
   - Applied to protected routes

5. **Input Validation**: Server-side checking
   - Format validation
   - Type checking
   - Length validation

---

**Generated**: February 19, 2026
