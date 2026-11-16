// Uji komponen jembatan MetaMask (jsdom + provider tiruan). Butuh: npm i --no-save jsdom, node hardhat aktif + deploy.
// Uji komponen jembatan dengan provider tiruan (EIP-1193) yang menandatangani ke node Hardhat nyata.
const path = require("path"); const ROOT = path.resolve(__dirname, "..");
const { JSDOM } = require("jsdom");
const ethers = require("ethers");
const fs = require("fs");
const dep = JSON.parse(fs.readFileSync(ROOT + "/deployment.json"));
const abi = JSON.parse(fs.readFileSync(ROOT + "/artifacts/contracts/HalalChain.sol/HalalChain.json")).abi;
const iface = new ethers.Interface(abi);
const rpc = new ethers.JsonRpcProvider("http://127.0.0.1:8545");
const KEY3 = process.env.HARDHAT_ACCOUNT3_KEY; // salin Private Key Account #3 dari terminal `npx hardhat node`
if (!KEY3) { console.error("Set env HARDHAT_ACCOUNT3_KEY (Account #3 dari output hardhat node)"); process.exit(2); }
const wallet = new ethers.Wallet(KEY3, rpc);

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
let listeners = {}, connected = false, chain = "0x7a69", rejectNext = false;
const mock = {
  isMetaMask: true,
  on(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); },
  async request({ method, params }) {
    if (method === "eth_accounts") return connected ? [wallet.address] : [];
    if (method === "eth_requestAccounts") { connected = true; return [wallet.address]; }
    if (method === "eth_chainId") return chain;
    if (method === "wallet_switchEthereumChain") { chain = params[0].chainId; (listeners.chainChanged||[]).forEach(f=>f(chain)); return null; }
    if (method === "eth_sendTransaction") {
      if (rejectNext) { rejectNext = false; const e = new Error("User rejected"); e.code = 4001; throw e; }
      const tx = await wallet.sendTransaction({ to: params[0].to, data: params[0].data });
      return tx.hash;
    }
    return rpc.send(method, params || []);
  },
};

(async () => {
  const msgs = [];
  const dom = new JSDOM(fs.readFileSync(ROOT + "/components/metamask_bridge/index.html", "utf8"), {
    runScripts: "dangerously", resources: "usable", url: "file://" + ROOT + "/components/metamask_bridge/index.html",
    beforeParse(w) { w.ethereum = mock; w.addEventListener("message", e => { if (e.data && e.data.isStreamlitMessage) msgs.push(e.data); }); },
  });
  const w = dom.window;
  await sleep(800);
  const last = () => [...msgs].reverse().find(m => m.type === "streamlit:setComponentValue")?.value;
  const render = (args) => w.postMessage({ type: "streamlit:render", args }, "*");
  const base = { chainId: 31337, rpcUrl: "http://127.0.0.1:8545", chainName: "Hardhat Localhost" };
  let ok = 0, fail = 0;
  const check = (name, cond, extra="") => { (cond ? ok++ : fail++); console.log((cond ? "PASS " : "FAIL ") + name + " " + extra); };

  check("componentReady dikirim", msgs.some(m => m.type === "streamlit:componentReady"));
  render(base); await sleep(600);
  check("provider terdeteksi, belum terhubung", last()?.installed === true && last()?.account === null, JSON.stringify(last()));
  check("tombol Hubungkan tampil", w.document.getElementById("b-connect") !== null);

  w.document.getElementById("b-connect").click(); await sleep(400);
  check("connect -> akun & chainId 31337", last()?.account?.toLowerCase() === wallet.address.toLowerCase() && last()?.chainId === 31337, JSON.stringify(last()));

  (listeners.accountsChanged||[]).forEach(f => f(["0x70997970C51812dc3A010C7d01b50e0d17dc79C8"])); await sleep(200);
  check("accountsChanged terdeteksi", last()?.account === "0x70997970C51812dc3A010C7d01b50e0d17dc79C8");
  (listeners.accountsChanged||[]).forEach(f => f([wallet.address])); await sleep(200);

  chain = "0x1"; (listeners.chainChanged||[]).forEach(f => f("0x1")); await sleep(200);
  check("chainChanged terdeteksi + tombol pindah jaringan", last()?.chainId === 1 && w.document.getElementById("b-net") !== null);
  w.document.getElementById("b-net").click(); await sleep(300);
  check("pindah jaringan -> 31337", last()?.chainId === 31337);

  const data = iface.encodeFunctionData("registrasiHalal", ["Produk Uji JS", "PT Uji", "Kosmetik", ethers.sha256("0x01"), "data:application/json;base64,e30="]);
  const action = { id: "tx-1", to: dep.address, data, from: wallet.address };
  render({ ...base, action }); await sleep(2500);
  let v = last();
  check("transaksi ditandatangani & dikonfirmasi", v?.tx?.id === "tx-1" && v?.tx?.status === "confirmed" && /^0x[0-9a-f]{64}$/.test(v?.tx?.hash||""), JSON.stringify(v?.tx));
  const before = msgs.length;
  render({ ...base, action }); await sleep(500);
  check("action yang sama tidak dikirim dua kali", msgs.filter(m=>m.type==="streamlit:setComponentValue").length === msgs.slice(0,before).filter(m=>m.type==="streamlit:setComponentValue").length);

  rejectNext = true; render({ ...base, action: { ...action, id: "tx-2" } }); await sleep(1200);
  v = last(); check("penolakan di MetaMask ditangani (rejected)", v?.tx?.id === "tx-2" && v?.tx?.status === "rejected", JSON.stringify(v?.tx));

  chain = "0x1"; render({ ...base, action: { ...action, id: "tx-3" } }); await sleep(1200);
  v = last(); check("transaksi di jaringan salah ditolak", v?.tx?.id === "tx-3" && v?.tx?.status === "failed" && /Hardhat/.test(v?.tx?.error||""), JSON.stringify(v?.tx));

  // tanpa MetaMask
  const msgs2 = [];
  const dom2 = new JSDOM(fs.readFileSync(ROOT + "/components/metamask_bridge/index.html", "utf8"), { runScripts: "dangerously", resources: "usable",
    beforeParse(w2) { w2.addEventListener("message", e => { if (e.data && e.data.isStreamlitMessage) msgs2.push(e.data); }); } });
  await sleep(500); dom2.window.postMessage({ type: "streamlit:render", args: base }, "*"); await sleep(3200);
  const v2 = [...msgs2].reverse().find(m => m.type === "streamlit:setComponentValue")?.value;
  check("MetaMask tidak terpasang terdeteksi", v2?.installed === false && /metamask.io/.test(dom2.window.document.body.innerHTML));
  console.log(`\nHASIL: ${ok} lulus, ${fail} gagal`); process.exit(fail ? 1 : 0);
})();
