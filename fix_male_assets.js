/*
fix_male_assets.js
扫描 assets/clothes_m、assets/top_m、assets/bottom_m，把缺少的男性素材补进 items.js。
*/
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const ITEMS_PATH = path.join(ROOT, 'items.js');
const INDEX_PATH = path.join(ROOT, 'index.html');
const REPORT_PATH = path.join(ROOT, 'male_assets_fix_report.txt');
const IMAGE_EXTS = new Set(['.gif', '.png', '.jpg', '.jpeg', '.webp']);

const TARGETS = {
  clothes_m: { folder: path.join(ROOT, 'assets', 'clothes_m'), label: '男装' },
  top_m: { folder: path.join(ROOT, 'assets', 'top_m'), label: '男上衣' },
  bottom_m: { folder: path.join(ROOT, 'assets', 'bottom_m'), label: '男下装' }
};

function pad2(n) { return String(n).padStart(2, '0'); }
function timestamp() {
  const d = new Date();
  return d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate()) + '_' + pad2(d.getHours()) + pad2(d.getMinutes()) + pad2(d.getSeconds());
}
function readText(file) { return fs.readFileSync(file, 'utf8'); }
function writeText(file, text) { fs.writeFileSync(file, text, 'utf8'); }
function readItemsJs() {
  if (!fs.existsSync(ITEMS_PATH)) throw new Error('没有找到 items.js。请把本工具放在 index.html、items.js、assets 同一层。');
  let text = readText(ITEMS_PATH).trim();
  if (text.startsWith('window.ITEMS = ')) text = text.slice('window.ITEMS = '.length);
  if (text.endsWith(';')) text = text.slice(0, -1);
  return JSON.parse(text);
}
function writeItemsJs(data) { writeText(ITEMS_PATH, 'window.ITEMS = ' + JSON.stringify(data, null, 2) + ';\n'); }
function toWebPath(file) { return path.relative(ROOT, file).split(path.sep).join('/'); }
function lastNumber(value) {
  const base = path.basename(value, path.extname(value));
  const matched = base.match(/(\d{1,6})(?!.*\d)/);
  return matched ? Number(matched[1]) : null;
}
function sortKeyForSrc(src) {
  const base = path.basename(src).toLowerCase();
  if (base.startsWith('default')) return [-1, -1, src];
  const n = lastNumber(src);
  return n === null ? [999999, 999999, src] : [0, n, src];
}
function compareItem(a, b) {
  const ka = sortKeyForSrc(a.src || '');
  const kb = sortKeyForSrc(b.src || '');
  for (let i = 0; i < ka.length; i++) {
    if (ka[i] < kb[i]) return -1;
    if (ka[i] > kb[i]) return 1;
  }
  return 0;
}
function makeName(label, src) {
  const n = lastNumber(src);
  if (n !== null) return label + String(n).padStart(3, '0');
  const base = path.basename(src, path.extname(src)).replace(/[_\-]+/g, ' ').trim();
  return (label + '-' + base).slice(0, 16);
}
function scanFolder(folder) {
  if (!fs.existsSync(folder)) return [];
  return fs.readdirSync(folder)
    .filter(name => {
      const full = path.join(folder, name);
      return fs.statSync(full).isFile() && IMAGE_EXTS.has(path.extname(name).toLowerCase());
    })
    .map(name => path.join(folder, name))
    .sort((a, b) => {
      const ka = sortKeyForSrc(toWebPath(a));
      const kb = sortKeyForSrc(toWebPath(b));
      for (let i = 0; i < ka.length; i++) {
        if (ka[i] < kb[i]) return -1;
        if (ka[i] > kb[i]) return 1;
      }
      return 0;
    });
}
function bumpIndexCache(stamp, report) {
  if (!fs.existsSync(INDEX_PATH)) { report.push('没有找到 index.html，跳过缓存版本号修改。'); return; }
  const oldText = readText(INDEX_PATH);
  const newText = oldText.replace(/<script\s+src="items\.js(?:\?v=[^"]*)?"><\/script>/, `<script src="items.js?v=maleAssetsFix_${stamp}"></script>`);
  if (newText === oldText) { report.push('index.html 里没有找到标准 items.js 引用，跳过缓存版本号修改。'); return; }
  const backup = path.join(ROOT, `index_backup_${stamp}.html`);
  fs.copyFileSync(INDEX_PATH, backup);
  writeText(INDEX_PATH, newText);
  report.push(`已修改 index.html 的 items.js 缓存版本号。备份：${path.basename(backup)}`);
}
function main() {
  const stamp = timestamp();
  const report = [];
  report.push('男性素材补全报告');
  report.push('='.repeat(30));
  report.push(`执行时间：${new Date().toLocaleString()}`);
  report.push('');
  const data = readItemsJs();
  const backupItems = path.join(ROOT, `items_backup_${stamp}.js`);
  fs.copyFileSync(ITEMS_PATH, backupItems);
  report.push(`已备份旧 items.js：${path.basename(backupItems)}`);
  report.push('');
  let totalAdded = 0;
  for (const [category, cfg] of Object.entries(TARGETS)) {
    if (!Array.isArray(data[category])) data[category] = [];
    const beforeCount = data[category].length;
    const existing = new Set(data[category].filter(item => item && item.src).map(item => String(item.src).replace(/\\/g, '/')));
    const files = scanFolder(cfg.folder);
    const added = [];
    for (const file of files) {
      const src = toWebPath(file);
      if (!existing.has(src)) {
        data[category].push({ name: makeName(cfg.label, src), src });
        existing.add(src);
        added.push(src);
      }
    }
    const seen = new Set();
    const cleaned = [];
    for (const item of data[category]) {
      if (!item || !item.src) continue;
      const src = String(item.src).replace(/\\/g, '/');
      if (seen.has(src)) continue;
      seen.add(src);
      cleaned.push({ ...item, src });
    }
    cleaned.sort(compareItem);
    data[category] = cleaned;
    totalAdded += added.length;
    report.push(`[${category}] ${cfg.label}`);
    report.push(`扫描文件夹：${path.relative(ROOT, cfg.folder).split(path.sep).join('/')}`);
    report.push(`文件夹实际图片数：${files.length}`);
    report.push(`原清单数量：${beforeCount}`);
    report.push(`本次新增：${added.length}`);
    report.push(`补全后清单数量：${cleaned.length}`);
    if (added.length) {
      report.push('新增文件：');
      for (const src of added) report.push('  + ' + src);
    }
    report.push('');
  }
  writeItemsJs(data);
  bumpIndexCache(stamp, report);
  report.push('');
  report.push(`总新增素材：${totalAdded}`);
  report.push('');
  report.push('操作完成。请上传新的 index.html 和 items.js 到 GitHub。');
  const output = report.join('\n');
  writeText(REPORT_PATH, output);
  console.log(output);
  console.log('\n已完成。请查看 male_assets_fix_report.txt');
}
try { main(); }
catch (err) {
  console.error('\n执行失败：');
  console.error(err.message || err);
  console.error('\n请确认：');
  console.error('1. 本工具放在 index.html、items.js、assets 文件夹同一层');
  console.error('2. cmd 里可以运行 node -v');
  process.exitCode = 1;
}
