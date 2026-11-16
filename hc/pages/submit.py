import hashlib

import streamlit as st

from .. import config, tx
from ..chain import build_metadata_uri, is_hash
from ..ctx import gate
from ..ui import page_heading, stretch

MAX_FILE_MB = 10


def render(ctx):
    page_heading("REGISTRASI PRODUK", "Ajukan sertifikasi halal",
                 "Daftarkan produk Anda. Pengajuan dicatat on-chain dan menghasilkan NFT sertifikat (ERC-721) atas nama wallet Anda.")
    if not gate(ctx, ("PENGUSAHA",), "Pengusaha"):
        return

    n = st.session_state.get("form_nonce", 0)
    key = lambda name: f"{name}_{n}"

    with st.container(border=True):
        st.markdown('<div class="sec-h">Informasi produk</div><div class="sec-s">Semua kolom bertanda * wajib diisi.</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        nama = c1.text_input("Nama produk *", key=key("f_nama"), max_chars=120, placeholder="Contoh: Kopi Susu Aren Premium")
        produsen = c2.text_input("Nama produsen *", key=key("f_produsen"), max_chars=120, placeholder="Contoh: PT Kopi Nusantara")
        kategori = c1.selectbox("Kategori produk *", config.CATEGORIES, key=key("f_kategori"))
        c2.text_input("Wallet pemohon", value=ctx.account, disabled=True, key=key("f_wallet"))
        bahan = st.text_area("Daftar bahan / komposisi * (satu bahan per baris)", key=key("f_bahan"), height=140,
                             placeholder="Biji Kopi Arabika\nSusu UHT\nGula Aren")

        st.markdown('<div class="sec-h" style="margin-top:8px">Dokumen pendukung</div>'
                    '<div class="sec-s">Hanya hash SHA-256 dokumen yang disimpan on-chain. Berkas aslinya tidak diunggah ke blockchain.</div>',
                    unsafe_allow_html=True)
        mode = st.radio("Sumber hash dokumen", ["Unggah dokumen", "Masukkan hash manual"], horizontal=True, key=key("f_mode"))
        doc_hash, doc_name, file_error = "", "", None
        if mode == "Unggah dokumen":
            up = st.file_uploader("Dokumen persyaratan (PDF/gambar/Word)", type=["pdf", "png", "jpg", "jpeg", "doc", "docx"], key=key("f_file"))
            if up is not None:
                data = up.getvalue()
                if len(data) > MAX_FILE_MB * 1024 * 1024:
                    file_error = f"Ukuran berkas melebihi {MAX_FILE_MB} MB."
                elif len(data) == 0:
                    file_error = "Berkas kosong."
                else:
                    doc_hash, doc_name = "0x" + hashlib.sha256(data).hexdigest(), up.name
                    st.caption("Hash SHA-256 dokumen (dihitung di aplikasi):")
                    st.code(doc_hash, language=None)
        else:
            doc_hash = st.text_input("Hash dokumen (0x + 64 karakter heksadesimal) *", key=key("f_hash"), placeholder="0x…").strip()
            doc_name = "hash manual"
        go = st.button("Kirim pengajuan produk", type="primary", key=key("f_submit"), icon=":material/send:", **stretch())

    if not go:
        return
    errors = []
    if len(nama.strip()) < 3:
        errors.append("Nama produk minimal 3 karakter.")
    if len(produsen.strip()) < 3:
        errors.append("Nama produsen minimal 3 karakter.")
    items = [x.strip() for x in bahan.splitlines() if x.strip()]
    if not items:
        errors.append("Daftar bahan wajib diisi (minimal satu bahan).")
    elif len(items) > 60 or any(len(x) > 120 for x in items):
        errors.append("Daftar bahan terlalu panjang (maksimal 60 bahan, 120 karakter per bahan).")
    if file_error:
        errors.append(file_error)
    elif not doc_hash:
        errors.append("Unggah dokumen atau isi hash dokumen.")
    elif not is_hash(doc_hash):
        errors.append("Format hash dokumen tidak valid (harus 0x diikuti 64 karakter heksadesimal, bukan nol).")
    if errors:
        for e in errors:
            st.error(e)
        return

    meta = {"name": nama.strip(), "producer": produsen.strip(), "category": kategori, "ingredients": items,
            "documentName": doc_name, "documentHash": doc_hash.lower()}
    fn = ctx.chain.contract.functions.registrasiHalal(
        nama.strip(), produsen.strip(), kategori, bytes.fromhex(doc_hash[2:]), build_metadata_uri(meta)
    )
    tx.begin(ctx, "Registrasi produk halal", fn, [
        ("Nama produk", nama.strip()), ("Produsen", produsen.strip()), ("Kategori", kategori),
        ("Jumlah bahan", str(len(items))), ("Hash dokumen", doc_hash.lower()),
    ], kind="registrasi")
    st.rerun()
