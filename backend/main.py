from fastapi import FastAPI
from config.logger import logger
from routes.translation_routes import router as translation_router
from routes import upload_route, get_languages_route, add_language_route, po_compiler_route, export_excel_route
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.config import Config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Application started")

app.include_router(translation_router, prefix="/api")
app.include_router(po_compiler_route.router, prefix="/api/localization")
app.include_router(upload_route.router, prefix="/api")
app.include_router(get_languages_route.router, prefix="/api")
app.include_router(add_language_route.router, prefix="/api")
app.include_router(export_excel_route.router, prefix="/api")

# Mount frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")


if __name__ == "__main__":

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT, log_level="info")
    logger.info(f"Server running at http://localhost:{Config.PORT}")