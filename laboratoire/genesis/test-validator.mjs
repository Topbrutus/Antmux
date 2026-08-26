#!/usr/bin/env node

import { validateDemo } from './validate-demo.mjs';

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

const validDemo = {
  contract_version: '1.0.0-draft',
  mode: 'DEMO',
  publication_id: 'DEMO-TEST-0001',
  published_at: '2026-08-26T06:05:00Z',
  source_status: 'SYNTHETIC',
  integrity_status: 'NOT_APPLICABLE',
  payload: {
    experiment: {
      public_experiment_id: 'DEMO-EXP-TEST-001',
      label: 'Synthetic validator test',
      status: 'DEMO_ONLY',
      generation: 1
    },
    continuity: {
      stage: 'test',
      origin_ref: 'DEMO-ORIGIN-TEST-001',
      previous_publication_ref: 'DEMO-PREVIOUS-TEST-0000',
      return_status: 'PENDING'
    },
    pipeline: {
      steps: [
        { id: 'step-origin', label: 'Origine', status: 'PASSED' },
        { id: 'step-test', label: 'Test', status: 'RUNNING_PUBLIC' }
      ]
    },
    metrics: [
      {
        id: 'metric-1',
        label: 'Synthetic metric',
        value: 1,
        unit: 'unit',
        status: 'SYNTHETIC',
        provenance_ref: 'DEMO-PROVENANCE-TEST-001'
      }
    ],
    evidence: [
      {
        id: 'DEMO-PROVENANCE-TEST-001',
        type: 'PUBLIC_DOCUMENT',
        status: 'SYNTHETIC',
        public_ref: 'laboratoire/genesis/PUBLIC-CONTRACT-v1.md'
      }
    ],
    integrity: {
      status: 'NOT_APPLICABLE',
      checks: [
        {
          id: 'synthetic-label-present',
          status: 'PASSED',
          public_ref: 'DEMO / SYNTHETIC DATA'
        }
      ]
    }
  }
};

const cases = [
  {
    name: 'valid synthetic envelope passes',
    shouldPass: true,
    build: () => clone(validDemo)
  },
  {
    name: 'unknown top-level field is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.private_debug = 'forbidden';
      return data;
    }
  },
  {
    name: 'SNAPSHOT mode is rejected by DEMO validator',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.mode = 'SNAPSHOT';
      return data;
    }
  },
  {
    name: 'non-synthetic source status is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.source_status = 'PUBLIC_READ_ONLY';
      return data;
    }
  },
  {
    name: 'invalid pipeline status is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.payload.pipeline.steps[1].status = 'SECRET_RUNNING';
      return data;
    }
  },
  {
    name: 'private Windows path is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.payload.evidence[0].public_ref = 'C:\\private\\genesis\\audit.json';
      return data;
    }
  },
  {
    name: 'localhost endpoint is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.payload.evidence[0].public_ref = 'http://127.0.0.1:8080/private';
      return data;
    }
  },
  {
    name: 'private RFC1918 endpoint is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.payload.evidence[0].public_ref = 'https://192.168.1.10/genesis';
      return data;
    }
  },
  {
    name: 'GitHub token-shaped string is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.payload.evidence[0].public_ref = 'ghp_123456789012345678901234567890123456';
      return data;
    }
  },
  {
    name: 'private-key marker is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.payload.evidence[0].public_ref = '-----BEGIN PRIVATE KEY-----';
      return data;
    }
  },
  {
    name: 'missing required publication_id is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      delete data.publication_id;
      return data;
    }
  },
  {
    name: 'non-finite metric is rejected',
    shouldPass: false,
    build: () => {
      const data = clone(validDemo);
      data.payload.metrics[0].value = Infinity;
      return data;
    }
  }
];

let failures = 0;

for (const testCase of cases) {
  let passedValidation = false;
  let errorMessage = '';

  try {
    validateDemo(testCase.build());
    passedValidation = true;
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : String(error);
  }

  const behavedAsExpected = testCase.shouldPass === passedValidation;

  if (behavedAsExpected) {
    console.log(`PASS  ${testCase.name}`);
  } else {
    failures += 1;
    console.error(`FAIL  ${testCase.name}`);
    console.error(`      expected=${testCase.shouldPass ? 'PASS' : 'REJECT'} actual=${passedValidation ? 'PASS' : 'REJECT'}`);
    if (errorMessage) console.error(`      ${errorMessage}`);
  }
}

if (failures > 0) {
  console.error(`GENESIS_VALIDATOR_TESTS_FAILED ${failures}/${cases.length}`);
  process.exitCode = 1;
} else {
  console.log(`GENESIS_VALIDATOR_TESTS_PASSED ${cases.length}/${cases.length}`);
}
