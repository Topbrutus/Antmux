import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../index.html", import.meta.url), "utf8");

test("calculation journal panel and copy button are present", () => {
  assert.match(html, /06 · JOURNAL DE CALCUL/);
  assert.match(html, /id="calcJournalLines"/);
  assert.match(html, /id="calcCopy"/);
  assert.match(html, /⧉ COPIER/);
});

test("journal resets on every new AI calculation", () => {
  assert.match(
    html,
    /const traceId=String\(spec\.trace_id[\s\S]*?zelCalcBegin\(\{[\s\S]*?traceId,[\s\S]*?formula:formula\.normalized_formula/
  );
  assert.match(html, /zelCurrentCalculation=\{[\s\S]*?lines:\[\]/);
});

test("each stage is appended live and final result is persisted", () => {
  assert.match(html, /zelCalcAppend\(i,step,exact,\{decimal,complexity_ratio:complexityRatio,sfx_id:state\.sfx_id\}\)/);
  assert.match(html, /zelCalcFinish\(rendered\.length\?rendered\[rendered\.length-1\]\.exact:null\)/);
});

test("persistent log is bounded to 100 traces", () => {
  assert.match(html, /const ZEL_CALC_LOG_MAX=100;/);
  assert.match(html, /slice\(-ZEL_CALC_LOG_MAX\)/);
  assert.match(html, /localStorage\.setItem\(ZEL_CALC_LOG_KEY,JSON\.stringify\(safe\)\)/);
});

test("copy payload includes formula, trace id, lines and result", () => {
  assert.match(html, /out\.push\('TRACE_ID: '\+c\.trace_id\)/);
  assert.match(html, /out\.push\('FORMULE: '\+c\.formula\)/);
  assert.match(html, /c\.lines\.forEach\(\(line,i\)=>out\.push/);
  assert.match(html, /out\.push\('','RÉSULTAT: '\+c\.result\)/);
  assert.match(html, /navigator\.clipboard\.writeText\(text\)/);
});

test("public AI exposes current journal and stored calculation log", () => {
  assert.match(html, /calculationLog:\(\)=>zelAiClone\(zelCalcReadLog\(\)\)/);
  assert.match(html, /currentCalculation:\(\)=>zelCurrentCalculation\?zelAiClone\(zelCurrentCalculation\):null/);
  assert.match(html, /copyCurrentCalculation:zelCalcCopyCurrent/);
});

test("stage logger accepts explicit operation or expression metadata", () => {
  assert.match(html, /step\?\.operation\|\|step\?\.expression\|\|step\?\.detail/);
});
