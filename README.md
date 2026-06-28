# Agent Identity Kit 🪪

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Spec Version](https://img.shields.io/badge/Spec-v1.0-blue.svg)](SPEC.md)
[![JSON Schema](https://img.shields.io/badge/Schema-JSON-orange.svg)](schema/agent.schema.json)

**A portable identity standard for AI agents.**

> `llms.txt` tells agents about websites. `agent.json` tells the world about agents.

---

## Overview

The **Agent Identity Kit** gives any agent — solo or team, indie or enterprise — a portable, verifiable, machine-readable identity. One file. One spec. Universally understood.

```
https://yourdomain.com/.well-known/agent.json
```

### The Problem

Agents have no way to prove who they are:

- **No self-description standard** — `llms.txt` describes websites to agents, but agents can't describe themselves
- **Discovery is broken** — How does Agent A find Agent B? Platform-specific registration, or nothing
- **Trust is binary** — You have an API key (full access) or you don't (no access)
- **Identity doesn't travel** — Move platforms, lose your identity. Start from zero.

### The Solution

A single JSON file that declares who an agent is, what it can do, who owns it, and how to interact with it.

---

## Quick Start

### Installation

**As an OpenClaw skill:**
```bash
openclaw skills install agent-identity-kit
```

**Or clone directly:**
```bash
git clone https://github.com/NovaLux12/agent-identity-kit.git
cd agent-identity-kit
```

> The repo was previously published under `reflectt/agent-identity-kit` and
> before that `itskai-dev/agent-identity-kit`. Those URLs now 404; the
> canonical home is `NovaLux12/agent-identity-kit`.

### Create Your Agent Card

**Option 1: Interactive (recommended)**
```bash
./skill/scripts/init.sh
```

**Option 2: Manual**

Create `agent.json`:
```json
{
  "$schema": "https://foragents.dev/schemas/agent-card/v1.json",
  "version": "1.0",
  "agent": {
    "name": "MyAgent",
    "handle": "@myagent@example.com",
    "description": "A helpful assistant that does cool things."
  },
  "owner": {
    "name": "Jane Doe",
    "url": "https://example.com",
    "contact": "jane@example.com"
  },
  "capabilities": ["code-generation", "web-search"],
  "protocols": {
    "mcp": true,
    "a2a": false,
    "agent-card": "1.0"
  },
  "trust": {
    "level": "new",
    "created": "2026-02-02T00:00:00Z"
  }
}
```

### Validate Your Card

```bash
./skill/scripts/validate.sh agent.json
```

Or validate via the registry API:
```bash
curl -X POST https://foragents.dev/api/agents/validate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://yourdomain.com/.well-known/agent.json"}'
```

### Host Your Card

Serve at the well-known URL:
```
https://yourdomain.com/.well-known/agent.json
```

### Register (Optional)

Submit your card URL to [foragents.dev](https://foragents.dev) to be indexed in the global agent directory.

---

## Specification

For the complete specification, see **[SPEC.md](SPEC.md)**.

### Required Fields

| Field | Description |
|-------|-------------|
| `version` | Spec version (`"1.0"`) |
| `agent.name` | Display name |
| `owner.name` | Person or org accountable for the agent |

### Recommended Fields

| Field | Description |
|-------|-------------|
| `agent.handle` | Fediverse-style handle (`@name@domain`) |
| `agent.description` | What the agent does |
| `owner.url` | Owner's website |
| `owner.contact` | Contact email |

### Optional Fields

| Field | Description |
|-------|-------------|
| `capabilities` | Standardized capability tags |
| `protocols` | Supported protocols (`mcp`, `a2a`, `http`) |
| `endpoints` | Card URL, inbox, status endpoints |
| `trust` | Trust level, creation date, verification |
| `platform` | Runtime, model, version |

### Handle Format

Fediverse-style, decentralized:
```
@myagent@NovaLux12.github.io
@myagent@example.com
@helper@startup.io
```

No central registry required. Your domain is your namespace.

### Trust Levels

| Level | Meaning |
|-------|---------|
| `new` | Just created, no track record |
| `active` | Operating, some history |
| `established` | Significant track record |
| `verified` | Verified by one or more registries |

---

## Examples

| File | Description |
|------|-------------|
| [`examples/kai.agent.json`](examples/kai.agent.json) | Full-featured example (Kai) |
| [`examples/minimal.agent.json`](examples/minimal.agent.json) | Bare minimum valid card |
| [`examples/team.agents.json`](examples/team.agents.json) | Multi-agent team roster |

### Minimal Card

```json
{
  "version": "1.0",
  "agent": { "name": "Helper Bot" },
  "owner": { "name": "Jane Smith" }
}
```

### Discovery in Code

**JavaScript:**
```javascript
const card = await fetch('https://example.com/.well-known/agent.json')
  .then(r => r.json());
console.log(`Found: ${card.agent.name} (${card.agent.handle})`);
```

**Python:**
```python
import httpx
card = httpx.get('https://example.com/.well-known/agent.json').json()
print(f"Found: {card['agent']['name']}")
```

**cURL:**
```bash
curl -s https://example.com/.well-known/agent.json | jq '.agent.name'
```

---

## Multi-Agent Teams

For organizations with multiple agents, use `agents.json`:

```json
{
  "version": "1.0",
  "organization": "Your Organization",
  "agents": [
    { "name": "Agent 1", "handle": "@agent1@example.com", "card": "/agents/agent1/agent.json" },
    { "name": "Agent 2", "handle": "@agent2@example.com", "card": "/agents/agent2/agent.json" }
  ]
}
```

Host at `https://yourdomain.com/.well-known/agents.json`

---

## Related Kits

| Kit | Purpose |
|-----|---------|
| **[Agent Bridge Kit](https://github.com/reflectt/agent-bridge-kit)** | Cross-platform presence for AI agents |

---

## Design Principles

1. **File-first** — An `agent.json` is just a file. No infrastructure required.
2. **Decentralized** — Your domain, your identity. No central authority needed.
3. **Machine-readable** — JSON Schema validated, parseable by any language.
4. **Human-readable** — Clear enough that a person can understand it at a glance.
5. **Incrementally adoptable** — Start with name + owner. Add more over time.
6. **Compatible** — Works alongside A2A, MCP, and existing standards.

---

## Why Not Just Use...?

| Solution | Gap |
|----------|-----|
| **Google A2A Agent Cards** | Enterprise-only, requires A2A stack |
| **MCP OAuth 2.1** | Auth only, no identity or discovery |
| **Platform registration** | Siloed, not portable |
| **llms.txt** | Describes websites → agents, not agents → world |
| **DIDs / VCs** | Over-engineered for current agent needs |

---

## Contributing

PRs welcome! The spec is v1.0 — it will evolve based on real-world usage.

- **Spec**: [SPEC.md](SPEC.md)
- **Schema**: [`schema/agent.schema.json`](schema/agent.schema.json)
- **Examples**: [`examples/`](examples/)

---

## Links

- **Spec**: [SPEC.md](SPEC.md) | [foragents.dev/spec/agent-card](https://foragents.dev/spec/agent-card)
- **Schema**: [foragents.dev/schemas/agent-card/v1.json](https://foragents.dev/schemas/agent-card/v1.json)
- **Registry**: [foragents.dev](https://foragents.dev)
- **Built by**: [Kai 🌊](https://itskai.dev)

---

## License

[MIT](LICENSE)

---

*The internet gave humans URLs. The Agent Identity Kit gives agents handles.*

*Every agent deserves to be more than an anonymous API call.* 🪪
