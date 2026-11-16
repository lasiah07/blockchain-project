const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("Memulai deployment HalalChain...");

  // Ambil akun bawaan dari Hardhat node
  const accounts = await hre.ethers.getSigners();
  const pengusaha = accounts[0];
  const lph = accounts[1];
  const bpjph = accounts[2];

  console.log("Mendeploy contract dengan akun pengusaha:", pengusaha.address);
  console.log("Alamat Wallet LPH (Account 1):", lph.address);
  console.log("Alamat Wallet BPJPH (Account 2):", bpjph.address);

  const ContractFactory = await hre.ethers.getContractFactory("HalalChain");
  
  // Masukkan argumen constructor (lph & bpjph)
  const contract = await ContractFactory.deploy(lph.address, bpjph.address);
  await contract.waitForDeployment();

  const contractAddress = await contract.getAddress();
  console.log("\n=============================================");
  console.log("Deployment Berhasil!");
  console.log("Alamat Contract HalalChain:", contractAddress);
  console.log("=============================================\n");

  // Simpan alamat kontrak ke deployment.json
  const deploymentData = {
    contractName: "HalalChain",
    address: contractAddress,
    network: "localhost",
    chainId: 31337,
    deployer: pengusaha.address,
    lph: lph.address,
    bpjph: bpjph.address
  };

  const deploymentPath = path.join(__dirname, "..", "deployment.json");
  fs.writeFileSync(
    deploymentPath,
    JSON.stringify(deploymentData, null, 2)
  );
  console.log("Alamat kontrak berhasil disimpan ke deployment.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});