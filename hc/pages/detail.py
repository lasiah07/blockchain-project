import hashlib

import streamlit as st

from .. import config
from ..chain import fmt_time, get_events, read_product, short
from ..ctx import gate
from ..qr import make_qr_png, verify_url
from ..ui import card, chip, esc, goto, notice, page_heading, rows


def stepper(status: int) -> str:
    s = [("Diajukan", "done"), ("Audit LPH", ""), ("Sertifikat terbit", ""), ("Berlaku", "")]
    if status >= 1 and status != 2:
        s[1] = ("Lolos audit", "done")
    if status == 2:
        s[1] = ("Gagal audit", "fail")
    if status in (3, 4):
        s[2] = ("Sertifikat terbit", "done")
        s[3] = ("Berlaku", "done") if status == 3 else ("Kedaluwarsa", "exp")
    return '<div class="steps">' + "".join(f'<div class="step {c}">{esc(t)}</div>' for t, c in s) + "</div>"


def document_checker(p, key: str):
    up = st.file_uploader("Cocokkan dokumen dengan hash on-chain", key=key, help="Berkas dibaca di aplikasi untuk menghitung SHA-256; tidak disimpan.")
    if up is not None:
        h = "0x" + hashlib.sha256(up.getvalue()).hexdigest()
        if h.lower() == p["hash_dokumen"].lower():
            st.success("Dokumen COCOK: hash SHA-256 sama dengan hash yang tercatat on-chain.")
        else:
            st.error("Dokumen TIDAK COCOK dengan hash on-chain. Berkas mungkin berbeda atau telah diubah.")
            st.caption(f"Hash berkas ini: {h}")


def render(ctx):
    st.button("‹ Kembali ke daftar produk", on_click=goto, args=("Daftar Produk",), key="detail_back")
    if not gate(ctx, None):
        return
    tid = st.session_state.get("detail_token")
    p = read_product(ctx.chain, tid) if tid else None
    if not p:
        st.error("Produk tidak ditemukan. Pilih produk dari halaman Daftar Produk.")
        return
    if ctx.role == "PENGUSAHA" and ctx.account not in (p["pemohon"], p["owner"]):
        notice("<b>Akses terbatas.</b> Produk ini bukan milik wallet Anda. Untuk memeriksa keaslian sertifikat, gunakan halaman <b>Lacak Sertifikat</b>.", "danger")
        return

    page_heading(f'{p["id_registrasi"]} · TOKEN #{p["token_id"]}', p["nama"], f'{p["produsen"]} · {p["kategori"]}')
    st.markdown(f'<div class="card">{chip(p["status"])}{stepper(p["status"])}</div>', unsafe_allow_html=True)
    st.write("")

    l, r = st.columns(2)
    with l:
        ing = "".join(f"<li>{esc(x)}</li>" for x in p["bahan"]) or "<li>-</li>"
        st.markdown(card("Informasi produk", "", rows([("Nama produk", p["nama"]), ("Produsen", p["produsen"]), ("Kategori", p["kategori"])])
                         + f'<div class="drow"><span class="dl">Komposisi</span><span class="dv"><ul style="margin:0;padding-left:18px;text-align:left">{ing}</ul></span></div>'),
                    unsafe_allow_html=True)
        st.markdown(card("Hasil audit LPH", "", rows([
            ("Status audit", chip(p["status"]) if p["status"] != 0 else "Menunggu audit"),
            ("Kehalalan bahan", p["status_bahan"]), ("Kesesuaian fasilitas", p["fas_sesuai"]), ("Tanggal audit", fmt_time(p["tgl_audit"])),
        ])), unsafe_allow_html=True)
    with r:
        st.markdown(card("Registrasi & sertifikat", "", rows([
            ("Nomor registrasi", p["id_registrasi"]), ("Tanggal pengajuan", fmt_time(p["tgl_daftar"])),
            ("Nomor sertifikat", p["id_ketetapan"] or "Belum diterbitkan"), ("Tanggal terbit", fmt_time(p["tgl_terbit"])),
            ("Berlaku sampai", fmt_time(p["berlaku_sampai"], False)),
        ])), unsafe_allow_html=True)
        st.markdown(card("Data blockchain", "", rows([
            ("Pemilik NFT", p["owner"]), ("Pemohon awal", p["pemohon"]), ("Alamat smart contract", ctx.chain.address),
            ("Hash dokumen", p["hash_dokumen"]), ("Standar token", "ERC-721"),
        ], mono=("Pemilik NFT", "Pemohon awal", "Alamat smart contract", "Hash dokumen"))), unsafe_allow_html=True)

    st.write("")
    a, b = st.columns([1.5, 1])
    with a:
        events = get_events(ctx.chain, token_id=p["token_id"])
        if events:
            items = "".join(
                f'<div class="tl-i"><div class="tl-t">{esc(e["title"])}</div><div class="tl-m">{esc(e["detail"])}<br>'
                f'{esc(fmt_time(e["time"]))} · block #{e["block"]} · oleh {esc(short(e["actor"], 8, 6))}<br>tx {esc(e["tx_hash"])}</div></div>'
                for e in reversed(events))
            body = f'<div class="tl">{items}</div>'
        else:
            body = "<div class='notice'>Belum ada riwayat.</div>"
        st.markdown(card("Riwayat aktivitas", "Event dibaca langsung dari blockchain.", body), unsafe_allow_html=True)
    with b:
        if p["id_ketetapan"]:
            url = verify_url(p["id_ketetapan"])
            png = make_qr_png(url)
            st.markdown('<div class="card"><div class="sec-h">QR Code verifikasi</div><div class="sec-s">Pindai untuk memeriksa keaslian sertifikat tanpa wallet.</div></div>', unsafe_allow_html=True)
            st.image(png, width=190)
            st.caption(url)
            st.download_button("Unduh QR Code (PNG)", png, file_name=f'qr-{p["id_ketetapan"]}.png', mime="image/png", key="dl_qr", icon=":material/download:")
        else:
            st.markdown('<div class="card"><div class="sec-h">QR Code verifikasi</div><div class="sec-s">QR Code tersedia setelah BPJPH menerbitkan sertifikat.</div></div>', unsafe_allow_html=True)
        st.write("")
        document_checker(p, key=f'doc_check_{p["token_id"]}')

    notice("<b>Data on-chain:</b> identitas produk, komposisi (dalam metadata NFT), hash dokumen, hasil audit, nomor &amp; masa berlaku sertifikat, pemilik NFT, riwayat event. "
           "<b>Off-chain:</b> berkas dokumen asli (hanya hash-nya yang dicatat) dan catatan internal LPH (tidak disimpan).", "info")
