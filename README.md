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
├── workflows/               # n8n workflow export + verificación
├── scripts/                 # verify_api.sh, test_n8n_webhook.sh
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

---

## Cumplimiento de consignas (prueba técnica Unilink)

Este repositorio resuelve el ejercicio de **asistente automatizado de soporte** con documentación interna. Resumen de cumplimiento:

| Parte / requisito | Estado | Implementación |
|-------------------|--------|----------------|
| **Objetivo:** n8n + Python + REST + LLM local | Cumple | n8n webhook → FastAPI → Ollama |
| **Parte 1:** Ingesta (.txt, .md, .pdf, .json) | Cumple | [`src/ingest/`](src/ingest/) |
| **Parte 1:** Limpieza, ruido, fragmentos | Cumple | `TextCleaner` + `SentenceAwareChunker` |
| **Parte 2:** Workflow n8n + Webhook | Cumple | [`workflows/n8n-rag-assistant.json`](workflows/n8n-rag-assistant.json) |
| **Parte 3:** Recuperación + no inventar | Cumple | FAISS + `min_score` + prompt grounded |
| **Parte 3:** Sin info → mensaje explícito | Cumple | *"No encontré información suficiente..."* |
| **Parte 4:** Contexto, prompts, flujo, claridad | Cumple | [`src/rag/prompts.py`](src/rag/prompts.py), bloques `[1]`, `[2]` |
| **Parte 5:** Python (chunking, embeddings, etc.) | Cumple | [`src/rag/`](src/rag/), [`src/services/`](src/services/) |
| **Parte 6:** Errores, timeouts, inputs vacíos | Cumple | Handlers en [`src/main.py`](src/main.py) |
| **Parte 7:** Local + README + `.env.example` | Cumple | Este documento |
| **Entregables:** código + workflow n8n | Cumple | `src/`, `workflows/` |

### ¿Hay frontend?

**No.** Las consignas no piden una aplicación web de chat. Los canales de uso son:

- **n8n** (webhook HTTP — canal principal del enunciado)
- **Swagger** en http://localhost:8000/docs (pruebas manuales)
- **curl** (pruebas por consola)

### Parte 4 — ¿Por qué Ollama y no OpenAI?

El enunciado general permite *«un LLM local o la capa gratuita de la API OpenAI»*. La Parte 4 del PDF menciona OpenAI API; esta solución opta por **LLM 100% local con Ollama** porque:

- Cumple el requisito de **LLM local**
- No requiere API key ni costos
- La inferencia corre en la máquina del evaluador (alineado con deployment local)
- El procesamiento pesado (embeddings, FAISS, chunking) ya está en Python; Ollama solo genera la respuesta final con el contexto recuperado

---

## Demo para entrevista técnica

Guion sugerido para la presentación oral (15–20 min). Tener **Ollama**, la **API** y, si es posible, **n8n** activos.

### 1. Verificar servicios

```bash
curl http://localhost:8000/health
```

Confirmar: `index_loaded: true`, `ollama_reachable: true`, `chunk_count` > 0.

Si `index_loaded` es `false`:

```bash
curl -X POST http://localhost:8000/reindex
```

### 2. Preguntas alineadas al corpus (deben responder con fuentes)

| Pregunta (consigna / MineCatalog) | Qué validar |
|-----------------------------------|-------------|
| «¿Qué hacer si las credenciales son incorrectas?» | Menciona ERR-AUTH-001 o pasos de `Documentación 3.md`; `sources` no vacío |
| «¿Cómo soluciono un error de conexión con la base de datos?» | Causas/solución de DB; `sources` apuntan a .txt o .json |
| «No puedo acceder al dashboard» | Si no hay info en docs → mensaje *sin inventar*, no pasos ficticios |

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué hacer si las credenciales son incorrectas?"}'
```

### 3. Pregunta fuera del corpus (anti-alucinación)

Del enunciado: *«El sistema devuelve error 502, ¿qué significa?»*

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "El sistema devuelve error 502, ¿qué significa?"}'
```

**Comportamiento esperado:** respuesta explícita de que no hay información en la documentación (o `sources: []`), **sin** inventar significado del 502.

### 4. Flujo n8n (Parte 2)

1. Importar [`workflows/n8n-rag-assistant.json`](workflows/n8n-rag-assistant.json)
2. Activar el workflow
3. Probar el webhook (puerto 5678 por defecto):

```bash
curl -X POST http://localhost:5678/webhook/support-ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cómo reinicio el servicio de autenticación?"}'
```

Script alternativo (misma prueba): [`scripts/test_n8n_webhook.sh`](scripts/test_n8n_webhook.sh)  
Checklist detallada: [`workflows/VERIFICACION_N8N.md`](workflows/VERIFICACION_N8N.md)

### 5. Guion oral (30 segundos por punto)

1. **Arquitectura:** ingesta offline (`/reindex`) + consulta online (`/ask`); Python procesa documentos; n8n solo enruta HTTP.
2. **Anti-alucinación:** umbral de similitud + prompt con contexto numerado + sin LLM si no hay chunks relevantes.
3. **Stack local:** MiniLM + FAISS + Ollama, sin servicios cloud de pago.
4. **Limitaciones:** sin UI de chat; calidad acotada al contenido de `docs/`.

---

## Entrega en GitHub

Requisito de la consigna: repositorio **público** con nombre:

```text
Prueba Técnica – (Nombre Postulante)
```

Reemplazá `(Nombre Postulante)` por tu nombre real.

### Pasos

Checklist completa: [`GITHUB_ENTREGA.md`](GITHUB_ENTREGA.md)

```bash
cd "ML - Unilink"

# Verificar que .env NO se sube (debe aparecer en .gitignore)
git check-ignore -v .env   # esperado: .gitignore:9:.env    .env
git ls-files .env          # no debe imprimir nada

# Crear repo público en github.com/new con el nombre de la consigna
git remote add origin https://github.com/TU_USUARIO/Prueba-Tecnica-Tu-Nombre.git
git push -u origin develop
```

### Qué incluir en el repo

| Incluir | No incluir |
|---------|------------|
| `src/`, `docs/`, `tests/`, `workflows/` | `.env` (secretos locales) |
| `requirements.txt`, `.env.example`, `README.md` | `.venv/` |
| `run.sh`, `scripts/` | `__pycache__/`, `.pytest_cache/` |

El índice en `storage/` puede omitirse del commit (está en `.gitignore`); el evaluador lo regenera con `POST /reindex`.

### Enlace al repo

Repositorio configurado en este proyecto:

**https://github.com/Ramadema/Prueba-Tecnica---Ramiro-De-Marco**

La consigna sugiere el nombre `Prueba Técnica – (Nombre Postulante)`. Si el evaluador exige el nombre exacto, renombrá el repo en GitHub → **Settings** → **Repository name** o creá uno nuevo y actualizá `git remote`.

---

## Licencia

Proyecto de prueba técnica — uso educativo/evaluación.
