"""Konteks sesi (wallet aktif + peran) dan penjaga hak akses."""
from __future__ import annotations

from dataclasses import dataclass

from . import config
from .chain import Chain, short
from .ui import esc, notice


@dataclass
class Ctx:
    chain: Chain
    wallet: dict
    account: str | None
    role: str | None
    chain_ok: bool
    page: str

    @property
    def connected(self) -> bool:
        return bool(self.account)

    @property
    def can_tx(self) -> bool:
        return self.connected and self.chain_ok


def gate(ctx: Ctx, allowed: tuple[str, ...] | None, needed_label: str = "") -> bool:
    """Tampilkan pesan jika wallet belum siap / bukan peran yang berwenang. True bila boleh lanjut.

    Validasi peran memakai alamat yang terdaftar di smart contract (lphAuditor / bpjphPenerbit),
    bukan pilihan menu. Kontrak tetap menjadi penjaga akhir saat transaksi dikirim.
    """
    w = ctx.wallet
    if w.get("installed") is False:
        notice("<b>MetaMask belum terpasang.</b> Pasang ekstensi MetaMask pada browser Anda, lalu muat ulang halaman.", "danger")
        return False
    if not ctx.connected:
        notice("<b>Wallet belum terhubung.</b> Klik <b>Hubungkan MetaMask</b> pada panel Wallet &amp; Akses di sidebar.", "warn")
        return False
    if not ctx.chain_ok:
        notice(
            f"<b>Jaringan MetaMask salah.</b> Aplikasi memerlukan <b>{config.CHAIN_NAME}</b> (Chain ID {config.CHAIN_ID}). "
            "Klik <b>Pindah ke Hardhat Localhost</b> di sidebar.",
            "warn",
        )
        return False
    if allowed and ctx.role not in allowed:
        notice(
            f"<b>Akses terbatas.</b> Wallet aktif <code>{esc(short(ctx.account, 10, 6))}</code> terdeteksi sebagai "
            f"<b>{esc(config.ROLE_LABEL.get(ctx.role, '-'))}</b>, bukan wallet resmi <b>{esc(needed_label)}</b> yang terdaftar di smart contract. "
            "Ganti akun melalui MetaMask (tombol <b>Ganti akun</b> di sidebar).",
            "danger",
        )
        return False
    return True
