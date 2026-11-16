"""Alur transaksi: simulasi -> konfirmasi -> tanda tangan MetaMask -> status."""
from __future__ import annotations

import uuid

import streamlit as st

from . import config
from .chain import calldata, receipt_token_id, short, simulate
from .ctx import Ctx
from .ui import esc, goto, rows, stretch


def get():
    return st.session_state.get("tx")


def begin(ctx: Ctx, label: str, fn, summary: list[tuple[str, str]], kind: str):
    """Mulai alur transaksi. Simulasi dulu (eth_call) agar penolakan kontrak tampil sebelum MetaMask dibuka."""
    ok, err = simulate(fn, ctx.account)
    st.session_state["tx"] = {
        "id": uuid.uuid4().hex,
        "label": label,
        "kind": kind,
        "summary": summary,
        "from": ctx.account,
        "to": ctx.chain.address,
        "data": calldata(fn) if ok else None,
        "stage": "confirm" if ok else "failed",
        "error": None if ok else f"Transaksi tidak dikirim. Smart contract menolak: {err}",
        "hash": None,
        "block": None,
        "token_id": None,
    }


def pending_action():
    tx = get()
    if tx and tx["stage"] == "signing":
        return {"id": tx["id"], "to": tx["to"], "data": tx["data"], "from": tx["from"]}
    return None


def consume_result(ctx: Ctx):
    """Terapkan hasil dari MetaMask (dikembalikan komponen) pada transaksi yang sedang berjalan."""
    tx, res = get(), ctx.wallet.get("tx")
    if not tx or tx["stage"] != "signing" or not res or res.get("id") != tx["id"]:
        return
    status = res.get("status")
    if res.get("hash"):
        tx["hash"] = res["hash"]
    if status == "confirmed":
        tx["stage"], tx["block"] = "done", res.get("blockNumber")
        if tx["kind"] == "registrasi" and tx["hash"]:
            tx["token_id"] = receipt_token_id(ctx.chain, tx["hash"])
        st.session_state["form_nonce"] = st.session_state.get("form_nonce", 0) + 1
    elif status == "rejected":
        tx["stage"], tx["error"] = "failed", "Transaksi dibatalkan: Anda menolak permintaan tanda tangan di MetaMask. Tidak ada data yang berubah."
    elif status in ("failed", "reverted"):
        tx["stage"], tx["error"] = "failed", res.get("error") or "Transaksi gagal."


def _confirm():
    tx = get()
    if tx and tx["stage"] == "confirm":
        tx["stage"] = "signing"


def _close():
    st.session_state["tx"] = None


def render_panel(ctx: Ctx):
    tx = get()
    if not tx:
        return
    stage = tx["stage"]
    if stage == "confirm":
        mismatch = ctx.account != tx["from"]
        body = rows(
            [("Aksi", tx["label"])] + tx["summary"] + [
                ("Dikirim dari", tx["from"]),
                ("Smart contract", ctx.chain.address),
                ("Jaringan", f"{config.CHAIN_NAME} (Chain ID {config.CHAIN_ID})"),
                ("Biaya jaringan", "Gas jaringan uji lokal (ETH tanpa nilai), dihitung MetaMask"),
            ],
            mono=("Dikirim dari", "Smart contract"),
        )
        st.markdown(
            f'<div class="card"><div class="eyebrow">KONFIRMASI TRANSAKSI</div><div class="sec-h">Tinjau sebelum menandatangani</div>'
            f'<div class="sec-s">Simulasi smart contract berhasil. Setelah Anda melanjutkan, MetaMask akan meminta tanda tangan.</div>{body}</div>',
            unsafe_allow_html=True,
        )
        if mismatch:
            st.warning("Akun MetaMask aktif berubah sejak konfirmasi dibuat. Batalkan lalu ulangi transaksi.")
        c1, c2 = st.columns([2, 1])
        c1.button("Konfirmasi & tandatangani di MetaMask", type="primary", on_click=_confirm,
                  disabled=mismatch or not ctx.can_tx, key="tx_confirm", icon=":material/draw:", **stretch())
        c2.button("Batal", on_click=_close, key="tx_cancel", **stretch())
    elif stage == "signing":
        hash_line = (f'<br><span class="mono">Hash: {esc(tx["hash"])}</span>' if tx.get("hash") else "")
        st.markdown(
            f'<div class="notice info"><b>{"Menunggu konfirmasi block…" if tx.get("hash") else "Menunggu persetujuan di MetaMask…"}</b><br>'
            f'{"Transaksi sudah dikirim ke jaringan." if tx.get("hash") else "Buka jendela MetaMask dan setujui (Confirm) atau tolak (Reject) transaksi."}{hash_line}</div>',
            unsafe_allow_html=True,
        )
        st.button("Tutup panel (tidak membatalkan transaksi di MetaMask)", on_click=_close, key="tx_abort")
    elif stage == "done":
        st.markdown(
            f'<div class="notice ok"><b>✓ Transaksi berhasil — {esc(tx["label"])}</b><br>'
            f'Tercatat pada block #{esc(tx["block"])}.<br><span class="mono">Transaction hash: {esc(tx["hash"])}</span></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns([1.3, 1, 2])
        if tx.get("token_id"):
            cols[0].button(f"Lihat detail produk #{tx['token_id']}", type="primary", key="tx_detail", icon=":material/open_in_new:",
                           on_click=goto, args=("Detail Produk",), kwargs={"detail_token": tx["token_id"]}, **stretch())
        cols[1].button("Tutup", on_click=_close, key="tx_close", **stretch())
    elif stage == "failed":
        st.markdown(f'<div class="notice danger"><b>Transaksi tidak berhasil</b><br>{esc(tx["error"])}'
                    + (f'<br><span class="mono">Hash: {esc(tx["hash"])}</span>' if tx.get("hash") else "") + "</div>",
                    unsafe_allow_html=True)
        st.button("Tutup", on_click=_close, key="tx_close_f")
