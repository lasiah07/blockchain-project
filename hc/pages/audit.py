import streamlit as st

from .. import config, tx
from ..chain import fmt_time, list_products
from ..ctx import gate
from ..ui import card, chip, esc, goto, notice, page_heading, rows, stretch


def render(ctx):
    page_heading("PEMERIKSAAN LPH", "Audit dan inspeksi produk",
                 "Periksa kehalalan bahan dan kesesuaian fasilitas produksi. Hasil audit dicatat permanen on-chain, termasuk hasil yang gagal.")
    if not gate(ctx, ("LPH",), "LPH"):
        return
    notice("Akses terverifikasi: wallet aktif adalah <b>LPH resmi</b> yang terdaftar di smart contract.", "ok")

    pending = sorted([p for p in list_products(ctx.chain) if p["status"] == config.DIAJUKAN], key=lambda p: p["token_id"])
    if not pending:
        st.info("Tidak ada produk yang menunggu audit.")
        return
    labels = {f'#{p["token_id"]} · {p["nama"]} — {p["produsen"]}': p for p in pending}
    p = labels[st.selectbox(f"Produk menunggu audit ({len(pending)})", list(labels), key="audit_pick")]
    tid = p["token_id"]

    ing = "".join(f"<li>{esc(x)}</li>" for x in p["bahan"]) or "<li>-</li>"
    st.markdown(card(f'{esc(p["nama"])}', "Data pengajuan dari blockchain", rows([
        ("ID registrasi", p["id_registrasi"]), ("Produsen", p["produsen"]), ("Kategori", p["kategori"]),
        ("Tanggal pengajuan", fmt_time(p["tgl_daftar"])), ("Pemohon", p["pemohon"]), ("Hash dokumen", p["hash_dokumen"]),
    ], mono=("Pemohon", "Hash dokumen")) + f'<div class="drow"><span class="dl">Komposisi</span><span class="dv"><ul style="margin:0;padding-left:18px;text-align:left">{ing}</ul></span></div>'),
        unsafe_allow_html=True)
    st.button("Lihat detail & cocokkan dokumen", key=f"audit_detail_{tid}", icon=":material/open_in_new:",
              on_click=goto, args=("Detail Produk",), kwargs={"detail_token": tid})

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="sec-h">Lembar pemeriksaan</div><div class="sec-s">Jawaban di bawah dikirim ke smart contract.</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        bahan = c1.radio("Status kehalalan bahan", ["Halal", "Tidak Halal"], horizontal=True, key=f"audit_bahan_{tid}")
        fas = c2.radio("Kesesuaian fasilitas produksi", ["Ya", "Tidak"], horizontal=True, key=f"audit_fas_{tid}",
                       format_func=lambda v: "Sesuai" if v == "Ya" else "Tidak sesuai")
        catatan = st.text_area("Catatan pemeriksaan (opsional)", key=f"audit_note_{tid}", max_chars=500, height=90,
                               placeholder="Catatan internal. Tidak disimpan on-chain.")
        lolos = bahan == "Halal" and fas == "Ya"
        st.markdown(f'Hasil audit berdasarkan lembar ini: {chip(config.LOLOS_AUDIT if lolos else config.GAGAL_AUDIT)}', unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        approve = b1.button("Setujui audit", type="primary", key=f"audit_ok_{tid}", icon=":material/check_circle:", **stretch())
        reject = b2.button("Tolak audit", key=f"audit_no_{tid}", icon=":material/cancel:", **stretch())

    if approve or reject:
        if approve and not lolos:
            st.error("Audit tidak dapat disetujui: bahan harus Halal dan fasilitas harus Sesuai. Perbaiki lembar pemeriksaan atau pilih Tolak audit.")
            return
        if reject and lolos:
            st.error("Semua pemeriksaan memenuhi syarat, sehingga audit tidak dapat ditolak. Ubah hasil pemeriksaan atau pilih Setujui audit.")
            return
        fn = ctx.chain.contract.functions.pemeriksaanLPH(tid, bahan, fas)
        tx.begin(ctx, "Setujui audit LPH" if approve else "Tolak audit LPH", fn, [
            ("Produk", f'#{tid} · {p["nama"]}'), ("Kehalalan bahan", bahan),
            ("Fasilitas", "Sesuai" if fas == "Ya" else "Tidak sesuai"),
            ("Hasil", "Lolos audit" if approve else "Gagal audit (tercatat permanen)"),
            ("Catatan", (catatan.strip() or "-") + " (tidak disimpan on-chain)"),
        ], kind="audit")
        st.rerun()
