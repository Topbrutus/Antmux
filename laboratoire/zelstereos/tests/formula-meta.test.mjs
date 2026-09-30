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
  assert.notEqual(brace, -1, `${name} opening brace not found`);
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
    if (ch === "'" || ch === '"' || ch === "`") {
      quote = ch;
      continue;
    }
    if (ch === "{") depth += 1;
    if (ch === "}") {
      depth -= 1;
      if (depth === 0) return html.slice(start, i + 1);
    }
  }
  throw new Error(`${name} closing brace not found`);
}

function makeFormulaContext() {
  const context = {
    JSON,
    Number,
    String,
    Object,
    TypeError,
    aiSelectedFormula: null
  };
  vm.createContext(context);
  vm.runInContext(
    [
      extractFunction("zelAiClone"),
      extractFunction("zelAiFormulaSummary"),
      extractFunction("zelAiSelectFormula"),
      extractFunction("zelAiSelectedFormula")
    ].join("\n"),
    context
  );
  return context;
}

function runSelfTest(renderedState) {
  const context = {
    JSON,
    Number,
    Object,
    Date,
    counts: [1, 3, 9, 36, 9, 3, 1],
    lastRenderedPublicState: renderedState,
    zelAiDiagnostics: () => ({ source: "TEST" })
  };
  vm.createContext(context);
  vm.runInContext(extractFunction("zelAiSelfTest"), context);
  return context.zelAiSelfTest();
}

test("formula selection preserves integer k", () => {
  const ctx = makeFormulaContext();
  const selected = ctx.zelAiSelectFormula({
    selector: "F1",
    formula_id: "F1",
    name: "Pell rank",
    status: "TEST",
    category: "BREAK_TEST",
    normalized_formula: "z_P(21^k)=4*21^(k-1)",
    k: 1
  });
  assert.equal(selected.k, 1);
  assert.equal(ctx.zelAiSelectedFormula().k, 1);
});

test("formula selection rejects invalid k instead of silently dropping it", () => {
  const ctx = makeFormulaContext();
  assert.throws(() => ctx.zelAiSelectFormula({
    formula_id: "F1",
    normalized_formula: "z_P(21^k)=4*21^(k-1)",
    k: 1.5
  }), /formula k must be a non-negative integer/);
});

test("AI stage payload carries k into formula_meta", () => {
  assert.match(html, /formula_meta:\{[\s\S]*?k:formula\.k\?\?null,[\s\S]*?source_commit_short:'AI-RECTO'/);
});

test("F1 self-test now distinguishes missing k from a real contradiction", () => {
  const missing = runSelfTest({
    mode: "PUBLIC_SAFE",
    read_only: true,
    status: "LIVE",
    formula_meta: { formula_id: "F1", value: 12 },
    global_error: { exact: "0", decimal: 0 }
  });
  const missingF1 = missing.checks.find(item => item.name === "f1_rank_formula");
  assert.equal(missingF1.ok, false);
  assert.equal(missingF1.detail.k, null);
  assert.equal(missingF1.detail.expected, null);

  const contradiction = runSelfTest({
    mode: "PUBLIC_SAFE",
    read_only: true,
    status: "LIVE",
    formula_meta: { formula_id: "F1", k: 1, value: 12 },
    global_error: { exact: "0", decimal: 0 }
  });
  const brokenF1 = contradiction.checks.find(item => item.name === "f1_rank_formula");
  assert.equal(brokenF1.ok, false);
  assert.equal(brokenF1.detail.k, 1);
  assert.equal(brokenF1.detail.expected, 4);
  assert.equal(brokenF1.detail.actual, 12);

  const control = runSelfTest({
    mode: "PUBLIC_SAFE",
    read_only: true,
    status: "LIVE",
    formula_meta: { formula_id: "F1", k: 3, value: 1764 },
    global_error: { exact: "0", decimal: 0 }
  });
  const passingF1 = control.checks.find(item => item.name === "f1_rank_formula");
  assert.equal(passingF1.ok, true);
  assert.equal(passingF1.detail.expected, 1764);
});
