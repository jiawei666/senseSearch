"""FastAPI 应用入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.search import router as search_router
from app.api.conversation import router as conversation_router

from app.core.config import get_settings
from app.core.milvus import close_milvus_connection

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_milvus_connection()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="SenseSearch Backend API",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(search_router)
app.include_router(conversation_router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "not available",
    }
