import streamlit as st

from .. import config
from ..chain import fmt_time, find_token, get_events, list_products, read_product, short
from ..qr import cert_from_payload, decode_qr, make_qr_png, verify_url
from ..ui import card, chip, esc, page_heading, rows, stretch
from .detail import document_checker


def _check(ok, text):
    cls, mark = {True: ("y", "✓"), False: ("n", "✕"), None: ("w", "!")}[ok]
    return f'<div class="check"><span class="ck {cls}">{mark}</span><span>{text}</span></div>'


def _verdict(p, found: bool, query: str):
    if not found:
        return "bad", "✕", "Sertifikat tidak ditemukan", f"Tidak ada catatan on-chain untuk “{esc(query)}”. Periksa penulisan nomor atau pindai ulang QR Code. Nomor yang tidak terdaftar di blockchain tidak dapat dianggap sah."
    s = p["status"]
    if s == config.AKTIF:
        return "ok", "✓", "Sertifikat halal VALID", "Data cocok dengan catatan blockchain dan sertifikat masih berlaku."
    if s == config.KEDALUWARSA:
        return "warn", "⌛", "Sertifikat KEDALUWARSA", f'Sertifikat pernah diterbitkan namun masa berlakunya berakhir pada {esc(fmt_time(p["berlaku_sampai"], False))}. Tidak dapat dianggap valid.'
    if s == config.GAGAL_AUDIT:
        return "bad", "✕", "TIDAK VALID — produk gagal audit", "Produk tidak lulus audit LPH. Tidak ada sertifikat halal untuk produk ini."
    return "info", "◔", "Belum ada sertifikat", "Produk terdaftar, tetapi sertifikat halal belum diterbitkan. Belum dapat dianggap bersertifikat halal."


def show_result(chain, query: str, key_prefix="search"):
    tid = find_token(chain, query)
    p = read_product(chain, tid) if tid else None
    tone, icon, title, sub = _verdict(p, bool(p), query)
    st.markdown(f'<div class="verdict {tone}"><div class="vi">{icon}</div><div><div class="vt">{title}</div><div class="vs">{sub}</div></div></div>', unsafe_allow_html=True)
    if not p:
        return
    issue_ev = next((e for e in get_events(chain, tid) if e["kind"] == "SertifikatDiterbitkan"), None)
    by_cert = p["id_ketetapan"] and p["id_ketetapan"] == query.strip()
    checks = [
        _check(True, f'Data ditemukan di smart contract <span class="mono">{esc(short(chain.address, 8, 6))}</span> (Chain ID {config.CHAIN_ID})'),
        _check(True if by_cert else None,
               "Nomor sertifikat cocok dengan catatan on-chain" if by_cert else "Pencarian bukan melalui nomor sertifikat (ID registrasi / Token ID)"),
        _check(p["status"] == config.AKTIF, f'Status on-chain: <b>{esc(config.STATUS[p["status"]][0])}</b>'),
    ]
    if p["tgl_terbit"]:
        checks.append(_check(p["status"] != config.KEDALUWARSA, f'Masa berlaku sampai <b>{esc(fmt_time(p["berlaku_sampai"], False))}</b>'))
        ok_issuer = bool(issue_ev) and issue_ev["actor"] == chain.bpjph
        checks.append(_check(ok_issuer, "Diterbitkan oleh wallet BPJPH resmi yang terdaftar di kontrak"))
    checks.append(_check(True, f'Pemilik NFT ERC-721: <span class="mono">{esc(short(p["owner"], 10, 8))}</span>'))

    a, b = st.columns([1, 1])
    with a:
        st.markdown(card("Validasi dari blockchain", "", "".join(checks)), unsafe_allow_html=True)
        st.markdown(card("Informasi produk", "", rows([
            ("Nama produk", p["nama"]), ("Produsen", p["produsen"]), ("Kategori", p["kategori"]), ("ID registrasi", p["id_registrasi"]),
            ("Status", chip(p["status"])),
        ])), unsafe_allow_html=True)
    with b:
        st.markdown(card("Informasi penerbitan", "", rows([
            ("Nomor sertifikat", p["id_ketetapan"] or "Belum diterbitkan"), ("Tanggal terbit", fmt_time(p["tgl_terbit"])),
            ("Berlaku sampai", fmt_time(p["berlaku_sampai"], False)),
            ("Diterbitkan oleh", issue_ev["actor"] if issue_ev else "-"),
            ("Block penerbitan", f'#{issue_ev["block"]}' if issue_ev else "-"),
            ("Transaction hash", issue_ev["tx_hash"] if issue_ev else "-"), ("Hash dokumen", p["hash_dokumen"]),
        ], mono=("Diterbitkan oleh", "Transaction hash", "Hash dokumen"))), unsafe_allow_html=True)
        st.write("")
        document_checker(p, key=f'verify_doc_{key_prefix}_{p["token_id"]}')


def _use(cert: str):
    st.session_state["verify_input"] = cert
    st.session_state["verify_active"] = cert


def render(ctx):
    page_heading("VERIFIKASI PUBLIK", "Lacak & verifikasi sertifikat halal",
                 "Dapat digunakan siapa saja tanpa wallet. Seluruh data dibaca langsung dari smart contract, bukan dari basis data aplikasi.")
    chain = ctx.chain
    tab_search, tab_qr = st.tabs(["Cari nomor sertifikat", "Pindai QR Code"])

    with tab_search:
        with st.form("verify_form"):
            c1, c2 = st.columns([4, 1.2])
            q = c1.text_input("Nomor sertifikat", key="verify_input", placeholder="Contoh: HC-2026-0001 (atau ID registrasi REG-001)")
            c2.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            go = c2.form_submit_button("Verifikasi", type="primary", icon=":material/search:", **stretch())
        if go:
            st.session_state["verify_active"] = q.strip()
            if not q.strip():
                st.session_state["verify_active"] = ""
                st.warning("Masukkan nomor sertifikat terlebih dahulu.")
        active = st.session_state.get("verify_active")
        if active:
            show_result(chain, active)

        st.write("")
        recent = sorted([p for p in list_products(chain) if p["tgl_terbit"]], key=lambda p: p["tgl_terbit"], reverse=True)[:5]
        if recent:
            st.markdown('<div class="sec-h">Sertifikat yang baru diterbitkan</div><div class="sec-s">Klik untuk memverifikasi langsung dari blockchain.</div>', unsafe_allow_html=True)
            for p in recent:
                c = st.columns([2.2, 1.6, 1.3, 1])
                c[0].markdown(f'<div class="tcell"><b>{esc(p["nama"])}</b></div>', unsafe_allow_html=True)
                c[1].markdown(f'<div class="tcell mono">{esc(p["id_ketetapan"])}</div>', unsafe_allow_html=True)
                c[2].markdown(f'<div class="tcell">{chip(p["status"])}</div>', unsafe_allow_html=True)
                c[3].button("Verifikasi", key=f'vr_{p["token_id"]}', on_click=_use, args=(p["id_ketetapan"],), **stretch())

    with tab_qr:
        st.caption("Pindai QR Code pada kemasan/sertifikat menggunakan kamera, atau unggah gambar QR Code.")
        cam = st.camera_input("Arahkan kamera ke QR Code", key="qr_cam")
        up = st.file_uploader("…atau unggah gambar QR Code", type=["png", "jpg", "jpeg"], key="qr_upload")
        src = cam or up
        if src is not None:
            try:
                payload = decode_qr(src.getvalue())
            except RuntimeError as exc:
                st.error(str(exc))
                payload = None
            else:
                if not payload:
                    st.error("QR Code tidak terbaca. Pastikan gambar jelas, cukup terang, dan QR Code terlihat penuh.")
            if payload:
                cert = cert_from_payload(payload)
                st.success(f"QR Code terbaca: {cert}")
                show_result(chain, cert)

