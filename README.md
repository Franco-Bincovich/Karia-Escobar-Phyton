# KarIA Escobar — Backend Python/FastAPI

Backend del agente KarIA Escobar, migrado de Node.js/Express a Python/FastAPI.

## Requisitos

- Python 3.11+
- pip

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Completar las variables en .env
```

## Cómo correr

```bash
uvicorn src.main:app --reload --port 3004
```

El servidor queda disponible en `http://localhost:3004`.
Health check: `GET /health`
