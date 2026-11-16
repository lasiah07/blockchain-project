import streamlit as st

from .. import config
from ..chain import fmt_time, get_events, list_products, short
from ..ui import card, esc, metric, rows


def render(ctx):
    chain, w3 = ctx.chain, ctx.chain.w3
    products = list_products(chain)
    n = lambda s: sum(1 for p in products if p["status"] == s)
    issued = sum(1 for p in products if p["tgl_terbit"])
    waiting = n(config.DIAJUKAN)

    st.markdown(
        f"""<div class="banner"><div class="kick">HalalChain Certification Network</div>
        <div class="ttl">Sertifikasi halal, tercatat transparan.</div>
        <p class="cp">Pantau pengajuan, audit LPH, penerbitan BPJPH, dan keaslian sertifikat dalam satu portal berbasis blockchain.</p>
        <span class="pill">● {esc(config.CHAIN_NAME)} · Chain ID {w3.eth.chain_id}</span>
        <span class="pill">Kontrak {esc(short(chain.address, 8, 6))}</span></div>""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="eyebrow">RINGKASAN JARINGAN</div>', unsafe_allow_html=True)
    c = st.columns(5)
    c[0].markdown(metric("Total pengajuan", len(products), "▦", "Terdata di smart contract", hero=True), unsafe_allow_html=True)
    c[1].markdown(metric("Sertifikat diterbitkan", issued, "✦", "Sejak awal jaringan"), unsafe_allow_html=True)
    c[2].markdown(metric("Pengajuan menunggu", waiting, "◔", "Menunggu audit LPH"), unsafe_allow_html=True)
    c[3].markdown(metric("Block terbaru", f"#{w3.eth.block_number}", "◈", "Tinggi block lokal"), unsafe_allow_html=True)
    c[4].markdown(metric("Chain ID", w3.eth.chain_id, "⌘", config.CHAIN_NAME), unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="eyebrow">STATISTIK SERTIFIKASI</div>', unsafe_allow_html=True)
    pending = n(config.DIAJUKAN) + n(config.LOLOS_AUDIT)
    stats = [
        ("Pending", pending, "◔", f"{n(config.DIAJUKAN)} menunggu audit · {n(config.LOLOS_AUDIT)} menunggu penerbitan", "#C9A64B"),
        ("Approved", n(config.AKTIF), "✓", "Sertifikat aktif", "#2A7358"),
        ("Rejected", n(config.GAGAL_AUDIT), "✕", "Gagal audit LPH", "#B24848"),
        ("Expired", n(config.KEDALUWARSA), "⌛", "Melewati masa berlaku", "#9A9A8C"),
    ]
    cols = st.columns(4)
    for col, (label, val, icon, note, _) in zip(cols, stats):
        col.markdown(metric(label, val, icon, note), unsafe_allow_html=True)
    total = max(len(products), 1)
    bar = "".join(f'<div style="width:{v / total * 100:.2f}%;background:{clr}"></div>' for _, v, _, _, clr in stats if v)
    legend = "".join(f'<span><i style="background:{clr}"></i>{lbl} {v}</span>' for lbl, v, _, _, clr in stats)
    st.markdown(f'<div class="card" style="margin-top:12px"><div class="sec-h">Distribusi status</div><div class="bar">{bar}</div><div class="legend">{legend}</div></div>',
                unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.5, 1])
    with left:
        events = get_events(chain, limit=8)
        if events:
            items = "".join(
                f'<div class="tl-i"><div class="tl-t">{esc(e["title"])} · Token #{e["token_id"]}</div>'
                f'<div class="tl-m">{esc(e["detail"])}<br>{esc(fmt_time(e["time"]))} · block #{e["block"]} · {esc(short(e["tx_hash"], 10, 6))}</div></div>'
                for e in events
            )
            body = f'<div class="tl">{items}</div>'
        else:
            body = '<div class="notice">Belum ada aktivitas pada jaringan ini. Aktivitas muncul setelah produk didaftarkan.</div>'
        st.markdown(card("Aktivitas sertifikasi terbaru", "Dibaca dari event smart contract (on-chain).", body), unsafe_allow_html=True)
    with right:
        info = rows([
            ("Nama kontrak", "HalalChain"), ("Standar token", "ERC-721 (NFT sertifikat)"),
            ("Alamat kontrak", short(chain.address, 10, 8)), ("Jaringan", f"{config.CHAIN_NAME}"),
            ("Alamat LPH", short(chain.lph, 8, 6)), ("Alamat BPJPH", short(chain.bpjph, 8, 6)),
            ("Masa berlaku sertifikat", "365 hari"),
        ])
        st.markdown(card("Informasi smart contract", "Otoritas dibaca langsung dari kontrak.", info), unsafe_allow_html=True)
