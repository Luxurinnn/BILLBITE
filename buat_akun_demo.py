import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent / "fj_billiard.db"

email = "user@gmail.com"
password = "user"
password_hash = generate_password_hash(password)

conn = sqlite3.connect(DB_PATH)

try:
    # Masukkan jika belum ada
    conn.execute("""
        INSERT INTO users (
            full_name, email, password_hash, role,
            email_verified, is_active
        )
        VALUES (?, ?, ?, ?, 1, 1)
        ON CONFLICT(email) DO UPDATE SET
            password_hash = excluded.password_hash,
            email_verified = 1,
            is_active = 1
    """, (
        "Demo Member",
        email,
        password_hash,
        "member"
    ))
    conn.commit()

    user = conn.execute(
        "SELECT id FROM users WHERE email = ? COLLATE NOCASE",
        (email,)
    ).fetchone()

    print("Akun demo berhasil diperbarui/disiapkan!")
    print("Email:", email)
    print("Password:", password)

    if user:
        print("ID akun:", user[0])

finally:
    conn.close()