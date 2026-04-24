from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import logger
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting API | debug={settings.debug} | provider={settings.llm_provider}")
    yield
    logger.info("Shutting down API")


app = FastAPI(
    title="Media Growth AI Agent",
    version="0.1.0",
    description="MVP: FastAPI + LangGraph + BigQuery (thelook_ecommerce)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["chat"])


@app.get("/health")
async def health():
    return {"status": "ok", "debug": settings.debug, "llm_provider": str(settings.llm_provider)}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "detail": [{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()],
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    logger.error("Unhandled error", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred",
        },
    )