const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

const deploymentPath = path.join(__dirname, "..", "deployment.json");

// Deploy hanya bila belum ada kontrak HalalChain yang valid pada alamat di deployment.json.
// Paksa deploy ulang (alamat/data baru) dengan:  FORCE_DEPLOY=1 npm run deploy
async function alreadyDeployed(lph, bpjph) {
  if (process.env.FORCE_DEPLOY === "1" || !fs.existsSync(deploymentPath)) return null;
  try {
    const saved = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
    if ((await hre.ethers.provider.getCode(saved.address)) === "0x") return null;
    const c = await hre.ethers.getContractAt("HalalChain", saved.address);
    const [l, b] = await Promise.all([c.lphAuditor(), c.bpjphPenerbit()]);
    if (l.toLowerCase() === lph.toLowerCase() && b.toLowerCase() === bpjph.toLowerCase()) return saved;
  } catch (_) {}
  return null;
}

async function main() {
  console.log("Memulai deployment HalalChain...");

  const accounts = await hre.ethers.getSigners();
  const pengusaha = accounts[0];
  const lph = accounts[1];
  const bpjph = accounts[2];

  console.log("Alamat Wallet Pengusaha (Account 0):", pengusaha.address);
  console.log("Alamat Wallet LPH (Account 1):", lph.address);
  console.log("Alamat Wallet BPJPH (Account 2):", bpjph.address);

  const existing = await alreadyDeployed(lph.address, bpjph.address);
  if (existing) {
    console.log("\n=============================================");
    console.log("Kontrak SUDAH ter-deploy pada chain ini. Deploy dilewati.");
    console.log("Alamat Contract HalalChain:", existing.address);
    console.log("(Gunakan FORCE_DEPLOY=1 hanya bila ingin kontrak & data baru.)");
    console.log("=============================================\n");
    return;
  }

  const ContractFactory = await hre.ethers.getContractFactory("HalalChain");
  const contract = await ContractFactory.deploy(lph.address, bpjph.address);
  await contract.waitForDeployment();

  const contractAddress = await contract.getAddress();
  console.log("\n=============================================");
  console.log("Deployment Berhasil!");
  console.log("Alamat Contract HalalChain:", contractAddress);
  console.log("=============================================\n");

  const deploymentData = {
    contractName: "HalalChain",
    address: contractAddress,
    network: "localhost",
    chainId: 31337,
    deployer: pengusaha.address,
    lph: lph.address,
    bpjph: bpjph.address,
  };
  fs.writeFileSync(deploymentPath, JSON.stringify(deploymentData, null, 2));
  console.log("Alamat kontrak berhasil disimpan ke deployment.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
