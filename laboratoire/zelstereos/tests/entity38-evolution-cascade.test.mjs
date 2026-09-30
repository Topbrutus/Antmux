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

function makeElement() {
  return { textContent: "", innerHTML: "", style: {}, appendChild() {} };
}

function makeContext() {
  const elements = new Map();
  const $ = id => {
    if (!elements.has(id)) elements.set(id, makeElement());
    return elements.get(id);
  };
  const context = {
    console, Map, Set, Object, Array, String, Number, Math, JSON, BigInt,
    TypeError, RangeError, Error, Promise, Date, performance,
    setTimeout, clearTimeout, $, document: { createElement: () => makeElement() },
  };
  vm.createContext(context);
  const prelude = `
    const ZEL_FORMULA_WAVE_MAX=2000;
    const ZEL_FORMULA_BATCH_DEFAULT=64;
    const ZEL_FORMULA_STATUSES=Object.freeze(['PASS','FAIL','DOMAIN','ERROR']);
    const zelFormulaBanks=new Map();
    let zelLastFormulaWave=null;
    let zelLastFormulaCascade=null;
    let zelCanonicalBankReady=null;
    let zelEvolutionBanksReady=null;
    let zelLastEvolutionCascade=null;
    const zelEvolutionFormulaRegistry=new Map();
    const zelEvolutionBankState=new Map();
    const zelEvolutionPromotionHistory=[];
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
    "zelEvolutionExactInt",
    "zelEvolutionLinearDefinition",
    "zelEvolutionSeedDefinitions",
    "zelRegisterEvolutionSeedBanks",
    "zelFormulaRunBranchLayer",
    "zelEvolutionBraidOrder",
    "zelEvolutionVerifyInverse",
    "zelFormulaRunEvolutionCascade",
    "zelEvolutionValidatePromotionEvidence",
    "zelEvolutionPromoteFormula",
    "zelEvolutionState",
    "zelEvolutionAudioStages",
  ].map(extractFunction).join("\n");
  vm.runInContext(prelude + functions, context);
  return context;
}

test("Entity 38 registers exact 9 / 12 / 12 verified Z Stereo seed banks", async () => {
  const ctx = makeContext();
  const ready = await ctx.zelRegisterEvolutionSeedBanks();
  assert.equal(ready.status, "VERIFIED");
  assert.deepEqual(Array.from(ready.banks, x => x.count), [9, 12, 12]);
  assert.deepEqual(Array.from(ready.route, x => x.fanout), [9, 12, 12]);
  const state = ctx.zelEvolutionState();
  assert.deepEqual(Array.from(state.banks, x => x.slots.length), [9, 12, 12]);
});

test("Entity 38 applies formulas at every branch: 1 -> 9 -> 108 -> 1296", async () => {
  const ctx = makeContext();
  const cascade = await ctx.zelFormulaRunEvolutionCascade({ cascade_id: "ENTITY38-COUNT", input: 7 });
  assert.equal(cascade.status, "PASS");
  assert.deepEqual(Array.from(cascade.actual_outputs), [9, 108, 1296]);
  assert.deepEqual(Array.from(cascade.fanout), [9, 12, 12]);
  assert.equal(cascade.total_formula_evaluations, 1413);
  assert.equal(cascade.summary.PASS, 1413);
  assert.equal(cascade.summary.FAIL, 0);
  assert.equal(cascade.summary.DOMAIN, 0);
  assert.equal(cascade.summary.ERROR, 0);
  assert.equal(cascade.final_nodes.length, 1296);
  assert.equal(new Set(cascade.final_nodes.map(x => x.branch_id)).size, 1296);
  assert.ok(cascade.final_nodes.every(x => x.path.length === 3));
  assert.ok(cascade.final_nodes.every(x => x.history.length === 3));
});

test("Entity 38 braid/inverse path reconstructs the original input for all 1296 outputs", async () => {
  const ctx = makeContext();
  const cascade = await ctx.zelFormulaRunEvolutionCascade({ cascade_id: "ENTITY38-INVERSE", input: "1234567890123456789012345" });
  const inverse = cascade.inverse_verification;
  assert.equal(cascade.status, "PASS");
  assert.equal(inverse.mode, "BRAID_LAST_TO_FIRST_THEN_Z3_Z2_Z1");
  assert.equal(inverse.root, "1234567890123456789012345");
  assert.equal(inverse.total, 1296);
  assert.equal(inverse.verified, 1296);
  assert.equal(inverse.failed, 0);
  assert.equal(inverse.ok, true);
  assert.equal(inverse.braid_pairs[0].first_branch, cascade.final_nodes[0].branch_id);
  assert.equal(inverse.braid_pairs[0].last_branch, cascade.final_nodes.at(-1).branch_id);
});

test("Entity 38 keeps huge integers exact across all three Z Stereo stages", async () => {
  const ctx = makeContext();
  const root = "90071992547409931234567890123456789";
  const cascade = await ctx.zelFormulaRunEvolutionCascade({ cascade_id: "ENTITY38-BIGINT", input: root });
  assert.equal(cascade.status, "PASS");
  assert.deepEqual(Array.from(cascade.actual_outputs), [9, 108, 1296]);
  assert.ok(cascade.final_nodes.every(x => typeof x.value === "string" && /^[+-]?\d+$/.test(x.value)));
  assert.equal(cascade.inverse_verification.root, root);
  assert.equal(cascade.inverse_verification.verified, 1296);
});

function promotedCandidate(id, delta = 97n) {
  const I = value => {
    if (typeof value === "bigint") return value;
    if (typeof value === "number" && Number.isSafeInteger(value)) return BigInt(value);
    if (typeof value === "string" && /^[+-]?\d+$/.test(value.trim())) return BigInt(value.trim());
    throw new RangeError("exact integer required");
  };
  return {
    formula_id: id,
    name: id,
    normalized_formula: `y=x+${delta}`,
    domain: "exact integer",
    provenance_ref: "TEST/MAX-ATTACK",
    accepts: input => { try { I(input); return true; } catch { return false; } },
    verify: () => ({ ok: I("123") + delta - delta === 123n, checks: ["roundtrip"] }),
    evaluate: input => ({ status: "PASS", value: (I(input) + delta).toString() }),
    inverse: value => (I(value) - delta).toString(),
  };
}

test("Entity 38 refuses unproven promotion and preserves fanout after a MAX_VERIFIED replacement", async () => {
  const ctx = makeContext();
  const candidate = promotedCandidate("MAX-001");
  await assert.rejects(
    ctx.zelEvolutionPromoteFormula({
      world_id: "ZSTEREO/Z1",
      candidate,
      evidence: { status: "PARTIAL", attacks_run: 10, attacks_passed: 10, counterexamples: 0, proof_ref: "TEST" },
    }),
    /MAX_VERIFIED/
  );
  const record = await ctx.zelEvolutionPromoteFormula({
    world_id: "ZSTEREO/Z1",
    candidate,
    evidence: { status: "MAX_VERIFIED", attacks_run: 100, attacks_passed: 100, counterexamples: 0, proof_ref: "TEST/MAX-100" },
  });
  assert.equal(record.world_id, "ZSTEREO/Z1");
  assert.equal(record.slot, 1);
  assert.equal(record.replaced_formula_id, "Z1-01");
  assert.equal(record.promoted_formula_id, "MAX-001");
  const cascade = await ctx.zelFormulaRunEvolutionCascade({ cascade_id: "ENTITY38-PROMOTED", input: 11 });
  assert.equal(cascade.status, "PASS");
  assert.deepEqual(Array.from(cascade.actual_outputs), [9, 108, 1296]);
  assert.equal(cascade.inverse_verification.verified, 1296);
});


test("Entity 38 sonic trace mirrors the full outward and inverse path", async () => {
  const ctx = makeContext();
  const cascade = await ctx.zelFormulaRunEvolutionCascade({ cascade_id: "ENTITY38-SONIC", input: 7 });
  const stages = ctx.zelEvolutionAudioStages(cascade);
  assert.equal(stages.length, 7);
  assert.deepEqual(Array.from(stages, x => x.value), [7, 9, 108, 1296, 108, 9, 7]);
  assert.deepEqual(Array.from(stages, x => x.complexity_ratio), [.05, .18, .55, 1, .55, .18, .05]);
  assert.match(stages[3].label, /1 296/);
  assert.equal(stages[6].status, "PASS");
});
