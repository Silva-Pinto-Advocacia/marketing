// node render_reel.js <timeline.json> <mode: preview|frames> [times]
const fs = require('fs'); const path = require('path');
// playwright may live next to the project, in the cwd, or in the global node modules: try each
const pwCandidates = ['playwright', path.join(process.cwd(), 'node_modules', 'playwright'), '/opt/node22/lib/node_modules/playwright', '/usr/lib/node_modules/playwright'];
let chromium = null; for (const c of pwCandidates) { try { chromium = require(c).chromium; break; } catch (e) {} }
if (!chromium) { console.error('playwright not found: npm i playwright@1.56.1 in the cwd'); process.exit(1); }
const tlPath = process.argv[2]; const mode = process.argv[3] || 'preview';
const tl = JSON.parse(fs.readFileSync(tlPath, 'utf8'));
const ASSETS = 'file://' + path.resolve(__dirname, '..', 'assets');
const html = fs.readFileSync(path.join(__dirname, 'comp_reel.html'), 'utf8').replace('__TIMELINE__', JSON.stringify(tl)).split('__ASSETS__').join(ASSETS);
// the built page lives in the project dir so relative frame paths (src_frames/f00001.jpg) resolve
const projectDir = path.dirname(path.resolve(tlPath));
const built = path.join(projectDir, 'comp_reel.built.html'); fs.writeFileSync(built, html);
(async () => {
  const b = await chromium.launch({ headless: true, executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox', '--font-render-hinting=none'] });
  const page = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + built); await page.evaluate(() => document.fonts.ready); await page.waitForTimeout(300);
  if (mode === 'preview') {
    const dir = path.join(projectDir, 'preview'); fs.mkdirSync(dir, { recursive: true });
    const times = (process.argv[4] || '0.8,3,6,9').split(',').map(Number);
    for (const t of times) { await page.evaluate(t => window.seek(t), t); await page.screenshot({ path: path.join(dir, `r_${t.toFixed(2)}.png`) }); }
    console.log('preview ok');
  } else {
    const dir = tl.outFrames; const range = process.argv[4] ? process.argv[4].split(',').map(Number) : null;
    if (!range) { fs.rmSync(dir, { recursive: true, force: true }); } fs.mkdirSync(dir, { recursive: true });
    const n = Math.ceil(tl.total * tl.fps); const t0 = Date.now();
    const i0 = range ? Math.floor(range[0] * tl.fps) : 0, i1 = range ? Math.min(n, Math.ceil(range[1] * tl.fps)) : n;
    for (let i = i0; i < i1; i++) { await page.evaluate(t => window.seek(t), i / tl.fps); await page.screenshot({ path: path.join(dir, `o${String(i).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 94 });
      if (i % 240 === 0) console.log(`frame ${i}/${n} ${(Date.now() - t0) / 1000}s`); }
    console.log('frames done', n, (Date.now() - t0) / 1000 + 's');
  }
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
