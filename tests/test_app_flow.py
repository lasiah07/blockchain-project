"""Uji end-to-end sisi server (butuh: npx hardhat node + deploy aktif).
Jalankan:  python tests/test_app_flow.py   (gunakan node BARU agar hasil deterministik)
"""
"""Uji alur end-to-end sisi server dengan Streamlit AppTest. Jembatan MetaMask diganti stub berprotokol sama."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from streamlit.testing.v1 import AppTest
from web3 import Web3
import hc.wallet as hw
from hc import chain as C

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
ACC = w3.eth.accounts
S = {"account": None, "chainId": 31337, "installed": True, "reject": False, "results": {}}

def stub(action):
    st = {"installed": S["installed"], "account": S["account"], "chainId": S["chainId"], "error": None, "tx": None, "rev": 1}
    if action:
        aid = action["id"]
        if aid in S["results"]:
            st["tx"] = S["results"][aid]
        else:  # eksekusi "MetaMask": tandatangani & kirim; hasil muncul pada run berikutnya
            if S["reject"]:
                S["results"][aid] = {"id": aid, "status": "rejected", "hash": None, "blockNumber": None, "error": "ditolak"}
            else:
                h = w3.eth.send_transaction({"from": action["from"], "to": action["to"], "data": action["data"]})
                r = w3.eth.wait_for_transaction_receipt(h)
                S["results"][aid] = {"id": aid, "status": "confirmed" if r.status == 1 else "reverted", "hash": w3.to_hex(h), "blockNumber": r.blockNumber, "error": None}
    return st
hw.render_bridge = stub

ok = fail = 0
def check(name, cond, extra=""):
    global ok, fail
    (ok, fail) = (ok + 1, fail) if cond else (ok, fail + 1)
    print(("PASS " if cond else "FAIL ") + name, extra if not cond else "")

def app(account=None, page="Dashboard", **kw):
    S["account"] = account
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=60)
    at.session_state["page"] = page
    for k, v in kw.items(): at.session_state[k] = v
    at.run(); return at

def txt(at):  # semua teks markdown/error/success/info
    parts = [m.value for m in at.markdown] + [e.value for e in at.error] + [e.value for e in at.success] + [e.value for e in at.warning] + [e.value for e in at.info]
    return "\n".join(parts)

def goto(at, page, account=None, **kw):
    if account is not None: S["account"] = account
    at.session_state["page"] = page
    for k, v in kw.items(): at.session_state[k] = v
    at.run(); return at

def sign_flow(at):
    """klik konfirmasi -> (stub menjalankan tx) -> run lagi (hasil kembali)."""
    at.button(key="tx_confirm").click().run()
    at.run()
    return at

LPH, BPJPH, USAHA, USAHA2 = ACC[1], ACC[2], ACC[3], ACC[4]

# 1. Tanpa wallet
at = app(None)
check("Dashboard tanpa wallet tanpa exception", not at.exception, at.exception)
check("Dashboard memuat 'Total pengajuan'", "Total pengajuan" in txt(at))
at = goto(at, "Pengajuan Produk"); check("Pengajuan tanpa wallet meminta koneksi", "Wallet belum terhubung" in txt(at))
at = goto(at, "Lacak Sertifikat"); check("Verifikasi publik terbuka tanpa wallet", not at.exception and "Lacak" in txt(at))
at = goto(at, "Daftar Produk"); check("Daftar produk tanpa wallet meminta koneksi", "Wallet belum terhubung" in txt(at))

# 2. MetaMask tidak terpasang / jaringan salah
S["installed"] = False; at = goto(at, "Pengajuan Produk", None); check("MetaMask tidak terpasang -> pesan jelas", "MetaMask belum terpasang" in txt(at)); S["installed"] = True
S["chainId"] = 1; at = goto(at, "Pengajuan Produk", USAHA); check("Jaringan salah diblokir", "Jaringan MetaMask salah" in txt(at)); S["chainId"] = 31337

# 3. Hak akses berbasis alamat di kontrak
at = goto(at, "Audit LPH", USAHA); check("Pengusaha ditolak di Audit LPH", "Akses terbatas" in txt(at))
at = goto(at, "Penerbitan BPJPH", USAHA); check("Pengusaha ditolak di Penerbitan BPJPH", "Akses terbatas" in txt(at))
at = goto(at, "Pengajuan Produk", LPH); check("LPH ditolak mendaftar produk", "Akses terbatas" in txt(at))
at = goto(at, "Audit LPH", BPJPH); check("BPJPH ditolak di Audit LPH", "Akses terbatas" in txt(at))

# 4. Validasi input pengajuan
at = goto(at, "Pengajuan Produk", USAHA)
check("Form pengajuan tampil untuk Pengusaha", len(at.text_input) >= 2, txt(at)[:300])
at.radio(key="f_mode_0").set_value("Masukkan hash manual").run()
at.button(key="f_submit_0").click().run()
errs = " ".join(e.value for e in at.error)
check("Validasi: nama, bahan, hash wajib", "Nama produk minimal" in errs and "bahan wajib" in errs and "hash dokumen" in errs.lower(), errs)
at.text_input(key="f_nama_0").set_value("Kopi Aren Premium"); at.text_input(key="f_produsen_0").set_value("PT Kopi Nusantara")
at.text_area(key="f_bahan_0").set_value("Kopi Arabika\nGula Aren"); at.text_input(key="f_hash_0").set_value("0x1234")
at.button(key="f_submit_0").click().run()
check("Validasi: format hash salah ditolak", "Format hash" in " ".join(e.value for e in at.error))
check("Tidak ada transaksi dibuat saat input invalid", at.session_state["tx"] is None if "tx" in at.session_state else True)

# 5. Pengajuan sukses (tanda tangan via stub berprotokol MetaMask)
before = w3.eth.contract(address=C.get_chain().address, abi=C.get_chain().abi).functions.jumlahToken().call()
H = "0x" + "ab" * 32
at.text_input(key="f_hash_0").set_value(H); at.button(key="f_submit_0").click().run()
check("Panel konfirmasi transaksi muncul", "Tinjau sebelum menandatangani" in txt(at), txt(at)[:400])
sign_flow(at)
check("Transaksi sukses + hash tampil", "Transaksi berhasil" in txt(at) and "Transaction hash" in txt(at), txt(at)[-600:])
ch = C.get_chain(); n = ch.contract.functions.jumlahToken().call(); check("Token baru tercatat on-chain", n == before + 1)
p1 = C.read_product(ch, n)
check("Data on-chain benar (produsen, kategori, hash, pemohon, ID dinamis)", p1["produsen"] == "PT Kopi Nusantara" and p1["hash_dokumen"] == H and p1["pemohon"] == USAHA and p1["id_registrasi"] == f"REG-{n:03d}" and p1["bahan"] == ["Kopi Arabika", "Gula Aren"], p1)
check("Form direset setelah sukses", at.text_input(key="f_nama_1").value == "")

# 6. Pengusaha membatalkan di MetaMask
at = goto(at, "Pengajuan Produk", USAHA)
at.radio(key="f_mode_1").set_value("Masukkan hash manual").run()
at.text_input(key="f_nama_1").set_value("Teh Melati"); at.text_input(key="f_produsen_1").set_value("CV Teh"); at.text_area(key="f_bahan_1").set_value("Daun teh")
at.text_input(key="f_hash_1").set_value("0x" + "cd" * 32); at.button(key="f_submit_1").click().run()
S["reject"] = True; sign_flow(at); S["reject"] = False
check("Penolakan MetaMask ditangani", "Transaksi tidak berhasil" in txt(at) and "menolak" in txt(at).lower(), txt(at)[-500:])
check("Penolakan tidak membuat token", ch.contract.functions.jumlahToken().call() == n)
at.button(key="tx_close_f").click().run()

# 7. Daftar produk (pengusaha melihat miliknya saja)
at.session_state["tx"] = None
at = goto(at, "Daftar Produk", USAHA2); check("Pengusaha lain tidak melihat produk orang", "Belum ada produk" in txt(at))
at = goto(at, "Daftar Produk", USAHA); t = txt(at); check("Pengusaha melihat produk miliknya + ID Registrasi + aksi Detail", "Kopi Aren Premium" in t and f"REG-{n:03d}" in t and any(b.key == f"detail_{n}" for b in at.button))
at.text_input(key="plist_q").set_value("tidak-ada-xyz").run(); check("Pencarian tanpa hasil ditangani", "Tidak ada produk yang cocok" in txt(at))
at.text_input(key="plist_q").set_value("kopi").run(); at.selectbox(key="plist_status").set_value("Lolos Audit").run(); check("Filter status bekerja", "Tidak ada produk yang cocok" in txt(at))
at.selectbox(key="plist_status").set_value("Semua status").run()
at.button(key=f"detail_{n}").click().run(); check("Tombol Detail membuka halaman detail", "Riwayat aktivitas" in txt(at) and "Hash dokumen" in txt(at) and not at.exception, txt(at)[:300])
at = goto(at, "Detail Produk", USAHA2, detail_token=n); check("Pengusaha lain tidak bisa membuka detail produk orang", "bukan milik wallet Anda" in txt(at))

# 8. LPH: audit gagal tersimpan on-chain; audit lolos
at = goto(at, "Audit LPH", LPH); check("LPH melihat produk menunggu", "Lembar pemeriksaan" in txt(at), txt(at)[:300])
key = f"audit_bahan_{n}"
at.radio(key=key).set_value("Tidak Halal").run()
at.button(key=f"audit_ok_{n}").click().run(); check("Setujui diblokir bila bahan tidak halal", any("tidak dapat disetujui" in e.value.lower() for e in at.error))
at.button(key=f"audit_no_{n}").click().run(); check("Konfirmasi tolak audit muncul", "Tinjau sebelum menandatangani" in txt(at)); sign_flow(at)
p1 = C.read_product(ch, n); check("GAGAL_AUDIT tersimpan on-chain (bug revert terselesaikan)", p1["status"] == 2 and p1["status_bahan"] == "Tidak Halal", p1["status"])

# daftar produk 2 oleh pengusaha, lalu LOLOS
def register(acct, nama, h):
    ctr = ch.contract.functions.registrasiHalal(nama, "PT Uji", "Kosmetik", bytes.fromhex(h[2:]), C.build_metadata_uri({"ingredients": ["x"]}))
    r = w3.eth.wait_for_transaction_receipt(ctr.transact({"from": acct})); return ch.contract.functions.jumlahToken().call()
m = register(USAHA, "Sabun Herbal", "0x" + "11" * 32)
at = goto(at, "Audit LPH", LPH); at.tx = None; at.session_state["tx"] = None; at.run()
at.selectbox(key="audit_pick").set_value([o for o in at.selectbox(key="audit_pick").options if f"#{m} " in o][0]).run()
at.button(key=f"audit_ok_{m}").click().run(); sign_flow(at)
check("Audit lolos tercatat", C.read_product(ch, m)["status"] == 1)

# 9. BPJPH menerbitkan
at = goto(at, "Penerbitan BPJPH", BPJPH); at.session_state["tx"] = None; at.run()
check("BPJPH melihat produk lolos audit", "Ketetapan sertifikat" in txt(at))
at.text_input(key=f"issue_decree_{m}").set_value("bad nomor!"); at.button(key=f"issue_go_{m}").click().run()
check("Validasi nomor ketetapan", any("tidak valid" in e.value for e in at.error))
at.text_input(key=f"issue_decree_{m}").set_value("HC-2026-0001"); at.button(key=f"issue_go_{m}").click().run(); sign_flow(at)
pm = C.read_product(ch, m); check("Sertifikat aktif on-chain + masa berlaku 365 hari", pm["status"] == 3 and pm["id_ketetapan"] == "HC-2026-0001" and abs((pm["berlaku_sampai"] - pm["tgl_terbit"]) - 365 * 86400) < 5)

# nomor ketetapan duplikat
m2 = register(USAHA2, "Madu Hutan", "0x" + "22" * 32)
ch.contract.functions.pemeriksaanLPH(m2, "Halal", "Ya").transact({"from": LPH})
at = goto(at, "Penerbitan BPJPH", BPJPH); at.session_state["tx"] = None; at.run()
at.text_input(key=f"issue_decree_{m2}").set_value("HC-2026-0001"); at.button(key=f"issue_go_{m2}").click().run()
check("Nomor ketetapan duplikat ditolak", any("sudah digunakan" in e.value for e in at.error))

# 10. Pre-flight: kontrak menolak -> MetaMask tidak dibuka
from hc import tx as T
ok_, err = C.simulate(ch.contract.functions.pemeriksaanLPH(m, "Halal", "Ya"), USAHA); check("Simulasi: non-LPH ditolak dengan pesan jelas", (not ok_) and "Hanya LPH" in err, err)
ok_, err = C.simulate(ch.contract.functions.terbitSertifikat(n, "X-1"), BPJPH); check("Simulasi: produk gagal audit tak bisa diterbitkan", (not ok_) and "Lolos Audit" in err, err)

# 11. Verifikasi publik (tanpa wallet)
at = app(None, "Lacak Sertifikat", verify_input="HC-2026-0001", verify_active="HC-2026-0001")
t = txt(at); check("Verifikasi: sertifikat VALID", "Sertifikat halal VALID" in t and "Sabun Herbal" in t and not at.exception, t[:500])
at = app(None, "Lacak Sertifikat", verify_input="HC-TIDAK-ADA", verify_active="HC-TIDAK-ADA"); check("Verifikasi: tidak ditemukan", "Sertifikat tidak ditemukan" in txt(at))
at = app(None, "Lacak Sertifikat", verify_input=f"REG-{n:03d}", verify_active=f"REG-{n:03d}"); check("Verifikasi: gagal audit -> tidak valid", "TIDAK VALID" in txt(at))
at = app(None, "Lacak Sertifikat", verify_input=f"REG-{m2:03d}", verify_active=f"REG-{m2:03d}"); check("Verifikasi: belum diterbitkan", "Belum ada sertifikat" in txt(at))
at = app(None, "Lacak Sertifikat", verify_input="<script>alert(1)</script>", verify_active="<script>alert(1)</script>"); check("Input berbahaya di-escape", "<script>alert(1)</script>" not in txt(at) and "&lt;script&gt;" in txt(at))

# 12. Kedaluwarsa
w3.provider.make_request("evm_increaseTime", [366 * 86400]); w3.provider.make_request("evm_mine", [])
at = app(None, "Lacak Sertifikat", verify_input="HC-2026-0001", verify_active="HC-2026-0001"); check("Verifikasi: sertifikat KEDALUWARSA", "KEDALUWARSA" in txt(at))
at = app(None, "Dashboard"); check("Dashboard menghitung Expired", not at.exception and "Expired" in txt(at))

# 13. Detail + QR sebagai pengusaha pemilik sertifikat
at = goto(app(USAHA, "Dashboard"), "Detail Produk", USAHA, detail_token=m); check("Detail sertifikat + QR tanpa error", not at.exception and "QR Code verifikasi" in txt(at) and any("verify=HC-2026-0001" in c.value for c in at.caption), at.exception)

print(f"\nHASIL: {ok} lulus, {fail} gagal"); sys.exit(1 if fail else 0)
