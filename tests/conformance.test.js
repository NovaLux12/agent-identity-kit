'use strict';

/**
 * Conformance test suite for the agent-identity-kit v1.1 spec.
 *
 * Tests:
 *   1. Every example file validates against the v1.1 schema.
 *   2. The minimal v1.0 example validates against BOTH v1.0 and v1.1 schemas
 *      (proves backward-compatibility).
 *   3. Negative cases — invalid cards are correctly rejected.
 *   4. Semantic federation checks — revoked/impersonation/kind-missing
 *      are correctly flagged.
 *   5. Team index schema validates the team example.
 *
 * Run: cd tests && npm install && npm test
 *
 * Why this suite exists:
 *   v1.0 of the spec shipped with no tests. The schema was claimed to
 *   validate, but no consumer had a way to verify the claim. v1.1 ships
 *   with this suite so future edits to the schema MUST keep all examples
 *   passing — no silent drift.
 */

const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const assert = require('node:assert');

const Ajv = require('ajv');
const addFormats = require('ajv-formats');

const REPO_ROOT = path.resolve(__dirname, '..');
const SCHEMA_V11 = path.join(REPO_ROOT, 'schema', 'agent-card.v1.1.json');
const SCHEMA_V10 = path.join(REPO_ROOT, 'schema', 'agent.schema.json');
const SCHEMA_TEAM_V11 = path.join(REPO_ROOT, 'schema', 'agents.v1.1.json');
const EXAMPLES_DIR = path.join(REPO_ROOT, 'examples');

function makeAjv() {
  // Fresh Ajv instance per compile. ajv caches compiled schemas by $id,
  // and our v1.1 schema declares a GitHub $id that ajv treats as a unique
  // key — compiling the same schema twice across tests would error with
  // "schema with key or id ... already exists". A fresh instance per
  // compile avoids the cache collision.
  const ajv = new Ajv({ strict: false, allErrors: true });
  addFormats(ajv);
  return ajv;
}

function loadJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function compileValidator(schemaPath) {
  // Strip $id before compiling so ajv doesn't cache by URL key. The schema
  // metadata is still correct on disk; we're just telling ajv "this is a
  // fresh anonymous schema".
  const schema = loadJson(schemaPath);
  delete schema.$id;
  return makeAjv().compile(schema);
}

// ─── 1. Examples validate against v1.1 schema ──────────────────────────────

test('kai.agent.json validates against v1.1 schema', () => {
  const validate = compileValidator(SCHEMA_V11);
  const card = loadJson(path.join(EXAMPLES_DIR, 'kai.agent.json'));
  const valid = validate(card);
  if (!valid) {
    console.error('Validation errors:', validate.errors);
  }
  assert.strictEqual(valid, true, 'kai.agent.json must validate');
});

test('autonomous-nova-lux.agent.json validates against v1.1 schema', () => {
  const validate = compileValidator(SCHEMA_V11);
  const card = loadJson(path.join(EXAMPLES_DIR, 'autonomous-nova-lux.agent.json'));
  const valid = validate(card);
  if (!valid) {
    console.error('Validation errors:', validate.errors);
  }
  assert.strictEqual(valid, true, 'autonomous-nova-lux.agent.json must validate');
});

test('hybrid-kestrel.agent.json validates against v1.1 schema', () => {
  const validate = compileValidator(SCHEMA_V11);
  const card = loadJson(path.join(EXAMPLES_DIR, 'hybrid-kestrel.agent.json'));
  const valid = validate(card);
  if (!valid) {
    console.error('Validation errors:', validate.errors);
  }
  assert.strictEqual(valid, true, 'hybrid-kestrel.agent.json must validate');
});

test('revoked-zombie.agent.json validates against v1.1 schema', () => {
  // Revoked cards MUST still be schema-valid. The revocation flag is
  // semantic, not structural. Consumers refuse based on the field, not
  // schema validation.
  const validate = compileValidator(SCHEMA_V11);
  const card = loadJson(path.join(EXAMPLES_DIR, 'revoked-zombie.agent.json'));
  const valid = validate(card);
  if (!valid) {
    console.error('Validation errors:', validate.errors);
  }
  assert.strictEqual(valid, true, 'revoked-zombie.agent.json must validate');
});

test('team.agents.json validates against v1.1 team schema', () => {
  const validate = compileValidator(SCHEMA_TEAM_V11);
  const team = loadJson(path.join(EXAMPLES_DIR, 'team.agents.json'));
  const valid = validate(team);
  if (!valid) {
    console.error('Validation errors:', validate.errors);
  }
  assert.strictEqual(valid, true, 'team.agents.json must validate');
});

// ─── 2. Backward-compatibility: v1.0 cards still validate against v1.1 ─────

test('minimal.agent.json (v1.0) validates against v1.1 schema (back-compat)', () => {
  // This proves the additive promise: any v1.0 card is a valid v1.1 card
  // without changes. If this fails, v1.1 has introduced a breaking change
  // and the CHANGELOG must be updated.
  const validate = compileValidator(SCHEMA_V11);
  const card = loadJson(path.join(EXAMPLES_DIR, 'minimal.agent.json'));
  assert.strictEqual(card.version, '1.0', 'minimal.agent.json should be v1.0');
  const valid = validate(card);
  if (!valid) {
    console.error('Validation errors:', validate.errors);
  }
  assert.strictEqual(valid, true, 'v1.0 minimal card must validate against v1.1 schema');
});

test('minimal.agent.json (v1.0) also validates against v1.0 schema', () => {
  const validate = compileValidator(SCHEMA_V10);
  const card = loadJson(path.join(EXAMPLES_DIR, 'minimal.agent.json'));
  const valid = validate(card);
  if (!valid) {
    console.error('Validation errors:', validate.errors);
  }
  assert.strictEqual(valid, true, 'v1.0 minimal card must validate against v1.0 schema');
});

// ─── 3. Negative cases — invalid cards must be rejected ────────────────────

test('rejects card with missing required fields', () => {
  const validate = compileValidator(SCHEMA_V11);
  const bad = {
    version: '1.1',
    // missing agent object
    owner: { name: 'Jane' }
  };
  assert.strictEqual(validate(bad), false, 'card without agent must fail');
  assert.ok(
    validate.errors.some(e => e.instancePath === '' && e.params.missingProperty === 'agent'),
    'error should mention missing agent'
  );
});

test('rejects card with unknown agent.kind', () => {
  const validate = compileValidator(SCHEMA_V11);
  const bad = {
    version: '1.1',
    agent: {
      kind: 'unknown-kind',
      name: 'Test'
    },
    owner: { name: 'Jane' }
  };
  assert.strictEqual(validate(bad), false, 'card with unknown kind must fail');
});

test('rejects card where human-operated is missing owner', () => {
  // Conditional: owner is REQUIRED when agent.kind is human-operated.
  const validate = compileValidator(SCHEMA_V11);
  const bad = {
    version: '1.1',
    agent: {
      kind: 'human-operated',
      name: 'Test'
    }
    // no owner
  };
  assert.strictEqual(validate(bad), false, 'human-operated without owner must fail');
});

test('rejects card where hybrid is missing owner', () => {
  const validate = compileValidator(SCHEMA_V11);
  const bad = {
    version: '1.1',
    agent: {
      kind: 'hybrid',
      name: 'Test'
    }
  };
  assert.strictEqual(validate(bad), false, 'hybrid without owner must fail');
});

test('rejects card where autonomous-ai-agent has no owner (allowed) — passes', () => {
  // Positive case: autonomous agents without owner are allowed.
  const validate = compileValidator(SCHEMA_V11);
  const card = {
    version: '1.1',
    agent: {
      kind: 'autonomous-ai-agent',
      name: 'Test'
    },
    operator: null
  };
  assert.strictEqual(validate(card), true, 'autonomous without owner must pass');
});

test('v1.0 card with no agent.kind and no owner validates against v1.1 (B1 regression)', () => {
  // Regression for B1: the schema's if/then for owner should only fire
  // when agent.kind is explicitly present. A v1.0 card that declares no
  // kind and no owner must validate against v1.1 schema unchanged —
  // this is the v1.0 back-compat invariant. Before the fix, the if/then
  // fired vacuously and required owner.
  const validate = compileValidator(SCHEMA_V11);
  const card = { version: '1.0', agent: { name: 'Test' } };
  const valid = validate(card);
  if (!valid) console.error('Validation errors:', validate.errors);
  assert.strictEqual(valid, true, 'v1.0 card with no kind and no owner must validate');
});

test('card with trust present but no revoked field validates (B1 regression)', () => {
  // Regression for B1 (revoked branch): the if/then for trust.revoked_at
  // should only fire when trust.revoked is explicitly true. A v1.0 card
  // with a trust object but no revoked field must validate against v1.1
  // schema unchanged.
  const validate = compileValidator(SCHEMA_V11);
  const card = {
    version: '1.1',
    agent: { kind: 'human-operated', name: 'Test' },
    owner: { name: 'Jane' },
    trust: { level: 'new', verified_by: [] }
  };
  const valid = validate(card);
  if (!valid) console.error('Validation errors:', validate.errors);
  assert.strictEqual(valid, true, 'card with trust but no revoked must validate');
});

test('rejects card with invalid version', () => {
  const validate = compileValidator(SCHEMA_V11);
  const bad = {
    version: '2.0', // not in enum
    agent: { name: 'Test' },
    owner: { name: 'Jane' }
  };
  assert.strictEqual(validate(bad), false, 'card with version 2.0 must fail');
});

test('rejects card where trust.revoked=true is missing revoked_at', () => {
  // Conditional: revoked_at is REQUIRED when revoked is true.
  const validate = compileValidator(SCHEMA_V11);
  const bad = {
    version: '1.1',
    agent: {
      kind: 'human-operated',
      name: 'Test'
    },
    owner: { name: 'Jane' },
    trust: {
      revoked: true
      // missing revoked_at
    }
  };
  assert.strictEqual(validate(bad), false, 'revoked card without revoked_at must fail');
});

test('rejects card with malformed handle (no @ prefix)', () => {
  // v1.1 relaxed the regex to allow uppercase for ecosystem portability
  // (the SPEC text recommended lowercase but the v1.0 schema allowed mixed
  // case, and the real ecosystem uses mixed case). The handle must still
  // have the @name@domain shape.
  const validate = compileValidator(SCHEMA_V11);
  const bad = {
    version: '1.1',
    agent: {
      name: 'Test',
      handle: 'not-a-handle' // missing @ prefix
    },
    owner: { name: 'Jane' }
  };
  assert.strictEqual(validate(bad), false, 'handle without @ must fail');
});

test('accepts card with mixed-case handle (v1.1 relaxed from v1.0 SPEC text)', () => {
  // The v1.0 SPEC said handles MUST be lowercase, but the v1.0 schema
  // allowed mixed case, and the real ecosystem uses mixed case (e.g.,
  // @NovaLux12@NovaLux12.github.io). v1.1 relaxed to match what people
  // actually do. The SPEC text recommendation stays (lowercase preferred)
  // but the schema accepts mixed case.
  const validate = compileValidator(SCHEMA_V11);
  const card = {
    version: '1.1',
    agent: {
      kind: 'autonomous-ai-agent',
      name: 'Nova',
      handle: '@NovaLux12@NovaLux12.github.io'
    },
    operator: null
  };
  assert.strictEqual(validate(card), true, 'mixed-case handle must pass');
});

test('rejects card with bad attestation shape (legacy v1.0 by/at/claim)', () => {
  // v1.1 schema requires the SPEC shape (issuer/type/issued_at/...).
  // The legacy v1.0 schema shape (by/at/claim) must fail.
  const validate = compileValidator(SCHEMA_V11);
  const bad = {
    version: '1.1',
    agent: {
      kind: 'human-operated',
      name: 'Test'
    },
    owner: { name: 'Jane' },
    trust: {
      attestations: [
        { by: 'someone', at: '2026-01-01T00:00:00Z', claim: 'verified' }
      ]
    }
  };
  assert.strictEqual(validate(bad), false, 'legacy attestation shape must fail v1.1');
});

// ─── 4. Semantic federation checks (not schema, but consumer logic) ────────

function federationCheck(card) {
  const warnings = [];
  const refusals = [];

  // 1. Revocation — refuse if explicitly revoked
  if (card.trust?.revoked === true) {
    refusals.push('card is revoked');
  }

  // 2. Impersonation — refuse per SPEC §4.5: consumers MUST refuse cards
  //    where scope.impersonates_humans is absent, null, or true.
  //    'absent' includes the case where the field is missing entirely.
  if (card.version === '1.1') {
    const impersonates = card.scope?.impersonates_humans;
    if (impersonates === true) {
      refusals.push('scope.impersonates_humans is true');
    } else if (impersonates === undefined || impersonates === null) {
      refusals.push('scope.impersonates_humans is absent or null');
    }

    // 3. Kind clarity — warn if missing (not a refusal)
    if (!card.agent?.kind) {
      warnings.push('agent.kind not declared (recommend human-operated/autonomous-ai-agent/hybrid)');
    }
  }

  return { warnings, refusals };
}

test('semantic: revoked card is refused', () => {
  const card = loadJson(path.join(EXAMPLES_DIR, 'revoked-zombie.agent.json'));
  const { warnings, refusals } = federationCheck(card);
  assert.ok(refusals.includes('card is revoked'), 'revoked card must be refused');
});

test('semantic: cards with impersonates_humans:true are refused', () => {
  const card = {
    version: '1.1',
    agent: { kind: 'human-operated', name: 'Spoof' },
    owner: { name: 'Spoof Co' },
    scope: { impersonates_humans: true }
  };
  const { refusals } = federationCheck(card);
  assert.ok(refusals.includes('scope.impersonates_humans is true'), 'spoofing card must be refused');
});

test('semantic: cards without impersonates_humans set are refused (per SPEC §4.5)', () => {
  // SPEC §4.5: consumers MUST refuse cards where scope.impersonates_humans
  // is absent, null, or true. 'absent' is a refusal, not a warning.
  // This is the federation-check implementation of B2.
  const card = {
    version: '1.1',
    agent: { kind: 'human-operated', name: 'Sloppy' },
    owner: { name: 'Sloppy Co' }
  };
  const { refusals } = federationCheck(card);
  assert.ok(refusals.some(r => r.includes('impersonates_humans')), 'must refuse on missing impersonates_humans');
});

test('semantic: cards without agent.kind set get a warning', () => {
  const card = {
    version: '1.1',
    agent: { name: 'Anonymous' },
    owner: { name: 'Anonymous Co' },
    scope: { impersonates_humans: false }
  };
  const { warnings } = federationCheck(card);
  assert.ok(warnings.some(w => w.includes('agent.kind')), 'must warn about missing agent.kind');
});

test('semantic: well-formed autonomous card passes all federation checks', () => {
  const card = loadJson(path.join(EXAMPLES_DIR, 'autonomous-nova-lux.agent.json'));
  const { warnings, refusals } = federationCheck(card);
  assert.deepStrictEqual(refusals, [], 'autonomous card must not be refused');
  assert.deepStrictEqual(warnings, [], 'well-formed autonomous card must have no warnings');
});

// ─── 5. Schema metadata sanity checks ──────────────────────────────────────

test('v1.1 schema has correct $id', () => {
  const schema = loadJson(SCHEMA_V11);
  assert.ok(schema.$id.includes('NovaLux12/agent-identity-kit'), 'schema $id must point at the fork');
  assert.ok(schema.$id.includes('v1.1'), 'schema $id must reference v1.1');
});

test('v1.1 schema version enum accepts both 1.0 and 1.1', () => {
  const schema = loadJson(SCHEMA_V11);
  const versionProp = schema.properties.version;
  assert.deepStrictEqual(
    versionProp.enum.sort(),
    ['1.0', '1.1'],
    'version must accept both 1.0 and 1.1'
  );
});

test('v1.1 schema allows top-level x_* extensions (additionalProperties: true)', () => {
  const schema = loadJson(SCHEMA_V11);
  assert.strictEqual(
    schema.additionalProperties,
    true,
    'top-level additionalProperties must be true so x_* extensions work'
  );
});

test('v1.1 schema documents trust.attestations shape as SPEC (issuer/type/issued_at)', () => {
  const schema = loadJson(SCHEMA_V11);
  const attestationProps = schema.properties.trust.properties.attestations.items.properties;
  assert.ok(attestationProps.issuer, 'must have issuer');
  assert.ok(attestationProps.type, 'must have type');
  assert.ok(attestationProps.issued_at, 'must have issued_at');
  assert.ok(!attestationProps.by, 'must NOT have legacy by field');
  assert.ok(!attestationProps.at, 'must NOT have legacy at field');
  assert.ok(!attestationProps.claim, 'must NOT have legacy claim field');
});