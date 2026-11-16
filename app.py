"""HalalChain Certification Network — Streamlit + Hardhat + MetaMask.

Jalankan:  streamlit run app.py
Struktur:  hc/ (logika & halaman) · components/metamask_bridge (jembatan MetaMask/ethers.js)
"""
import streamlit as st
from web3 import Web3

from hc import config, tx
from hc.chain import ChainError, get_chain, role_of, short
from hc.ctx import Ctx
from hc.pages import audit, dashboard, detail, issue, products, submit, verify
from hc.ui import esc, goto, inject_css, stretch
from hc.wallet import render_bridge

st.set_page_config(page_title="HalalChain | Certification Network", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
inject_css()

NAV = [
    ("Dashboard", ":material/dashboard:"),
    ("Pengajuan Produk", ":material/note_add:"),
    ("Daftar Produk", ":material/list_alt:"),
    ("Audit LPH", ":material/fact_check:"),
    ("Penerbitan BPJPH", ":material/verified:"),
    ("Lacak Sertifikat", ":material/qr_code_scanner:"),
]
ROUTES = {
    "Dashboard": dashboard.render,
    "Pengajuan Produk": submit.render,
    "Daftar Produk": products.render,
    "Detail Produk": detail.render,
    "Audit LPH": audit.render,
    "Penerbitan BPJPH": issue.render,
    "Lacak Sertifikat": verify.render,
}
LOGO = ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#173F31" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 3 4.5 6v5.5c0 4.4 3.1 8.1 7.5 9.5 4.4-1.4 7.5-5.1 7.5-9.5V6z"/><path d="m8.7 12.2 2.4 2.4 4.3-4.6"/></svg>')

# ---------------------------------------------------------------- state awal
st.session_state.setdefault("page", "Dashboard")
if "verify" in st.query_params and not st.session_state.get("_qp_done"):
    cert = st.query_params["verify"]
    st.session_state.update(page="Lacak Sertifikat", verify_input=cert, verify_active=cert, _qp_done=True)

# ---------------------------------------------------------------- blockchain
try:
    chain = get_chain()
except ChainError as exc:
    st.markdown(f'<div class="brand"><div class="brand-mark">{LOGO}</div><div><div class="brand-name" style="color:#173F31">HalalChain</div></div></div>', unsafe_allow_html=True)
    st.error(str(exc))
    st.code("npm install\nnpx hardhat compile\nnpx hardhat node                                      # terminal 1\nnpx hardhat run scripts/deploy.js --network localhost  # terminal 2", language="bash")
    st.stop()

# ---------------------------------------------------------------- sidebar
page = st.session_state["page"]
with st.sidebar:
    st.markdown(f'<div class="brand"><div class="brand-mark">{LOGO}</div><div><div class="brand-name">HalalChain</div>'
                f'<div class="brand-sub">CERTIFICATION NETWORK</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-title">Navigasi utama</div>', unsafe_allow_html=True)
    active_nav = "Daftar Produk" if page == "Detail Produk" else page
    for name, icon in NAV:
        st.button(name, key=f"nav_{name}", icon=icon, type="primary" if name == active_nav else "secondary",
                  on_click=goto, args=(name,), **stretch())

    st.divider()
    st.markdown('<div class="sb-title">Wallet &amp; akses</div>', unsafe_allow_html=True)
    wallet = render_bridge(tx.pending_action())

    raw = wallet.get("account")
    account = Web3.to_checksum_address(raw) if raw and Web3.is_address(raw) else None
    chain_ok = wallet.get("chainId") == config.CHAIN_ID
    role = role_of(chain, account)

    if account:
        try:
            bal = f'{Web3.from_wei(chain.w3.eth.get_balance(account), "ether"):,.4f} ETH'
        except Exception:
            bal = "Tidak tersedia"
        status_txt = "Terhubung" if chain_ok else "Jaringan salah"
        badge = f'<span class="role-badge">{esc(config.ROLE_LABEL[role].upper())}</span>'
        card = (f'<div class="wallet-card"><div class="wc-cap"><span>WALLET AKTIF · {status_txt.upper()}</span>{badge}</div>'
                f'<div class="wc-addr">{esc(account)}</div><div class="wc-bal">{esc(bal)}</div></div>')
    else:
        msg = {None: "Memeriksa…", False: "MetaMask tidak terdeteksi"}.get(wallet.get("installed"), "Belum terhubung")
        card = (f'<div class="wallet-card"><div class="wc-cap"><span>WALLET</span><span class="role-badge off">TANPA PERAN</span></div>'
                f'<div class="wc-addr">{msg}</div><div class="wc-bal" style="color:#C6DDCE;font-weight:500;font-size:.78rem">Verifikasi publik tetap dapat dipakai tanpa wallet.</div></div>')
    st.markdown(card, unsafe_allow_html=True)
    st.markdown(
        f'<div class="auth-row"><span>LPH</span><b>{esc(short(chain.lph, 7, 5))}</b></div>'
        f'<div class="auth-row"><span>BPJPH</span><b>{esc(short(chain.bpjph, 7, 5))}</b></div>'
        f'<div class="auth-row"><span>Jaringan</span><b>{config.CHAIN_NAME} · {config.CHAIN_ID}</b></div>',
        unsafe_allow_html=True,
    )
    st.caption("Peran ditentukan otomatis dari alamat wallet yang terdaftar di smart contract. Untuk berganti peran, ganti akun di MetaMask.")

ctx = Ctx(chain=chain, wallet=wallet, account=account, role=role, chain_ok=chain_ok, page=page)

# ---------------------------------------------------------------- konten
tx.consume_result(ctx)
tx.render_panel(ctx)
ROUTES.get(page, dashboard.render)(ctx)

st.markdown(
    f'<div style="border-top:1px solid {"#E4E1D3"};margin-top:34px;padding-top:14px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;">'
    f'<span style="color:#76817A;font-size:.74rem">HalalChain · Certification Network</span>'
    f'<span style="color:#76817A;font-size:.74rem">ERC-721 · {config.CHAIN_NAME} · Chain ID {config.CHAIN_ID}</span></div>',
    unsafe_allow_html=True,
)
