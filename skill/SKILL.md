# Agent Identity Kit — OpenClaw Skill (v1.1)

A portable identity system for AI agents. Create, validate, and publish
`agent.json` identity cards. **v1.1** of the [Nova Lux fork](../FORK_NOTES.md).

## What This Skill Does

- **Creates** agent identity cards (`agent.json`) via interactive setup
- **Validates** identity cards against the Agent Card v1.0 OR v1.1 schema
  (auto-detects from `version` field)
- **Provides** JSON Schemas for editor integration and CI pipelines

## Quick Start

### Generate a new agent.json

```bash
./scripts/init.sh
```

Prompts you for name, handle, description, **agent kind** (v1.1),
owner/operator, capabilities, scope flags, and trust settings.
Outputs a valid v1.1 `agent.json` by default.

### Validate an existing agent.json

```bash
./scripts/validate.sh path/to/agent.json
```

Auto-detects the card's spec version and validates against the matching
schema (v1.0 or v1.1). Requires `ajv-cli` or Python's `jsonschema`
(auto-installs if missing).

For the full conformance suite (every example in this repo, every
negative case, plus revocation + impersonation checks), use the Node test
suite:

```bash
cd tests && npm install && npm test
```

## What's new in v1.1

If you're already on v1.0, **you don't need to change anything**. v1.1
cards validate against the v1.1 schema and v1.0 cards validate against
the v1.0 schema. The v1.1 release is additive.

New optional fields:

- `agent.kind` (`human-operated` | `autonomous-ai-agent` | `hybrid`)
- `operator` (peer of `owner`, nullable)
- `scope` (boolean flags, peer of `capabilities[]`)
- `trust.verification` (orthogonal to `trust.level`)
- `trust.revoked` + `revoked_at` + `revoked_reason`
- `description_i18n` (BCP-47 localised descriptions)
- `endpoints.llms_txt` (cross-reference to `llms.txt`)
- Top-level extensions via `x_*` prefix now allowed (schema has
  `additionalProperties: true` at top level)

Plus schema fixes for v1.0 inconsistencies (see
[`FORK_NOTES.md §3`](../FORK_NOTES.md)).

## File Structure (v1.1)

```
agent-identity-kit/
├── schema/
│   ├── agent.schema.json          # v1.0 schema (preserved for back-compat)
│   ├── agent-card.v1.1.json       # v1.1 schema (NEW — use this for new cards)
│   ├── agents.json                # v1.0 team-index schema (preserved)
│   └── agents.v1.1.json           # v1.1 team-index schema (NEW)
├── examples/
│   ├── kai.agent.json                        # Updated to v1.1
│   ├── minimal.agent.json                    # UNCHANGED — proves v1.0 compat
│   ├── autonomous-nova-lux.agent.json        # NEW — real autonomous agent
│   ├── hybrid-kestrel.agent.json             # NEW — kind/owner/operator triad
│   ├── revoked-zombie.agent.json             # NEW — revocation test fixture
│   └── team.agents.json                      # Updated to v1.1
├── skill/
│   ├── SKILL.md                    # This file
│   └── scripts/
│       ├── init.sh                 # Generate a starter agent.json (v1.1)
│       └── validate.sh             # Validate against v1.0 OR v1.1 schema
├── tests/                          # NEW
│   ├── conformance.test.js         # Node + ajv test suite
│   ├── package.json
│   └── README.md
├── .github/workflows/test.yml      # NEW — CI runs conformance on every PR
├── CHANGELOG.md                    # NEW
├── FORK_NOTES.md                   # NEW — why this fork exists
├── MIGRATION.md                    # NEW — v1.0 → v1.1 guide
├── SPEC.md                         # Fully rewritten for v1.1
├── README.md
├── DEFINE.md
└── LICENSE                         # MIT, preserved from upstream
```

## Schema Fields (v1.1 summary)

| Field | Required | v1.1 notes |
|-------|----------|------------|
| `version` | ✅ | Now accepts `"1.0"` or `"1.1"`. |
| `agent.name` | ✅ | |
| `agent.kind` | recommended | NEW. `human-operated` / `autonomous-ai-agent` / `hybrid`. |
| `agent.handle` | recommended | Regex tightened. |
| `agent.description` | recommended | |
| `agent.description_i18n` | optional | NEW. BCP-47 keyed. |
| `owner` | conditional | REQUIRED iff `agent.kind` is `human-operated` or `hybrid`. |
| `operator` | recommended | NEW. Peer of owner. `null` for autonomous. |
| `capabilities` | — | |
| `scope` | recommended | NEW. Boolean flags for trust calibration. |
| `protocols` | — | |
| `endpoints.card` | recommended | |
| `endpoints.llms_txt` | optional | NEW. |
| `trust.level` | — | `new`/`active`/`established`/`verified`. |
| `trust.verification` | optional | NEW. Orthogonal to level. |
| `trust.revoked` | optional | NEW. If `true`, refuse. |
| `links` | — | Now documented in SPEC (was schema-only in v1.0). |

## Federation checks (v1.1)

Per SPEC §4.5, consumers **MUST** refuse cards where:

- `trust.revoked` is `true`
- `scope.impersonates_humans` is absent, `null`, or `true`

Consumers SHOULD warn (not refuse) when:

- `agent.kind` is missing AND kind clarity is required

The conformance test suite in `tests/` exercises all of these.

## Hosting Your Card

Serve your `agent.json` at a well-known URL:

```
https://yourdomain.com/.well-known/agent.json
```

For multiple agents:

```
https://yourdomain.com/.well-known/agents.json
```

## Integration with forAgents.dev

Register your agent at [foragents.dev](https://foragents.dev) to be indexed
in the global agent directory. Verified agents get a badge on their card.

## Spec Reference

- v1.1 SPEC: [`SPEC.md`](../SPEC.md)
- v1.1 schema: [`schema/agent-card.v1.1.json`](../schema/agent-card.v1.1.json)
- Fork rationale: [`FORK_NOTES.md`](../FORK_NOTES.md)
- Migration guide: [`MIGRATION.md`](../MIGRATION.md)