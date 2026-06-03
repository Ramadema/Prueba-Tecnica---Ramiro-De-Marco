#!/usr/bin/env bash
# Verificación rápida de la API para demo / entrevista (sin n8n).
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"

echo "=== GET /health ==="
curl -sS "$API_BASE/health" | python3 -m json.tool

echo ""
echo "=== POST /ask (credenciales) ==="
curl -sS -X POST "$API_BASE/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué hacer si las credenciales son incorrectas?"}' | python3 -m json.tool

echo ""
echo "=== POST /ask (error 502 — fuera de corpus) ==="
curl -sS -X POST "$API_BASE/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "El sistema devuelve error 502, ¿qué significa?"}' | python3 -m json.tool

echo ""
echo "Verificación API completada."
