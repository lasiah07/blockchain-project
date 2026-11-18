// Memajukan nomor block chain yang SEDANG BERJALAN tanpa mengubah data (block kosong, ikut tercatat di jurnal).
// Dipakai bila MetaMask pernah melihat chain yang lebih tinggi (mis. dari node lama) dan "masih mengira" block terakhir
// lebih besar dari chain sekarang.   Contoh:  npm run chain:advance -- 300
const url = process.env.HC_RPC || "http://127.0.0.1:8545";
const n = Math.min(Math.max(parseInt(process.argv[2] || "100", 10) || 100, 1), 50000);
const rpc = async (body) => (await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) })).json();
(async () => {
  const before = parseInt((await rpc({ jsonrpc: "2.0", id: 1, method: "eth_blockNumber", params: [] })).result, 16);
  for (let done = 0; done < n; done += 500) {
    const batch = Array.from({ length: Math.min(500, n - done) }, (_, i) => ({ jsonrpc: "2.0", id: i + 1, method: "evm_mine", params: [] }));
    await rpc(batch);
  }
  const after = parseInt((await rpc({ jsonrpc: "2.0", id: 1, method: "eth_blockNumber", params: [] })).result, 16);
  console.log(`Block dimajukan: #${before} -> #${after} (${after - before} block kosong, tercatat di jurnal). Data produk/audit/sertifikat tidak berubah.`);
})().catch((e) => { console.error("Gagal (node `npm run node` harus berjalan):", e.message); process.exit(1); });