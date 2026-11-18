// Menghapus data chain persisten (jurnal dicadangkan). Jalankan: npm run chain:reset
// high-water.json SENGAJA dipertahankan: nomor block chain baru akan dimulai di atas tinggi terakhir chain lama,
// sehingga MetaMask tidak pernah melihat nomor block "mundur" atau terpakai ulang.
const fs = require("fs");
const path = require("path");
const dir = process.env.HC_CHAIN_DATA || path.join(__dirname, "..", "chain-data");
const journal = path.join(dir, "journal.jsonl");
if (!fs.existsSync(journal)) { console.log("Tidak ada data chain untuk direset."); process.exit(0); }
const blocks = fs.readFileSync(journal, "utf8").split("\n").filter((l) => l.includes('"t":"block"')).length;
const hwFile = path.join(dir, "high-water.json");
let hw = 0; try { hw = Number(JSON.parse(fs.readFileSync(hwFile, "utf8")).height) || 0; } catch (_) {}
fs.writeFileSync(hwFile, JSON.stringify({ height: Math.max(hw, blocks), updatedAt: new Date().toISOString() }));
const backup = path.join(dir, `journal-backup-${new Date().toISOString().replace(/[:.]/g, "-")}.jsonl`);
fs.renameSync(journal, backup);
console.log("Data chain direset. Cadangan:", path.relative(process.cwd(), backup));
console.log(`Chain baru akan dimulai di atas block #${Math.max(hw, blocks)} (high-water dipertahankan).`);