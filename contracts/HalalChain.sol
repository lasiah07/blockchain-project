// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * HalalChain Certification Network (revisi v2)
 *
 * Perubahan utama dibanding versi awal (semua kompatibel dengan alur lama):
 *  - idRegistrasi dinamis (REG-001, REG-002, ...) mengikuti tokenId.
 *  - Audit gagal TIDAK lagi revert: status GAGAL_AUDIT benar-benar tersimpan on-chain.
 *  - Status KEDALUWARSA ditambahkan (indeks 4, enum lama tidak bergeser).
 *  - Hash dokumen (SHA-256, bytes32) tersimpan on-chain; dokumen asli tetap off-chain.
 *  - Nomor ketetapan sertifikat unik dan dapat dicari (verifikasi publik).
 *  - Audit hanya bisa dilakukan pada status DIAJUKAN (sertifikat aktif tidak bisa diturunkan).
 *  - Wallet otoritas (LPH/BPJPH) tidak boleh mendaftarkan produk.
 *  - Field struct baru hanya DITAMBAHKAN di akhir agar urutan field lama tetap sama.
 */
contract HalalChain is ERC721URIStorage, Ownable {
    // Status Sertifikasi Halal (urutan 0-3 sama dengan versi awal)
    enum Status {
        DIAJUKAN,         // 0
        LOLOS_AUDIT,      // 1
        GAGAL_AUDIT,      // 2
        SERTIFIKAT_AKTIF, // 3
        KEDALUWARSA       // 4 (turunan: lihat statusSaatIni)
    }

    struct Sertifikasi {
        uint256 tokenId;
        string idRegistrasi;
        string namaProduk;
        string statusBahan;
        string fasSesuai;
        string idKetetapan;
        Status status;
        uint256 timestamp;
        // ---- field tambahan (append-only) ----
        string produsen;
        string kategori;
        bytes32 hashDokumen;
        address pemohon;
        uint256 tglAudit;
        uint256 tglTerbit;
        uint256 berlakuSampai;
    }

    /// Masa berlaku sertifikat sejak diterbitkan.
    uint256 public constant MASA_BERLAKU = 365 days;

    uint256 private nextTokenId = 1;

    address public lphAuditor;    // Wallet LPH resmi
    address public bpjphPenerbit; // Wallet BPJPH resmi

    mapping(uint256 => Sertifikasi) private _sertifikasi;
    mapping(bytes32 => uint256) private tokenByKetetapan; // keccak256(idKetetapan) => tokenId

    event RegistrasiBerhasil(uint256 indexed tokenId, string idRegistrasi, string namaProduk, address indexed pemohon);
    event AuditLPHSelesai(uint256 indexed tokenId, string hasilAudit, address indexed auditor);
    event SertifikatDiterbitkan(uint256 indexed tokenId, string idKetetapan, address indexed penerbit);

    modifier onlyLPH() {
        require(msg.sender == lphAuditor, "Otoritas Ditolak: Hanya LPH resmi yang berhak!");
        _;
    }

    modifier onlyBPJPH() {
        require(msg.sender == bpjphPenerbit, "Otoritas Ditolak: Hanya BPJPH resmi yang berhak!");
        _;
    }

    constructor(address _lphAuditor, address _bpjphPenerbit)
        ERC721("Halal Certificate NFT", "HALAL")
        Ownable(msg.sender)
    {
        require(_lphAuditor != address(0) && _bpjphPenerbit != address(0), "Alamat otoritas tidak valid");
        require(_lphAuditor != _bpjphPenerbit, "LPH dan BPJPH harus wallet berbeda");
        lphAuditor = _lphAuditor;
        bpjphPenerbit = _bpjphPenerbit;
    }

    // ==========================================
    // 1. REGISTRASI HALAL (PENGUSAHA)
    // ==========================================
    function registrasiHalal(
        string memory _namaProduk,
        string memory _produsen,
        string memory _kategori,
        bytes32 _hashDokumen,
        string memory _metadataURI
    ) public returns (uint256) {
        require(msg.sender != lphAuditor && msg.sender != bpjphPenerbit, "Wallet otoritas tidak boleh mendaftarkan produk");
        require(bytes(_namaProduk).length > 0, "Nama produk wajib diisi");
        require(bytes(_produsen).length > 0, "Nama produsen wajib diisi");
        require(bytes(_kategori).length > 0, "Kategori wajib diisi");
        require(_hashDokumen != bytes32(0), "Hash dokumen wajib diisi, lengkapi dokumen!");

        uint256 tokenId = nextTokenId;
        nextTokenId++;

        _safeMint(msg.sender, tokenId);
        _setTokenURI(tokenId, _metadataURI);

        string memory idReg = _formatIdRegistrasi(tokenId);

        _sertifikasi[tokenId] = Sertifikasi({
            tokenId: tokenId,
            idRegistrasi: idReg,
            namaProduk: _namaProduk,
            statusBahan: "",
            fasSesuai: "",
            idKetetapan: "",
            status: Status.DIAJUKAN,
            timestamp: block.timestamp,
            produsen: _produsen,
            kategori: _kategori,
            hashDokumen: _hashDokumen,
            pemohon: msg.sender,
            tglAudit: 0,
            tglTerbit: 0,
            berlakuSampai: 0
        });

        emit RegistrasiBerhasil(tokenId, idReg, _namaProduk, msg.sender);
        return tokenId;
    }

    // ==========================================
    // 2. PEMERIKSAAN LPH
    // Hasil gagal DISIMPAN (tidak revert) agar status GAGAL_AUDIT tercatat.
    // ==========================================
    function pemeriksaanLPH(
        uint256 _tokenId,
        string memory _statusBahan,
        string memory _fasSesuai
    ) public onlyLPH {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        require(
            _sertifikasi[_tokenId].status == Status.DIAJUKAN,
            "Produk sudah diaudit atau tidak berstatus Diajukan"
        );

        bool bahanHalal = keccak256(bytes(_statusBahan)) == keccak256(bytes("Halal"));
        bool fasilitasSesuai = keccak256(bytes(_fasSesuai)) == keccak256(bytes("Ya"));

        Sertifikasi storage s = _sertifikasi[_tokenId];
        s.statusBahan = _statusBahan;
        s.fasSesuai = _fasSesuai;
        s.tglAudit = block.timestamp;

        if (bahanHalal && fasilitasSesuai) {
            s.status = Status.LOLOS_AUDIT;
            emit AuditLPHSelesai(_tokenId, "Lolos Audit", msg.sender);
        } else {
            s.status = Status.GAGAL_AUDIT;
            emit AuditLPHSelesai(_tokenId, "Gagal Audit", msg.sender);
        }
    }

    // ==========================================
    // 3. PENERBITAN SERTIFIKAT (BPJPH)
    // ==========================================
    function terbitSertifikat(
        uint256 _tokenId,
        string memory _idKetetapan
    ) public onlyBPJPH {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        require(bytes(_idKetetapan).length > 0, "Gagal. ID Ketetapan Tidak Valid.");
        require(_sertifikasi[_tokenId].status == Status.LOLOS_AUDIT, "Harus Lolos Audit LPH Terlebih Dahulu");

        bytes32 key = keccak256(bytes(_idKetetapan));
        require(tokenByKetetapan[key] == 0, "ID Ketetapan sudah digunakan");

        Sertifikasi storage s = _sertifikasi[_tokenId];
        s.idKetetapan = _idKetetapan;
        s.status = Status.SERTIFIKAT_AKTIF;
        s.tglTerbit = block.timestamp;
        s.berlakuSampai = block.timestamp + MASA_BERLAKU;
        tokenByKetetapan[key] = _tokenId;

        emit SertifikatDiterbitkan(_tokenId, _idKetetapan, msg.sender);
    }

    // ==========================================
    // FUNGSI BACA
    // ==========================================
    /// Data lengkap satu sertifikasi (menggantikan getter otomatis; nama fungsi tetap sama).
    function sertifikasiList(uint256 _tokenId) external view returns (Sertifikasi memory) {
        return _sertifikasi[_tokenId];
    }

    function getBatchOwner(uint256 _tokenId) public view returns (address) {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        return ownerOf(_tokenId);
    }

    /// Jumlah total pendaftaran (tokenId berjalan 1..jumlahToken).
    function jumlahToken() external view returns (uint256) {
        return nextTokenId - 1;
    }

    /// Status efektif: SERTIFIKAT_AKTIF yang melewati masa berlaku dilaporkan KEDALUWARSA.
    function statusSaatIni(uint256 _tokenId) public view returns (Status) {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        Sertifikasi storage s = _sertifikasi[_tokenId];
        if (s.status == Status.SERTIFIKAT_AKTIF && block.timestamp > s.berlakuSampai) {
            return Status.KEDALUWARSA;
        }
        return s.status;
    }

    /// Cari tokenId dari nomor ketetapan sertifikat. Mengembalikan 0 jika tidak ada.
    function cariByKetetapan(string memory _idKetetapan) external view returns (uint256) {
        return tokenByKetetapan[keccak256(bytes(_idKetetapan))];
    }

    // ==========================================
    // INTERNAL
    // ==========================================
    function _formatIdRegistrasi(uint256 id) internal pure returns (string memory) {
        string memory n = Strings.toString(id);
        if (bytes(n).length == 1) return string.concat("REG-00", n);
        if (bytes(n).length == 2) return string.concat("REG-0", n);
        return string.concat("REG-", n);
    }
}
