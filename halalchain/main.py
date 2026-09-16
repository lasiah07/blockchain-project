from blockchain import Blockchain


# Membuat blockchain
blockchain = Blockchain()


# ==========================================
# BLOCK 1 - PRODUSEN
# ==========================================

blockchain.add_block({
    "id_produk": "HALAL-001",
    "nama_produk": "Choco Delight",
    "actor": "Produsen",
    "aktivitas": "Pengajuan Sertifikasi Halal",
    "status": "Diajukan"
})


# ==========================================
# BLOCK 2 - PEMERIKSA
# ==========================================

blockchain.add_block({
    "id_produk": "HALAL-001",
    "nama_produk": "Choco Delight",
    "actor": "Pemeriksa",
    "aktivitas": "Pemeriksaan Produk",
    "status": "Diverifikasi"
})


# ==========================================
# BLOCK 3 - BPJPH
# ==========================================

blockchain.add_block({
    "id_produk": "HALAL-001",
    "nama_produk": "Choco Delight",
    "actor": "BPJPH",
    "aktivitas": "Proses Sertifikasi Halal",
    "status": "Diproses"
})
# ========================================
# BLOK 4 - Distribusi Produk
# Ditambahkan oleh: Fidz
# Pertemuan: 1
# ========================================
blockchain.add_block({
    "id_produk": "HALAL-001",
    "nama_produk": "Choco Delight",
    "actor": "Distributor",
    "aktivitas": "Pengiriman Produk ke Toko",
    "status": "Tersedia di Pasar"
})

# ========================================
# BLOK 5 - Penjualan ke Konsumen
# Ditambahkan oleh: Fidz
# Pertemuan: 1
# ========================================
blockchain.add_block({
    "id_produk": "HALAL-001",
    "nama_produk": "Choco Delight",
    "actor": "Konsumen",
    "aktivitas": "Pembelian Produk",
    "status": "Selesai"
})



# ==========================================
# MENAMPILKAN BLOCKCHAIN
# ==========================================

for block in blockchain.chain:

    print("\n==========================================")
    print("BLOCK", block.index)
    print("==========================================")

    print("Timestamp     :", block.timestamp)
    print("Data          :", block.data)
    print("Previous Hash :", block.previous_hash)
    print("Hash          :", block.hash)


# ==========================================
# CEK VALIDITAS BLOCKCHAIN
# ==========================================

print("\n==========================================")
print("STATUS BLOCKCHAIN")
print("==========================================")

if blockchain.is_valid():
    print("Blockchain valid")
else:
    print("Blockchain tidak valid")
  