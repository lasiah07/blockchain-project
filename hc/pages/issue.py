import re
from datetime import datetime

import streamlit as st

from .. import config, tx
from ..chain import fmt_time, list_products
from ..ctx import gate
from ..ui import card, esc, goto, notice, page_heading, rows, stretch

DECREE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9/._-]{2,63}$")


def render(ctx):
    page_heading("PENERBITAN SERTIFIKAT", "Penerbitan sertifikat BPJPH",
                 "Terbitkan sertifikat untuk produk yang telah lolos audit LPH. Sertifikat berlaku 365 hari sejak diterbitkan.")
    if not gate(ctx, ("BPJPH",), "BPJPH"):
        return
    notice("Akses terverifikasi: wallet aktif adalah <b>BPJPH resmi</b> yang terdaftar di smart contract.", "ok")

    ready = sorted([p for p in list_products(ctx.chain) if p["status"] == config.LOLOS_AUDIT], key=lambda p: p["token_id"])
    if not ready:
        st.info("Belum ada produk yang lolos audit dan menunggu penerbitan.")
        return
    labels = {f'#{p["token_id"]} · {p["nama"]} — {p["produsen"]}': p for p in ready}
    p = labels[st.selectbox(f"Produk lolos audit ({len(ready)})", list(labels), key="issue_pick")]
    tid = p["token_id"]

    l, r = st.columns(2)
    l.markdown(card("Detail produk", "", rows([
        ("ID registrasi", p["id_registrasi"]), ("Nama produk", p["nama"]), ("Produsen", p["produsen"]),
        ("Kategori", p["kategori"]), ("Pemilik NFT", p["owner"]), ("Hash dokumen", p["hash_dokumen"]),
    ], mono=("Pemilik NFT", "Hash dokumen"))), unsafe_allow_html=True)
    r.markdown(card("Hasil audit LPH", "Dicatat on-chain", rows([
        ("Kehalalan bahan", p["status_bahan"]), ("Kesesuaian fasilitas", "Sesuai" if p["fas_sesuai"] == "Ya" else p["fas_sesuai"]),
        ("Tanggal audit", fmt_time(p["tgl_audit"])), ("Status", "Lolos audit"),
    ])), unsafe_allow_html=True)
    st.button("Lihat detail lengkap", key=f"issue_detail_{tid}", icon=":material/open_in_new:",
              on_click=goto, args=("Detail Produk",), kwargs={"detail_token": tid})

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="sec-h">Ketetapan sertifikat</div><div class="sec-s">Nomor harus unik; 3–64 karakter (huruf, angka, / . _ -).</div>', unsafe_allow_html=True)
        decree = st.text_input("Nomor ketetapan sertifikat *", value=f"HC-{datetime.now().year}-{tid:04d}", key=f"issue_decree_{tid}", max_chars=64).strip()
        go = st.button("Terbitkan sertifikat halal", type="primary", key=f"issue_go_{tid}", icon=":material/verified:", **stretch())

    if not go:
        return
    if not DECREE_RE.match(decree):
        st.error("Nomor ketetapan tidak valid. Gunakan 3–64 karakter: huruf, angka, / . _ - (tanpa spasi).")
        return
    if ctx.chain.contract.functions.cariByKetetapan(decree).call() != 0:
        st.error(f"Nomor ketetapan “{decree}” sudah digunakan sertifikat lain. Gunakan nomor yang berbeda.")
        return
    fn = ctx.chain.contract.functions.terbitSertifikat(tid, decree)
    tx.begin(ctx, "Terbitkan sertifikat halal", fn, [
        ("Produk", f'#{tid} · {p["nama"]}'), ("Pemilik NFT", p["owner"]), ("Nomor ketetapan", decree), ("Masa berlaku", "365 hari"),
    ], kind="terbit")
    st.rerun()
