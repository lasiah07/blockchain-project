/**
 * Node Hardhat PERSISTEN untuk HalalChain.
 *
 * Masalah: Hardhat 2.x (termasuk 2.29.1) menyimpan chain hanya di memori. Setiap `npx hardhat node`
 * dimulai dari kosong, sehingga produk/audit/sertifikat hilang dan nonce MetaMask tidak sinkron
 * ("Nonce too high").
 *
 * Solusi: setiap block yang di-mine dicatat ke chain-data/journal.jsonl (transaksi asli yang sudah
 * ditandatangani + timestamp block). Saat node dimulai lagi, transaksi yang sama diputar ulang ke chain
 * baru, berurutan, dengan timestamp asli. Hasilnya chain identik: alamat kontrak, state, nonce, dan hash
 * transaksi sama seperti sebelum dimatikan. Ini tetap blockchain sungguhan (bukan database terpisah).
 *
 * Arsitektur:  MetaMask/Web3.py/Hardhat CLI --> 127.0.0.1:8545 (proxy pencatat) --> 127.0.0.1:8546 (Hardhat node)
 * Jalankan:    npm run node        (reset data: npm run chain:reset)
 */
const fs = require("fs");
const path = require("path");
const http = require("http");

const ROOT = path.resolve(__dirname, "..");
const DATA_DIR = process.env.HC_CHAIN_DATA || path.join(ROOT, "chain-data");
const JOURNAL = path.join(DATA_DIR, "journal.jsonl");
const PUBLIC_PORT = Number(process.env.HC_PORT || 8545);
const INTERNAL_PORT = Number(process.env.HC_INTERNAL_PORT || 8546);
const HOST = "127.0.0.1";
const HIGH_WATER = path.join(DATA_DIR, "high-water.json");
const TRACE_FILE = path.join(DATA_DIR, "rpc-trace.log");
const JOURNAL_VERSION = 1;

const log = (...a) => console.log("[persistent-node]", ...a);
const hex = (n) => "0x" + BigInt(n).toString(16);

// ---------------------------------------------------------------- jurnal (disk)
function readJournal() {
  if (!fs.existsSync(JOURNAL)) return { meta: null, blocks: [] };
  const raw = fs.readFileSync(JOURNAL, "utf8");
  const lines = raw.split("\n");
  const entries = [];
  let goodBytes = 0;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) { goodBytes += line.length + 1; continue; }
    try { entries.push(JSON.parse(line)); goodBytes += Buffer.byteLength(line) + 1; }
    catch (e) {
      if (i >= lines.length - 2) { log("Baris terakhir jurnal terpotong (komputer mati mendadak?) - diabaikan."); break; }
      throw new Error(`Jurnal rusak pada baris ${i + 1}: ${e.message}`);
    }
  }
  // buang baris terpotong agar penambahan berikutnya tidak merusak berkas
  const clean = entries.map((e) => JSON.stringify(e)).join("\n") + (entries.length ? "\n" : "");
  if (clean !== raw) fs.writeFileSync(JOURNAL, clean);
  const meta = entries.find((e) => e.t === "meta") || null;
  const blocks = entries.filter((e) => e.t === "block");
  return { meta, blocks };
}

// Tinggi block tertinggi yang pernah dilayani. Dipertahankan walau chain di-reset, agar nomor block
// tidak pernah "mundur" / terpakai ulang (MetaMask menyimpan block terakhir & cache per nomor block).
function readHighWater() { try { return Number(JSON.parse(fs.readFileSync(HIGH_WATER, "utf8")).height) || 0; } catch (_) { return 0; } }
function writeHighWater(h) { try { fs.mkdirSync(DATA_DIR, { recursive: true }); fs.writeFileSync(HIGH_WATER, JSON.stringify({ height: h, updatedAt: new Date().toISOString() })); } catch (_) {} }

// Jejak lalu lintas nonce (konsol + chain-data/rpc-trace.log) sebagai BUKTI apa yang ditanyakan/dikirim MetaMask.
function trace(line) {
  console.log("[rpc]", line);
  try { fs.mkdirSync(DATA_DIR, { recursive: true }); fs.appendFileSync(TRACE_FILE, `${new Date().toISOString()} ${line}\n`); } catch (_) {}
}

let journalFd = null;
function appendJournal(entry) {
  if (journalFd === null) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    journalFd = fs.openSync(JOURNAL, "a");
  }
  fs.writeSync(journalFd, JSON.stringify(entry) + "\n");
  fs.fsyncSync(journalFd); // pastikan benar-benar tertulis ke disk sebelum MetaMask menerima hash
}

// Jurnal harus bisa ditulis SEBELUM sebuah transaksi diteruskan ke chain. Bila tidak (mis. berkas terkunci oleh
// sinkronisasi OneDrive/antivirus), transaksi ditolak: lebih baik gagal jelas daripada chain & jurnal tidak sinkron
// (itulah yang membuat nonce MetaMask "lebih tinggi" dari nonce chain setelah restart).
function ensureJournalWritable() {
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      if (journalFd === null) { fs.mkdirSync(DATA_DIR, { recursive: true }); journalFd = fs.openSync(JOURNAL, "a"); }
      fs.writeSync(journalFd, ""); fs.fsyncSync(journalFd);
      return null;
    } catch (e) {
      try { if (journalFd !== null) fs.closeSync(journalFd); } catch (_) {}
      journalFd = null;
      if (attempt === 1) return e.message;
    }
  }
}

// ---------------------------------------------------------------- main
(async () => {
  const journal = readJournal();
  if (journal.meta && journal.meta.version !== JOURNAL_VERSION) throw new Error("Versi jurnal tidak dikenal.");
  if (journal.meta) process.env.HC_INITIAL_DATE = new Date(journal.meta.genesisTimestamp * 1000).toISOString();

  const hre = require("hardhat"); // dimuat SETELAH HC_INITIAL_DATE diset
  const { keccak256, Transaction } = require("ethers");
  const provider = hre.network.provider;
  const send = (m, p = []) => provider.send(m, p);

  // 1) jalankan server Hardhat standar pada port internal (perilaku RPC identik dengan `hardhat node`)
  hre.run("node", { hostname: HOST, port: INTERNAL_PORT }).catch((e) => { console.error(e); process.exit(1); });
  for (let i = 0; i < 100; i++) {
    try { const r = await fetch(`http://${HOST}:${INTERNAL_PORT}`, { method: "POST", headers: { "content-type": "application/json" }, body: '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' }); if (r.ok) break; } catch (_) {}
    await new Promise((r) => setTimeout(r, 100));
  }

  const rawByHash = new Map(); // hash -> raw tx (ditangkap dari eth_sendRawTransaction milik MetaMask)
  const block = async (n, full = true) => send("eth_getBlockByNumber", [typeof n === "number" ? hex(n) : n, full]);

  // 2) putar ulang jurnal
  if (journal.meta) {
    log(`Memulihkan chain dari jurnal: ${journal.blocks.length} block...`);
    for (const rec of journal.blocks) {
      await send("evm_setNextBlockTimestamp", [rec.timestamp]);
      const before = parseInt(await send("eth_blockNumber"), 16);
      if (rec.txs.length === 0) {
        await send("evm_mine");
      } else if (rec.txs.length === 1) {
        const tx = rec.txs[0];
        try {
          if (tx.raw) await send("eth_sendRawTransaction", [tx.raw]);
          else await send("eth_sendTransaction", [tx.params]);
        } catch (e) {
          // transaksi yang revert tetap di-mine oleh Hardhat; cukup pastikan block bertambah
          if (parseInt(await send("eth_blockNumber"), 16) === before) throw e;
        }
      } else {
        throw new Error(`Block #${rec.number} berisi ${rec.txs.length} transaksi (tidak didukung mode automine).`);
      }
      const now = parseInt(await send("eth_blockNumber"), 16);
      if (now !== rec.number) throw new Error(`Penyimpangan saat replay: diharapkan block #${rec.number}, hasil #${now}.`);
      if (rec.txs[0]) {
        const b = await block(now);
        const h = b.transactions[0].hash;
        if (rec.txs[0].hash && h.toLowerCase() !== rec.txs[0].hash.toLowerCase()) {
          if (rec.txs[0].raw) throw new Error(`Hash transaksi block #${now} berbeda dari jurnal. Jurnal tidak cocok dengan versi Hardhat ini.`);
          log(`Peringatan: hash transaksi block #${now} berbeda (transaksi akun terbuka), state tetap sama.`);
        }
        if (rec.txs[0].raw) rawByHash.set(h.toLowerCase(), rec.txs[0].raw);
      }
    }
    // geser jam chain ke waktu nyata supaya block baru tidak bertanggal lampau
    const last = parseInt((await block("latest", false)).timestamp, 16);
    const delta = Math.floor(Date.now() / 1000) - last;
    if (delta > 0) await send("evm_increaseTime", [delta]);
    log(`Pemulihan selesai. Block terakhir: #${journal.blocks.length ? journal.blocks[journal.blocks.length - 1].number : 0}.`);
  } else {
    const genesis = await block(0, false);
    appendJournal({ t: "meta", version: JOURNAL_VERSION, chainId: 31337, genesisTimestamp: parseInt(genesis.timestamp, 16), createdAt: new Date().toISOString() });
    log("Chain baru. Jurnal dibuat di", path.relative(ROOT, JOURNAL));
  }

  // 2b) PERIKSA: nonce akun di chain hasil pemulihan harus sama dengan jumlah transaksi akun itu di jurnal
  if (journal.meta) {
    const expected = new Map();
    for (const rec of journal.blocks) for (const t of rec.txs) {
      const from = (t.raw ? Transaction.from(t.raw).from : t.params.from).toLowerCase();
      expected.set(from, (expected.get(from) || 0) + 1);
    }
    for (const [addr, cnt] of expected) {
      const real = parseInt(await send("eth_getTransactionCount", [addr, "latest"]), 16);
      if (real !== cnt) throw new Error(`Nonce ${addr} hasil pemulihan (${real}) tidak sama dengan jurnal (${cnt}). Jurnal tidak konsisten; data TIDAK diubah.`);
    }
  }
  const accounts = await send("eth_accounts");
  log("Nonce akun di chain (harus sama dengan nonce yang dipakai MetaMask):");
  for (let i = 0; i < accounts.length; i++) {
    const n = parseInt(await send("eth_getTransactionCount", [accounts[i], "latest"]), 16);
    if (n > 0 || i < 4) log(`   Account #${i} ${accounts[i]} -> nonce ${n}`);
  }

  // 3) pencatat block baru
  let journaled = parseInt(await send("eth_blockNumber"), 16);
  let chain = Promise.resolve();
  const sync = () => (chain = chain.then(async () => {
    const latest = parseInt(await send("eth_blockNumber"), 16);
    for (let n = journaled + 1; n <= latest; n++) {
      const b = await block(n);
      const txs = [];
      for (const t of b.transactions) {
        const h = t.hash.toLowerCase();
        if (rawByHash.has(h)) { txs.push({ hash: t.hash, raw: rawByHash.get(h) }); continue; }
        // transaksi dari akun Hardhat terbuka (deploy script, console): simpan parameter, tanda tangan deterministik
        const params = { from: t.from, data: t.input, value: t.value, gas: t.gas, nonce: t.nonce };
        if (t.to) params.to = t.to;
        if (t.maxFeePerGas) { params.maxFeePerGas = t.maxFeePerGas; params.maxPriorityFeePerGas = t.maxPriorityFeePerGas; } else if (t.gasPrice) params.gasPrice = t.gasPrice;
        txs.push({ hash: t.hash, params });
      }
      appendJournal({ t: "block", number: n, timestamp: parseInt(b.timestamp, 16), txs });
      journaled = n;
    }
    if (journaled > readHighWater()) writeHighWater(journaled);
  }).catch((e) => log("Gagal mencatat jurnal:", e.message)));

  // 3b) Nomor block tidak boleh mundur / terpakai ulang. Setiap start memajukan chain sedikitnya 1 block, dan setelah
  //     reset chain dimajukan melewati tinggi tertinggi yang pernah dilayani. Block penanda ini dicatat di jurnal.
  {
    const height = parseInt(await send("eth_blockNumber"), 16);
    const hw = readHighWater();
    const target = journal.meta ? Math.max(height + 1, hw + 1) : (hw > 0 ? hw + 1 : height);
    if (target > height) {
      for (let i = 0; i < target - height; i++) await send("evm_mine");
      await sync();
      log(`Block penanda dimajukan: #${height} -> #${target} (nomor block tidak pernah dipakai ulang).`);
    }
  }

  // 4) proxy publik: meneruskan request apa adanya, mencatat jurnal SEBELUM membalas klien
  const server = http.createServer((req, res) => {
    const cors = { "access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "POST, GET, OPTIONS" };
    if (req.method === "OPTIONS") { res.writeHead(204, cors); return res.end(); }
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", async () => {
      const body = Buffer.concat(chunks);
      let writes = false;
      let reqs = [];
      try {
        const parsed = JSON.parse(body.toString("utf8"));
        reqs = (Array.isArray(parsed) ? parsed : [parsed]).filter((r) => r && typeof r.method === "string");
        for (const r of reqs) {
          if (/^(eth_send|evm_|hardhat_)/.test(r.method)) writes = true;
          if (r.method === "eth_sendRawTransaction" && typeof r.params?.[0] === "string") rawByHash.set(keccak256(r.params[0]).toLowerCase(), r.params[0]);
        }
      } catch (_) {}

      // jurnal harus dapat ditulis sebelum transaksi/mining diteruskan
      if (writes) {
        const err = ensureJournalWritable();
        if (err) {
          trace(`DITOLAK: jurnal tidak dapat ditulis (${err})`);
          const out = reqs.map((r) => ({ jsonrpc: "2.0", id: r.id, error: { code: -32000, message: `HalalChain: jurnal chain tidak dapat ditulis (${err}). Transaksi ditolak agar chain dan jurnal tetap sinkron. Pindahkan folder proyek dari OneDrive atau hentikan sinkronisasi folder chain-data.` } }));
          res.writeHead(200, { "content-type": "application/json", ...cors });
          return res.end(JSON.stringify(Array.isArray(JSON.parse(body.toString("utf8"))) ? out : out[0]));
        }
      }

      // jejak: nonce transaksi yang datang dari MetaMask vs nonce yang diharapkan chain
      for (const r of reqs) {
        if (r.method !== "eth_sendRawTransaction" || typeof r.params?.[0] !== "string") continue;
        try {
          const t = Transaction.from(r.params[0]);
          const expect = parseInt(await send("eth_getTransactionCount", [t.from, "pending"]), 16);
          trace(`eth_sendRawTransaction dari ${t.from} nonce=${t.nonce} (chain mengharapkan ${expect}) ${t.nonce === expect ? "OK" : t.nonce > expect ? "<-- NONCE MetaMask LEBIH TINGGI dari chain" : "<-- nonce MetaMask lebih rendah"}`);
        } catch (e) { trace("eth_sendRawTransaction: gagal membaca raw tx: " + e.message); }
      }

      try {
        const up = await fetch(`http://${HOST}:${INTERNAL_PORT}`, { method: req.method, headers: { "content-type": "application/json" }, body: req.method === "POST" ? body : undefined });
        const text = await up.text();
        // jejak: apa yang ditanyakan MetaMask tentang nonce, dan jawaban chain
        try {
          const ask = reqs.filter((r) => r.method === "eth_getTransactionCount");
          if (ask.length) {
            const pr = JSON.parse(text); const list = Array.isArray(pr) ? pr : [pr];
            for (const r of ask) { const a = list.find((x) => x.id === r.id); trace(`eth_getTransactionCount(${r.params?.[0]}, ${r.params?.[1]}) -> ${a?.result ? parseInt(a.result, 16) : JSON.stringify(a?.error?.message)}`); }
          }
        } catch (_) {}
        if (writes) await sync();
        res.writeHead(up.status, { "content-type": "application/json", ...cors });
        res.end(text);
      } catch (e) {
        res.writeHead(502, cors); res.end(JSON.stringify({ jsonrpc: "2.0", id: null, error: { code: -32603, message: "Node internal tidak merespons: " + e.message } }));
      }
    });
  });
  server.on("error", (e) => { console.error(e.code === "EADDRINUSE" ? `Port ${PUBLIC_PORT} sudah dipakai. Tutup node Hardhat lain terlebih dahulu.` : e); process.exit(1); });
  server.listen(PUBLIC_PORT, HOST, () => {
    log(`SIAP. RPC untuk MetaMask/aplikasi: http://${HOST}:${PUBLIC_PORT} (Chain ID 31337)`);
    log("Data tersimpan otomatis di chain-data/. Tekan Ctrl+C untuk berhenti.");
  });

  setInterval(sync, 2000).unref(); // jaring pengaman (mis. block dari skrip yang langsung ke port internal)
  const stop = async () => { try { await sync(); } finally { process.exit(0); } };
  process.on("SIGINT", stop); process.on("SIGTERM", stop);
})().catch((e) => { console.error("\n[persistent-node] GAGAL:", e.message || e); process.exit(1); });