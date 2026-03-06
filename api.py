import os, sqlite3, io, csv, random, string
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.ensemble import RandomForestRegressor
import json
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "foodchain_ai.db")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change_this_secret_key_in_production")

# Get allowed origins from environment or use defaults
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://food-chain-ai.vercel.app",
    os.getenv("FRONTEND_URL", "http://localhost:3000")
]

# Configure CORS with explicit settings for credentials
CORS(app, 
     supports_credentials=True,
     origins=allowed_origins,
     allow_headers=["Content-Type", "Authorization", "Accept"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Type"])

# Configure session cookie settings for cross-origin requests
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True  # True for HTTPS in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_PATH'] = '/'

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    # Create database connection directly (not using get_db() which requires app context)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        schema_path = os.path.join(BASE_DIR, 'schema.sql')
        if os.path.exists(schema_path):
            db.executescript(open(schema_path).read())
        # Seed admin and ngo
        cur = db.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin'")
        if cur.fetchone()["c"] == 0:
            db.execute("INSERT INTO users (username,password_hash,role,created_at) VALUES (?,?,?,?)",
                       ("admin", generate_password_hash("admin123"), "admin", datetime.now().isoformat()))
        cur = db.execute("SELECT COUNT(*) AS c FROM ngos")
        if cur.fetchone()["c"] == 0:
            db.execute("INSERT INTO ngos (name,contact,email) VALUES (?,?,?)",
                       ("Sample NGO", "9876543210", "ngo@example.com"))
        
        # Seed festivals/seasons
        cur = db.execute("SELECT COUNT(*) AS c FROM festivals_seasons")
        if cur.fetchone()["c"] == 0:
            festivals = [
                ("Diwali", "2024-11-01", "2024-11-05", 1.5, "Major festival - high demand"),
                ("Christmas", "2024-12-20", "2024-12-26", 1.4, "Holiday season"),
                ("New Year", "2024-12-30", "2025-01-02", 1.3, "Celebration period"),
                ("Summer Season", "2024-04-01", "2024-06-30", 1.2, "Hot season - cold drinks demand"),
                ("Winter Season", "2024-11-01", "2024-02-28", 1.15, "Hot food demand")
            ]
            for name, start, end, mult, desc in festivals:
                db.execute("INSERT INTO festivals_seasons (name, start_date, end_date, multiplier, description) VALUES (?,?,?,?,?)",
                          (name, start, end, mult, desc))
        
        # Seed demo restaurant + data
        cur = db.execute("SELECT id FROM users WHERE username = ?", ("demo_rest",)).fetchone()
        if cur is None:
            db.execute("INSERT INTO users (username,password_hash,role,restaurant_name,location,email,created_at) VALUES (?,?,?,?,?,?,?)",
                       ("demo_rest", generate_password_hash("demo123"), "manager", "Green Bite Restaurant", "City Center", "demo@example.com", datetime.now().isoformat()))
            demo_id = db.execute("SELECT id FROM users WHERE username=?", ("demo_rest",)).fetchone()["id"]
        else:
            demo_id = cur["id"]
        cur = db.execute("SELECT COUNT(*) AS c FROM daily_records WHERE user_id=?", (demo_id,))
        if cur.fetchone()["c"] == 0:
            items = [("Veg Burger","Fast Food",80,1), ("Margherita Pizza","Fast Food",150,1), ("Pasta Alfredo","Italian",200,1),
                     ("Fried Rice","Main Course",120,1), ("Gulab Jamun","Dessert",40,2)]
            item_ids = {}
            for name,cat,price,shelf in items:
                db.execute("INSERT INTO menu_items (user_id,name,category,price,shelf_life_days) VALUES (?,?,?,?,?)",
                           (demo_id,name,cat,price,shelf))
                item_ids[name] = db.execute("SELECT id FROM menu_items WHERE user_id=? AND name=? ORDER BY id DESC LIMIT 1",(demo_id,name)).fetchone()["id"]
            today = datetime.now().date()
            for d in range(1,31):
                date_str = (today - timedelta(days=d)).isoformat()
                for name,idv in item_ids.items():
                    if name=="Veg Burger":
                        prepared = 40 + (d%5); sold = max(prepared - (5 + d%3), 0)
                    elif name=="Margherita Pizza":
                        prepared = 30 + (d%4); sold = max(prepared - (4 + d%2), 0)
                    elif name=="Pasta Alfredo":
                        prepared = 20 + (d%3); sold = max(prepared - (3 + d%2), 0)
                    elif name=="Fried Rice":
                        prepared = 35 + (d%4); sold = max(prepared - (6 + d%3), 0)
                    else:
                        prepared = 50 + (d%6); sold = max(prepared - (8 + d%4), 0)
                    wasted = max(prepared - sold, 0)
                    reason = "Over-prepared" if wasted>0 else ""
                    db.execute("INSERT INTO daily_records (user_id,menu_item_id,date,prepared_qty,sold_qty,wasted_qty,reason) VALUES (?,?,?,?,?,?,?)",
                               (demo_id,idv,date_str,prepared,sold,wasted,reason))
                    # Add sample inventory purchases
                    # Get the price from the items list
                    item_price = next((p for n, c, p, s in items if n == name), 80)
                    purchase_qty = prepared * 1.2  # Assume they purchase 20% more than prepared
                    db.execute("INSERT INTO inventory_purchases (user_id,menu_item_id,purchase_date,quantity,unit_price,created_at) VALUES (?,?,?,?,?,?)",
                              (demo_id, idv, date_str, purchase_qty, item_price*0.6, datetime.now().isoformat()))
        db.commit()
    finally:
        db.close()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Using session-based auth
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    # In production, use actual email service (SendGrid, AWS SES, etc.)
    print(f"OTP for {email}: {otp}")
    return True

def send_otp_sms(phone, otp):
    # In production, use actual SMS service (Twilio, AWS SNS, etc.)
    print(f"OTP for {phone}: {otp}")
    return True

def get_season_multiplier(target_date):
    """Get demand multiplier based on festivals/seasons"""
    db = get_db()
    date_str = target_date.isoformat()
    festivals = db.execute("""
        SELECT multiplier FROM festivals_seasons 
        WHERE start_date <= ? AND end_date >= ?
        ORDER BY multiplier DESC LIMIT 1
    """, (date_str, date_str)).fetchone()
    return festivals['multiplier'] if festivals else 1.0

def get_prediction_for_item(user_id, menu_item_id, target_date=None):
    """Enhanced prediction based on inventory purchases, seasons, and festivals"""
    db = get_db()
    if target_date is None:
        target_date = datetime.now().date() + timedelta(days=1)
    
    # Get inventory purchase history (not sold products)
    rows = db.execute("""
        SELECT purchase_date, quantity 
        FROM inventory_purchases 
        WHERE user_id=? AND menu_item_id=? 
        ORDER BY purchase_date ASC
    """, (user_id, menu_item_id)).fetchall()
    
    if not rows or len(rows) < 7:
        rows_avg = db.execute("""
            SELECT quantity FROM inventory_purchases 
            WHERE user_id=? AND menu_item_id=? 
            ORDER BY purchase_date DESC LIMIT 7
        """, (user_id, menu_item_id)).fetchall()
        if not rows_avg: 
            # Fallback to daily_records if no inventory data
            rows_avg = db.execute("""
                SELECT prepared_qty as quantity FROM daily_records 
                WHERE user_id=? AND menu_item_id=? 
                ORDER BY date DESC LIMIT 7
            """, (user_id, menu_item_id)).fetchall()
            if not rows_avg: return None
        avg_qty = sum(r["quantity"] for r in rows_avg) / len(rows_avg)
        season_mult = get_season_multiplier(target_date)
        predicted = round(avg_qty * season_mult, 2)
        return {
            "predicted_demand": predicted,
            "suggested_purchase": round(predicted * 1.1, 2),
            "model": "average_with_season",
            "season_multiplier": season_mult
        }
    
    X = []
    y = []
    for r in rows:
        d = datetime.fromisoformat(r["purchase_date"]).date()
        dow = d.weekday()
        is_weekend = 1 if dow >= 5 else 0
        month = d.month
        # Get season multiplier for historical date
        hist_mult = get_season_multiplier(d)
        X.append([dow, is_weekend, month, hist_mult])
        y.append(r["quantity"])
    
    try:
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        target_dow = target_date.weekday()
        target_weekend = 1 if target_dow >= 5 else 0
        target_month = target_date.month
        target_mult = get_season_multiplier(target_date)
        pred = rf.predict([[target_dow, target_weekend, target_month, target_mult]])[0]
        predicted = round(max(pred, 0), 2)
        return {
            "predicted_demand": predicted,
            "suggested_purchase": round(predicted * 1.1, 2),
            "model": "random_forest_with_season",
            "season_multiplier": target_mult
        }
    except Exception as e:
        avg_qty = sum(y) / len(y)
        season_mult = get_season_multiplier(target_date)
        predicted = round(avg_qty * season_mult, 2)
        return {
            "predicted_demand": predicted,
            "suggested_purchase": round(predicted * 1.1, 2),
            "model": "average_with_season",
            "season_multiplier": season_mult
        }

# API Routes
@app.route('/api/init', methods=['GET'])
def api_init():
    init_db()
    return jsonify({'message': 'Database initialized'})

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def api_health():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def api_login():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Use force=True to parse JSON even if Content-Type is not set correctly
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'error': 'Invalid request data. Please send JSON data.'}), 400
        
        username = data.get('username', '').strip() if data else ''
        password = data.get('password', '').strip() if data else ''
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        try:
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            
            if not user:
                return jsonify({'error': 'Invalid username or password'}), 401
            
            if not check_password_hash(user['password_hash'], password):
                return jsonify({'error': 'Invalid username or password'}), 401
            
            # Generate and send OTP
            otp = generate_otp()
            expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
            
            # Store OTP
            db.execute("""
                INSERT INTO otp_verifications (user_id, email, otp_code, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user['id'], user.get('email', ''), otp, datetime.now().isoformat(), expires_at))
            db.commit()
            
            # Send OTP (in production, use real service)
            if user.get('email'):
                send_otp_email(user['email'], otp)
            else:
                print(f"Warning: User {username} has no email. OTP: {otp}")
            
            return jsonify({
                'message': 'OTP sent to your email',
                'user_id': user['id'],
                'requires_otp': True
            })
        except sqlite3.Error as db_err:
            print(f"Database error during login: {db_err}")
            return jsonify({'error': 'Database error. Please try again.'}), 500
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}. Please try again.'}), 500

@app.route('/api/verify-otp', methods=['POST', 'OPTIONS'])
def api_verify_otp():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Use force=True to parse JSON even if Content-Type is not set correctly
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'error': 'Invalid request data. Please send JSON data.'}), 400
        
        user_id = data.get('user_id') if data else None
        otp = data.get('otp', '').strip() if data else ''
        
        if not user_id or not otp:
            return jsonify({'error': 'User ID and OTP are required'}), 400
        
        try:
            db = get_db()
            otp_record = db.execute("""
                SELECT * FROM otp_verifications 
                WHERE user_id=? AND otp_code=? AND is_used=0 
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, otp)).fetchone()
            
            if not otp_record:
                return jsonify({'error': 'Invalid OTP'}), 401
            
            expires_at = datetime.fromisoformat(otp_record['expires_at'])
            if datetime.now() > expires_at:
                return jsonify({'error': 'OTP has expired'}), 401
            
            # Mark OTP as used
            db.execute("UPDATE otp_verifications SET is_used=1 WHERE id=?", (otp_record['id'],))
            
            # Get user and create session
            user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            db.commit()
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'restaurant_name': user.get('restaurant_name'),
                    'location': user.get('location')
                }
            })
        except sqlite3.Error as db_err:
            print(f"Database error during OTP verification: {db_err}")
            return jsonify({'error': 'Database error. Please try again.'}), 500
    except Exception as e:
        print(f"OTP verification error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}. Please try again.'}), 500

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def api_register():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Use force=True to parse JSON even if Content-Type is not set correctly
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'error': 'Invalid request data. Please send JSON data.'}), 400
        
        username = data.get('username', '').strip() if data else ''
        password = data.get('password', '').strip() if data else ''
        restaurant_name = data.get('restaurant_name', '').strip() if data else ''
        location = data.get('location', '').strip() if data else ''
        email = data.get('email', '').strip() if data else ''
        phone = data.get('phone', '').strip() if data else ''
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        try:
            db = get_db()
            db.execute("""
                INSERT INTO users (username,password_hash,role,restaurant_name,location,email,phone,created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (username, generate_password_hash(password), 'manager', restaurant_name, location, email, phone, datetime.now().isoformat()))
            db.commit()
            return jsonify({'message': 'Registration successful. Please log in.'})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username already taken'}), 400
        except sqlite3.Error as db_err:
            print(f"Registration database error: {db_err}")
            return jsonify({'error': 'Database error. Please try again.'}), 500
        except Exception as e:
            print(f"Registration database error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Registration failed. Please try again.'}), 500
    except Exception as e:
        print(f"Registration API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}. Please try again.'}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/dashboard', methods=['GET'])
@token_required
def api_dashboard():
    db = get_db()
    user_id = session['user_id']
    today = datetime.now().date().isoformat()
    week_ago = (datetime.now().date() - timedelta(days=7)).isoformat()
    
    rows = db.execute("""
        SELECT SUM(prepared_qty) AS prepared, SUM(sold_qty) AS sold, SUM(wasted_qty) AS wasted
        FROM daily_records
        WHERE user_id=? AND date BETWEEN ? AND ?
    """, (user_id, week_ago, today)).fetchone()
    
    stats = {
        'prepared': rows['prepared'] or 0,
        'sold': rows['sold'] or 0,
        'wasted': rows['wasted'] or 0
    }
    
    trend_rows = db.execute("""
        SELECT date, SUM(prepared_qty) AS prepared, SUM(sold_qty) AS sold, SUM(wasted_qty) AS wasted
        FROM daily_records
        WHERE user_id=? AND date BETWEEN ? AND ?
        GROUP BY date ORDER BY date ASC
    """, (user_id, week_ago, today)).fetchall()
    
    trend_data = [{
        'date': r['date'],
        'prepared': r['prepared'] or 0,
        'sold': r['sold'] or 0,
        'wasted': r['wasted'] or 0
    } for r in trend_rows]
    
    top_waste = db.execute("""
        SELECT m.name, SUM(d.wasted_qty) AS wasted
        FROM daily_records d
        JOIN menu_items m ON d.menu_item_id=m.id
        WHERE d.user_id=?
        GROUP BY m.name ORDER BY wasted DESC LIMIT 10
    """, (user_id,)).fetchall()
    
    top_waste_data = [{'name': r['name'], 'wasted': r['wasted'] or 0} for r in top_waste]
    
    return jsonify({
        'stats': stats,
        'trend_data': trend_data,
        'top_waste': top_waste_data
    })

@app.route('/api/menu', methods=['GET'])
@token_required
def api_menu_get():
    db = get_db()
    user_id = session['user_id']
    items = db.execute("SELECT * FROM menu_items WHERE user_id=? AND is_active=1 ORDER BY name", (user_id,)).fetchall()
    return jsonify({'items': [dict(item) for item in items]})

@app.route('/api/menu', methods=['POST'])
@token_required
def api_menu_post():
    data = request.get_json()
    db = get_db()
    user_id = session['user_id']
    
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    price = float(data.get('price', 0))
    shelf_life_days = int(data.get('shelf_life_days', 0))
    
    if not name:
        return jsonify({'error': 'Item name is required'}), 400
    
    db.execute("""
        INSERT INTO menu_items (user_id,name,category,price,shelf_life_days)
        VALUES (?,?,?,?,?)
    """, (user_id, name, category, price, shelf_life_days))
    db.commit()
    
    return jsonify({'message': 'Menu item added'})

@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
@token_required
def api_menu_delete(item_id):
    db = get_db()
    user_id = session['user_id']
    db.execute("UPDATE menu_items SET is_active=0 WHERE id=? AND user_id=?", (item_id, user_id))
    db.commit()
    return jsonify({'message': 'Item deactivated'})

@app.route('/api/entry', methods=['GET'])
@token_required
def api_entry_get():
    db = get_db()
    user_id = session['user_id']
    items = db.execute("SELECT * FROM menu_items WHERE user_id=? AND is_active=1 ORDER BY name", (user_id,)).fetchall()
    
    predictions = {}
    for item in items:
        p = get_prediction_for_item(user_id, item['id'])
        if p:
            predictions[item['id']] = p
    
    records = db.execute("""
        SELECT d.id,d.date,m.name,d.prepared_qty,d.sold_qty,d.wasted_qty
        FROM daily_records d
        JOIN menu_items m ON d.menu_item_id=m.id
        WHERE d.user_id=?
        ORDER BY d.date DESC,d.id DESC LIMIT 10
    """, (user_id,)).fetchall()
    
    today = datetime.now().date().isoformat()
    week_ago = (datetime.now().date() - timedelta(days=7)).isoformat()
    entry_summary = db.execute("""
        SELECT date,SUM(prepared_qty) AS prepared,SUM(sold_qty) AS sold,SUM(wasted_qty) AS wasted
        FROM daily_records
        WHERE user_id=? AND date BETWEEN ? AND ?
        GROUP BY date ORDER BY date ASC
    """, (user_id, week_ago, today)).fetchall()
    
    return jsonify({
        'items': [dict(item) for item in items],
        'predictions': predictions,
        'records': [dict(r) for r in records],
        'entry_summary': [dict(r) for r in entry_summary]
    })

@app.route('/api/entry', methods=['POST'])
@token_required
def api_entry_post():
    data = request.get_json()
    db = get_db()
    user_id = session['user_id']
    
    date_str = data.get('date') or datetime.now().date().isoformat()
    menu_item_id = int(data.get('menu_item_id'))
    prepared_qty = float(data.get('prepared_qty', 0))
    sold_qty = float(data.get('sold_qty', 0))
    wasted_qty = float(data.get('wasted_qty', 0))
    reason = data.get('reason', '').strip()
    
    db.execute("""
        INSERT INTO daily_records (user_id,menu_item_id,date,prepared_qty,sold_qty,wasted_qty,reason)
        VALUES (?,?,?,?,?,?,?)
    """, (user_id, menu_item_id, date_str, prepared_qty, sold_qty, wasted_qty, reason))
    db.commit()
    
    return jsonify({'message': 'Record saved'})

@app.route('/api/billing/create', methods=['POST'])
@token_required
def api_billing_create():
    """Create a bill and automatically update daily_records"""
    data = request.get_json()
    db = get_db()
    user_id = session['user_id']
    
    bill_date = data.get('bill_date') or datetime.now().date().isoformat()
    items = data.get('items', [])  # Array of {menu_item_id, quantity, unit_price}
    
    total_amount = 0
    for item in items:
        menu_item_id = int(item['menu_item_id'])
        quantity = float(item['quantity'])
        unit_price = float(item.get('unit_price', 0))
        total_item_amount = quantity * unit_price
        total_amount += total_item_amount
        
        # Insert billing record
        db.execute("""
            INSERT INTO billing_records (user_id,menu_item_id,bill_date,quantity,unit_price,total_amount,created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (user_id, menu_item_id, bill_date, quantity, unit_price, total_item_amount, datetime.now().isoformat()))
        
        # Auto-update daily_records (sold_qty)
        # Check if record exists for today
        existing = db.execute("""
            SELECT id, sold_qty FROM daily_records
            WHERE user_id=? AND menu_item_id=? AND date=?
        """, (user_id, menu_item_id, bill_date)).fetchone()
        
        if existing:
            new_sold_qty = existing['sold_qty'] + quantity
            db.execute("""
                UPDATE daily_records
                SET sold_qty=?
                WHERE id=?
            """, (new_sold_qty, existing['id']))
        else:
            # Create new record with sold_qty only
            db.execute("""
                INSERT INTO daily_records (user_id,menu_item_id,date,prepared_qty,sold_qty,wasted_qty,reason)
                VALUES (?,?,?,?,?,?,?)
            """, (user_id, menu_item_id, bill_date, 0, quantity, 0, 'Auto-generated from billing'))
    
    db.commit()
    
    return jsonify({
        'message': 'Bill created and data entry updated',
        'total_amount': total_amount
    })

@app.route('/api/inventory/purchases', methods=['GET'])
@token_required
def api_inventory_purchases_get():
    db = get_db()
    user_id = session['user_id']
    purchases = db.execute("""
        SELECT ip.*, m.name as menu_item_name
        FROM inventory_purchases ip
        JOIN menu_items m ON ip.menu_item_id = m.id
        WHERE ip.user_id=?
        ORDER BY ip.purchase_date DESC
        LIMIT 50
    """, (user_id,)).fetchall()
    
    return jsonify({'purchases': [dict(p) for p in purchases]})

@app.route('/api/inventory/purchases', methods=['POST'])
@token_required
def api_inventory_purchases_post():
    data = request.get_json()
    db = get_db()
    user_id = session['user_id']
    
    menu_item_id = int(data.get('menu_item_id'))
    purchase_date = data.get('purchase_date') or datetime.now().date().isoformat()
    quantity = float(data.get('quantity', 0))
    unit_price = float(data.get('unit_price', 0))
    supplier = data.get('supplier', '').strip()
    notes = data.get('notes', '').strip()
    
    db.execute("""
        INSERT INTO inventory_purchases (user_id,menu_item_id,purchase_date,quantity,unit_price,supplier,notes,created_at)
        VALUES (?,?,?,?,?,?,?,?)
    """, (user_id, menu_item_id, purchase_date, quantity, unit_price, supplier, notes, datetime.now().isoformat()))
    db.commit()
    
    return jsonify({'message': 'Inventory purchase recorded'})

@app.route('/api/predictions/<int:menu_item_id>', methods=['GET'])
@token_required
def api_predictions(menu_item_id):
    user_id = session['user_id']
    target_date_str = request.args.get('target_date')
    target_date = datetime.fromisoformat(target_date_str).date() if target_date_str else None
    
    prediction = get_prediction_for_item(user_id, menu_item_id, target_date)
    if not prediction:
        return jsonify({'error': 'Insufficient data for prediction'}), 400
    
    return jsonify(prediction)

@app.route('/api/analytics', methods=['GET'])
@token_required
def api_analytics():
    db = get_db()
    user_id = session['user_id']
    thirty_days_ago = (datetime.now().date() - timedelta(days=30)).isoformat()
    today = datetime.now().date().isoformat()
    
    daily = db.execute("""
        SELECT date,SUM(prepared_qty) AS prepared,SUM(sold_qty) AS sold,SUM(wasted_qty) AS wasted
        FROM daily_records
        WHERE user_id=? AND date BETWEEN ? AND ?
        GROUP BY date ORDER BY date ASC
    """, (user_id, thirty_days_ago, today)).fetchall()
    
    top_waste = db.execute("""
        SELECT m.name, SUM(d.wasted_qty) AS wasted
        FROM daily_records d
        JOIN menu_items m ON d.menu_item_id=m.id
        WHERE d.user_id=?
        GROUP BY m.name ORDER BY wasted DESC LIMIT 10
    """, (user_id,)).fetchall()
    
    return jsonify({
        'daily': [dict(d) for d in daily],
        'top_waste': [dict(t) for t in top_waste]
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

