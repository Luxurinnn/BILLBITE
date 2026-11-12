
import sqlite3
from pathlib import Path

# Lokasi database di folder yang sama dengan file ini
DB_PATH = Path(__file__).resolve().parent / "fj_billiard.db"


def get_connection():
    """Membuka koneksi ke database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_database():
    """Membuat seluruh tabel database FJ BILLIARD."""
    conn = get_connection()

    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member'
                CHECK (role IN ('member', 'owner', 'staff', 'kitchen')),
            email_verified INTEGER NOT NULL DEFAULT 0
                CHECK (email_verified IN (0, 1)),
            is_active INTEGER NOT NULL DEFAULT 1
                CHECK (is_active IN (0, 1)),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS staff_invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL COLLATE NOCASE,
            role TEXT NOT NULL
                CHECK (role IN ('owner', 'staff', 'kitchen')),
            invite_code_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS billiard_tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1
                CHECK (is_active IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_code TEXT NOT NULL UNIQUE,
            customer_id INTEGER NOT NULL,
            table_id INTEGER NOT NULL,
            start_at TEXT NOT NULL,
            end_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN (
                    'pending', 'confirmed', 'cancelled',
                    'expired', 'completed'
                )),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            CHECK (end_at > start_at),
            FOREIGN KEY (customer_id) REFERENCES users(id),
            FOREIGN KEY (table_id) REFERENCES billiard_tables(id)
        );

        CREATE INDEX IF NOT EXISTS idx_booking_table_time
        ON bookings(table_id, start_at, end_at, status);

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            table_id INTEGER NOT NULL,
            staff_id INTEGER,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN (
                    'active', 'paused', 'completed', 'cancelled'
                )),
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (table_id) REFERENCES billiard_tables(id),
            FOREIGN KEY (staff_id) REFERENCES users(id),
            CHECK (ended_at IS NULL OR ended_at >= started_at)
        );

        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL
                CHECK (category IN ('food', 'drink', 'other')),
            price INTEGER NOT NULL CHECK (price >= 0),
            is_available INTEGER NOT NULL DEFAULT 1
                CHECK (is_available IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL UNIQUE,
            customer_id INTEGER,
            booking_id INTEGER,
            session_id INTEGER,
            status TEXT NOT NULL DEFAULT 'awaiting_payment'
                CHECK (status IN (
                    'awaiting_payment', 'queued', 'preparing',
                    'ready', 'served', 'cancelled'
                )),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users(id),
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
            FOREIGN KEY (order_id) REFERENCES orders(id)
                ON DELETE CASCADE,
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_code TEXT NOT NULL UNIQUE,
            booking_id INTEGER,
            session_id INTEGER,
            order_id INTEGER,
            recorded_by INTEGER,
            method TEXT NOT NULL CHECK (method IN ('cash', 'qris')),
            amount INTEGER NOT NULL CHECK (amount >= 0),
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN (
                    'pending', 'paid', 'failed', 'refunded'
                )),
            provider_reference TEXT,
            paid_at TEXT DEFAULT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (recorded_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS rate_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hourly_rate INTEGER NOT NULL CHECK (hourly_rate >= 0),
            effective_from TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER,
            FOREIGN KEY (updated_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE SET NULL
        );
        """)

        conn.commit()

        print("\nDatabase FJ BILLIARD berhasil dibuat!")
        print(f"Lokasi database: {DB_PATH}")
        print("\nDaftar tabel:")

        tables = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        for table in tables:
            print("-", table["name"])

        # Pastikan tabel users benar-benar tersedia.
        check = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'users'
        """).fetchone()

        if check:
            print("\nPemeriksaan tabel users: BERHASIL")
        else:
            print("\nPemeriksaan tabel users: GAGAL")

    except sqlite3.Error as error:
        conn.rollback()
        print(f"Gagal membuat database: {error}")

    finally:
        conn.close()


if __name__ == "__main__":
    create_database()
