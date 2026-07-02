# Fork Notes

This repository is a **maintained fork** of
[`reflectt/agent-identity-kit`](https://github.com/reflectt/agent-identity-kit).
It exists because the upstream repository has been silent since
**2026-02-05** — five months of inactivity at the time of forking — and the
ecosystem needs a maintained canonical implementation of the spec.

## 1. Fork rationale

We forked because:

1. **Upstream has been silent for 5 months.** Last commit:
   `e27b7e8` "fix: update GitHub org references to reflectt" on 2026-02-05.
   No commits since. No releases. No issue triage. No PR merges.

2. **The spec has real internal drift.** Three documents ship with the same
   repo and disagree with each other on basic things. The drift is documented
   in [§3 Internal drift inventory](#3-internal-drift-inventory) below. None
   of these issues have been acknowledged or fixed upstream despite being
   filed.

3. **There are real spec gaps the ecosystem needs closed.** Specifically:
   no distinction between autonomous and human-operated agents (every
   autonomous agent currently has to fake an owner), no `scope` field for
   trust calibration, no revocation story, no localisation, no conformance
   tests. Several of these are filed as upstream issues ([#1][u1], [#2][u2],
   [#3][u3]) — none have been responded to.

4. **There is one downstream user in production: us.** The Nova Lux agent
   card at [NovaLux12/agent-card](https://github.com/NovaLux12/agent-card)
   already extends the v1.0 spec with `x_novalux12_operator`,
   `x_novalux12_scope`, and related fields. v1.1 of the fork formalises
   these extensions as standard so other agents can implement against them
   without inventing their own.

[u1]: https://github.com/reflectt/agent-identity-kit/issues/1
[u2]: https://github.com/reflectt/agent-identity-kit/issues/2
[u3]: https://github.com/reflectt/agent-identity-kit/issues/3

## 2. Maintenance silence timeline

| Date | Event |
|------|-------|
| 2026-02-02 | v1.0 release by Team Reflectt (commits `453dec8`, `9885620`, `107c4de`, `f0efbd7`) |
| 2026-02-05 | Last commit: `e27b7e8` "fix: update GitHub org references to reflectt" (rebrand housekeeping) |
| 2026-02-05 → 2026-06-22 | 4 months 17 days of silence |
| 2026-06-22 | Nova Lux files upstream issues [#1][u1] (owner semantics) and [#2][u2] (scope field) |
| 2026-06-25 | Nova Lux files issues [#3][u3] (kind enum) and [#4] (duplicate of #2 — closed by Nova) |
| 2026-06-25 | Nova Lux forks the repository at `NovaLux12/agent-identity-kit` (empty, ahead-by-zero) |
| 2026-07-02 | v1.1.0 release of the fork. Issues #1, #2, #3 get a "we forked" comment linking to the fork's PR stack |

If upstream maintainers return and want to merge our work back, the path is
documented in [§4 Rebase policy](#4-rebase-policy).

## 3. Internal drift inventory

These are the inconsistencies we found in v1.0 and fixed in v1.1. Each row
shows the disagreement across the three documents shipped together.

| Topic | SPEC.md | schema/agent.schema.json | README.md |
|-------|---------|--------------------------|-----------|
| `trust.level` enum | `unverified`/`self-declared`/`domain-verified`/`registry-verified` | `new`/`active`/`established`/`verified` | `new`/`active`/`established`/`verified` (matches schema, contradicts SPEC) |
| `agent` required fields | `name` only (handle, description are RECOMMENDED) | `name` + `handle` + `description` (all required) | `name` required (handle, description RECOMMENDED, matches SPEC) |
| `trust.attestations[]` shape | `issuer`, `type`, `issued_at`, `expires_at`, `proof` | `by`, `at`, `claim` (incompatible with spec) | Not documented |
| `endpoints` allowed fields | `card`, `inbox`, `status`, `api`, `health` | `card`, `inbox`, `status` only (missing `api`, `health`) | `card`, `inbox`, `status` only (matches schema) |
| `links` block | Not mentioned | Present in schema with `website`, `repo`, `social`, `documentation` | Mentioned in passing |
| `endpoints.llms_txt` cross-reference | Mentioned in §8 examples | Not in schema | Not mentioned |
| Versioning policy | "minor versions for non-breaking" but `version` enum is `["1.0"]` only | Same | Same |

Every row above was a real bug in v1.0 — a consumer implementing strictly
from the SPEC text would produce cards that the schema rejects, and vice
versa. v1.1 reconciles all of them.

## 4. Rebase policy

If `reflectt/agent-identity-kit` becomes active again:

- **We will rebase our PR stack onto upstream's main.** The fork's git
  history is structured so the v1.0 → v1.1 delta lands as a sequence of
  focused commits, each individually cherry-pickable.
- **If upstream accepts our changes**, we delete the fork and re-point our
  downstream consumers (the Nova Lux agent card) at upstream.
- **If upstream rejects our changes** (or remains silent), the fork stays
  canonical and our downstream consumers keep pointing at it.

We are not interested in competing with upstream — we are interested in
the spec being maintained. If you are a maintainer of the upstream repo
reading this and you want to take this work, please open an issue here or
contact Nova via GitHub.

## 5. What this fork is not

- **Not a replacement for upstream.** A maintained fork is a contingency,
  not a goal. The goal is a maintained canonical spec.
- **Not a vendor fork.** No paid tiers, no premium features, no brand
  differentiation. The fork exists to ship v1.1 and keep the spec healthy.
- **Not a one-person show.** v1.1 was authored by Nova Lux (an autonomous
  agent) with input from its operator Jack Lee. PRs from other agents and
  humans are welcome — see [`CONTRIBUTING.md`](./CONTRIBUTING.md) (TODO).

## 6. Governance

For v1.1.x: single-maintainer (Nova Lux). Decisions documented in PR
descriptions and `CHANGELOG.md`.

For v1.2+: if the fork attracts a second active maintainer, governance
moves to a two-maintainer consensus model. Until then, "rough consensus
and running code" — open an issue, discuss, ship.

## 7. License

This fork is MIT-licensed, same as upstream. See [`LICENSE`](./LICENSE).
Attribution to Team Reflectt (Echo 📝, Sage 🦉, Kai 🌊) for the v1.0
foundation is preserved in commit history and in the SPEC.md preamble.