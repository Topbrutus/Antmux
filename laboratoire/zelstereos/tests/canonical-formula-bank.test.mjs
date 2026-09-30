import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../index.html", import.meta.url), "utf8");

function extractFunction(name) {
  const asyncMarker = `async function ${name}(`;
  const syncMarker = `function ${name}(`;
  const asyncStart = html.indexOf(asyncMarker);
  const start = asyncStart !== -1 ? asyncStart : html.indexOf(syncMarker);
  assert.notEqual(start, -1, `${name} not found`);

  const openParen = html.indexOf("(", start);
  let parenDepth = 0, quote = null, escaped = false, closeParen = -1;
  for (let i = openParen; i < html.length; i += 1) {
    const ch = html[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === "\\") escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === "'" || ch === '"' || ch === "`") { quote = ch; continue; }
    if (ch === "(") parenDepth += 1;
    if (ch === ")") {
      parenDepth -= 1;
      if (parenDepth === 0) { closeParen = i; break; }
    }
  }
  assert.notEqual(closeParen, -1, `${name} parameter list not closed`);
  const brace = html.indexOf("{", closeParen);
  let depth = 0; quote = null; escaped = false;
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

function loadDefinitions() {
  const context = { Object, Array, String, Number, Math, Set };
  vm.createContext(context);
  vm.runInContext(extractFunction("zelCanonicalMathDefinitions"), context);
  return context.zelCanonicalMathDefinitions();
}

test("canonical bank exposes exactly 25 non-fabricated core definitions", () => {
  const defs = loadDefinitions();
  assert.equal(defs.length, 25);
  assert.equal(new Set(defs.map(x => x.formula_id)).size, 25);
  assert.equal(defs[0].formula_id, "AM-001");
  assert.equal(defs.at(-1).formula_id, "AM-025");
});

test("every canonical formula carries provenance domain definition evaluator and verifier", () => {
  for (const def of loadDefinitions()) {
    assert.match(def.formula_id, /^AM-\d{3}$/);
    assert.equal(def.provenance_ref, "antmux_formula.py#verifier");
    assert.ok(def.domain.length > 0, def.formula_id + " missing domain");
    assert.ok(def.normalized_formula.length > 0, def.formula_id + " missing normalized formula");
    assert.equal(typeof def.evaluate, "function");
    assert.equal(typeof def.verify, "function");
  }
});

test("all 25 canonical verifiers pass independently", async () => {
  const failures = [];
  for (const def of loadDefinitions()) {
    const result = await def.verify();
    const ok = result === true || result?.ok === true;
    if (!ok) failures.push({ id: def.formula_id, result });
  }
  assert.deepEqual(failures, []);
});

test("phase index enforces exact integer domain and periodic invariant", async () => {
  const def = loadDefinitions().find(x => x.formula_id === "AM-022");
  assert.equal(def.accepts({ t: 2, b: 5, o: 11 }), true);
  assert.equal(def.accepts({ t: 2.5, b: 5, o: 11 }), false);
  assert.equal(def.accepts({ t: "9007199254740993123456789", b: "1", o: "-2" }), true);
  const a = await def.evaluate({ t: 2, b: 5, o: 11 });
  const b = await def.evaluate({ t: 5, b: 12, o: 24 });
  assert.equal(a.value, b.value);
  assert.ok(a.value >= 0 && a.value < 273);
});

test("AM-022 regression: exact BigInt arithmetic survives the previously broken large-integer case", async () => {
  const def = loadDefinitions().find(x => x.formula_id === "AM-022");
  const input = {
    t: 9007199254739001,
    b: 9007199254738123,
    o: -9007199254737557,
  };
  const shifted = { t: input.t + 3, b: input.b + 7, o: input.o + 13 };
  const first = await def.evaluate(input);
  const second = await def.evaluate(shifted);
  assert.equal(first.value, 132);
  assert.equal(second.value, 132);
  assert.equal(first.value, second.value);
  assert.equal(first.trace[0].exact_mod, "132");
});

test("AM-022 accepts arbitrary exact decimal integer strings without Number precision loss", async () => {
  const def = loadDefinitions().find(x => x.formula_id === "AM-022");
  const input = {
    t: "9007199254740993123456789",
    b: "-9007199254740992123456789",
    o: "1234567890123456789012345",
  };
  const shifted = {
    t: (BigInt(input.t) + 3n).toString(),
    b: (BigInt(input.b) + 7n).toString(),
    o: (BigInt(input.o) + 13n).toString(),
  };
  const first = await def.evaluate(input);
  const second = await def.evaluate(shifted);
  assert.equal(first.value, second.value);
  assert.ok(first.value >= 0 && first.value < 273);
});

test("Z7^4 address exhaustively verifies 2401 unique addresses and rejects bad coordinates", async () => {
  const def = loadDefinitions().find(x => x.formula_id === "AM-023");
  const verification = await def.verify();
  assert.equal(verification.ok, true);
  assert.deepEqual(Array.from(verification.checks), [2401, 0, 2400]);
  assert.equal(def.accepts({ a: 6, b: 6, c: 6, d: 6 }), true);
  assert.equal(def.accepts({ a: 7, b: 0, c: 0, d: 0 }), false);
  const out = await def.evaluate({ a: 6, b: 6, c: 6, d: 6 });
  assert.equal(out.value, 2400);
});

test("lemniscate verifier preserves x-y periodicity and z progression", async () => {
  const def = loadDefinitions().find(x => x.formula_id === "AM-024");
  assert.equal((await def.verify()).ok, true);
  assert.equal(def.accepts({ n: -547, alpha: 0.75 }), true);
  assert.equal(def.accepts({ n: 1.2, alpha: 0.75 }), false);
});

test("canonical bank is registered into MATH/GEOMETRY through the verified gate", () => {
  assert.match(html, /zelFormulaRegisterBank\('MATH\/GEOMETRY',zelCanonicalMathDefinitions\(\),\{batch_size:64\}\)/);
  assert.match(html, /zelRegisterCanonicalMathBank\(\)\.catch\(err=>console\.error\('ZEL_CANONICAL_BANK_REJECTED',err\)\)/);
});
