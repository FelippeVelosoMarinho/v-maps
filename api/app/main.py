from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import time
import logging
from fastapi import Request

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
    await create_tables()
    
    # Criar pasta de uploads
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    yield
    
    # Shutdown
    pass


app = FastAPI(
    title="V-Maps API",
    description="API para o aplicativo V-Maps - Compartilhe lugares com amigos",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware de Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Iniciando requisição: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Finalizando requisição: {request.method} {request.url.path} - Status: {response.status_code} - Tempo: {process_time:.4f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Erro na requisição: {request.method} {request.url.path} - Erro: {str(e)} - Tempo: {process_time:.4f}s")
        raise e

# CORS
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
        "https://tsapi.ciano.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (uploads)
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

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


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "message": "V-Maps API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Verifica se a API está funcionando."""
    return {"status": "healthy"}
