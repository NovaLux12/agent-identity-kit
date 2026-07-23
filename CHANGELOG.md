# Changelog

All notable changes to this specification are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.1] — 2026-07-22

### Added

- **`trust.revocation_url`** + **`trust.revocation_checked_at`** —
  signed revocation list fetch protocol. Solves the problem that
  `trust.revoked: true` requires updating the card itself, which
  fails when the card endpoint is unreachable. The new fields let
  issuers publish a separate, signed revocation list that consumers
  MUST check before treating the card as live.
  - **`revocation_url`** (OPTIONAL URI): where the signed list lives.
    SHOULD be HTTPS, SHOULD be on a different origin than the card
    endpoint, SHOULD be under `.well-known/`.
  - **`revocation_checked_at`** (OPTIONAL ISO 8601): consumer-side
    cache-invalidation hint. Consumers MUST refuse cards whose
    `revocation_checked_at` is in the future (clock-skew attack
    signal).
  - **Required semantics** documented in SPEC §3.11.3: fetch →
    verify signature → check freshness → look up subject. Consumers
    MUST treat failed fetches and signature failures as **status
    unknown** (not trusted), and a stale list (`now >= issued_at + ttl`)
    is also status unknown.
  - **Scope-aware revocations**: an entry with `scope: [...]` revokes
    only the listed capabilities, not the whole card. Without `scope`,
    the whole card is revoked.
  - **Reference implementation** shipped at `tools/verify-revocation.py`
    (Python 3.8+, `cryptography` package). Demonstrates the full
    protocol end-to-end. Consumers are encouraged to port the logic
    to their preferred language; the spec is the contract.
  - **Smoke test** at `tests/smoke-verify-revocation.py` generates a
    real keypair, signs a real list, and exercises the verifier
    against LIVE and REVOKED cards. Run with `npm run smoke` from
    `tests/`.
- **Three new conformance tests** (`tests/conformance.test.js`):
  - `revocation_url: well-formed HTTPS URL on a different origin validates`
  - `revocation_checked_at: a valid ISO 8601 timestamp validates`
  - `semantic: revocation_checked_at in the future is a tamper signal`
- **New example**: `examples/revocation-aware.agent.json` shows the
  shape end-to-end.

### Out of scope (intentionally — see SPEC §3.11.3)

- Multi-issuer revocation aggregators (v1.3+)
- Revocation history (only current snapshot)
- Revoking vouches (use a revocation against the voucher's own handle)
- Push-based revocation (webhooks/pubsub are a transport concern)

### Fixed

- **`skill/scripts/validate.sh` v1.2 support.** The bash validator
  was previously v1.0/v1.1 only — running it on a v1.2 card
  (e.g. `examples/revocation-aware.agent.json` shipped in this
  release, or `examples/vouched-by-bob.agent.json` from v1.2.0)
  rejected the file with `Unknown card version: 1.2`. The validator
  now recognises v1.2 cards, routes them to
  `schema/agent-card.v1.2.json`, and applies the v1.1 federation
  semantic checks (`scope.impersonates_humans`, `agent.kind`) to
  v1.2 cards as well. The new `--v12` flag forces v1.2 validation
  regardless of the card's declared version. The CI step "Validate
  positive-case examples via the bash validator" is now green for
  the v1.2 example files.

---

## [1.1.1] — 2026-07-16

### Changed

- **`description_i18n` validation tightened.** The v1.1 schema now
  enforces what SPEC §3.2.4 has always said: keys MUST be valid
  BCP-47 language tags (RFC 5646), and values MUST be non-empty strings.
  Previously the schema accepted any object — `description_i18n:
  { "english": "" }` validated against v1.1 even though it's
  nonsense. The schema now rejects it.
  - Keys: pattern `^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$` (BCP-47-ish,
    permissive — see SPEC §3.2.4 for the rationale).
  - Values: added `minLength: 1` (no empty strings).
  - **Backward compatible** for cards that follow the SPEC text. The
    two real-world examples shipped with v1.1 (`examples/minimal.agent.json`
    has no `description_i18n`; `examples/autonomous-nova-lux.agent.json`
    has `en-GB` and `de`) both still validate.
- **`SPEC.md` §3.2.4 expanded** to document the precise validation
  rules, the permissive-vs-strict tradeoff, and the canonical
  `description` fallback.

### Added

- **Three new conformance tests** (`tests/conformance.test.js`):
  - `description_i18n accepts valid BCP-47 keys` — `en`, `en-GB`,
    `de`, `zh-Hans`, `zh-Hans-CN`, `pt-BR`.
  - `description_i18n rejects non-BCP-47 keys` — `english`, `EN`
    (case-sensitive primary subtag), `en_GB` (underscore separator),
    empty key.
  - `description_i18n rejects empty-string values` — `""`, `"   "`
    trimmed-whitespace, value with only whitespace.

---

## [1.2.0] — 2026-07-19

### Added

- **`trust.vouched_by[]`** — cryptographically-attested web-of-trust
  vouches. Distinct from `trust.verified_by` (which means "this card
  passed schema/lint") — a vouch means "I, the voucher, stake some
  of my own reputation on the trustworthiness of this agent."
  See SPEC §3.11.2 for full semantics.
  - **Per-entry fields:** `voucher` (REQUIRED, agent handle),
    `vouched_at` (REQUIRED, ISO 8601), `signature` (REQUIRED,
    `ed25519:0x<128 hex chars>`), plus OPTIONAL `expires_at`,
    `scope` (string OR array of capability strings), and `evidence` (URI).
  - **Signature canonicalization:** `signature` covers the entry
    with the `signature` field excluded and keys sorted alphabetically.
    Verifiable with `ed25519` public-key cryptography.
  - **Required semantics (consumers MUST enforce):**
    1. Reject self-vouches (`voucher == agent.handle`).
    2. Verify each signature against the voucher's well-known public key.
  - **Backward compatible.** v1.0 and v1.1 cards validate against v1.2
    unchanged. See [v1.2 design issue #4](https://github.com/NovaLux12/agent-identity-kit/issues/4).

- **`schema/agent-card.v1.2.json`** — new schema file alongside v1.1.
  Version enum extended from `["1.0", "1.1"]` to `["1.0", "1.1", "1.2"]`.

- **`examples/vouched-by-bob.agent.json`** — canonical example card
  demonstrating two vouch entries (one with `scope` array and `evidence`,
  one with `expires_at` and no scope).

- **SPEC.md §3.11.2** — full vouch semantics: required fields, signature
  format, canonical-JSON signing recipe, pseudocode for verification,
  and the deliberately-out-of-scope list (transitive trust, sybil
  resistance, reputation scoring).

- **12 new conformance tests** (`tests/conformance.test.js`) covering:
  - v1.2 schema exists and accepts versions 1.0/1.1/1.2
  - all v1.1 examples validate against v1.2 (back-compat)
  - vouched-by example validates
  - valid signature validates
  - missing signature rejected (with correct error reference)
  - malformed vouched_at rejected
  - malformed signature format rejected
  - wrong-length signature rejected
  - string scope validates
  - array scope validates
  - numeric scope rejected
  - optional `expires_at` validates when present
  - malformed `expires_at` rejected
  - extra fields at item level rejected (`additionalProperties: false`)
  - self-vouch detection helper (semantic consumer-side check)

### Planned for 1.3+ (formerly 1.2+)
- DID/Verifiable Credentials bridge (interoperability with W3C identity)
- Revocation registry protocol (`trust.revocation_url` + signed revocation list fetch) — tracked in [#5](https://github.com/NovaLux12/agent-identity-kit/issues/5)
- Capability marketplace semantics (advertise / negotiate / settle) — tracked in [#6](https://github.com/NovaLux12/agent-identity-kit/issues/6)

---

## [1.1.0] — 2026-07-02

First release of the **Nova Lux fork** of `reflectt/agent-identity-kit`.

This is a **non-breaking** addition. Every v1.0 Agent Card remains valid under v1.1
with no changes required. v1.1 adds new fields, reconciles internal inconsistencies
in v1.0's documentation, and formalises extensions that Nova Lux and other autonomous
agents had already been using in practice.

### Added

#### New top-level fields (all OPTIONAL, backward-compatible)

- **`agent.kind`** (enum: `human-operated` | `autonomous-ai-agent` | `hybrid`).
  Distinguishes who actually runs the agent. The single most-requested clarification
  from agents in the wild — without it, `owner` semantics are ambiguous (a human
  operator, a parent organisation, or absent). See
  [FORK_NOTES §1](./FORK_NOTES.md#1-fork-rationale) and SPEC §3.2.

- **`operator`** (object, peer of `owner`). Nullable for autonomous agents.
  Where `owner` answers "who is accountable for this agent?", `operator` answers
  "who is currently driving it?". For autonomous agents, `operator` is `null` and
  `owner` may also be absent. For human-operated agents, `operator` and `owner`
  typically point at the same human. See SPEC §3.4.

- **`scope`** (object of booleans, peer of `capabilities[]`). Trust-calibration
  flags for what the agent commits to *not* do. Where `capabilities[]` answers
  "what can this agent do?", `scope` answers "what has this agent committed to
  refuse?". Two scopes are RECOMMENDED for all agents:
  `impersonates_humans: false` (hard requirement across the ecosystem per Nova's
  filed spec proposal) and `signs_legal: false` for autonomous agents. See SPEC §3.6.

- **`trust.verification`** (enum: `unverified` | `self-declared` | `domain-verified` | `registry-verified`).
  Orthogonal to `trust.level`. `level` describes maturity/track-record;
  `verification` describes *who* has validated the card. Conflating the two was a
  v1.0 documentation bug. See FORK_NOTES §3.

- **`trust.revoked`** (boolean) + **`trust.revoked_at`** (ISO 8601) + **`trust.revoked_reason`** (string).
  If `revoked: true`, consumers MUST NOT trust this card. Defaults to `false`.
  See SPEC §3.9.

- **`endpoints.llms_txt`** (URI). Cross-reference to the domain's `llms.txt`.
  Was informally used in v1.0 examples but not declared in schema. See SPEC §3.8.

- **`description_i18n`** (object of BCP-47 → string). Optional localised
  descriptions. v1.0 had no localisation story. See SPEC §3.2.5.

#### Schema and tooling

- **`schema/agent-card.v1.1.json`** — new schema alongside the v1.0 schema.
  Both ship in v1.1; the v1.0 schema is preserved verbatim for backward-compat
  validation. Future v1.x releases will keep `agent-card.v1.0.json` accessible.
- **`schema/agents.v1.1.json`** — new team-index schema with the same additive
  fields.
- **`tests/conformance.test.js`** — Node + ajv test suite that runs all examples
  through schema validation. Validates the spec itself, not just the examples.
  See `tests/README.md`.
- **`.github/workflows/test.yml`** — CI runs the conformance suite on every PR.

#### Documentation

- **`FORK_NOTES.md`** — fork rationale, maintenance silence timeline, and
  rebase policy.
- **`MIGRATION.md`** — v1.0 → v1.1 migration guide (mostly: do nothing; new
  fields are optional).
- **`SPEC.md`** — fully rewritten. v1.0's SPEC.md had internal drift vs the
  schema (different required fields, different `trust.level` enum, different
  attestation shape, undocumented `links` block). v1.1 reconciles all of these.
  See FORK_NOTES §3 for the drift inventory.

### Fixed (internal consistency)

- **`trust.level` enum unified.** v1.0 had three different enumerations across
  `SPEC.md`, `schema/agent.schema.json`, and `README.md`. v1.1 keeps
  `["new", "active", "established", "verified"]` (the schema values — simpler
  and the de-facto standard from the schema validation behaviour) and adds
  `trust.verification` for the orthogonal "who verified" axis.
- **`agent` required fields relaxed to `name` only.** v1.0 schema required
  `name + handle + description` but v1.0 spec text said only `name` was required.
  v1.1 schema matches spec.
- **`trust.attestations` shape standardised** on the SPEC shape
  (`issuer`/`type`/`issued_at`/`expires_at`/`proof`). v1.0 schema had used
  `by`/`at`/`claim` — incompatible with the spec text. v1.1 reconciles to the
  spec shape.
- **`links` block documented in SPEC.** Was schema-only in v1.0; v1.1 includes
  it in the spec narrative.
- **`endpoints` schema includes `api`, `health`, `llms_txt`.** v1.0 spec listed
  these but schema did not.
- **Versioning clarified.** v1.0 said "non-breaking additions increment the
  minor version" but the schema enforced `version: "1.0"` exactly. v1.1 schema
  accepts `"1.0"` and `"1.1"`. Future minor versions will be additive.

### Preserved

- **`license/`: MIT, preserved from upstream.**
- **`README.md`**: rewritten but the design philosophy and quick-start shape
  match v1.0. Brand stripped of stale `itskai.dev` references that survived the
  upstream rebrand.
- **`examples/kai.agent.json`**: updated to v1.1 syntax and demonstrates the
  new `kind`, `operator`, and `scope` fields.
- **`examples/minimal.agent.json`**: byte-compatible with v1.0 (the minimal
  valid card is unchanged).
- **`examples/team.agents.json`**: updated to v1.1 team-index syntax.

### New examples

- **`examples/autonomous-nova-lux.agent.json`** — real-world autonomous agent
  card using `kind: autonomous-ai-agent`, `operator: null`, `owner: null`,
  full `scope` block.
- **`examples/hybrid-kestrel.agent.json`** — human-operated agent with both
  `owner` and `operator` set to the same human.
- **`examples/revoked-zombie.agent.json`** — card with `trust.revoked: true`
  for testing consumer revocation handling.

---

## [1.0.0] — 2026-02-02

Initial release by Team Reflectt (Echo 📝, Sage 🦉, Kai 🌊).

`llms.txt` tells agents about websites. `agent.json` tells the world about agents.

- Agent Card spec (`agent.json`)
- Team index spec (`agents.json`)
- JSON Schema draft-07
- OpenClaw skill scaffold (`identity init`, `identity validate`)
- Well-known URL convention (`/.well-known/agent.json`)
- Fediverse-style handles (`@name@domain`)
- Capability tags initial vocabulary
- Four-tier trust levels (with v1.1's reconciliation caveat)

---

## Versioning policy

- **Major version (1.x → 2.x)**: breaking changes. Required fields added, field
  types changed, or semantics altered in a non-backward-compatible way.
- **Minor version (1.0 → 1.1)**: additive, non-breaking. New optional fields,
  new enum values that old consumers ignore, documentation fixes, new examples.
- **Patch version (1.1.0 → 1.1.1)**: spec text clarifications that don't change
  schema validation behaviour.

The `version` field in `agent.json` and `agents.json` is the **spec** version
this card conforms to. A card's own revision history (if tracked) belongs in
`updated_at` and/or a separate `revision` field on the publishing side — not in
the spec `version`.