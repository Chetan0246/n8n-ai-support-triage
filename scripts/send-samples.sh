#!/usr/bin/env bash
# Sends every sample ticket to the n8n test webhook and prints the triage result.
URL="${1:-http://localhost:5678/webhook-test/support-triage}"
jq -c '.[]' "$(dirname "$0")/../samples/tickets.json" | while read -r t; do
  echo "--- $(echo "$t" | jq -r .subject)"
  curl -s -X POST "$URL" -H "Content-Type: application/json" -d "$t" | jq .
done
