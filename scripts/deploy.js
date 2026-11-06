import hre from "hardhat";

async function main() {
  const [deployer, accountLPH, accountBPJPH] = await hre.ethers.getSigners();

  console.log("Mendeploy contract dengan akun pengusaha:", deployer.address);
  console.log("Alamat Wallet LPH (Account 1):", accountLPH.address);
  console.log("Alamat Wallet BPJPH (Account 2):", accountBPJPH.address);

  const HalalChain = await hre.ethers.getContractFactory("HalalChain");
  const halalChain = await HalalChain.deploy(accountLPH.address, accountBPJPH.address);

  await halalChain.waitForDeployment();

  const contractAddress = await halalChain.getAddress();

  console.log("\n=============================================");
  console.log("Deployment Berhasil!");
  console.log("Alamat Contract HalalChain:", contractAddress);
  console.log("=============================================");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});