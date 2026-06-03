# Asistente de soporte RAG (local)

API FastAPI que responde preguntas sobre la documentación en `docs/`, usando embeddings + FAISS y generación con Ollama. Opcionalmente se expone vía webhook de n8n.

## Requisitos

- Python 3.12+
- [Ollama](https://ollama.com)
- [n8n](https://n8n.io) (opcional; en este proyecto se probó con Docker en el puerto 5678)

## Instalación (una sola vez)

Desde la carpeta del proyecto:

```bash
cd "ML - Unilink"   # raíz del repositorio

python3.12 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

ollama pull llama3.2:3b
```

> En macOS también podés usar la app Ollama en lugar de `ollama serve`, siempre que el modelo `llama3.2:3b` esté descargado (`ollama list`).

## Ejecución

Necesitás **dos terminales** con los servicios corriendo. Una tercera sirve solo para `curl` o pruebas.

### Terminal 1 — Ollama

Si `ollama pull` falla con *could not connect to ollama server*, primero levantá el servidor:

```bash
ollama serve
```

Dejá esta terminal abierta (o la app Ollama en segundo plano).

### Terminal 2 — API

```bash
cd "ML - Unilink"   # raíz del repositorio
source .venv/bin/activate

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Alternativa (usa el Python del `.venv` sin activar el entorno):

```bash
./run.sh
```

Deberías ver `Uvicorn running on http://0.0.0.0:8000` y, si ya existe índice en `storage/`, `Loaded FAISS index with N chunks`.

**No abras un segundo uvicorn** si el puerto 8000 ya está en uso.

### Terminal 3 — Verificar y usar la API

**Health:**

```bash
curl http://localhost:8000/health
```

Confirmá `ollama_reachable: true`. Si `index_loaded` es `false`, construí el índice:

```bash
curl -X POST http://localhost:8000/reindex
```

La primera vez puede tardar (descarga del modelo de embeddings). Con los documentos actuales en `docs/` se indexan 4 archivos (~18 chunks).

**Pregunta de prueba:**

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué hacer si las credenciales son incorrectas?"}'
```

**Swagger (sin curl):** http://localhost:8000/docs

**Script de verificación:**

```bash
./scripts/verify_api.sh
```

## n8n (opcional)

1. Levantá n8n (por ejemplo con Docker en el puerto 5678).
2. Importá `workflows/n8n-rag-assistant.json` y activá el workflow.
3. En el nodo **Call RAG API**:
   - n8n en Docker: `http://host.docker.internal:8000/ask`
   - n8n en el mismo host: `http://localhost:8000/ask`
4. Probá el webhook:

```bash
./scripts/test_n8n_webhook.sh "¿Qué hacer si las credenciales son incorrectas?"
```

Checklist detallada: [`workflows/VERIFICACION_N8N.md`](workflows/VERIFICACION_N8N.md)

## Orden rápido

1. Instalación (`venv`, `pip`, `.env`, `ollama pull`)
2. Terminal 1: Ollama activo
3. Terminal 2: `uvicorn` o `./run.sh`
4. `GET /health` → si hace falta, `POST /reindex`
5. `POST /ask` o `./scripts/verify_api.sh`
6. (Opcional) n8n + webhook

## Problemas frecuentes

| Síntoma | Qué hacer |
|---------|-----------|
| `ModuleNotFoundError: No module named 'pydantic_settings'` | Activá `.venv` (`source .venv/bin/activate`) o usá `./run.sh` / `.venv/bin/uvicorn` |
| `could not connect to ollama server` | Ejecutá `ollama serve` o abrí la app Ollama antes de `ollama pull` o `/ask` |
| `index_loaded: false` | `POST /reindex` con documentos en `docs/` |
| Puerto 8000 ocupado | Ya hay una API corriendo; usala o detenela con Ctrl+C |
| n8n no llega a la API | Con n8n en Docker usá `host.docker.internal:8000` |

Configuración avanzada: [`.env.example`](.env.example)
