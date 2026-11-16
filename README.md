# HalalChain Certification Network

Platform pendaftaran, audit, penerbitan, dan verifikasi sertifikasi halal berbasis blockchain.
**Stack:** Streamlit (Python) · Solidity/Hardhat · ethers.js · MetaMask · Hardhat Localhost (Chain ID 31337).

## Struktur
```
app.py                          router, sidebar, panel wallet
hc/                             logika aplikasi (config, chain, tx, ctx, ui, wallet, qr)
hc/pages/                       dashboard, submit, products, detail, audit, issue, verify
components/metamask_bridge/     komponen Streamlit dua arah (index.html + ethers.umd.min.js)
contracts/HalalChain.sol        smart contract ERC-721 (revisi v2)
scripts/deploy.js               deploy + tulis deployment.json
test/HalalChain.test.js         test kontrak (Hardhat/chai)
tests/                          uji alur server (AppTest) & uji jembatan JS
```

## Instalasi & menjalankan (urutan wajib)
Prasyarat: Node.js 18+, Python 3.10+, ekstensi MetaMask.

```bash
npm install
pip install -r requirements.txt

npx hardhat compile                                    # menghasilkan ABI di artifacts/
npx hardhat node                                       # TERMINAL 1 (biarkan berjalan)
npx hardhat run scripts/deploy.js --network localhost  # TERMINAL 2
streamlit run app.py                                   # TERMINAL 2 -> http://localhost:8501
```
Alamat kontrak pada node baru selalu `0x5FbDB2315678afecb367f032d93F642f64180aa3` (deploy pertama oleh Account #0), sama dengan `deployment.json` Anda.

> **Setiap kali `npx hardhat node` dimulai ulang, chain kembali kosong → jalankan lagi perintah deploy** dan reset MetaMask (lihat Troubleshooting).

Opsional: `HALALCHAIN_BASE_URL` (default `http://localhost:8501`) menentukan URL di dalam QR Code. Untuk demo lewat HP, isi dengan `http://<IP-laptop>:8501`.

## Konfigurasi MetaMask
1. **Tambah jaringan** (atau klik **Pindah ke Hardhat Localhost** di sidebar, otomatis menambahkan):
   Nama `Hardhat Localhost` · RPC `http://127.0.0.1:8545` · Chain ID `31337` · Simbol `ETH`.
2. **Impor akun** lewat *Account → Add account → Import account → Private key*. Salin private key dari output terminal `npx hardhat node` (jangan pernah dipakai di jaringan sungguhan):

| Peran | Akun Hardhat |
|---|---|
| Pengusaha A | Account #0 (juga deployer) |
| **LPH** | **Account #1** |
| **BPJPH** | **Account #2** |
| Pengusaha B / C | Account #3 / #4 |

Peran **tidak dipilih di aplikasi**, melainkan dideteksi dari alamat wallet yang terdaftar di smart contract (`lphAuditor`, `bpjphPenerbit`). Untuk berganti peran, ganti akun di MetaMask (tombol **Ganti akun** di sidebar).

## Panduan pengujian manual per peran
1. **Pengusaha (#3)** — Hubungkan MetaMask → *Pengajuan Produk* → isi form, unggah dokumen (hash SHA-256 dihitung otomatis) → *Kirim* → tinjau panel konfirmasi → *Konfirmasi & tandatangani* → setujui di MetaMask. Hash transaksi & block tampil. Cek di *Daftar Produk*.
2. **LPH (#1)** — Ganti akun → *Audit LPH* → pilih produk → isi lembar pemeriksaan → *Setujui audit* (atau *Tolak audit*; hasil gagal tercatat permanen).
3. **BPJPH (#2)** — Ganti akun → *Penerbitan BPJPH* → pilih produk lolos audit → isi nomor ketetapan (mis. `HC-2026-0001`) → *Terbitkan*.
4. **Pengusaha** — *Daftar Produk → Detail*: lihat status, nomor sertifikat, riwayat, QR Code (bisa diunduh).
5. **Publik (tanpa wallet)** — *Lacak Sertifikat*: cari nomor sertifikat, atau pindai QR (kamera/unggah gambar), atau buka URL `?verify=<nomor>`.
6. **Uji negatif** — buka *Audit LPH* dengan wallet Pengusaha (ditolak); pindah ke jaringan lain di MetaMask (transaksi diblokir); klik *Reject* di MetaMask (pesan "dibatalkan"); isi hash tidak valid; pakai nomor ketetapan ganda.

## Troubleshooting
| Gejala | Solusi |
|---|---|
| "Node Hardhat belum berjalan" | Jalankan `npx hardhat node` |
| "Tidak ada smart contract pada alamat…" | Node di-restart → jalankan deploy lagi |
| MetaMask: *nonce too high* / transaksi macet setelah restart node | MetaMask → Settings → Advanced → **Clear activity tab data** |
| Tombol MetaMask tidak muncul | Muat ulang halaman; pastikan ekstensi aktif untuk `localhost` |
| Kamera QR tidak jalan | Izinkan kamera; `localhost` dianggap aman oleh browser. Gunakan unggah gambar sebagai alternatif |

## Menjalankan test
```bash
npx hardhat test                  # kontrak (12 test)
python tests/test_app_flow.py     # alur server (47 cek) — pakai node baru + deploy
HARDHAT_ACCOUNT3_KEY=<private key Account #3> node tests/bridge_test.js   # butuh: npm i --no-save jsdom
```
