# Quick Reference Card

## URLs Reference

| Page | URL | Purpose |
|------|-----|---------|
| Home | `/` | Main page |
| User Login | `/login` | User authentication |
| User Register | `/register` | Create new account |
| MFA Verify | `/verify-mfa` | 2FA verification |
| User Dashboard | `/dashboard/<username>` | User profile & stats |
| Leaderboard | `/leaderboard` | Global rankings |
| Energy Tiles | `/energy-tiles` | Tile locations |
| Admin Login | `/admin-login` | Admin authentication |
| Admin Panel | `/admin-panel` | Admin dashboard |
| Logout | `/logout` | End user session |
| Admin Logout | `/admin-logout` | End admin session |

## Default Admin Account

```
Username: admin
Password: admin123
```

⚠️ **Change in production!**

## User Roles & Permissions

### Regular User
- ✅ Create account via `/register`
- ✅ Login with username/password
- ✅ Verify via 2FA (Email OTP or TOTP)
- ✅ View own dashboard
- ✅ View leaderboard
- ✅ Submit energy records
- ❌ Access admin panel
- ❌ View other users' dashboards

### Administrator
- ✅ Access admin login (`/admin-login`)
- ✅ View admin panel (`/admin-panel`)
- ✅ See all user statistics
- ✅ View top contributors
- ✅ Monitor platform usage
- ❌ Cannot modify individual users (yet)

## Testing Credentials

### Create Test User
- **URL**: `/register`
- **Username**: `testuser`
- **Email**: `test@example.com`
- **Password**: `testpass123`

### Test Admin Login
- **URL**: `/admin-login`
- **Username**: `admin`
- **Password**: `admin123`

## MFA Methods

### Method 1: Email OTP
1. After entering credentials, you'll see MFA page
2. "Email OTP" tab is selected by default
3. **Look in Flask console for code like: `[DEBUG] MFA OTP for username: 123456`**
4. Copy the 6-digit number
5. Paste in the OTP field
6. Click "Verify & Login"

### Method 2: TOTP (Authenticator App)
1. After entering credentials, you'll see MFA page
2. Click "Authenticator" tab
3. Scan QR code with authenticator app OR manually add:
   - User's TOTP secret (shown on account setup)
   - Issuer: "EcoWalk 2026"
4. Enter 6-digit code from authenticator
5. Click "Verify & Login"

## Common Tasks

### Create New User Account
```
1. Go to /register
2. Fill in: username, email, password
3. Click "Create Account"
4. Go to /login to test account
```

### Login as User
```
1. Go to /login
2. Enter username and password
3. See MFA page
4. Choose authentication method
5. Enter OTP code (check console or app)
6. Access dashboard
```

### Access Admin Panel
```
1. Go to /admin-login
2. Use: admin / admin123
3. Complete MFA verification
4. View admin statistics
```

### Check OTP Code
```
When you use Email OTP:
- Look in Flask console output
- Find line: [DEBUG] MFA OTP for {username}: {6-digit code}
- Copy the 6-digit code
- Paste into MFA form
```

## File Descriptions

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application with all routes |
| `templates/login.html` | User login form |
| `templates/register.html` | User registration form |
| `templates/admin_login.html` | Admin login form |
| `templates/mfa.html` | MFA verification form |
| `templates/admin_panel.html` | Admin dashboard |
| `users.txt` | Database of user accounts |
| `mfa_sessions.txt` | Active MFA sessions |
| `sessions/` folder | Flask session storage |

## Features Implemented

✅ User registration with validation
✅ Secure password hashing (SHA256)
✅ Two-factor authentication (Email OTP)
✅ TOTP authenticator support
✅ Session management
✅ Admin-only routes
✅ User dashboard protection
✅ Logout functionality
✅ Error handling and messages
✅ Responsive design

## Troubleshooting Quick Tips

| Problem | Solution |
|---------|----------|
| "User not found" | Check username spelling (case-sensitive) |
| "Invalid OTP" | Copy full 6-digit code from console |
| App won't start | Install packages: `python -m pip install flask-session pyotp` |
| Can't see OTP code | Make sure Flask console is visible, run `python app.py` |
| "MFA session expired" | Start login process again |
| Port 5000 in use | Change port in app.py: `app.run(port=5001)` |

## Security Checklist

For Production Deployment:

- [ ] Change default admin password
- [ ] Enable HTTPS/SSL
- [ ] Implement real email service
- [ ] Use database instead of text files
- [ ] Add rate limiting
- [ ] Setup password reset flow
- [ ] Add backup codes
- [ ] Enable CSRF protection
- [ ] Setup logging/monitoring
- [ ] Review and update security headers

## Command Reference

```bash
# Start application
python app.py

# Install dependencies (if needed)
python -m pip install flask flask-session pyotp

# Check Python version
python --version

# Reset all data (delete files)
# Delete: users.txt, mfa_sessions.txt, sessions/
```

## Browser Access

```
Development:
http://127.0.0.1:5000/

Production:
https://yourdomain.com/
```

## Session Information

When logged in, session contains:
```python
session['username']    # Current logged-in user
session['user_type']   # 'user' or 'admin'
session.permanent      # Session persistence flag
```

## API Endpoints

### Public Routes (No Auth Required)
- `GET /` - Homepage
- `GET /login` - Login form
- `POST /login` - Login submission
- `GET /register` - Registration form
- `POST /register` - Registration submission
- `GET /admin-login` - Admin login form
- `POST /admin-login` - Admin login submission
- `GET /verify-mfa` - MFA form
- `POST /verify-mfa` - MFA submission

### Protected Routes (User Auth Required)
- `GET /dashboard/<username>` - User dashboard
- `GET /leaderboard` - Leaderboard
- `GET /energy-tiles` - Energy tiles map
- `POST /api/iot-sensor` - IoT data submission

### Protected Routes (Admin Auth Required)
- `GET /admin-panel` - Admin dashboard

### Logout Routes
- `GET /logout` - User logout
- `GET /admin-logout` - Admin logout

---

**Version**: 1.0  
**Last Updated**: February 19, 2026  
**Status**: ✅ Ready to Use
