#!/usr/bin/env bash
# Prueba el webhook n8n del workflow RAG (Parte 2 de la consigna).
# Requisitos: n8n activo con el workflow importado y activado; API en :8000.
set -euo pipefail

N8N_WEBHOOK_URL="${N8N_WEBHOOK_URL:-http://localhost:5678/webhook/support-ask}"
QUESTION="${1:-¿Qué hacer si las credenciales son incorrectas?}"

echo "POST $N8N_WEBHOOK_URL"
echo "question: $QUESTION"
echo "---"

response=$(curl -sS -w "\n%{http_code}" -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"$QUESTION\"}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

echo "HTTP $http_code"
echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"

if [ "$http_code" != "200" ]; then
  echo "Error: verificá que n8n esté activo y el workflow publicado." >&2
  exit 1
fi

echo "OK — flujo n8n → API respondió."
