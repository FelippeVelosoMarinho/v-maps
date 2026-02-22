from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import time
import logging
import json

import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.config import settings
from app.database import create_tables
from app.routers import (
    auth_router,
    users_router,
    maps_router,
    places_router,
    check_ins_router,
    chat_router,
    friends_router,
    groups_router,
    social_router,
    trips_router,
    avatars_router,
    notifications_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    logger.info(f"--- STARTUP: USING DATABASE URL: {settings.database_url} ---")
    await create_tables()
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Log de diagnóstico
    allowed_origins = [
        settings.frontend_url,
        "http://localhost:8080", "http://localhost:5173", "http://localhost:8081",
        "http://127.0.0.1:8080", "http://127.0.0.1:5173", "http://127.0.0.1:8081",
        "https://client.felippe-91e.workers.dev",
        "https://76.13.71.126",
        "capacitor://localhost",
        "http://localhost",
        "https://localhost",
        "http://10.0.2.2:8000",
        "http://10.0.0.24:5173",
        "http://10.0.0.24",
    ]
    logger.info(f">>> API INICIADA | CORS ALLOWED ORIGINS: {allowed_origins}")
    
    yield

app = FastAPI(
    title="V-Maps API",
    description="API para o aplicativo V-Maps - Compartilhe lugares com amigos",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (Interno do FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:8080",
        "http://localhost:5173",
        "http://localhost:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8081",
        "https://client.felippe-91e.workers.dev",
        "https://76.13.71.126",
        "capacitor://localhost",
        "http://localhost",
        "https://localhost",
        "http://10.0.2.2:8000",
        "http://10.0.0.24:5173",
        "http://10.0.0.24",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (uploads)
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Exception Handler Global (Modo de Diagnóstico)
from fastapi.responses import JSONResponse
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    logger.error(f"FATAL ERROR CAPTURED: {str(exc)}\n{error_trace}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "traceback": error_trace,
            "path": request.url.path,
            "method": request.method
        }
    )

@app.get("/debug/cors-check")
async def cors_check(request: Request):
    """Retorna os headers da requisição para ajudar no debug de CORS."""
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client": request.client.host,
        "allowed_origins_hint": "capacitor://localhost, http://localhost, https://localhost"
    }

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(maps_router)
app.include_router(places_router)
app.include_router(check_ins_router)
app.include_router(chat_router)
app.include_router(friends_router)
app.include_router(groups_router)
app.include_router(social_router)
app.include_router(trips_router)
app.include_router(avatars_router)
app.include_router(notifications_router)

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_all(request: Request, path_name: str):
    """Catch-all para logar rotas não encontradas e ajudar a depurar o prefixo /vmaps."""
    method = request.method
    full_url = str(request.url)
    origin = request.headers.get("origin", "unknown")
    
    logger.warning(f"!!! ROTA NÃO ENCONTRADA: {method} /{path_name} !!!")
    logger.warning(f"    URL Completa: {full_url}")
    logger.warning(f"    Origin: {origin}")
    
    return {
        "error": "Not Found",
        "detail": f"A rota {method} /{path_name} não existe neste servidor.",
        "hint": "Se você está usando o prefixo /vmaps no frontend, verifique se o seu Nginx está removendo esse prefixo antes de repassar para o FastAPI.",
        "received_path": path_name,
        "received_method": method
    }

@app.get("/")
async def root():
    return {"message": "V-Maps API is running"}
