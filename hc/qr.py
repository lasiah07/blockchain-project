"""QR Code verifikasi publik: pembuatan dan pemindaian."""
from __future__ import annotations

import io
from urllib.parse import parse_qs, quote, urlparse

from . import config


def verify_url(cert_number: str) -> str:
    return f"{config.BASE_URL}/?verify={quote(cert_number, safe='')}"


def make_qr_png(text: str) -> bytes:
    import qrcode

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=9, border=3)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#173F31", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def decode_qr(image_bytes: bytes):
    """Baca teks dari gambar QR. Mengembalikan None bila tidak terbaca."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        raise RuntimeError("Paket opencv-python-headless belum terpasang. Jalankan: pip install -r requirements.txt")
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    detector = cv2.QRCodeDetector()
    text, _, _ = detector.detectAndDecode(img)
    if not text:  # coba perbesar / grayscale untuk foto yang kecil atau buram
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        big = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        text, _, _ = detector.detectAndDecode(big)
    return text or None


def cert_from_payload(payload: str) -> str:
    """Ekstrak nomor sertifikat dari isi QR (URL verifikasi atau teks biasa)."""
    payload = (payload or "").strip()
    try:
        parsed = urlparse(payload)
        if parsed.scheme in ("http", "https"):
            values = parse_qs(parsed.query).get("verify")
            if values:
                return values[0].strip()
    except ValueError:
        pass
    return payload
