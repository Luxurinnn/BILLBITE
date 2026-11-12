import os
import sqlite3
from pathlib import Path
from functools import wraps

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fj_billiard.db"

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    app.secret_key = os.urandom(32)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email dan password wajib diisi.")
            return render_template("login.html")

        conn = get_db()
        try:
            user = conn.execute(
                """
                SELECT id, full_name, email, password_hash,
                       role, email_verified, is_active
                FROM users
                WHERE email = ? COLLATE NOCASE
                """,
                (email,)
            ).fetchone()
        finally:
            conn.close()

        if user is None or not check_password_hash(
            user["password_hash"], password
        ):
            flash("Email atau password salah.")
            return render_template("login.html")

        if not user["is_active"]:
            flash("Akun belum aktif.")
            return render_template("login.html")

        if not user["email_verified"]:
            flash("Email belum diverifikasi.")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]
        session["role"] = user["role"]

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not full_name or not email or not password:
            flash("Semua kolom wajib diisi.")
            return render_template("register.html")

        conn = get_db()
        try:
            existing_user = conn.execute(
                "SELECT id FROM users WHERE email = ? COLLATE NOCASE",
                (email,)
            ).fetchone()

            if existing_user:
                flash("Email sudah terdaftar. Silakan masuk.")
                return redirect(url_for("login"))

            conn.execute(
                """
                INSERT INTO users (
                    full_name, email, password_hash, role,
                    email_verified, is_active
                )
                VALUES (?, ?, ?, 'member', 1, 1)
                """,
                (full_name, email, generate_password_hash(password))
            )
            conn.commit()
            flash("Pendaftaran berhasil! Silakan masuk dengan akun Anda.")
            return redirect(url_for("login"))
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Terjadi kesalahan pada database: {e}")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    try:
        tables = conn.execute(
            "SELECT id, table_number, is_active FROM billiard_tables ORDER BY table_number"
        ).fetchall()
        
        recent_orders = conn.execute(
            """
            SELECT o.order_number, o.status, 
                   COALESCE(u.full_name, 'Pelanggan Umum') as customer_name,
                   (SELECT SUM(quantity * unit_price) FROM order_items WHERE order_id = o.id) as total_price
            FROM orders o
            LEFT JOIN users u ON o.customer_id = u.id
            ORDER BY o.id DESC LIMIT 5
            """
        ).fetchall()

        recent_transactions = conn.execute(
            """
            SELECT p.payment_code, p.method, p.amount, p.status,
                   COALESCE(u.full_name, 'Pelanggan') as customer_name
            FROM payments p
            LEFT JOIN users u ON p.recorded_by = u.id
            ORDER BY p.id DESC LIMIT 5
            """
        ).fetchall()

        total_tables = len(tables)
        active_tables_count = conn.execute(
            "SELECT COUNT(DISTINCT table_id) FROM sessions WHERE status = 'active'"
        ).fetchone()[0]

    finally:
        conn.close()

    return render_template(
        "dashboard.html",
        nama=session.get("full_name", "Pengguna"),
        role=session.get("role", "member"),
        tables=tables,
        recent_orders=recent_orders,
        recent_transactions=recent_transactions,
        total_tables=total_tables,
        active_tables_count=active_tables_count
    )


@app.route("/meja")
@login_required
def meja_billiard():
    conn = get_db()
    try:
        tables = conn.execute(
            "SELECT id, table_number, is_active FROM billiard_tables ORDER BY table_number"
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        "meja.html",
        tables=tables,
        nama=session.get("full_name", "Pengguna"),
        role=session.get("role", "member")
    )


@app.route("/menu")
@login_required
def menu_makanan():
    conn = get_db()
    try:
        menu_items = conn.execute(
            "SELECT id, name, category, price, is_available FROM menu_items ORDER BY category, name"
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        "menu.html",
        menu_items=menu_items,
        nama=session.get("full_name", "Pengguna"),
        role=session.get("role", "member")
    )


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/booking')
@login_required
def booking_page():
    conn = get_db()
    try:
        # Ambil data booking jika tabelnya sudah ada, atau kosongkan
        bookings = []
    finally:
        conn.close()
    
    return render_template(
        'booking.html', 
        nama=session.get("full_name", "Pengguna"), 
        role=session.get("role", "member"), 
        bookings=bookings
    )

@app.route('/pesanan')
@login_required
def pesanan_page():
    conn = get_db()
    try:
        recent_orders = conn.execute(
            """
            SELECT o.order_number, o.status, 
                   COALESCE(u.full_name, 'Pelanggan Umum') as customer_name,
                   (SELECT SUM(quantity * unit_price) FROM order_items WHERE order_id = o.id) as total_price
            FROM orders o
            LEFT JOIN users u ON o.customer_id = u.id
            ORDER BY o.id DESC
            """
        ).fetchall()
    finally:
        conn.close()
    
    return render_template(
        'pesanan.html', 
        nama=session.get("full_name", "Pengguna"), 
        role=session.get("role", "member"), 
        recent_orders=recent_orders
    )

@app.route('/transaksi')
@login_required
def transaksi_page():
    conn = get_db()
    try:
        recent_transactions = conn.execute(
            """
            SELECT p.payment_code, p.method, p.amount, p.status,
                   COALESCE(u.full_name, 'Pelanggan') as customer_name
            FROM payments p
            LEFT JOIN users u ON p.recorded_by = u.id
            ORDER BY p.id DESC
            """
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        'transaksi.html',
        nama=session.get("full_name", "Pengguna"),
        role=session.get("role", "member"),
        recent_transactions=recent_transactions
    )
    
if __name__ == "__main__":
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "Database belum ada. Jalankan python database.py dahulu."
        )

    app.run(debug=True)