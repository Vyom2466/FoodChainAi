CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    restaurant_name TEXT,
    location TEXT,
    email TEXT,
    phone TEXT,
    is_email_verified INTEGER DEFAULT 0,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS otp_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    email TEXT,
    phone TEXT,
    otp_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    is_used INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS inventory_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    purchase_date TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_price REAL,
    supplier TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
);
CREATE TABLE IF NOT EXISTS billing_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    bill_date TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_price REAL,
    total_amount REAL,
    customer_info TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
);
CREATE TABLE IF NOT EXISTS festivals_seasons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    multiplier REAL DEFAULT 1.0,
    description TEXT
);
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    price REAL,
    shelf_life_days INTEGER,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS daily_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    prepared_qty REAL NOT NULL,
    sold_qty REAL NOT NULL,
    wasted_qty REAL NOT NULL,
    reason TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
);
CREATE TABLE IF NOT EXISTS ngos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT,
    email TEXT
);
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    ngo_id INTEGER NOT NULL,
    qty REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(menu_item_id) REFERENCES menu_items(id),
    FOREIGN KEY(ngo_id) REFERENCES ngos(id)
);
