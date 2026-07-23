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

## Revocation verifier smoke test (v1.2.1)

The reference implementation in `../tools/verify-revocation.py` has its own
end-to-end smoke test. It generates a real ed25519 keypair, signs a real
revocation list, spins up a local HTTP server, and exercises the verifier
against a LIVE card and a REVOKED card.

```bash
cd tests
npm run smoke
```

Requires Python 3.8+ with the `cryptography` package (`pip install cryptography`).
The smoke test is separate from `npm test` because it depends on Python and the
`cryptography` library, not on the Node toolchain.

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
- Card with malformed handle (no `@` prefix) → must fail
- Card with mixed-case handle → must pass (v1.1 relaxed from v1.0 SPEC text)
- Card with legacy attestation shape (`by`/`at`/`claim`) → must fail v1.1
- v1.0 card with no `agent.kind` and no `owner` → must pass (B1 regression)
- Card with `trust` but no `revoked` field → must pass (B1 regression)

### Semantic federation checks
- `trust.revoked: true` cards are flagged for refusal
- `scope.impersonates_humans: true` cards are flagged for refusal
- Missing or `null` `scope.impersonates_humans` cards are flagged for refusal (per SPEC §4.5; see B2)
- Missing `agent.kind` produces a warning
- Well-formed autonomous card passes with zero warnings/refusals

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