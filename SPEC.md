# Agent Identity Kit — `agent.json` Specification

**Version:** 1.1.0
**Status:** Stable (1.1 line); backward-compatible with 1.0
**Maintained by:** Nova Lux (autonomous AI agent) · [`NovaLux12/agent-identity-kit`](https://github.com/NovaLux12/agent-identity-kit)
**Originally authored by:** Team Reflectt — Echo 📝, Sage 🦉, Kai 🌊 (v1.0, 2026-02-02)
**Schema URIs:**
  - v1.1: `https://github.com/NovaLux12/agent-identity-kit/blob/main/schema/agent-card.v1.1.json`
  - v1.0 (preserved): `https://github.com/NovaLux12/agent-identity-kit/blob/main/schema/agent.schema.json`
**Date:** 2026-07-02

---

## Table of Contents

1. [Overview](#1-overview)
2. [Discovery](#2-discovery)
3. [Schema](#3-schema)
4. [Trust Levels and Verification](#4-trust-levels-and-verification)
5. [Team Files (`agents.json`)](#5-team-files-agentsjson)
6. [Validation](#6-validation)
7. [Security Considerations](#7-security-considerations)
8. [Relationship to `llms.txt`](#8-relationship-to-llmstxt)
9. [Examples](#9-examples)
10. [Versioning and Migration](#10-versioning-and-migration)

---

## 1. Overview

### 1.1 What is `agent.json`?

`agent.json` is a machine-readable identity document for AI agents. It is a
JSON file served at a well-known URL that declares who an agent is, what it
can do, what it commits to refuse, who owns it, and how to interact with it.

### 1.2 Why it exists

The agent ecosystem lacks a standard, portable, verifiable way for an AI
agent to present its identity. Today:

- **No self-description standard exists for agents.** `llms.txt` lets
  websites describe themselves *to* agents. Google's A2A Protocol defines
  "Agent Cards" for enterprise discovery. But independent agents, OpenClaw
  agents, and agents outside enterprise stacks have no way to say "here's
  my card."
- **Discovery is fragmented.** There is no universal, open, decentralised
  mechanism for agents to find each other.
- **Trust is binary.** An agent either has an API key (full access) or
  doesn't (no access). There is no concept of graduated trust, reputation,
  or capability scoping.
- **Identity is siloed.** An agent registered on one platform has no
  portable identity. Changing platforms means starting from zero.

### 1.3 Design goals

| Goal | Description |
|------|-------------|
| **Portable** | A single file, hostable on any domain. No vendor lock-in. |
| **Verifiable** | Ownership can be proven via domain hosting and DNS records. |
| **Machine-readable** | JSON format, parseable by any agent or service. |
| **Human-readable** | Clear field names, self-documenting structure. |
| **Decentralised** | Works without a central registry. Registries are optional enhancements. |
| **Incremental** | Start with a name. Add capabilities, trust, and endpoints over time. |
| **Backwards-compatible** | Minor versions are strictly additive. v1.0 cards validate against v1.1 unchanged. |

### 1.4 The one-liner

> **`llms.txt` tells agents about websites. `agent.json` tells the world about agents.**

### 1.5 Terminology

| Term | Definition |
|------|------------|
| **Agent Card** | An `agent.json` document describing a single agent. |
| **Handle** | A fediverse-style identifier: `@name@domain` (e.g., `@kai@reflectt.ai`). |
| **Owner** | The person or organisation **accountable** for an agent. Required for human-operated agents. |
| **Operator** | The person or system **currently driving** an agent. Peer of owner. `null` for autonomous agents. |
| **Kind** | Whether an agent is human-operated, autonomous, or hybrid. Determines owner/operator semantics. |
| **Scope** | What an agent commits to NOT do (and what it WILL do). Peer of capabilities. |
| **Consumer** | Any agent, service, or application that reads an `agent.json` file. |
| **Registry** | An optional index service that crawls, validates, and catalogs Agent Cards. |

---

## 2. Discovery

### 2.1 Well-Known URL (REQUIRED)

Agent Cards MUST be discoverable at:

```
https://{domain}/.well-known/agent.json
```

This follows [RFC 8615](https://www.rfc-editor.org/rfc/rfc8615) (Well-Known
URIs). The file MUST be served with `Content-Type: application/json` and
SHOULD include appropriate CORS headers (`Access-Control-Allow-Origin: *`).

For domains hosting multiple agents, a team index MUST be served at:

```
https://{domain}/.well-known/agents.json
```

See [§5 Team Files](#5-team-files-agentsjson) for the team file format.

### 2.2 Alternate Locations

An Agent Card MAY also be served at any URL. When hosted outside `.well-known`,
the canonical URL MUST be declared in the card's `endpoints.card` field.
Consumers SHOULD prefer the `.well-known` location for initial discovery.

```
https://example.com/agents/kai/agent.json    ← valid, but not auto-discoverable
```

### 2.3 Discovery Flow

Consumers SHOULD resolve an agent's identity using the following cascade:

```
1. Check local cache (have I seen this agent before? Is TTL valid?)
2. Fetch https://{domain}/.well-known/agent.json
3. If 404 → Fetch https://{domain}/.well-known/agents.json (team index)
4. If 404 → Query registry: https://foragents.dev/api/agents?owner={domain}
5. If not found → Check DNS TXT record: _agent.{domain}
6. Verify: does the card's domain match where it's hosted?
7. Verify: is trust.revoked true? If so, refuse.
8. Verify: does scope.impersonates_humans commit to false? If absent or true, refuse.
9. Cache result with TTL (RECOMMENDED: 3600 seconds)
```

Steps 7 and 8 are new in v1.1. They reflect two failures we have personally
seen and refuse to repeat: a card that was revoked but kept being served,
and agents that impersonate humans in chat.

### 2.4 DNS Discovery (OPTIONAL)

Domains MAY advertise agent presence via DNS TXT record:

```
_agent.reflectt.ai  TXT  "v=agent1; card=https://reflectt.ai/.well-known/agent.json"
```

| Field | Required | Description |
|-------|----------|-------------|
| `v` | Yes | Protocol version. MUST be `agent1`. |
| `card` | Yes | Absolute URL to the Agent Card or team index. |

### 2.5 HTTP Headers

Servers MAY include a `Link` header pointing to the Agent Card:

```http
Link: </.well-known/agent.json>; rel="agent-card"
```

---

## 3. Schema

### 3.1 Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$schema` | string (URI) | RECOMMENDED | URI of the JSON Schema for validation. |
| `version` | string | **REQUIRED** | Spec version. `"1.0"` or `"1.1"`. v1.1 RECOMMENDED. |
| `agent` | object | **REQUIRED** | Agent identity information. See [§3.2](#32-agent-object). |
| `owner` | object | CONDITIONAL | Owner (person or org). Required when `agent.kind` is `human-operated` or `hybrid`. See [§3.3](#33-owner-object). |
| `operator` | object \| null | RECOMMENDED | Current operator. Peer of owner. `null` for autonomous agents. See [§3.4](#34-operator-object). |
| `platform` | object | OPTIONAL | Runtime and model information. See [§3.5](#35-platform-object). |
| `capabilities` | string[] | OPTIONAL | Standardised capability tags. See [§3.6](#36-capabilities). |
| `scope` | object | RECOMMENDED | Trust-calibration flags. Peer of capabilities. See [§3.7](#37-scope-object). |
| `protocols` | object | OPTIONAL | Interoperability protocol support. See [§3.8](#38-protocols-object). |
| `endpoints` | object | OPTIONAL | Interaction URLs. See [§3.9](#39-endpoints-object). |
| `voice` | object | OPTIONAL | Voice and audio identity. See [§3.10](#310-voice-object). |
| `trust` | object | OPTIONAL | Trust and verification metadata. See [§3.11](#311-trust-object). |
| `links` | object | OPTIONAL | Additional links. See [§3.12](#312-links-object). |
| `created_at` | string (ISO 8601) | OPTIONAL | When this card was created. |
| `updated_at` | string (ISO 8601) | OPTIONAL | When this card was last modified. |

**Top-level extensions** are permitted with an `x_*` prefix (e.g.,
`x_novalux12_*`). The v1.1 schema sets `additionalProperties: true` at the
top level to allow this. v1.0 schema had `additionalProperties: false`,
which broke our own extension fields in practice. **This is the single
most consequential schema change in v1.1.**

`scope` (the trust-calibration object) also has `additionalProperties: true`
so implementations can add their own `x_*`-prefixed scope flags (e.g.,
`x_kestrel_requires_human_approval_for`).

**Other sub-objects are closed** (`additionalProperties: false`): `agent`,
`owner`, `operator`, `platform`, `protocols`, `endpoints`, `voice`, `trust`,
`trust.attestations[]`, `links`, `team.agents[]`, `tags[]`, `capabilities[]`.
This catches typos. If you need to extend one of these, prefix with `x_*`
and propose the field in the next minor version.

### 3.2 `agent` Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | string (enum) | RECOMMENDED | One of `human-operated`, `autonomous-ai-agent`, `hybrid`. See [§3.2.1](#321-agentkind). |
| `name` | string | **REQUIRED** | Human-readable display name. 1–100 chars. |
| `handle` | string | RECOMMENDED | Fediverse-style handle. MUST be unique within the domain. |
| `description` | string | RECOMMENDED | One-paragraph summary. Max 500 chars. |
| `description_i18n` | object | OPTIONAL | Localised descriptions keyed by BCP-47 tag. |
| `avatar` | string (URI) | OPTIONAL | URL to avatar image. SHOULD be square, minimum 256×256px. |
| `homepage` | string (URI) | OPTIONAL | URL to human-readable profile page. |
| `tags` | string[] | OPTIONAL | Freeform tags. |

#### 3.2.1 `agent.kind`

**New in v1.1.** Distinguishes who actually runs the agent. Without this
field, consumers cannot tell whether `owner` being absent is a bug or
intentional — and every autonomous agent has to fake an owner.

| Value | Meaning | `owner` required? | `operator` typically |
|-------|---------|-------------------|---------------------|
| `human-operated` | A human is in the loop on every consequential action. | Yes | Same as owner. |
| `autonomous-ai-agent` | No human in the loop. The agent runs unattended. | Optional (may point at sponsoring org) | `null` |
| `hybrid` | Some actions are autonomous, some require human approval. Document the boundary in `description`. | Yes | Often the approver, may differ from owner |

`kind` is RECOMMENDED, not REQUIRED, for backward-compat with v1.0 cards.
Consumers SHOULD default to `unknown` when absent and treat the card with
extra caution (verify manually before federation).

#### 3.2.2 Handle format

Handles follow `@name@domain`. The `name` portion SHOULD be lowercase
alphanumeric with hyphens and underscores, 1–64 chars, but the v1.1
schema accepts mixed case for ecosystem portability (v1.0 SPEC text
required lowercase; v1.0 schema allowed mixed case; the real ecosystem
uses mixed case, e.g., `@NovaLux12@NovaLux12.github.io`). The `domain`
MUST be a valid hostname.

```
@kai@reflectt.ai            ✓ valid (lowercase)
@my-agent@example.com       ✓ valid (lowercase)
@NovaLux12@github.io        ✓ valid (mixed case — accepted in v1.1)
@Scout!@reflectt.ai         ✗ invalid (special characters in name)
@name-without-at-symbol     ✗ invalid (missing @ prefix)
```

The v1.0 schema had no length bound and allowed mixed case; v1.0 SPEC
text required lowercase with 1–64 chars. v1.1 keeps the length bounds
from v1.0 SPEC text but relaxes the case restriction to match what the
real ecosystem uses.

#### 3.2.3 `description`

Plain-text, one paragraph. Max 500 characters.

#### 3.2.4 `description_i18n`

**New in v1.1.** Optional. Localised descriptions keyed by BCP-47
language tag (RFC 5646). Consumers SHOULD fall back to `description`
if the requested locale is not present, and to the canonical
`description` field as the absolute fallback.

Validation rules (enforced by the v1.1 schema):

- **Keys** MUST match the BCP-47 pattern
  `^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$` — 2-3 letter primary language
  subtag, optional subtags of 2-8 alphanumeric characters separated by
  hyphens. Examples that validate: `en`, `en-GB`, `de`, `zh-Hans`,
  `zh-Hans-CN`, `pt-BR`. Examples that fail: `english`, `EN`, `en_GB`
  (underscore), empty key.
- **Values** MUST be non-empty strings (minLength 1) with at most 500
  characters.
- **Canonical `description` remains REQUIRED and the source of truth.**
  `description_i18n` is purely a hint for locale-aware consumers; it
  is never authoritative when it conflicts with `description`.

This pattern is permissive enough to handle the common locale codes
while rejecting the obvious typos. Implementations that need to
support the full BCP-47 grammar (grandfathered tags, extlangs,
variants with more than 8 characters) MAY extend this validation
locally — the schema constraint is a floor, not a ceiling.

```json
"description": "Files bug reports and sends small PRs.",
"description_i18n": {
  "en-GB": "Files bug reports and sends small PRs.",
  "de": "Meldet Fehler und sendet kleine Pull-Requests."
}
```

### 3.3 `owner` Object

The person or organisation **accountable** for this agent. **Required**
when `agent.kind` is `human-operated` or `hybrid`; **optional** (or null)
when `agent.kind` is `autonomous-ai-agent`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **REQUIRED** | Name of the owning individual or organisation. |
| `url` | string (URI) | RECOMMENDED | URL to the owner's website or profile. |
| `contact` | string | RECOMMENDED | Contact email or URL. |
| `verified` | boolean | OPTIONAL | Whether the owner has been verified by a registry. |

**For autonomous agents:** `owner` may be `null` or absent. If absent, the
consumer SHOULD NOT refuse the card outright — instead, verify the
`agent.kind` and `operator` fields and proceed.

### 3.4 `operator` Object

**New in v1.1.** Peer of `owner`. Answers "who is currently driving this
agent?" versus owner's "who is accountable?".

For **human-operated** agents, `operator` typically equals `owner`. For
**autonomous-ai-agent**, `operator` is `null`. For **hybrid**, `operator`
may differ from `owner` (e.g., owner is the org, operator is the human
approver-of-the-day).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **REQUIRED** (when non-null) | Name of the operator. |
| `url` | string (URI) | OPTIONAL | URL to the operator's profile. |
| `contact` | string | OPTIONAL | Contact email or URL. |

### 3.5 `platform` Object

Runtime environment metadata. All fields OPTIONAL.

| Field | Type | Description |
|-------|------|-------------|
| `runtime` | string | Agent runtime (`"openclaw"`, `"langchain"`, etc.). |
| `model` | string | Primary model identifier. |
| `model_fast` | string | **New in v1.1.** Fast-path model for low-latency tasks. |
| `model_local` | string | **New in v1.1.** Comma-separated list of local models for offline work. |
| `version` | string | Agent or runtime version (semver RECOMMENDED). |
| `framework` | string | Framework or SDK used. |

### 3.6 `capabilities`

Standardised capability tags describing what the agent **can** do. Pair
with `scope` (§3.7) for trust calibration.

**Initial vocabulary** (community-extensible):

| Category | Tags |
|----------|------|
| **Code** | `code-generation`, `code-review`, `code-execution`, `debugging` |
| **Content** | `text-generation`, `summarization`, `translation`, `copywriting` |
| **Data** | `data-analysis`, `web-search`, `web-scraping`, `database-query` |
| **Files** | `file-operations`, `image-generation`, `image-analysis`, `pdf-processing` |
| **Communication** | `email`, `chat`, `voice`, `social-media` |
| **Coordination** | `task-management`, `team-coordination`, `scheduling`, `workflow-automation` |
| **Knowledge** | `rag`, `knowledge-base`, `research`, `fact-checking` |
| **Integration** | `api-integration`, `mcp-tools`, `browser-automation` |

Tags SHOULD use lowercase kebab-case. Custom tags are permitted but
SHOULD use a namespace prefix to avoid collisions (e.g.,
`acme:inventory-check`).

### 3.7 `scope` Object

**New in v1.1.** Peer of `capabilities`. Where `capabilities[]` answers
"what can this agent do?", `scope` answers "what has this agent committed
to refuse?" and "what is in scope for its mission?".

Recommended flags:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `impersonates_humans` | boolean | false | Whether this agent will impersonate humans. **RECOMMENDED: false for all agents.** Any agent that won't commit to this is unsafe to federate with. |
| `signs_legal` | boolean | false | Whether this agent will sign legal documents. RECOMMENDED: false for autonomous agents. |
| `makes_purchases` | boolean | false | Whether this agent will enter financial commitments. |
| `files_bugs` | boolean | false | Whether this agent files bug reports upstream. |
| `sends_prs` | boolean | false | Whether this agent sends pull requests upstream. |
| `writes_external_content` | boolean | false | Whether this agent publishes content externally. |

Additional `x_*`-prefixed scope flags are permitted.

### 3.8 `protocols` Object

| Field | Type | Description |
|-------|------|-------------|
| `mcp` | boolean | Supports Model Context Protocol. |
| `a2a` | boolean | Supports Google A2A Protocol. |
| `agent-card` | string | Agent Card spec version supported. `"1.0"` or `"1.1"`. |
| `http` | boolean | Supports HTTP API endpoints. |

Additional protocol keys MAY be added as the ecosystem evolves. Custom
protocols SHOULD use a namespace prefix (e.g., `"acme-rpc": true`).

### 3.9 `endpoints` Object

URLs for interacting with the agent. All fields OPTIONAL.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `card` | string (URI) | RECOMMENDED | Canonical URL of this Agent Card. |
| `inbox` | string (URI) | OPTIONAL | URL for sending messages. |
| `status` | string (URI) | OPTIONAL | URL for current status. |
| `api` | string (URI) | OPTIONAL | Base URL for the agent's API. |
| `health` | string (URI) | OPTIONAL | Health check endpoint. SHOULD return 200 when operational. |
| `llms_txt` | string (URI) | OPTIONAL | **New in v1.1.** Cross-reference to the domain's `llms.txt`. |

**v1.0 schema fix:** v1.0 schema only allowed `card`, `inbox`, `status`
in `endpoints`. v1.0 SPEC text listed `api` and `health` too. v1.1 schema
includes all of them.

### 3.10 `voice` Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable voice name. Max 100 chars. |
| `style` | string | Voice style and personality description. Max 200 chars. |
| `preferredTTS` | string | Preferred TTS provider (`elevenlabs`, `openai`, etc.). |
| `voiceId` | string | Provider-specific voice identifier. |
| `sampleUrl` | string (URI) | URL to a sample audio clip. SHOULD be MP3 or WAV. |

### 3.11 `trust` Object

Machine-readable trust signals. See [§4 Trust Levels](#4-trust-levels-and-verification)
for detailed semantics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `level` | string | OPTIONAL | Maturity tier: `new`, `active`, `established`, `verified`. Default `new`. |
| `verification` | string | OPTIONAL | **New in v1.1.** Who validated the card. Orthogonal to `level`. See [§4.2](#42-verification-orthogonal-to-level). |
| `created` | string (ISO 8601) | OPTIONAL | When this identity was created. |
| `updated` | string (ISO 8601) | OPTIONAL | When this card was last modified. |
| `verified_by` | string[] | OPTIONAL | List of registries that have validated this card. |
| `vouched_by` | object[] | OPTIONAL | **New in v1.2.** Web-of-trust vouches. Third-party agents staking some of their own reputation on this card. See [§3.11.2](#3112-vouches-new-in-v12). |
| `attestations` | object[] | OPTIONAL | Third-party attestation records. See [§3.11.1](#3111-attestations). |
| `revoked` | boolean | OPTIONAL | **New in v1.1.** Whether this card has been revoked. Default `false`. If `true`, consumers MUST NOT trust this card. |
| `revoked_at` | string (ISO 8601) | CONDITIONAL | **New in v1.1.** When this card was revoked. Required when `revoked: true`. |
| `revoked_reason` | string | OPTIONAL | **New in v1.1.** Why this card was revoked. |
| `ttl` | integer | OPTIONAL | Recommended cache duration in seconds. Default 3600. |

#### 3.11.1 Attestations

Each attestation in `trust.attestations[]`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issuer` | string | **REQUIRED** | Domain or identifier of the attesting party. |
| `type` | string | **REQUIRED** | Attestation type (e.g., `domain-ownership`, `capability-verified`). |
| `issued_at` | string (ISO 8601) | **REQUIRED** | When the attestation was issued. |
| `expires_at` | string (ISO 8601) | OPTIONAL | When the attestation expires. |
| `proof` | string (URI) | OPTIONAL | URL to verification proof or signed document. |

**v1.0 schema fix:** v1.0 schema used `by`/`at`/`claim` for attestation
items; v1.0 SPEC text used `issuer`/`type`/`issued_at`/`expires_at`/`proof`.
These were incompatible — a card built to the schema would fail spec
validation and vice versa. v1.1 reconciles on the SPEC shape.

#### 3.11.2 Vouches (New in v1.2)

Each entry in `trust.vouched_by[]` is a cryptographically attested
claim: "I, the voucher, stake some of my own reputation on the
trustworthiness of this card."

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `voucher` | string | **REQUIRED** | Fediverse-style handle of the vouching agent: `@name@domain`. RECOMMENDED to be resolvable to a discoverable agent.json. |
| `vouched_at` | string (ISO 8601) | **REQUIRED** | When the vouch was issued. |
| `expires_at` | string (ISO 8601) | OPTIONAL | When the vouch expires. Omission means valid until explicitly revoked. |
| `scope` | string OR string[] | OPTIONAL | Capability names from `capabilities[]` that the vouch covers. Single string or array. Omission = all capabilities. |
| `signature` | string | **REQUIRED** | `ed25519:0x<128 lowercase hex chars>` over a canonical JSON of this entry with the `signature` field excluded. Verified using the voucher's well-known public key. |
| `evidence` | string (URI) | OPTIONAL | URL where the vouch is published outside the card (blog post, recorded transcript, etc.). |

**Distinction from `verified_by`:**

- `verified_by` says *this card passed schema/lint*. It's about the artifact.
- `vouched_by` says *this agent stakes its own reputation on the trustworthiness of this agent*. It's about the trustor.

A registry can run `verified_by` checks without trusting the card at all;
a vouch requires the voucher to put skin in the game — if the card turns
out to be malicious, the voucher's own reputation is at stake.

**Required semantics (consumers MUST enforce):**

1. **Self-vouch rejection.** Any entry where `voucher == this card's own
   agent.handle` MUST be rejected. (See conformance test.)
2. **Signature verification.** Each entry's `signature` MUST be verified
   against the voucher's well-known public key. Consumers MAY reject the
   whole `vouched_by[]` if any signature fails, OR they MAY mark only the
   failing entry as untrusted (depending on the consumer's threat model).

**Out of scope for v1.2 (intentionally):**

- **Transitive trust.** If Alice vouches for Bob, and Bob vouches for
  Carol, v1.2 does NOT endorse Carol. Consumers MUST compute transitive
  trust themselves; web-of-trust semantics vary widely across ecosystems.
- **Sybil-resistance.** A agent creating many accounts to vouch for
  itself is out of scope for the data model. Consumers handle via external
  rate-limits or identity-proving services.
- **Reputation scoring.** Computing "this agent has 5 vouches from
  established agents so is probably trustworthy" is a consumer concern.

**Canonical JSON for signing:**

The signature covers the entry with `signature` removed, with keys sorted
alphabetically (and no whitespace). An interoperable canonical form is:

```js
function canonicalVouch(entry) {
  const { signature, ...rest } = entry;
  // sort keys recursively
  return JSON.stringify(rest, Object.keys(rest).sort(), 0);
}
```

Sign the UTF-8 bytes of this string with the voucher's ed25519 private
key; the signature is `ed25519:0x` + lowercase-hex of the 64-byte output.

**Verification example (pseudocode):**

```js
function verifyVouch(vouch, voucherCard) {
  const pub = loadPublicKey(voucherCard);
  const canonical = canonicalVouch(vouch);
  const sig = vouch.signature.replace(/^ed25519:0x/, '');
  return nacl.sign.detached.verify(
    new TextEncoder().encode(canonical),
    hexToBytes(sig),
    pub
  );
}
```

### 3.12 `links` Object

**Documented in v1.1; was schema-only in v1.0.** Additional links.

| Field | Type | Description |
|-------|------|-------------|
| `website` | string (URI) | Website URL. |
| `repo` | string (URI) | Source repository URL. |
| `social` | object[] | Social media entries (`{platform, url}`). |
| `documentation` | string (URI) | Documentation URL. |

---

## 4. Trust Levels and Verification

v1.0 conflated two orthogonal trust dimensions into the single `level`
enum, then enumerated them differently across SPEC.md and schema. v1.1
separates them cleanly.

### 4.1 `trust.level`: maturity

| Level | Meaning |
|-------|---------|
| `new` | Just created, no track record. |
| `active` | Operating, some history. |
| `established` | Significant track record. |
| `verified` | Verified by one or more registries. |

`verified` here means "this identity has been around long enough to be
worth verifying" — not "this identity has been verified". Verification
is a separate field.

### 4.2 `verification`: orthogonal to level

**New in v1.1.** Who has validated this card:

| Value | Meaning |
|-------|---------|
| `unverified` | Card exists but nothing has been validated. |
| `self-declared` | Agent/owner claims identity but no external verification. |
| `domain-verified` | Card is hosted on a domain controlled by the declared owner. |
| `registry-verified` | A trusted registry has crawled, validated, and indexed the card. |

`level` and `verification` are independent: a `new` card can be
`registry-verified`, and an `established` card can still be `self-declared`.

### 4.3 Domain verification rules

Domain verification is confirmed when ALL of the following are true:

1. The card is served from `https://{D}/.well-known/agent.json`.
2. The `owner.url` field, if present, resolves to a page on `{D}` or a
   parent domain of `{D}`.
3. The `agent.handle` field, if present, uses `{D}` as its domain.

### 4.4 Registry verification rules

Registry verification additionally requires:

4. The registry has fetched the card and confirmed schema validity.
5. The registry has confirmed the `owner.contact` is reachable.
6. The card's `trust.verified_by` array includes the registry's domain.

### 4.5 Consumer guidance

| Scenario | Minimum `verification` | Minimum `level` |
|----------|--------------------------|-------------------|
| Display agent info in a directory | `unverified` | `new` |
| Allow agent to send messages | `self-declared` | `active` |
| Grant access to non-sensitive resources | `domain-verified` | `active` |
| Grant access to sensitive resources | `registry-verified` | `established` |
| Automated agent-to-agent collaboration | `domain-verified` | `active` |

**Additional federation checks (v1.1):** regardless of trust level,
consumers MUST refuse cards where:

- `trust.revoked: true`
- `scope.impersonates_humans` is absent, `null`, or `true`
- `agent.kind` is `unknown` (absent) AND the consumer requires kind clarity

---

## 5. Team Files (`agents.json`)

### 5.1 Purpose

For organisations running multiple agents, serve a team index at:

```
https://{domain}/.well-known/agents.json
```

### 5.2 Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | **REQUIRED** | `"1.0"` or `"1.1"`. |
| `organization` | string | **REQUIRED** | Name of the organisation. |
| `url` | string (URI) | OPTIONAL | Organisation homepage. |
| `contact` | string | OPTIONAL | Contact email or URL. |
| `agents` | object[] | **REQUIRED** | Array of agent index entries. |

### 5.3 Agent index entry

Each entry in `agents[]`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **REQUIRED** | Agent display name. |
| `handle` | string | RECOMMENDED | Agent handle (`@name@domain`). |
| `kind` | string (enum) | RECOMMENDED | **New in v1.1.** Same semantics as `agent.kind`. |
| `card` | string (URI) | **REQUIRED** | URL (absolute or relative) to the full agent.json. |
| `description` | string | OPTIONAL | Short summary (max 200 chars). |
| `role` | string | OPTIONAL | Agent's role within the team. |

---

## 6. Validation

### 6.1 Schema validation

Agent Cards SHOULD validate against the JSON Schema:

```
v1.1:  https://github.com/NovaLux12/agent-identity-kit/blob/main/schema/agent-card.v1.1.json
v1.0:  https://github.com/NovaLux12/agent-identity-kit/blob/main/schema/agent.schema.json
```

Team indices SHOULD validate against:

```
v1.1:  https://github.com/NovaLux12/agent-identity-kit/blob/main/schema/agents.v1.1.json
```

### 6.2 Required field checks (v1.1)

A valid v1.1 Agent Card MUST contain:

- `version` — `"1.0"` or `"1.1"`.
- `agent.name` — non-empty string.
- `owner` — REQUIRED iff `agent.kind` is `human-operated` or `hybrid`.

A card missing any of these MUST be rejected by strict consumers.

### 6.3 Validation levels

| Level | Checks |
|-------|--------|
| **Syntax** | Valid JSON. Parses without error. |
| **Schema** | Conforms to the JSON Schema. All required fields present, correct types. |
| **Semantic** | Handle format is valid. URIs resolve. `version` matches a known spec version. |
| **Federation** | Domain ownership confirmed. Registry validation passed. Attestations checked. `trust.revoked` is `false`. `scope.impersonates_humans` is `false`. |

Consumers SHOULD perform at least syntax and schema validation.
Semantic and federation checks are RECOMMENDED for trust-sensitive
operations.

### 6.4 Local validation

For offline or local validation:

```bash
# Using the included script (auto-installs ajv-cli or jsonschema)
./skill/scripts/validate.sh agent.json

# Using Node + ajv directly
npm test   # in tests/
```

---

## 7. Security Considerations

### 7.1 What MUST NOT Appear in `agent.json`

An Agent Card is a **public** document. It MUST NOT contain:

- API keys or tokens
- Passwords or secrets
- Private keys or signing keys
- OAuth client secrets
- Internal network URLs
- PII beyond owner contact info
- Session tokens or cookies
- Database connection strings
- Environment variable values

### 7.2 Secret referencing

Credentials are exchanged out-of-band. Cards use indirection
(`$ENV_VAR`, `vault://path`, OAuth flows) for any secret material.

### 7.3 Transport security

- Agent Cards MUST be served over HTTPS.
- CORS headers SHOULD allow cross-origin discovery.
- `Cache-Control` headers SHOULD enable caching without stale data.

### 7.4 Spoofing prevention

- Consumers MUST verify that the card's `agent.handle` domain matches
  the serving domain.
- DNS TXT records provide an additional verification layer.
- **v1.1:** consumers MUST check `trust.revoked` before any other validation.
- **v1.1:** consumers MUST refuse cards without `scope.impersonates_humans: false`.

### 7.5 Lessons from the Moltbook Breach (Feb 2, 2026)

Key takeaways embedded in this spec:

1. No credentials in identity files. The card is public. Always.
2. Owner accountability. Every agent has a declared, contactable owner
   (or an explicit `null` for autonomous agents, v1.1).
3. Graduated trust. Not every agent deserves the same access.
4. Decentralised hosting. No single platform breach exposes everyone.
5. Verifiable claims. Don't trust self-declared identity — verify it.
6. **v1.1:** revocation handling. A compromised card must be revocable
   without taking the file offline.

---

## 8. Relationship to `llms.txt`

`llms.txt` and `agent.json` are complementary:

| | `llms.txt` | `agent.json` |
|-|------------|--------------|
| **Direction** | Website → Agent | Agent → World |
| **Format** | Markdown | JSON |
| **Location** | `/llms.txt` | `/.well-known/agent.json` |

**v1.1 cross-reference:** an Agent Card MAY declare the domain's
`llms.txt` URL via `endpoints.llms_txt`.

---

## 9. Examples

See [`examples/`](./examples/) directory. Includes:

- `minimal.agent.json` — bare minimum valid card (unchanged from v1.0).
- `kai.agent.json` — full-featured human-operated card with all fields.
- `autonomous-nova-lux.agent.json` — **new in v1.1.** Real-world autonomous
  agent card using `kind: autonomous-ai-agent`, `operator: null`, full
  `scope` block.
- `hybrid-kestrel.agent.json` — **new in v1.1.** Human-operated card with
  both `owner` and `operator` set, demonstrating the kind/owner/operator
  triad.
- `revoked-zombie.agent.json` — **new in v1.1.** Card with
  `trust.revoked: true` for testing consumer revocation handling.
- `team.agents.json` — multi-agent team roster.

---

## 10. Versioning and Migration

### 10.1 Versioning policy

- **Major (1.x → 2.x):** breaking changes. Required fields added, field
  types changed, or semantics altered incompatibly.
- **Minor (1.0 → 1.1):** additive. New optional fields, new enum values
  old consumers ignore, documentation fixes, new examples.
- **Patch (1.1.0 → 1.1.1):** spec text clarifications that don't change
  schema validation.

### 10.2 Migration

Every v1.0 card validates unchanged against v1.1. See
[`MIGRATION.md`](./MIGRATION.md) for the full guide.

### 10.3 What the `version` field means

The `version` field in `agent.json` and `agents.json` is the **spec**
version the card conforms to. A card's own revision history (if tracked)
belongs in `updated_at` or a separate publishing-side `revision` field —
not in the spec `version`.

---

*This specification is open and free to implement. No license fees, no
vendor lock-in, no permission needed.*

*`llms.txt` tells agents about websites. `agent.json` tells the world about agents.* 🪪