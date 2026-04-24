import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
from app.routers import health, protocols as protocols_module, generate, check, export, templates, auth, audit, biocad_trials, embeddings as embeddings_module

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup: AI Protocol Generator backend starting")

    # RAG: background indexing of existing protocol versions (non-blocking)
    if settings.AI_EMBEDDING_URL:
        async def _bg_index():
            try:
                from app.core.database import AsyncSessionLocal
                from app.services.embedding_service import reindex_all
                async with AsyncSessionLocal() as db:
                    result = await reindex_all(db, limit=100)
                    logger.info("startup_rag_index_done", extra=result)
            except Exception as e:
                logger.warning("startup_rag_index_failed", extra={"error": str(e)})

        import asyncio as _asyncio
        _asyncio.create_task(_bg_index())
    else:
        logger.info("startup: RAG disabled (AI_EMBEDDING_URL not set)")

    yield
    await engine.dispose()
    logger.info("shutdown: engine disposed")


app = FastAPI(
    title="AI Protocol Generator API",
    version="0.1.0",
    description="AI-powered clinical trial protocol generator. AI: InHouse/Qwen3.5-122B via internal AI Gateway.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", extra={"path": request.url.path, "error": str(exc)})
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "details": []}},
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(protocols_module.tags_router)
app.include_router(protocols_module.router)
app.include_router(generate.router)
app.include_router(check.router)
app.include_router(export.router)
app.include_router(templates.router)
app.include_router(audit.router)
app.include_router(biocad_trials.router)
app.include_router(embeddings_module.router)


@app.get("/api/v1/info")
async def api_info():
    return {
        "version": "0.1.0",
        "ai_model": settings.AI_GATEWAY_MODEL,
        "environment": settings.APP_ENV,
    }
