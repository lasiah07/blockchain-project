const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

const HASH = ethers.sha256(ethers.toUtf8Bytes("dokumen-halal.pdf"));
const Status = { DIAJUKAN: 0n, LOLOS: 1n, GAGAL: 2n, AKTIF: 3n, KEDALUWARSA: 4n };

describe("HalalChain", function () {
  let c, owner, lph, bpjph, usaha, usaha2;

  async function daftar(signer = usaha, nama = "Kopi Aren") {
    const tx = await c.connect(signer).registrasiHalal(nama, "PT Kopi Nusantara", "Makanan & Minuman", HASH, "data:application/json;base64,e30=");
    await tx.wait();
    return await c.jumlahToken();
  }

  beforeEach(async () => {
    [owner, lph, bpjph, usaha, usaha2] = await ethers.getSigners();
    c = await (await ethers.getContractFactory("HalalChain")).deploy(lph.address, bpjph.address);
    await c.waitForDeployment();
  });

  describe("Registrasi", () => {
    it("membuat NFT, menyimpan hash dokumen dan metadata", async () => {
      const id = await daftar();
      expect(await c.ownerOf(id)).to.equal(usaha.address);
      const s = await c.sertifikasiList(id);
      expect(s.namaProduk).to.equal("Kopi Aren");
      expect(s.produsen).to.equal("PT Kopi Nusantara");
      expect(s.hashDokumen).to.equal(HASH);
      expect(s.pemohon).to.equal(usaha.address);
      expect(s.status).to.equal(Status.DIAJUKAN);
    });
    it("ID registrasi dinamis dan berurutan (bukan statis REG-001)", async () => {
      await daftar(); await daftar(usaha2, "Teh Melati");
      expect((await c.sertifikasiList(1)).idRegistrasi).to.equal("REG-001");
      expect((await c.sertifikasiList(2)).idRegistrasi).to.equal("REG-002");
    });
    it("menolak hash kosong, nama kosong, dan wallet otoritas", async () => {
      await expect(c.connect(usaha).registrasiHalal("A", "B", "C", ethers.ZeroHash, "x")).to.be.revertedWith(/Hash dokumen wajib/);
      await expect(c.connect(usaha).registrasiHalal("", "B", "C", HASH, "x")).to.be.revertedWith(/Nama produk/);
      await expect(c.connect(lph).registrasiHalal("A", "B", "C", HASH, "x")).to.be.revertedWith(/otoritas tidak boleh/);
      await expect(c.connect(bpjph).registrasiHalal("A", "B", "C", HASH, "x")).to.be.revertedWith(/otoritas tidak boleh/);
    });
  });

  describe("Audit LPH", () => {
    it("hanya LPH resmi yang boleh mengaudit", async () => {
      const id = await daftar();
      await expect(c.connect(usaha).pemeriksaanLPH(id, "Halal", "Ya")).to.be.revertedWith(/Hanya LPH/);
      await expect(c.connect(bpjph).pemeriksaanLPH(id, "Halal", "Ya")).to.be.revertedWith(/Hanya LPH/);
    });
    it("audit lolos -> LOLOS_AUDIT + event", async () => {
      const id = await daftar();
      await expect(c.connect(lph).pemeriksaanLPH(id, "Halal", "Ya")).to.emit(c, "AuditLPHSelesai").withArgs(id, "Lolos Audit", lph.address);
      expect((await c.sertifikasiList(id)).status).to.equal(Status.LOLOS);
    });
    it("audit GAGAL tersimpan on-chain (tidak revert lagi)", async () => {
      const id = await daftar();
      await expect(c.connect(lph).pemeriksaanLPH(id, "Tidak Halal", "Tidak")).to.emit(c, "AuditLPHSelesai").withArgs(id, "Gagal Audit", lph.address);
      const s = await c.sertifikasiList(id);
      expect(s.status).to.equal(Status.GAGAL);
      expect(s.statusBahan).to.equal("Tidak Halal");
    });
    it("audit tidak bisa diulang / tidak bisa menurunkan sertifikat aktif", async () => {
      const id = await daftar();
      await c.connect(lph).pemeriksaanLPH(id, "Halal", "Ya");
      await c.connect(bpjph).terbitSertifikat(id, "KET-1");
      await expect(c.connect(lph).pemeriksaanLPH(id, "Tidak Halal", "Tidak")).to.be.revertedWith(/sudah diaudit/);
      expect((await c.sertifikasiList(id)).status).to.equal(Status.AKTIF);
    });
    it("token tidak ada ditolak", async () => {
      await expect(c.connect(lph).pemeriksaanLPH(99, "Halal", "Ya")).to.be.revertedWith(/tidak ditemukan/);
    });
  });

  describe("Penerbitan BPJPH", () => {
    it("hanya BPJPH resmi; wajib lolos audit; ID ketetapan wajib & unik", async () => {
      const a = await daftar(); const b = await daftar(usaha2, "Teh");
      await expect(c.connect(bpjph).terbitSertifikat(a, "KET-1")).to.be.revertedWith(/Lolos Audit/);
      await c.connect(lph).pemeriksaanLPH(a, "Halal", "Ya");
      await c.connect(lph).pemeriksaanLPH(b, "Halal", "Ya");
      await expect(c.connect(lph).terbitSertifikat(a, "KET-1")).to.be.revertedWith(/Hanya BPJPH/);
      await expect(c.connect(usaha).terbitSertifikat(a, "KET-1")).to.be.revertedWith(/Hanya BPJPH/);
      await expect(c.connect(bpjph).terbitSertifikat(a, "")).to.be.revertedWith(/Tidak Valid/);
      await expect(c.connect(bpjph).terbitSertifikat(a, "KET-1")).to.emit(c, "SertifikatDiterbitkan").withArgs(a, "KET-1", bpjph.address);
      await expect(c.connect(bpjph).terbitSertifikat(b, "KET-1")).to.be.revertedWith(/sudah digunakan/);
      expect(await c.cariByKetetapan("KET-1")).to.equal(a);
      expect(await c.cariByKetetapan("TIDAK-ADA")).to.equal(0n);
    });
    it("produk gagal audit tidak bisa diterbitkan", async () => {
      const id = await daftar();
      await c.connect(lph).pemeriksaanLPH(id, "Tidak Halal", "Ya");
      await expect(c.connect(bpjph).terbitSertifikat(id, "KET-X")).to.be.revertedWith(/Lolos Audit/);
    });
  });

  describe("Kedaluwarsa", () => {
    it("status efektif menjadi KEDALUWARSA setelah masa berlaku", async () => {
      const id = await daftar();
      await c.connect(lph).pemeriksaanLPH(id, "Halal", "Ya");
      await c.connect(bpjph).terbitSertifikat(id, "KET-EXP");
      expect(await c.statusSaatIni(id)).to.equal(Status.AKTIF);
      await time.increase(366 * 24 * 3600);
      expect(await c.statusSaatIni(id)).to.equal(Status.KEDALUWARSA);
    });
  });

  it("constructor menolak alamat nol / sama", async () => {
    const F = await ethers.getContractFactory("HalalChain");
    await expect(F.deploy(ethers.ZeroAddress, bpjph.address)).to.be.revertedWith(/tidak valid/);
    await expect(F.deploy(lph.address, lph.address)).to.be.revertedWith(/berbeda/);
  });
});
