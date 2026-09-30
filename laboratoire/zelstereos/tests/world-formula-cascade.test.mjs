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
  const brace = html.indexOf("{", start);
  let depth = 0, quote = null, escaped = false;
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

function makeElement() {
  return {
    textContent: "",
    innerHTML: "",
    style: {},
    appendChild() {},
  };
}

function makeContext() {
  const elements = new Map();
  const $ = id => {
    if (!elements.has(id)) elements.set(id, makeElement());
    return elements.get(id);
  };
  const context = {
    console,
    Map, Set, Object, Array, String, Number, Math, JSON,
    TypeError, RangeError, Error, Promise, Date,
    performance,
    setTimeout,
    clearTimeout,
    $,
    document: { createElement: () => makeElement() },
  };
  vm.createContext(context);
  const prelude = `
    const ZEL_FORMULA_WAVE_MAX=2000;
    const ZEL_FORMULA_BATCH_DEFAULT=64;
    const ZEL_FORMULA_STATUSES=Object.freeze(['PASS','FAIL','DOMAIN','ERROR']);
    const zelFormulaBanks=new Map();
    let zelLastFormulaWave=null;
    let zelLastFormulaCascade=null;
  `;
  const functions = [
    "zelFormulaSafeValue",
    "zelFormulaSummary",
    "zelFormulaNormalizeVerification",
    "zelFormulaQualifyOne",
    "zelFormulaQualifyDefinitions",
    "zelFormulaRegisterBank",
    "zelFormulaBankInfo",
    "zelFormulaNormalizeResult",
    "zelFormulaRunOne",
    "zelSwarmSummary",
    "zelSwarmRender",
    "zelFormulaRunWave",
    "zelFormulaValidatePortal",
    "zelFormulaRunCascade",
  ].map(extractFunction).join("\n");
  vm.runInContext(prelude + functions, context);
  return context;
}

function qualifiedFormula(id, {
  verify = () => true,
  accepts = () => true,
  evaluate = input => ({ status: "PASS", value: input }),
} = {}) {
  return {
    formula_id: id,
    name: id,
    normalized_formula: `${id}(x)`,
    domain: "x ∈ finite JSON values",
    provenance_ref: "TEST/SYNTHETIC-CAPACITY-ONLY",
    verify,
    accepts,
    evaluate,
  };
}

test("formula metadata is mandatory before qualification", () => {
  const ctx = makeContext();
  assert.throws(
    () => ctx.zelFormulaSummary({
      formula_id: "BAD",
      normalized_formula: "x",
      domain: "numbers",
      evaluate: x => x,
      verify: () => true,
    }),
    /provenance_ref required/
  );
  assert.throws(
    () => ctx.zelFormulaSummary({
      formula_id: "BAD2",
      normalized_formula: "x",
      provenance_ref: "TEST",
      evaluate: x => x,
      verify: () => true,
    }),
    /formula domain required/
  );
});

test("a bank is rejected if even one formula fails verification", async () => {
  const ctx = makeContext();
  const formulas = [
    qualifiedFormula("GOOD"),
    qualifiedFormula("BAD", { verify: () => ({ ok: false, reason: "counterexample" }) }),
  ];
  await assert.rejects(
    ctx.zelFormulaRegisterBank("MATH/TEST", formulas),
    /FORMULA_BANK_QUALIFICATION_FAILED 1\/2 \[BAD\]/
  );
  assert.equal(ctx.zelFormulaBankInfo().length, 0);
});

test("2000 synthetic verified jobs fit in one deterministic wave", async () => {
  const ctx = makeContext();
  const formulas = Array.from({ length: 2000 }, (_, i) =>
    qualifiedFormula("SYN-" + String(i + 1).padStart(4, "0"), {
      evaluate: input => ({ status: "PASS", value: Number(input) + i }),
    })
  );
  const registered = await ctx.zelFormulaRegisterBank("MATH/CAPACITY", formulas, { batch_size: 128 });
  assert.equal(registered.status, "VERIFIED");
  assert.equal(registered.count, 2000);
  const wave = await ctx.zelFormulaRunWave({
    world_id: "MATH/CAPACITY",
    wave_id: "CAPACITY-2000",
    input: 7,
    batch_size: 128,
  });
  assert.equal(wave.deterministic, true);
  assert.equal(wave.summary.total, 2000);
  assert.equal(wave.summary.PASS, 2000);
  assert.equal(wave.summary.FAIL, 0);
  assert.equal(wave.summary.DOMAIN, 0);
  assert.equal(wave.summary.ERROR, 0);
  assert.equal(wave.results[0].value, 7);
  assert.equal(wave.results[1999].value, 2006);
});

test("wave keeps PASS FAIL DOMAIN and ERROR distinct", async () => {
  const ctx = makeContext();
  await ctx.zelFormulaRegisterBank("MATH/STATUS", [
    qualifiedFormula("PASS", { evaluate: () => ({ status: "PASS", value: 1 }) }),
    qualifiedFormula("FAIL", { evaluate: () => ({ status: "FAIL", value: 2, expected: 3 }) }),
    qualifiedFormula("DOMAIN", { accepts: () => false }),
    qualifiedFormula("ERROR", { evaluate: () => { throw new Error("boom"); } }),
  ]);
  const wave = await ctx.zelFormulaRunWave({ world_id: "MATH/STATUS", input: 1 });
  assert.deepEqual(
    {
      PASS: wave.summary.PASS,
      FAIL: wave.summary.FAIL,
      DOMAIN: wave.summary.DOMAIN,
      ERROR: wave.summary.ERROR,
      total: wave.summary.total,
    },
    { PASS: 1, FAIL: 1, DOMAIN: 1, ERROR: 1, total: 4 }
  );
});

test("world opening is blocked without an explicit portal contract", async () => {
  const ctx = makeContext();
  await ctx.zelFormulaRegisterBank("WORLD/A", [qualifiedFormula("A1")]);
  await ctx.zelFormulaRegisterBank("WORLD/B", [qualifiedFormula("B1")]);
  const cascade = await ctx.zelFormulaRunCascade({
    cascade_id: "BLOCKED",
    input: 5,
    layers: [{ world_id: "WORLD/A" }, { world_id: "WORLD/B" }],
  });
  assert.equal(cascade.status, "BLOCKED");
  assert.equal(cascade.reason, "NO_PORTAL_CONTRACT");
  assert.equal(cascade.waves.length, 1);
});

test("valid portal contract opens the next verified world layer", async () => {
  const ctx = makeContext();
  await ctx.zelFormulaRegisterBank("WORLD/A", [
    qualifiedFormula("A1", { evaluate: x => ({ status: "PASS", value: Number(x) + 1 }) }),
  ]);
  await ctx.zelFormulaRegisterBank("WORLD/B", [
    qualifiedFormula("B1", { evaluate: x => ({ status: "PASS", value: Array.isArray(x) ? x.length : -1 }) }),
  ]);
  const cascade = await ctx.zelFormulaRunCascade({
    cascade_id: "OPEN",
    input: 5,
    layers: [
      {
        world_id: "WORLD/A",
        portal_contract: {
          id: "PORTAL-A-B",
          from: "WORLD/A",
          to: "WORLD/B",
          transform: "PASS-VALUES-V1",
          proof: "ROUNDTRIP-TEST",
        },
      },
      { world_id: "WORLD/B" },
    ],
  });
  assert.equal(cascade.status, "PASS");
  assert.deepEqual(Array.from(cascade.route), ["WORLD/A", "WORLD/B"]);
  assert.equal(cascade.waves.length, 2);
  assert.equal(cascade.openings[0].open, true);
  assert.equal(cascade.waves[1].results[0].value, 1);
});

test("direct unqualified formula execution is disabled", () => {
  assert.match(html, /DIRECT_FORMULA_EXECUTION_DISABLED_REGISTER_VERIFIED_BANK_FIRST/);
});
