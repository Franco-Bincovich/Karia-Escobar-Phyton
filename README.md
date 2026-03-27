# 🤖 KarIA Escobar — Backend Python/FastAPI

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Anthropic](https://img.shields.io/badge/Claude-Sonnet_4.5-6B4FBB?logo=anthropic&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-2.15-3FCF8E?logo=supabase&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-5.2-DC382D?logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-Privado-red)

Backend del agente de IA **KarIA Escobar**, migrado de Node.js/Express a **Python/FastAPI**. El frontend React se mantiene sin cambios.

---

## 📋 Descripción

KarIA Escobar es un agente de IA para la Municipalidad del Partido de Escobar. Permite a los usuarios interactuar con Claude para generar documentos formales, buscar normativa, gestionar emails, calendario y archivos de Google Workspace, y crear presentaciones con Gamma AI.

**¿Por qué Python/FastAPI?**

- **Async nativo** — FastAPI es async por defecto, sin callbacks ni promesas
- **Tipado estricto** — Pydantic valida todos los inputs en la frontera
- **Ecosistema IA** — El SDK de Anthropic y las librerías de ML son Python-first
- **Performance** — Uvicorn + async/await maneja concurrencia eficientemente

---

## 🛠️ Stack Tecnológico

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Python** | 3.12+ | Runtime |
| **FastAPI** | 0.115.6 | Framework HTTP async |
| **Uvicorn** | 0.34.0 | ASGI server |
| **Pydantic** | 2.10.4 | Validación de inputs |
| **Supabase** | 2.15.0 | Base de datos (PostgreSQL) |
| **Anthropic SDK** | 0.50.0 | Cliente Claude Sonnet 4.5 |
| **Redis** | 5.2.1 | Rate limiting persistente (opcional) |
| **bcrypt** | 4.2.1 | Hashing de contraseñas (12 rounds) |
| **python-jose** | 3.3.0 | JWT HS256 (8h expiry) |
| **cryptography** | 44.0.3 | AES-256-CBC para credenciales |
| **httpx** | 0.27.0 | HTTP client async (scraping) |
| **BeautifulSoup** | 4.13.4 | Parsing HTML (Infoleg, SAIJ) |
| **openpyxl** | 3.1.5 | Generación/análisis Excel |
| **python-docx** | 1.1.2 | Generación Word |
| **pdfplumber** | 0.11.4 | Extracción de texto PDF |
| **Google APIs** | 2.169.0 | Gmail, Calendar, Drive |

---

## 🏗️ Arquitectura

```
src/
├── main.py                  ← Entry point, arranca Uvicorn
├── app.py                   ← FastAPI, middlewares, rutas, security headers
├── agent.py                 ← Orquestador del agente Claude
│
├── config/
│   ├── index.py             ← ÚNICO lugar que lee variables de entorno
│   ├── integraciones.py     ← Constantes de tipos y scopes Google
│   └── system_prompts.py    ← System prompts del agente
│
├── routes/                  ← Solo routing + validación Pydantic
│   ├── auth_routes.py       ← POST /api/auth/login
│   ├── chat_routes.py       ← POST /api/chat, GET /api/conversaciones
│   ├── documento_routes.py  ← POST /api/documentos/upload
│   ├── funcionalidad_routes.py
│   └── integracion_routes.py ← CRUD + OAuth Google
│
├── controllers/             ← Solo orquestación, sin lógica
│   ├── auth_controller.py
│   ├── chat_controller.py
│   ├── documento_controller.py
│   ├── funcionalidad_controller.py
│   ├── integracion_controller.py
│   └── oauth_controller.py  ← Flujo OAuth2 Google
│
├── services/                ← TODA la lógica de negocio
│   ├── auth_service.py      ← Login, JWT, bcrypt, rate limit por cuenta
│   ├── chat_service.py      ← Conversaciones, título auto con Claude
│   ├── documento_service.py ← Parseo PDF/Excel/Word/CSV/TXT
│   ├── funcionalidad_service.py ← CRUD + prompt injection blocklist
│   └── integracion_service.py   ← API keys cifradas, tokens Google
│
├── repositories/            ← ÚNICO contacto con Supabase
│   ├── base_repository.py   ← check_db_error() compartido
│   ├── user_repository.py
│   ├── conversacion_repository.py
│   ├── funcionalidad_repository.py
│   └── integracion_repository.py
│
├── integrations/            ← Clientes de APIs externas
│   ├── anthropic_client.py  ← Singleton Claude
│   ├── supabase_client.py   ← Singleton Supabase (lazy)
│   ├── redis_client.py      ← Singleton Redis (graceful degradation)
│   ├── google_client.py     ← OAuth2 autenticado + auto-refresh
│   ├── google_oauth_factory.py
│   └── google_token_refresh.py ← Refresh con deduplicación
│
├── tools/                   ← Herramientas del agente (14 tools)
│   ├── index.py             ← Registro central + dispatcher
│   ├── tool_definitions.py  ← Schemas Anthropic
│   ├── excel_tools.py       ← generar_excel, analizar_excel_avanzado
│   ├── word_tools.py        ← generar_word (5 tipos formales)
│   ├── gamma_tools.py       ← Presentaciones con Gamma AI
│   ├── search/
│   │   ├── web.py           ← DuckDuckGo + protección SSRF
│   │   ├── normativa.py     ← Infoleg + SAIJ en paralelo
│   │   └── ordenanzas.py    ← HCD Partido de Escobar
│   └── google/
│       ├── gmail_tools.py   ← Leer/enviar emails
│       ├── calendar_tools.py ← Leer/crear eventos
│       └── drive_tools.py   ← Buscar archivos
│
├── middleware/
│   ├── auth.py              ← Dependency JWT (get_current_user)
│   ├── error_handler.py     ← AppError + handler global
│   └── rate_limiter.py      ← Redis + fallback memoria
│
└── utils/
    ├── app_error.py         ← Excepción base operacional
    ├── logger.py            ← Logger centralizado
    ├── crypto.py            ← AES-256-CBC cifrado/descifrado
    └── agent_loop.py        ← Loop agéntico con Semaphore
```

**Flujo de datos:** `Route → Controller → Service → Repository/Integration`

Ninguna capa salta a otra. Los controllers nunca importan repositories.

---

## 🔄 Diferencias con la Versión JS

| Aspecto | Node.js/Express | Python/FastAPI |
|---------|----------------|----------------|
| **Runtime** | Node.js 20 | Python 3.12 |
| **Framework** | Express | FastAPI + Uvicorn |
| **Validación** | express-validator | Pydantic models |
| **Async** | Callbacks/Promises | async/await nativo |
| **Rate limiting** | express-rate-limit (memoria) | Redis + fallback memoria |
| **Concurrencia API** | Sin límite | `asyncio.Semaphore(15)` |
| **Security headers** | Helmet | Middleware custom |
| **Config validation** | Manual al startup | Pydantic Settings + `_validar_config()` |
| **Cifrado** | crypto (Node) | cryptography (Python) |
| **Scraping** | cheerio | BeautifulSoup + httpx async |
| **SSRF protection** | No | Whitelist hosts + bloqueo IPs privadas |

**Mejoras sobre el JS:**
- `asyncio.Semaphore(15)` protege el rate limit de Anthropic
- Redis para rate limiting persistente entre reinicios
- Protección SSRF en tools de búsqueda web
- Sanitización FTS en búsqueda de Google Drive
- Validación de tamaño de archivo (20MB) antes de leer en memoria
- Config validation al startup (falla rápido si faltan variables críticas)

---

## 📦 Requisitos

- **Python** 3.12+
- **pip** (viene con Python)
- **Supabase** — cuenta con las tablas del proyecto JS ya creadas
- **Redis** (opcional) — sin Redis funciona con rate limiting en memoria
- **API Key de Anthropic** — para Claude Sonnet 4.5

---

## 🚀 Instalación

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd Escobar-Phyton

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

---

## 🔐 Variables de Entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `PORT` | No | Puerto del servidor (default: `3004`) |
| `NODE_ENV` | No | Entorno: `development` o `production` |
| `ALLOWED_ORIGINS` | No | Orígenes CORS separados por coma (default: `http://localhost:5173`) |
| `JWT_SECRET` | **Sí** | Secret para firmar JWTs — mínimo 32 caracteres |
| `ANTHROPIC_API_KEY` | **Sí** | API key de Anthropic para Claude |
| `SUPABASE_URL` | **Sí** | URL del proyecto Supabase |
| `SUPABASE_KEY` | **Sí** | Service key de Supabase |
| `GOOGLE_CLIENT_ID` | No | Client ID de Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | No | Client Secret de Google Cloud Console |
| `GOOGLE_REDIRECT_URI` | No | URI de callback OAuth |
| `REDIS_URL` | No | URL de Redis (default: `redis://localhost:6379`) |
| `GAMMA_API_KEY` | No | API key de Gamma AI |
| `ANTHROPIC_MAX_CONCURRENT` | No | Máximo de requests concurrentes a Claude (default: `15`) |

> Las 4 variables marcadas como **Sí** son validadas al startup. Si falta alguna, el servidor no arranca.

---

## ▶️ Cómo Correr

```bash
# Desarrollo (con hot reload)
uvicorn src.main:app --reload --port 3004

# Producción
uvicorn src.main:app --host 0.0.0.0 --port 3004 --workers 4
```

El servidor queda disponible en `http://localhost:3004`.

| Endpoint | Descripción |
|----------|-------------|
| `GET /health` | Health check |
| `GET /docs` | Swagger UI (solo desarrollo) |
| `GET /redoc` | ReDoc (solo desarrollo) |

---

## 📈 Escalabilidad

### Semaphore de Anthropic

```python
_semaphore = asyncio.Semaphore(settings.ANTHROPIC_MAX_CONCURRENT)  # default: 15

async with _semaphore:
    respuesta = client.messages.create(...)
```

Limita a 15 llamadas concurrentes a la API de Claude. Evita errores 429 por rate limit de Anthropic. Configurable vía `ANTHROPIC_MAX_CONCURRENT`.

### Redis para Rate Limiting

```
Con Redis:    Persistente entre reinicios, sliding window con INCR+EXPIRE
Sin Redis:    Fallback automático a dict en memoria (graceful degradation)
```

| Endpoint | Límite | Key |
|----------|--------|-----|
| `POST /api/auth/login` | 10 req / 15 min | `ratelimit:login:{email}` |
| `POST /api/chat` | 20 req / 1 min | `ratelimit:chat:{userId}` |
| `POST /api/documentos/upload` | 100 req / 15 min | IP |
| `POST /api/integraciones/*` | 100 req / 15 min | IP |

---

## 🔒 Seguridad

| Medida | Implementación |
|--------|----------------|
| **Cifrado de credenciales** | AES-256-CBC con scrypt key derivation, salt dinámico |
| **Autenticación** | JWT HS256, 8 horas de expiración |
| **Contraseñas** | bcrypt 12 rounds + dummy hash anti-timing attack |
| **Ownership checks** | `user_id` en WHERE de todas las queries (19/19 funciones) |
| **Security headers** | X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS |
| **SSRF protection** | Whitelist de hosts + HTTPS only + bloqueo IPs privadas |
| **FTS injection** | Sanitización de `'"\():]` en búsquedas de Google Drive |
| **Prompt injection** | Blocklist de 25+ patrones + normalización NFC + zero-width removal |
| **CRLF injection** | Validación en destinatario y asunto de emails |
| **File upload** | Validación de tamaño (20MB), extensión (whitelist), limpieza en finally |
| **CORS** | Orígenes, métodos y headers explícitos |
| **Config validation** | Falla al startup si faltan JWT_SECRET, ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY |

---

## 📐 Bases de Desarrollo

El proyecto sigue 11 bases de desarrollo, verificadas con auditoría automatizada.

| # | Base | Estado |
|---|------|--------|
| 1 | Arquitectura por capas (routes → controllers → services → repos) | ✅ 0 violaciones |
| 2 | Manejo de errores centralizado (AppError + handler global) | ✅ |
| 3 | Config externalizado (os.environ solo en config/index.py) | ✅ 0 fugas |
| 4 | Validación Pydantic en todos los POST | ✅ 6/6 endpoints |
| 5 | Migraciones versionadas (misma DB que el proyecto JS) | ✅ |
| 6 | Código legible (máximo 150 líneas por archivo) | ✅ 0 excedidos |
| 7 | Contratos explícitos (docstrings en services/repos/integrations) | ✅ 100% |
| 8 | Flujo run & see (levanta con un comando) | ✅ |
| 9 | Autenticación segura (JWT en todos los endpoints protegidos) | ✅ 13/13 |
| 10 | Sin CVEs activos en dependencias | ✅ |
| 11 | Estilo consistente (snake_case en Python) | ✅ |

**Resultado de auditoría: 9.3 / 10 — APTO PARA PRODUCCIÓN**

---

## 🖥️ Frontend

El frontend React del proyecto JS original (`Karia-Agent/Escobar-React`) es **compatible sin cambios**. La API mantiene el mismo contrato:

- Mismos endpoints y métodos HTTP
- Mismos nombres de campos en JSON (camelCase)
- Mismos códigos de error (INVALID_CREDENTIALS, TOKEN_EXPIRED, etc.)
- Mismo formato de respuesta: `{ error: true, message, code }`

Para conectar el frontend, asegurate de que `ALLOWED_ORIGINS` incluya la URL donde corre React (default: `http://localhost:5173`).

---

## 📁 Endpoints

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/auth/login` | No | Login con email y password |
| POST | `/api/chat` | JWT | Enviar mensaje al agente |
| GET | `/api/conversaciones` | JWT | Listar conversaciones |
| GET | `/api/conversaciones/{id}` | JWT | Cargar conversación |
| POST | `/api/documentos/upload` | JWT | Subir y parsear documento |
| GET | `/api/funcionalidades` | JWT | Listar funcionalidades |
| POST | `/api/funcionalidades` | JWT | Crear funcionalidad |
| PATCH | `/api/funcionalidades/{id}/toggle` | JWT | Activar/desactivar |
| DELETE | `/api/funcionalidades/{id}` | JWT | Eliminar funcionalidad |
| GET | `/api/integraciones` | JWT | Listar integraciones |
| POST | `/api/integraciones/apikey` | JWT | Conectar API key |
| POST | `/api/integraciones/google/auth` | JWT | Iniciar OAuth Google |
| GET | `/api/integraciones/google/callback` | State | Callback OAuth |
| PATCH | `/api/integraciones/{tipo}/toggle` | JWT | Activar/desactivar |
| DELETE | `/api/integraciones/{tipo}` | JWT | Desconectar integración |
