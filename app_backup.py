import base64
import json
import time
from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu
from web3 import Web3

# ==========================================
# 1. PAGE CONFIG
# ==========================================
st.set_page_config(page_title="HalalChain - Certification Portal", page_icon="🛡️", layout="wide")

# Design tokens
BG = "#0f172a"
CARD = "#1e293b"
BORDER = "#334155"
TEXT = "#f1f5f9"
MUTED = "#94a3b8"
ACCENT = "#10b981"

st.markdown(
    f"""
<style>
/* ---------- Base: semua permukaan gelap ---------- */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: {BG} !important;
    color: {TEXT} !important;
    color-scheme: dark;
}}
[data-testid="stHeader"], [data-testid="stToolbar"] {{ background: transparent !important; }}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
    background: {CARD} !important;
    border-right: 1px solid {BORDER};
}}
.block-container {{ padding-top: 2rem; max-width: 1200px; }}

/* ---------- Teks ---------- */
h1, h2, h3, h4, h5, h6, p, span, label, li, div,
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] p {{ color: {TEXT}; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p, small {{ color: {MUTED} !important; }}
code {{ background: {BG} !important; color: {ACCENT} !important; border: 1px solid {BORDER}; border-radius: 6px; }}
hr {{ border-color: {BORDER} !important; }}

/* ---------- Input, textarea, select, number ---------- */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
[data-baseweb="select"] > div, [data-testid="stNumberInput"] > div > div {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
}}
[data-baseweb="input"] input, [data-baseweb="base-input"] input, textarea,
[data-baseweb="select"] div, [data-baseweb="select"] span {{
    background: transparent !important;
    color: {TEXT} !important;
    -webkit-text-fill-color: {TEXT} !important;
}}
input::placeholder, textarea::placeholder {{ color: #64748b !important; -webkit-text-fill-color: #64748b !important; }}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within,
[data-baseweb="select"] > div:focus-within {{ border-color: {ACCENT} !important; box-shadow: 0 0 0 1px {ACCENT}; }}
[data-testid="stNumberInput"] button {{ background: {CARD} !important; color: {TEXT} !important; border-color: {BORDER} !important; }}
[data-baseweb="select"] svg, [data-testid="stNumberInput"] svg {{ fill: {MUTED} !important; }}

/* Dropdown list */
[data-baseweb="popover"], [data-baseweb="popover"] > div, [data-baseweb="menu"], ul[role="listbox"] {{
    background: {CARD} !important; border: 1px solid {BORDER}; border-radius: 10px;
}}
li[role="option"] {{ background: {CARD} !important; color: {TEXT} !important; }}
li[role="option"]:hover, li[aria-selected="true"] {{ background: {BORDER} !important; }}

/* Radio & checkbox */
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label {{ color: {TEXT} !important; }}

/* ---------- Tombol ---------- */
.stButton > button, [data-testid="stBaseButton-secondary"] {{
    background: {CARD} !important; color: {TEXT} !important;
    border: 1px solid {BORDER} !important; border-radius: 10px !important; font-weight: 600;
}}
.stButton > button:hover {{ border-color: {ACCENT} !important; color: {ACCENT} !important; }}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] {{
    background: {ACCENT} !important; color: #04271b !important; border: 1px solid {ACCENT} !important;
}}
.stButton > button[kind="primary"]:hover {{ background: #34d399 !important; color: #04271b !important; }}

/* ---------- Container bercard ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD} !important; border: 1px solid {BORDER} !important;
    border-radius: 16px !important; padding: 12px !important;
}}

/* ---------- Alert ---------- */
[data-testid="stAlert"] {{ border-radius: 12px; border: 1px solid {BORDER}; }}
[data-testid="stAlert"] p {{ color: {TEXT} !important; }}

/* ---------- Navbar (iframe option_menu) ---------- */
iframe[title="streamlit_option_menu.option_menu"] {{ background: transparent !important; border: 0; color-scheme: dark; }}

/* ---------- Komponen custom ---------- */
.header-card {{
    background: linear-gradient(135deg, #064e3b 0%, #065f46 55%, #047857 100%);
    border: 1px solid #059669; border-radius: 16px; padding: 24px 28px; margin-bottom: 18px;
}}
.header-card h2 {{ margin: 0; font-weight: 800; color: #ecfdf5; }}
.header-card p {{ margin: 6px 0 0; color: #a7f3d0; font-size: .95rem; }}
.metric-card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 16px 18px; }}
.metric-label {{ color: {MUTED}; font-size: .8rem; margin-bottom: 4px; }}
.metric-value {{ color: {TEXT}; font-size: 1.5rem; font-weight: 700; font-family: ui-monospace, monospace; }}
.metric-value.accent {{ color: {ACCENT}; }}
.badge {{ display:inline-block; padding: 3px 12px; border-radius: 999px; font-size: .8rem; font-weight: 700; border: 1px solid; }}
.badge.ok {{ color:{ACCENT}; border-color:{ACCENT}; background: rgba(16,185,129,.12); }}
.badge.warn {{ color:#fbbf24; border-color:#fbbf24; background: rgba(251,191,36,.12); }}
.badge.bad {{ color:#f87171; border-color:#f87171; background: rgba(248,113,113,.12); }}
.badge.info {{ color:#60a5fa; border-color:#60a5fa; background: rgba(96,165,250,.12); }}
.denied {{
    background: rgba(239,68,68,.10); border: 1px solid #ef4444; border-radius: 14px;
    padding: 18px 22px; color: #fecaca;
}}
.denied b {{ color: #fca5a5; font-size: 1.05rem; }}
.kv {{ display:flex; justify-content:space-between; gap:16px; padding: 9px 0; border-bottom: 1px solid {BORDER}; }}
.kv:last-child {{ border-bottom: 0; }}
.kv span:first-child {{ color: {MUTED}; }}
.kv span:last-child {{ color: {TEXT}; font-weight: 600; text-align: right; word-break: break-all; }}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. BLOCKCHAIN & CONTRACT
# ==========================================
RPC_URL = "http://127.0.0.1:8545"
PROJECT_DIR = Path(__file__).parent
DEPLOYMENT_PATH = PROJECT_DIR / "deployment.json"
ARTIFACT_PATH = PROJECT_DIR / "artifacts" / "contracts" / "HalalChain.sol" / "HalalChain.json"

# Wallet resmi (Hardhat default)
ADDRESS_LPH = Web3.to_checksum_address("0x70997970C51812dc3A010C7d01b50e0d17dc79C8")    # Account #1
ADDRESS_BPJPH = Web3.to_checksum_address("0x3C44CdDDb6a900fa2b585dd299e03d12FA4293BC")  # Account #2

STATUS_LABEL = {
    0: ("Diajukan", "info"),
    1: ("Lolos Audit LPH", "warn"),
    2: ("Gagal Audit", "bad"),
    3: ("Sertifikat Aktif", "ok"),
}

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected() or not DEPLOYMENT_PATH.exists() or not ARTIFACT_PATH.exists():
    st.error("Node Hardhat atau file deployment tidak ditemukan. Jalankan `npx hardhat node` lalu script deploy.")
    st.stop()

CONTRACT_ADDRESS = Web3.to_checksum_address(json.loads(DEPLOYMENT_PATH.read_text())["address"])
CONTRACT_ABI = json.loads(ARTIFACT_PATH.read_text())["abi"]
halal = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
ACCOUNTS = [Web3.to_checksum_address(a) for a in w3.eth.accounts]


def short(addr: str, a: int = 8, b: int = 6) -> str:
    return f"{addr[:a]}...{addr[-b:]}"


def send_tx(fn, sender: str):
    """Kirim transaksi dari akun Hardhat (unlocked). Return (receipt, error)."""
    try:
        tx_hash = fn.transact({"from": sender})
        return w3.eth.wait_for_transaction_receipt(tx_hash), None
    except Exception as e:  # revert reason ada di pesan exception
        msg = str(e)
        for key in ("revert", "reverted with reason string"):
            if key in msg:
                msg = msg.split(key, 1)[-1].strip(" :'\"")
                break
        return None, msg


def metric_card(label: str, value: str, accent: bool = False) -> str:
    cls = "metric-value accent" if accent else "metric-value"
    return f'<div class="metric-card"><div class="metric-label">{label}</div><div class="{cls}">{value}</div></div>'


def denied(role: str, required: str):
    st.markdown(
        f"""<div class="denied"><b>⛔ Akses Ditolak / Unauthorized Access</b><br>
        Wallet aktif <code>{short(active_address, 10, 6)}</code> bukan wallet resmi {role}.<br>
        Ganti akun di sidebar ke <b>{required}</b> untuk melanjutkan.</div>""",
        unsafe_allow_html=True,
    )


# ==========================================
# 3. HEADER & STATUS CARDS
# ==========================================
st.markdown(
    """<div class="header-card"><h2>🛡️ HalalChain Certification Network</h2>
    <p>Platform traceability & sertifikasi halal berbasis blockchain ERC-721 (Hardhat Node)</p></div>""",
    unsafe_allow_html=True,
)
m1, m2, m3 = st.columns(3)
m1.markdown(metric_card("Chain ID", str(w3.eth.chain_id)), unsafe_allow_html=True)
m2.markdown(metric_card("Block terbaru", f"#{w3.eth.block_number}"), unsafe_allow_html=True)
m3.markdown(metric_card("Smart contract", short(CONTRACT_ADDRESS), accent=True), unsafe_allow_html=True)
st.write("")

# ==========================================
# 4. SIDEBAR: WALLET & RBAC
# ==========================================
with st.sidebar:
    st.subheader("🔑 Wallet aktif")
    st.caption("Pilih akun untuk menandatangani transaksi.")

    CUSTOM = "Pengusaha - alamat custom"
    options = {
        "Pengusaha A (Account #0)": ACCOUNTS[0],
        "Pengusaha B (Account #3)": ACCOUNTS[3],
        "Pengusaha C (Account #4)": ACCOUNTS[4],
        "LPH Verifikator (Account #1)": ADDRESS_LPH,
        "BPJPH Otoritas (Account #2)": ADDRESS_BPJPH,
        CUSTOM: None,
    }
    role_label = st.selectbox("Peran wallet", list(options.keys()))

    if role_label == CUSTOM:
        custom_addr = st.text_input("Alamat wallet", placeholder="0x...")
        if custom_addr and Web3.is_address(custom_addr):
            active_address = Web3.to_checksum_address(custom_addr)
        else:
            active_address = ACCOUNTS[0]
            if custom_addr:
                st.error("Format alamat tidak valid. Memakai Account #0.")
    else:
        active_address = Web3.to_checksum_address(options[role_label])

    st.markdown(f"**Alamat aktif**<br><code>{active_address}</code>", unsafe_allow_html=True)
    try:
        st.markdown(f"**Saldo:** {w3.from_wei(w3.eth.get_balance(active_address), 'ether'):,.2f} ETH")
    except Exception:
        pass

    st.divider()
    st.caption("🔒 Otoritas resmi")
    st.caption(f"LPH: `{short(ADDRESS_LPH, 8, 4)}`")
    st.caption(f"BPJPH: `{short(ADDRESS_BPJPH, 8, 4)}`")

# ==========================================
# 5. NAVBAR
# ==========================================
selected_tab = option_menu(
    menu_title=None,
    options=["Pengajuan Produk", "Audit LPH", "Penerbitan BPJPH", "Lacak Sertifikat"],
    icons=["box-seam", "clipboard-check", "award", "search"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "6px", "background-color": CARD, "border": f"1px solid {BORDER}", "border-radius": "14px", "max-width": "100%"},
        "icon": {"color": ACCENT, "font-size": "16px"},
        "nav-link": {"font-size": "14px", "font-weight": "600", "color": MUTED, "border-radius": "10px",
                     "padding": "10px 14px", "--hover-color": BORDER, "text-align": "center"},
        "nav-link-selected": {"background-color": "rgba(16,185,129,.15)", "color": ACCENT, "border": f"1px solid {ACCENT}"},
    },
)
st.write("")

# ==========================================
# 6. TABS
# ==========================================

# ---------- TAB 1: PENGAJUAN (publik / pengusaha) ----------
if selected_tab == "Pengajuan Produk":
    st.markdown("### 📝 Registrasi produk halal baru")
    st.caption("Akun pengusaha mana pun dapat mengajukan. NFT sertifikat langsung dicetak ke wallet pemohon.")

    if active_address in (ADDRESS_LPH, ADDRESS_BPJPH):
        st.warning("Wallet aktif adalah wallet otoritas. Ganti ke wallet Pengusaha untuk mendaftar.")

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            nama_produk = st.text_input("Nama produk", placeholder="Contoh: Kopi Susu Aren Premium")
            kategori = st.selectbox("Kategori produk", ["Makanan & Minuman", "Kosmetik", "Farmasi", "Barang Gunaan"])
            dok_lengkap = st.checkbox("Dokumen persyaratan sudah lengkap")
        with c2:
            wallet_pemohon = st.text_input("Alamat wallet pemohon", value=active_address)
            bahan = st.text_area("Daftar bahan & komposisi", placeholder="1. Biji Kopi Arabika\n2. Susu UHT\n3. Gula Aren", height=130)

        if st.button("🚀 Kirim pengajuan", type="primary"):
            if not (nama_produk and bahan and wallet_pemohon):
                st.error("Lengkapi nama produk, bahan, dan alamat wallet.")
            elif not Web3.is_address(wallet_pemohon):
                st.error("Alamat wallet tidak valid.")
            elif Web3.to_checksum_address(wallet_pemohon) not in ACCOUNTS:
                st.error("Alamat ini tidak dikenal node Hardhat sehingga tidak bisa menandatangani. Pakai salah satu akun Hardhat.")
            else:
                meta = {"name": nama_produk, "category": kategori, "ingredients": bahan.splitlines()}
                uri = "data:application/json;base64," + base64.b64encode(json.dumps(meta).encode()).decode()
                with st.spinner("Menunggu konfirmasi blok..."):
                    receipt, err = send_tx(
                        halal.functions.registrasiHalal(nama_produk, "Ya" if dok_lengkap else "Tidak", uri),
                        Web3.to_checksum_address(wallet_pemohon),
                    )
                if err:
                    st.error(f"Transaksi gagal: {err}")
                else:
                    ev = halal.events.RegistrasiBerhasil().process_receipt(receipt)
                    tid = ev[0]["args"]["tokenId"] if ev else "?"
                    st.success(f"Produk **{nama_produk}** terdaftar dengan Token ID **#{tid}**.")
                    st.caption(f"Tx: `{receipt['transactionHash'].hex()}`")

# ---------- TAB 2: AUDIT LPH ----------
elif selected_tab == "Audit LPH":
    st.markdown("### 🔬 Audit & inspeksi LPH")
    st.caption("Hanya dapat dijalankan oleh wallet resmi LPH Verifikator.")

    if active_address != ADDRESS_LPH:
        denied("LPH Verifikator", "LPH Verifikator (Account #1)")
    else:
        with st.container(border=True):
            st.success(f"Terautentikasi sebagai LPH Verifikator `{short(ADDRESS_LPH, 10, 6)}`")
            a1, a2 = st.columns(2)
            with a1:
                token_id = st.number_input("Token ID pengajuan", min_value=1, value=1, step=1)
                hasil = st.radio("Hasil inspeksi", ["Memenuhi syarat (Halal)", "Tidak memenuhi syarat"])
            with a2:
                st.text_area("Catatan audit (opsional, tidak disimpan on-chain)", placeholder="Bahan baku bersih dan bebas kontaminasi najis...", height=130)

            if st.button("💾 Simpan hasil audit", type="primary"):
                lolos = hasil.startswith("Memenuhi")
                status_bahan, fas = ("Halal", "Ya") if lolos else ("Tidak Halal", "Tidak")
                with st.spinner("Menunggu konfirmasi blok..."):
                    receipt, err = send_tx(
                        halal.functions.pemeriksaanLPH(int(token_id), status_bahan, fas), ADDRESS_LPH
                    )
                if lolos:
                    st.error(f"Transaksi gagal: {err}") if err else st.success(f"Token #{token_id} dinyatakan lolos audit.")
                else:
                    st.warning(
                        f"Token #{token_id} dinyatakan tidak lolos. Kontrak me-revert transaksi ini, "
                        "jadi status gagal tidak tersimpan on-chain (lihat catatan di balasan)."
                    )

# ---------- TAB 3: PENERBITAN BPJPH ----------
elif selected_tab == "Penerbitan BPJPH":
    st.markdown("### 📜 Penerbitan sertifikat BPJPH")
    st.caption("Hanya dapat dijalankan oleh wallet resmi BPJPH. Produk harus sudah lolos audit LPH.")

    if active_address != ADDRESS_BPJPH:
        denied("BPJPH", "BPJPH Otoritas (Account #2)")
    else:
        with st.container(border=True):
            st.success(f"Terautentikasi sebagai Otoritas BPJPH `{short(ADDRESS_BPJPH, 10, 6)}`")
            b1, b2 = st.columns(2)
            with b1:
                tid = st.number_input("Token ID siap terbit", min_value=1, value=1, step=1)
            with b2:
                id_ket = st.text_input("ID ketetapan", value=f"KET-{int(time.time())}")
            st.info("Penerbitan mengaktifkan sertifikat pada NFT yang sudah dimiliki pemohon.")

            if st.button("✨ Terbitkan sertifikat halal", type="primary"):
                with st.spinner("Menunggu konfirmasi blok..."):
                    receipt, err = send_tx(halal.functions.terbitSertifikat(int(tid), id_ket), ADDRESS_BPJPH)
                if err:
                    st.error(f"Transaksi gagal: {err}")
                else:
                    st.balloons()
                    st.success(f"Sertifikat Token ID #{tid} diterbitkan dengan ID ketetapan `{id_ket}`.")

# ---------- TAB 4: LACAK (publik) ----------
elif selected_tab == "Lacak Sertifikat":
    st.markdown("### 🔍 Lacak sertifikat halal")
    st.caption("Terbuka untuk publik. Data dibaca langsung dari smart contract.")

    s1, s2 = st.columns([3, 1])
    with s1:
        query = st.number_input("Token ID", min_value=1, value=1, step=1, label_visibility="collapsed")
    with s2:
        st.button("🔍 Cari sertifikat", use_container_width=True)

    try:
        data = halal.functions.sertifikasiList(int(query)).call()
        # (tokenId, idRegistrasi, namaProduk, statusBahan, fasSesuai, idKetetapan, status, timestamp)
        if data[0] == 0:
            raise ValueError("kosong")
        owner = halal.functions.getBatchOwner(int(query)).call()
        label, tone = STATUS_LABEL.get(data[6], ("Tidak diketahui", "warn"))
        tanggal = time.strftime("%d %b %Y %H:%M", time.localtime(data[7]))

        with st.container(border=True):
            st.subheader(f"Sertifikat Halal #{data[0]}")
            st.markdown(f'<span class="badge {tone}">{label}</span>', unsafe_allow_html=True)
            st.write("")
            k1, k2 = st.columns(2)
            k1.markdown(
                f"""<div class="kv"><span>Nama produk</span><span>{data[2]}</span></div>
                <div class="kv"><span>ID registrasi</span><span>{data[1]}</span></div>
                <div class="kv"><span>Status bahan</span><span>{data[3] or '-'}</span></div>
                <div class="kv"><span>Fasilitas sesuai</span><span>{data[4] or '-'}</span></div>""",
                unsafe_allow_html=True,
            )
            k2.markdown(
                f"""<div class="kv"><span>ID ketetapan</span><span>{data[5] or '-'}</span></div>
                <div class="kv"><span>Pemilik NFT</span><span><code>{short(owner, 10, 6)}</code></span></div>
                <div class="kv"><span>Diajukan</span><span>{tanggal}</span></div>
                <div class="kv"><span>Standar token</span><span>ERC-721</span></div>""",
                unsafe_allow_html=True,
            )
    except Exception:
        st.info(f"Token ID #{int(query)} belum terdaftar di blockchain.")