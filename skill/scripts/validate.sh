#!/usr/bin/env bash
set -euo pipefail

# Agent Identity Kit — Schema Validator (v1.1)
# Auto-detects card spec version and validates against the matching schema.
# Usage: validate.sh <agent.json> [--schema <path>] [--strict]
#
# Flags:
#   --schema PATH   Use a custom schema file (overrides auto-detection)
#   --strict        Run additional semantic checks (revocation, impersonation)
#   --v10           Force v1.0 schema validation regardless of card version
#   --v11           Force v1.1 schema validation regardless of card version

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

FILE=""
CUSTOM_SCHEMA=""
STRICT=false
FORCE_VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --schema)
      CUSTOM_SCHEMA="$2"
      shift 2
      ;;
    --strict)
      STRICT=true
      shift
      ;;
    --v10)
      FORCE_VERSION="1.0"
      shift
      ;;
    --v11)
      FORCE_VERSION="1.1"
      shift
      ;;
    -*)
      echo "Unknown flag: $1" >&2
      exit 1
      ;;
    *)
      FILE="$1"
      shift
      ;;
  esac
done

if [ -z "$FILE" ]; then
  echo "Usage: validate.sh <agent.json> [--schema <path>] [--strict] [--v10|--v11]"
  echo ""
  echo "Auto-detects the card's spec version and validates against the matching schema."
  echo "Supports both v1.0 and v1.1 cards."
  exit 1
fi

if [ ! -f "$FILE" ]; then
  echo "❌ File not found: $FILE"
  exit 1
fi

# Auto-detect version and file type from card
# shellcheck disable=SC2162 # read without -r here is intentional: pipe substitution only carries two whitespace-separated words; backslash-mangling is not a concern.
read CARD_TYPE CARD_VERSION < <(python3 -c "
import json, sys
try:
    with open('$FILE') as f:
        d = json.load(f)
    is_team = isinstance(d.get('agents'), list)
    ftype = 'team' if is_team else 'card'
    print(ftype, d.get('version', '1.0'))
except Exception as e:
    print(f'ERROR:{e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null) || {
    echo "❌ Could not read $FILE (invalid JSON?)"
    exit 1
}

if [ -n "$FORCE_VERSION" ]; then
  CARD_VERSION="$FORCE_VERSION"
fi

# Pick schema based on type + version
if [ -n "$CUSTOM_SCHEMA" ]; then
  SCHEMA="$CUSTOM_SCHEMA"
elif [ "$CARD_TYPE" == "team" ] && [ "$CARD_VERSION" == "1.1" ]; then
  SCHEMA="$REPO_ROOT/schema/agents.v1.1.json"
elif [ "$CARD_TYPE" == "team" ] && [ "$CARD_VERSION" == "1.0" ]; then
  SCHEMA="$REPO_ROOT/schema/agents.json"
elif [ "$CARD_VERSION" == "1.1" ]; then
  SCHEMA="$REPO_ROOT/schema/agent-card.v1.1.json"
elif [ "$CARD_VERSION" == "1.0" ]; then
  SCHEMA="$REPO_ROOT/schema/agent.schema.json"
else
  echo "❌ Unknown card version: $CARD_VERSION (expected 1.0 or 1.1)"
  exit 1
fi

if [ ! -f "$SCHEMA" ]; then
  echo "❌ Schema not found: $SCHEMA"
  exit 1
fi

echo "🔍 Validating $FILE ($CARD_TYPE, v$CARD_VERSION) against schema..."
echo "   Schema: $SCHEMA"
echo ""

# Run ajv validation
run_ajv() {
  if command -v ajv &> /dev/null; then
    ajv validate -s "$SCHEMA" -d "$FILE" --spec=draft7
  elif command -v npx &> /dev/null; then
    npx --yes ajv-cli validate -s "$SCHEMA" -d "$FILE" --spec=draft7
  else
    return 1
  fi
}

run_python() {
  python3 -c "
import json, sys
try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print('Installing jsonschema...', file=sys.stderr)
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'jsonschema', '-q'])
    from jsonschema import validate, ValidationError, Draft7Validator

with open('$SCHEMA') as f:
    schema = json.load(f)
with open('$FILE') as f:
    data = json.load(f)

validator = Draft7Validator(schema)
errors = list(validator.iter_errors(data))
if errors:
    for e in errors:
        path = '/'.join(str(p) for p in e.absolute_path) or '(root)'
        print(f'  - {path}: {e.message}')
    sys.exit(1)
print('OK')
"
}

if run_ajv; then
  echo ""
  echo "✅ Schema valid (v$CARD_VERSION)."
elif run_python; then
  echo ""
  echo "✅ Schema valid (v$CARD_VERSION)."
else
  echo ""
  echo "❌ Validation failed (no validator available). Install ajv-cli or python jsonschema."
  exit 1
fi

# Strict mode: additional semantic checks
if [ "$STRICT" = true ]; then
  echo ""
  echo "🔒 Running strict semantic checks..."

  python3 -c "
import json, sys

with open('$FILE') as f:
    data = json.load(f)

warnings = []

# Federation check 1: trust.revoked (cards only, not team indexes)
if '$CARD_TYPE' == 'card':
    revoked = data.get('trust', {}).get('revoked', False)
    if revoked:
        warnings.append('trust.revoked is true — card is revoked, should be refused')

# Federation check 2 & 3: only apply to v1.1 individual cards, not team indexes
if '$CARD_TYPE' == 'card' and '$CARD_VERSION' == '1.1':
    scope = data.get('scope', {})
    impersonates = scope.get('impersonates_humans', None)
    if impersonates is None:
        warnings.append('scope.impersonates_humans is absent or null — consumers MUST refuse per SPEC §4.5')
    elif impersonates is True:
        warnings.append('scope.impersonates_humans is true — consumers MUST refuse per SPEC §4.5')

    kind = data.get('agent', {}).get('kind', None)
    if kind is None:
        warnings.append('agent.kind not set — RECOMMENDED to declare (human-operated/autonomous-ai-agent/hybrid)')

if warnings:
    for w in warnings:
        print(f'  ⚠️  {w}')
    sys.exit(2)
else:
    print('  ✅ All strict semantic checks passed')
"
fi

echo ""
echo "Done."