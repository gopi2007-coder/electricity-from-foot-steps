# Authentication System Documentation

## Overview
This application now includes a comprehensive **Two-Factor Authentication (2FA)** system with separate login pages for users and administrators.

## Features

### 1. User Authentication
- **User Registration**: New users can create accounts at `/register`
- **User Login**: Users log in at `/login` with username and password
- **2FA via Email OTP**: After login, users receive a 6-digit OTP code via email (simulated in console)
- **TOTP Support**: Users can enable Time-based One-Time Password (TOTP) authenticator apps

### 2. Admin Authentication  
- **Admin Login**: Administrators log in at `/admin-login`
- **Admin Panel**: Secure admin dashboard at `/admin-panel` showing:
  - Total users registered
  - Total energy generated (Wh)
  - Total reward points distributed
  - Top 10 energy contributors

### 3. Session Management
- Secure session tracking using Flask-Session
- Session storage in the filesystem
- Automatic session timeout for security
- Clear separation between user and admin sessions

## Files Created/Modified

### New Templates
- `login.html` - User login page
- `admin_login.html` - Admin login page  
- `mfa.html` - MFA verification page with email OTP and TOTP options
- `register.html` - User registration page
- `admin_panel.html` - Admin dashboard

### Updated Files
- `app.py` - Added authentication routes and logic:
  - `POST /login` - User login
  - `POST /register` - User registration
  - `POST /admin-login` - Admin login
  - `GET/POST /verify-mfa` - MFA verification
  - `GET /logout` - User logout
  - `GET /admin-logout` - Admin logout
  - `GET /admin-panel` - Admin dashboard (protected)
  - `GET /dashboard/<username>` - Protected user dashboard

- `home.html` - Updated with auth navigation and user info display

### New Data Files
- `users.txt` - Stores user accounts (username|password_hash|email|mfa_secret|otp_secret)
- `mfa_sessions.txt` - Temporary storage for MFA sessions during verification

## Usage

### For Regular Users

1. **Register**: Go to `/register` and create a new account
   - Provide username, email, and password
   - Account is created with TOTP secret automatically

2. **Login**: Go to `/login`
   - Enter username and password
   - You'll be redirected to MFA verification

3. **MFA Verification**: 
   - Choose between Email OTP or TOTP
   - With Email OTP: Check console for 6-digit code (email integration needed for production)
   - With TOTP: Use your authenticator app (Google Authenticator, Microsoft Authenticator, Authy, etc.)
   - Enter the 6-digit code

4. **Dashboard**: After successful MFA verification, access your dashboard at `/dashboard/<username>`

5. **Logout**: Click the logout button to end your session

### For Administrators

1. **Login**: Go to `/admin-login`
   - Default credentials: `admin` / `admin123` 
   - **⚠️ Change these in production!**

2. **MFA Verification**:
   - Similar to user MFA process
   - Default admin will use email OTP method

3. **Admin Panel**: Access `/admin-panel` to view:
   - Platform statistics
   - Top contributors
   - User management metrics

## Security Features

### Password Security
- Passwords are hashed using SHA256
- Never stored in plain text
- Passwords verified during login

### Session Security
- Session IDs are randomly generated using `secrets.token_hex()`
- Sessions stored server-side (filesystem)
- Separate session tracking for users vs admins
- Automatic session requirements on protected routes

### MFA Security
- 2FA via Email OTP (6-digit code)
- 2FA via TOTP (Time-based One-Time Password)
- OTP codes expire after session timeout
- Temporary MFA session data stored separately

### Protected Routes
- `/dashboard/<username>` - Users can only view their own dashboard
- `/admin-panel` - Admin-only access
- Route decorators ensure authentication is enforced

## Configuration

### Admin Credentials
Edit `ADMIN_CREDENTIALS` in `app.py`:
```python
ADMIN_CREDENTIALS = {
    "admin": {"password_hash": hashlib.sha256("admin123".encode()).hexdigest(), "email": "admin@energy.com"}
}
```

### Flask Configuration
Current settings:
- `SESSION_TYPE = 'filesystem'` - Sessions stored on disk
- `SECRET_KEY` - Randomly generated on startup (use fixed key in production)

## Production Recommendations

1. **Change Admin Credentials**: Update the default admin password
2. **Email Integration**: Implement actual email sending for OTP codes
3. **HTTPS**: Use SSL/TLS certificates for all connections
4. **Database**: Replace text file storage with a proper database (SQLite, PostgreSQL, etc.)
5. **Session Storage**: Use Redis or database for session management
6. **TOTP QR Code**: Display QR codes for users to scan during TOTP setup
7. **Rate Limiting**: Implement login attempt limits
8. **Password Requirements**: Enforce strong password policies
9. **Email Verification**: Add email verification during registration

## Testing the System

### Test User Registration
```
Username: testuser
Email: test@example.com
Password: testpass123
```

### Test Login
1. Go to `/login`
2. Enter test user credentials
3. Check console for OTP code
4. Enter OTP code for verification

### Test Admin Panel
1. Go to `/admin-login`
2. Enter default admin credentials
3. Check MFA (OTP code in console)
4. View admin dashboard statistics

## Troubleshooting

**Issue**: "MFA session expired" error
- **Solution**: Log in again, MFA sessions have 15-minute timeout

**Issue**: Can't see console output for OTP
- **Solution**: Check Flask console output, or implement email integration

**Issue**: TOTP code not working
- **Solution**: Ensure device time is synchronized with server, try with email OTP

**Issue**: Session not persisting
- **Solution**: Ensure `flask_session` is installed and `sessions/` folder exists

## Dependencies

- `Flask` - Web framework
- `Flask-Session` - Server-side session management
- `PyOTP` - Time-based One-Time Password (TOTP) implementation

Install with:
```bash
pip install flask flask-session pyotp
```

## Future Enhancements

- [ ] Real email OTP delivery
- [ ] Automatic TOTP QR code generation
- [ ] Multi-factor authentication options (SMS, push notifications)
- [ ] Account recovery/password reset
- [ ] Login attempt logging and monitoring
- [ ] Two-device verification
- [ ] Backup codes for account recovery
- [ ] Biometric authentication support

---

**Last Updated**: February 19, 2026
**Version**: 1.0
