require("@nomicfoundation/hardhat-toolbox");

// scripts/persistent-node.js mengisi HC_INITIAL_DATE agar waktu genesis chain hasil
// restart sama dengan chain asli (dibutuhkan untuk memutar ulang transaksi dengan timestamp asli).
const initialDate = process.env.HC_INITIAL_DATE;

module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      evmVersion: "cancun",
    },
  },
  networks: {
    hardhat: {
      chainId: 31337,
      ...(initialDate ? { initialDate } : {}),
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    },
  },
};
