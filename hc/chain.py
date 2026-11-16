"""Lapisan baca/tulis smart contract HalalChain (web3.py)."""
from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime

import streamlit as st
from web3 import Web3

from . import config


class ChainError(Exception):
    """Masalah konfigurasi/koneksi blockchain dengan pesan yang ramah pengguna."""


@dataclass
class Chain:
    w3: Web3
    contract: object
    address: str
    abi: list
    lph: str
    bpjph: str


@st.cache_resource(show_spinner=False)
def _build(rpc_url: str, dep_mtime: float, art_mtime: float):
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
    deployment = json.loads(config.DEPLOYMENT_PATH.read_text(encoding="utf-8"))
    abi = json.loads(config.ARTIFACT_PATH.read_text(encoding="utf-8"))["abi"]
    address = Web3.to_checksum_address(deployment["address"])
    return w3, w3.eth.contract(address=address, abi=abi), address, abi


def get_chain() -> Chain:
    if not config.DEPLOYMENT_PATH.exists():
        raise ChainError("File deployment.json tidak ditemukan. Jalankan: npx hardhat run scripts/deploy.js --network localhost")
    if not config.ARTIFACT_PATH.exists():
        raise ChainError("ABI belum dikompilasi. Jalankan: npx hardhat compile")
    try:
        w3, contract, address, abi = _build(
            config.RPC_URL, config.DEPLOYMENT_PATH.stat().st_mtime, config.ARTIFACT_PATH.stat().st_mtime
        )
    except Exception as exc:  # JSON rusak, dsb.
        raise ChainError(f"Gagal membaca konfigurasi kontrak: {exc}")
    if not w3.is_connected():
        raise ChainError("Node Hardhat belum berjalan di " + config.RPC_URL + ". Jalankan: npx hardhat node")
    if w3.eth.chain_id != config.CHAIN_ID:
        raise ChainError(f"Node RPC memakai Chain ID {w3.eth.chain_id}, seharusnya {config.CHAIN_ID}.")
    if len(w3.eth.get_code(address)) == 0:
        raise ChainError(
            "Tidak ada smart contract pada alamat di deployment.json. Node Hardhat kemungkinan baru dijalankan ulang. "
            "Jalankan: npx hardhat run scripts/deploy.js --network localhost"
        )
    try:
        lph = Web3.to_checksum_address(contract.functions.lphAuditor().call())
        bpjph = Web3.to_checksum_address(contract.functions.bpjphPenerbit().call())
    except Exception:
        raise ChainError("Kontrak pada alamat tersebut bukan HalalChain versi terbaru. Kompilasi ulang dan deploy ulang.")
    return Chain(w3, contract, address, abi, lph, bpjph)


# ------------------------------------------------------------------ util
def short(value: str, start: int = 8, end: int = 6) -> str:
    value = value or ""
    return value if len(value) <= start + end + 3 else f"{value[:start]}…{value[-end:]}"


def fmt_time(ts: int, with_time: bool = True) -> str:
    if not ts:
        return "-"
    return datetime.fromtimestamp(int(ts)).strftime("%d %b %Y %H:%M" if with_time else "%d %b %Y")


def sha256_bytes32(data: bytes) -> str:
    return "0x" + hashlib.sha256(data).hexdigest()


HASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")


def is_hash(value: str) -> bool:
    return bool(HASH_RE.match(value or "")) and int(value, 16) != 0


def build_metadata_uri(meta: dict) -> str:
    raw = json.dumps(meta, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "data:application/json;base64," + base64.b64encode(raw).decode("ascii")


def parse_metadata(uri: str) -> dict:
    try:
        if uri.startswith("data:application/json;base64,"):
            return json.loads(base64.b64decode(uri.split(",", 1)[1]).decode("utf-8"))
    except Exception:
        pass
    return {}


def friendly_error(exc: Exception) -> str:
    """Ambil alasan revert yang mudah dibaca dari berbagai bentuk error web3/Hardhat."""
    msg = str(exc)
    for pattern in (
        r"reverted with reason string '([^']*)'",
        r"execution reverted: \"?([^\"\n]*)\"?",
        r"execution reverted: ([^\n]*)",
        r"revert(?:ed)?:? ([^\n]*)",
    ):
        m = re.search(pattern, msg)
        if m and m.group(1).strip():
            return m.group(1).strip()
    if "execution reverted" in msg:
        return "Transaksi ditolak oleh smart contract."
    return msg[:300]


def calldata(fn) -> str:
    return fn._encode_transaction_data()


def simulate(fn, sender: str):
    """Simulasi eth_call dari wallet pengirim. Mengembalikan (ok, pesan_error)."""
    try:
        fn.call({"from": sender})
        return True, None
    except Exception as exc:
        return False, friendly_error(exc)


# ------------------------------------------------------------------ data produk
def _unwrap(raw, names):
    if isinstance(raw, dict):
        return raw
    if len(raw) == 1 and isinstance(raw[0], (list, tuple)):
        raw = raw[0]
    return dict(zip(names, raw))


def _struct_names(chain: Chain):
    for item in chain.abi:
        if item.get("name") == "sertifikasiList" and item.get("type") == "function":
            return [c["name"] for c in item["outputs"][0]["components"]]
    raise ChainError("ABI tidak memuat fungsi sertifikasiList.")


def read_product(chain: Chain, token_id: int):
    """Baca satu produk dari kontrak. Mengembalikan None jika tidak ada."""
    fn = chain.contract.functions
    try:
        data = _unwrap(fn.sertifikasiList(int(token_id)).call(), _struct_names(chain))
        if int(data["tokenId"]) == 0:
            return None
        status = int(fn.statusSaatIni(int(token_id)).call())
        owner = Web3.to_checksum_address(fn.getBatchOwner(int(token_id)).call())
        uri = fn.tokenURI(int(token_id)).call()
    except ChainError:
        raise
    except Exception:
        return None
    meta = parse_metadata(uri)
    return {
        "token_id": int(data["tokenId"]),
        "id_registrasi": data["idRegistrasi"],
        "nama": data["namaProduk"],
        "produsen": data["produsen"],
        "kategori": data["kategori"],
        "status_bahan": data["statusBahan"],
        "fas_sesuai": data["fasSesuai"],
        "id_ketetapan": data["idKetetapan"],
        "status": status,
        "status_raw": int(data["status"]),
        "tgl_daftar": int(data["timestamp"]),
        "tgl_audit": int(data["tglAudit"]),
        "tgl_terbit": int(data["tglTerbit"]),
        "berlaku_sampai": int(data["berlakuSampai"]),
        "hash_dokumen": "0x" + bytes(data["hashDokumen"]).hex(),
        "pemohon": Web3.to_checksum_address(data["pemohon"]),
        "owner": owner,
        "bahan": meta.get("ingredients", []),
        "nama_dokumen": meta.get("documentName", ""),
        "metadata_uri": uri,
    }


def list_products(chain: Chain):
    total = int(chain.contract.functions.jumlahToken().call())
    items = [read_product(chain, i) for i in range(1, total + 1)]
    return [p for p in items if p]


def find_token(chain: Chain, query: str) -> int:
    """Cari token dari nomor sertifikat, ID registrasi (REG-001) atau Token ID. 0 jika tidak ada."""
    q = (query or "").strip()
    if not q:
        return 0
    m = re.fullmatch(r"(?i)reg-?0*(\d+)", q) or re.fullmatch(r"#?(\d+)", q)
    if m:
        tid = int(m.group(1))
        total = int(chain.contract.functions.jumlahToken().call())
        return tid if 1 <= tid <= total else 0
    return int(chain.contract.functions.cariByKetetapan(q).call())


# ------------------------------------------------------------------ event / riwayat
_EVENT_META = {
    "RegistrasiBerhasil": "Produk didaftarkan oleh pemohon",
    "AuditLPHSelesai": "Audit LPH selesai",
    "SertifikatDiterbitkan": "Sertifikat diterbitkan BPJPH",
}


def get_events(chain: Chain, token_id: int | None = None, limit: int | None = None):
    """Kumpulkan event kontrak (terbaru dahulu)."""
    events = []
    block_time: dict[int, int] = {}
    flt = {"tokenId": int(token_id)} if token_id else None
    for name in _EVENT_META:
        try:
            logs = getattr(chain.contract.events, name)().get_logs(
                from_block=0, to_block="latest", argument_filters=flt
            )
        except Exception:
            continue
        for lg in logs:
            args = lg["args"]
            bn = int(lg["blockNumber"])
            if bn not in block_time:
                block_time[bn] = int(chain.w3.eth.get_block(bn)["timestamp"])
            if name == "RegistrasiBerhasil":
                actor, detail = args["pemohon"], f'{args["idRegistrasi"]} · {args["namaProduk"]}'
            elif name == "AuditLPHSelesai":
                actor, detail = args["auditor"], args["hasilAudit"]
            else:
                actor, detail = args["penerbit"], f'Nomor {args["idKetetapan"]}'
            events.append({
                "kind": name,
                "title": _EVENT_META[name] if name != "AuditLPHSelesai" else f'Audit LPH: {args["hasilAudit"]}',
                "token_id": int(args["tokenId"]),
                "actor": Web3.to_checksum_address(actor),
                "detail": detail,
                "tx_hash": "0x" + bytes(lg["transactionHash"]).hex(),
                "block": bn,
                "time": block_time[bn],
                "order": (bn, int(lg["logIndex"])),
            })
    events.sort(key=lambda e: e["order"], reverse=True)
    return events[:limit] if limit else events


def role_of(chain: Chain, account: str | None):
    if not account:
        return None
    if account == chain.lph:
        return "LPH"
    if account == chain.bpjph:
        return "BPJPH"
    return "PENGUSAHA"


def receipt_token_id(chain: Chain, tx_hash: str):
    """Ambil tokenId dari event RegistrasiBerhasil pada receipt (tanpa mendekode log Transfer ERC-721)."""
    try:
        receipt = chain.w3.eth.get_transaction_receipt(tx_hash)
        topic = bytes(chain.w3.keccak(text="RegistrasiBerhasil(uint256,string,string,address)"))
        for log in receipt["logs"]:
            if Web3.to_checksum_address(log["address"]) == chain.address and bytes(log["topics"][0]) == topic:
                return int.from_bytes(bytes(log["topics"][1]), "big")
    except Exception:
        pass
    return None
