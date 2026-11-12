import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "fj_billiard.db"

def seed_billiard_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Masukkan 12 Meja Billiard
        tables_data = [(f"{i:02d}", 1) for i in range(1, 13)]
        
        cursor.executemany("""
            INSERT INTO billiard_tables (table_number, is_active)
            VALUES (?, ?)
            ON CONFLICT(table_number) DO NOTHING
        """, tables_data)
        
        # 2. Opsional: Tambahkan beberapa sampel item menu jika belum ada
        menu_items = [
            ("Kopi Susu", "drink", 18000, 1),
            ("Mie Goreng", "food", 22000, 1),
            ("Es Teh", "drink", 8000, 1),
            ("Kentang Goreng", "food", 20000, 1),
        ]
        
        cursor.executemany("""
            INSERT INTO menu_items (name, category, price, is_available)
            VALUES (?, ?, ?, ?)
        """, menu_items)

        conn.commit()
        print("✓ Berhasil mengisikan 12 Meja Billiard ke dalam database!")

        # Tampilkan daftar meja
        cursor.execute("SELECT id, table_number, is_active FROM billiard_tables")
        rows = cursor.fetchall()
        print("\nDaftar Meja Billiard:")
        for row in rows:
            status = "Aktif" if row[2] else "Nonaktif"
            print(f"- ID: {row[0]} | Nomot Meja: Meja {row[1]} | Status: {status}")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Gagal mengisikan data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_billiard_tables()