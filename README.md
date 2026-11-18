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
npx hardhat compile
```
Setiap kali bekerja, buka 3 terminal VS Code:

```bash
# Terminal 1 - blockchain PERSISTEN (biarkan berjalan; Ctrl+C untuk berhenti)
npm run node

# Terminal 2 - deploy (aman dijalankan berulang: dilewati bila kontrak sudah ada)
npm run deploy

# Terminal 3 - aplikasi (Windows: .venv\Scripts\activate dahulu)
streamlit run app.py          # -> http://localhost:8501
```

### Persistensi blockchain (data tidak hilang saat restart)
**Penyebab masalah lama:** Hardhat 2.x (termasuk 2.29.1) tidak punya penyimpanan state. `npx hardhat node` selalu memulai chain kosong, sehingga produk/audit/sertifikat hilang, dan nonce chain kembali ke 0 sementara MetaMask masih mengingat nonce lama (error *Nonce too high*).

**Solusi:** gunakan `npm run node` (bukan `npx hardhat node`). Skrip `scripts/persistent-node.js` mencatat setiap block (transaksi asli yang sudah ditandatangani + timestamp) ke `chain-data/journal.jsonl` sebelum MetaMask menerima hash transaksi. Saat dijalankan lagi, transaksi yang sama diputar ulang ke chain baru secara berurutan dengan timestamp asli, sehingga **alamat kontrak, state, nonce, dan hash transaksi identik**. Karena itu `hardhat_setNonce` tidak diperlukan lagi.

- Aman terhadap penutupan mendadak (jurnal di-`fsync` per block; baris terakhir yang terpotong diabaikan).
- Verifikasi integritas saat pemulihan: nomor block dan hash transaksi dicocokkan dengan jurnal; bila tidak cocok, node berhenti dengan pesan jelas dan **tidak menimpa data**.
- `npm run deploy` tidak deploy ulang bila kontrak sudah ada. Paksa kontrak baru hanya bila perlu: `FORCE_DEPLOY=1 npm run deploy`.
- `npm run chain:reset` mengosongkan chain (jurnal lama disimpan sebagai cadangan). Setelah reset: jalankan node, deploy, lalu di MetaMask **Settings > Advanced > Clear activity tab data** (satu-satunya situasi yang masih memerlukan reset MetaMask).
- `chain-data/` ada di `.gitignore` (data lokal, jangan di-commit). Salin foldernya bila ingin memindahkan data ke komputer lain.
- Batasan: hanya block/transaksi yang dipersistenkan (bukan `hardhat_setBalance`, impersonasi, atau mining interval). Mode automine bawaan Hardhat (1 transaksi = 1 block) didukung penuh.

Alamat kontrak pada chain persisten tidak berubah antarrestart: `0x5FbDB2315678afecb367f032d93F642f64180aa3` (selama deploy dilakukan pertama kali oleh Account #0 pada chain baru).

Opsi `npm run node:volatile` menjalankan node Hardhat biasa (tanpa persistensi) bila diperlukan.

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
| "Node Hardhat belum berjalan" | Jalankan `npm run node` |
| "Tidak ada smart contract pada alamat…" | Chain kosong (mis. setelah `chain:reset` atau memakai `node:volatile`) → `npm run deploy` |
| `Port 8545 sudah dipakai` | Tutup node Hardhat lain (mis. `npx hardhat node` lama) lalu ulangi `npm run node` |
| *Nonce too high* | Pastikan memakai `npm run node`. Bila chain pernah di-reset: MetaMask → Settings → Advanced → **Clear activity tab data** |
| Tombol MetaMask tidak muncul | Muat ulang halaman; pastikan ekstensi aktif untuk `localhost` |
| Kamera QR tidak jalan | Izinkan kamera; `localhost` dianggap aman oleh browser. Gunakan unggah gambar sebagai alternatif |

## Menjalankan test
```bash
npx hardhat test                  # kontrak (12 test)
node tests/persistence_test.js    # persistensi: kill -9 berulang, nonce, deploy idempoten (14 cek)
python tests/test_app_flow.py     # alur server (47 cek) — pakai node baru + deploy
HARDHAT_ACCOUNT3_KEY=<private key Account #3> node tests/bridge_test.js   # butuh: npm i --no-save jsdom
```
