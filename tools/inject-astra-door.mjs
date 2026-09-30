import fs from "node:fs";

const target = process.argv[2] || "_site/index.html";
const marker = "<body>";
const id = 'id="astra-heart-door"';
const heart = '<a id="astra-heart-door" href="/astra-door/" aria-label="Ouvrir la porte Astra" title="ASTRA" style="position:fixed;top:16px;left:16px;z-index:100000;width:46px;height:46px;display:grid;place-items:center;border:1px solid rgba(243,223,154,.58);border-radius:50%;background:rgba(4,4,4,.88);color:#f3df9a;text-decoration:none;font:700 23px/1 Georgia,serif;box-shadow:0 4px 24px rgba(0,0,0,.42),inset 0 0 18px rgba(216,180,95,.08);backdrop-filter:blur(10px)" data-public-visual-door="true">♥</a>';

const html = fs.readFileSync(target, "utf8");

if (html.includes(id)) {
  console.log("ASTRA heart already present:", target);
  process.exit(0);
}

if (!html.includes(marker)) {
  console.error("ASTRA heart injection failed: <body> marker not found in", target);
  process.exit(1);
}

const next = html.replace(marker, marker + heart);
fs.writeFileSync(target, next, "utf8");

const count = (next.match(/astra-heart-door/g) || []).length;
if (count !== 1) {
  console.error("ASTRA heart injection failed: expected exactly one marker, got", count);
  process.exit(1);
}

console.log("ASTRA heart injected:", target);
