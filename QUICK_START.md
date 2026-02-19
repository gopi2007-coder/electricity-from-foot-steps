# Quick Start Guide - Login & MFA System

## Getting Started

### Start the Application
```bash
python app.py
```
The app will run on `http://127.0.0.1:5000`

## User Authentication Flow

### 1. New User Registration
- Navigate to `/register`
- Fill in: Username, Email, Password, Confirm Password
- Account created instantly with TOTP secret

### 2. User Login
- Navigate to `/login`
- Enter username and password
- Click "Login"
- Redirected to MFA verification page

### 3. Multi-Factor Authentication (Choose One)

#### Option A: Email OTP
- **Look in Flask console for 6-digit code**
- Copy the code from console output
- Enter it in the OTP field
- Click "Verify & Login"

#### Option B: Authenticator App (TOTP)
- Click "Authenticator" tab on MFA page
- Open Google Authenticator, Microsoft Authenticator, or Authy
- Scan QR code (currently must be added to app)
- Or add manually using the secret provided
- Enter the 6-digit code from your authenticator
- Click "Verify & Login"

### 4. User Dashboard
- After successful MFA verification, you'll land on your dashboard
- View energy records, points, tier, and stats
- Click "Logout" to sign out

## Admin Access

### Admin Login
- Navigate to `/admin-login`
- Use credentials: 
  - Username: `admin`
  - Password: `admin123`
- Follow MFA verification (check console for OTP)
- Access admin panel with platform statistics

⚠️ **Change admin password before production!**

## Test Accounts

You can create test accounts at `/register`:
- Any username (must be unique)
- Any email address
- Password (min 6 characters)

## Viewing OTP Codes

In development, OTP codes are printed to Flask console:
```
[DEBUG] MFA OTP for username: 123456
```

Look for this line in your Flask console output.

## Reset Everything

To start fresh with clean data:
```bash
# Delete these files to reset:
- users.txt (all user accounts)
- mfa_sessions.txt (active MFA sessions)
- user_data.txt (energy records)
- sessions/ folder (active sessions)
```

Then restart the app.

## File Structure

```
c:\h\
├── app.py                          # Main Flask application
├── templates/
│   ├── home.html                   # Home page
│   ├── login.html                  # User login
│   ├── admin_login.html            # Admin login
│   ├── register.html               # User registration
│   ├── mfa.html                    # MFA verification
│   ├── admin_panel.html            # Admin dashboard
│   ├── dashboard.html              # User dashboard
│   ├── leaderboard.html            # Global leaderboard
│   └── energy_tiles.html           # Energy tile map
├── users.txt                       # User database (auto-created)
├── mfa_sessions.txt                # MFA sessions (auto-created)
└── AUTH_DOCUMENTATION.md           # Full documentation
```

## Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| "User not found" on login | Username is case-sensitive, check spelling |
| "MFA session expired" | Start fresh login |
| "Invalid OTP code" | Copy code from Flask console output |
| Can't see Flask console | Run `python app.py` in terminal, don't use debug mode |
| Port 5000 already in use | Change `app.run(port=5001)` in app.py |

## Key Features

✅ User registration and login  
✅ Two-factor authentication (Email OTP + TOTP)  
✅ Admin login with separate credentials  
✅ Session management  
✅ Protected user dashboards  
✅ Admin statistics dashboard  
✅ Password hashing (SHA256)  
✅ Secure session IDs  

## Next Steps

1. **Test the system**: Create an account and log in
2. **Try MFA**: Verify account with both email OTP and TOTP
3. **Check admin panel**: Login as admin to see platform stats
4. **Review code**: Check `app.py` for authentication flow
5. **Customize**: Update admin credentials and styling

---

For detailed documentation, see `AUTH_DOCUMENTATION.md`
