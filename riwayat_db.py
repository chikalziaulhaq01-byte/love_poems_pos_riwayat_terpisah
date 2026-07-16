"""
riwayat_db.py
Database SQLite TERPISAH khusus untuk Riwayat Transaksi Love Poems Coffee Shop.

Kenapa dipisah dari love_poems.db?
- Supaya data user & menu (love_poems.db) tidak bercampur dengan data
  transaksi/riwayat penjualan (riwayat.db).
- Memudahkan backup / analisis pendapatan tanpa menyentuh database utama.

File ini menyimpan:
- transactions        : header setiap transaksi (nama pemesan, meja, waktu, total, dll)
- transaction_items    : rincian item per transaksi
Serta menyediakan fungsi rekap pendapatan (harian, bulanan, total, menu terlaris).
"""

import sqlite3
import os
import datetime

RIWAYAT_DB_PATH = os.path.join(os.path.dirname(__file__), "riwayat.db")


def get_riwayat_connection():
    conn = sqlite3.connect(RIWAYAT_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_riwayat_db():
    conn = get_riwayat_connection()
    cur = conn.cursor()

    # ---------- Tabel Transaksi (header struk) ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT DEFAULT CURRENT_TIMESTAMP,
            tanggal TEXT NOT NULL,
            nama_pemesan TEXT NOT NULL DEFAULT '',
            meja TEXT NOT NULL DEFAULT '',
            total INTEGER NOT NULL,
            uang_bayar INTEGER NOT NULL,
            kembalian INTEGER NOT NULL
        )
    """)

    # ---------- Tabel Detail Item per Transaksi ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            menu_id INTEGER,
            nama_menu TEXT NOT NULL,
            harga_satuan INTEGER NOT NULL,
            qty INTEGER NOT NULL,
            subtotal INTEGER NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # ---------- Migrasi ringan: jaga-jaga jika tabel lama belum punya kolom baru ----------
    existing_cols = [r["name"] for r in cur.execute("PRAGMA table_info(transactions)").fetchall()]
    if "nama_pemesan" not in existing_cols:
        cur.execute("ALTER TABLE transactions ADD COLUMN nama_pemesan TEXT NOT NULL DEFAULT ''")
    if "meja" not in existing_cols:
        cur.execute("ALTER TABLE transactions ADD COLUMN meja TEXT NOT NULL DEFAULT ''")
    if "tanggal" not in existing_cols:
        cur.execute("ALTER TABLE transactions ADD COLUMN tanggal TEXT NOT NULL DEFAULT ''")

    conn.commit()
    conn.close()
    print(f"Database riwayat siap di: {RIWAYAT_DB_PATH}")


def catat_transaksi(nama_pemesan, meja, items, total, uang_bayar, kembalian):
    """Simpan satu transaksi + rincian itemnya ke database riwayat. Mengembalikan (transaction_id, waktu, tanggal)."""
    now = datetime.datetime.now()
    waktu = now.strftime("%d-%m-%Y %H:%M:%S")
    tanggal = now.strftime("%Y-%m-%d")

    conn = get_riwayat_connection()
    cur = conn.execute(
        """INSERT INTO transactions
           (waktu, tanggal, nama_pemesan, meja, total, uang_bayar, kembalian)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (waktu, tanggal, nama_pemesan, meja, total, uang_bayar, kembalian),
    )
    transaction_id = cur.lastrowid

    for it in items:
        conn.execute(
            """INSERT INTO transaction_items
               (transaction_id, menu_id, nama_menu, harga_satuan, qty, subtotal)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (transaction_id, it["menu_id"], it["nama"], it["harga"], it["qty"], it["subtotal"]),
        )

    conn.commit()
    conn.close()
    return transaction_id, waktu, tanggal


def list_riwayat(limit=50):
    """Riwayat transaksi, terbaru duluan, lengkap dengan rincian item."""
    conn = get_riwayat_connection()
    trx_rows = conn.execute(
        "SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()

    result = []
    for t in trx_rows:
        item_rows = conn.execute(
            "SELECT * FROM transaction_items WHERE transaction_id = ?", (t["id"],)
        ).fetchall()
        result.append({
            "id": t["id"],
            "waktu": t["waktu"],
            "tanggal": t["tanggal"],
            "nama_pemesan": t["nama_pemesan"],
            "meja": t["meja"],
            "total": t["total"],
            "uang_bayar": t["uang_bayar"],
            "kembalian": t["kembalian"],
            "items": [dict(i) for i in item_rows],
        })
    conn.close()
    return result


def get_rekap():
    """Rekap penghasilan/pendapatan: hari ini, bulan ini, total keseluruhan, & menu terlaris."""
    conn = get_riwayat_connection()
    now = datetime.datetime.now()
    hari_ini = now.strftime("%Y-%m-%d")
    bulan_ini = now.strftime("%Y-%m")

    def sum_and_count(where_clause, params):
        row = conn.execute(
            f"SELECT COALESCE(SUM(total),0) AS pendapatan, COUNT(*) AS jumlah FROM transactions WHERE {where_clause}",
            params,
        ).fetchone()
        return row["pendapatan"], row["jumlah"]

    pendapatan_hari_ini, jumlah_hari_ini = sum_and_count("tanggal = ?", (hari_ini,))
    pendapatan_bulan_ini, jumlah_bulan_ini = sum_and_count("tanggal LIKE ?", (bulan_ini + "%",))
    pendapatan_total, jumlah_total = sum_and_count("1 = 1", ())

    # ---------- Rekap harian (14 hari terakhir yang ada transaksinya) ----------
    rekap_harian_rows = conn.execute(
        """SELECT tanggal, COALESCE(SUM(total),0) AS pendapatan, COUNT(*) AS jumlah
           FROM transactions GROUP BY tanggal ORDER BY tanggal DESC LIMIT 14"""
    ).fetchall()
    rekap_harian = [dict(r) for r in rekap_harian_rows]

    # ---------- Menu terlaris ----------
    menu_terlaris_rows = conn.execute(
        """SELECT nama_menu, SUM(qty) AS total_qty, SUM(subtotal) AS total_pendapatan
           FROM transaction_items GROUP BY nama_menu ORDER BY total_qty DESC LIMIT 5"""
    ).fetchall()
    menu_terlaris = [dict(r) for r in menu_terlaris_rows]

    conn.close()

    return {
        "pendapatan_hari_ini": pendapatan_hari_ini,
        "jumlah_transaksi_hari_ini": jumlah_hari_ini,
        "pendapatan_bulan_ini": pendapatan_bulan_ini,
        "jumlah_transaksi_bulan_ini": jumlah_bulan_ini,
        "pendapatan_total": pendapatan_total,
        "jumlah_transaksi_total": jumlah_total,
        "rekap_harian": rekap_harian,
        "menu_terlaris": menu_terlaris,
    }


if __name__ == "__main__":
    init_riwayat_db()
