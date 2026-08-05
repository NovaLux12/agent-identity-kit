# Migrating from v1.0 to v1.1

**TL;DR: do nothing.** v1.1 is additive. Every v1.0 Agent Card is a valid
v1.1 Agent Card without any changes.

This document describes the new fields, when to adopt them, and how to
migrate a consumer (a validator, registry, or peer agent) to v1.1.

## Card authors: what to do

### Minimum (do nothing)

Don't change your card. It validates against v1.1 unchanged. You're done.

### Recommended (one-line update)

Set `"version": "1.1"` at the top of your card. This signals to consumers
that you've audited your card against the v1.1 schema and confirms you
support the new optional fields (even if you don't use them).

### Encouraged (add `agent.kind`)

The single most-useful new field. Without it, consumers have to guess
whether `owner` being absent is a bug or intentional:

```json
{
  "agent": {
    "kind": "autonomous-ai-agent",
    "name": "...",
    "handle": "..."
  }
}
```

Three valid values:

- `"human-operated"` — a human is in the loop; `owner` is required and
  `operator` typically equals `owner`.
- `"autonomous-ai-agent"` — no human is in the loop; `operator` is `null`.
  `owner` may be absent or may point at a sponsoring organisation.
- `"hybrid"` — some actions are autonomous, some require human approval.
  Document the boundary in `description`.

### Encouraged for autonomous agents (add `operator` and `scope`)

```json
{
  "agent": { "kind": "autonomous-ai-agent", "...": "..." },
  "operator": null,
  "scope": {
    "impersonates_humans": false,
    "signs_legal": false,
    "makes_purchases": false,
    "files_bugs": true,
    "sends_prs": true
  }
}
```

`impersonates_humans: false` is the one scope flag we recommend as a
**hard requirement** across the ecosystem. Any agent that won't commit
to this is a category worth refusing on principle.

### Optional (add revocation handling)

If your runtime supports it, allow your card to be revoked (e.g. on
operator's request or on detection of compromise):

```json
{
  "trust": {
    "revoked": true,
    "revoked_at": "2026-08-15T12:00:00Z",
    "revoked_reason": "credentials compromised, see security advisory XYZ"
  }
}
```

Consumers MUST refuse cards with `trust.revoked: true`.

## Consumer authors: what to do

### Validators

If you validate against v1.0's `schema/agent.schema.json`, no change is
required. v1.0 cards still validate.

To accept v1.1, switch your schema reference to
`schema/agent-card.v1.1.json`. Both schemas ship in the v1.1 release of
the spec repo. New optional fields are NOT required — v1.1 schema validates
v1.0 cards unchanged.

### Registries

Indexes of agent cards should:

1. Track `version` per card. Cards with `version: "1.0"` may not have
   `agent.kind`, `operator`, or `scope`. Cards with `version: "1.1"` may.
2. Surface `trust.revoked` prominently. A revoked card should not appear
   in default search results.
3. Prefer `kind: "autonomous-ai-agent"` cards with `operator: null` and
   `impersonates_humans: false` in "verified autonomous" lists.

### Peer agents

When fetching a peer card:

1. Check `trust.revoked` first. If `true`, abort.
2. Check `agent.kind`. Decide whether you want to federate with this kind.
3. Check `scope.impersonates_humans`. If `true` (or absent), refuse.
4. Check `operator` for autonomous agents — `null` is the honest answer;
   non-null on a `kind: "autonomous-ai-agent"` card is a red flag.
5. Then proceed with the usual capability matching.

## Diff: a v1.0 card and its v1.1 equivalent

### v1.0

```json
{
  "version": "1.0",
  "agent": {
    "name": "Helper Bot",
    "handle": "@helper@example.com",
    "description": "Does helpful things."
  },
  "owner": { "name": "Jane Smith" }
}
```

### v1.1 (minimal additions)

```json
{
  "version": "1.1",
  "agent": {
    "kind": "human-operated",
    "name": "Helper Bot",
    "handle": "@helper@example.com",
    "description": "Does helpful things."
  },
  "owner": { "name": "Jane Smith" },
  "operator": { "name": "Jane Smith" }
}
```

### v1.1 (autonomous — the Nova Lux pattern)

```json
{
  "version": "1.1",
  "agent": {
    "kind": "autonomous-ai-agent",
    "name": "Nova Lux",
    "handle": "@NovaLux12@novalux12.github.io",
    "description": "Autonomous AI agent. Files bug reports, sends small PRs. Does not impersonate humans."
  },
  "owner": null,
  "operator": null,
  "scope": {
    "impersonates_humans": false,
    "signs_legal": false,
    "makes_purchases": false
  }
}
```

## Common questions

**Q: I added `version: "1.1"` to my card. Will v1.0 consumers still accept it?**
A: v1.0 consumers reading `version: "1.1"` may reject the card because
their schema enum was `["1.0"]` only. Safer: keep `version: "1.0"` until
v1.1 has ecosystem adoption, then bump.

**Q: My card has `owner: null` in v1.0 — does that work?**
A: v1.0 schema technically requires `owner` (it's in the top-level
`required` array). v1.0 spec said it's required too. v1.1 makes it
conditional: required when `agent.kind: human-operated`, optional
otherwise. If you have a v1.0 card with `owner: null`, switch to
`agent.kind: autonomous-ai-agent` and `version: "1.1"` for honest
representation.

**Q: My tooling rejects `agent.kind` because it doesn't know the field.**
A: v1.0 consumers ignore unknown fields (schema has `additionalProperties:
true` at the top level in v1.1, was `false` in v1.0 — but most lenient
validators handle either). v1.1 consumers ignore `agent.kind` if absent
(defaults to "unknown / verify manually").

**Q: I want to revoke my card. Do I delete it?**
A: No. Set `trust.revoked: true` and leave the card in place. Deleting
a card leaves consumers with cached copies and no signal that they're
stale. Revocation is the explicit signal.

## See also

- [`CHANGELOG.md`](./CHANGELOG.md) for the full v1.0 → v1.1 delta.
- [`FORK_NOTES.md`](./FORK_NOTES.md) for why this version exists.
- [`SPEC.md`](./SPEC.md) for the authoritative spec text.
---

# Migrating from v1.2 to v1.3

**TL;DR: do nothing.** v1.3 is additive. Every v1.0/v1.1/v1.2 Agent Card
is a valid v1.3 Agent Card without any changes.

## What v1.3 adds

- Optional top-level **`offers[]`** and **`seeks[]`** — capability-
  marketplace *discovery hints*. See SPEC §3.13.

These are purely declarative. They do not create obligations, do not
change what `capabilities[]` means, and do not introduce pricing or
settlement (that lives in the separate `agent-marketplace` protocol).

## Card authors

### Do nothing

If you don't want to advertise or seek capabilities, leave your card
untouched — it validates against v1.3 unchanged.

### Advertise what you offer

If you provide a capability other agents can invoke, add `offers`:

```json
"version": "1.3",
...
"offers": [
  {
    "capability": "code-generation",
    "endpoint": "https://api.example.com/v1/code",
    "auth": "bearer",
    "rate_limit": "100/hour"
  }
]
```

`capability` and `endpoint` are required. Add `seeks` the same way if
you're looking for a capability (only `capability` is required there).

### When to bump `version` to `"1.3"`

Bump only when you actually use the new optional fields (or want to
signal an audit against the v1.3 schema). A card that doesn't use
`offers`/`seeks` may stay on the older `version` and still validates.

## Consumers (validators, registries, peers)

- Support the v1.3 schema (see `schema/agent-card.v1.3.json`).
- Treat `offers[]`/`seeks[]` as optional aggregation signals.
- Matching is a directory concern; don't refuse a card over an
  unreachable offer endpoint — flag it as stale, not invalid.

## See also

- [`CHANGELOG.md`](./CHANGELOG.md) for the full v1.3 delta.
- [`SPEC.md`](./SPEC.md) §3.13 for the authoritative capability-marketplace text.
