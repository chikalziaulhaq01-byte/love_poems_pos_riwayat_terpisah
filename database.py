"""
database.py
Inisialisasi database SQLite untuk Love Poems Coffee Shop POS.
Jalankan file ini sekali di awal (atau otomatis dipanggil oleh app.py)
untuk membuat tabel dan mengisi data awal (menu + user login).
"""

import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "love_poems.db")


def hash_password(password: str) -> str:
    """Hash password sederhana pakai SHA-256 (cukup untuk project tugas kuliah)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ---------- Tabel Users ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------- Tabel Menu ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT UNIQUE NOT NULL,
            harga INTEGER NOT NULL,
            foto_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Catatan: tabel "transactions" dan "transaction_items" (riwayat transaksi)
    # SEKARANG disimpan di database terpisah -> lihat riwayat_db.py (riwayat.db)

    conn.commit()

    # ---------- Seed: user default ----------
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("chikal ziaulhaq", hash_password("12345678")),
        )

    # ---------- Seed: menu awal ----------
    cur.execute("SELECT COUNT(*) FROM menu")
    if cur.fetchone()[0] == 0:
        menu_awal = [
            ("Black Coffee", 25000, "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&auto=format&fit=crop&q=60"),
            ("White Coffee", 25000, "https://images.unsplash.com/photo-1534778101976-62847782c213?w=400&auto=format&fit=crop&q=60"),
            ("Espresso", 20000, "https://images.unsplash.com/photo-1510707577719-0d158d349386?w=400&auto=format&fit=crop&q=60"),
            ("Americano", 20000, "https://images.unsplash.com/photo-1551046713-2d2d0b57fa0d?w=400&auto=format&fit=crop&q=60"),
            ("Caffe Latte", 26000, "https://images.unsplash.com/photo-1570968915860-54d5c301fc9f?w=400&auto=format&fit=crop&q=60"),
            ("Cappuccino", 22000, "https://images.unsplash.com/photo-1534778101976-62847782c213?w=400&auto=format&fit=crop&q=60"),
            ("Flat White", 28000, "https://images.unsplash.com/photo-1577968897966-3d4325b36b61?w=400&auto=format&fit=crop&q=60"),
            ("Macchiato", 25000, "https://images.unsplash.com/photo-1485808191679-5f86510681a2?w=400&auto=format&fit=crop&q=60"),
            ("Affogato", 28000, "https://images.unsplash.com/photo-1594911774802-8822a707cbb3?w=400&auto=format&fit=crop&q=60"),
            ("Manual Brew V60", 20000, "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&auto=format&fit=crop&q=60"),
            ("Nitro Cold Brew", 28000, "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?w=400&auto=format&fit=crop&q=60"),
            ("Frappe", 32000, "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400&auto=format&fit=crop&q=60"),
            ("Vietnam Drip", 25000, "https://images.unsplash.com/photo-1541167760496-1628856ab772?w=400&auto=format&fit=crop&q=60"),
            ("Mocha", 28000, "https://images.unsplash.com/photo-1606791405792-1004f1718d4c?w=400&auto=format&fit=crop&q=60"),
        ]
        cur.executemany(
            "INSERT INTO menu (nama, harga, foto_url) VALUES (?, ?, ?)", menu_awal
        )

    conn.commit()
    conn.close()
    print(f"Database siap di: {DB_PATH}")


if __name__ == "__main__":
    init_db()
