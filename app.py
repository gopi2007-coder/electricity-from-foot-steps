from flask import Flask, render_template, request, redirect, jsonify, session
from flask_session import Session
import json
import math
from datetime import datetime
import hashlib
import secrets
import pyotp
import smtplib
from email.mime.text import MIMEText
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# ============= ADMIN CREDENTIALS =============
ADMIN_CREDENTIALS = {
    "admin": {"password_hash": hashlib.sha256("admin123".encode()).hexdigest(), "email": "admin@energy.com"}
}

def load_admin_credentials():
    """Load admin accounts from storage"""
    credentials = {}
    try:
        with open("admin_credentials.txt", "r") as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split("|")
                    if len(parts) >= 3:
                        username = parts[0]
                        credentials[username] = {
                            "password_hash": parts[1],
                            "email": parts[2]
                        }
    except:
        # Initialize with default admin if file doesn't exist
        credentials = ADMIN_CREDENTIALS.copy()
    return credentials

def save_admin_credentials(credentials):
    """Save admin credentials to storage"""
    with open("admin_credentials.txt", "w") as f:
        for username in credentials:
            admin = credentials[username]
            f.write(f"{username}|{admin['password_hash']}|{admin['email']}\n")

# ============= AUTHENTICATION DATABASE FUNCTIONS =============
def load_users():
    """Load user accounts with credentials"""
    users = {}
    try:
        with open("users.txt", "r") as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split("|")
                    if len(parts) >= 5:
                        username = parts[0]
                        users[username] = {
                            "password_hash": parts[1],
                            "email": parts[2],
                            "mfa_secret": parts[3],
                            "otp_secret": parts[4] if len(parts) > 4 else None
                        }
    except:
        pass
    return users


def load_active_users():
    """Load currently active (logged-in) users from storage"""
    active = set()
    try:
        with open("active_users.txt", "r") as f:
            for line in f:
                u = line.strip()
                if u:
                    active.add(u)
    except:
        pass
    return active


def save_active_users(active_set):
    """Save active users set to storage"""
    try:
        with open("active_users.txt", "w") as f:
            for u in sorted(active_set):
                f.write(u + "\n")
    except Exception:
        pass

def save_users(users):
    """Save user accounts"""
    with open("users.txt", "w") as f:
        for username in users:
            user = users[username]
            f.write(f"{username}|{user['password_hash']}|{user['email']}|{user['mfa_secret']}|{user.get('otp_secret', '')}\n")

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    """Verify password hash"""
    return stored_hash == hash_password(password)

def generate_mfa_secret():
    """Generate TOTP secret for user"""
    return pyotp.random_base32()

def load_mfa_sessions():
    """Load pending MFA sessions"""
    sessions = {}
    try:
        with open("mfa_sessions.txt", "r") as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split("|")
                    if len(parts) >= 4:
                        session_id = parts[0]
                        sessions[session_id] = {
                            "username": parts[1],
                            "user_type": parts[2],
                            "otp": parts[3],
                            "timestamp": float(parts[4]) if len(parts) > 4 else 0
                        }
    except:
        pass
    return sessions

def save_mfa_sessions(sessions):
    """Save MFA sessions"""
    with open("mfa_sessions.txt", "w") as f:
        for session_id in sessions:
            s = sessions[session_id]
            f.write(f"{session_id}|{s['username']}|{s['user_type']}|{s['otp']}|{s['timestamp']}\n")

# ============= ENERGY TILE DATABASE =============
# Default tiles - will be created on first run
DEFAULT_ENERGY_TILES = {
    "tile_001": {"name": "Shibuya Crossing", "lat": 35.6595, "lon": 139.7004, "radius": 0.001, "capacity": 1000, "usage_count": 0},
    "tile_002": {"name": "Tokyo Station", "lat": 35.6762, "lon": 139.7674, "radius": 0.001, "capacity": 800, "usage_count": 0},
    "tile_003": {"name": "Shinjuku Station", "lat": 35.5308, "lon": 139.7100, "radius": 0.001, "capacity": 900, "usage_count": 0},
    "tile_004": {"name": "Harajuku", "lat": 35.6654, "lon": 139.7033, "radius": 0.0015, "capacity": 700, "usage_count": 0},
    "tile_005": {"name": "Ginza", "lat": 35.6730, "lon": 139.7725, "radius": 0.0012, "capacity": 600, "usage_count": 0},
}

def load_energy_tiles():
    """Load energy tiles from storage"""
    tiles = {}
    try:
        with open("energy_tiles.txt", "r") as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split("|")
                    if len(parts) >= 6:
                        tile_id = parts[0]
                        tiles[tile_id] = {
                            "name": parts[1],
                            "lat": float(parts[2]),
                            "lon": float(parts[3]),
                            "radius": float(parts[4]),
                            "capacity": int(parts[5]),
                            "usage_count": int(parts[6]) if len(parts) > 6 else 0
                        }
    except:
        # Initialize with default tiles if file doesn't exist
        tiles = DEFAULT_ENERGY_TILES.copy()
        save_energy_tiles(tiles)
    return tiles

def save_energy_tiles(tiles):
    """Save energy tiles to storage"""
    with open("energy_tiles.txt", "w") as f:
        for tile_id in tiles:
            tile = tiles[tile_id]
            usage = tile.get('usage_count', 0)
            f.write(f"{tile_id}|{tile['name']}|{tile['lat']}|{tile['lon']}|{tile['radius']}|{tile['capacity']}|{usage}\n")

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in kilometers"""
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def is_on_energy_tile(user_lat, user_lon):
    """Check if user is on an energy tile and return tile info"""
    energy_tiles = load_energy_tiles()
    for tile_id, tile_info in energy_tiles.items():
        distance = calculate_distance(user_lat, user_lon, tile_info["lat"], tile_info["lon"])
        # Convert radius from degrees to km (approximately)
        if distance < (tile_info["radius"] * 111):  # 1 degree ≈ 111 km
            return tile_id, tile_info
    return None, None

def ensure_monthly_reset(user_data, username):
    """Reset monthly counters when a new month is reached."""
    now_month = datetime.now().strftime("%Y-%m")
    user = user_data.get(username)
    if not user:
        return
    if user.get("last_reset_month") != now_month:
        user["monthly_energy_wh"] = 0
        user["monthly_voltage"] = 0
        user["monthly_ampere"] = 0
        user["monthly_pressure"] = 0
        user["monthly_reward_points"] = 0
        user["monthly_steps"] = 0
        user["last_reset_month"] = now_month

def load_user_data():
    """Load all user data including energy records and rewards"""
    data = {}
    try:
        with open("user_data.txt", "r") as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split("|")
                    # expanded fields: username|total_energy_wh|reward_points|tiles_visited|total_steps|pressure|ampere|voltage|monthly_energy|monthly_voltage|monthly_ampere|monthly_pressure|monthly_reward|monthly_steps|last_reset_month
                    if len(parts) >= 5:
                        username = parts[0]
                        user = {
                            "total_energy_wh": float(parts[1]),
                            "reward_points": float(parts[2]),
                            "tiles_visited": int(parts[3]),
                            "total_steps": int(parts[4]),
                            "pressure_given": float(parts[5]) if len(parts) > 5 else 0,
                            "ampere": float(parts[6]) if len(parts) > 6 else 0,
                            "voltage": float(parts[7]) if len(parts) > 7 else 0,
                            "monthly_energy_wh": float(parts[8]) if len(parts) > 8 else 0,
                            "monthly_voltage": float(parts[9]) if len(parts) > 9 else 0,
                            "monthly_ampere": float(parts[10]) if len(parts) > 10 else 0,
                            "monthly_pressure": float(parts[11]) if len(parts) > 11 else 0,
                            "monthly_reward_points": float(parts[12]) if len(parts) > 12 else 0,
                            "monthly_steps": int(parts[13]) if len(parts) > 13 else 0,
                            "last_reset_month": parts[14] if len(parts) > 14 else ""
                        }
                        data[username] = user
    except:
        pass
    return data

def save_user_data(data):
    """Save user data to persistent storage"""
    with open("user_data.txt", "w") as f:
        for username in data:
            user = data[username]
            # ensure all monthly fields exist
            f.write(f"{username}|{user['total_energy_wh']}|{user['reward_points']}|{user['tiles_visited']}|{user['total_steps']}|{user.get('pressure_given', 0)}|{user.get('ampere', 0)}|{user.get('voltage', 0)}|{user.get('monthly_energy_wh', 0)}|{user.get('monthly_voltage', 0)}|{user.get('monthly_ampere', 0)}|{user.get('monthly_pressure', 0)}|{user.get('monthly_reward_points', 0)}|{user.get('monthly_steps', 0)}|{user.get('last_reset_month', '')}\n")

def load_energy_records():
    """Load IoT energy tile records"""
    records = []
    try:
        with open("energy_records.txt", "r") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    except:
        pass
    return records

def save_energy_record(record):
    """Save IoT sensor data"""
    with open("energy_records.txt", "a") as f:
        f.write(json.dumps(record) + "\n")

def calculate_reward_points(electricity_wh):
    """Convert electricity generated to reward points
    Formula: 1 Wh = 100 reward points"""
    return round(electricity_wh * 100, 2)

def get_tier(reward_points):
    """Get user tier based on reward points"""
    if reward_points >= 100000:
        return "💎 Platinum Contributor"
    elif reward_points >= 50000:
        return "🏆 Gold Contributor"
    elif reward_points >= 20000:
        return "🥈 Silver Contributor"
    elif reward_points >= 10000:
        return "🥉 Bronze Contributor"
    elif reward_points >= 5000:
        return "⚡ Energy Generator"
    else:
        return "🔋 Starter"


# ============= AUTHENTICATION DECORATORS & UTILITIES =============
def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('user_type') != 'user':
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def admin_login_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('user_type') != 'admin':
            return redirect('/admin-login')
        return f(*args, **kwargs)
    return decorated_function


# ============= AUTHENTICATION ROUTES =============
@app.route("/login", methods=["GET", "POST"])
def login():
    """User login page"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        users = load_users()
        
        if username in users and verify_password(users[username]["password_hash"], password):
            # Login successful for normal user - NO MFA required
            session['username'] = username
            session['user_type'] = 'user'
            session.permanent = True
            # mark user active
            active = load_active_users()
            active.add(username)
            save_active_users(active)

            return redirect(f'/dashboard/{username}')
        else:
            return render_template("login.html", error="Invalid username or password")
    
    return render_template("login.html")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    if request.method == "POST":
        admin_username = request.form.get("admin_username")
        admin_password = request.form.get("admin_password")
        
        admin_credentials = load_admin_credentials()
        
        if admin_username in admin_credentials and verify_password(admin_credentials[admin_username]["password_hash"], admin_password):
            # Generate OTP for MFA - Fixed OTP for admin: 000000
            otp_code = "000000"
            mfa_session_id = secrets.token_hex(16)
            
            mfa_sessions = load_mfa_sessions()
            mfa_sessions[mfa_session_id] = {
                "username": admin_username,
                "user_type": "admin",
                "otp": otp_code,
                "timestamp": datetime.now().timestamp()
            }
            save_mfa_sessions(mfa_sessions)
            
            session['mfa_session_id'] = mfa_session_id
            
            print(f"[DEBUG] MFA OTP for admin {admin_username}: {otp_code}")
            
            return redirect('/verify-mfa?user_type=admin&username=' + admin_username)
        else:
            return render_template("admin_login.html", error="Invalid admin credentials")
    
    return render_template("admin_login.html")


@app.route("/verify-mfa", methods=["GET", "POST"])
def verify_mfa():
    """MFA verification page"""
    if request.method == "POST":
        mfa_session_id = session.get('mfa_session_id')
        mfa_method = request.form.get("mfa_method", "email")
        user_type = request.form.get("user_type")
        username = request.form.get("username")
        
        mfa_sessions = load_mfa_sessions()
        
        if mfa_session_id not in mfa_sessions:
            return render_template("mfa.html", user_type=user_type, username=username, 
                                 error="MFA session expired. Please login again.")
        
        mfa_data = mfa_sessions[mfa_session_id]
        
        if mfa_method == "email":
            email_otp = request.form.get("email_otp")
            if email_otp == mfa_data["otp"]:
                # Clear MFA session
                del mfa_sessions[mfa_session_id]
                save_mfa_sessions(mfa_sessions)
                
                # Create user session
                session['username'] = mfa_data['username']
                session['user_type'] = mfa_data['user_type']
                session.permanent = True
                
                if mfa_data['user_type'] == 'admin':
                    return redirect('/admin-panel')
                else:
                    return redirect(f'/dashboard/{mfa_data["username"]}')
            else:
                return render_template("mfa.html", user_type=user_type, username=username, 
                                     error="Invalid OTP code. Please try again.")
        
        elif mfa_method == "totp":
            totp_code = request.form.get("totp_code")
            users = load_users()
            
            if mfa_data['user_type'] == 'user' and mfa_data['username'] in users:
                user = users[mfa_data['username']]
                if user.get('mfa_secret'):
                    totp = pyotp.TOTP(user['mfa_secret'])
                    if totp.verify(totp_code):
                        # Clear MFA session
                        del mfa_sessions[mfa_session_id]
                        save_mfa_sessions(mfa_sessions)
                        
                        # Create user session
                        session['username'] = mfa_data['username']
                        session['user_type'] = mfa_data['user_type']
                        session.permanent = True
                        
                        return redirect(f'/dashboard/{mfa_data["username"]}')
            
            return render_template("mfa.html", user_type=user_type, username=username, 
                                 error="Invalid TOTP code. Please try again.")
    
    user_type = request.args.get("user_type", "user")
    username = request.args.get("username", "")
    
    return render_template("mfa.html", user_type=user_type, username=username)


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration page"""
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        users = load_users()
        
        # Validation
        if not username or len(username) < 3:
            return render_template("register.html", error="Username must be at least 3 characters")
        
        if username in users:
            return render_template("register.html", error="Username already exists")
        
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")
        
        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters")
        
        # Create new user
        users[username] = {
            "password_hash": hash_password(password),
            "email": email,
            "mfa_secret": generate_mfa_secret(),
            "otp_secret": None
        }
        save_users(users)
        
        # Initialize user data
        user_data = load_user_data()
        user_data[username] = {
            "total_energy_wh": 0,
            "reward_points": 0,
            "pressure_given": 0,
            "ampere": 0,
            "voltage": 0,
            "total_steps": 0
        }
        save_user_data(user_data)
        
        return render_template("register.html", message="Account created successfully! Please login.")
    
    return render_template("register.html")


@app.route("/admin-register", methods=["GET", "POST"])
def admin_register():
    """Admin registration page"""
    if request.method == "POST":
        admin_username = request.form.get("admin_username")
        admin_email = request.form.get("admin_email")
        admin_password = request.form.get("admin_password")
        confirm_password = request.form.get("confirm_password")
        
        admin_credentials = load_admin_credentials()
        
        # Validation
        if not admin_username or len(admin_username) < 3:
            return render_template("admin_register.html", error="Admin username must be at least 3 characters")
        
        if admin_username in admin_credentials:
            return render_template("admin_register.html", error="Admin username already exists")
        
        if admin_password != confirm_password:
            return render_template("admin_register.html", error="Passwords do not match")
        
        if len(admin_password) < 6:
            return render_template("admin_register.html", error="Password must be at least 6 characters")
        
        # Create new admin account
        admin_credentials[admin_username] = {
            "password_hash": hash_password(admin_password),
            "email": admin_email
        }
        save_admin_credentials(admin_credentials)
        
        return render_template("admin_register.html", message="Admin account created successfully! Please login.")
    
    return render_template("admin_register.html")


@app.route("/logout")
def logout():
    """Logout user"""
    # remove from active users
    username = session.get('username')
    try:
        active = load_active_users()
        if username in active:
            active.remove(username)
            save_active_users(active)
    except Exception:
        pass
    session.clear()
    return redirect('/login')


@app.route("/admin-logout")
def admin_logout():
    """Logout admin"""
    session.clear()
    return redirect('/admin-login')


@app.route("/admin-panel")
@admin_login_required
def admin_panel():
    """Admin dashboard"""
    user_data = load_user_data()
    
    total_users = len(user_data)
    total_energy = sum(u["total_energy_wh"] for u in user_data.values())
    total_points = sum(u["reward_points"] for u in user_data.values())
    total_pressure = sum(u.get("pressure_given", 0) for u in user_data.values())
    total_ampere = sum(u.get("ampere", 0) for u in user_data.values())
    total_voltage = sum(u.get("voltage", 0) for u in user_data.values())
    
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]["reward_points"], reverse=True)[:10]
    top_users = []
    for rank, (username, data) in enumerate(sorted_users, 1):
        # Ensure all fields have defaults
        data_with_defaults = {
            "total_energy_wh": data.get("total_energy_wh", 0),
            "reward_points": data.get("reward_points", 0),
            "pressure_given": data.get("pressure_given", 0),
            "ampere": data.get("ampere", 0),
            "voltage": data.get("voltage", 0)
        }
        top_users.append((rank, username, data_with_defaults))
    
    # Convert tiles dict to list for template
    tiles_list = []
    for tile_id, tile in load_energy_tiles().items():
        tiles_list.append({
            "id": tile_id,
            "name": tile["name"],
            "lat": tile["lat"],
            "lon": tile["lon"],
            "radius": tile["radius"],
            "capacity": tile["capacity"],
            "usage_count": tile.get("usage_count", 0)
        })
    
    return render_template("admin_panel.html",
        total_users=total_users,
        total_energy=round(total_energy, 2),
        total_points=int(total_points),
        total_pressure=round(total_pressure, 2),
        total_ampere=round(total_ampere, 2),
        total_voltage=round(total_voltage, 2),
        top_users=top_users,
        energy_tiles=tiles_list
    )



@app.route("/", methods=["GET"])
def home():
    # If not logged in, redirect to login
    if 'username' not in session or session.get('user_type') != 'user':
        return redirect("/login")
    
    return render_template("home.html", username=session['username'])


@app.route("/api/iot-sensor", methods=["POST"])
def iot_sensor_endpoint():
    """IoT endpoint for sensors to submit energy data to a specific tile"""
    try:
        data = request.get_json()
        
        username = data.get("username")
        tile_id = data.get("tile_id")
        electricity_wh = float(data.get("electricity_wh", 0))
        user_lat = data.get("latitude")
        user_lon = data.get("longitude")
        
        if not username or not tile_id:
            return jsonify({"status": "error", "message": "Missing username or tile_id"}), 400
        
        # Load and verify tile exists
        energy_tiles = load_energy_tiles()
        if tile_id not in energy_tiles:
            return jsonify({"status": "error", "message": "Invalid tile_id"}), 400
        
        tile_info = energy_tiles[tile_id]
        
        # Record sensor data
        energy_record = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "tile_id": tile_id,
            "tile_name": tile_info["name"],
            "location": {"lat": user_lat, "lon": user_lon} if user_lat and user_lon else {},
            "electricity_wh": round(electricity_wh, 4),
            "tile_lat": tile_info["lat"],
            "tile_lon": tile_info["lon"]
        }
        save_energy_record(energy_record)
        
        # Update user account
        user_data = load_user_data()
        if username not in user_data:
            user_data[username] = {
                "total_energy_wh": 0,
                "reward_points": 0,
                "pressure_given": 0,
                "ampere": 0,
                "voltage": 0,
                "total_steps": 0
            }
        
        reward_points = calculate_reward_points(electricity_wh)
        user_data[username]["total_energy_wh"] += electricity_wh
        user_data[username]["reward_points"] += reward_points
        
        save_user_data(user_data)
        
        return jsonify({
            "status": "success",
            "electricity_wh": round(electricity_wh, 4),
            "reward_points": reward_points,
            "tile_name": tile_info["name"]
        })
    except Exception as e:
        print(f"IoT Sensor Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/check-gps-location", methods=["POST"])
@login_required
def check_gps_location():
    """Check user's GPS location and calculate generated power if on a tile"""
    try:
        data = request.get_json()
        username = session.get('username')
        user_lat = float(data.get("latitude"))
        user_lon = float(data.get("longitude"))
        
        if not username:
            return jsonify({"status": "error", "message": "Not logged in"}), 401
        
        # Check if user is on an energy tile
        tile_id, tile_info = is_on_energy_tile(user_lat, user_lon)
        
        if not tile_id:
            return jsonify({
                "status": "no_tile",
                "message": "Not on any energy tile",
                "nearby_tiles": get_nearby_tiles(user_lat, user_lon)
            })
        
        # Determine if user location is an exact match to the tile location
        # Use a small epsilon (degrees) roughly ~5m (0.00005° ≈ 5.5m)
        exact_match_epsilon = 0.00005
        exact_match = (abs(user_lat - tile_info["lat"]) <= exact_match_epsilon and
                       abs(user_lon - tile_info["lon"]) <= exact_match_epsilon)

        # Generate power values based on tile capacity and random user activity
        import random
        if exact_match:
            # Stronger readings when the user is standing exactly on the tile center
            base_power_wh = tile_info["capacity"] * 0.002 * random.uniform(0.8, 1.2)
            voltage_generated = random.uniform(10, 20)
            ampere_generated = random.uniform(0.5, 1.0)
            pressure_applied = random.uniform(150, 350)
        else:
            # Simulate power generation for near-miss or within tile radius
            base_power_wh = tile_info["capacity"] * 0.001 * random.uniform(0.4, 1.0)
            voltage_generated = random.uniform(5, 15)
            ampere_generated = random.uniform(0.1, 0.5)
            pressure_applied = random.uniform(50, 150)
        
        # Update user data
        user_data = load_user_data()
        # make sure monthly counters are reset if a new month has started
        ensure_monthly_reset(user_data, username)
        if username not in user_data:
            user_data[username] = {
                "total_energy_wh": 0,
                "reward_points": 0,
                "tiles_visited": 0,
                "total_steps": 0,
                "pressure_given": 0,
                "ampere": 0,
                "voltage": 0
            }
            # initialize monthly fields too
            user_data[username]["monthly_energy_wh"] = 0
            user_data[username]["monthly_voltage"] = 0
            user_data[username]["monthly_ampere"] = 0
            user_data[username]["monthly_pressure"] = 0
            user_data[username]["monthly_reward_points"] = 0
            user_data[username]["monthly_steps"] = 0
            user_data[username]["last_reset_month"] = datetime.now().strftime("%Y-%m")
        
        # Calculate reward points for this generation
        reward_points = calculate_reward_points(base_power_wh)

        # Update metrics
        user_data[username]["total_energy_wh"] += base_power_wh
        user_data[username]["pressure_given"] += pressure_applied
        user_data[username]["ampere"] += ampere_generated
        user_data[username]["voltage"] += voltage_generated
        user_data[username]["total_steps"] += 1
        # also accumulate monthly stats
        user_data[username]["monthly_energy_wh"] = user_data[username].get("monthly_energy_wh", 0) + base_power_wh
        user_data[username]["monthly_voltage"] = user_data[username].get("monthly_voltage", 0) + voltage_generated
        user_data[username]["monthly_ampere"] = user_data[username].get("monthly_ampere", 0) + ampere_generated
        user_data[username]["monthly_pressure"] = user_data[username].get("monthly_pressure", 0) + pressure_applied
        user_data[username]["monthly_steps"] = user_data[username].get("monthly_steps", 0) + 1
        user_data[username]["monthly_reward_points"] = user_data[username].get("monthly_reward_points", 0) + reward_points

        user_data[username]["reward_points"] += reward_points
        
        save_user_data(user_data)
        
        # Save energy record (include exact_match flag)
        energy_record = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "tile_id": tile_id,
            "tile_name": tile_info["name"],
            "location": {"lat": user_lat, "lon": user_lon},
            "electricity_wh": round(base_power_wh, 4),
            "voltage": round(voltage_generated, 2),
            "ampere": round(ampere_generated, 2),
            "pressure": round(pressure_applied, 2),
            "exact_match": bool(exact_match),
            "tile_lat": tile_info["lat"],
            "tile_lon": tile_info["lon"]
        }
        save_energy_record(energy_record)
        
        return jsonify({
            "status": "success",
            "tile_name": tile_info["name"],
            "tile_id": tile_id,
            "electricity_wh": round(base_power_wh, 4),
            "voltage": round(voltage_generated, 2),
            "ampere": round(ampere_generated, 2),
            "pressure": round(pressure_applied, 2),
            "exact_match": bool(exact_match),
            "reward_points": round(reward_points, 2),
            "total_energy": round(user_data[username]["total_energy_wh"], 4),
            "monthly_energy": round(user_data[username].get("monthly_energy_wh", 0), 4),
            "monthly_voltage": round(user_data[username].get("monthly_voltage", 0), 2),
            "monthly_ampere": round(user_data[username].get("monthly_ampere", 0), 2),
            "monthly_pressure": round(user_data[username].get("monthly_pressure", 0), 2),
            "total_voltage": round(user_data[username]["voltage"], 2),
            "total_ampere": round(user_data[username]["ampere"], 2),
            "total_pressure": round(user_data[username]["pressure_given"], 2)
        })
    
    except Exception as e:
        print(f"GPS Location Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


def get_nearby_tiles(user_lat, user_lon, radius_km=1):
    """Get tiles within a certain radius of user location"""
    energy_tiles = load_energy_tiles()
    nearby = []
    
    for tile_id, tile_info in energy_tiles.items():
        distance = calculate_distance(user_lat, user_lon, tile_info["lat"], tile_info["lon"])
        if distance < radius_km:
            nearby.append({
                "id": tile_id,
                "name": tile_info["name"],
                "distance_km": round(distance, 3),
                "lat": tile_info["lat"],
                "lon": tile_info["lon"]
            })
    
    return sorted(nearby, key=lambda x: x["distance_km"])


@app.route("/dashboard")
@login_required
def dashboard_root():
    # Redirect generic dashboard access to the logged-in user
    username = session.get('username')
    if not username:
        return redirect('/')
    return redirect(f"/dashboard/{username}")


@app.route("/dashboard/<username>")
@login_required
def dashboard(username):
    """5️⃣ USER DASHBOARD - View energy, points, and rewards"""
    # Only allow users to view their own dashboard
    if session.get('username') != username:
        return redirect(f"/dashboard/{session['username']}")
    
    user_data = load_user_data()
    
    if username not in user_data:
        # Initialize a fresh user data record if missing so dashboard can show
        user_data[username] = {
            "total_energy_wh": 0.0,
            "reward_points": 0.0,
            "tiles_visited": 0,
            "total_steps": 0,
            "pressure_given": 0.0,
            "ampere": 0.0,
            "voltage": 0.0,
            "monthly_energy_wh": 0.0,
            "monthly_voltage": 0.0,
            "monthly_ampere": 0.0,
            "monthly_pressure": 0.0,
            "monthly_reward_points": 0.0,
            "monthly_steps": 0,
            "last_reset_month": datetime.now().strftime("%Y-%m")
        }
        save_user_data(user_data)
    
    user = user_data[username]
    tier = get_tier(user["reward_points"])
    
    # Get recent energy records
    all_records = load_energy_records()
    user_records = [r for r in all_records if r["username"] == username][-5:]
    # Calculate today's energy and today's reward points
    today = datetime.now().date()
    todays_records = [r for r in all_records if r["username"] == username and datetime.fromisoformat(r["timestamp"]).date() == today]
    todays_energy = sum(r.get("electricity_wh", 0) for r in todays_records)
    todays_reward_points = int(calculate_reward_points(todays_energy))
    # ensure monthly statistics are up to date/reset
    ensure_monthly_reset(user_data, username)
    # save in case reset occurred
    save_user_data(user_data)

    # Determine user's last known location from most recent record (if any)
    latest_user_record = None
    for r in reversed(all_records):
        if r.get("username") == username and r.get("location") and r["location"].get("lat") is not None:
            latest_user_record = r
            break

    user_lat = None
    user_lon = None
    if latest_user_record:
        try:
            user_lat = float(latest_user_record["location"].get("lat"))
            user_lon = float(latest_user_record["location"].get("lon"))
        except Exception:
            user_lat = None
            user_lon = None

    # Prepare tiles with distances (if user location available)
    tiles_list = []
    for tile_id, info in load_energy_tiles().items():
        distance_km = None
        if user_lat is not None and user_lon is not None:
            try:
                distance_km = round(calculate_distance(user_lat, user_lon, info["lat"], info["lon"]), 3)
            except Exception:
                distance_km = None
        tiles_list.append({
            "id": tile_id,
            "name": info["name"],
            "lat": info["lat"],
            "lon": info["lon"],
            "capacity": info.get("capacity", 0),
            "distance_km": distance_km
        })

    # Active users and active tiles counts
    active_users = load_active_users()
    active_users_count = len(active_users)
    active_tiles_count = len(tiles_list)

    # Leaderboard (top 10)
    all_user_data = load_user_data()
    sorted_users = sorted(all_user_data.items(), key=lambda x: x[1]["reward_points"], reverse=True)[:10]
    leaderboard = []
    for rank, (uname, udata) in enumerate(sorted_users, 1):
        leaderboard.append({
            "rank": rank,
            "username": uname,
            "energy_wh": round(udata.get("total_energy_wh", 0), 2),
            "points": int(udata.get("reward_points", 0)),
            "tier": get_tier(udata.get("reward_points", 0))
        })

    return render_template("dashboard.html", 
        username=username,
        total_energy_wh=round(user["total_energy_wh"], 4),
        todays_energy_wh=round(todays_energy,4),
        todays_reward_points=todays_reward_points,
        reward_points=int(user["reward_points"]),
        pressure_given=user.get("pressure_given", 0),
        ampere=user.get("ampere", 0),
        voltage=user.get("voltage", 0),
        total_steps=user.get("total_steps", 0),
        monthly_energy_wh=round(user.get("monthly_energy_wh", 0),4),
        monthly_voltage=round(user.get("monthly_voltage", 0),2),
        monthly_ampere=round(user.get("monthly_ampere", 0),2),
        monthly_pressure=round(user.get("monthly_pressure", 0),2),
        tier=tier,
        recent_records=user_records,
        tiles=tiles_list,
        user_location={"lat": user_lat, "lon": user_lon} if user_lat is not None else None,
        active_users_count=active_users_count,
        active_tiles_count=active_tiles_count,
        leaderboard=leaderboard
    )


@app.route("/leaderboard")
def leaderboard():
    """Global leaderboard of top energy contributors"""
    user_data = load_user_data()
    
    sorted_users = sorted(user_data.items(), 
        key=lambda x: x[1]["reward_points"], reverse=True)
    
    leaderboard_data = []
    for rank, (username, data) in enumerate(sorted_users, 1):
        leaderboard_data.append({
            "rank": rank,
            "username": username,
            "energy_wh": round(data["total_energy_wh"], 2),
            "points": int(data["reward_points"]),
            "pressure_given": data.get("pressure_given", 0),
            "ampere": data.get("ampere", 0),
            "voltage": data.get("voltage", 0),
            "tier": get_tier(data["reward_points"])
        })
    
    return render_template("leaderboard.html", leaderboard=leaderboard_data)


@app.route("/energy-tiles")
def energy_tiles():
    """View all available energy tile locations"""
    tiles_list = []
    for tile_id, info in load_energy_tiles().items():
        tiles_list.append({
            "id": tile_id,
            "name": info["name"],
            "lat": info["lat"],
            "lon": info["lon"],
            "capacity": info["capacity"]
        })
    return render_template("energy_tiles.html", tiles=tiles_list)



@app.route("/add-tile", methods=["GET", "POST"])
@admin_login_required
def add_tile():
    """Admin route to add a new energy tile"""
    if request.method == "POST":
        tile_name = request.form.get("tile_name")
        latitude = float(request.form.get("latitude"))
        longitude = float(request.form.get("longitude"))
        radius = float(request.form.get("radius", 0.001))
        capacity = int(request.form.get("capacity", 1000))
        
        if not tile_name or len(tile_name.strip()) == 0:
            return jsonify({"status": "error", "message": "Tile name required"}), 400
        
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return jsonify({"status": "error", "message": "Invalid GPS coordinates"}), 400
        
        if capacity <= 0:
            return jsonify({"status": "error", "message": "Capacity must be greater than 0"}), 400
        
        energy_tiles = load_energy_tiles()
        
        # Check for duplicate locations (within 0.0001 degrees)
        for tile_id, tile in energy_tiles.items():
            if abs(tile['lat'] - latitude) < 0.0001 and abs(tile['lon'] - longitude) < 0.0001:
                return jsonify({"status": "error", "message": "A tile already exists at this location. The new tile was not added."}), 400
        
        # Generate new tile ID based on existing count
        tile_num = len(energy_tiles) + 1
        tile_id = f"tile_{str(tile_num).zfill(3)}"
        
        # Ensure ID doesn't already exist
        while tile_id in energy_tiles:
            tile_num += 1
            tile_id = f"tile_{str(tile_num).zfill(3)}"
        
        energy_tiles[tile_id] = {
            "name": tile_name,
            "lat": latitude,
            "lon": longitude,
            "radius": radius,
            "capacity": capacity,
            "usage_count": 0
        }
        save_energy_tiles(energy_tiles)
        
        return jsonify({"status": "success", "message": "Tile added successfully"})
    
    return render_template("add_tile.html")


@app.route("/remove-tile/<tile_id>", methods=["POST"])
@admin_login_required
def remove_tile(tile_id):
    """Admin route to remove an energy tile"""
    energy_tiles = load_energy_tiles()
    
    if tile_id not in energy_tiles:
        return jsonify({"status": "error", "message": "Tile not found"}), 404
    
    tile_name = energy_tiles[tile_id]["name"]
    del energy_tiles[tile_id]
    save_energy_tiles(energy_tiles)
    
    return jsonify({"status": "success", "message": "Tile removed"})


@app.route("/api/tile-usage/<tile_id>", methods=["POST"])
def increment_tile_usage(tile_id):
    """API endpoint to increment tile usage count"""
    energy_tiles = load_energy_tiles()
    
    if tile_id not in energy_tiles:
        return jsonify({"status": "error", "message": "Tile not found"}), 404
    
    energy_tiles[tile_id]["usage_count"] = energy_tiles[tile_id].get("usage_count", 0) + 1
    save_energy_tiles(energy_tiles)
    
    return jsonify({"status": "success", "message": "Usage count updated", "usage_count": energy_tiles[tile_id]["usage_count"]})


@app.route("/api/user-info")
def get_user_info():
    """API endpoint to get current logged-in user info"""
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({
        "username": session.get('username'),
        "user_type": session.get('user_type')
    })


@app.route("/api/get-tiles")
def get_tiles():
    """API endpoint to get all energy tiles as JSON"""
    energy_tiles = load_energy_tiles()
    
    tiles_list = []
    for tile_id, tile in energy_tiles.items():
        tiles_list.append({
            "id": tile_id,
            "name": tile["name"],
            "lat": tile["lat"],
            "lon": tile["lon"],
            "radius": tile["radius"],
            "capacity": tile["capacity"]
        })
    
    return jsonify(tiles_list)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
