"""FastAPI main application"""

import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.api.routes import api_router
from app.core.model_loader import get_model_manager
from app.services.file_handler import get_file_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("Starting MRI SAAS API...")

    # Ensure temp directory exists
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Pre-load model (optional, can be lazy loaded)
    try:
        model_manager = get_model_manager()
        model_manager.get_model()
        print(f"Model loaded successfully on {model_manager.get_device()}")
    except Exception as e:
        print(f"Warning: Could not pre-load model: {e}")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    print("MRI SAAS API shutdown complete")


async def periodic_cleanup():
    """Periodically clean up expired sessions"""
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            file_handler = get_file_handler()
            file_handler.cleanup_expired()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Cleanup error: {e}")


app = FastAPI(
    title="MRI Segmentation API",
    description="API for MRI T2 coronal segmentation using Vanilla U-Net",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add Render URL if available
render_url = os.environ.get("RENDER_EXTERNAL_URL")
if render_url:
    origins.append(render_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "MRI Segmentation API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health"
    }


# Serve frontend static files (for production deployment)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend SPA - fallback to index.html"""
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(static_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
