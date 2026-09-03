#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REQUIRED_STATUS = Object.freeze({
  science_baseline: 'GREEN',
  genesis003_c041_c060: 'COMPLETE_VALIDATED',
  experiment_selection_performed: 'true',
  selected_experiment_status: 'PLANNED_NOT_EXECUTED',
  hypothesis_selection_performed: 'false',
  hypothesis_ranking_produced: 'false',
  uncertainty_promotion_performed: 'false',
  probabilities_produced: 'false',
  evidence_ledger_auto_promotion: 'false',
  GENESIS_AUDIT_FAILED: '0'
});

function fail(message) {
  throw new Error(message);
}

export function extractWhitelistedGenesisStatus(text) {
  if (typeof text !== 'string' || text.length === 0) fail('Source Genesis absente.');
  const found = new Map();
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(/^([A-Za-z0-9_]+)=(.*)$/);
    if (!match) continue;
    const [, key, value] = match;
    if (!(key in REQUIRED_STATUS)) continue;
    if (found.has(key) && found.get(key) !== value) fail(`Statut Genesis contradictoire: ${key}.`);
    found.set(key, value);
  }

  for (const [key, expected] of Object.entries(REQUIRED_STATUS)) {
    if (!found.has(key)) fail(`Statut Genesis requis absent: ${key}.`);
    if (found.get(key) !== expected) fail(`Statut Genesis refusé: ${key}.`);
  }

  return Object.fromEntries(Object.keys(REQUIRED_STATUS).map(key => [key, found.get(key)]));
}

export function buildBridgeInputFromWhitelistedStatus(status, options = {}) {
  for (const [key, expected] of Object.entries(REQUIRED_STATUS)) {
    if (status?.[key] !== expected) fail(`Projection refusée: ${key}.`);
  }

  const observedAt = new Date(options.observedAt ?? Date.now());
  if (Number.isNaN(observedAt.getTime())) fail('Horodatage d’observation invalide.');
  const receivedAt = new Date(options.receivedAt ?? observedAt);
  if (Number.isNaN(receivedAt.getTime())) fail('Horodatage bridge invalide.');

  return {
    bridge_input_version: '1.0.0',
    publication_intent: 'SERVER_SIDE_PUBLIC_READ_ONLY_BRIDGE',
    bridge_received_at: receivedAt.toISOString(),
    source_observed_at: observedAt.toISOString(),
    max_age_seconds: 300,
    source_attestation: {
      source_kind: 'PRIVATE_GENESIS_PUBLIC_PROJECTION',
      source_identity: 'OPAQUE_PUBLIC_ATTESTATION',
      source_state: 'C041_C060_COMPLETE_VALIDATED',
      selected_experiment_status: status.selected_experiment_status,
      read_capability: 'READ_ONLY',
      write_capability: 'NONE',
      adapter_only: true
    },
    transport: {
      server_side_pull: true,
      public_endpoint_only: true,
      fail_closed: true,
      snapshot_fallback_available: true,
      browser_credentials_present: false,
      private_browser_request: false
    },
    public_payload: {
      identity: {
        seed_label: 'Genesis',
        root_status: 'PRESERVED_AT_SOURCE_VALIDATION',
        root_version: 'GENESIS-003-C060-PUBLIC-ATTESTATION-v1',
        continuity_policy: 'PRIVATE_ROOT_NOT_EXPOSED; PUBLIC_PROJECTION_ONLY'
      },
      publication_gates: {
        current_gate: 'LIVE_READ_ONLY_BRIDGE_READY_NOT_DEPLOYED',
        recommended_next_step: 'AUTHORIZE_CONTROLLED_PUBLIC_READ_ONLY_DEPLOYMENT',
        gates: [
          { id: 'contract-v2', label: 'Contrat public v2', status: 'PASSED' },
          { id: 'adapter', label: 'Genesis Public Adapter', status: 'PASSED' },
          { id: 'snapshot', label: 'Snapshot public figé', status: 'PASSED' },
          { id: 'live-read-only', label: 'Bridge serveur lecture seule', status: 'PASSED' }
        ]
      },
      metrics: [
        { id: 'genesis003-c041-c060', label: 'GENESIS-003 C041–C060', value: 'COMPLETE_VALIDATED', status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST' },
        { id: 'selected-experiment-status', label: 'État du test sélectionné', value: status.selected_experiment_status, status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST' },
        { id: 'hypothesis-selection', label: 'Hypothèse sélectionnée', value: false, status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST' },
        { id: 'hypothesis-ranking', label: 'Classement d’hypothèses', value: false, status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST' },
        { id: 'probabilities-produced', label: 'Probabilités produites', value: false, status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST' },
        { id: 'bridge-read-capability', label: 'Capacité de lecture bridge', value: 'READ_ONLY', status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST' },
        { id: 'bridge-write-capability', label: 'Capacité d’écriture bridge', value: 'NONE', status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST' }
      ],
      evidence: [
        { id: 'SERVER-SIDE-WHITELIST', type: 'PUBLIC_ATTESTATION', status: 'VERIFIED_PUBLIC', public_ref: 'Whitelisted server-side Genesis status projection' }
      ],
      integrity: {
        status: 'VERIFIED_PUBLIC',
        checks: [
          { id: 'private-source-read-only', status: 'PASSED', public_ref: 'Dedicated read-only deploy key' },
          { id: 'private-identifiers-not-projected', status: 'PASSED', public_ref: 'Repository, branch, paths and private SHAs excluded' },
          { id: 'hypothesis-boundary-preserved', status: 'PASSED', public_ref: 'No hypothesis selection, ranking or probability promotion' },
          { id: 'snapshot-fallback', status: 'PASSED', public_ref: 'Frozen public snapshot remains available' }
        ]
      }
    }
  };
}

async function main() {
  const sourcePath = process.argv[2];
  if (!sourcePath) fail('Usage: build-public-source-from-seedgenesis.mjs <private-result-file> [output-json]');
  const outputPath = process.argv[3] ?? '.build/genesis-public-read-only-bridge/server-side-public-source.json';
  const source = await readFile(path.resolve(sourcePath), 'utf8');
  const status = extractWhitelistedGenesisStatus(source);
  const input = buildBridgeInputFromWhitelistedStatus(status);
  const resolvedOutput = path.resolve(outputPath);
  await mkdir(path.dirname(resolvedOutput), { recursive: true });
  await writeFile(resolvedOutput, `${JSON.stringify(input, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PRIVATE_SOURCE_WHITELIST_VALID');
  console.log(JSON.stringify({
    source_state: input.source_attestation.source_state,
    selected_experiment_status: input.source_attestation.selected_experiment_status,
    read_capability: input.source_attestation.read_capability,
    write_capability: input.source_attestation.write_capability,
    private_identifiers_projected: false
  }, null, 2));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch(error => {
    console.error(`GENESIS_PRIVATE_SOURCE_WHITELIST_INVALID: ${error.message}`);
    process.exit(1);
  });
}
