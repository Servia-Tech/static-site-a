#!/usr/bin/env node
// Submit every URL in the live sitemap.xml to IndexNow (Bing, Yandex, Seznam, Naver and others share submissions).
// Node 18+, no dependencies. Run only after the site is deployed:
//   node indexnow-ping.mjs            # submit
//   node indexnow-ping.mjs --dry-run  # list what would be sent
// The key file https://calcnate.com/<KEY>.txt must be live first.
const HOST = 'calcnate.com';
const KEY = 'd011935629dad9143fc3cbe52682655b';
const KEY_LOCATION = `https://${HOST}/${KEY}.txt`;
const SITEMAP = `https://${HOST}/sitemap.xml`;
const ENDPOINT = 'https://api.indexnow.org/indexnow';
const dryRun = process.argv.includes('--dry-run');

const get = async (url) => {
  const r = await fetch(url, { headers: { 'User-Agent': 'indexnow-ping/1.0' } });
  if (!r.ok) throw new Error(`GET ${url}: HTTP ${r.status}`);
  return r.text();
};

const xml = await get(SITEMAP);
const urls = [...xml.matchAll(/<loc>\s*(.*?)\s*<\/loc>/g)].map((m) => m[1]).filter((u) => u.startsWith(`https://${HOST}/`));
if (!urls.length) { console.error('No URLs found in sitemap'); process.exit(1); }
const liveKey = (await get(KEY_LOCATION)).trim();
if (liveKey !== KEY) { console.error(`Key file at ${KEY_LOCATION} does not match KEY`); process.exit(1); }
if (dryRun) { console.log(urls.join('\n')); console.log(`Dry run: ${urls.length} URLs would be submitted`); process.exit(0); }

let failed = false;
for (let i = 0; i < urls.length; i += 10000) {
  const urlList = urls.slice(i, i + 10000);
  const r = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify({ host: HOST, key: KEY, keyLocation: KEY_LOCATION, urlList }),
  });
  const body = (await r.text()).slice(0, 300);
  console.log(`IndexNow: HTTP ${r.status} ${r.statusText} for ${urlList.length} URLs${body ? ' - ' + body : ''}`);
  if (r.status !== 200 && r.status !== 202) failed = true;
}
process.exit(failed ? 1 : 0);
