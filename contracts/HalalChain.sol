// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract HalalChain is ERC721URIStorage, Ownable {
    
    // Status Sertifikasi Halal
    enum Status {
        DIAJUKAN,        // 0: Hasil dari Pilihan 1 (Registrasi Halal)
        LOLOS_AUDIT,     // 1: Hasil dari Pilihan 2 (Audit LPH Lolos)
        GAGAL_AUDIT,     // 2: Hasil dari Pilihan 2 (Audit LPH Gagal)
        SERTIFIKAT_AKTIF // 3: Hasil dari Pilihan 3 (Terbit Sertifikat)
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
    }

    uint256 private nextTokenId = 1;

    // Alamat Otoritas Instansi Berwenang
    address public lphAuditor;    // Account 1 (LPH)
    address public bpjphPenerbit; // Account 2 (BPJPH)

    mapping(uint256 => Sertifikasi) public sertifikasiList;

    // Events
    event RegistrasiBerhasil(uint256 indexed tokenId, string idRegistrasi, string namaProduk, address indexed pemohon);
    event AuditLPHSelesai(uint256 indexed tokenId, string hasilAudit, address indexed auditor);
    event SertifikatDiterbitkan(uint256 indexed tokenId, string idKetetapan, address indexed penerbit);

    // Modifier Pembatasan Hak Akses Otoritas
    modifier onlyLPH() {
        require(msg.sender == lphAuditor, "Otoritas Ditolak: Hanya LPH (Account 1) yang berhak!");
        _;
    }

    modifier onlyBPJPH() {
        require(msg.sender == bpjphPenerbit, "Otoritas Ditolak: Hanya BPJPH (Account 2) yang berhak!");
        _;
    }

    constructor(address _lphAuditor, address _bpjphPenerbit) 
        ERC721("Halal Certificate NFT", "HALAL") 
        Ownable(msg.sender) 
    {
        lphAuditor = _lphAuditor;
        bpjphPenerbit = _bpjphPenerbit;
    }

    // ==========================================
    // PILIHAN 1: REGISTRASI HALAL (PENGUSAHA)
    // Dipanggil oleh Pengusaha (Account 3, 4, 5, 6, dll)
    // ==========================================
    function registrasiHalal(
        string memory _namaProduk,
        string memory _dokLengkap,
        string memory _metadataURI
    ) public returns (uint256) {
        require(
            keccak256(abi.encodePacked(_dokLengkap)) == keccak256(abi.encodePacked("Ya")),
            "Registrasi Ditolak, lengkapi dokumen!"
        );

        uint256 tokenId = nextTokenId;
        nextTokenId++;

        // Mint NFT ke wallet Pengusaha yang memanggil fungsi ini
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
    // PILIHAN 2: PEMERIKSAAN LPH (AUDITOR)
    // Hanya dipanggil oleh LPH (Account 1)
    // ==========================================
    function pemeriksaanLPH(
        uint256 _tokenId,
        string memory _statusBahan,
        string memory _fasSesuai
    ) public onlyLPH {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        
        bool bahanHalal = keccak256(abi.encodePacked(_statusBahan)) == keccak256(abi.encodePacked("Halal"));
        bool fasilitasSesuai = keccak256(abi.encodePacked(_fasSesuai)) == keccak256(abi.encodePacked("Ya"));

        if (!bahanHalal || !fasilitasSesuai) {
            sertifikasiList[_tokenId].status = Status.GAGAL_AUDIT;
            revert("Audit Gagal: Bahan atau Fasilitas Tidak Sesuai");
        }

        sertifikasiList[_tokenId].statusBahan = _statusBahan;
        sertifikasiList[_tokenId].fasSesuai = _fasSesuai;
        sertifikasiList[_tokenId].status = Status.LOLOS_AUDIT;

        emit AuditLPHSelesai(_tokenId, "Lolos Audit", msg.sender);
    }

    // ==========================================
    // PILIHAN 3: TERBIT SERTIFIKAT (BPJPH)
    // Hanya dipanggil oleh BPJPH (Account 2)
    // ==========================================
    function terbitSertifikat(
        uint256 _tokenId,
        string memory _idKetetapan
    ) public onlyBPJPH {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        require(bytes(_idKetetapan).length > 0, "Gagal. ID Ketetapan Tidak Valid.");
        require(sertifikasiList[_tokenId].status == Status.LOLOS_AUDIT, "Harus Lolos Audit LPH Terlebih Dahulu");

        sertifikasiList[_tokenId].idKetetapan = _idKetetapan;
        sertifikasiList[_tokenId].status = Status.SERTIFIKAT_AKTIF;

        emit SertifikatDiterbitkan(_tokenId, _idKetetapan, msg.sender);
    }

    // Cek Pemilik NFT
    function getBatchOwner(uint256 _tokenId) public view returns (address) {
        require(_ownerOf(_tokenId) != address(0), "NFT tidak ditemukan");
        return ownerOf(_tokenId);
    }
}
