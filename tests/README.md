# Conformance Test Suite

Runs every example file in [`../examples/`](../examples/) through the JSON
Schema validators, plus negative cases and semantic federation checks.

## Running

```bash
cd tests
npm install
npm test
```

Requires Node.js 18+ (uses the built-in `node:test` runner).

## What it tests

### Schema validation (positive)
- `kai.agent.json` validates against v1.1 schema
- `autonomous-nova-lux.agent.json` validates against v1.1 schema
- `hybrid-kestrel.agent.json` validates against v1.1 schema
- `revoked-zombie.agent.json` validates against v1.1 schema
- `team.agents.json` validates against v1.1 team-index schema

### Backward compatibility
- `minimal.agent.json` (v1.0) validates against v1.1 schema (proves additive)
- `minimal.agent.json` (v1.0) validates against v1.0 schema (regression)

### Schema validation (negative)
- Card missing required fields → must fail
- Card with unknown `agent.kind` → must fail
- Card where `human-operated` lacks `owner` → must fail
- Card where `hybrid` lacks `owner` → must fail
- Card where `autonomous-ai-agent` lacks `owner` → must pass (allowed)
- Card with `version: "2.0"` → must fail
- Card where `revoked: true` lacks `revoked_at` → must fail
- Card with uppercase handle → must fail
- Card with legacy attestation shape (`by`/`at`/`claim`) → must fail v1.1

### Semantic federation checks
- `trust.revoked: true` cards are flagged for refusal
- `scope.impersonates_humans: true` cards are flagged for refusal
- Missing `scope.impersonates_humans` produces a warning
- Missing `agent.kind` produces a warning
- Well-formed autonomous card passes with zero warnings

### Schema metadata
- v1.1 schema `$id` points at the fork
- v1.1 schema `version` enum accepts both `1.0` and `1.1`
- v1.1 schema top-level `additionalProperties: true` (allows extensions)
- v1.1 schema `trust.attestations` uses SPEC shape (not legacy)

## Adding a new example

1. Create `../examples/your-card.agent.json` with `$schema` pointing at the v1.1 schema.
2. Add a positive test in `conformance.test.js`:
   ```js
   test('your-card.agent.json validates against v1.1 schema', () => {
     const schema = loadJson(SCHEMA_V11);
     const validate = ajv.compile(schema);
     const card = loadJson(path.join(EXAMPLES_DIR, 'your-card.agent.json'));
     const valid = validate(card);
     if (!valid) console.error('Validation errors:', validate.errors);
     assert.strictEqual(valid, true, 'your-card.agent.json must validate');
   });
   ```
3. Run `npm test`. If it fails, the schema needs updating — fix the schema, not the test.

## Adding a negative case

When fixing a schema bug, add a regression test that fails on the buggy
schema and passes on the fixed one. This prevents the bug from coming back.