"""
FastAPI Translation Application.

This application provides REST APIs for managing multilingual translations,
generating PO/MO files, and integrating with OpenAI for automated translation.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.config import Config
from config.logger import logger
from routes import (
    add_language_route,
    export_excel_route,
    get_languages_route,
    health_router,
    po_compiler_route,
    translation_routes,
    upload_from_excel_route,
    upload_route,
)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Translation Management API",
        version="1.0.0",
        description="Translation management system with OpenAI integration",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(translation_routes.router, prefix="/api")
    app.include_router(po_compiler_route.router, prefix="/api/localization")
    app.include_router(upload_route.router, prefix="/api")
    app.include_router(get_languages_route.router, prefix="/api")
    app.include_router(add_language_route.router, prefix="/api")
    app.include_router(export_excel_route.router, prefix="/api")
    app.include_router(upload_from_excel_route.router, prefix="/api")
    app.include_router(health_router.router, prefix="/api")

    # Mount frontend (if exists)
    try:
        app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
    except RuntimeError:
        logger.warning("Frontend directory not found, skipping static files mount")

    return app


app = create_application()


@app.on_event("startup")
async def startup_event():
    """Execute startup tasks."""
    logger.info(
        "Application started",
        extra={
            "environment": getattr(Config, 'ENVIRONMENT', 'development'),
            "port": Config.PORT,
        },
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Execute shutdown tasks."""
    logger.info("Application shutting down")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=Config.PORT,
        log_level="info",
    )
    logger.info(f"Server running at http://localhost:{Config.PORT}")