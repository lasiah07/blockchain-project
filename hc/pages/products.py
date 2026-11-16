import streamlit as st

from .. import config
from ..chain import fmt_time, list_products
from ..ctx import gate
from ..ui import chip, esc, goto, page_heading, stretch

PAGE_SIZE = 10


def render(ctx):
    page_heading("DAFTAR PRODUK", "Produk & status sertifikasi",
                 "Pengusaha melihat produk miliknya; LPH dan BPJPH melihat seluruh pengajuan.")
    if not gate(ctx, None):
        return
    products = list_products(ctx.chain)
    if ctx.role == "PENGUSAHA":
        products = [p for p in products if ctx.account in (p["pemohon"], p["owner"])]

    f1, f2 = st.columns([2.2, 1])
    q = f1.text_input("Cari produk", placeholder="Nama produk, produsen, ID registrasi, atau nomor sertifikat", key="plist_q")
    status_opts = ["Semua status"] + [v[0] for v in config.STATUS.values()]
    sel = f2.selectbox("Filter status", status_opts, key="plist_status")

    def match(p):
        if sel != "Semua status" and config.STATUS[p["status"]][0] != sel:
            return False
        hay = " ".join([p["nama"], p["produsen"], p["id_registrasi"], p["id_ketetapan"], f'#{p["token_id"]}']).lower()
        return q.strip().lower() in hay

    shown = sorted([p for p in products if match(p)], key=lambda p: p["token_id"], reverse=True)
    if not products:
        st.info("Belum ada produk" + (" atas wallet Anda." if ctx.role == "PENGUSAHA" else " pada jaringan ini."))
        return
    if not shown:
        st.warning("Tidak ada produk yang cocok dengan pencarian atau filter.")
        return

    pages = max(1, -(-len(shown) // PAGE_SIZE))
    cur = min(st.session_state.get("plist_page", 1), pages)
    view = shown[(cur - 1) * PAGE_SIZE: cur * PAGE_SIZE]

    widths = [1.0, 2.3, 1.9, 1.5, 1.5, 1.0]
    head = st.columns(widths)
    for col, text in zip(head, ["ID Registrasi", "Nama produk", "Produsen", "Tanggal pengajuan", "Status", "Aksi"]):
        col.markdown(f'<div class="thead">{text}</div>', unsafe_allow_html=True)
    for p in view:
        cols = st.columns(widths)
        cols[0].markdown(f'<div class="tcell mono">{esc(p["id_registrasi"])}<br>#{p["token_id"]}</div>', unsafe_allow_html=True)
        cols[1].markdown(f'<div class="tcell"><b>{esc(p["nama"])}</b></div>', unsafe_allow_html=True)
        cols[2].markdown(f'<div class="tcell">{esc(p["produsen"])}</div>', unsafe_allow_html=True)
        cols[3].markdown(f'<div class="tcell">{esc(fmt_time(p["tgl_daftar"]))}</div>', unsafe_allow_html=True)
        cols[4].markdown(f'<div class="tcell">{chip(p["status"])}</div>', unsafe_allow_html=True)
        cols[5].button("Detail", key=f'detail_{p["token_id"]}', icon=":material/visibility:",
                       on_click=goto, args=("Detail Produk",), kwargs={"detail_token": p["token_id"]}, **stretch())
    st.caption(f"Menampilkan {len(view)} dari {len(shown)} produk · halaman {cur}/{pages}")
    if pages > 1:
        n1, n2, _ = st.columns([1, 1, 5])
        n1.button("‹ Sebelumnya", disabled=cur <= 1, key="pl_prev", on_click=lambda: st.session_state.update(plist_page=cur - 1))
        n2.button("Berikutnya ›", disabled=cur >= pages, key="pl_next", on_click=lambda: st.session_state.update(plist_page=cur + 1))
