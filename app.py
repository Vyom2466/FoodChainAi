import os, sqlite3, io, csv
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, Response
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.ensemble import RandomForestRegressor

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "foodchain_ai.db")

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

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
    db = get_db()
    db.executescript(open(os.path.join(BASE_DIR,'schema.sql')).read())
    # seed admin and ngo
    cur = db.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin'")
    if cur.fetchone()["c"] == 0:
        db.execute("INSERT INTO users (username,password_hash,role,created_at) VALUES (?,?,?,?)",
                   ("admin", generate_password_hash("admin123"), "admin", datetime.now().isoformat()))
    cur = db.execute("SELECT COUNT(*) AS c FROM ngos")
    if cur.fetchone()["c"] == 0:
        db.execute("INSERT INTO ngos (name,contact,email) VALUES (?,?,?)",
                   ("Sample NGO", "9876543210", "ngo@example.com"))
    # seed demo restaurant + data
    cur = db.execute("SELECT id FROM users WHERE username = ?", ("demo_rest",)).fetchone()
    if cur is None:
        db.execute("INSERT INTO users (username,password_hash,role,restaurant_name,location,created_at) VALUES (?,?,?,?,?,?)",
                   ("demo_rest", generate_password_hash("demo123"), "manager", "Green Bite Restaurant", "City Center", datetime.now().isoformat()))
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
        # sample donation records
        ngo = db.execute("SELECT id FROM ngos LIMIT 1").fetchone()
        if ngo:
            for i in range(3):
                db.execute("INSERT INTO donations (user_id,menu_item_id,ngo_id,qty,created_at) VALUES (?,?,?,?,?)",
                           (demo_id, list(item_ids.values())[0], ngo["id"], 5+i*2, datetime.now().isoformat(timespec='seconds')))
    db.commit()

def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role")!=role:
                flash("Unauthorized access.", "danger")
                return redirect(url_for("dashboard"))
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_prediction_for_item(user_id, menu_item_id):
    db = get_db()
    rows = db.execute("SELECT date,sold_qty FROM daily_records WHERE user_id=? AND menu_item_id=? ORDER BY date ASC",(user_id,menu_item_id)).fetchall()
    if not rows or len(rows)<7:
        rows_avg = db.execute("SELECT sold_qty FROM daily_records WHERE user_id=? AND menu_item_id=? ORDER BY date DESC LIMIT 7",(user_id,menu_item_id)).fetchall()
        if not rows_avg: return None
        avg_sold = sum(r["sold_qty"] for r in rows_avg)/len(rows_avg)
        return {"predicted_demand": round(avg_sold,2), "suggested_prepare": round(avg_sold*1.1,2), "model":"average"}
    X=[]; y=[]
    for r in rows:
        d = datetime.fromisoformat(r["date"]).date(); dow = d.weekday(); is_weekend = 1 if dow>=5 else 0
        X.append([dow,is_weekend]); y.append(r["sold_qty"])
    try:
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X,y)
        target = datetime.now().date()+timedelta(days=1); dow=target.weekday(); is_weekend=1 if dow>=5 else 0
        pred = rf.predict([[dow,is_weekend]])[0]; predicted = round(max(pred,0),2)
        return {"predicted_demand": predicted, "suggested_prepare": round(predicted*1.1,2), "model":"random_forest"}
    except Exception:
        avg_sold = sum(y)/len(y)
        return {"predicted_demand": round(avg_sold,2), "suggested_prepare": round(avg_sold*1.1,2), "model":"average"}

@app.route('/', methods=['GET','POST'])
def login():
    init_db()
    if request.method=='POST':
        username = request.form.get('username','').strip(); password = request.form.get('password','').strip()
        db = get_db(); user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not user or not check_password_hash(user['password_hash'], password):
            flash("Invalid username or password.", "danger"); return redirect(url_for('login'))
        session['user_id']=user['id']; session['username']=user['username']; session['role']=user['role']
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    init_db()
    if request.method=='POST':
        username = request.form.get('username','').strip(); password = request.form.get('password','').strip()
        restaurant_name = request.form.get('restaurant_name','').strip(); location = request.form.get('location','').strip()
        if not username or not password:
            flash("Username and password are required.", "danger"); return redirect(url_for('register'))
        db=get_db()
        try:
            db.execute("INSERT INTO users (username,password_hash,role,restaurant_name,location,created_at) VALUES (?,?,?,?,?,?)",
                       (username, generate_password_hash(password), 'manager', restaurant_name, location, datetime.now().isoformat()))
            db.commit()
        except sqlite3.IntegrityError:
            flash("Username already taken.", "danger"); return redirect(url_for('register'))
        flash("Registration successful. Please log in.", "success"); return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/dashboard')
@login_required()
def dashboard():
    db=get_db(); user_id=session['user_id']
    today = datetime.now().date().isoformat(); week_ago = (datetime.now().date()-timedelta(days=7)).isoformat()
    rows = db.execute("SELECT SUM(prepared_qty) AS prepared, SUM(sold_qty) AS sold, SUM(wasted_qty) AS wasted FROM daily_records WHERE user_id=? AND date BETWEEN ? AND ?", (user_id, week_ago, today)).fetchone()
    stats = {'prepared': rows['prepared'] or 0, 'sold': rows['sold'] or 0, 'wasted': rows['wasted'] or 0}
    trend_rows = db.execute("SELECT date, SUM(prepared_qty) AS prepared, SUM(sold_qty) AS sold, SUM(wasted_qty) AS wasted FROM daily_records WHERE user_id=? AND date BETWEEN ? AND ? GROUP BY date ORDER BY date ASC", (user_id, week_ago, today)).fetchall()
    trend_labels=[r['date'] for r in trend_rows]; trend_prepared=[r['prepared'] or 0 for r in trend_rows]; trend_sold=[r['sold'] or 0 for r in trend_rows]; trend_wasted=[r['wasted'] or 0 for r in trend_rows]
    top_waste = db.execute("SELECT m.name, SUM(d.wasted_qty) AS wasted FROM daily_records d JOIN menu_items m ON d.menu_item_id=m.id WHERE d.user_id=? GROUP BY m.name ORDER BY wasted DESC LIMIT 10", (user_id,)).fetchall()
    top_waste_labels=[r['name'] for r in top_waste]; top_waste_values=[r['wasted'] or 0 for r in top_waste]
    return render_template('dashboard.html', stats=stats, trend_labels=trend_labels, trend_prepared=trend_prepared, trend_sold=trend_sold, trend_wasted=trend_wasted, top_waste=top_waste, top_waste_labels=top_waste_labels, top_waste_values=top_waste_values)

@app.route('/menu', methods=['GET','POST'])
@login_required()
def menu():
    db=get_db(); user_id=session['user_id']
    if request.method=='POST':
        name=request.form.get('name','').strip(); category=request.form.get('category','').strip(); price=request.form.get('price') or 0; shelf=request.form.get('shelf_life_days') or 0
        if not name: flash("Item name is required.", "danger"); return redirect(url_for('menu'))
        db.execute("INSERT INTO menu_items (user_id,name,category,price,shelf_life_days) VALUES (?,?,?,?,?)", (user_id,name,category,float(price),int(shelf)))
        db.commit(); flash("Menu item added.", "success"); return redirect(url_for('menu'))
    items = db.execute("SELECT * FROM menu_items WHERE user_id=? AND is_active=1 ORDER BY name", (user_id,)).fetchall()
    return render_template('menu.html', items=items)

@app.route('/menu/deactivate/<int:item_id>')
@login_required()
def deactivate_menu_item(item_id):
    db=get_db(); user_id=session['user_id']; db.execute("UPDATE menu_items SET is_active=0 WHERE id=? AND user_id=?", (item_id, user_id)); db.commit(); flash("Item deactivated.", "info"); return redirect(url_for('menu'))

@app.route('/entry', methods=['GET','POST'])
@login_required()
def entry():
    db=get_db(); user_id=session['user_id']
    items=db.execute("SELECT * FROM menu_items WHERE user_id=? AND is_active=1 ORDER BY name", (user_id,)).fetchall()
    if request.method=='POST':
        date_str=request.form.get('date') or datetime.now().date().isoformat(); menu_item_id=int(request.form.get('menu_item_id')); prepared_qty=float(request.form.get('prepared_qty') or 0); sold_qty=float(request.form.get('sold_qty') or 0); wasted_qty=float(request.form.get('wasted_qty') or 0); reason=request.form.get('reason','').strip()
        db.execute("INSERT INTO daily_records (user_id,menu_item_id,date,prepared_qty,sold_qty,wasted_qty,reason) VALUES (?,?,?,?,?,?,?)", (user_id, menu_item_id, date_str, prepared_qty, sold_qty, wasted_qty, reason)); db.commit(); flash("Record saved.", "success"); return redirect(url_for('entry'))
    records=db.execute("SELECT d.id,d.date,m.name,d.prepared_qty,d.sold_qty,d.wasted_qty FROM daily_records d JOIN menu_items m ON d.menu_item_id=m.id WHERE d.user_id=? ORDER BY d.date DESC,d.id DESC LIMIT 10", (user_id,)).fetchall()
    predictions={}
    for item in items:
        p=get_prediction_for_item(user_id, item['id'])
        if p: predictions[item['id']]=p
    today = datetime.now().date().isoformat(); week_ago = (datetime.now().date()-timedelta(days=7)).isoformat()
    entry_summary = db.execute("SELECT date,SUM(prepared_qty) AS prepared,SUM(sold_qty) AS sold,SUM(wasted_qty) AS wasted FROM daily_records WHERE user_id=? AND date BETWEEN ? AND ? GROUP BY date ORDER BY date ASC",(user_id,week_ago,today)).fetchall()
    entry_labels=[r['date'] for r in entry_summary]; entry_prepared=[r['prepared'] or 0 for r in entry_summary]; entry_sold=[r['sold'] or 0 for r in entry_summary]; entry_wasted=[r['wasted'] or 0 for r in entry_summary]
    return render_template('entry.html', items=items, records=records, predictions=predictions, entry_labels=entry_labels, entry_prepared=entry_prepared, entry_sold=entry_sold, entry_wasted=entry_wasted)

@app.route('/donation', methods=['GET','POST'])
@login_required()
def donation():
    db=get_db(); user_id=session['user_id']
    items=db.execute("SELECT m.id,m.name FROM menu_items m WHERE m.user_id=? AND m.is_active=1 ORDER BY m.name",(user_id,)).fetchall()
    ngos=db.execute("SELECT * FROM ngos ORDER BY name").fetchall()
    if request.method=='POST':
        menu_item_id=int(request.form.get('menu_item_id')); ngo_id=int(request.form.get('ngo_id')); qty=float(request.form.get('qty') or 0)
        db.execute("INSERT INTO donations (user_id,menu_item_id,ngo_id,qty,created_at) VALUES (?,?,?,?,?)", (user_id, menu_item_id, ngo_id, qty, datetime.now().isoformat(timespec='seconds'))); db.commit(); flash("Donation recorded.", "success"); return redirect(url_for('donation'))
    donations=db.execute("SELECT d.created_at,d.qty,m.name AS item_name,n.name AS ngo_name FROM donations d JOIN menu_items m ON d.menu_item_id=m.id JOIN ngos n ON d.ngo_id=n.id WHERE d.user_id=? ORDER BY d.created_at DESC LIMIT 20", (user_id,)).fetchall()
    return render_template('donation.html', items=items, ngos=ngos, donations=donations)

@app.route('/analytics')
@login_required()
def analytics():
    db=get_db(); user_id=session['user_id']
    thirty_days_ago=(datetime.now().date()-timedelta(days=30)).isoformat(); today=datetime.now().date().isoformat()
    daily=db.execute("SELECT date,SUM(prepared_qty) AS prepared,SUM(sold_qty) AS sold,SUM(wasted_qty) AS wasted FROM daily_records WHERE user_id=? AND date BETWEEN ? AND ? GROUP BY date ORDER BY date ASC",(user_id,thirty_days_ago,today)).fetchall()
    top_waste=db.execute("SELECT m.name, SUM(d.wasted_qty) AS wasted FROM daily_records d JOIN menu_items m ON d.menu_item_id=m.id WHERE d.user_id=? GROUP BY m.name ORDER BY wasted DESC LIMIT 10",(user_id,)).fetchall()
    daily_labels=[d['date'] for d in daily]; daily_prepared=[d['prepared'] or 0 for d in daily]; daily_sold=[d['sold'] or 0 for d in daily]; daily_wasted=[d['wasted'] or 0 for d in daily]
    top_labels=[row['name'] for row in top_waste]; top_values=[row['wasted'] or 0 for row in top_waste]
    return render_template('analytics.html', daily=daily, top_waste=top_waste, daily_labels=daily_labels, daily_prepared=daily_prepared, daily_sold=daily_sold, daily_wasted=daily_wasted, top_labels=top_labels, top_values=top_values)

@app.route('/download/monthly')
@login_required()
def download_monthly():
    db=get_db(); user_id=session['user_id']
    thirty_days_ago=(datetime.now().date()-timedelta(days=30)).isoformat(); today=datetime.now().date().isoformat()
    rows=db.execute("SELECT date,SUM(prepared_qty) AS prepared,SUM(sold_qty) AS sold,SUM(wasted_qty) AS wasted FROM daily_records WHERE user_id=? AND date BETWEEN ? AND ? GROUP BY date ORDER BY date ASC",(user_id,thirty_days_ago,today)).fetchall()
    buf=io.StringIO(); w=csv.writer(buf); w.writerow(['Date','Prepared','Sold','Waste'])
    for r in rows: w.writerow([r['date'], r['prepared'] or 0, r['sold'] or 0, r['wasted'] or 0])
    csv_data=buf.getvalue(); buf.close(); fn=f"monthly_report_{today}.csv"
    return Response(csv_data, mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={fn}'})

@app.route('/download/daily')
@login_required()
def download_daily():
    db=get_db(); user_id=session['user_id']
    date_str=request.args.get('date') or datetime.now().date().isoformat()
    rows=db.execute("SELECT m.name AS item_name, d.prepared_qty, d.sold_qty, d.wasted_qty, d.reason FROM daily_records d JOIN menu_items m ON d.menu_item_id=m.id WHERE d.user_id=? AND d.date=? ORDER BY m.name",(user_id,date_str)).fetchall()
    buf=io.StringIO(); w=csv.writer(buf); w.writerow(['Date','Item','Prepared','Sold','Waste','Reason'])
    for r in rows: w.writerow([date_str, r['item_name'], r['prepared_qty'], r['sold_qty'], r['wasted_qty'], r['reason']])
    csv_data=buf.getvalue(); buf.close(); fn=f"daily_report_{date_str}.csv"
    return Response(csv_data, mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={fn}'})

@app.route('/admin', methods=['GET','POST'])
@login_required(role='admin')
def admin_panel():
    db=get_db()
    if request.method=='POST':
        ngo_name=request.form.get('ngo_name','').strip(); ngo_contact=request.form.get('ngo_contact','').strip(); ngo_email=request.form.get('ngo_email','').strip()
        if ngo_name: db.execute("INSERT INTO ngos (name,contact,email) VALUES (?,?,?)", (ngo_name, ngo_contact, ngo_email)); db.commit(); flash("NGO added.", "success"); return redirect(url_for('admin_panel'))
    users=db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall(); ngos=db.execute("SELECT * FROM ngos ORDER BY name").fetchall()
    return render_template('admin.html', users=users, ngos=ngos)

if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
