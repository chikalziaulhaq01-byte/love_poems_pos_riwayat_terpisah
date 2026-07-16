"""
app.py
Backend Flask untuk Love Poems Coffee Shop POS.

Cara menjalankan:
    pip install flask
    python app.py

Lalu buka http://127.0.0.1:5000 di browser.
"""

from flask import Flask, jsonify, request, render_template
from database import get_connection, init_db, hash_password
import riwayat_db as rwdb
import datetime

app = Flask(__name__)

# Inisialisasi database utama (users + menu) & database riwayat (transaksi/pendapatan)
# saat app pertama kali start. Keduanya file .db yang terpisah.
init_db()
rwdb.init_riwayat_db()


# ============================================================
#  HALAMAN UTAMA
# ============================================================
@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
#  AUTH
# ============================================================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username dan password wajib diisi."}), 400

    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if row and row["password_hash"] == hash_password(password):
        return jsonify({"success": True, "message": "Login berhasil.", "username": row["username"]})
    return jsonify({"success": False, "message": "Nama pengguna atau kata sandi salah."}), 401


@app.route("/api/register", methods=["POST"])
def register():
    """Opsional: mendaftarkan user baru ke database."""
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username dan password wajib diisi."}), 400

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
    except Exception:
        conn.close()
        return jsonify({"success": False, "message": "Username sudah terdaftar."}), 409
    conn.close()
    return jsonify({"success": True, "message": "Registrasi berhasil."})


# ============================================================
#  MENU (CRUD)
# ============================================================
@app.route("/api/menu", methods=["GET"])
def get_menu():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM menu ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/menu", methods=["POST"])
def add_menu():
    data = request.get_json(force=True)
    nama = (data.get("nama") or "").strip()
    harga = data.get("harga")
    foto_url = (data.get("foto_url") or "").strip()

    if not nama or harga is None:
        return jsonify({"success": False, "message": "Nama dan harga wajib diisi."}), 400
    try:
        harga = int(harga)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Harga harus berupa angka."}), 400

    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO menu (nama, harga, foto_url) VALUES (?, ?, ?)",
            (nama, harga, foto_url),
        )
        conn.commit()
        new_id = cur.lastrowid
    except Exception:
        conn.close()
        return jsonify({"success": False, "message": "Menu dengan nama tersebut sudah ada."}), 409
    conn.close()
    return jsonify({"success": True, "id": new_id})


@app.route("/api/menu/<int:menu_id>", methods=["PUT"])
def update_menu(menu_id):
    data = request.get_json(force=True)
    nama = (data.get("nama") or "").strip()
    harga = data.get("harga")
    foto_url = (data.get("foto_url") or "").strip()

    conn = get_connection()
    existing = conn.execute("SELECT * FROM menu WHERE id = ?", (menu_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"success": False, "message": "Menu tidak ditemukan."}), 404

    nama = nama or existing["nama"]
    foto_url = foto_url or existing["foto_url"]
    try:
        harga = int(harga) if harga is not None else existing["harga"]
    except (TypeError, ValueError):
        conn.close()
        return jsonify({"success": False, "message": "Harga harus berupa angka."}), 400

    conn.execute(
        "UPDATE menu SET nama = ?, harga = ?, foto_url = ? WHERE id = ?",
        (nama, harga, foto_url, menu_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/menu/<int:menu_id>", methods=["DELETE"])
def delete_menu(menu_id):
    conn = get_connection()
    existing = conn.execute("SELECT * FROM menu WHERE id = ?", (menu_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"success": False, "message": "Menu tidak ditemukan."}), 404
    conn.execute("DELETE FROM menu WHERE id = ?", (menu_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ============================================================
#  CHECKOUT / TRANSAKSI
# ============================================================
@app.route("/api/checkout", methods=["POST"])
def checkout():
    """
    Body JSON:
    {
        "cart": {"1": 2, "3": 1},   # menu_id -> qty
        "uang_bayar": 100000,
        "nama_pemesan": "Budi",
        "meja": "A1"
    }
    """
    data = request.get_json(force=True)
    cart = data.get("cart") or {}
    uang_bayar = data.get("uang_bayar")
    nama_pemesan = (data.get("nama_pemesan") or "").strip()
    meja = (data.get("meja") or "").strip()

    if not nama_pemesan:
        return jsonify({"success": False, "message": "Nama pemesan wajib diisi."}), 400
    if not meja:
        return jsonify({"success": False, "message": "Nomor/nama meja wajib diisi."}), 400
    if not cart:
        return jsonify({"success": False, "message": "Keranjang masih kosong."}), 400
    try:
        uang_bayar = int(uang_bayar)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Jumlah pembayaran tidak valid."}), 400

    conn = get_connection()

    items = []
    total = 0
    for menu_id_str, qty in cart.items():
        try:
            menu_id = int(menu_id_str)
            qty = int(qty)
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue
        row = conn.execute("SELECT * FROM menu WHERE id = ?", (menu_id,)).fetchone()
        if not row:
            continue
        subtotal = row["harga"] * qty
        total += subtotal
        items.append({
            "menu_id": menu_id,
            "nama": row["nama"],
            "harga": row["harga"],
            "qty": qty,
            "subtotal": subtotal,
        })

    if not items:
        conn.close()
        return jsonify({"success": False, "message": "Tidak ada item valid di keranjang."}), 400

    if uang_bayar < total:
        conn.close()
        return jsonify({
            "success": False,
            "message": f"Uang kurang! Membutuhkan Rp {total - uang_bayar:,} lagi.".replace(",", "."),
        }), 400

    kembalian = uang_bayar - total
    conn.close()

    # Riwayat transaksi disimpan di database TERPISAH (riwayat.db), bukan di love_poems.db
    transaction_id, waktu, tanggal = rwdb.catat_transaksi(
        nama_pemesan, meja, items, total, uang_bayar, kembalian
    )

    return jsonify({
        "success": True,
        "transaction_id": transaction_id,
        "waktu": waktu,
        "tanggal": tanggal,
        "nama_pemesan": nama_pemesan,
        "meja": meja,
        "items": items,
        "total": total,
        "uang_bayar": uang_bayar,
        "kembalian": kembalian,
    })


@app.route("/api/transactions", methods=["GET"])
def list_transactions():
    """Riwayat transaksi (dari database riwayat.db yang terpisah), terbaru duluan."""
    return jsonify(rwdb.list_riwayat(limit=50))


@app.route("/api/riwayat/rekap", methods=["GET"])
def rekap_riwayat():
    """Rekap penghasilan/pendapatan: hari ini, bulan ini, total, & menu terlaris."""
    return jsonify(rwdb.get_rekap())


if __name__ == "__main__":
    app.run(debug=True, port=5050)
