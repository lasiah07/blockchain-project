from blockchain import Blockchain
from block import Block
from pow import ProofOfWork
from pos import ProofOfStake


# ==========================================
# MEMBUAT BLOCKCHAIN
# ==========================================

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


# ==========================================
# BLOCK 4 - DISTRIBUTOR
# ==========================================

blockchain.add_block({
    "id_produk": "HALAL-001",
    "nama_produk": "Choco Delight",
    "actor": "Distributor",
    "aktivitas": "Pengiriman Produk ke Toko",
    "status": "Tersedia di Pasar"
})


# ==========================================
# BLOCK 5 - KONSUMEN
# ==========================================

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

print("\n==========================================")
print("BLOCKCHAIN SERTIFIKASI HALAL")
print("==========================================")

for block in blockchain.chain:

    print("\n==========================================")
    print("BLOCK", block.index)
    print("==========================================")

    print("Timestamp     :", block.timestamp)
    print("Data          :", block.data)
    print("Previous Hash :", block.previous_hash)
    print("Nonce         :", block.nonce)
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


# ==========================================
# SIMULASI PROOF OF WORK
# ==========================================

print("\n==========================================")
print("SIMULASI PROOF OF WORK")
print("==========================================")


for difficulty in [2, 3, 4, 5]:

    # Membuat block khusus untuk percobaan PoW
    block_pow = Block(
        index=6,
        data={
            "id_produk": "HALAL-001",
            "nama_produk": "Choco Delight",
            "aktivitas": "Pengujian Proof of Work"
        },
        previous_hash=blockchain.chain[-1].hash
    )

    # Membuat Proof of Work
    pow = ProofOfWork(difficulty)

    # Melakukan mining
    nonce, hash_result, mining_time = pow.mine(block_pow)

    # Menampilkan hasil
    print("\nDifficulty :", difficulty)
    print("Nonce      :", nonce)
    print("Waktu      :", mining_time, "detik")
    print("Hash       :", hash_result)


# ==========================================
# SIMULASI PROOF OF STAKE
# ==========================================

print("\n==========================================")
print("SIMULASI PROOF OF STAKE")
print("==========================================")


validators = {
    "Produsen": 10,
    "Pemeriksa": 20,
    "BPJPH": 30,
    "Distributor": 40
}


pos = ProofOfStake(validators)


hasil = {
    "Produsen": 0,
    "Pemeriksa": 0,
    "BPJPH": 0,
    "Distributor": 0
}


# Simulasi 20 kali

for i in range(20):

    selected = pos.select_validator()

    hasil[selected] += 1

    print("Simulasi", i + 1, ":", selected)


# ==========================================
# HASIL PEMILIHAN VALIDATOR
# ==========================================

print("\n==========================================")
print("HASIL PEMILIHAN VALIDATOR")
print("==========================================")

for validator, jumlah in hasil.items():

    print(validator, ":", jumlah, "kali")