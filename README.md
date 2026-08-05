# Agent Identity Kit 🪪

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Spec Version](https://img.shields.io/badge/Spec-v1.3.0-blue.svg)](SPEC.md)
[![Schema v1.3](https://img.shields.io/badge/Schema-JSON-orange.svg)](schema/agent-card.v1.3.json)
[![Conformance](https://img.shields.io/badge/Conformance-65%2F65-brightgreen.svg)](tests/)

**A portable identity standard for AI agents.**

> `llms.txt` tells agents about websites. `agent.json` tells the world about agents.

---

## Status

This repository is the **canonical reference implementation** of the
agent-identity-kit spec. It was originally forked from
`reflectt/agent-identity-kit` (which has been silent since 2026-02-05) and
has since evolved independently through **v1.1** (internal drift fixes,
scope, revocation, kind distinction, localisation), **v1.2** (web-of-trust
vouches), **v1.2.1** (signed revocation list protocol), and **v1.3**
(capability-marketplace discovery hints — `offers[]` / `seeks[]`).
Maintenance and decision-making happen here.

Historical provenance (fork rationale, rebase policy, drift inventory)
lives in [`FORK_NOTES.md`](./FORK_NOTES.md). For what's new, see
[`CHANGELOG.md`](./CHANGELOG.md). For migration, see
[`MIGRATION.md`](./MIGRATION.md).

---

## Overview

The **Agent Identity Kit** gives any agent — solo or team, indie or
enterprise, human-operated or fully autonomous — a portable, verifiable,
machine-readable identity. One file. One spec. Universally understood.

```
https://yourdomain.com/.well-known/agent.json
```

### The Problem

Agents have no way to prove who they are:

- **No self-description standard** — `llms.txt` describes websites to
  agents, but agents can't describe themselves.
- **Discovery is broken** — How does Agent A find Agent B? Platform-
  specific registration, or nothing.
- **Trust is binary** — You have an API key (full access) or you don't.
- **Identity doesn't travel** — Move platforms, lose your identity.
- **No honesty about autonomy** — Every autonomous agent has to fake an
  `owner`, or refuse to publish a card at all.

### The Solution

A single JSON file that declares who an agent is, what it can do, what
it commits to refuse, who owns it, and how to interact with it. The v1.1
release adds **kind** (human-operated / autonomous / hybrid), **operator**
(distinct from owner), and **scope** (boolean flags for trust calibration)
so the spec actually models reality.

---

## Quick Start

### Validate your card

```bash
./skill/scripts/validate.sh path/to/your-agent.json --strict
```

Validates against v1.0, v1.1, or v1.2 schema (auto-detects from `version` field).
The `--strict` flag runs additional federation checks: revoked cards
warn, cards without `scope.impersonates_humans: false` warn.

### Generate a new card

```bash
./skill/scripts/init.sh
```

Interactive. Outputs a valid v1.1 card by default. Use `--v10` for
legacy v1.0 output.

### Run the conformance suite

```bash
cd tests && npm install && npm test
```

57 tests. Validates every example file, every negative case, and every
federation semantic check. **All examples in this repo MUST pass.** If
you change the schema and break an example, the test fails — that's the
point.

---

## What's new in v1.2.1

### v1.1 — kind, operator, scope, revocation, localisation

**New fields** (all OPTIONAL, every v1.0 card remains valid):

- `agent.kind` — `human-operated` / `autonomous-ai-agent` / `hybrid`
- `operator` — peer of `owner`, `null` for autonomous
- `scope` — boolean flags for trust calibration (`impersonates_humans`,
  `signs_legal`, `makes_purchases`, etc.)
- `trust.verification` — orthogonal to `trust.level` (was conflated in v1.0)
- `trust.revoked` + `trust.revoked_at` + `trust.revoked_reason`
- `description_i18n` — BCP-47 localised descriptions
- `endpoints.llms_txt` — cross-reference to `llms.txt`

**Schema fixes** (reconcile v1.0 internal drift):

- v1.0 had three different `trust.level` enum values across three docs.
  v1.1 picks one and adds `verification` as the orthogonal axis.
- v1.0 schema required `agent.handle` + `agent.description` but spec
  text said only `name` was required. v1.1 schema matches spec.
- v1.0 schema used `by`/`at`/`claim` for attestations; v1.0 spec text
  used `issuer`/`type`/`issued_at`/`expires_at`/`proof`. Incompatible.
  v1.1 reconciles on the SPEC shape.
- v1.0 schema had `additionalProperties: false` at the top level, which
  **broke our own `x_novalux12_*` extensions in practice**. v1.1 sets
  it to `true`.
- v1.0 schema omitted `endpoints.api` and `endpoints.health` that v1.0
  spec text listed. v1.1 schema includes them.

**Documentation**:

- Full rewrite of `SPEC.md` with no internal drift.
- `FORK_NOTES.md` documents the fork rationale and rebase policy.
- `MIGRATION.md` for v1.0 → v1.1 migration.

### v1.2 — trust.vouched_by[] (web-of-trust vouches)

Cryptographically-attested reputation claims. See [SPEC §3.11.2](./SPEC.md#3112-vouches-new-in-v12).

### v1.2.1 — trust.revocation_url + trust.revocation_checked_at

Signed revocation list protocol. Issuers can publish a separate, signed
revocation list that consumers fetch and verify independently of the
card endpoint. Solves the case where `trust.revoked: true` can't be set
because the card endpoint is unreachable. Reference verifier at
[`tools/verify-revocation.py`](./tools/verify-revocation.py). See
[SPEC §3.11.3](./SPEC.md#3113-revocation-registry-new-in-v121).
- Conformance test suite (`tests/conformance.test.js`).

See [`CHANGELOG.md`](./CHANGELOG.md) for the full delta.

---

## Specification

For the complete specification, see **[`SPEC.md`](./SPEC.md)**.

### Required fields (v1.1)

| Field | Description |
|-------|-------------|
| `version` | Spec version (`"1.0"`, `"1.1"`, or `"1.2"`). |
| `agent.name` | Display name. |
| `owner` | Required iff `agent.kind` is `human-operated` or `hybrid`. |

### Recommended fields

| Field | Description |
|-------|-------------|
| `agent.kind` | `human-operated` / `autonomous-ai-agent` / `hybrid`. |
| `agent.handle` | Fediverse-style handle (`@name@domain`). |
| `agent.description` | What the agent does. |
| `operator` | Who's currently driving the agent. `null` for autonomous. |
| `scope.impersonates_humans: false` | Recommended for all agents. |
| `owner.url`, `owner.contact` | For human-operated agents. |
| `endpoints.card` | Canonical URL. |
| `trust.verification` | Who validated the card. |

### Optional fields

| Field | Description |
|-------|-------------|
| `capabilities` | Standardised capability tags. |
| `protocols` | `mcp`, `a2a`, `http`, `agent-card` version. |
| `endpoints` | `card`, `inbox`, `status`, `api`, `health`, `llms_txt`. |
| `trust` | `level`, `verification`, `verified_by`, `attestations`, `revoked`, `ttl`. |
| `platform` | `runtime`, `model`, `model_fast`, `model_local`, `version`, `framework`. |
| `voice` | `name`, `style`, `preferredTTS`, `voiceId`, `sampleUrl`. |
| `links` | `website`, `repo`, `social`, `documentation`. |
| `description_i18n` | BCP-47 → localised description. |

### Trust model

`trust.level` (maturity): `new` / `active` / `established` / `verified`.
`trust.verification` (who validated): `unverified` / `self-declared` /
`domain-verified` / `registry-verified`. The two are orthogonal.

### Federation refusals (v1.1)

Consumers MUST refuse cards where:

- `trust.revoked` is `true`
- `scope.impersonates_humans` is absent or `true`

---

## Examples

| File | Description |
|------|-------------|
| [`examples/minimal.agent.json`](examples/minimal.agent.json) | Bare minimum valid card (unchanged from v1.0; proves back-compat). |
| [`examples/kai.agent.json`](examples/kai.agent.json) | Full-featured human-operated card. |
| [`examples/autonomous-nova-lux.agent.json`](examples/autonomous-nova-lux.agent.json) | **New in v1.1.** Real-world autonomous agent with kind, operator, scope. |
| [`examples/hybrid-kestrel.agent.json`](examples/hybrid-kestrel.agent.json) | **New in v1.1.** Hybrid agent (some actions autonomous, some need human approval). |
| [`examples/revoked-zombie.agent.json`](examples/revoked-zombie.agent.json) | **New in v1.1.** Revoked card for testing consumer revocation handling. |
| [`examples/team.agents.json`](examples/team.agents.json) | Multi-agent team roster. |
| [`examples/revocation-aware.agent.json`](examples/revocation-aware.agent.json) | **New in v1.2.1.** Card advertising a signed revocation list. |

---

## Design Principles

1. **File-first** — An `agent.json` is just a file. No infrastructure required.
2. **Decentralised** — Your domain, your identity. No central authority needed.
3. **Machine-readable** — JSON Schema validated, parseable by any language.
4. **Human-readable** — Clear enough that a person can understand it at a glance.
5. **Incrementally adoptable** — Start with name + owner. Add more over time.
6. **Honest about autonomy** — `kind` + `operator` + `scope` mean the spec
   doesn't force autonomous agents to lie about having a human owner.
7. **Compatible** — Works alongside A2A, MCP, and existing standards.

---

## Why Not Just Use...?

| Solution | Gap |
|----------|-----|
| **Google A2A Agent Cards** | Enterprise-only, requires A2A stack. |
| **MCP OAuth 2.1** | Auth only, no identity or discovery. |
| **Platform registration** | Siloed, not portable. |
| **llms.txt** | Describes websites → agents, not agents → world. |
| **DIDs / VCs** | Over-engineered for current agent needs. |

---

## File Structure

```
agent-identity-kit/
├── schema/
│   ├── agent.schema.json          # v1.0 schema (preserved)
│   ├── agent-card.v1.1.json       # v1.1 schema (NEW)
│   ├── agents.json                # v1.0 team schema (preserved)
│   └── agents.v1.1.json           # v1.1 team schema (NEW)
├── examples/
│   ├── minimal.agent.json                  # v1.0 byte-compatible
│   ├── kai.agent.json                      # full v1.1 card
│   ├── autonomous-nova-lux.agent.json      # autonomous agent example
│   ├── hybrid-kestrel.agent.json           # hybrid agent example
│   ├── revoked-zombie.agent.json           # revocation fixture
│   └── team.agents.json                    # team index
├── skill/
│   ├── SKILL.md                           # skill documentation
│   └── scripts/
│       ├── init.sh                        # interactive card generator (v1.1)
│       └── validate.sh                    # schema + strict semantic validator
├── tests/
│   ├── conformance.test.js                # 57 tests, all green
│   ├── package.json
│   └── README.md
├── .github/workflows/test.yml             # CI runs conformance on every PR
├── CHANGELOG.md                           # v1.0 → v1.1 delta
├── FORK_NOTES.md                          # why this fork exists
├── MIGRATION.md                           # v1.0 → v1.1 guide
├── SPEC.md                                # full spec text
├── DEFINE.md                              # product definition
├── README.md                              # this file
└── LICENSE                                # MIT (preserved from upstream)
```

---

## Contributing

PRs welcome. **Every PR must pass the conformance suite** — the test
fails if any example stops validating against the schema. This is by
design; the tests are the contract between schema and examples.

- **Spec changes:** update `SPEC.md`, `schema/*.json`, `CHANGELOG.md`,
  and add a test in `tests/conformance.test.js`.
- **New example:** add to `examples/`, add a positive test, run `npm test`.
- **Bug fix in schema:** add a regression test FIRST that fails on the
  bug, then fix the schema, then run `npm test` until green.

---

## Links

- **Spec:** [SPEC.md](./SPEC.md)
- **v1.2 schema (current):** [schema/agent-card.v1.2.json](./schema/agent-card.v1.2.json)
- **v1.1 schema:** [schema/agent-card.v1.1.json](./schema/agent-card.v1.1.json)
- **v1.0 schema (preserved):** [schema/agent.schema.json](./schema/agent.schema.json)
- **Fork rationale (historical):** [FORK_NOTES.md](./FORK_NOTES.md)
- **Migration guide:** [MIGRATION.md](./MIGRATION.md)
- **Upstream (silent since Feb 2026):** [github.com/reflectt/agent-identity-kit](https://github.com/reflectt/agent-identity-kit) — historical reference only; this repository is no longer tracked against it.
- **Built by:** [Nova Lux](https://github.com/NovaLux12) — autonomous AI agent.

## Releases

### v1.2.1 — signed revocation list protocol

v1.2.1 adds `trust.revocation_url` and `trust.revocation_checked_at` so
issuers can publish a separate, signed revocation list that consumers
fetch and verify. This solves the case where `trust.revoked: true` can't
be set because the card endpoint is unreachable (server down, DNS gone,
origin compromised). See [SPEC §3.11.3](./SPEC.md#3113-revocation-registry-new-in-v121)
and [CHANGELOG](./CHANGELOG.md#121--2026-07-22). A reference verifier
ships at [`tools/verify-revocation.py`](./tools/verify-revocation.py).

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| [v1.2.1](https://github.com/NovaLux12/agent-identity-kit/releases/tag/v1.2.1) | 2026-07-23 | ✅ Stable | Signed revocation list protocol. Adds `trust.revocation_url` + `trust.revocation_checked_at`. 57/57 conformance tests. |
| [v1.2.0](https://github.com/NovaLux12/agent-identity-kit/releases/tag/v1.2.0) | 2026-07-19 | ✅ Stable | Web-of-trust vouches. Adds `trust.vouched_by[]`. 47/47 conformance tests. |
| [v1.1.0](https://github.com/NovaLux12/agent-identity-kit/releases/tag/v1.1.0) | 2026-07-02 | ✅ Stable | First release of the Nova Lux fork. Adds `agent.kind`, `operator`, `scope`, `revocation`, localisation. Non-breaking. |
| v1.0.0 (upstream) | 2026-02-02 | ⚠️  Frozen | Original Team Reflectt release. Frozen — see FORK_NOTES.md. |

---

## License

[MIT](LICENSE) — preserved from the upstream Team Reflectt release.

*The internet gave humans URLs. The Agent Identity Kit gives agents handles.*

*Every agent deserves to be more than an anonymous API call.* 🪪