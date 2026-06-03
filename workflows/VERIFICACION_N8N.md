# Verificación del workflow n8n (Parte 2)

Checklist para validar el flujo **Webhook → API FastAPI → respuesta** antes de la entrevista.

## Prerrequisitos

- [ ] API corriendo: `uvicorn src.main:app --host 0.0.0.0 --port 8000`
- [ ] Ollama activo con `llama3.2:3b`
- [ ] `curl http://localhost:8000/health` → `index_loaded: true`
- [ ] n8n instalado y en ejecución (puerto **5678** por defecto)

## Importar y activar

1. n8n → **Workflows** → **Import from File**
2. Archivo: `workflows/n8n-rag-assistant.json`
3. En el nodo **Call RAG API**, URL:
   - n8n en Docker: `http://host.docker.internal:8000/ask`
   - n8n nativo en Mac: `http://localhost:8000/ask`
4. **Activar** el workflow (toggle Active)

## Prueba directa de la API (sin n8n)

Equivalente funcional al nodo HTTP del workflow:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué hacer si las credenciales son incorrectas?"}'
```

Si esto funciona, el backend está listo; n8n solo reenvía la misma petición.

## Prueba del webhook

```bash
./scripts/test_n8n_webhook.sh "¿Qué hacer si las credenciales son incorrectas?"
```

O manualmente:

```bash
curl -X POST http://localhost:5678/webhook/support-ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cómo reinicio el servicio de autenticación?"}'
```

## Resultado esperado

- HTTP **200**
- JSON con campos `answer` y `sources`
- Si n8n no conecta: revisar URL del nodo HTTP y que la API escuche en `0.0.0.0:8000`

## Estado de verificación en desarrollo

| Prueba | Resultado |
|--------|-----------|
| `GET /health` | Verificado — API responde con índice cargado |
| `POST /ask` directo | Verificado — cadena RAG + Ollama operativa |
| Webhook n8n `:5678` | Requiere n8n activo localmente (script `scripts/test_n8n_webhook.sh`) |
