import sqlite3
import os
import hashlib
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), 'database.db')

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def create_tables():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT, item_code TEXT, name TEXT, cost_price REAL, selling_price REAL, stock INTEGER)")
        cursor.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'Staff')")
        cursor.execute("CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user TEXT, action TEXT, details TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, contact TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, quantity INTEGER, total REAL, date TEXT, FOREIGN KEY (product_id) REFERENCES products (id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value REAL)")
        conn.commit()

def add_log(user, action, details):
    with get_connection() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO logs (timestamp, user, action, details) VALUES (?, ?, ?, ?)", (now, user, action, details))

def get_logs():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 50").fetchall()

# --- Products ---
def add_product(user, item_code, name, cost, price, stock):
    with get_connection() as conn:
        conn.execute("INSERT INTO products (item_code, name, cost_price, selling_price, stock) VALUES (?, ?, ?, ?, ?)", (item_code, name, cost, price, stock))
    add_log(user, "ADD_PRODUCT", f"Added {name}")

def update_product(user, p_id, item_code, name, cost, price, stock):
    with get_connection() as conn:
        conn.execute("UPDATE products SET item_code=?, name=?, cost_price=?, selling_price=?, stock=? WHERE id=?", (item_code, name, cost, price, stock, p_id))
    add_log(user, "UPDATE_PRODUCT", f"Updated ID {p_id}")

def delete_product(user, p_id, p_name):
    with get_connection() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (p_id,))
    add_log(user, "DELETE_PRODUCT", f"Deleted {p_name}")

def get_products():
    with get_connection() as conn: return conn.execute("SELECT * FROM products").fetchall()

# --- Customers ---
def add_customer(user, name, contact):
    with get_connection() as conn:
        conn.execute("INSERT INTO customers (name, contact) VALUES (?, ?)", (name, contact))
    add_log(user, "ADD_CUSTOMER", f"Added {name}")

def update_customer(user, c_id, name, contact):
    with get_connection() as conn:
        conn.execute("UPDATE customers SET name=?, contact=? WHERE id=?", (name, contact, c_id))
    add_log(user, "UPDATE_CUSTOMER", f"Updated ID {c_id}")

def delete_customer(user, c_id, name):
    with get_connection() as conn:
        conn.execute("DELETE FROM customers WHERE id=?", (c_id,))
    add_log(user, "DELETE_CUSTOMER", f"Deleted {name}")

def get_customers():
    with get_connection() as conn: return conn.execute("SELECT * FROM customers").fetchall()

# --- Sales & Auth ---
def add_sale(user, p_id, p_name, qty, total, date):
    with get_connection() as conn:
        conn.execute("INSERT INTO sales (product_id, quantity, total, date) VALUES (?, ?, ?, ?)", (p_id, qty, total, date))
        conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, p_id))
    add_log(user, "SALE", f"Sold {qty} of {p_name}")

def login_user(u, p):
    hashed_p = hash_password(p)
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hashed_p)).fetchone()

def register_user(u, p, role="Staff"):
    try:
        hashed_p = hash_password(p)
        with get_connection() as conn:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (u, hashed_p, role))
            return True
    except: return False

def get_sales_analytics():
    with get_connection() as conn:
        return conn.execute("SELECT sales.date, products.name, sales.quantity, sales.total, (products.cost_price * sales.quantity) FROM sales JOIN products ON sales.product_id = products.id").fetchall()
