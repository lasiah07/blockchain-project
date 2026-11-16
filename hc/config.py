"""Konfigurasi pusat HalalChain."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RPC_URL = os.getenv("HALALCHAIN_RPC_URL", "http://127.0.0.1:8545")
CHAIN_ID = 31337
CHAIN_NAME = "Hardhat Localhost"
# Dipakai untuk membuat tautan pada QR Code verifikasi publik.
BASE_URL = os.getenv("HALALCHAIN_BASE_URL", "http://localhost:8501").rstrip("/")

DEPLOYMENT_PATH = ROOT / "deployment.json"
ARTIFACT_PATH = ROOT / "artifacts" / "contracts" / "HalalChain.sol" / "HalalChain.json"
COMPONENT_DIR = ROOT / "components" / "metamask_bridge"

# Urutan sama dengan enum Status pada HalalChain.sol
STATUS = {
    0: ("Diajukan", "info"),
    1: ("Lolos Audit", "warn"),
    2: ("Gagal Audit", "bad"),
    3: ("Sertifikat Aktif", "ok"),
    4: ("Kedaluwarsa", "muted"),
}
DIAJUKAN, LOLOS_AUDIT, GAGAL_AUDIT, AKTIF, KEDALUWARSA = 0, 1, 2, 3, 4

CATEGORIES = ["Makanan & Minuman", "Kosmetik", "Farmasi", "Obat Tradisional", "Barang Gunaan", "Lainnya"]

ROLE_LABEL = {"PENGUSAHA": "Pengusaha", "LPH": "LPH (Auditor)", "BPJPH": "BPJPH (Penerbit)"}
