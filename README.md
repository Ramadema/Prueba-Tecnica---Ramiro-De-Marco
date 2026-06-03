# RAG Support Assistant — Asistente de Soporte Local

Asistente de soporte técnico basado en **RAG** (Retrieval Augmented Generation) que responde preguntas usando documentación interna. Ejecución 100% local con herramientas gratuitas.

## Stack

| Componente | Tecnología |
|------------|------------|
| API | FastAPI + Uvicorn |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector store | FAISS (IndexFlatIP) |
| LLM | Ollama (llama3.2:3b) |
| Orquestación | n8n (webhook) |
| Validación | Pydantic |

## Arquitectura

```
docs/ → Ingesta → Limpieza → Chunking → Embeddings → FAISS
Usuario → n8n Webhook → POST /ask → Recuperación → Ollama → Respuesta
```

## Requisitos previos

- Python 3.12+
- [Ollama](https://ollama.com) instalado y en ejecución
- [n8n](https://n8n.io) (Docker o desktop) — opcional para integración webhook

## Instalación (una sola vez)

Ejecutá estos comandos **en cualquier terminal**, dentro de la carpeta del proyecto:

```bash
cd "ML - Unilink"   # carpeta raíz del proyecto (ajustá la ruta completa si hace falta)

python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # opcional; hay valores por defecto

ollama pull llama3.2:3b            # descarga el modelo de generación
```

---

## Cómo ejecutar el programa (guía por consolas)

Necesitás **2 consolas siempre abiertas** mientras usás el asistente. Una **tercera** es opcional (solo para enviar pruebas con `curl`).

| Consola | ¿Para qué? | ¿Dejarla corriendo? |
|---------|------------|---------------------|
| **1 — Ollama** | Servidor del modelo de lenguaje (LLM) | Sí, todo el tiempo |
| **2 — API (Python)** | FastAPI en el puerto 8000 | Sí, todo el tiempo |
| **3 — Pruebas (opcional)** | `curl` o navegador; no levanta ningún servidor | Solo cuando querés probar |

No hace falta una consola por cada comando: **Ollama y la API deben quedar en ejecución**; los `curl` los podés tirar desde la misma consola 3 o desde una terminal nueva que cierre al terminar.

### Consola 1 — Ollama

Si tenés la app Ollama abierta en macOS, suele alcanzar. Si no:

```bash
ollama serve
```

En **otra** terminal (o antes de arrancar la API), verificá el modelo:

```bash
ollama list
# Debe aparecer llama3.2:3b
```

Dejá esta consola abierta (o la app Ollama en segundo plano).

### Consola 2 — API FastAPI

Entrá al proyecto, activá el entorno virtual y levantá uvicorn:

```bash
cd "ML - Unilink"
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Importante:** usá siempre el Python del `.venv`. Si corrés `uvicorn` sin activar el venv, verás:

`ModuleNotFoundError: No module named 'pydantic_settings'`

Alternativas equivalentes (sin `source activate`):

```bash
.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

o:

```bash
chmod +x run.sh    # solo la primera vez
./run.sh
```

Cuando arranque bien, deberías ver algo como:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Si ya existe un índice en `storage/`, también verás: `Loaded FAISS index with N chunks`.

**No ejecutes `./run.sh` ni otro uvicorn si la API ya está corriendo en esta consola** — el puerto 8000 quedaría ocupado y fallará.

### Consola 3 — Probar la API (opcional)

Podés usar una terminal nueva o la misma donde no corre nada. Desde ahí:

#### Health check

```bash
curl http://localhost:8000/health
```

Ejemplo de respuesta útil:

```json
{
  "status": "ok",
  "index_loaded": true,
  "chunk_count": 18,
  "ollama_reachable": true
}
```

#### Construir o actualizar el índice (primera vez o si cambiaste `docs/`)

```bash
curl -X POST http://localhost:8000/reindex
```

La primera vez puede tardar varios minutos (descarga del modelo de embeddings). Respuesta esperada:

```json
{
  "documents": 4,
  "chunks": 25,
  "duration_sec": 12.5,
  "message": "Index rebuilt successfully."
}
```

Si reiniciás la API después de un reindex exitoso, el índice se carga solo al arrancar.

#### Hacer una pregunta

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cómo soluciono un error de conexión con la base de datos?"}'
```

Respuesta:

```json
{
  "answer": "...",
  "sources": [
    {
      "source_file": "Documentación 2.txt",
      "chunk_index": 0,
      "score": 0.72,
      "excerpt": "..."
    }
  ]
}
```

#### Probar desde el navegador (sin curl)

Con la API en marcha, abrí: **http://localhost:8000/docs**  
Ahí podés probar `POST /ask` y `POST /reindex` con la interfaz Swagger.

---

## Orden recomendado (checklist)

1. [ ] `pip install -r requirements.txt` dentro de `.venv` (instalación única)
2. [ ] `ollama pull llama3.2:3b` (instalación única)
3. [ ] Consola 1: Ollama corriendo
4. [ ] Consola 2: `source .venv/bin/activate` + `uvicorn ...` → `Application startup complete`
5. [ ] Consola 3 (o navegador): `curl http://localhost:8000/health`
6. [ ] Si `index_loaded` es `false`: `curl -X POST http://localhost:8000/reindex`
7. [ ] `curl -X POST http://localhost:8000/ask` con una pregunta de prueba

## Integración n8n

### Importar workflow

1. Abrir n8n → **Workflows** → **Import from File**
2. Seleccionar [`workflows/n8n-rag-assistant.json`](workflows/n8n-rag-assistant.json)
3. Activar el workflow

### Configurar URL de la API

En el nodo **Call RAG API**, ajustar la URL según tu entorno:

| Entorno | URL |
|---------|-----|
| n8n en Docker, API en host | `http://host.docker.internal:8000/ask` |
| n8n y API en localhost | `http://localhost:8000/ask` |

### Probar el webhook

```bash
curl -X POST http://localhost:5678/webhook/support-ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué hacer si las credenciales son incorrectas?"}'
```

## Estructura del proyecto

```
├── docs/                    # Documentos fuente (.txt, .md, .pdf, .json)
├── src/
│   ├── main.py              # FastAPI app
│   ├── config/              # Settings y logging
│   ├── models/              # Schemas y domain models
│   ├── ingest/              # Lectura y limpieza
│   ├── rag/                 # Chunking, embeddings, FAISS, Ollama
│   ├── services/            # IndexService, RagService
│   └── api/                 # Routes y dependencies
├── storage/
│   ├── faiss/               # Índice persistido
│   └── metadata/            # Metadatos de chunks
├── workflows/               # n8n workflow export
└── tests/
```

## Variables de entorno

Ver [`.env.example`](.env.example). Principales:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CHUNK_SIZE` | 500 | Tamaño máximo de chunk (caracteres) |
| `CHUNK_OVERLAP` | 80 | Solapamiento entre chunks |
| `TOP_K` | 4 | Chunks a recuperar |
| `MIN_SCORE` | 0.35 | Umbral mínimo de similitud coseno |
| `OLLAMA_MODEL` | llama3.2:3b | Modelo de generación |

## Tests

```bash
pytest -v
```

Los tests de embeddings pesados se omiten por defecto; los tests de API usan mocks.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio |
| POST | `/reindex` | Reprocesar documentos y reconstruir índice |
| POST | `/ask` | Responder pregunta con RAG |

## Manejo de errores

| Código | Causa |
|--------|-------|
| 400 | Pregunta vacía |
| 404 | Sin documentos en `/docs` |
| 503 | Índice no construido o Ollama no disponible |
| 500 | Error de embeddings |

## Troubleshooting

**`ModuleNotFoundError: No module named 'pydantic_settings'`**  
Estás usando el Python del sistema, no el del proyecto. Solución: `source .venv/bin/activate` y volvé a ejecutar uvicorn, o usá `.venv/bin/uvicorn` / `./run.sh`.

**`Address already in use` / puerto 8000 ocupado**  
La API ya está corriendo en otra consola. No lances un segundo uvicorn ni `./run.sh`; usá esa instancia o detenela con Ctrl+C antes de reiniciar.

**`./run.sh` no hace nada o permission denied**  
```bash
cd "ML - Unilink"
chmod +x run.sh
./run.sh
```
Si la API ya está en el puerto 8000, `run.sh` fallará hasta que liberes el puerto.

**`index_loaded: false` en /health**  
Ejecutar `POST /reindex` después de colocar documentos en `docs/`.

**`ollama_reachable: false` o error 503 en /ask**  
Ollama no está corriendo o falta el modelo. Verificá: app Ollama abierta o `ollama serve`, y `ollama list` debe incluir `llama3.2:3b`.

**n8n no conecta a la API**  
Usar `host.docker.internal` si n8n corre en Docker.

**Primera ejecución lenta**  
La descarga del modelo `all-MiniLM-L6-v2` ocurre en el primer `/reindex`. La primera respuesta de `/ask` también puede tardar mientras Ollama carga el modelo.

## Licencia

Proyecto de prueba técnica — uso educativo/evaluación.
