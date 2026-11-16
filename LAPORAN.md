# Laporan Audit, Perubahan, dan Pengujian

## 1. Temuan audit (kondisi awal)
| # | Temuan | Dampak | Status |
|---|---|---|---|
| 1 | `app.py` tidak memakai MetaMask: transaksi dikirim server via `transact({"from":…})` memakai akun Hardhat yang di-unlock; "wallet" hanya dropdown | Tidak ada tanda tangan pengguna; hak akses hanya di UI | **Diganti** jembatan MetaMask + ethers.js |
| 2 | Alamat LPH/BPJPH ditulis statis di Python | Bisa tidak sinkron dengan kontrak | Dibaca dari kontrak |
| 3 | `idRegistrasi` selalu `"REG-001"` | ID tidak unik | `REG-001`, `REG-002`, … mengikuti tokenId |
| 4 | Audit gagal: status `GAGAL_AUDIT` ditulis lalu `revert` | Status gagal **tidak pernah tersimpan** | Tidak revert lagi; tersimpan + event "Gagal Audit" |
| 5 | Tidak ada status Expired | Sertifikat tak pernah kedaluwarsa | `KEDALUWARSA` (indeks 4) + `berlakuSampai` (365 hari) + `statusSaatIni()` |
| 6 | Hash dokumen tidak disimpan; "dokumen lengkap" hanya string `"Ya"` | Klaim fitur blockchain tidak benar | `bytes32 hashDokumen` (SHA-256) wajib & tersimpan |
| 7 | LPH bisa mengaudit ulang sertifikat aktif (menurunkan status) | Integritas data | Audit hanya dari status `DIAJUKAN` |
| 8 | Nomor ketetapan bisa ganda, tak bisa dicari | Verifikasi publik mustahil | Unik + `cariByKetetapan()` |
| 9 | Wallet otoritas bisa mendaftar produk di kontrak (hanya dicegah UI) | Hak akses lemah | Dicegah di kontrak |
| 10 | Pembacaan daftar bergantung `get_logs` penuh | Rapuh | `jumlahToken()` + pembacaan langsung |

**Kompatibilitas:** nama fungsi/event dipertahankan; urutan enum 0–3 dan 8 field struct awal tidak berubah (field baru ditambah di akhir). **Perubahan yang disengaja:** signature `registrasiHalal` (kini menerima produsen, kategori, hash dokumen sebagai ganti string `"Ya"`) dan `sertifikasiList` kini fungsi yang mengembalikan struct (getter otomatis 15 field memicu *stack too deep*). Kontrak perlu **dideploy ulang**; alamatnya tetap `0x5FbD…0aa3` pada node baru.

**Data on-chain:** identitas produk, produsen, kategori, hash dokumen, komposisi (di dalam `tokenURI` data-URI), hasil audit, nomor/tanggal/masa berlaku sertifikat, pemilik NFT, event. **Off-chain:** berkas dokumen asli (hanya hash yang dicatat) dan catatan internal LPH (hanya tampil di sesi, tidak disimpan).

## 2. File
**Ditambah:** `hc/*` (config, chain, tx, ctx, ui, wallet, qr), `hc/pages/*` (7 halaman), `components/metamask_bridge/{index.html,ethers.umd.min.js}`, `test/HalalChain.test.js`, `tests/*`, `requirements.txt`, `.gitignore`, `README.md`, `LAPORAN.md`.
**Diubah:** `contracts/HalalChain.sol`, `app.py` (ditulis ulang sebagai router), `scripts/deploy.js` (menyimpan alamat deployer/LPH/BPJPH), `package.json` (script npm), `.streamlit/config.toml` (tema terang ivory; sebelumnya dark).
**Tidak diubah:** `hardhat.config.js`, `deployment.json` (alamat sama). **Dihapus:** tidak ada.

## 3. Hasil pengujian (dijalankan di sandbox)
| Lapisan | Hasil | Cakupan |
|---|---|---|
| Kontrak (Hardhat) | **12/12** | registrasi, ID dinamis, hak akses, audit lolos/gagal, tak bisa audit ulang, penerbitan, duplikat, kedaluwarsa (time travel), constructor |
| Alur server (Streamlit AppTest + node Hardhat nyata) | **47/47** (web3 v7.16 dan v8.0) | alur Pengusaha→LPH→BPJPH→publik, tanpa wallet, MetaMask tak terpasang, jaringan salah, role salah (4 kombinasi), validasi input, tolak di MetaMask, simulasi pra-kirim, pencarian/filter, kepemilikan, XSS escape, verifikasi valid/tak ditemukan/gagal/belum terbit/kedaluwarsa, QR |
| Jembatan JS (jsdom + provider EIP-1193 tiruan menandatangani ke node nyata) | **12/12** | connect, accountsChanged, chainChanged, pindah jaringan, tanda tangan + receipt, anti-kirim ganda, reject (4001), jaringan salah, MetaMask absen |
| Server Streamlit nyata via WebSocket | OK | seluruh skrip jalan tanpa exception, komponen dirender, `index.html` & ethers.js disajikan (HTTP 200) |
| QR | OK | pembuatan → dekode → ekstraksi nomor |

## 4. Keterbatasan (jujur)
- **MetaMask asli belum diuji.** Sandbox tidak punya browser/ekstensi. Logika dibuktikan dengan provider EIP-1193 tiruan yang menandatangani ke node nyata, tetapi perilaku ekstensi MetaMask di dalam iframe komponen Streamlit baru bisa dipastikan di komputer Anda. Komponen mencoba `window.ethereum` di iframe, lalu `window.parent`/`window.top` sebagai cadangan. **Mohon jalankan panduan pengujian di README satu kali sebelum demo.**
- **Tampilan visual belum diperiksa lewat screenshot** (tidak ada browser). CSS ditulis mengikuti spesifikasi dan kode berjalan tanpa error, namun kerapian pixel perlu dicek mata Anda; sesuaikan di `hc/ui.py`.
- Kamera QR (`st.camera_input`) hanya diuji di sisi dekode; pengambilan kamera bergantung browser.
- Peran tidak berupa dropdown; dideteksi dari wallet (lebih aman dan sesuai syarat validasi on-chain). Perubahan ini disengaja.
- NFT masih dapat ditransfer (aturan awal dipertahankan). "Produk milik" memakai `pemohon` atau pemilik NFT saat ini.
- Hanya Hardhat Localhost; tidak ada penyimpanan berkas dokumen (hanya hash).
- Dependensi npm (`typescript ^7`, `@types/node ^26`) dari proyek awal tidak saya ubah; bila `npm install` bermasalah di mesin Anda, periksa versi tersebut.
