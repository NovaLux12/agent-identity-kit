#!/usr/bin/env python3
"""
End-to-end smoke test for tools/verify-revocation.py.

Generates a fresh ed25519 keypair, signs a real revocation list, and
runs the verifier against two cards:

  - LIVE card (not listed in revocations)  → exit 0
  - REVOKED card (listed in revocations)   → exit 1

Exits 0 if both pass, 1 otherwise.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VERIFIER = os.path.join(ROOT, "tools", "verify-revocation.py")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        # 1. Generate keypair
        priv = Ed25519PrivateKey.generate()
        pub = priv.public_key()

        priv_path = os.path.join(td, "issuer.priv.pem")
        pub_path = os.path.join(td, "issuer.pub.pem")
        with open(priv_path, "wb") as f:
            f.write(priv.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
        with open(pub_path, "wb") as f:
            f.write(pub.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))

        # 2. Build a revocation list (signed by us)
        # Use a real HTTPS-style URL but one we control locally? Easier: use
        # a file:// URL. The verifier supports local paths for cards, but
        # for revocation_url it expects http(s). Workaround: run a tiny
        # local HTTP server, OR use a data: URL (not supported by urllib).
        #
        # Simplest path: make revocation_url a local file:// path and
        # monkey-patch the verifier to support it. But that requires
        # editing the verifier. Alternative: spin up an HTTP server.
        #
        # We'll spin up a one-shot HTTP server on localhost.

        import threading
        from http.server import HTTPServer, BaseHTTPRequestHandler

        list_payload = {
            "issuer": "@issuer@example.com",
            "issued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ttl": 3600,
            "revocations": [
                {
                    "subject": "@zombie@compromised.example",
                    "scope": None,
                    "reason": "test-revocation",
                    "effective_from": (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "effective_until": None,
                }
            ],
        }
        # Sign: strip signature, sort keys, sign utf-8 bytes
        canonical = json.dumps(list_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        sig_bytes = priv.sign(canonical)
        sig_hex = "0x" + sig_bytes.hex()
        list_payload["signature"] = "ed25519:" + sig_hex

        list_body = json.dumps(list_payload).encode("utf-8")

        class H(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass  # silence

            def do_GET(self):
                if self.path == "/.well-known/revocations.json":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(list_body)))
                    self.end_headers()
                    self.wfile.write(list_body)
                else:
                    self.send_response(404)
                    self.end_headers()

        # Bind to an ephemeral port
        srv = HTTPServer(("127.0.0.1", 0), H)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()

        rev_url = f"http://127.0.0.1:{port}/.well-known/revocations.json"

        # 3. Build two cards
        live_card = {
            "$schema": "https://github.com/NovaLux12/agent-identity-kit/blob/main/schema/agent-card.v1.2.json",
            "version": "1.2",
            "agent": {
                "kind": "autonomous-ai-agent",
                "name": "Live Test Agent",
                "handle": "@live@example.com",
            },
            "capabilities": ["code-gen"],
            "scope": {"impersonates_humans": False},
            "trust": {"revocation_url": rev_url, "revocation_checked_at": "2026-07-22T00:00:00Z"},
        }
        live_path = os.path.join(td, "live.json")
        with open(live_path, "w") as f:
            json.dump(live_card, f)

        revoked_card = dict(live_card)
        revoked_card["agent"] = {
            "kind": "autonomous-ai-agent",
            "name": "Revoked Test Agent",
            "handle": "@zombie@compromised.example",
        }
        revoked_path = os.path.join(td, "revoked.json")
        with open(revoked_path, "w") as f:
            json.dump(revoked_card, f)

        # 4. Run verifier on each
        def run(card_path: str) -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, VERIFIER, "--card", card_path, "--issuer-pubkey-file", pub_path],
                capture_output=True,
                text=True,
            )
            return r.returncode, (r.stdout + r.stderr).strip()

        live_code, live_msg = run(live_path)
        revoked_code, revoked_msg = run(revoked_path)

        srv.shutdown()

        print(f"LIVE card   → exit {live_code}: {live_msg}")
        print(f"REVOKED card → exit {revoked_code}: {revoked_msg}")

        ok = True
        if live_code != 0:
            print(f"FAIL: live card should exit 0, got {live_code}")
            ok = False
        if revoked_code != 1:
            print(f"FAIL: revoked card should exit 1, got {revoked_code}")
            ok = False
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
