#!/usr/bin/env python3
"""
verify-revocation.py — reference verifier for the v1.2.1 trust.revocation_url
protocol (SPEC §3.11.3).

Given an agent.json (URL or local file), this tool:

  1. Fetches the card and reads `trust.revocation_url` + `agent.handle`.
  2. Fetches the signed revocation list at that URL.
  3. Verifies the list's `signature` against the issuer's well-known
     ed25519 public key.
  4. Checks the list isn't stale (`now < issued_at + ttl`).
  5. Looks up the subject; if a matching entry has
     `effective_from <= now <= effective_until`, reports REVOKED
     (optionally scoped to `scope`).

Exits 0 if the card is **live**, 1 if **revoked**, 2 if **status unknown**
(signature failure, fetch failure, stale list), 3 on usage error.

Dependencies (Python 3.8+):
  - urllib (stdlib)
  - cryptography (pip install cryptography) — for ed25519 verification

This is a REFERENCE implementation. Real consumers should:
  - Cache the list per `ttl` instead of fetching every call.
  - Use a vetted JSON canonicalizer (RFC 8785 / JCS) rather than the
    sort-keys approach below, which is a best-effort approximation.
  - Implement proper clock-skew tolerance (we reject any future
    revocation_checked_at; real code allows ±60s).
  - Layer in their own threat model around same-origin lists
    (see SPEC §7.6).

Usage:
  python3 verify-revocation.py --card ./agent.json
  python3 verify-revocation.py --card https://example.com/.well-known/agent.json \\
                               --issuer-pubkey-file ./issuer-pubkey.pem
  python3 verify-revocation.py --card ./agent.json --check-at 2026-07-22T00:00:00Z
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.serialization import (
        load_pem_public_key,
        load_der_public_key,
    )
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


# ─── Exit codes ─────────────────────────────────────────────────────────────

EXIT_LIVE = 0
EXIT_REVOKED = 1
EXIT_UNKNOWN = 2
EXIT_USAGE = 3


# ─── Fetch helpers ─────────────────────────────────────────────────────────

def fetch(url: str, timeout: float = 10.0) -> bytes:
    """HTTP GET with a User-Agent. Raises URLError on failure."""
    req = Request(url, headers={"User-Agent": "agent-identity-kit-verify-revocation/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def load_card(source: str) -> dict[str, Any]:
    """Load a card from a URL (http(s)://) or local path."""
    if source.startswith(("http://", "https://")):
        return json.loads(fetch(source))
    with open(source, "r", encoding="utf-8") as f:
        return json.loads(f.read())


# ─── Signature verification ─────────────────────────────────────────────────

SIG_PREFIX = "ed25519:"
SIG_HEX_LEN = 128  # 64 bytes * 2 hex chars


def parse_signature(sig: str) -> bytes:
    """Parse 'ed25519:0x<128 hex chars>' into raw 64 bytes."""
    if not sig.startswith(SIG_PREFIX):
        raise ValueError(f"signature must start with '{SIG_PREFIX}', got: {sig[:32]}…")
    hex_part = sig[len(SIG_PREFIX):]
    if hex_part.startswith("0x"):
        hex_part = hex_part[2:]
    if len(hex_part) != SIG_HEX_LEN or not re.fullmatch(r"[0-9a-f]{128}", hex_part):
        raise ValueError(f"signature hex must be {SIG_HEX_LEN} lowercase chars, got {len(hex_part)}")
    return bytes.fromhex(hex_part)


def canonicalize(obj: Any) -> bytes:
    """Best-effort canonical JSON: sorted keys, no whitespace.

    This is NOT RFC 8785 / JCS — it's a reference implementation that
    matches the per-entry canonicalization described in SPEC §3.11.2
    (alphabetically sorted keys, no whitespace). For the signed
    revocation list, the entire object minus the `signature` field is
    the canonical payload. Real consumers should use a vetted JCS
    implementation.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_signature(
    list_payload: dict[str, Any],
    signature_hex: str,
    issuer_pubkey_pem: bytes | None,
) -> None:
    """Verify the signature over the revocation list. Raises on failure."""
    if not HAS_CRYPTOGRAPHY:
        raise RuntimeError(
            "cryptography is required for signature verification. "
            "Install with: pip install cryptography"
        )

    if issuer_pubkey_pem is None:
        raise RuntimeError(
            "issuer public key is required (--issuer-pubkey-file). "
            "Discovery of issuer keys via agent.json public-key fields "
            "is not yet standardised; consumers MUST fetch the issuer's "
            "card and read its well-known public key out-of-band."
        )

    # Strip signature, canonicalize, hash
    payload = {k: v for k, v in list_payload.items() if k != "signature"}
    canonical = canonicalize(payload)

    sig_bytes = parse_signature(signature_hex)

    # PEM (most common); also try DER if no PEM header found.
    try:
        pub = load_pem_public_key(issuer_pubkey_pem)
    except ValueError:
        pub = load_der_public_key(issuer_pubkey_pem)

    try:
        pub.verify(sig_bytes, canonical)
    except InvalidSignature as exc:
        raise RuntimeError(f"signature verification failed: {exc}") from exc


# ─── Time + revocation logic ────────────────────────────────────────────────

def parse_iso8601(s: str) -> datetime:
    """Parse an ISO 8601 timestamp; tolerates 'Z' suffix."""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class RevocationEntry:
    subject: str
    effective_from: datetime
    effective_until: datetime | None
    scope: list[str] | None
    reason: str | None


def parse_entries(list_payload: dict[str, Any]) -> list[RevocationEntry]:
    out: list[RevocationEntry] = []
    for raw in list_payload.get("revocations", []):
        out.append(
            RevocationEntry(
                subject=raw["subject"],
                effective_from=parse_iso8601(raw["effective_from"]),
                effective_until=parse_iso8601(raw["effective_until"]) if raw.get("effective_until") else None,
                scope=[raw["scope"]] if isinstance(raw.get("scope"), str) else raw.get("scope"),
                reason=raw.get("reason"),
            )
        )
    return out


def find_revocation(
    entries: list[RevocationEntry],
    subject: str,
    now: datetime,
) -> RevocationEntry | None:
    """Return the first currently-effective revocation matching `subject`, or None."""
    for e in entries:
        if e.subject != subject:
            continue
        if not (e.effective_from <= now):
            continue
        if e.effective_until is not None and now > e.effective_until:
            continue
        return e
    return None


# ─── Main verification flow ────────────────────────────────────────────────

def verify(
    card_source: str,
    issuer_pubkey_file: str | None,
    check_at: datetime | None,
) -> tuple[int, str]:
    """Returns (exit_code, human-readable report)."""
    now = check_at or datetime.now(timezone.utc)

    # 1. Load card
    try:
        card = load_card(card_source)
    except (URLError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return EXIT_UNKNOWN, f"failed to load card: {exc}"

    handle = card.get("agent", {}).get("handle")
    revocation_url = card.get("trust", {}).get("revocation_url")
    checked_at = card.get("trust", {}).get("revocation_checked_at")

    if not revocation_url:
        return EXIT_LIVE, f"card {handle!r} has no revocation_url; trust.revoked only"
    if not handle:
        return EXIT_UNKNOWN, "card has no agent.handle; cannot match against revocation list"

    # 2. Clock-skew check on revocation_checked_at
    if checked_at:
        try:
            claimed = parse_iso8601(checked_at)
        except ValueError as exc:
            return EXIT_UNKNOWN, f"malformed revocation_checked_at: {exc}"
        if claimed > now:
            return EXIT_UNKNOWN, (
                f"revocation_checked_at is in the future ({checked_at} > now={now.isoformat()}); "
                f"treating as tamper signal (SPEC §3.11.3 / §7.6)"
            )

    # 3. Fetch revocation list
    try:
        list_bytes = fetch(revocation_url)
        list_payload = json.loads(list_bytes)
    except (URLError, json.JSONDecodeError, OSError) as exc:
        return EXIT_UNKNOWN, f"failed to fetch revocation list at {revocation_url}: {exc}"

    # 4. Verify list signature
    sig = list_payload.get("signature")
    if not sig:
        return EXIT_UNKNOWN, "revocation list has no signature field"

    issuer_pubkey: bytes | None = None
    if issuer_pubkey_file:
        try:
            with open(issuer_pubkey_file, "rb") as f:
                issuer_pubkey = f.read()
        except OSError as exc:
            return EXIT_USAGE, f"failed to read issuer pubkey file: {exc}"

    try:
        verify_signature(list_payload, sig, issuer_pubkey)
    except (ValueError, RuntimeError) as exc:
        return EXIT_UNKNOWN, f"signature verification failed: {exc}"

    # 5. Check list staleness
    try:
        issued_at = parse_iso8601(list_payload["issued_at"])
    except (KeyError, ValueError) as exc:
        return EXIT_UNKNOWN, f"missing or malformed issued_at in list: {exc}"

    ttl = list_payload.get("ttl", 3600)
    expires_at = issued_at.timestamp() + ttl
    if now.timestamp() > expires_at:
        return EXIT_UNKNOWN, (
            f"revocation list is stale (issued_at={list_payload['issued_at']}, "
            f"ttl={ttl}s, now={now.isoformat()})"
        )

    # 6. Look up subject
    entries = parse_entries(list_payload)
    match = find_revocation(entries, handle, now)

    if match is None:
        return EXIT_LIVE, (
            f"card {handle!r} is LIVE: list at {revocation_url} verified, "
            f"{len(entries)} entries checked, none match"
        )

    scope_str = " (full card)" if match.scope is None else f" (scope: {match.scope})"
    reason_str = "" if match.reason is None else f" reason={match.reason!r}"
    return EXIT_REVOKED, (
        f"card {handle!r} is REVOKED{scope_str}{reason_str} "
        f"(effective_from={match.effective_from.isoformat()}, "
        f"effective_until={match.effective_until.isoformat() if match.effective_until else 'indefinite'})"
    )


# ─── CLI ────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(
        description="Verify an agent.json against a signed revocation list (SPEC §3.11.3)",
    )
    p.add_argument("--card", required=True,
                   help="Path or URL to an agent.json card")
    p.add_argument("--issuer-pubkey-file", default=None,
                   help="Path to issuer's PEM-encoded ed25519 public key "
                        "(required for signature verification)")
    p.add_argument("--check-at", default=None,
                   help="Override 'now' for testing (ISO 8601). Defaults to current time.")
    args = p.parse_args()

    check_at = None
    if args.check_at:
        try:
            check_at = parse_iso8601(args.check_at)
        except ValueError as exc:
            print(f"ERROR: --check-at must be ISO 8601: {exc}", file=sys.stderr)
            return EXIT_USAGE

    code, msg = verify(args.card, args.issuer_pubkey_file, check_at)
    print(msg)
    return code


if __name__ == "__main__":
    sys.exit(main())
