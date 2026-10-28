import os
from dotenv import load_dotenv
load_dotenv()
import sqlite3
import re
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, flash, jsonify, redirect, render_template,
    request, session, url_for, send_from_directory
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "brew_bloom.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "local-demo-change-this-secret-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

ADMIN_USERNAME = os.environ.get("BREW_ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("BREW_ADMIN_PASSWORD")
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

MENU_ITEMS = [
    ("Espresso Romano", 4.50, "A bold double shot of Arabica espresso served with a twist of fresh lemon zest.", "Double Shot • 60ml"),
    ("Caramel Macchiato", 5.75, "Velvety steamed milk layered with espresso and salted vanilla caramel.", "Hot or Iced • 350ml"),
    ("Golden Honey Latte", 6.00, "Oat milk, wildflower honey and espresso finished with cinnamon.", "Creamy • 300ml"),
    ("Cold Brew Reserve", 5.25, "Slow-steeped coffee that is smooth, rich and naturally sweet.", "Slow Steeped • 400ml"),
]
ORDER_STATUSES = {"Pending", "Preparing", "Completed", "Cancelled"}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL CHECK(price >= 0),
                description TEXT NOT NULL DEFAULT '',
                serving_size TEXT NOT NULL DEFAULT '',
                available INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 20),
                unit_price REAL NOT NULL,
                total REAL NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL,
                FOREIGN KEY(item_id) REFERENCES menu_items(id)
            );
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        for name, price, description, serving_size in MENU_ITEMS:
            db.execute(
                """INSERT OR IGNORE INTO menu_items
                   (name, price, description, serving_size) VALUES (?, ?, ?, ?)""",
                (name, price, description, serving_size),
            )


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    # Serves the existing CSS, JS, images/, and videos/ files without changing their paths.
    safe_roots = {"style.css", "script.js", "images", "videos", "favicon.ico"}
    first_part = filename.split("/", 1)[0]
    if first_part not in safe_roots:
        abort(404)
    return send_from_directory(BASE_DIR, filename)


@app.get("/api/menu")
def api_menu():
    with get_db() as db:
        rows = db.execute(
            "SELECT id, name, price, description, serving_size FROM menu_items WHERE available = 1 ORDER BY id"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/orders")
def create_order():
    data = request.get_json(silent=True) or request.form
    name = str(data.get("customer_name", "")).strip()
    email = str(data.get("customer_email", "")).strip()
    item_id = data.get("item_id")
    notes = str(data.get("notes", "")).strip()[:500]

    try:
        quantity = int(data.get("quantity", 1))
        item_id = int(item_id)
    except (TypeError, ValueError):
        return jsonify(error="Choose a menu item and a valid quantity."), 400

    if not name or len(name) > 100:
        return jsonify(error="Enter your name (up to 100 characters)."), 400
    if not re_email(email):
        return jsonify(error="Enter a valid email address."), 400
    if quantity < 1 or quantity > 20:
        return jsonify(error="Quantity must be between 1 and 20."), 400

    with get_db() as db:
        item = db.execute(
            "SELECT id, name, price FROM menu_items WHERE id = ? AND available = 1", (item_id,)
        ).fetchone()
        if item is None:
            return jsonify(error="That menu item is not available."), 404
        total = round(item["price"] * quantity, 2)
        cursor = db.execute(
            """INSERT INTO orders
               (customer_name, customer_email, item_id, item_name, quantity,
                unit_price, total, notes, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)""",
            (name, email, item["id"], item["name"], quantity, item["price"],
             total, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        order_id = cursor.lastrowid
    return jsonify(message="Order saved successfully.", order_id=order_id, total=total), 201


@app.post("/api/contact")
def create_contact_message():
    data = request.get_json(silent=True) or request.form
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    message = str(data.get("message", "")).strip()

    if not name or len(name) > 100:
        return jsonify(error="Enter your name (up to 100 characters)."), 400
    if not re_email(email):
        return jsonify(error="Enter a valid email address."), 400
    if not message or len(message) > 3000:
        return jsonify(error="Message must be between 1 and 3000 characters."), 400

    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO contact_messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
            (name, email, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        message_id = cursor.lastrowid
    return jsonify(message="Your message has been saved.", message_id=message_id), 201


def re_email(value):
    # Simple format check for a college demo; production systems should verify email ownership.
    import re
    return len(value) <= 254 and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value) is not None



@app.get("/admin-assets/admin.css")
def admin_static_css():
    return send_from_directory(BASE_DIR / "templates", "admin.css")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session.clear()
            session["is_admin"] = True
            session["admin_username"] = username
            return redirect(url_for("admin_dashboard"))
        error = "Incorrect username or password."
    return render_template("admin_login.html", error=error)


@app.post("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    if request.method == "POST":
        try:
            order_id = int(request.form.get("order_id", ""))
        except ValueError:
            abort(400)
        status = request.form.get("status", "")
        if status not in ORDER_STATUSES:
            abort(400)
        with get_db() as db:
            db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        flash(f"Order #{order_id} updated.", "success")
        return redirect(url_for("admin_dashboard"))

    with get_db() as db:
        orders = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        messages = db.execute("SELECT * FROM contact_messages ORDER BY id DESC").fetchall()
        menu = db.execute("SELECT * FROM menu_items ORDER BY id").fetchall()
    return render_template(
        "admin_dashboard.html",
        orders=orders, messages=messages, menu=menu, statuses=sorted(ORDER_STATUSES)
    )


@app.post("/admin/menu/<int:item_id>/availability")
@admin_required
def toggle_menu_item(item_id):
    with get_db() as db:
        row = db.execute("SELECT available, name FROM menu_items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            abort(404)
        new_value = 0 if row["available"] else 1
        db.execute("UPDATE menu_items SET available = ? WHERE id = ?", (new_value, item_id))
    flash(f"{row['name']} is now {'available' if new_value else 'hidden from ordering'}.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    init_db()
    print("Brew & Bloom is starting at http://127.0.0.1:5000")
    print("Admin login: username=admin, password=CoffeeDemo123! (change this before sharing/deployment)")
    app.run(debug=True)
