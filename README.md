# HalalChain Certification Network

HalalChain adalah aplikasi pendaftaran, audit, penerbitan, dan verifikasi sertifikasi halal berbasis teknologi blockchain.

## Teknologi yang Digunakan

- Python dan Streamlit
- Solidity dan Hardhat
- Web3.py dan ethers.js
- MetaMask
- Hardhat Localhost (Chain ID 31337)

## Persyaratan

Sebelum menjalankan aplikasi, pastikan perangkat sudah memiliki:

- Node.js versi 18 atau lebih baru
- Python versi 3.10 atau lebih baru
- MetaMask Extension
- Visual Studio Code

## Instalasi

1. Buka folder project melalui Visual Studio Code.
2. Buka terminal pada folder project.
3. Instal dependensi Node.js:

```bash
npm install
```

4. Buat dan aktifkan virtual environment Python (Windows):

```powershell
python -m venv .venv
.venv\Scripts\activate
```

5. Instal dependensi Python:

```bash
pip install -r requirements.txt
```

6. Kompilasi smart contract:

```bash
npx hardhat compile
```

## Cara Menjalankan Aplikasi

Jalankan aplikasi menggunakan tiga terminal di Visual Studio Code. Setiap terminal memiliki fungsi yang berbeda.

### Terminal 1 — Menjalankan Blockchain

```bash
npm run node
```

Perintah ini menjalankan jaringan blockchain lokal Hardhat dengan mekanisme persistensi data.

Biarkan terminal tetap berjalan selama aplikasi digunakan.

### Terminal 2 — Deployment Smart Contract

Buka terminal baru, kemudian jalankan:

```bash
npm run deploy
```

Perintah ini memastikan smart contract tersedia pada jaringan Hardhat Localhost.

### Terminal 3 — Menjalankan Aplikasi Streamlit

Buka terminal baru, aktifkan virtual environment jika belum aktif:

```powershell
.venv\Scripts\activate
```

Kemudian jalankan:

```bash
streamlit run app.py
```

Aplikasi dapat diakses melalui browser pada alamat:

**http://localhost:8501**

## Konfigurasi MetaMask

Hubungkan MetaMask dengan jaringan blockchain lokal menggunakan konfigurasi berikut:

| Konfigurasi | Nilai |
|---|---|
| Network Name | Hardhat Localhost |
| RPC URL | http://127.0.0.1:8545 |
| Chain ID | 31337 |
| Currency Symbol | ETH |

Gunakan akun pengujian dari Hardhat untuk menjalankan setiap peran dalam aplikasi.

| Akun | Peran |
|---|---|
| Account #0 | Pengusaha |
| Account #1 | LPH |
| Account #2 | BPJPH |
| Account #3 dan seterusnya | Pengusaha tambahan |

Private key akun pengujian dapat diperoleh dari output terminal Hardhat. Akun tersebut hanya digunakan pada jaringan lokal, bukan jaringan blockchain sungguhan.

**Catatan:** Jangan pernah menggunakan atau membagikan private key akun pribadi maupun akun dengan aset sungguhan.

## Alur Penggunaan Aplikasi

1. **Pengusaha:** Mendaftarkan produk dan mengunggah dokumen persyaratan sertifikasi halal.
2. **LPH:** Melakukan pemeriksaan dan audit terhadap produk yang diajukan.
3. **BPJPH:** Menerbitkan sertifikat halal untuk produk yang telah lolos audit.
4. **Pengusaha:** Melihat detail pengajuan, status sertifikasi, dan QR Code.
5. **Publik:** Melakukan verifikasi sertifikat melalui nomor sertifikat atau QR Code.

## Menghentikan Aplikasi

Untuk menghentikan aplikasi:

1. Tekan `Ctrl + C` pada terminal Streamlit.
2. Tekan `Ctrl + C` pada terminal deployment jika prosesnya masih berjalan.
3. Tekan `Ctrl + C` pada terminal blockchain.

**Catatan:** Jangan menghapus folder `chain-data` jika ingin mempertahankan data blockchain lokal yang sudah tersimpan.

---

**Repository:** https://github.com/lasiah07/blockchain-project