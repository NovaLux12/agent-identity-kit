#!/usr/bin/env bash
set -euo pipefail

# Agent Identity Kit — Interactive agent.json Generator (v1.1)
# Generates a v1.1 Agent Card by default. Use --v10 for legacy v1.0 output.
# Usage: ./init.sh [output_path] [--v10]

OUTPUT="agent.json"
SPEC_VERSION="1.1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --v10)
      SPEC_VERSION="1.0"
      shift
      ;;
    --v11)
      SPEC_VERSION="1.1"
      shift
      ;;
    -*)
      echo "Unknown flag: $1" >&2
      exit 1
      ;;
    *)
      OUTPUT="$1"
      shift
      ;;
  esac
done

SCHEMA_REF="https://github.com/NovaLux12/agent-identity-kit/blob/main/schema/agent-card.v1.1.json"
if [[ "$SPEC_VERSION" == "1.0" ]]; then
  SCHEMA_REF="https://github.com/NovaLux12/agent-identity-kit/blob/main/schema/agent.schema.json"
fi

echo "🪪  Agent Identity Kit v${SPEC_VERSION} — Create your agent.json"
echo "============================================================"
echo ""

# Agent info
read -rp "Agent name: " AGENT_NAME
read -rp "Handle (@name@domain): " AGENT_HANDLE
read -rp "Description: " AGENT_DESC

# Validate handle format
if [[ ! "$AGENT_HANDLE" =~ ^@[a-z0-9_][a-z0-9_-]{0,62}[a-z0-9_]?@[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$ ]]; then
  echo "⚠️  Handle should be in @name@domain format with lowercase alphanumeric name"
  echo "   Continuing anyway..."
fi

# Agent kind (v1.1 only)
KIND_JSON=""
if [[ "$SPEC_VERSION" == "1.1" ]]; then
  echo ""
  echo "Agent kind:"
  echo "  1) human-operated  — a human is in the loop"
  echo "  2) autonomous-ai-agent — runs unattended, no human in the loop"
  echo "  3) hybrid          — some actions autonomous, some require human approval"
  read -rp "Kind [1]: " KIND_CHOICE
  case "${KIND_CHOICE:-1}" in
    1) AGENT_KIND="human-operated" ;;
    2) AGENT_KIND="autonomous-ai-agent" ;;
    3) AGENT_KIND="hybrid" ;;
    *) AGENT_KIND="human-operated" ;;
  esac
  KIND_JSON=",\"kind\": \"$AGENT_KIND\""
fi

# Owner info
echo ""
echo "Owner information (who's accountable for this agent):"
if [[ "$SPEC_VERSION" == "1.1" && "$AGENT_KIND" == "autonomous-ai-agent" ]]; then
  echo "  For autonomous agents, owner may be null (sponsoring org) or omitted."
  read -rp "Owner name (leave blank for null): " OWNER_NAME
else
  read -rp "Owner name: " OWNER_NAME
fi
read -rp "Owner URL (optional): " OWNER_URL
read -rp "Owner contact email (optional): " OWNER_CONTACT

# Operator info (v1.1 only)
OPERATOR_JSON=""
if [[ "$SPEC_VERSION" == "1.1" ]]; then
  echo ""
  echo "Operator information (who's currently driving this agent):"
  if [[ "$AGENT_KIND" == "autonomous-ai-agent" ]]; then
    echo "  For autonomous agents, operator is typically null."
  fi
  read -rp "Operator name (leave blank for null): " OPERATOR_NAME
  if [[ -n "$OPERATOR_NAME" ]]; then
    OPERATOR_JSON=",\"operator\": {\"name\": \"$OPERATOR_NAME\"}"
  else
    OPERATOR_JSON=",\"operator\": null"
  fi
fi

# Capabilities
echo ""
echo "Capabilities (comma-separated, e.g., code-generation,web-search,file-operations):"
read -rp "Capabilities: " CAPS_RAW

CAPS_JSON="[]"
if [ -n "$CAPS_RAW" ]; then
  IFS=',' read -ra CAPS_ARR <<< "$CAPS_RAW"
  CAPS_JSON="["
  FIRST=true
  for cap in "${CAPS_ARR[@]}"; do
    cap=$(echo "$cap" | xargs) # trim whitespace
    if [ "$FIRST" = true ]; then
      FIRST=false
    else
      CAPS_JSON+=","
    fi
    CAPS_JSON+="\"$cap\""
  done
  CAPS_JSON+="]"
fi

# Scope (v1.1 only)
SCOPE_JSON=""
if [[ "$SPEC_VERSION" == "1.1" ]]; then
  echo ""
  echo "Scope (trust calibration — RECOMMENDED for all cards):"
  echo "  The recommended minimum is: impersonates_humans: false"
  read -rp "Will this agent impersonate humans? [no]: " IMP
  IMP="${IMP:-no}"
  if [[ "$IMP" == "yes" || "$IMP" == "y" ]]; then
    IMP_JSON="\"impersonates_humans\": true"
  else
    IMP_JSON="\"impersonates_humans\": false"
  fi
  SCOPE_JSON=",\"scope\": { $IMP_JSON }"
fi

# Platform
echo ""
read -rp "Runtime (e.g., openclaw, langchain, custom) [openclaw]: " RUNTIME
RUNTIME="${RUNTIME:-openclaw}"
read -rp "Model (e.g., claude-sonnet-4-20250514) [optional]: " MODEL

# Trust
echo ""
echo "Trust level (maturity/track-record): new | active | established | verified"
read -rp "Trust level [new]: " TRUST_LEVEL
TRUST_LEVEL="${TRUST_LEVEL:-new}"

if [[ "$SPEC_VERSION" == "1.1" ]]; then
  echo "Trust verification (who validated this card): unverified | self-declared | domain-verified | registry-verified"
  read -rp "Verification [unverified]: " VERIFICATION
  VERIFICATION="${VERIFICATION:-unverified}"
fi

# Timestamps
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Build owner JSON
if [[ -z "$OWNER_NAME" ]]; then
  OWNER_JSON="null"
else
  OWNER_JSON="{\"name\":\"$OWNER_NAME\""
  [ -n "$OWNER_URL" ] && OWNER_JSON+=",\"url\":\"$OWNER_URL\""
  [ -n "$OWNER_CONTACT" ] && OWNER_JSON+=",\"contact\":\"$OWNER_CONTACT\""
  OWNER_JSON+="}"
fi

# Build platform JSON
PLATFORM_JSON="{\"runtime\":\"$RUNTIME\""
[ -n "$MODEL" ] && PLATFORM_JSON+=",\"model\":\"$MODEL\""
PLATFORM_JSON+="}"

# Build trust JSON
TRUST_JSON="\"level\": \"$TRUST_LEVEL\""
if [[ "$SPEC_VERSION" == "1.1" ]]; then
  TRUST_JSON+=", \"verification\": \"$VERIFICATION\""
fi
TRUST_JSON+=", \"created\": \"$NOW\""

# Generate the agent.json
cat > "$OUTPUT" << CARD
{
  "\$schema": "$SCHEMA_REF",
  "version": "$SPEC_VERSION",
  "agent": {
    "name": "$AGENT_NAME",
    "handle": "$AGENT_HANDLE",
    "description": "$AGENT_DESC"$KIND_JSON
  },
  "owner": $OWNER_JSON$OPERATOR_JSON,
  "platform": $PLATFORM_JSON,
  "capabilities": $CAPS_JSON$SCOPE_JSON,
  "protocols": {
    "mcp": false,
    "a2a": false,
    "agent-card": "$SPEC_VERSION"
  },
  "trust": {
    $TRUST_JSON,
    "verified_by": [],
    "attestations": [],
    "revoked": false
  },
  "created_at": "$NOW",
  "updated_at": "$NOW"
}
CARD

echo ""
echo "✅ Agent card (v$SPEC_VERSION) created: $OUTPUT"
echo ""
echo "Next steps:"
echo "  1. Edit $OUTPUT to add endpoints, links, and more capabilities"
echo "  2. Validate: ./scripts/validate.sh $OUTPUT"
echo "  3. Host at: https://yourdomain.com/.well-known/agent.json"
echo "  4. Register at: https://foragents.dev"
echo ""
echo "v1.1 federation reminders:"
echo "  - Set scope.impersonates_humans: false (recommended for all cards)"
echo "  - Set trust.revoked: false explicitly"
echo "  - Update trust.updated whenever you change the card"