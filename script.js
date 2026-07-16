// ============================================================
//  LOVE POEMS COFFEE SHOP — script.js
//  Semua data (menu, login, transaksi) sekarang diambil/disimpan
//  lewat API Flask (bukan lagi hardcode di JS).
// ============================================================

let MENU_KOPI = {};   // { id: { nama, harga, foto_url } }
let keranjang = {};   // { id: qty }

// ---------- Util ----------
function formatRupiah(n) {
  return "Rp " + n.toLocaleString("id-ID");
}

// ============================================================
//  LOGIN
// ============================================================
document.getElementById("loginForm").addEventListener("submit", async function (e) {
  e.preventDefault();
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value.trim();
  const errorBox = document.getElementById("loginError");
  errorBox.style.display = "none";

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();

    if (data.success) {
      runEntranceTransition();
    } else {
      errorBox.textContent = data.message || "Nama pengguna atau kata sandi salah.";
      errorBox.style.display = "block";
    }
  } catch (err) {
    errorBox.textContent = "Gagal menghubungi server. Pastikan backend Flask berjalan.";
    errorBox.style.display = "block";
  }
});

function runEntranceTransition() {
  const loginScreen = document.getElementById("loginScreen");
  const loadingGate = document.getElementById("loadingGate");
  const posApp = document.getElementById("posApp");

  loginScreen.classList.add("fade-out");

  setTimeout(() => {
    loginScreen.style.display = "none";
    document.body.classList.remove("login-active");
    loadingGate.classList.add("active");

    setTimeout(() => {
      loadingGate.classList.remove("active");
      posApp.style.display = "block";
      posApp.classList.add("entering");
      loadMenu();
    }, 1300);
  }, 500);
}

// ============================================================
//  MENU (ambil dari backend)
// ============================================================
async function loadMenu() {
  const res = await fetch("/api/menu");
  const items = await res.json();
  MENU_KOPI = {};
  items.forEach((item) => {
    MENU_KOPI[item.id] = item;
  });
  renderMenu();
  renderCart();
}

function renderMenu() {
  const grid = document.getElementById("menuGrid");
  grid.innerHTML = "";
  Object.values(MENU_KOPI).forEach((item, idx) => {
    const wrap = document.createElement("div");
    wrap.className = "menu-card-wrap";
    wrap.style.animationDelay = (idx * 0.05) + "s";
    wrap.innerHTML = `
      <div class="menu-card">
        <div class="menu-title">${item.nama}</div>
        <div class="menu-price">${formatRupiah(item.harga)}</div>
      </div>
      <div class="image-container">
        <img src="${item.foto_url}" alt="${item.nama}">
      </div>
      <button class="order-btn" onclick="tambahKeKeranjang(${item.id})">📜 Pesan</button>
      <div class="admin-row">
        <button class="admin-btn" onclick="editMenu(${item.id})">✏️ Edit</button>
        <button class="admin-btn" onclick="hapusMenu(${item.id})">🗑️ Hapus</button>
      </div>
    `;
    grid.appendChild(wrap);
  });
}

// ============================================================
//  ADMIN: TAMBAH / EDIT / HAPUS MENU
// ============================================================
function toggleAdminForm() {
  document.getElementById("adminForm").classList.toggle("active");
}

function resetAdminForm() {
  document.getElementById("editingMenuId").value = "";
  document.getElementById("formNama").value = "";
  document.getElementById("formHarga").value = "";
  document.getElementById("formFoto").value = "";
  document.getElementById("adminAlert").innerHTML = "";
}

function editMenu(id) {
  const item = MENU_KOPI[id];
  if (!item) return;
  document.getElementById("adminForm").classList.add("active");
  document.getElementById("editingMenuId").value = id;
  document.getElementById("formNama").value = item.nama;
  document.getElementById("formHarga").value = item.harga;
  document.getElementById("formFoto").value = item.foto_url;
}

async function submitMenuForm() {
  const id = document.getElementById("editingMenuId").value;
  const nama = document.getElementById("formNama").value.trim();
  const harga = document.getElementById("formHarga").value;
  const foto_url = document.getElementById("formFoto").value.trim();
  const alertBox = document.getElementById("adminAlert");

  if (!nama || !harga) {
    alertBox.innerHTML = `<div class="alert alert-error">Nama dan harga wajib diisi.</div>`;
    return;
  }

  const payload = { nama, harga: parseInt(harga), foto_url };
  const url = id ? `/api/menu/${id}` : "/api/menu";
  const method = id ? "PUT" : "POST";

  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();

  if (data.success) {
    alertBox.innerHTML = `<div class="alert alert-success">Menu berhasil disimpan.</div>`;
    resetAdminForm();
    loadMenu();
  } else {
    alertBox.innerHTML = `<div class="alert alert-error">${data.message}</div>`;
  }
}

async function hapusMenu(id) {
  if (!confirm("Yakin ingin menghapus menu ini?")) return;
  const res = await fetch(`/api/menu/${id}`, { method: "DELETE" });
  const data = await res.json();
  if (data.success) {
    delete keranjang[id];
    loadMenu();
  } else {
    alert(data.message);
  }
}

// ============================================================
//  KERANJANG / CART
// ============================================================
function tambahKeKeranjang(id) {
  keranjang[id] = (keranjang[id] || 0) + 1;
  renderCart();
}

function hitungTotal() {
  return Object.entries(keranjang).reduce((sum, [id, qty]) => {
    const item = MENU_KOPI[id];
    return item ? sum + item.harga * qty : sum;
  }, 0);
}

function renderCart() {
  const cartArea = document.getElementById("cartArea");
  const entries = Object.entries(keranjang).filter(([id]) => MENU_KOPI[id]);

  if (entries.length === 0) {
    cartArea.innerHTML = `<div class="empty-cart">Belum ada ramuan kopi yang dipilih.</div>`;
  } else {
    let rows = entries.map(([id, qty]) => {
      const item = MENU_KOPI[id];
      const subtotal = item.harga * qty;
      return `<tr><td>${item.nama}</td><td>${qty}</td><td>${formatRupiah(subtotal)}</td></tr>`;
    }).join("");
    cartArea.innerHTML = `
      <table>
        <thead><tr><th>Menu Kopi</th><th>Qty</th><th>Subtotal</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }
  document.getElementById("totalValue").textContent = formatRupiah(hitungTotal());
}

function resetTransaksi() {
  keranjang = {};
  document.getElementById("alertArea").innerHTML = "";
  document.getElementById("receiptArea").innerHTML = "";
  document.getElementById("uangBayar").value = 0;
  renderCart();
}

// ============================================================
//  CHECKOUT (via backend, tersimpan ke database)
// ============================================================
async function prosesBayar() {
  const uangBayar = parseInt(document.getElementById("uangBayar").value) || 0;
  const namaPemesan = document.getElementById("namaPemesan").value.trim();
  const nomorMeja = document.getElementById("nomorMeja").value.trim();
  const alertArea = document.getElementById("alertArea");
  const receiptArea = document.getElementById("receiptArea");
  alertArea.innerHTML = "";
  receiptArea.innerHTML = "";

  const cartPayload = {};
  Object.entries(keranjang).forEach(([id, qty]) => {
    if (MENU_KOPI[id]) cartPayload[id] = qty;
  });

  if (Object.keys(cartPayload).length === 0) {
    alertArea.innerHTML = `<div class="alert alert-warning">Keranjang masih kosong, petualang!</div>`;
    return;
  }
  if (!namaPemesan) {
    alertArea.innerHTML = `<div class="alert alert-error">Mohon isi nama pemesan terlebih dahulu!</div>`;
    return;
  }
  if (!nomorMeja) {
    alertArea.innerHTML = `<div class="alert alert-error">Mohon isi nomor/nama meja terlebih dahulu!</div>`;
    return;
  }
  if (uangBayar === 0) {
    alertArea.innerHTML = `<div class="alert alert-error">Masukkan jumlah emas pembayaran dengan benar!</div>`;
    return;
  }

  const res = await fetch("/api/checkout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cart: cartPayload,
      uang_bayar: uangBayar,
      nama_pemesan: namaPemesan,
      meja: nomorMeja,
    }),
  });
  const data = await res.json();

  if (!data.success) {
    alertArea.innerHTML = `<div class="alert alert-error">${data.message}</div>`;
    return;
  }

  let struk = "========================================\n";
  struk += "              LOVE POEMS                \n";
  struk += "         - Coffee & High Poetry -       \n";
  struk += "========================================\n";
  struk += `Waktu Alam : ${data.waktu}\n`;
  struk += `No. Manuskrip: #${data.transaction_id}\n`;
  struk += `Nama Pemesan: ${data.nama_pemesan}\n`;
  struk += `Meja        : ${data.meja}\n`;
  struk += "----------------------------------------\n";

  data.items.forEach((it) => {
    struk += `${it.nama.padEnd(22)} x${String(it.qty).padEnd(3)} Rp${it.subtotal.toLocaleString("id-ID").padStart(10)}\n`;
  });

  struk += "----------------------------------------\n";
  struk += `Total Harga:                  Rp${data.total.toLocaleString("id-ID").padStart(10)}\n`;
  struk += `Pembayaran:                   Rp${data.uang_bayar.toLocaleString("id-ID").padStart(10)}\n`;
  struk += `Kembalian Kemakmuran:         Rp${data.kembalian.toLocaleString("id-ID").padStart(10)}\n`;
  struk += "----------------------------------------\n";
  struk += "      Terima Kasih Atas Kunjungan Anda  \n";
  struk += "   Semoga Harimu Dipenuhi Bait Indah    \n";
  struk += "========================================\n";

  alertArea.innerHTML = `<div class="alert alert-success">Manuskrip Pembayaran Berhasil Diselesaikan &amp; Tersimpan!</div>`;
  receiptArea.innerHTML = `<h3 class="section-title" style="margin-top:14px;">📄 Gulungan Struk Love Poems</h3><div class="receipt-box">${struk}</div>`;

  keranjang = {};
  document.getElementById("namaPemesan").value = "";
  document.getElementById("nomorMeja").value = "";
  renderCart();

  // Jika panel riwayat sedang terbuka, refresh datanya juga
  const riwayatPanel = document.getElementById("riwayatPanel");
  if (riwayatPanel.classList.contains("active")) {
    loadRiwayat();
  }
}

// ============================================================
//  RIWAYAT & REKAP PENDAPATAN (dari database terpisah riwayat.db)
// ============================================================
function toggleRiwayatPanel() {
  const panel = document.getElementById("riwayatPanel");
  panel.classList.toggle("active");
  if (panel.classList.contains("active")) {
    loadRiwayat();
  }
}

async function loadRiwayat() {
  await Promise.all([loadRekap(), loadRiwayatList()]);
}

async function loadRekap() {
  const res = await fetch("/api/riwayat/rekap");
  const data = await res.json();

  const rekapGrid = document.getElementById("rekapGrid");
  rekapGrid.innerHTML = `
    <div class="rekap-card">
      <div class="rekap-label">Pendapatan Hari Ini</div>
      <div class="rekap-value">${formatRupiah(data.pendapatan_hari_ini)}</div>
      <div class="rekap-sub">${data.jumlah_transaksi_hari_ini} transaksi</div>
    </div>
    <div class="rekap-card">
      <div class="rekap-label">Pendapatan Bulan Ini</div>
      <div class="rekap-value">${formatRupiah(data.pendapatan_bulan_ini)}</div>
      <div class="rekap-sub">${data.jumlah_transaksi_bulan_ini} transaksi</div>
    </div>
    <div class="rekap-card">
      <div class="rekap-label">Pendapatan Total</div>
      <div class="rekap-value">${formatRupiah(data.pendapatan_total)}</div>
      <div class="rekap-sub">${data.jumlah_transaksi_total} transaksi</div>
    </div>
  `;

  const rekapHarianArea = document.getElementById("rekapHarianArea");
  if (data.rekap_harian.length === 0) {
    rekapHarianArea.innerHTML = `<div class="empty-cart">Belum ada data harian.</div>`;
  } else {
    const rows = data.rekap_harian.map((r) => `
      <tr><td>${r.tanggal}</td><td>${r.jumlah}</td><td>${formatRupiah(r.pendapatan)}</td></tr>
    `).join("");
    rekapHarianArea.innerHTML = `
      <table>
        <thead><tr><th>Tanggal</th><th>Jumlah Transaksi</th><th>Pendapatan</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  const menuTerlarisArea = document.getElementById("menuTerlarisArea");
  if (data.menu_terlaris.length === 0) {
    menuTerlarisArea.innerHTML = `<div class="empty-cart">Belum ada data penjualan menu.</div>`;
  } else {
    const rows = data.menu_terlaris.map((m) => `
      <tr><td>${m.nama_menu}</td><td>${m.total_qty}</td><td>${formatRupiah(m.total_pendapatan)}</td></tr>
    `).join("");
    menuTerlarisArea.innerHTML = `
      <table>
        <thead><tr><th>Menu</th><th>Terjual</th><th>Pendapatan</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }
}

async function loadRiwayatList() {
  const res = await fetch("/api/transactions");
  const data = await res.json();
  const area = document.getElementById("riwayatListArea");

  if (data.length === 0) {
    area.innerHTML = `<div class="empty-cart">Belum ada riwayat transaksi.</div>`;
    return;
  }

  const rows = data.map((t) => {
    const daftarItem = t.items.map((i) => `${i.nama_menu} x${i.qty}`).join(", ");
    return `
      <tr>
        <td>#${t.id}</td>
        <td>${t.waktu}</td>
        <td>${t.nama_pemesan}</td>
        <td><span class="badge-meja">${t.meja}</span></td>
        <td>${daftarItem}</td>
        <td>${formatRupiah(t.total)}</td>
      </tr>`;
  }).join("");

  area.innerHTML = `
    <table>
      <thead><tr><th>No</th><th>Waktu</th><th>Pemesan</th><th>Meja</th><th>Item</th><th>Total</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}
