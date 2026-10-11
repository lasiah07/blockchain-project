// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract HalalChain is ERC721URIStorage {
    
    // Status Proses Sertifikasi Halal sesuai Flowchart
    enum Status {
        DIAJUKAN,       // Pilihan 1: Registrasi Halal
        LOLOS_AUDIT,    // Pilihan 2: Audit LPH Lolos
        GAGAL_AUDIT,    // Pilihan 2: Audit LPH Gagal
        SERTIFIKAT_AKTIF // Pilihan 3: Terbit Sertifikat
    }

    // Struktur Data Sertifikasi Halal
    struct Sertifikasi {
        uint256 tokenId;
        string idRegistrasi;
        string namaProduk;
        string statusBahan;
        string fasSesuai;
        string idKetetapan;
        Status status;
        uint256 timestamp;
    }

    uint256 private nextTokenId = 1;

    // Mapping Token ID ke Data Sertifikasi
    mapping(uint256 => Sertifikasi) public sertifikasiList;

    // Events
    event RegistrasiBerhasil(uint256 indexed tokenId, string idRegistrasi, string namaProduk, address indexed pemohon);
    event AuditLPHSelesai(uint256 indexed tokenId, string hasilAudit, address indexed auditor);
    event SertifikatDiterbitkan(uint256 indexed tokenId, string idKetetapan, address indexed penerbit);

    // CONSTRUCTOR: Menentukan Nama Token dan Symbol (Modul 6)
    constructor() ERC721("Halal Certificate NFT", "HALAL") {}

    // ==========================================
    // PILIHAN 1: REGISTRASI HALAL 
    // ==========================================
    function registrasiHalal(
        string memory _namaProduk,
        string memory _dokLengkap,
        string memory _metadataURI
    ) public returns (uint256) {
        // Validasi Kelengkapan Dokumen
        require(
            keccak256(abi.encodePacked(_dokLengkap)) == keccak256(abi.encodePacked("Ya")),
            "Registrasi Ditolak, lengkapi dokumen!"
        );

        uint256 tokenId = nextTokenId;
        nextTokenId++;

        // Mint NFT ke pemohon (Modul 6)
        _safeMint(msg.sender, tokenId);
        _setTokenURI(tokenId, _metadataURI);

        string memory idReg = "REG-001";

        sertifikasiList[tokenId] = Sertifikasi({
            tokenId: tokenId,
            idRegistrasi: idReg,
            namaProduk: _namaProduk,
            statusBahan: "",
            fasSesuai: "",
            idKetetapan: "",
            status: Status.DIAJUKAN,
            timestamp: block.timestamp
        });

        emit RegistrasiBerhasil(tokenId, idReg, _namaProduk, msg.sender);
        return tokenId;
    }

    // ==========================================
    // PILIHAN 2: PEMERIKSAAN LPH 
    // ==========================================
    function pemeriksaanLPH(
        uint256 _tokenId,
        string memory _statusBahan,
        string memory _fasSesuai
    ) public {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        
        bool bahanHalal = keccak256(abi.encodePacked(_statusBahan)) == keccak256(abi.encodePacked("Halal"));
        bool fasilitasSesuai = keccak256(abi.encodePacked(_fasSesuai)) == keccak256(abi.encodePacked("Ya"));

        if (!bahanHalal) {
            sertifikasiList[_tokenId].status = Status.GAGAL_AUDIT;
            revert("Audit Gagal: Bahan Tidak Halal");
        }

        if (!fasilitasSesuai) {
            sertifikasiList[_tokenId].status = Status.GAGAL_AUDIT;
            revert("Audit Gagal: Fasilitas Tidak Sesuai");
        }

        // Jika Lolos
        sertifikasiList[_tokenId].statusBahan = _statusBahan;
        sertifikasiList[_tokenId].fasSesuai = _fasSesuai;
        sertifikasiList[_tokenId].status = Status.LOLOS_AUDIT;

        emit AuditLPHSelesai(_tokenId, "Lolos Audit", msg.sender);
    }

    // ==========================================
    // PILIHAN 3: TERBIT SERTIFIKAT 
    // ==========================================
    function terbitSertifikat(
        uint256 _tokenId,
        string memory _idKetetapan
    ) public {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        require(bytes(_idKetetapan).length > 0, "Gagal. ID Ketetapan Tidak Valid.");
        require(sertifikasiList[_tokenId].status == Status.LOLOS_AUDIT, "Harus Lolos Audit LPH Terlebih Dahulu");

        sertifikasiList[_tokenId].idKetetapan = _idKetetapan;
        sertifikasiList[_tokenId].status = Status.SERTIFIKAT_AKTIF;

        emit SertifikatDiterbitkan(_tokenId, _idKetetapan, msg.sender);
    }

    // ==========================================
    // CEK PEMILIK NFT 
    // ==========================================
    function getBatchOwner(uint256 _tokenId) public view returns (address) {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        return ownerOf(_tokenId);
    }
}