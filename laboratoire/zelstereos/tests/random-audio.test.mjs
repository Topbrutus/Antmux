import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../index.html", import.meta.url), "utf8");

function extractFunction(name) {
  const marker = `function ${name}(`;
  const start = html.indexOf(marker);
  assert.notEqual(start, -1, `${name} not found`);
  const brace = html.indexOf("{", start);
  let depth = 0;
  let quote = null;
  let escaped = false;
  for (let i = brace; i < html.length; i += 1) {
    const ch = html[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === "\\") escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === "'" || ch === '"' || ch === "`") { quote = ch; continue; }
    if (ch === "{") depth += 1;
    if (ch === "}") {
      depth -= 1;
      if (depth === 0) return html.slice(start, i + 1);
    }
  }
  throw new Error(`${name} closing brace not found`);
}

function makeContext() {
  let seed = 0x12345678;
  const crypto = {
    getRandomValues(array) {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      array[0] = seed;
      return array;
    }
  };
  const context = {
    Math, Number, String, Array, Object, RangeError, TypeError, Uint32Array,
    crypto,
    audioCtx: null,
    ZEL_SFX_IDS: Array.from({length:36},(_,i)=>"SFX"+String(i+1).padStart(2,"0")),
    aiSfxStageMap: ["SFX06","SFX03","SFX08","SFX24","SFX12","SFX30","SFX35"],
    aiSfxRandomMode: true,
    zelLastRandomSfxMap: ["SFX06","SFX03","SFX08","SFX24","SFX12","SFX30","SFX35"],
    zelSfxWarm: () => Promise.resolve([]),
    clamp01: v => Math.max(0,Math.min(1,v))
  };
  vm.createContext(context);
  vm.runInContext([
    extractFunction("zelAiRandomUnit"),
    extractFunction("zelAiSecureRandomInt"),
    extractFunction("zelAiValidSfxId"),
    extractFunction("zelAiRandomSfxMap"),
    extractFunction("zelAiUseRandomSfx"),
    extractFunction("zelAiSetSfxMap"),
    extractFunction("zelAiSfxMap"),
    extractFunction("zelAiSfxMode"),
    extractFunction("zelAiComplexityRatio")
  ].join("\n"), context);
  return context;
}

test("random A-to-Z mode selects seven unique SFX from all 36", () => {
  const ctx = makeContext();
  const map = ctx.zelAiUseRandomSfx();
  assert.equal(ctx.zelAiSfxMode(), "RANDOM_A_Z");
  assert.equal(map.length, 7);
  assert.equal(new Set(map).size, 7);
  assert.ok(map.every(id => /^SFX(?:0[1-9]|[12][0-9]|3[0-6])$/.test(id)));
});

test("random mode prevents the same SFX sticking to the same stage", () => {
  const ctx = makeContext();
  const first = ctx.zelAiUseRandomSfx();
  const second = ctx.zelAiRandomSfxMap();
  assert.equal(second.length, 7);
  for (let i = 0; i < 7; i += 1) assert.notEqual(second[i], first[i]);
});

test("explicit SFX map remains available as a deterministic diagnostic override", () => {
  const ctx = makeContext();
  const fixed = ["SFX01","SFX02","SFX03","SFX04","SFX05","SFX06","SFX07"];
  assert.deepEqual(Array.from(ctx.zelAiSetSfxMap(fixed)), fixed);
  assert.equal(ctx.zelAiSfxMode(), "FIXED");
});

test("complexity controls sonic effort independently from SFX identity", () => {
  const ctx = makeContext();
  assert.equal(ctx.zelAiComplexityRatio({complexity_ratio:0.82},{},{exec_ms:null}),0.82);
  assert.equal(ctx.zelAiComplexityRatio({work_ratio:0.25},{},{exec_ms:null}),0.25);
  assert.equal(ctx.zelAiComplexityRatio({}, {}, {exec_ms:10000}),1);
  assert.equal(ctx.zelAiComplexityRatio({}, {}, {exec_ms:null}),null);
});

test("default AI calculation and live cycle both use random mode", () => {
  assert.match(html,/else \{aiSfxRandomMode=true;zelAiRandomSfxMap\(\);\}/);
  assert.match(html,/stageIndex===0&&aiSfxRandomMode&&!aiPresentationActive\)zelAiRandomSfxMap\(\)/);
  assert.match(html,/const sonicDt=complexity===null\?stageDt:Math\.max\(stageDt,\.65\+\(complexity\*3\.35\)\)/);
});
